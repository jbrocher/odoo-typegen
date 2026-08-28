from odoo_typegen.compiler.model_fragment import ModelFragment


class ModelIndex:
    def __init__(self) -> None:
        self._models: dict[str, list[ModelFragment]] = {}

    def add(self, model_name: str, fragment: ModelFragment) -> None:
        self._models.setdefault(model_name, []).append(fragment)

    def fragments_for(self, model_name: str) -> tuple[ModelFragment, ...]:
        return tuple(self._models.get(model_name, ()))

    def items(self) -> tuple[tuple[str, tuple[ModelFragment, ...]], ...]:
        return tuple(
            (model_name, tuple(fragments))
            for model_name, fragments in self._models.items()
        )
