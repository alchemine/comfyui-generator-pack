import pytest


@pytest.mark.parametrize(
    "cand, ref, blocked",
    [
        # seen together, lift 0.5 or more, expected fewer than 3 times:
        # the E < 3 gate blocked these, lift alone does not
        ("grin", "affectionate", False),
        ("smile", "age_difference", False),
        ("blush", "age_difference", False),
        ("closed_eyes", "leaning_on_person", False),
        ("sweatdrop", "hetero", False),
        ("happy", "affectionate", False),
        ("half-closed_eyes", "mature_male", False),
        # never seen together: lift 0, blocked at any threshold
        ("grin", "fatherly", True),
        ("drooling", "affectionate", True),
        # lift under 0.5
        ("open_mouth", "mature_male", True),
        ("night", "day", True),
        ("long_hair", "short_hair", True),
        ("laughing", "pout", True),
    ],
)
def test_conflict(veto, cand, ref, blocked):
    assert (veto.conflict(cand, [ref], 0.5, False) == ref) is blocked


def test_no_rare_gate(veto):
    assert not hasattr(veto, "pair_rare")
