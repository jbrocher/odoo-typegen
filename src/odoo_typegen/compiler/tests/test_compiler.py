from pathlib import Path

from odoo_typegen.compiler.consolidated_model import (
    ConsolidatedModel,
    StubAttribute,
    StubClass,
    StubMethod,
)
from odoo_typegen.compiler.compiler import Compiler
from odoo_typegen.compiler.model_fragment import ModelFragment
from odoo_typegen.compiler.model_index import ModelIndex
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
            file=addon_path / "crm_base_extension/models/crm_lead.py",
            class_name="CrmLead",
            name=None,
            inherits=("crm.lead",),
            line=4,
        ),
        ModelFragment(
            module="crm_second_extension",
            file=addon_path / "crm_second_extension/models/crm_lead.py",
            class_name="CrmLead",
            name=None,
            inherits=("crm.lead",),
            line=4,
        ),
    )


def test_consolidate_returns_fields_and_methods_from_fragments():
    addon_path = get_addon_path()
    model_index = ModelIndex()
    model_index.add(
        "crm.lead",
        ModelFragment(
            module="crm_base_extension",
            file=addon_path / "crm_base_extension/models/crm_lead.py",
            class_name="CrmLead",
            name=None,
            inherits=("crm.lead",),
            line=4,
        ),
    )
    model_index.add(
        "crm.lead",
        ModelFragment(
            module="crm_second_extension",
            file=addon_path / "crm_second_extension/models/crm_lead.py",
            class_name="CrmLead",
            name=None,
            inherits=("crm.lead",),
            line=4,
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
                    StubAttribute(
                        name="x_base_code",
                        type="str",
                        module="crm_base_extension",
                        file=addon_path / "crm_base_extension/models/crm_lead.py",
                        line=7,
                    ),
                    StubAttribute(
                        name="x_is_priority",
                        type="bool",
                        module="crm_base_extension",
                        file=addon_path / "crm_base_extension/models/crm_lead.py",
                        line=8,
                    ),
                    StubAttribute(
                        name="x_followup_days",
                        type="int",
                        module="crm_second_extension",
                        file=addon_path / "crm_second_extension/models/crm_lead.py",
                        line=7,
                    ),
                ),
                methods=(
                    StubMethod(
                        name="action_mark_priority",
                        signature="def action_mark_priority(self) -> None",
                        module="crm_base_extension",
                        file=addon_path / "crm_base_extension/models/crm_lead.py",
                        line=10,
                    ),
                    StubMethod(
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
