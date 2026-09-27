from pathlib import Path

import pydantic


class ModelFragment(pydantic.BaseModel):
    module: str
    file: Path
    class_name: str
    name: str | None
    inherits: tuple[str, ...]
    line: int

    @property
    def effective_name(self) -> str | None:
        if self.name is not None:
            return self.name

        if len(self.inherits) == 1:
            return self.inherits[0]

        return None
