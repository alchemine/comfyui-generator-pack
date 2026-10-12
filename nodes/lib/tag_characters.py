"""Which tags name a character.

resources/characters_v1.txt is the pool CharacterTagsGenerator draws
from: one row per Danbooru character tag with at least 100 posts in
danbooru-2026-clean-metadata (to 2025-09): name (spaced), posts, the
year of its first post, and its sex -- the one of 1girl, 1boy, 1other
found on the most solo posts with it, other on a tie or none, and other
again when it sits on no_humans posts at twice the average rate or
more (pikachu, kirby, gundams). Built by
playground/tag-conflict-filter/precompute_characters.py.

resources/danbooru-tags.txt (name, category, posts, aliases) names
every character tag, however few its posts, and is what ClassifyTags
recognises characters by.
"""

import csv
import re
from collections import namedtuple

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

_PATH = artifact.resource("characters_v1.txt")
# not committed (560KB); fetched from the data release on first use
_URL = artifact.url_for("data-v5.1.0", "characters_v1.txt")
_SHA256 = "ef76c8e7588102120ed120d0576920150ca1d986b20e7743641c51d869bd6691"

Character = namedtuple("Character", "name posts first_year sex")

# Danbooru's category codes in the dump
_GENERAL = "0"
_CHARACTER = "4"
# the trailing "(arknights)" qualifiers, all of them: amiya_(medic)_(arknights)
_QUALIFIER_RE = re.compile(r"(_\([^()]*\))+$")


@artifact.lazy
def load_characters():
    """Every character row, most posts first, or False if the file is missing."""
    artifact.ensure(_PATH, _URL, _SHA256, "CharacterTagsGenerator", "560KB")
    with open(_PATH, encoding="utf-8") as f:
        rows = (line.rstrip("\n").split("\t") for line in f)
        return [Character(n, int(p), int(y), s) for n, p, y, s in rows]


@artifact.lazy
def character_names():
    """Every character tag and alias in the dump, spaced and lowercased.

    A character's bare name counts too: Danbooru files amiya as
    amiya_(arknights) and has no alias for plain amiya, yet a prompt
    says amiya. The bare name is skipped when it is a general tag in
    its own right (rose, cat, king), where the flower is the likelier
    meaning.
    """
    with open(artifact.bundled("danbooru-tags.txt"), newline="", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if len(r) >= 2]
    general = {r[0] for r in rows if r[1] == _GENERAL}
    names = set()
    for row in rows:
        if row[1] != _CHARACTER:
            continue
        aliases = row[3].split(",") if len(row) >= 4 else []
        bare = _QUALIFIER_RE.sub("", row[0])
        spellings = [row[0], *aliases]
        if bare != row[0] and bare not in general:
            spellings.append(bare)
        for spelling in spellings:
            spelling = spelling.strip().lower().replace("_", " ")
            if spelling:
                names.add(spelling)
    return names
