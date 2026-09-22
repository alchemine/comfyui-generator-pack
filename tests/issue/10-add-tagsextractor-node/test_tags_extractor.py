import csv
import asyncio
import importlib.util
import re
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
LIB_DIR = PACK_DIR / "nodes" / "lib"

sys.path.insert(0, str(LIB_DIR))
import tag_search  # noqa: E402


@pytest.fixture(scope="module")
def search_tags():
    return tag_search.search_tags


@pytest.fixture(scope="module")
def general_tags():
    """Every general (category 0) tag name in the dump, with spaces."""
    with open(
        PACK_DIR / "resources" / "danbooru-tags.txt", newline="", encoding="utf-8"
    ) as f:
        return {r[0].replace("_", " ") for r in csv.reader(f) if r and r[1] == "0"}


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


def test_the_node_is_registered(pack):
    assert "TagsExtractor" in pack.NODE_CLASS_MAPPINGS


def test_the_node_runs_inside_an_event_loop(pack):
    """The executor awaits node functions on its own loop; a sync node that
    starts a loop of its own raises there."""
    node = pack.NODE_CLASS_MAPPINGS["TagsExtractor"]

    async def inside_a_loop():
        return await node.execute(text="a girl sitting on a chair")

    assert asyncio.run(inside_a_loop())[0] == "1girl, solo, sitting, on chair"


def test_the_tags_come_back_grouped_by_kind(pack):
    node = pack.NODE_CLASS_MAPPINGS["TagsExtractor"]
    (tags, _) = asyncio.run(node.execute(text="a girl in a library, smiling"))
    assert tags == "1girl, solo, smile, library"


@pytest.mark.skipif(
    importlib.util.find_spec("googletrans") is None, reason="googletrans translates"
)
def test_translate_reaches_the_same_tags(pack):
    node = pack.NODE_CLASS_MAPPINGS["TagsExtractor"]
    (tags, _) = asyncio.run(
        node.execute(text="창가 의자에 앉아 있는 소녀, 노을", translate=True)
    )
    assert {"1girl", "sitting", "window", "sunset"} <= set(tags.split(", "))


def test_a_scene_maps_to_its_tags(search_tags):
    tags = search_tags("a girl sitting on a chair by the window at sunset")
    assert {"sitting", "on chair", "window", "sunset"} <= set(tags)


def test_the_subject_leads(search_tags):
    tags = search_tags("a girl sitting on a chair by the window at sunset")
    assert tags[:2] == ["1girl", "solo"]


def test_subject_off_keeps_the_scene_only(search_tags):
    tags = search_tags(
        "a girl sitting on a chair by the window at sunset", subject=False
    )
    assert tags == ["sitting", "on chair", "window", "sunset"]


def test_two_people_are_not_solo(search_tags):
    assert search_tags("a girl and a boy in a library") == ["1girl", "1boy", "library"]


def test_a_number_counts(search_tags):
    assert search_tags("two girls and 3 boys") == ["2girls", "3boys"]


def test_a_person_noun_is_never_searched(search_tags):
    tags = search_tags("a man is taking off her bra")
    assert "1boy" in tags
    assert "male focus" not in tags


def test_an_object_pronoun_is_another(search_tags):
    assert search_tags("a man is undressing her bra") == [
        "1boy",
        "undressing another",
        "bra",
    ]
    assert search_tags("she is looking at him") == ["looking at another"]


def test_an_object_pronoun_takes_solo_away(search_tags):
    assert search_tags("a girl hugging him") == ["1girl", "hug"]


def test_min_count_drops_a_rare_alias_hit(search_tags):
    sentence = "a man is taking off her bra"
    assert "takeoff" in search_tags(sentence)
    assert search_tags(sentence, min_count=500) == ["1boy", "solo", "bra"]


def test_a_phrase_the_vocabulary_cannot_spell_comes_from_the_wiki():
    tags, matches = tag_search.search("a man is taking off her bra", min_count=500)
    assert tags == ["1boy", "undressing another", "bra"]
    assert [(m.phrase, m.tag) for m in matches if m.spelling == "wiki"] == [
        ("taking off", "undressing another")
    ]


def test_a_spelled_phrase_never_goes_to_the_wiki(search_tags):
    assert search_tags("a girl on a chair") == ["1girl", "solo", "on chair"]


def test_a_single_leftover_word_never_goes_to_the_wiki(search_tags):
    assert search_tags("a girl, surface") == ["1girl", "solo"]


def test_the_table_names_the_spelling_and_the_verdict():
    tags, matches = tag_search.search("a man is taking off her bra", min_count=500)
    table = tag_search.format_table(matches, 500)
    assert re.search(
        r"\| taking off \| takeoff \| take-off \| +130 \| below min_count \|", table
    )
    assert table.endswith("(min_count: 500)")


def test_inflections_reach_the_tag(search_tags):
    assert "sitting" in search_tags("she sits")


def test_a_phrase_picks_the_whole_tag(search_tags):
    tags = search_tags("her hair in a low ponytail")
    assert "low ponytail" in tags
    assert "high ponytail" not in tags


def test_a_negated_phrase_is_dropped(search_tags):
    assert "hat" not in search_tags("a girl without a hat")


def test_an_alias_reaches_its_tag(search_tags):
    assert "breasts" in search_tags("oppai")


def test_only_real_tags_come_back(search_tags, general_tags):
    tags = search_tags("a girl sitting on a chair by the window at sunset")
    assert set(tags) <= general_tags


def test_a_blacklisted_tag_is_left_out(search_tags):
    sentence = "a girl in a school uniform"
    assert "school uniform" in search_tags(sentence)
    assert "school uniform" not in search_tags(
        sentence, blacklist=re.compile("uniform")
    )


def test_max_tags_is_a_ceiling(search_tags):
    assert (
        len(
            search_tags("a girl sitting on a chair by the window at sunset", max_tags=3)
        )
        <= 3
    )
