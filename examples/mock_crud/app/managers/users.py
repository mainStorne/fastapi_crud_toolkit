from secrets import token_urlsafe
from typing import Iterable, Any, Optional, List
import jwt
from fastapi import UploadFile, HTTPException
from fastapi_sqlalchemy_toolkit.model_manager import CreateSchemaT, ModelT
from fastapi_users.password import PasswordHelperProtocol, PasswordHelper
from sqlalchemy import UnaryExpression, select, Row, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, joinedload
from starlette import status

from shared.storage.cache.redis_client import RedisClient
from shared.storage.db.models import User, Role, OAuthAccount
from .base import BaseManager
from ..schemas.users import UserCredentials
from ..exceptions import InvalidResetPasswordToken, UserAlreadyVerifiedException
from ..services.oauth import YandexUserInfo
from ..services.oauth.base import OAuth2Response
from ..services.oauth.vk_oauth import VKUserInfo
from ..managers.files import _save_file_to_static
from ..conf import settings
from secrets import token_urlsafe


class UsersManager(BaseManager):

    def __init__(self,
                 default_ordering: InstrumentedAttribute | UnaryExpression | None = None,
                 password_helper: Optional[PasswordHelperProtocol] = None,
                 ) -> None:
        if password_helper is None:
            self.password_helper = PasswordHelper()
        else:
            self.password_helper = password_helper  # pragma: no cover
        super().__init__(User, default_ordering)

    async def forgot_password(self, user: User, redis_client: RedisClient):
        token = token_urlsafe(32)
        await redis_client.forgot_password(token, user)
        return token

    async def verify(self, session: AsyncSession, redis: RedisClient, token: str):
        user_id = await redis.reset_password(token)
        user: User = await self.get_or_404(session, id=user_id)
        if user.is_verified:
            raise UserAlreadyVerifiedException

        user.is_verified = True
        session.add(user)
        await session.commit()
        return user

    async def reset_password(self, session: AsyncSession, redis: RedisClient, token: str, new_password: str):
        user_id = await redis.reset_password(token)
        user: User = await self.get_or_404(session, id=user_id)

        user.password = self.password_helper.hash(new_password)
        session.add(user)
        await session.commit()
        return user

    async def create_user(
            self,
            session: AsyncSession,
            in_obj: CreateSchemaT | None = None,
            file: UploadFile | None = None,
            *,
            commit: bool = True,
            refresh_attribute_names: Iterable[str] | None = None,
            role_name: str = 'usual',
            **attrs: Any,
    ) -> ModelT:

        in_obj.password = self.password_helper.hash(in_obj.password)
        create_data = in_obj.model_dump()
        create_data.update(attrs)

        # Добавляем дефолтные значения полей для валидации уникальности
        for field, default in self.defaults.items():
            if field not in create_data:
                create_data[field] = default

        await self.run_db_validation(session, in_obj=create_data)
        if file is not None:
            try:
                photo_url = await _save_file_to_static(file)
                create_data['photo_url'] = photo_url
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Could not upload file')
        else:
            create_data['photo_url'] = None

        db_obj = self.model(**create_data)
        stmt = select(Role).where(Role.name == role_name)
        role = await session.scalar(stmt)
        if not role:
            role = Role(name=role_name)
        db_obj.roles.append(role)
        session.add(db_obj)

        await self.save(session, commit=commit)

        await session.refresh(db_obj, attribute_names=refresh_attribute_names)
        return db_obj

    async def create_yandex_user(
            self,
            session: AsyncSession,
            user_info: YandexUserInfo,
            yandex_tokens: OAuth2Response,

    ):
        stmt = self.assemble_stmt(username=user_info.login, options=[joinedload(User.oauth_accounts)])
        user = await session.scalar(stmt)
        if user:
            return user

        user = User(username=user_info.login, password=None, first_name=user_info.first_name, middle_name=None,
                    last_name=user_info.last_name,
                    email=user_info.default_email,
                    photo_url=f'https://avatars.yandex.net/get-yapic/{user_info.default_avatar_id}')
        account = OAuthAccount(provider='yandex', access_token=yandex_tokens.access_token,
                               refresh_token=yandex_tokens.refresh_token)
        user.oauth_accounts = [account]
        session.add(user)

        await session.commit()
        return user

    async def create_vk_user(
            self,
            session: AsyncSession,
            user_info: VKUserInfo,
            tokens: OAuth2Response,
    ):
        user_info = user_info.user
        stmt = self.assemble_stmt(username=user_info.email, options=[joinedload(User.oauth_accounts)])
        user = await session.scalar(stmt)
        if user:
            return user

        user = User(username=user_info, password=None, first_name=user_info.first_name, middle_name=None,
                    last_name=user_info.last_name,
                    email=user_info.email,
                    photo_url=user_info.avatar)
        account = OAuthAccount(provider='yandex', access_token=tokens.access_token,
                               refresh_token=tokens.refresh_token)
        user.oauth_accounts = [account]
        session.add(user)

        await session.commit()
        return user

    async def authenticate(self, session: AsyncSession, credentials: UserCredentials):
        stmt = select(User).where(credentials.login == User.username)
        user = (await session.execute(stmt)).scalar()
        if not user:
            # Run the hasher to mitigate timing attack
            # Inspired from Django: https://code.djangoproject.com/ticket/20760
            self.password_helper.hash(credentials.password)
            return None
        if user.password is None:
            return None

        verified, updated_password_hash = self.password_helper.verify_and_update(
            credentials.password, user.password
        )
        if not verified:
            return None
        # Update password hash to a more robust one if needed
        if updated_password_hash is not None:
            user.password = updated_password_hash
            session.add(user)
            await session.commit()

        return user

    def _generate_partial_token(self):
        return token_urlsafe()
