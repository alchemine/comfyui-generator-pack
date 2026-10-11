import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]

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


def test_character_follows_subject(pack):
    required = pack.NODE_CLASS_MAPPINGS["WeightTags"].INPUT_TYPES()["required"]
    pairs = tuple(key for name in CATEGORIES for key in (name, name + "_weight"))
    assert tuple(required) == ("text", *pairs)


def test_character_weight(weight):
    assert (
        weight(
            "amiya \\(arknights\\), amiya, smile", character=True, character_weight=1.2
        )
        == "(amiya \\(arknights\\):1.2), (amiya:1.2), smile"
    )


def test_other_toggles_leave_characters(weight):
    assert (
        weight("amiya \\(arknights\\), smile", expressions=True, expressions_weight=1.2)
        == "amiya \\(arknights\\), (smile:1.2)"
    )
