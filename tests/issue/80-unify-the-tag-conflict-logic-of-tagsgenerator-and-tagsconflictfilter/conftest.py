import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]

# tests/issue/27's prompt: a character sheet, many views of one character
SHEET = (
    "multiple views, character profile, (full body:0.8), cropped torso, "
    "turnaround, profile, from above, from below, text, emphasis lines, "
    "comic expression, variations, (wince:1.1), (>:\\(:1.1), (excited:1.1), "
    "(bored:1.1), (trembling:1.1), (notice lines:1.1), breasts"
)
WIDGETS = ("subject", "body", "expressions", "pose", "clothes", "background", "bg_details", "framing")


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
def generate(pack):
    def run(text, seed, n=15, **toggles):
        out, _ = pack.NODE_CLASS_MAPPINGS["TagsGenerator"].execute(text=text, n=n, seed=seed, **toggles)
        given = {t.strip() for t in text.split(",")}
        return [t for t in out.split(", ") if t and t not in given]

    return run


@pytest.fixture(scope="session")
def conflict_filter(pack):
    def run(fixed, generated):
        text = ", ".join(t for t in (fixed, generated) if t)
        out, _ = pack.NODE_CLASS_MAPPINGS["TagsConflictFilter"].execute(text=text, fixed_tags=fixed)
        return [t for t in out.split(", ") if t]

    return run


@pytest.fixture(scope="session")
def background_only():
    """TagsGenerator widget toggles with only background on."""
    return {w: w == "background" for w in WIDGETS}


@pytest.fixture(scope="session")
def sheet():
    return SHEET
