"""Subject-conjunction veto: what two subject tags rule out together.

Every other table here is pairwise, and the sampler scores a candidate
by summing log lift over the context -- naive Bayes, a product of
pairwise terms. For the subject count that is wrong in a way more data
cannot fix, because the contradiction lives only in the conjunction:

    lift(threesome | 1girl) = 0.59      near neutral
    lift(threesome | 1boy)  = 2.62      attracts, if anything
    product                 = 1.56      passes any veto
    lift(threesome | both)  = 0.02      52 posts where 2,636 were due

"1girl" does not mean one person, it means one girl, so 1girl+2boys
threesomes are ordinary and both pairwise terms are honest about their
own halves. Only together do they say three cannot be two.

The table stores only what the pairwise tables cannot already say (see
MAX_SURPRISE in the build script): tags whose joint lift falls far below
the product the sampler would have estimated. Everything merely
uncommon in that kind of picture -- shrimp tempura in a 1girl+1boy
scene -- is left out, because vetoing it would cost candidates without
buying consistency.

alpha is the runtime knob, as in tag_avoid: significance is stored per
entry, so tightening the test is a comparison rather than a rebuild.
Built by playground/tag-conflict-filter/precompute_subject_joint.py.
"""

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

_PATH = artifact.resource("subject_joint_v1.npz")
# not committed; fetched from the data release on first use
_URL = artifact.url_for("data-v1.0.0", "subject_joint_v1.npz")
_SHA256 = ("7cd0b1c461e81198cb30a5ea46037eb4"
           "a949c5a0a5ef6e1383039756b19be71e")

# The build runs at 1e-3. Kept the same here: unlike the avoidance
# table, an entry only survives the build if the conjunction also
# contradicts what the parts predict, so the surviving pairs are few and
# deliberate rather than a significance sweep that needs reining in.
DEFAULT_ALPHA = 1e-3

class SubjectJoint:
    """Which tags a pair of subject tags rules out between them."""

    def __init__(self, vocab, path=_PATH):
        import numpy as np
        if path == _PATH:
            artifact.ensure(path, _URL, _SHA256, "SubjectJoint", "260KB")
        data = np.load(path, allow_pickle=False)
        self._np = np
        self.scale = float(data["sig_scale"])
        subjects = [str(s) for s in data["subjects"]]
        table_tags = [str(t) for t in data["tags"]]

        where = {t: i for i, t in enumerate(vocab)}
        # the table carries its own vocabulary; map it onto the caller's
        # once so lookups afterwards are integer work only
        col_of = np.full(len(table_tags), -1, dtype=np.int64)
        for i, tag in enumerate(table_tags):
            j = where.get(tag)
            if j is not None:
                col_of[i] = j

        # subject tag -> its id in the caller's vocabulary, so the
        # runtime can find the pairs a context implies without matching
        # the is_subject rule a second time
        self.subject_ids = {}
        for s, name in enumerate(subjects):
            j = where.get(name)
            if j is not None:
                self.subject_ids[j] = s

        pair_a, pair_b = data["pair_a"], data["pair_b"]
        self._pair_of = {}
        for k, (a, b) in enumerate(zip(pair_a, pair_b)):
            self._pair_of[(int(a), int(b))] = k
            self._pair_of[(int(b), int(a))] = k

        veto_pair, veto_tag = data["veto_pair"], data["veto_tag"]
        self._sig = data["veto_sig"]
        self._tag = col_of[veto_tag]
        # group by pair once, so a lookup is a slice rather than a scan
        order = np.argsort(veto_pair, kind="stable")
        self._tag = self._tag[order]
        self._sig = self._sig[order]
        self.indptr = np.searchsorted(veto_pair[order],
                                      np.arange(len(pair_a) + 1))
        self._size = len(vocab)

    def mask(self, ids, alpha=DEFAULT_ALPHA):
        """Tags ruled out by the subject tags among `ids`."""
        np = self._np
        banned = np.zeros(self._size, dtype=bool)
        present = [self.subject_ids[i] for i in ids if i in self.subject_ids]
        if len(present) < 2 or alpha <= 0:
            return banned
        cut = -np.log10(alpha) * self.scale
        for x in range(len(present)):
            for y in range(x + 1, len(present)):
                k = self._pair_of.get((present[x], present[y]))
                if k is None:
                    continue                  # pair too rare to have data
                lo, hi = self.indptr[k], self.indptr[k + 1]
                if lo == hi:
                    continue
                hits = self._tag[lo:hi][self._sig[lo:hi] >= cut]
                banned[hits[hits >= 0]] = True
        return banned


@artifact.lazy
def load_subject_joint(vocab):
    """The subject-conjunction table, or False when it is missing."""
    return SubjectJoint(vocab)
