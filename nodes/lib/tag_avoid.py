"""Corpus-demonstrated tag avoidance, as a runtime veto.

The suggest artifact carries a fixed 512 repulsion neighbours per tag.
Those rows saturate -- for "bar_(place)" the weakest stored neighbour
still sits at lift 0.81 -- so absence from the table means "not among
the 512 most avoided", not "not avoided". Pairs that never co-occur at
all fall straight through it: bar_(place) and computer_keyboard appear
together in 0 of 4.8M solo posts, and the sampler still offered the
keyboard because it had never been told otherwise.

This table has no per-tag cap. It holds every pair whose shortfall the
corpus can actually demonstrate, judged by the Poisson lower tail:
under independence a pair is seen Poisson(expected) times, so seeing
`observed` or fewer has probability p, and a small p means avoidance
rather than a small sample. The median tag contributes 35 pairs and the
most contradictory ones ~10k, which a fixed cap can only get wrong in
one direction or the other.

alpha is the runtime knob: the significance is stored per pair, so
tightening or loosening the test costs a comparison rather than a
rebuild. Built by playground/tag-conflict-filter/precompute_avoidance.py.
"""

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

_PATH = artifact.resource("avoidance_v1.npz")
# not committed (14MB); fetched from the data release on first use
_URL = artifact.url_for("data-v1.0.0", "avoidance_v1.npz")
_SHA256 = "fad88158098e6e1f6a4f90cf24f85eb7d312b1f489858a6f1c1c9ac0a3441b26"

# The table is built at alpha 0.05 and cannot be loosened past it. This
# default is tighter: at 0.05 one pair in twenty is flagged by chance,
# and a veto that fires wrongly is expensive here -- it silently removes
# a tag the prompt may have wanted.
DEFAULT_ALPHA = 0.01


class Avoidance:
    """Directed pair lookup: which tags does this context tag avoid?"""

    def __init__(self, vocab, path=_PATH):
        import numpy as np

        if path == _PATH:
            artifact.ensure(path, _URL, _SHA256, "Avoidance", "14MB")
        data = np.load(path, allow_pickle=False)
        self._np = np
        self.indptr = data["indptr"]
        self.ids = data["ids"]
        self.sig = data["sig"]
        self.scale = float(data["sig_scale"][0])
        # the table has its own vocabulary; map it onto the caller's once
        # so lookups are integer slicing afterwards. It stores the space
        # form and the sampler the underscore form, so match on spaces.
        table_tags = [str(t) for t in data["tags"]]
        where = {t.replace("_", " "): i for i, t in enumerate(vocab)}
        self._row_of = np.full(len(vocab), -1, dtype=np.int64)
        self._col_of = np.full(len(table_tags), -1, dtype=np.int64)
        for i, tag in enumerate(table_tags):
            j = where.get(tag)
            if j is not None:
                self._row_of[j] = i
                self._col_of[i] = j
        self._size = len(vocab)

    def mask(self, ids, alpha):
        """Tags avoided by any of `ids`, as a bool mask over the vocab."""
        np = self._np
        banned = np.zeros(self._size, dtype=bool)
        if alpha <= 0:
            return banned
        cut = -np.log10(alpha) * self.scale
        for i in ids:
            row = self._row_of[i]
            if row < 0:
                continue
            lo, hi = self.indptr[row], self.indptr[row + 1]
            if lo == hi:
                continue
            hits = self.ids[lo:hi][self.sig[lo:hi] >= cut]
            mapped = self._col_of[hits]
            banned[mapped[mapped >= 0]] = True
        return banned


@artifact.lazy
def load_avoidance(vocab):
    """The avoidance table, or False when the artifact is missing."""
    return Avoidance(vocab)
