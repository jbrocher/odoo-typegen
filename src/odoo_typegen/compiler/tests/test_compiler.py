from pathlib import Path

from odoo_typegen.compiler.consolidated_model import (
    ConsolidatedModel,
    StubClass,
)
from odoo_typegen.compiler.compiler import Compiler
from odoo_typegen.compiler.model_fragment import ModelFragment
from odoo_typegen.compiler.model_index import ModelIndex
from odoo_typegen.compiler.model_member import Attribute, Method
from odoo_typegen.registry.module import Module
from odoo_typegen.registry.registry import Registry


def get_addon_path():
    return Path(__file__).resolve().parents[4] / "tests/test_addons"


def registry_for_addons(addon_path: Path):
    return Registry(
        modules={
            "crm_base_extension": Module(
                name="crm_base_extension",
                path=addon_path / "crm_base_extension",
                manifest=addon_path / "crm_base_extension" / "__manifest__.py",
                depends=(),
            ),
            "crm_second_extension": Module(
                name="crm_second_extension",
                path=addon_path / "crm_second_extension",
                manifest=addon_path / "crm_second_extension" / "__manifest__.py",
                depends=("crm_base_extension",),
            ),
        }
    )


def test_compile_indexes_the_correct_fragments():
    addon_path = get_addon_path()
    registry = registry_for_addons(addon_path)
    compiler = Compiler()
    models = compiler.index_fragments(registry)

    assert models.fragments_for("crm.lead") == (
        ModelFragment(
            module="crm_base_extension",
            addon_dependencies=(),
            file=addon_path / "crm_base_extension/models/crm_lead.py",
            class_name="CrmLead",
            name=None,
            inherits=("crm.lead",),
            line=4,
            attributes=(
                Attribute(
                    name="x_base_code",
                    type="str",
                    module="crm_base_extension",
                    file=addon_path / "crm_base_extension/models/crm_lead.py",
                    line=7,
                ),
                Attribute(
                    name="x_is_priority",
                    type="bool",
                    module="crm_base_extension",
                    file=addon_path / "crm_base_extension/models/crm_lead.py",
                    line=8,
                ),
            ),
            methods=(
                Method(
                    name="action_mark_priority",
                    signature="def action_mark_priority(self) -> None",
                    module="crm_base_extension",
                    file=addon_path / "crm_base_extension/models/crm_lead.py",
                    line=10,
                ),
            ),
        ),
        ModelFragment(
            module="crm_second_extension",
            addon_dependencies=("crm_base_extension",),
            file=addon_path / "crm_second_extension/models/crm_lead.py",
            class_name="CrmLead",
            name=None,
            inherits=("crm.lead",),
            line=4,
            attributes=(
                Attribute(
                    name="x_followup_days",
                    type="int",
                    module="crm_second_extension",
                    file=addon_path / "crm_second_extension/models/crm_lead.py",
                    line=7,
                ),
            ),
            methods=(
                Method(
                    name="action_schedule_followup",
                    signature=(
                        "def action_schedule_followup(self, days: int) -> bool"
                    ),
                    module="crm_second_extension",
                    file=addon_path / "crm_second_extension/models/crm_lead.py",
                    line=9,
                ),
            ),
        ),
    )


def test_compile_indexes_fragments_in_addon_dependency_order():
    addon_path = get_addon_path()
    registry = registry_for_addons(addon_path)
    reversed_registry = Registry(
        modules=dict(reversed(tuple(registry.modules.items())))
    )

    fragments = Compiler().index_fragments(reversed_registry).fragments_for("crm.lead")

    assert tuple(fragment.module for fragment in fragments) == (
        "crm_base_extension",
        "crm_second_extension",
    )


def test_compile_indexes_a_model_declared_without_inheritance(tmp_path):
    addon_path = tmp_path / "library"
    models_path = addon_path / "models"
    models_path.mkdir(parents=True)
    (addon_path / "__init__.py").write_text("from . import models\n")
    (models_path / "__init__.py").write_text("from . import library_book\n")
    model_path = models_path / "library_book.py"
    model_path.write_text(
        "from odoo import models\n\n\n"
        "class LibraryBook(models.Model):\n"
        '    _name = "library.book"\n'
    )
    registry = Registry(
        modules={
            "library": Module(
                name="library",
                path=addon_path,
                manifest=addon_path / "__manifest__.py",
            )
        }
    )

    fragments = Compiler().index_fragments(registry).fragments_for("library.book")

    assert fragments == (
        ModelFragment(
            module="library",
            addon_dependencies=(),
            file=model_path,
            class_name="LibraryBook",
            name="library.book",
            inherits=(),
            line=4,
            attributes=(),
            methods=(),
        ),
    )


def test_consolidate_returns_fields_and_methods_from_fragments(tmp_path):
    addon_path = tmp_path / "unavailable_addons"
    model_index = ModelIndex()
    model_index.add(
        "crm.lead",
        ModelFragment(
            module="crm_base_extension",
            addon_dependencies=(),
            file=addon_path / "crm_base_extension/models/crm_lead.py",
            class_name="CrmLead",
            name=None,
            inherits=("crm.lead",),
            line=4,
            attributes=(
                Attribute(
                    name="x_base_code",
                    type="str",
                    module="crm_base_extension",
                    file=addon_path / "crm_base_extension/models/crm_lead.py",
                    line=7,
                ),
                Attribute(
                    name="x_is_priority",
                    type="bool",
                    module="crm_base_extension",
                    file=addon_path / "crm_base_extension/models/crm_lead.py",
                    line=8,
                ),
            ),
            methods=(
                Method(
                    name="action_mark_priority",
                    signature="def action_mark_priority(self) -> None",
                    module="crm_base_extension",
                    file=addon_path / "crm_base_extension/models/crm_lead.py",
                    line=10,
                ),
            ),
        ),
    )
    model_index.add(
        "crm.lead",
        ModelFragment(
            module="crm_second_extension",
            addon_dependencies=("crm_base_extension",),
            file=addon_path / "crm_second_extension/models/crm_lead.py",
            class_name="CrmLead",
            name=None,
            inherits=("crm.lead",),
            line=4,
            attributes=(
                Attribute(
                    name="x_followup_days",
                    type="int",
                    module="crm_second_extension",
                    file=addon_path / "crm_second_extension/models/crm_lead.py",
                    line=7,
                ),
            ),
            methods=(
                Method(
                    name="action_schedule_followup",
                    signature=(
                        "def action_schedule_followup(self, days: int) -> bool"
                    ),
                    module="crm_second_extension",
                    file=addon_path / "crm_second_extension/models/crm_lead.py",
                    line=9,
                ),
            ),
        ),
    )

    models = Compiler().consolidate(model_index)

    assert models == (
        ConsolidatedModel(
            name="crm.lead",
            stub_class=StubClass(
                import_path="crm.lead",
                class_name="CrmLead",
                bases=("odoo.models.Model",),
                attributes=(
                    Attribute(
                        name="x_base_code",
                        type="str",
                        module="crm_base_extension",
                        file=addon_path / "crm_base_extension/models/crm_lead.py",
                        line=7,
                    ),
                    Attribute(
                        name="x_is_priority",
                        type="bool",
                        module="crm_base_extension",
                        file=addon_path / "crm_base_extension/models/crm_lead.py",
                        line=8,
                    ),
                    Attribute(
                        name="x_followup_days",
                        type="int",
                        module="crm_second_extension",
                        file=addon_path / "crm_second_extension/models/crm_lead.py",
                        line=7,
                    ),
                ),
                methods=(
                    Method(
                        name="action_mark_priority",
                        signature="def action_mark_priority(self) -> None",
                        module="crm_base_extension",
                        file=addon_path / "crm_base_extension/models/crm_lead.py",
                        line=10,
                    ),
                    Method(
                        name="action_schedule_followup",
                        signature="def action_schedule_followup(self, days: int) -> bool",
                        module="crm_second_extension",
                        file=addon_path / "crm_second_extension/models/crm_lead.py",
                        line=9,
                    ),
                ),
            ),
        ),
    )


def test_compile_returns_consolidated_models():
    addon_path = get_addon_path()
    registry = registry_for_addons(addon_path)

    models = Compiler().compile(registry)

    assert models == Compiler().consolidate(Compiler().index_fragments(registry))
