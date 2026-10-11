import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
JS = PACK_DIR / "web" / "js" / "tags_generator_categories.js"

CATEGORIES = (
    "subject",
    "character",
    "pose",
    "expressions",
    "body",
    "clothes",
    "background",
    "bg_details",
    "framing",
)


@pytest.fixture(scope="module")
def pack():
    spec = importlib.util.spec_from_file_location(
        "comfyui_generator_pack",
        PACK_DIR / "__init__.py",
        submodule_search_locations=[str(PACK_DIR)],
    )
    pack = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = pack
    spec.loader.exec_module(pack)
    return pack


@pytest.fixture
def weight(pack):
    node = pack.NODE_CLASS_MAPPINGS["WeightTags"]

    def run(text, **kwargs):
        return node.execute(text=text, **kwargs)[0]

    return run


def test_widget_pairs(pack):
    required = pack.NODE_CLASS_MAPPINGS["WeightTags"].INPUT_TYPES()["required"]
    pairs = tuple(key for name in CATEGORIES for key in (name, name + "_weight"))
    assert tuple(required) == ("text", *pairs)
    for name in CATEGORIES:
        assert required[name + "_weight"][0] == "FLOAT"
        assert required[name + "_weight"][1]["default"] == 1.1


def test_each_category_has_its_own_weight(weight):
    assert (
        weight(
            ":3, library",
            expressions=True,
            expressions_weight=1.5,
            background=True,
            background_weight=1.2,
        )
        == "(:3:1.5), (library:1.2)"
    )


def test_off_category_ignores_its_weight(weight):
    assert weight("library", background=False, background_weight=1.2) == "library"


def test_rows_are_drawn_for_weighttags():
    source = JS.read_text(encoding="utf-8")
    assert "WeightTags" in source
    assert "_weight" in source
