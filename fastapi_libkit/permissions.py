from fastapi_permissions import has_permission
from typing import TypeVar
from fastapi_libkit.exceptions import BatchPermittedException

# check that fastapi permission is installed: pip install fastapi-permissions


Resource = TypeVar('Resource')


async def atomic_operation(
        principals: list,
        items: list[Resource],
        requested_permission: str
):
    if not all(has_permission(principals, requested_permission, item) for item in items):
        raise BatchPermittedException()


async def filter_operation(
        resources: list[Resource],
        principals: list,
        requested_permission: str,
):
    return [item for item in resources if has_permission(principals, requested_permission, item)]
