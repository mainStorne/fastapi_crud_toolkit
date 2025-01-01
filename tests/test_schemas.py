from functools import reduce
from pydantic import BaseModel
from fastapi import UploadFile, Depends
from fastapi.applications import get_openapi as _get_openapi
from fastapi_libkit import FormBodyMixin
from fastapi.routing import APIRoute


def get_openapi(routes: list[APIRoute]):
    return _get_openapi(
        title='app.title',
        version='4.2.0',
        routes=routes
    )


def assert_multipart_form_data_and_return_component(openapi: dict, path_name: str = '') -> dict:
    register_path = openapi['paths'][path_name]
    request_content = register_path['post']['requestBody']['content']
    request_content: dict
    assert (len(request_content) == 1
            and request_content['multipart/form-data']), "Multipart/form-data is not in openapi schema!"
    ref = request_content['multipart/form-data']['schema']['$ref'][2:]  # get only ref for component
    component = reduce(lambda x, y: x[y], [openapi, *ref.split('/')])  # get component from openapi
    component: dict
    return component


class Example(BaseModel):
    name: str


class OneRequiredFile(FormBodyMixin, Example):
    file: UploadFile


def router_factory(model: type[FormBodyMixin], path_name: str = '', methods: list[str] = ['POST']):
    async def endpoint(obj=Depends(model.as_form())):
        pass

    return APIRoute(path_name, endpoint, methods=methods)


one_required_file_route = router_factory(OneRequiredFile)


def test_generated_schema_on_one_required_file():
    openapi = get_openapi([one_required_file_route])
    component = assert_multipart_form_data_and_return_component(openapi, '')
    assert len(component['properties']) == 2
    prop = component['properties']['file']
    assert prop['type'] == 'string'
    assert prop['format'] == 'binary'


class OneOptionalFile(FormBodyMixin, Example):
    file: UploadFile | None = None


one_optional_file_route = router_factory(OneOptionalFile)


def test_generated_schema_on_one_optional_file():
    openapi = get_openapi([one_optional_file_route])
    component = assert_multipart_form_data_and_return_component(openapi, '')
    prop = component['properties']['file']
    any_of = prop['anyOf']
    assert len(any_of) == 2
    assert {'format': 'binary', 'type': 'string'} in any_of and {'type': 'null'} in any_of


class ManyOptionalFiles(FormBodyMixin, Example):
    files: list[UploadFile] | None


many_optional_files_route = router_factory(ManyOptionalFiles)


def test_generated_schema_on_many_optional_files():
    openapi = get_openapi([many_optional_files_route])
    component = assert_multipart_form_data_and_return_component(openapi)
    prop = component['properties']['files']
    any_of = {'anyOf': [{'type': 'array', "items": {'type': 'string', 'format': 'binary'}},
                        {'type': 'null'}]}
    assert prop['anyOf'] == any_of['anyOf']


class ManyRequiredFiles(FormBodyMixin, Example):
    files: list[UploadFile]


many_required_files_route = router_factory(ManyRequiredFiles)


def test_generated_schema_on_many_required_files():
    openapi = get_openapi([many_required_files_route])
    component = assert_multipart_form_data_and_return_component(openapi)
    prop = component['properties']['files']
    assert prop['type'] == 'array'
    assert prop["items"] == {'type': 'string', 'format': 'binary'}


class AllFiles(FormBodyMixin, Example):
    file: UploadFile
    files: list[UploadFile]
    optional_file: UploadFile | None = None
    optional_files: list[UploadFile] | None = None

all_files_route = router_factory(AllFiles)


def test_generated_schema_on_all_files():
    openapi = get_openapi([all_files_route])
    component = assert_multipart_form_data_and_return_component(openapi)
    for prop_name, prop in component['properties'].items():
        prop: dict
        if prop_name == 'file':
            assert prop['type'] == 'string'
            assert prop['format'] == 'binary'
        elif prop_name == 'files':
            assert prop['type'] == 'array'
            items = prop.get('items', None)
            items: dict | None
            assert items is not None
            assert items['type'] == 'string'
            assert items['format'] == 'binary'
        elif prop_name == 'optional_file':
            any_of = prop['anyOf']
            assert len(any_of) == 2
            assert {'format': 'binary', 'type': 'string'} in any_of and {'type': 'null'} in any_of

        elif prop_name == 'optional_files':
            any_of = prop['anyOf']
            assert len(any_of) == 2
            assert {'type': 'array', "items": {'type': 'string', 'format': 'binary'}} in any_of and {
                'type': 'null'} in any_of

    assert 'file' in component['required'] and 'files' in component['required']
