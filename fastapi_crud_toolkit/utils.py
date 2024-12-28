from pydantic import BaseModel
from inspect import signature, Parameter
from fastapi.datastructures import UploadFile
from fastapi import Form
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


class FormBody(BaseModel):

    @classmethod
    def as_form(cls):
        def wrapper(**kwargs):
            return cls(**kwargs)

        _signature = signature(wrapper)

        parameters = []
        for field_name, field in cls.model_fields.items():
            field: FieldInfo
            if getattr(field.annotation, '__args__', False) and UploadFile in field.annotation.__args__:
                default = field.default if field.default is not PydanticUndefined else Parameter.empty
            else:
                default = Form(default=field.default)
            parameters.append(
                Parameter(
                    field_name,
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    default=default,
                    annotation=field.annotation,
                )
            )

        wrapper.__signature__ = _signature.replace(parameters=parameters)
        return wrapper
