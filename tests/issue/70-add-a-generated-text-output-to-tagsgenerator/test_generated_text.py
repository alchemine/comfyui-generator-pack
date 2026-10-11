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
def node(pack):
    return pack.NODE_CLASS_MAPPINGS["TagsGenerator"]


def test_outputs(node):
    assert tuple(node.RETURN_NAMES) == ("text", "generated_text")
    assert node.RETURN_TYPES == ("STRING", "STRING")


def test_text_is_input_then_generated(node):
    text, generated = node.execute(text="1girl, solo", n=5, seed=1, temperature=0.0)
    assert generated
    assert text == "1girl, solo, " + generated


def test_nothing_generated(node, monkeypatch):
    tags = sys.modules["comfyui_generator_pack.nodes.tags"]
    monkeypatch.setattr(tags, "suggest_tags", lambda text, **kwargs: [])
    assert node.execute(text="1girl, solo", n=5) == ("1girl, solo", "")
