import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
UNCAPPED = (
    "characters, pose, expressions, body, clothes, background+objects+compositions"
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
def spec_of(pack, monkeypatch):
    """Run TagsGenerator and return the categories spec it sampled with."""
    tags = sys.modules["comfyui_generator_pack.nodes.tags"]
    seen = []

    def fake_suggest(text, **kwargs):
        seen.append(kwargs["categories"])
        return []

    monkeypatch.setattr(tags, "suggest_tags", fake_suggest)

    def run(**kwargs):
        pack.NODE_CLASS_MAPPINGS["TagsGenerator"].execute(text="1girl", n=5, **kwargs)
        return seen[0]

    return run


def test_auto_follows_n(pack):
    required = pack.NODE_CLASS_MAPPINGS["TagsGenerator"].INPUT_TYPES()["required"]
    names = list(required)
    assert names[names.index("n") + 1] == "auto"
    kind, options = required["auto"]
    assert kind == "BOOLEAN"
    assert options["default"] is True


def test_auto_on_lifts_every_cap(spec_of):
    assert spec_of(auto=True, pose_share=0.3, body=False) == UNCAPPED


def test_auto_off_keeps_the_shares(spec_of):
    parts = spec_of(auto=False, pose_share=0.3, body=False).split(", ")
    assert "pose:0.3" in parts
    assert not any(p.startswith("body") for p in parts)


def test_auto_changes_the_cache_key(pack):
    node = pack.NODE_CLASS_MAPPINGS["TagsGenerator"]
    assert node.IS_CHANGED(text="1girl", auto=True) != node.IS_CHANGED(
        text="1girl", auto=False
    )
