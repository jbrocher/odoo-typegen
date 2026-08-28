import logging
from pathlib import Path

import pytest

from odoo_typegen.compiler.consolidated_model import ConsolidatedModel, StubClass
from odoo_typegen.compiler.environment_compiler import EnvironmentCompiler
from odoo_typegen.compiler.model_compiler import ModelCompiler
from odoo_typegen.emitter.type_emitter import TypeEmitter

logger = logging.getLogger(__name__)


@pytest.mark.integration
def test_emitter_preserves_local_odoo_environment_and_adds_model_overloads(
    tmp_path,
):
    odoo_path = Path(__file__).resolve().parents[1] / ".odoo_path"
    logger.warning("Using odoo_path=%s", odoo_path)
    models = (
        ConsolidatedModel(
            name="crm.lead",
            stub_class=StubClass(
                import_path="crm.lead",
                class_name="CrmLead",
                bases=("odoo.models.Model",),
            ),
        ),
    )

    emitter = TypeEmitter(output_path=tmp_path)
    emitted_environment_files = emitter.emit_environment(
        EnvironmentCompiler(odoo_path=odoo_path).compile(models)
    )
    core_model_files = emitter.emit_core_models(
        ModelCompiler(odoo_path=odoo_path).compile()
    )

    assert emitted_environment_files == (
        tmp_path / "odoo/orm/environments.pyi",
        tmp_path / "odoo/api/__init__.pyi",
    )
    assert core_model_files == (
        tmp_path / "odoo/orm/models.pyi",
        tmp_path / "odoo/models/__init__.pyi",
    )
    emitted_environment = (tmp_path / "odoo/orm/environments.pyi").read_text()
    assert "uid: int" in emitted_environment
    assert "def is_superuser(self) -> bool: ..." in emitted_environment
    assert 'model_name: typing.Literal["crm.lead"]' in emitted_environment
    assert ") -> CrmLead: ..." in emitted_environment
    assert (tmp_path / "odoo/api/__init__.pyi").read_text() == (
        "from odoo.orm.environments import Environment as Environment\n"
    )
    emitted_base_model = (tmp_path / "odoo/orm/models.pyi").read_text()
    assert "env: Environment" in emitted_base_model
    assert "_name: str" in emitted_base_model
    assert "class Model(BaseModel):" in emitted_base_model
    assert "_auto: bool" in emitted_base_model
    assert "def browse(" in emitted_base_model
    assert (tmp_path / "odoo/models/__init__.pyi").read_text() == (
        "from odoo.orm.models import BaseModel as BaseModel\n"
        "from odoo.orm.models import Model as Model\n"
    )
