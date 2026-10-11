import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]

CATEGORIES = (
    "subject",
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


def test_registered(pack):
    assert "WeightTags" in pack.NODE_CLASS_MAPPINGS
    assert pack.NODE_DISPLAY_NAME_MAPPINGS["WeightTags"] == "Weight Tags"


def test_widget_order(pack):
    required = pack.NODE_CLASS_MAPPINGS["WeightTags"].INPUT_TYPES()["required"]
    assert tuple(required) == ("text", "weight", *CATEGORIES)
    assert required["weight"][1]["default"] == 1.5
    for name in CATEGORIES:
        assert required[name][0] == "BOOLEAN"
        assert required[name][1]["default"] is False


def test_example(weight):
    assert (
        weight(
            ":3, :\\), shirt, 1girl, library",
            weight=1.5,
            expressions=True,
            background=True,
        )
        == "(:3:1.5), (:\\):1.5), shirt, 1girl, (library:1.5)"
    )


def test_group_covers_hair(weight):
    assert weight("long hair, smile", weight=1.2, body=True) == "(long hair:1.2), smile"


def test_existing_weight_is_replaced(weight):
    assert weight("(library:1.2), ((shirt))", weight=1.5, background=True) == (
        "(library:1.5), ((shirt))"
    )


def test_nothing_on_leaves_text(weight):
    assert weight("1girl, library", weight=1.5) == "1girl, library"
