from pathlib import Path

import pydantic


class Attribute(pydantic.BaseModel):
    name: str
    type: str
    module: str | None = None
    file: Path | None = None
    line: int | None = None


class Method(pydantic.BaseModel):
    name: str
    signature: str
    decorators: tuple[str, ...] = ()
    module: str | None = None
    file: Path | None = None
    line: int | None = None
