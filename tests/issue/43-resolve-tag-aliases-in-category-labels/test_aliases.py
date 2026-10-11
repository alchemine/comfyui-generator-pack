import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
LIB_DIR = PACK_DIR / "nodes" / "lib"

sys.path.insert(0, str(LIB_DIR))
import tag_category  # noqa: E402
import tag_guard  # noqa: E402


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
def labels():
    return tag_category.Labels()


@pytest.mark.parametrize(
    "tag, category",
    [(":)", "expressions"), ("smiling", "expressions"), ("longhair", "hair")],
)
def test_alias_has_a_category(labels, tag, category):
    assert labels.category_name(tag) == category


def test_alias_has_the_rating_of_its_tag(labels):
    assert labels.rating_of(":)", default=-1) == labels.rating_of("smile", default=-1)
    assert labels.rating_of("smile", default=-1) != -1


def test_table_spelling_wins(labels):
    assert labels.category_name("smile") == "expressions"


def test_classify_alias():
    assert tag_guard.classify_tags(":), library")["expressions"] == [":)"]


@pytest.mark.parametrize(
    "tag, bare",
    [
        (":)", ":)"),
        (":\\)", ":)"),
        (":3", ":3"),
        ("(:3:1.5)", ":3"),
        ("(smile:1.2)", "smile"),
        ("((smile))", "smile"),
        ("ganyu \\(genshin impact\\)", "ganyu (genshin impact)"),
    ],
)
def test_normalize_keeps_tag_parentheses(tag, bare):
    assert tag_guard.normalize(tag) == bare


def test_classify_emoticons():
    buckets = tag_guard.classify_tags(":3, :\\), ganyu \\(genshin impact\\)")
    assert buckets["expressions"] == [":3", ":)"]
    assert buckets["character"] == ["ganyu (genshin impact)"]


def test_order_tags_places_aliases(pack):
    tags = sys.modules["comfyui_generator_pack.nodes.tags"]
    assert tags._sort_by_category(
        ["library", ":\\)", ":3"], tags.CATEGORY_ORDER, lambda t: (t,)
    ) == [":\\)", ":3", "library"]
