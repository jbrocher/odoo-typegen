from pathlib import Path

import astroid
from astroid import nodes
from pydantic import ValidationError

from odoo_typegen.compiler.consolidated_model import (
    ConsolidatedModel,
    StubClass,
)
from odoo_typegen.compiler.model_fragment import ModelFragment
from odoo_typegen.compiler.model_index import ModelIndex
from odoo_typegen.compiler.model_member import Attribute, Method
from odoo_typegen.registry.module import Module
from odoo_typegen.registry.registry import Registry


class Compiler:
    _FIELD_TYPES = {
        "Char": "str",
        "Text": "str",
        "Selection": "str",
        "Boolean": "bool",
        "Integer": "int",
        "Float": "float",
        "Monetary": "float",
    }

    def compile(self, registry: Registry) -> tuple[ConsolidatedModel, ...]:
        return self.consolidate(self.index_fragments(registry))

    def index_fragments(self, registry: Registry) -> ModelIndex:
        index = ModelIndex()
        for module in registry.values():
            for fragment in self._compile_module(module):
                index.add(fragment.effective_name, fragment)
        return index

    def consolidate(self, model_index: ModelIndex) -> tuple[ConsolidatedModel, ...]:
        models: list[ConsolidatedModel] = []
        for model_name, fragments in model_index.items():
            attributes: list[Attribute] = []
            methods: list[Method] = []

            for fragment in fragments:
                attributes.extend(fragment.attributes)
                methods.extend(fragment.methods)

            models.append(
                ConsolidatedModel(
                    name=model_name,
                    stub_class=StubClass(
                        import_path=model_name,
                        class_name=self._class_name_for_model(model_name),
                        bases=("odoo.models.Model",),
                        attributes=tuple(attributes),
                        methods=tuple(methods),
                    ),
                )
            )

        return tuple(models)

    def _compile_module(self, module: Module) -> tuple[ModelFragment, ...]:
        return self._compile_python_file(
            module=module,
            file=module.path / "__init__.py",
            seen=set(),
        )

    def _compile_python_file(
        self,
        module: Module,
        file: Path,
        seen: set[Path],
    ) -> tuple[ModelFragment, ...]:
        if file in seen or not file.exists():
            return ()

        seen.add(file)
        tree = astroid.parse(file.read_text())
        fragments = list(self._extract_model_fragments(module, file, tree))

        for imported_file in self._resolve_local_imports(file, tree):
            fragments.extend(self._compile_python_file(module, imported_file, seen))

        return tuple(fragments)

    def _resolve_local_imports(
        self,
        file: Path,
        tree: nodes.Module,
    ) -> tuple[Path, ...]:
        imported_files: list[Path] = []
        package_path = file.parent

        for node in tree.body:
            if not isinstance(node, nodes.ImportFrom) or node.level != 1:
                continue

            for imported_name, _alias in node.names:
                if imported_name == "*":
                    continue

                package_import = package_path / imported_name / "__init__.py"
                module_import = package_path / f"{imported_name}.py"
                if package_import.exists():
                    imported_files.append(package_import)
                elif module_import.exists():
                    imported_files.append(module_import)

        return tuple(imported_files)

    def _extract_model_fragments(
        self,
        module: Module,
        file: Path,
        tree: nodes.Module,
    ) -> tuple[ModelFragment, ...]:
        fragments: list[ModelFragment] = []

        for node in tree.body:
            if not isinstance(node, nodes.ClassDef):
                continue

            name = None
            inherits: tuple[str, ...] = ()
            for statement in node.body:
                if not isinstance(statement, nodes.Assign):
                    continue

                for target in statement.targets:
                    if not isinstance(target, nodes.AssignName):
                        continue
                    if target.name == "_name":
                        name = self._parse_string_literal(statement.value)
                    elif target.name == "_inherit":
                        inherits = self._parse_string_collection(statement.value)
            try:
                fragment = ModelFragment(
                    module=module.name,
                    addon_dependencies=module.depends,
                    file=file,
                    class_name=node.name,
                    name=name,
                    inherits=inherits,
                    line=node.lineno,
                    attributes=self._extract_fields(module.name, file, node),
                    methods=self._extract_methods(module.name, file, node),
                )
            except ValidationError:
                continue

            fragments.append(fragment)

        return tuple(fragments)

    @staticmethod
    def _parse_string_literal(node: nodes.NodeNG) -> str | None:
        if isinstance(node, nodes.Const) and isinstance(node.value, str):
            return node.value
        return None

    def _parse_string_collection(self, node: nodes.NodeNG) -> tuple[str, ...]:
        literal = self._parse_string_literal(node)
        if literal is not None:
            return (literal,)

        if not isinstance(node, nodes.List | nodes.Tuple):
            return ()

        values: list[str] = []
        for item in node.elts:
            literal = self._parse_string_literal(item)
            if literal is None:
                return ()
            values.append(literal)

        return tuple(values)

    def _extract_fields(
        self,
        module: str,
        file: Path,
        class_node: nodes.ClassDef,
    ) -> tuple[Attribute, ...]:
        fields: list[Attribute] = []

        for statement in class_node.body:
            if not isinstance(statement, nodes.Assign):
                continue

            field_type = self._parse_field_type(statement.value)
            if field_type is None:
                continue

            for target in statement.targets:
                if not isinstance(target, nodes.AssignName):
                    continue
                fields.append(
                    Attribute(
                        name=target.name,
                        type=field_type,
                        module=module,
                        file=file,
                        line=statement.lineno,
                    )
                )

        return tuple(fields)

    def _extract_methods(
        self,
        module: str,
        file: Path,
        class_node: nodes.ClassDef,
    ) -> tuple[Method, ...]:
        methods: list[Method] = []

        for statement in class_node.body:
            if not isinstance(statement, nodes.FunctionDef):
                continue

            methods.append(
                Method(
                    name=statement.name,
                    signature=self._method_signature(statement),
                    module=module,
                    file=file,
                    line=statement.lineno,
                )
            )

        return tuple(methods)

    def _parse_field_type(self, node: nodes.NodeNG) -> str | None:
        if not isinstance(node, nodes.Call):
            return None

        func = node.func
        if not (
            isinstance(func, nodes.Attribute)
            and isinstance(func.expr, nodes.Name)
            and func.expr.name == "fields"
        ):
            return None

        return self._FIELD_TYPES.get(func.attrname, "Any")

    @staticmethod
    def _method_signature(node: nodes.FunctionDef) -> str:
        return_type = "Any"
        if node.returns is not None:
            return_type = node.returns.as_string()

        return f"def {node.name}({node.args.format_args()}) -> {return_type}"

    @staticmethod
    def _class_name_for_model(model_name: str) -> str:
        return "".join(
            part.capitalize()
            for part in model_name.replace("_", ".").split(".")
            if part
        )
