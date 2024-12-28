from abc import ABC, abstractmethod

from pydantic import BaseModel
from ..openapi_responses import (
    missing_token_or_inactive_user_response, not_found_response, forbidden_response,
)
from typing import Any, Type, Callable
from fastapi import Request, Depends, Response, status
from polyfactory.factories.pydantic_factory import ModelFactory
from .template import CRUDTemplate


class MockCrudAPIRouter(ABC, CRUDTemplate):

    def __init__(self, read_schema: Type[BaseModel],
                 create_schema: Type[BaseModel], update_schema: Type[BaseModel],
                 resource_id: str = 'id',
                 **kwargs: Any):
        super().__init__(read_schema, create_schema, update_schema, resource_id, **kwargs)  # type: ignore
        self.factory: ModelFactory = ModelFactory.create_factory(read_schema)

    def _get_all(self):
        @self.get(
            path='/',
            response_model=list[self.read_schema],

        )
        async def func(request: Request):
            return self.factory.batch(10)

    def _patch(self):
        patch_schema = self.update_schema

        @self.patch('/{%s}' % self.resource_id, response_model=self.read_schema)
        async def func(
                obj: patch_schema,
                resource=Depends(self.get_or_404()),
        ):
            model = {**obj.model_dump(), **resource.model_dump()}
            return self.factory.build(**model)

    def _get_one(self):
        @self.get(
            '/{%s}' % self.resource_id,
            response_model=self.read_schema,
            responses={**not_found_response}

        )
        async def func(response=Depends(self.get_or_404())):
            return response

    def _delete_one(self):
        @self.delete(
            '/{%s}' % self.resource_id,
            response_model=self.read_schema,
            responses={**not_found_response}

        )
        async def func(response=Depends(self.get_or_404())):
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    @abstractmethod
    def get_or_404(self, *args, **kwargs):
        ...

    def _create(self):
        create_schema = self.create_schema

        @self.post(
            '/',
            response_model=self.read_schema,
            responses={**missing_token_or_inactive_user_response, **forbidden_response}
        )
        async def func(request: Request, objs: create_schema):
            return self.factory.build(**objs.model_dump())
