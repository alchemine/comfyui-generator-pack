import builtins
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
LIB_DIR = PACK_DIR / "nodes" / "lib"

sys.path.insert(0, str(LIB_DIR))
import tag_category  # noqa: E402


@pytest.mark.parametrize(
    "tag, category",
    [
        ("missing headwear", "clothes"),
        ("cat symbol", "style"),
        ("shoulder bag", "clothes"),
        ("backpack", "clothes"),
        ("unworn bag", "objects"),
        ("falling petals", "effects"),
        ("nude cover", "clothes"),
        ("strip mahjong", "pose"),
    ],
)
def test_category(tag, category):
    labels = tag_category.Labels()
    assert labels.names[labels.category_of(tag)] == category


def test_old_tables_are_not_read(monkeypatch):
    """A user who already has an older table must not keep reading it."""
    opened = []
    real_open = builtins.open

    def spy(path, *args, **kwargs):
        opened.append(Path(path).name)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    tag_category.Labels()
    assert not {"categories_v2.0.json", "categories_v2.1.json"} & set(opened)
