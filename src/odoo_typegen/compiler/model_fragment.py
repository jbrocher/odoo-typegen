from pathlib import Path

import pydantic


class ModelFragment(pydantic.BaseModel):
    module: str
    file: Path
    class_name: str
    name: str | None
    inherits: tuple[str, ...]
    line: int
