"""Unit checks of the shared verdict: tag_veto.TagVeto.conflict and tag_solo.crowded."""

import sys

import pytest


@pytest.fixture(scope="module")
def veto(pack):
    return sys.modules["comfyui_generator_pack.nodes.lib.tag_veto"].load_veto()


@pytest.fixture(scope="module")
def solo(pack):
    return sys.modules["comfyui_generator_pack.nodes.lib.tag_solo"]


@pytest.mark.parametrize(
    "cand, refs, multi, blocked_by",
    [
        ("night", ["day"], False, "day"),  # lift far under 0.5
        ("long_hair", ["short_hair"], False, "short_hair"),
        ("smile", ["1girl"], False, None),  # subject tags never judge ordinary ones
        ("kiss", ["yuri"], False, None),  # solo posts: lift 1 or more
        ("kiss", ["yuri"], True, None),  # all posts: lift 17.5
        ("red_hair", ["blonde_hair"], True, None),  # two girls, two hair colours
        (
            "outdoors",
            ["multiple_views"],
            True,
            "multiple_views",
        ),  # lift 0.28 on all posts
        ("swimsuit", ["bikini"], False, None),
    ],
)
def test_conflict(veto, cand, refs, multi, blocked_by):
    assert veto.conflict(cand, refs, 0.5, multi) == blocked_by


@pytest.mark.parametrize(
    "tags, crowded",
    [
        (["2girls"], True),
        (["1boy", "1girl"], True),
        (["1girl", "hug"], True),
        (["multiple views"], True),
        (["grabbing another's hand"], True),
        (["1girl", "solo"], False),
        (["1girl", "turnaround", "variations"], False),
        ([], False),
    ],
)
def test_crowded(solo, tags, crowded):
    assert solo.crowded(tags) is crowded


def test_defaults(veto):
    mod = sys.modules["comfyui_generator_pack.nodes.lib.tag_veto"]
    assert mod.DEFAULT_LIFT_TH == 0.5
