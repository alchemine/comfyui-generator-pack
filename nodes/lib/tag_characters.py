"""The character pool CharacterTagsGenerator draws from.

resources/characters_v1.txt holds one row per Danbooru character tag
with at least 100 posts in danbooru-2026-clean-metadata (to 2025-09):
name (spaced), posts, the year of its first post, and its sex -- the
one of 1girl, 1boy, 1other found on the most solo posts with it, other
on a tie or none. Built by
playground/tag-conflict-filter/precompute_characters.py.
"""

from collections import namedtuple

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

_PATH = artifact.resource("characters_v1.txt")
# not committed (560KB); fetched from the data release on first use
_URL = artifact.url_for("data-v2.0.0", "characters_v1.txt")
_SHA256 = "f5c8c3787759c411fe416490aff95df567a75f8d3d84db8f3d0151085fe1bbf4"

Character = namedtuple("Character", "name posts first_year sex")


@artifact.lazy
def load_characters():
    """Every character row, most posts first, or False if the file is missing."""
    artifact.ensure(_PATH, _URL, _SHA256, "CharacterTagsGenerator", "560KB")
    with open(_PATH, encoding="utf-8") as f:
        rows = (line.rstrip("\n").split("\t") for line in f)
        return [Character(n, int(p), int(y), s) for n, p, y, s in rows]
