from pathlib import Path
import pydantic


class Module(pydantic.BaseModel):
    name: str
    path: Path
    manifest: Path
    depends: tuple[str, ...] = ()
