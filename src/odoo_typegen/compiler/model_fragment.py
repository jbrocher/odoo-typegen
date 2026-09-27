from pathlib import Path

import pydantic

from odoo_typegen.compiler.consolidated_model import StubAttribute, StubMethod


class ModelFragment(pydantic.BaseModel):
    module: str
    addon_dependencies: tuple[str, ...] | None = None
    file: Path
    class_name: str
    name: str | None
    inherits: tuple[str, ...]
    line: int
    attributes: tuple[StubAttribute, ...] | None = None
    methods: tuple[StubMethod, ...] | None = None

    @pydantic.model_validator(mode="after")
    def _validate_effective_name(self) -> "ModelFragment":
        if self.name is None and len(self.inherits) != 1:
            raise ValueError("model fragment must have an effective name")
        return self

    @property
    def effective_name(self) -> str:
        if self.name is not None:
            return self.name
        return self.inherits[0]
