import subprocess
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]


def shipped_sources():
    """The tracked .py files outside docs/ and tests/, which .comfyignore keeps out."""
    names = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=PACK_DIR, check=True, capture_output=True, text=True
    ).stdout.split()  # fmt: skip
    return [n for n in names if not n.startswith(("docs/", "tests/"))]


@pytest.mark.parametrize("pattern", ["sqlite3.connect(", ".connect("])
def test_no_shipped_source_spells_the_flagged_pattern(pattern):
    assert [n for n in shipped_sources() if pattern in (PACK_DIR / n).read_text()] == []
