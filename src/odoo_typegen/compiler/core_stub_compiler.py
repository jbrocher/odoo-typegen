from pathlib import Path

import astroid
from astroid import nodes

from odoo_typegen.compiler.consolidated_model import StubAttribute, StubClass, StubMethod


class CoreStubCompiler:
    _ALLOWED_PRIVATE_MEMBERS: set[str] = set()
    _ALLOWED_DUNDERS = {
        "__call__",
        "__contains__",
        "__getitem__",
        "__iter__",
        "__len__",
    }
    _SAFE_TYPES = {
        "Any",
        "None",
        "bool",
        "dict",
        "float",
        "int",
        "list",
        "object",
        "str",
        "tuple",
        "typing.Any",
        "typing.Iterator",
        "typing.Literal",
    }

    def _extract_stub_class(
        self,
        source_file: Path,
        class_name: str,
        import_path: str,
        imports: tuple[str, ...] = (),
        bases: tuple[str, ...] = (),
    ) -> StubClass:
        class_node = self._find_class(source_file, class_name)
        if class_node is None:
            return StubClass(
                import_path=import_path,
                class_name=class_name,
                imports=imports,
                bases=bases,
            )

        return StubClass(
            import_path=import_path,
            class_name=class_name,
            imports=imports,
            bases=bases,
            attributes=self._extract_attributes(class_node),
            methods=self._extract_methods(class_node),
        )

    @staticmethod
    def _find_class(source_file: Path, class_name: str) -> nodes.ClassDef | None:
        if not source_file.is_file():
            return None

        tree = astroid.parse(source_file.read_text())
        for node in tree.body:
            if isinstance(node, nodes.ClassDef) and node.name == class_name:
                return node
        return None

    def _extract_attributes(
        self,
        class_node: nodes.ClassDef,
    ) -> tuple[StubAttribute, ...]:
        attributes: list[StubAttribute] = []

        for statement in class_node.body:
            if isinstance(statement, nodes.AnnAssign):
                name = self._assignment_name(statement.target)
                if name is None or not self._is_public_member(name):
                    continue
                attributes.append(
                    StubAttribute(
                        name=name,
                        type=self._safe_annotation(statement.annotation),
                        line=statement.lineno,
                    )
                )
            elif isinstance(statement, nodes.FunctionDef) and self._is_property(statement):
                if not self._is_public_member(statement.name):
                    continue
                attributes.append(
                    StubAttribute(
                        name=statement.name,
                        type=self._safe_annotation(statement.returns),
                        line=statement.lineno,
                    )
                )

        return tuple(attributes)

    def _extract_methods(self, class_node: nodes.ClassDef) -> tuple[StubMethod, ...]:
        methods: list[StubMethod] = []

        for statement in class_node.body:
            if not isinstance(statement, nodes.FunctionDef):
                continue
            if self._is_property(statement) or not self._is_public_member(statement.name):
                continue

            methods.append(
                StubMethod(
                    name=statement.name,
                    signature=self._method_signature(statement),
                    decorators=self._method_decorators(statement),
                    line=statement.lineno,
                )
            )

        return tuple(methods)

    def _method_signature(self, node: nodes.FunctionDef) -> str:
        return_type = self._safe_annotation(node.returns)
        return f"def {node.name}({self._format_args(node.args)}) -> {return_type}"

    def _format_args(self, args: nodes.Arguments) -> str:
        formatted = args.format_args()
        for annotation in self._annotations_in_args(args):
            if annotation is None:
                continue
            raw_annotation = annotation.as_string()
            safe_annotation = self._safe_annotation(annotation)
            if raw_annotation != safe_annotation:
                formatted = formatted.replace(f": {raw_annotation}", f": {safe_annotation}")
        return formatted

    @staticmethod
    def _annotations_in_args(args: nodes.Arguments) -> tuple[nodes.NodeNG | None, ...]:
        annotations: list[nodes.NodeNG | None] = []
        annotations.extend(args.annotations)
        annotations.extend(args.posonlyargs_annotations)
        annotations.extend(args.kwonlyargs_annotations)
        if args.varargannotation is not None:
            annotations.append(args.varargannotation)
        if args.kwargannotation is not None:
            annotations.append(args.kwargannotation)
        return tuple(annotations)

    def _safe_annotation(self, annotation: nodes.NodeNG | None) -> str:
        if annotation is None:
            return "typing.Any"

        rendered = annotation.as_string()
        if self._is_safe_annotation(rendered):
            return rendered
        return "typing.Any"

    def _is_safe_annotation(self, rendered: str) -> bool:
        cleaned = (
            rendered.replace(" | ", "|")
            .replace("[", "|")
            .replace("]", "|")
            .replace(",", "|")
            .replace("'", "")
            .replace('"', "")
        )
        parts = {
            part.strip()
            for part in cleaned.split("|")
            if part.strip()
        }
        return all(
            part in self._SAFE_TYPES
            or part.startswith("typing.")
            or part in {"True", "False"}
            for part in parts
        )

    def _is_public_member(self, name: str) -> bool:
        return (
            not name.startswith("_")
            or name in self._ALLOWED_DUNDERS
            or name in self._ALLOWED_PRIVATE_MEMBERS
        )

    @staticmethod
    def _assignment_name(node: nodes.NodeNG) -> str | None:
        if isinstance(node, nodes.AssignName):
            return node.name
        return None

    @staticmethod
    def _is_property(node: nodes.FunctionDef) -> bool:
        for decorator in node.decorators.nodes if node.decorators is not None else ():
            if isinstance(decorator, nodes.Name) and decorator.name == "property":
                return True
            if (
                isinstance(decorator, nodes.Attribute)
                and decorator.attrname == "cached_property"
            ):
                return True
        return False

    @staticmethod
    def _method_decorators(node: nodes.FunctionDef) -> tuple[str, ...]:
        decorators: list[str] = []
        for decorator in node.decorators.nodes if node.decorators is not None else ():
            if isinstance(decorator, nodes.Attribute):
                name = decorator.as_string()
            elif isinstance(decorator, nodes.Name):
                name = decorator.name
            else:
                continue
            if name in {"typing.overload", "overload"}:
                decorators.append("@typing.overload")
        return tuple(decorators)
