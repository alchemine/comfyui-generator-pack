import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]


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


@pytest.fixture(scope="module")
def tags(pack):
    return sys.modules["comfyui_generator_pack.nodes.tags"]


def test_the_generator_offers_subject(pack):
    inputs = pack.NODE_CLASS_MAPPINGS["TagsGenerator"].INPUT_TYPES()["required"]
    assert {"subject", "subject_share"} <= set(inputs)
    assert not {"characters", "characters_share"} & set(inputs)


def test_subject_reaches_the_characters_category(tags):
    spec = tags._categories_spec({"subject_share": 0.4})
    assert "characters:0.4" in spec.split(", ")


def test_subject_off_drops_the_characters_category(tags):
    spec = tags._categories_spec({"subject": False})
    assert "characters" not in spec


def test_classify_names_its_first_output_subject(pack):
    assert pack.NODE_CLASS_MAPPINGS["ClassifyTags"].RETURN_NAMES[0] == "subject"


def test_classify_puts_the_subject_first(pack):
    out = pack.NODE_CLASS_MAPPINGS["ClassifyTags"].execute("1boy, serafuku, sitting")
    assert out[0] == "1boy"
