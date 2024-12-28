from typing import Callable, Any, Annotated
from fastapi import Depends, UploadFile, Form, HTTPException
from pydantic import ValidationError
from fastapi_crud_toolkit.openapi_responses import bad_request_response, missing_token_or_inactive_user_response, \
    forbidden_response, not_found_response
from ...schemas.users import ReadUser, CreateUser, UpdateUser
from fastapi_crud_toolkit.utils import FormBody
from fastapi_crud_toolkit import MockCrudAPIRouter


class UsersRouter(MockCrudAPIRouter):

    def __init__(self):
        super().__init__(ReadUser, CreateUser, UpdateUser, resource_id='username')

    def _get_one(self):
        @self.get(
            '/{%s}' % self.resource_id,
            response_model=self.read_schema,
            responses={**not_found_response}

        )
        async def func(response=Depends(self.get_or_404())):
            return response

    def _create(self):
        create_schema = self.create_schema

        @self.post(
            '/register',
            response_model=self.read_schema,
            responses={**missing_token_or_inactive_user_response, **forbidden_response, **bad_request_response},
            status_code=201,

        )
        async def func(
                username: Annotated[str, Form()],
                first_name: Annotated[str, Form()],
                last_name: Annotated[str, Form()],
                password: Annotated[str, Form()],
                email: Annotated[str, Form()],
                middle_name: Annotated[str | None, Form()] = None,
                about: Annotated[str | None, Form()] = None,
        ):
            """
            This function is used to create a new user. It takes in the following parameters:
            - username: The username of the user.
            - first_name: The first name of the user.
            - last_name: The last name of the user.
            - password: The password of the user.
            - email: The email of the user.
            - middle_name: The middle name of the user.
            - photo: The photo of the user.
            - session: The database session.

            It returns the created user.
            """
            try:
                user = create_schema(username=username, first_name=first_name, middle_name=middle_name,
                                     last_name=last_name,
                                     email=email, password=password, about=about)
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=e.errors())
            return self.factory.build(**user.model_dump())

    def _me(self):
        update_schema = self.update_schema

        # @self.get('/me', response_model=self.read_schema,
        #           responses={**missing_token_or_inactive_user_response})
        # async def func():
        #     return self.factory.build()

        @self.patch('/me', response_model=ReadUser,
                    responses={**missing_token_or_inactive_user_response, **bad_request_response})
        async def func(
                user=Depends(FormBody.as_form()),
        ):
            """
            This function is used to update the current user. It takes in the following parameters:
            - username: The username of the user.
            - first_name: The first name of the user.
            - last_name: The last name of the user.
            - email: The email of the user.
            - middle_name: The middle name of the user.
            - about: The about of the user.
            - file: The file of the user.
            - session: The database session.
            """

            return self.factory.build(**user.model_dump())

    def _register_routes(self) -> list[Callable[..., Any]]:
        return [self._me]

    def get_or_404(self, *args, **kwargs):
        async def wrapper(username: str):
            return self.factory.build(username=username)

        return wrapper


r = UsersRouter()
