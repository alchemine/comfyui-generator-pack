import csv
import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
DATA = PACK_DIR / "resources" / "characters_v1.txt"

# tagged no humans far more often than the average post: pokemon,
# kirby, an eevee evolution, a gundam
NON_HUMANS = ["pikachu", "eevee", "kirby", "charizard", "snorlax", "umbreon", "nu gundam"]
# drawn as people, however often a pokemon stands beside them
HUMANS = {"hatsune miku": "girl", "gardevoir": "girl", "lillie (pokemon)": "girl", "link": "boy"}


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
def data():
    with open(DATA, newline="", encoding="utf-8") as f:
        return {r[0]: r[3] for r in csv.reader(f, delimiter="\t")}


@pytest.fixture(scope="module")
def generate(pack):
    node = pack.NODE_CLASS_MAPPINGS["CharacterTagsGenerator"]

    def run(**kwargs):
        kwargs.setdefault("subject", False)
        return node.execute(**kwargs)[0]

    return run


def names(text, data):
    tags = (t.replace("\\", "") for t in text.split(", "))
    return [t for t in tags if t in data]


@pytest.mark.parametrize("name", NON_HUMANS)
def test_non_humans_are_other(data, name):
    assert data[name] == "other"


@pytest.mark.parametrize("name,sex", HUMANS.items())
def test_humans_keep_their_sex(data, name, sex):
    assert data[name] == sex


def test_girl_and_boy_never_draw_a_non_human(generate, data):
    drawn = set()
    for seed in range(200):
        drawn.update(names(generate(n=10, boy=True, min_count=100, seed=seed), data))
    assert len(drawn) > 1000
    assert not drawn & set(NON_HUMANS)


def test_other_draws_non_humans(generate, data):
    drawn = set()
    for seed in range(200):
        drawn.update(names(generate(n=10, girl=False, other=True, min_count=100, seed=seed), data))
    assert drawn & set(NON_HUMANS)
    assert not drawn & set(HUMANS)
