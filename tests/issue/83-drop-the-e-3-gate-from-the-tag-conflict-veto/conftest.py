import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]

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

# the reported prompt: the __mf__ wildcard, every tag a reference
MF = (
    "1girl, 1boy, hetero, affectionate, deep skin, leaning on person, "
    "age difference, mature male, aged down, loli, fatherly"
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
def veto(pack):
    return sys.modules["comfyui_generator_pack.nodes.lib.tag_veto"].load_veto()


@pytest.fixture(scope="session")
def expressions(pack):
    """Distinct expression tags TagsGenerator draws for a prompt over seeds."""
    node = pack.NODE_CLASS_MAPPINGS["TagsGenerator"]
    toggles = {w: w == "expressions" for w in WIDGETS}

    def run(text, seeds=20, n=3):
        given = {t.strip() for t in text.split(",")}
        seen = set()
        for seed in range(seeds):
            out, _ = node.execute(
                text=text, n=n, seed=seed, rating="explicit", **toggles
            )
            seen.update(t for t in out.split(", ") if t and t not in given)
        return seen

    return run


@pytest.fixture(scope="session")
def generate_then_filter(pack):
    """Tags the generator drew that TagsConflictFilter then removed."""
    gen = pack.NODE_CLASS_MAPPINGS["TagsGenerator"]
    flt = pack.NODE_CLASS_MAPPINGS["TagsConflictFilter"]
    toggles = {w: w == "expressions" for w in WIDGETS}

    def run(text, seed):
        out, _ = gen.execute(text=text, n=3, seed=seed, rating="explicit", **toggles)
        given = {t.strip() for t in text.split(",")}
        drawn = [t for t in out.split(", ") if t and t not in given]
        kept, _ = flt.execute(text=out, fixed_tags=text)
        kept = set(kept.split(", "))
        return [t for t in drawn if t not in kept]

    return run
