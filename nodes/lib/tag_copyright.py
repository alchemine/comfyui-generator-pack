"""Mask the tags that belong to one character or one franchise.

Co-occurrence faithfully reproduces the corpus, and on Danbooru the
corpus is fan art: "library" is Patchouli's library, so a draw seeded
with it comes back wearing her crescent hat ornament. The signature
tags are *general* tags, so neither the vocabulary (which already
excludes character and copyright tags) nor the category shares can
stop them.

copyright_v1.npz measures the leak directly: for every vocabulary tag,
the share of its posts carrying the tag's single most frequent
character tag, and the same over copyright tags ("original" excluded).
crescent hat ornament sits near 1 on both; holding book near 0. Built
by playground/tag-conflict-filter/precompute_copyright.py.

The mask removes candidates only. Signature tags the prompt itself
carries are references, never candidates, so asking for a character by
spelling out her design still works with the filter on.
"""

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

_PATH = artifact.resource("copyright_v1.npz")
# not committed (370KB); fetched from the data release on first use
_URL = artifact.url_for("data-v1.0.0", "copyright_v1.npz")
_SHA256 = ("1b719be52f00f7f00280d1f7c4d67e04"
           "dc2ddce7e2f1ba383cd58bbd24b2df7d")

# A tag is a signature when one character owns at least CHAR_THRESHOLD
# of its posts, or one franchise COPY_THRESHOLD. Calibrated on labeled
# tags (build log table): the character axis sits above aqua hair
# (0.45, half of it Miku but still a colour word) and below bat wings
# (0.55, Remilia's); the franchise axis above serafuku (0.36 kancolle)
# and witch hat (0.40 touhou), and below mob cap (0.97).
CHAR_THRESHOLD = 0.5
COPY_THRESHOLD = 0.6


class Copyright:
    """Boolean mask over the caller's vocabulary: True = signature tag."""

    def __init__(self, vocab, path=_PATH,
                 char_threshold=CHAR_THRESHOLD, copy_threshold=COPY_THRESHOLD):
        import numpy as np
        if path == _PATH:
            artifact.ensure(path, _URL, _SHA256, "Copyright", "370KB")
        data = np.load(path, allow_pickle=False)
        sig = ((data["char_score"].astype(np.float64) >= char_threshold)
               | (data["copy_score"].astype(np.float64) >= copy_threshold))
        table = {str(t): bool(s) for t, s in zip(data["tags"], sig)}
        self.mask = np.fromiter(
            (table.get(t, False) for t in vocab),
            dtype=bool, count=len(vocab))


@artifact.lazy
def load_copyright(vocab):
    return Copyright(vocab)
