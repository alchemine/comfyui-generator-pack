import pytest

from .conftest import BLACKLIST

TOKENS = BLACKLIST.split(", ")

# ten blacklists a user hands the node: the workflow's full list, cuts of
# it, and the wildcard and invalid-token forms the function also accepts
BLACKLISTS = [
    BLACKLIST,
    ", ".join(TOKENS[:1]),
    ", ".join(TOKENS[:10]),
    ", ".join(TOKENS[:100]),
    ", ".join(TOKENS[100:300]),
    ", ".join(TOKENS[300:]),
    ", ".join(TOKENS[::2]),
    ", ".join(TOKENS[:20]) + ", <color> hair",
    ", ".join(TOKENS[:20]) + ", __color__ eyes",
    ", ".join(TOKENS[:20]) + ", (unclosed",
]


@pytest.mark.parametrize("blacklist", BLACKLISTS)
def test_second_call_does_not_read_wildcards_again(tags_module, yaml_loads, blacklist):
    first = tags_module.blacklist_pattern(blacklist)
    reads = len(yaml_loads)
    assert reads <= 1
    second = tags_module.blacklist_pattern(blacklist)
    assert second == first
    assert len(yaml_loads) == reads


@pytest.mark.parametrize("blacklist", BLACKLISTS)
def test_pattern_matches_uncached_computation(tags_module, blacklist):
    cached = tags_module.blacklist_pattern(blacklist)
    uncached = getattr(tags_module.blacklist_pattern, "__wrapped__", tags_module.blacklist_pattern)(blacklist)
    assert cached == uncached


def test_empty_blacklist_is_empty_pattern(tags_module):
    assert tags_module.blacklist_pattern("") == ""
    assert tags_module.blacklist_pattern("  ,  ") == ""
