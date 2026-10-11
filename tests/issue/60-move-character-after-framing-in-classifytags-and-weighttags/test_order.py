import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]

ORDER = (
    "subject",
    "pose",
    "expressions",
    "body",
    "clothes",
    "background",
    "bg_details",
    "framing",
    "character",
    "others",
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


def test_classify_outputs(pack):
    node = pack.NODE_CLASS_MAPPINGS["ClassifyTags"]
    assert tuple(node.RETURN_NAMES) == ORDER


def test_weight_widgets(pack):
    required = pack.NODE_CLASS_MAPPINGS["WeightTags"].INPUT_TYPES()["required"]
    pairs = tuple(key for name in ORDER for key in (name, name + "_weight"))
    assert tuple(required) == ("text", *pairs)
