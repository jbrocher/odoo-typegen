from odoo_typegen.compiler.consolidated_model import ConsolidatedModel, StubAttribute, StubClass, StubMethod
from odoo_typegen.compiler.environment_compiler import EnvironmentCompiler


def test_environment_compiler_extracts_public_members_and_adds_model_overloads(
    tmp_path,
):
    environment_source = tmp_path / "odoo/orm/environments.py"
    environment_source.parent.mkdir(parents=True)
    environment_source.write_text(
        "\n".join(
            [
                "import functools",
                "import typing",
                "",
                "class Environment:",
                "    uid: int",
                "    su: bool",
                "    cr: BaseCursor",
                "    _private: str",
                "",
                "    def __getitem__(self, model_name: str) -> BaseModel:",
                "        ...",
                "",
                "    def is_superuser(self) -> bool:",
                "        ...",
                "",
                "    @functools.cached_property",
                "    def user(self) -> BaseModel:",
                "        ...",
                "",
            ]
        )
    )
    models = (
        ConsolidatedModel(
            name="crm.lead",
            stub_class=StubClass(
                import_path="crm.lead",
                class_name="CrmLead",
            ),
        ),
    )

    environment = EnvironmentCompiler(odoo_path=tmp_path).compile(models)

    assert environment == StubClass(
        import_path="odoo.orm.environments",
        class_name="Environment",
        imports=("import typing", "from crm.lead import CrmLead"),
        attributes=(
            StubAttribute(name="uid", type="int", line=5),
            StubAttribute(name="su", type="bool", line=6),
            StubAttribute(name="cr", type="typing.Any", line=7),
            StubAttribute(name="user", type="typing.Any", line=16),
        ),
        methods=(
            StubMethod(
                name="is_superuser",
                signature="def is_superuser(self) -> bool",
                line=13,
            ),
            StubMethod(
                name="__getitem__",
                signature=(
                    "def __getitem__(self, "
                    'model_name: typing.Literal["crm.lead"]) -> CrmLead'
                ),
                decorators=("@typing.overload",),
            ),
            StubMethod(
                name="__getitem__",
                signature="def __getitem__(self, model_name: str) -> typing.Any",
                decorators=("@typing.overload",),
            ),
        ),
    )


def test_environment_compiler_without_odoo_path_still_adds_model_overloads():
    models = (
        ConsolidatedModel(
            name="crm.lead",
            stub_class=StubClass(
                import_path="crm.lead",
                class_name="CrmLead",
            ),
        ),
    )

    environment = EnvironmentCompiler().compile(models)

    assert environment == StubClass(
        import_path="odoo.orm.environments",
        class_name="Environment",
        imports=("import typing", "from crm.lead import CrmLead"),
        methods=(
            StubMethod(
                name="__getitem__",
                signature=(
                    "def __getitem__(self, "
                    'model_name: typing.Literal["crm.lead"]) -> CrmLead'
                ),
                decorators=("@typing.overload",),
            ),
            StubMethod(
                name="__getitem__",
                signature="def __getitem__(self, model_name: str) -> typing.Any",
                decorators=("@typing.overload",),
            ),
        ),
    )
