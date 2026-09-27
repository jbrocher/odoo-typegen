from pathlib import Path

import pydantic


class ModelFragment(pydantic.BaseModel):
    module: str
    file: Path
    class_name: str
    name: str | None
    inherits: tuple[str, ...]
    line: int

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
