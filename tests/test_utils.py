import pytest
from fastapi import UploadFile, Request
from fastapi.datastructures import FormData
from io import BytesIO
from pydantic import ValidationError
from fastapi_crud_toolkit import FormBody


class Model(FormBody):
    file1: UploadFile | None = None
    num: int | None = None
    name: str | None
    file2: UploadFile


def test_make_formbody():
    data = FormData(name='dima', file2=UploadFile(BytesIO(b'hello')))
    wrong_data = FormData(name=1, file1=None)

    file2 = BytesIO()
    Model.as_form()(**data)
    Model.model_json_schema()
    with pytest.raises(ValidationError):
        Model.as_form()(**wrong_data)
