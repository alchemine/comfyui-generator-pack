import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]

# the workflow's blacklist (__blacklist/common__ of the user's wildcards),
# 540 regex tokens, one per line
BLACKLIST = ", ".join(
    (Path(__file__).parent / "blacklist_common.txt").read_text().split("\n")
).strip(", ")

# ten base prompts the chain starts from, taken from the first tags of
# images the workflow produced on 2026-10-29 (artists, quality tags, framing)
PROMPTS = [
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, dutch angle, curtains, ocean, day",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, from side, (looking to the side:1.1), sunset, outdoors, rock",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, profile, cigarette, backlighting, from side, cropped head",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, dutch angle, (facing to the side:1.1), from side, indoors, horizon, wide shot",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, dutch angle, window, ocean, outdoors, summer, lens flare",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, dutch angle, from side, (head tilt:1.1), transparent, chair, tile floor",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, teddy bear, balloon, bedroom, indoors",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, motor vehicle, military vehicle, tank, car, vehicle focus",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, from below, day, cloud, outdoors, sky, contrail",
    "ciloranko, mikozin, gulim, azuuru, nawakena, mside, (eyelashes:1.2), finely detailed fingers, original, dutch angle, pillar, indoors, window, wooden floor, reflection",
]

WIDGETS = (
    "subject",
    "body",
    "expressions",
    "pose",
    "clothes",
    "background",
    "bg_details",
    "framing",
)

# the three generators of the workflow, in chain order
CHAIN = (
    dict(
        n=5,
        auto=True,
        rating="all",
        lift_threshold=0.1,
        background=True,
        bg_details=True,
        framing=True,
    ),
    dict(
        n=10, auto=False, rating="all", lift_threshold=0.2, pose=True, expressions=True
    ),
    dict(n=10, auto=True, rating="all", lift_threshold=0.2, body=True, clothes=True),
)


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
def tags_module(pack):
    return sys.modules["comfyui_generator_pack.nodes.tags"]


@pytest.fixture
def yaml_loads(tags_module, monkeypatch):
    """Count how often blacklist_pattern reads wildcards.yaml."""
    calls = []
    orig = tags_module.yaml.safe_load

    def spy(stream):
        calls.append(1)
        return orig(stream)

    monkeypatch.setattr(tags_module.yaml, "safe_load", spy)
    return calls


@pytest.fixture(scope="session")
def generate(pack):
    def run(text, seed, blacklist=BLACKLIST, **widgets):
        widgets = {**{w: False for w in WIDGETS}, **widgets}
        return pack.NODE_CLASS_MAPPINGS["TagsGenerator"].execute(
            text=text, seed=seed, blacklist=blacklist, **widgets
        )[0]

    return run


def chain(generate, text, seed, blacklist=BLACKLIST):
    out = text
    for step in CHAIN:
        out = generate(out, seed, blacklist=blacklist, **step)
    return out
