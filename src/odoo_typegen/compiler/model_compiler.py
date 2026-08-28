from pathlib import Path

from odoo_typegen.compiler.consolidated_model import StubAttribute, StubClass
from odoo_typegen.compiler.core_stub_compiler import CoreStubCompiler


class ModelCompiler(CoreStubCompiler):
    _ALLOWED_PRIVATE_MEMBERS = {
        "_abstract",
        "_active_name",
        "_auto",
        "_custom",
        "_description",
        "_fields",
        "_fields__",
        "_fold_name",
        "_inherit",
        "_inherit_children",
        "_inherits",
        "_module",
        "_name",
        "_order",
        "_parent_name",
        "_parent_store",
        "_rec_name",
        "_rec_names_search",
        "_register",
        "_table",
        "_table_objects",
        "_table_query",
        "_transient",
        "_translate",
    }

    def __init__(self, odoo_path: Path | None = None):
        self._odoo_path = odoo_path

    def compile(self) -> tuple[StubClass, ...]:
        return (
            self._compile_base_model(),
            self._compile_model(),
        )

    def _compile_base_model(self) -> StubClass:
        base_model = self._extract_stub_class(
            source_file=self._source_file(),
            class_name="BaseModel",
            import_path="odoo.orm.models",
            imports=("import typing", "from odoo.orm.environments import Environment"),
        )
        attributes = tuple(
            attribute
            for attribute in base_model.attributes
            if attribute.name != "env"
        )

        return base_model.model_copy(
            update={
                "attributes": (
                    StubAttribute(name="env", type="Environment"),
                    *attributes,
                )
            }
        )

    def _compile_model(self) -> StubClass:
        model = self._extract_stub_class(
            source_file=self._source_file(),
            class_name="Model",
            import_path="odoo.orm.models",
            imports=("import typing",),
            bases=("odoo.orm.models.BaseModel",),
        )
        return model

    def _source_file(self) -> Path:
        if self._odoo_path is None:
            return Path()
        return self._odoo_path / "odoo/orm/models.py"
