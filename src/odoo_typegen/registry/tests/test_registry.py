from pathlib import Path

import pytest

from odoo_typegen.registry.module import Module
from odoo_typegen.registry.registry import Registry
from odoo_typegen.registry.registry_service import RegistryService


@pytest.fixture(name="cwd")
def cwd_fixture():
    return Path(__file__).resolve().parents[4]


def test_registry_service_builds_the_correct_registry(cwd):
    addon_path = cwd / Path("tests/test_addons")
    service = RegistryService(addon_path=addon_path)
    expected_registry = Registry(
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

    registry = service.build()
    assert registry == expected_registry
    assert registry.get_dependencies() == {
        "crm_base_extension": (),
        "crm_second_extension": ("crm_base_extension",),
    }
