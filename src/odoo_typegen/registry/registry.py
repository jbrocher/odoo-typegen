from collections.abc import Iterator, MutableMapping
from graphlib import TopologicalSorter

from odoo_typegen.registry.module import Module


class Registry(MutableMapping[str, Module]):
    def __init__(self, modules: dict[str, Module] | None = None):
        self.modules = modules or {}

    def __iter__(self) -> Iterator[str]:
        return iter(self.modules)

    def __len__(self) -> int:
        return len(self.modules)

    def __getitem__(self, name: str) -> Module:
        return self.modules[name]

    def __setitem__(self, name: str, module: Module) -> None:
        self.modules[name] = module

    def __delitem__(self, name: str) -> None:
        del self.modules[name]

    def get_dependencies(self) -> dict[str, tuple[str, ...]]:
        return {
            name: module.depends
            for name, module in self.modules.items()
        }

    def modules_in_dependency_order(self) -> tuple[Module, ...]:
        dependencies = {
            name: tuple(
                dependency
                for dependency in module.depends
                if dependency in self.modules
            )
            for name, module in self.modules.items()
        }
        module_names = TopologicalSorter(dependencies).static_order()
        return tuple(self.modules[name] for name in module_names)
