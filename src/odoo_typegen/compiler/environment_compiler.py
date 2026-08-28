from pathlib import Path

from odoo_typegen.compiler.consolidated_model import ConsolidatedModel, StubClass, StubMethod
from odoo_typegen.compiler.core_stub_compiler import CoreStubCompiler


class EnvironmentCompiler(CoreStubCompiler):
    def __init__(self, odoo_path: Path | None = None):
        self._odoo_path = odoo_path

    def compile(self, models: tuple[ConsolidatedModel, ...]) -> StubClass:
        stub_class = self._extract_stub_class(
            source_file=self._source_file(),
            class_name="Environment",
            import_path="odoo.orm.environments",
            imports=self._imports_for(models),
        )

        methods = tuple(
            method
            for method in stub_class.methods
            if method.name != "__getitem__"
        )

        return stub_class.model_copy(
            update={
                "methods": (
                    *methods,
                    *self._getitem_overloads(models),
                ),
            }
        )

    def _source_file(self) -> Path:
        if self._odoo_path is None:
            return Path()
        return self._odoo_path / "odoo/orm/environments.py"

    @staticmethod
    def _imports_for(models: tuple[ConsolidatedModel, ...]) -> tuple[str, ...]:
        imports = ["import typing"]
        imports.extend(
            f"from {model.stub_class.import_path} import {model.stub_class.class_name}"
            for model in models
        )
        return tuple(imports)

    @staticmethod
    def _getitem_overloads(
        models: tuple[ConsolidatedModel, ...],
    ) -> tuple[StubMethod, ...]:
        overloads: list[StubMethod] = []
        for model in models:
            overloads.append(
                StubMethod(
                    name="__getitem__",
                    decorators=("@typing.overload",),
                    signature=(
                        "def __getitem__("
                        "self, "
                        f"model_name: typing.Literal[\"{model.name}\"]"
                        f") -> {model.stub_class.class_name}"
                    ),
                )
            )

        overloads.append(
            StubMethod(
                name="__getitem__",
                decorators=("@typing.overload",),
                signature="def __getitem__(self, model_name: str) -> typing.Any",
            )
        )
        return tuple(overloads)
