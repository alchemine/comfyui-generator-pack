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

resources/copyright_blacklist.txt adds the tags the statistics cannot
justify -- near-misses under the thresholds, and tags a checkpoint
pulls toward an owner the corpus does not. It is meant to be edited,
and an edited copy is never overwritten.
"""

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

_PATH = artifact.resource("copyright_v1.npz")
# not committed (370KB); fetched from the data release on first use
_URL = artifact.url_for("data-v1.0.0", "copyright_v1.npz")
_SHA256 = ("9539fcd6a0271dd4234a244114aabbd5"
           "bdf4fe823de53a2cd56f9ecdb931f31e")

# A tag is a signature only when both halves of the evidence agree,
# the same both-or-neither structure as the veto's E_MIN gate: the
# share says the owner dominates the tag, the lift says that is not
# just the owner dominating the corpus. Share alone ate geta and
# no headwear (0.60/0.66 touhou -- volume, x6 lift); lift alone cannot
# tell mob cap (x9, the touhou ceiling) from ascot (x5), and explodes
# for niche owners (bodystocking x158 on one Genshin character).
# Calibrated on labeled tags -- the build log prints the table.
CHAR_SHARE = 0.5    # above aqua hair 0.45 (Miku), below bat wings 0.55
CHAR_LIFT = 20.0    # true signatures sit at x64-x222
COPY_SHARE = 0.6    # above serafuku 0.36, witch hat 0.40
COPY_LIFT = 8.0     # geta/no headwear x6 stay; mob cap x9, umamusume x66 go


class Copyright:
    """Boolean mask over the caller's vocabulary: True = signature tag."""

    def __init__(self, vocab, path=_PATH):
        import numpy as np
        if path == _PATH:
            artifact.ensure(path, _URL, _SHA256, "Copyright", "2MB")
        data = np.load(path, allow_pickle=False)
        sig = (((data["char_score"].astype(np.float64) >= CHAR_SHARE)
                & (data["char_lift"].astype(np.float64) >= CHAR_LIFT))
               | ((data["copy_score"].astype(np.float64) >= COPY_SHARE)
                  & (data["copy_lift"].astype(np.float64) >= COPY_LIFT)))
        table = {str(t): bool(s) for t, s in zip(data["tags"], sig)}
        extra = _extra_tags()
        self.mask = np.fromiter(
            (table.get(t, False) or t.replace("_", " ") in extra
             for t in vocab),
            dtype=bool, count=len(vocab))


def _extra_tags():
    """The hand-kept list, as normalized spaced names; missing file = empty."""
    tags = set()
    try:
        with open(artifact.bundled("copyright_blacklist.txt"),
                  encoding="utf-8") as fh:
            for line in fh:
                tag = line.split("#", 1)[0].strip().lower().replace("_", " ")
                if tag:
                    tags.add(tag)
    except Exception:
        pass
    return tags


@artifact.lazy
def load_copyright(vocab):
    return Copyright(vocab)
