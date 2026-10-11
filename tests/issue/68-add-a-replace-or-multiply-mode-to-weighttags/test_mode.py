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


@pytest.fixture
def weight(pack):
    node = pack.NODE_CLASS_MAPPINGS["WeightTags"]

    buckets = [n for n in node.INPUT_TYPES()["required"] if n not in ("text", "mode")]

    def run(text, mode, value):
        on = {b: True for b in buckets if not b.endswith("_weight")}
        on.update({b: value for b in buckets if b.endswith("_weight")})
        return node.execute(text=text, mode=mode, **on)[0]

    return run


def test_mode_follows_text(pack):
    required = pack.NODE_CLASS_MAPPINGS["WeightTags"].INPUT_TYPES()["required"]
    assert list(required)[:2] == ["text", "mode"]
    assert required["mode"][0] == ["replace", "multiply"]
    assert required["mode"][1]["default"] == "replace"


@pytest.mark.parametrize(
    "tag, out",
    [
        ("shirt", "(shirt:1.2)"),
        ("(library:1.2)", "(library:1.2)"),
        ("((shirt))", "(shirt:1.2)"),
        ("(abc:-1.1)", "(abc:-1.2)"),
        ("[smile]", "(smile:1.2)"),
    ],
)
def test_replace_keeps_the_sign(weight, tag, out):
    assert weight(tag, "replace", 1.2) == out


@pytest.mark.parametrize(
    "tag, out",
    [
        ("shirt", "(shirt:1.1)"),
        ("(library:1.2)", "(library:1.32)"),
        ("((shirt))", "(shirt:1.331)"),
        ("(abc:-1.1)", "(abc:-1.21)"),
    ],
)
def test_multiply(weight, tag, out):
    assert weight(tag, "multiply", 1.1) == out


@pytest.mark.parametrize(
    "tag, value",
    [
        ("shirt", 1.0),
        ("(shirt:1.2)", 1.2),
        ("((shirt))", 1.21),
        ("[smile]", 1 / 1.1),
        ("((x:1.2))", 1.2 * 1.1),
        ("(abc:-1.1)", -1.1),
        ("ganyu \\(genshin impact\\)", 1.0),
    ],
)
def test_weight_of(pack, tag, value):
    tags = sys.modules["comfyui_generator_pack.nodes.tags"]
    assert tags._weight_of(tag) == pytest.approx(value)
