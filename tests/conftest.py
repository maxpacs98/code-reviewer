from pathlib import Path

import pytest

from reviewer.diffparse import parse_unified_diff
from reviewer.model import Diff

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_diff():
    """Load a .diff fixture by name and parse it."""

    def _load(name: str) -> Diff:
        return parse_unified_diff((FIXTURES / name).read_text(encoding="utf-8"))

    return _load
