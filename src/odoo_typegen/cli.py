from pathlib import Path

from cyclopts import App

from odoo_typegen.compiler.compiler import Compiler
from odoo_typegen.compiler.environment_compiler import EnvironmentCompiler
from odoo_typegen.compiler.model_compiler import ModelCompiler
from odoo_typegen.emitter.type_emitter import TypeEmitter
from odoo_typegen.registry.registry_service import RegistryService


app = App()


def _generate(
    addon_path: Path,
    output_path: Path,
    odoo_path: Path | None = None,
) -> tuple[Path, ...]:
    registry = RegistryService(addon_path=addon_path).build()
    models = Compiler().compile(registry)
    environment = EnvironmentCompiler(odoo_path=odoo_path).compile(models)
    core_models = ModelCompiler(odoo_path=odoo_path).compile()
    emitter = TypeEmitter(output_path=output_path)

    emitted_files = (
        *emitter.emit(models),
        *emitter.emit_environment(environment),
        *emitter.emit_core_models(core_models),
    )

    for emitted_file in emitted_files:
        print(emitted_file)

    return emitted_files


@app.default
def default(
    addon_path: Path,
    output_path: Path = Path("typings"),
    *,
    odoo_path: Path | None = None,
) -> None:
    """Generate Python stub files for Odoo addons.

    Parameters
    ----------
    addon_path: Path
        Directory containing Odoo addon directories.
    output_path: Path
        Directory where generated .pyi files should be written. Defaults to
        ./typings, which Pyright discovers automatically.
    odoo_path: Path | None
        Optional path to a local Odoo checkout used to overlay core stubs.
    """
    _generate(addon_path, output_path, odoo_path)


@app.command
def generate(
    addon_path: Path,
    output_path: Path = Path("typings"),
    *,
    odoo_path: Path | None = None,
) -> None:
    """Generate Python stub files for Odoo addons.

    Parameters
    ----------
    addon_path: Path
        Directory containing Odoo addon directories.
    output_path: Path
        Directory where generated .pyi files should be written. Defaults to
        ./typings, which Pyright discovers automatically.
    odoo_path: Path | None
        Optional path to a local Odoo checkout used to overlay core stubs.
    """
    _generate(addon_path, output_path, odoo_path)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
