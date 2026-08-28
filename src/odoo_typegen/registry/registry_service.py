from pathlib import Path

import astroid
from astroid import nodes

from odoo_typegen.registry.module import Module
from odoo_typegen.registry.registry import Registry


class RegistryService:
    def __init__(self, addon_path: Path):
        self._addon_path = addon_path

    @staticmethod
    def _get_manifest_path(dir: Path) -> Path | None:
        if not dir.is_dir():
            return None

        for file in dir.iterdir():
            if file.name == "__manifest__.py":
                return file
        return None

    @staticmethod
    def _parse_manifest(manifest_path: Path) -> dict[str, object]:
        module = astroid.parse(manifest_path.read_text())
        if not module.body:
            raise ValueError(f"Manifest is empty: {manifest_path}")

        manifest_node = module.body[0]
        if not isinstance(manifest_node, nodes.Expr):
            raise ValueError(f"Manifest must be a dictionary expression: {manifest_path}")

        value_node = manifest_node.value
        if not isinstance(value_node, nodes.Dict):
            raise ValueError(f"Manifest must be a dictionary expression: {manifest_path}")

        manifest: dict[str, object] = {}
        for key_node, item_node in value_node.items:
            if not (
                isinstance(key_node, nodes.Const)
                and isinstance(key_node.value, str)
            ):
                raise ValueError(f"Manifest keys must be string literals: {manifest_path}")

            if key_node.value == "depends":
                manifest["depends"] = RegistryService._parse_manifest_depends(
                    item_node,
                    manifest_path,
                )

        return manifest

    @staticmethod
    def _parse_manifest_depends(
        depends_node: nodes.NodeNG,
        manifest_path: Path,
    ) -> tuple[str, ...]:
        if not isinstance(depends_node, nodes.List | nodes.Tuple):
            raise ValueError(f"Manifest depends must be a list or tuple: {manifest_path}")

        depends: list[str] = []
        for dependency_node in depends_node.elts:
            if not (
                isinstance(dependency_node, nodes.Const)
                and isinstance(dependency_node.value, str)
            ):
                raise ValueError(
                    f"Manifest depends entries must be string literals: {manifest_path}"
                )
            depends.append(dependency_node.value)

        return tuple(depends)

    def build(self) -> Registry:
        registry = Registry()
        for dir in self._addon_path.iterdir():
            manifest_path = self._get_manifest_path(dir)
            if manifest_path is not None:
                manifest = self._parse_manifest(manifest_path)
                registry[dir.name] = Module(
                    name=dir.name,
                    path=dir,
                    manifest=manifest_path,
                    depends=manifest.get("depends", ()),
                )
        return registry
