from pathlib import Path

import pydantic


class StubAttribute(pydantic.BaseModel):
    name: str
    type: str
    module: str | None = None
    file: Path | None = None
    line: int | None = None


class StubMethod(pydantic.BaseModel):
    name: str
    signature: str
    decorators: tuple[str, ...] = ()
    module: str | None = None
    file: Path | None = None
    line: int | None = None


class StubClass(pydantic.BaseModel):
    import_path: str
    class_name: str
    imports: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()
    attributes: tuple[StubAttribute, ...] = ()
    methods: tuple[StubMethod, ...] = ()


class ConsolidatedModel(pydantic.BaseModel):
    name: str
    stub_class: StubClass
