from abc import ABC, abstractmethod
from typing import Any, Callable, Type

from fastapi import APIRouter, HTTPException, status
from fastapi_sqlalchemy_toolkit import ModelManager
from pydantic import BaseModel


class CRUDTemplate(APIRouter):

    def __init__(
            self,
            read_schema: Type[BaseModel],
            create_schema: Type[BaseModel],
            update_schema: Type[BaseModel],
            resource_id: str = 'id',
            **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.resource_id = resource_id
        self.read_schema = read_schema
        self.create_schema = create_schema
        self.update_schema = update_schema

        for route in self._register_routes():
            route()

    @abstractmethod
    def _get_all(self) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_one(self) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _create(self) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _patch(self) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_one(self) -> Callable[..., Any]:
        raise NotImplementedError

    def _register_routes(self) -> list[Callable[..., Any]]:
        return [
            self._get_all, self._get_one, self._create, self._patch, self._delete_one
        ]
