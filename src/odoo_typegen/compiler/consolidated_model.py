import pydantic

from odoo_typegen.compiler.model_member import Attribute, Method


class StubClass(pydantic.BaseModel):
    import_path: str
    class_name: str
    imports: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()
    attributes: tuple[Attribute, ...] = ()
    methods: tuple[Method, ...] = ()


class ConsolidatedModel(pydantic.BaseModel):
    name: str
    stub_class: StubClass
