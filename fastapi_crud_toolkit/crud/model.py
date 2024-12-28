from fastapi_sqlalchemy_toolkit import ModelManager
from pydantic import BaseModel
from sqlalchemy import Select, UnaryExpression
from sqlalchemy.orm import InstrumentedAttribute
from starlette import status

from ..openapi_responses import (
    missing_token_or_inactive_user_response, not_found_response, forbidden_response,
)
from typing import Any, TypeVar, Type, Callable
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from .template import CRUDTemplate
from typing import TypeVar

Resource = TypeVar('Resource')


class CrudAPIRouter(CRUDTemplate):

    def __init__(self, read_schema: Type[BaseModel],
                 create_schema: Type[BaseModel], update_schema: Type[BaseModel],
                 manager: ModelManager,
                 get_session: Callable[[], AsyncSession],
                 resource_id: str = 'id',
                 **kwargs: Any):
        super().__init__(read_schema, create_schema, update_schema, resource_id, **kwargs)
        self.manager = manager
        self.get_session = get_session

    def _get_all(self):
        @self.get(
            path='/',
            response_model=list[self.read_schema],

        )
        async def func(request: Request, session: AsyncSession = Depends(self.get_session), ):
            return await self.manager.list(session)

    def _get_one(self):
        @self.get(
            '/{%s}' % self.resource_id,
            response_model=self.read_schema,
            responses={**not_found_response}

        )
        async def func(request: Request, response=Depends(self.get_or_404())):
            return response

    def get_or_404(self,
                   options: list[Any] | Any | None = None,
                   order_by: InstrumentedAttribute | UnaryExpression | None = None,
                   where: Any | None = None,
                   base_stmt: Select | None = None,
                   **simple_filters: Any,
                   ):
        async def wrapper(id: int, session: AsyncSession = Depends(self.get_session)):
            return await self.manager.get_or_404(session, id=id, **simple_filters,
                                                 options=options,
                                                 where=where,
                                                 base_stmt=base_stmt, )

        return wrapper
