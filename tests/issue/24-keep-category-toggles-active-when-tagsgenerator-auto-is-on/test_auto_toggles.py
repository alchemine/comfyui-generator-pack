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


def test_auto_drops_toggled_off_categories(spec_of):
    assert spec_of(auto=True, body=False) == (
        "characters, pose, expressions, clothes, background+objects+compositions"
    )


def test_auto_ignores_the_shares(spec_of):
    assert "pose" in spec_of(auto=True, pose_share=0.3).split(", ")
