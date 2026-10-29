import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]

# ten prompts a user runs the generator chain on: a fixed base the three
# generators share, varied in character, scene and crowd
PROMPTS = [
    "1girl, solo, azusa \\(blue archive\\), white hair, halo, school uniform, looking at viewer, smile",
    "1girl, solo, office lady, desk, pencil skirt, glasses, sitting",
    "1girl, solo, crying, rain, wet clothes, night, city",
    "2girls, yuri, holding hands, park, sunset",
    "1girl, 1boy, hetero, hug, couch, living room",
    "1girl, solo, swimsuit, beach, ocean, summer, from behind",
    "1boy, solo, armor, sword, castle, standing, serious",
    "1girl, solo, maid, tray, cafe, apron, blush",
    "multiple girls, 3girls, idol, stage, microphone, dynamic pose",
    "1girl, solo, cat ears, tail, kimono, shrine, autumn leaves",
]


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def veto(pack):
    return sys.modules["comfyui_generator_pack.nodes.lib.tag_veto"].load_veto()


@pytest.fixture(scope="session")
def generate(pack):
    def run(text, seed, n=10, **widgets):
        return pack.NODE_CLASS_MAPPINGS["TagsGenerator"].execute(
            text=text, n=n, seed=seed, **widgets
        )[1]

    return run


@pytest.fixture
def forget(veto):
    """Drop the masks kept from earlier calls, so a run starts cold."""

    def run():
        masks = getattr(veto, "_masks", None)
        if masks is not None:
            masks.clear()

    run()
    return run


@pytest.fixture
def lift_calls(veto, monkeypatch, forget):
    """Count the pair-table lookups conflict_mask makes, from a cold start."""
    calls = []
    orig = veto._lifts

    def spy(i, j, multi):
        calls.append(len(i))
        return orig(i, j, multi)

    monkeypatch.setattr(veto, "_lifts", spy)
    return calls
