import csv
import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
DATA = PACK_DIR / "resources" / "characters_v1.txt"


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
        return {
            r[0]: {"posts": int(r[1]), "first_year": int(r[2]), "sex": r[3]}
            for r in csv.reader(f, delimiter="\t")
        }


@pytest.fixture(scope="module")
def generate(pack):
    node = pack.NODE_CLASS_MAPPINGS["CharacterTagsGenerator"]

    def run(**kwargs):
        kwargs.setdefault("n", 1)
        kwargs.setdefault("seed", 0)
        return node.execute(**kwargs)[0]

    return run


def names(text, data):
    """The character names in an output, brackets unescaped."""
    tags = (t.replace("\\", "") for t in text.split(", "))
    return [t for t in tags if t in data]


def test_the_node_is_registered(pack):
    assert "CharacterTagsGenerator" in pack.NODE_CLASS_MAPPINGS


def test_the_node_offers_its_widgets(pack):
    inputs = pack.NODE_CLASS_MAPPINGS["CharacterTagsGenerator"].INPUT_TYPES()
    assert {
        "n",
        "girl",
        "boy",
        "other",
        "subject",
        "year_min",
        "year_min_value",
        "year_max",
        "year_max_value",
        "min_count",
        "seed",
    } <= set(inputs["required"])


def test_the_data_file_labels_known_characters(data):
    assert data["hatsune miku"]["sex"] == "girl"
    assert data["hatsune miku"]["first_year"] == 2007
    assert data["link"]["sex"] == "boy"
    assert data["astolfo (fate)"]["sex"] == "boy"


def test_n_characters_come_back(generate, data):
    text = generate(n=3, subject=False)
    assert len(text.split(", ")) == 3
    assert len(names(text, data)) == 3


def test_sex_filters_the_pool(generate, data):
    text = generate(n=5, girl=False, boy=True, subject=False)
    drawn = names(text, data)
    assert len(drawn) == 5
    assert all(data[t]["sex"] == "boy" for t in drawn)


def test_min_count_filters_the_pool(generate, data):
    drawn = names(generate(n=5, min_count=5000, subject=False), data)
    assert len(drawn) == 5
    assert all(data[t]["posts"] >= 5000 for t in drawn)


def test_year_limits_filter_the_pool(generate, data):
    drawn = names(
        generate(
            n=5,
            year_min=True,
            year_min_value=2023,
            year_max=True,
            year_max_value=2024,
            subject=False,
        ),
        data,
    )
    assert len(drawn) == 5
    assert all(2023 <= data[t]["first_year"] <= 2024 for t in drawn)


def test_year_limits_off_are_ignored(generate, data):
    text = generate(year_min_value=2030, year_max_value=2000, subject=False)
    assert len(names(text, data)) == 1


def test_subject_counts_one_girl(generate, data):
    text = generate(subject=True)
    tags = text.split(", ")
    assert tags[:2] == ["1girl", "solo"]
    assert len(tags) == 3 and len(names(text, data)) == 1


def test_subject_counts_mixed_sexes(generate, data):
    expected = {
        ("girl", "girl"): ["2girls", "multiple girls"],
        ("boy", "girl"): ["1girl", "1boy"],
        ("boy", "boy"): ["2boys", "multiple boys"],
    }
    for seed in range(20):
        tags = generate(n=2, boy=True, subject=True, seed=seed).split(", ")
        drawn = names(", ".join(tags), data)
        sexes = tuple(sorted(data[t]["sex"] for t in drawn))
        assert tags[: -len(drawn)] == expected[sexes]


def test_the_draw_follows_the_seed(generate):
    assert generate(n=3, seed=7) == generate(n=3, seed=7)
    assert len({generate(n=3, seed=s) for s in range(10)}) > 1


def test_no_sex_selected_returns_empty(generate):
    assert generate(n=3, girl=False, boy=False, other=False) == ""
