import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
LIB_DIR = PACK_DIR / "nodes" / "lib"

sys.path.insert(0, str(LIB_DIR))
import tag_guard  # noqa: E402


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


def test_widgets_follow_buckets(pack):
    required = pack.NODE_CLASS_MAPPINGS["WeightTags"].INPUT_TYPES()["required"]
    pairs = tuple(key for name in tag_guard.BUCKETS for key in (name, name + "_weight"))
    assert tuple(required) == ("text", "mode", *pairs)


def test_others_weight(weight):
    assert (
        weight("genshin impact, highres, smile", others=True, others_weight=1.2)
        == "(genshin impact:1.2), (highres:1.2), smile"
    )


def test_break_is_left_alone(weight):
    assert weight("smile, BREAK, highres", others=True, others_weight=1.2) == (
        "smile, BREAK, (highres:1.2)"
    )
