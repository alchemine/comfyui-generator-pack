import numpy as np
import pytest

REFS = [
    "1girl",
    "solo",
    "white_hair",
    "halo",
    "school_uniform",
    "smile",
    "office_lady",
    "rain",
    "yuri",
    "hetero",
    "swimsuit",
    "armor",
]


@pytest.mark.parametrize("ref", REFS)
def test_second_call_skips_the_pair_table(veto, lift_calls, ref):
    ids = np.arange(len(veto.vocab))
    first = veto.conflict_mask(ids, ref, 0.5, False)
    lookups = len(lift_calls)
    second = veto.conflict_mask(ids, ref, 0.5, False)
    assert np.array_equal(first, second)
    assert len(lift_calls) == lookups


@pytest.mark.parametrize("ref", REFS)
def test_subset_matches_the_full_mask(veto, ref):
    ids = np.arange(len(veto.vocab))
    full = veto.conflict_mask(ids, ref, 0.5, False)
    subset = np.array([-1, 0, 5, 1234, 20000, -1, 7], dtype=np.int64)
    out = veto.conflict_mask(subset, ref, 0.5, False)
    expected = np.where(subset >= 0, full[np.maximum(subset, 0)], False)
    assert np.array_equal(out, expected)


def test_threshold_and_table_are_part_of_the_key(veto):
    ids = np.arange(len(veto.vocab))
    loose = veto.conflict_mask(ids, "smile", 0.1, False)
    strict = veto.conflict_mask(ids, "smile", 0.5, False)
    assert strict.sum() > loose.sum()
    assert not np.array_equal(
        veto.conflict_mask(ids, "kiss", 0.5, False),
        veto.conflict_mask(ids, "kiss", 0.5, True),
    )
