from odoo_typegen.compiler.consolidated_model import StubAttribute, StubClass, StubMethod
from odoo_typegen.compiler.model_compiler import ModelCompiler


def test_model_compiler_extracts_base_model_and_model(tmp_path):
    model_source = tmp_path / "odoo/orm/models.py"
    model_source.parent.mkdir(parents=True)
    model_source.write_text(
        "\n".join(
            [
                "class BaseModel:",
                "    _name: str",
                "    display_name: str",
                "",
                "    def browse(self, ids: list[int]) -> BaseModel:",
                "        ...",
                "",
                "    @property",
                "    def ids(self) -> list[int]:",
                "        ...",
                "",
                "class Model(BaseModel):",
                "    _auto: bool",
                "    _register: bool",
                "    _abstract: typing.Literal[False]",
                "",
            ]
        )
    )

    core_models = ModelCompiler(odoo_path=tmp_path).compile()

    assert core_models == (
        StubClass(
            import_path="odoo.orm.models",
            class_name="BaseModel",
            imports=("import typing", "from odoo.orm.environments import Environment"),
            attributes=(
                StubAttribute(name="env", type="Environment"),
                StubAttribute(name="_name", type="str", line=2),
                StubAttribute(name="display_name", type="str", line=3),
                StubAttribute(name="ids", type="list[int]", line=8),
            ),
            methods=(
                StubMethod(
                    name="browse",
                    signature="def browse(self, ids: list[int]) -> typing.Any",
                    line=5,
                ),
            ),
        ),
        StubClass(
            import_path="odoo.orm.models",
            class_name="Model",
            imports=("import typing",),
            bases=("odoo.orm.models.BaseModel",),
            attributes=(
                StubAttribute(name="_auto", type="bool", line=13),
                StubAttribute(name="_register", type="bool", line=14),
                StubAttribute(name="_abstract", type="typing.Literal[False]", line=15),
            ),
        ),
    )


def test_model_compiler_without_odoo_path_still_emits_base_model_and_model():
    core_models = ModelCompiler().compile()

    assert core_models == (
        StubClass(
            import_path="odoo.orm.models",
            class_name="BaseModel",
            imports=("import typing", "from odoo.orm.environments import Environment"),
            attributes=(
                StubAttribute(name="env", type="Environment"),
            ),
        ),
        StubClass(
            import_path="odoo.orm.models",
            class_name="Model",
            imports=("import typing",),
            bases=("odoo.orm.models.BaseModel",),
        ),
    )
