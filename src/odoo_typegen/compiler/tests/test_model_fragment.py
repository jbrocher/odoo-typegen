from pathlib import Path

import pydantic
import pytest

from odoo_typegen.compiler.model_fragment import ModelFragment


def test_declared_model_name_is_the_effective_name():
    fragment = ModelFragment(
        module="library",
        file=Path("library/models/library_book.py"),
        class_name="LibraryBook",
        name="library.book",
        inherits=("mail.thread",),
        line=4,
    )

    assert fragment.effective_name == "library.book"


@pytest.mark.parametrize(
    "inherits",
    [
        (),
        ("mail.thread", "mail.activity.mixin"),
    ],
)
def test_fragment_requires_an_effective_model_name(inherits: tuple[str, ...]):
    with pytest.raises(pydantic.ValidationError):
        ModelFragment(
            module="library",
            file=Path("library/models/library_book.py"),
            class_name="LibraryBook",
            name=None,
            inherits=inherits,
            line=4,
        )
