from fastapi_permissions import has_permission
from fastapi_sqlalchemy_toolkit import ModelManager
from pydantic import BaseModel
from starlette import status
from shared.crud import (
    missing_token_or_inactive_user_response, not_found_response, forbidden_response,
)
from typing import Any, Type, Callable
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from shared.crud.openapi_responses import auth_responses
from web.app.utils.users import authenticator
from web.app.utils.permissions import Permission, get_user_principals
from .base import Resource, CrudAPIRouter


class BatchPermittedException(Exception):
    pass


class PermissionCrudAPIRouter(CrudAPIRouter):

    def __init__(self, schema: Type[BaseModel], manager: ModelManager, create_schema: Type[BaseModel],
                 update_schema: Type[BaseModel], **kwargs: Any):
        super().__init__(schema, manager, create_schema, update_schema, **kwargs)

    #
    @staticmethod
    async def atomic_operation(
            get_resources: Callable[[], list[Resource]],
            batch_permission: list,

    ):
        async def wrapper(
                items: list[Resource] = Depends(get_resources),
                principals: list = Depends(get_user_principals),
                acls: list = Permission("batch", batch_permission)
        ):
            if not all(has_permission(principals, "edit", item) for item in items):
                raise BatchPermittedException()

    def _get_all(self, *args: Any, **kwargs: Any):

        async def func(request: Request, session: AsyncSession = Depends(self.get_session), ):
            return await self.manager.list(session)

        @self.get(
            path='/',
            response_model=list[self.schema],
            dependencies=[Depends(authenticator.get_user())],
            responses={**missing_token_or_inactive_user_response, **forbidden_response}

        )
        async def filter_operation(
                resources: list[Resource] = Depends(func),
                principals: list = Depends(get_user_principals),
                # acls: list = Permission("batch", AclBatchPermission)
        ):
            return [item for item in resources if has_permission(principals, "view", item)]

    def _get_one(self, *args: Any, **kwargs: Any):
        async def func(request: Request, id: int, session: AsyncSession = Depends(self.get_session)):
            return await self.manager.get_or_404(session, id=id)

        @self.get(
            path='/{id}',
            response_model=self.schema,
            dependencies=[Depends(authenticator.get_user())],
            responses={**missing_token_or_inactive_user_response, **not_found_response,
                       **forbidden_response,
                       }

        )
        async def route(resource=Permission('view', func)):
            return resource

    def _create(self, *args: Any, **kwargs: Any):
        create_schema = self.create_schema

        async def func(request: Request, objs: create_schema, session: AsyncSession = Depends(self.get_session)):
            return await self.manager.create(session, objs)

        @self.post(
            '/',
            response_model=self.schema,
            dependencies=[Depends(authenticator.get_user())],
            responses={**missing_token_or_inactive_user_response, **forbidden_response}
        )
        async def route(resource=Permission('create', func)):
            return resource

    def _update(self, *args: Any, **kwargs: Any):
        update_schema = self.update_schema

        async def func(request: Request, id: int, scheme: update_schema,
                       session: AsyncSession = Depends(self.get_session)):
            model = await self.manager.get_or_404(session, id=id)
            return await self.manager.update(session, model, scheme)

        @self.patch(
            '/{id}',
            response_model=self.schema,
            dependencies=[Depends(authenticator.get_user(superuser=True))],
            responses={**missing_token_or_inactive_user_response, **forbidden_response
                       }
        )
        async def route(resource=Permission('edit', func)):
            return resource

    def _delete_all(self, *args: Any, **kwargs: Any):

        @self.delete(
            '/',
            status_code=status.HTTP_204_NO_CONTENT,
            responses={**auth_responses, **forbidden_response}
        )
        async def route(resource=Permission('delete_all', authenticator.get_user(superuser=True)),
                        session: AsyncSession = Depends(self.get_session)):

            for model in await self.manager.list(session):
                if model.id == resource.id:
                    continue
                await session.delete(model)
            await session.commit()
            return

    def _delete_one(self, *args: Any, **kwargs: Any):

        @self.delete(
            '/{id}',
            status_code=status.HTTP_204_NO_CONTENT,
            responses={**auth_responses, **not_found_response}
        )
        async def route(id: int, session: AsyncSession = Depends(self.get_session),
                        resource=Permission('delete', authenticator.get_user(superuser=True))):
            obj_in_db = await self.manager.get_or_404(session, id=id)
            await self.manager.delete(session, obj_in_db)
            return
