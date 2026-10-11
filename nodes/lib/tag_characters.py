"""Which tags name a character.

resources/characters_v1.txt is the pool CharacterTagsGenerator draws
from: one row per Danbooru character tag with at least 100 posts in
danbooru-2026-clean-metadata (to 2025-09): name (spaced), posts, the
year of its first post, and its sex -- the one of 1girl, 1boy, 1other
found on the most solo posts with it, other on a tie or none. Built by
playground/tag-conflict-filter/precompute_characters.py.

resources/danbooru-tags.txt (name, category, posts, aliases) names
every character tag, however few its posts, and is what ClassifyTags
recognises characters by.
"""

import csv
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

# Danbooru's category code for character tags in the dump
_CHARACTER = "4"


@artifact.lazy
def load_characters():
    """Every character row, most posts first, or False if the file is missing."""
    artifact.ensure(_PATH, _URL, _SHA256, "CharacterTagsGenerator", "560KB")
    with open(_PATH, encoding="utf-8") as f:
        rows = (line.rstrip("\n").split("\t") for line in f)
        return [Character(n, int(p), int(y), s) for n, p, y, s in rows]


@artifact.lazy
def character_names():
    """Every character tag and alias in the dump, spaced and lowercased."""
    with open(artifact.bundled("danbooru-tags.txt"), newline="", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if len(r) >= 2 and r[1] == _CHARACTER]
    names = set()
    for row in rows:
        aliases = row[3].split(",") if len(row) >= 4 else []
        for spelling in [row[0], *aliases]:
            spelling = spelling.strip().lower().replace("_", " ")
            if spelling:
                names.add(spelling)
    return names
