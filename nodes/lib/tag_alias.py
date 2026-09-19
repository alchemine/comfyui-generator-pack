"""Let a tag be spelled any of the ways Danbooru has spelled it.

Danbooru renames tags and keeps the old spelling as an alias, so one
prompt says `no_headwear` where another says `missing_headwear`. A table
is keyed by one of the two, and the other reads as a tag nobody has ever
posted: it conditions nothing, vetoes nothing, and silently drops out of
the context. That is worse than a typo, because the tag looks right.

resources/danbooru-tags.txt is the tag dump behind the fix -- one row
per tag as `name,category,post_count,"alias,alias,..."` -- and this
module turns its fourth column into groups of interchangeable spellings.

Which spelling is "right" depends on the table, not on Danbooru. The
statistics artifacts were built against an older vocabulary and store
`no_headwear`; a checkpoint trained on that same era answers to it too,
while `missing_headwear` means nothing to either. So this module does
not rewrite tags toward the current name -- it folds a whole alias group
onto whichever member the table in front of it actually has, which is
the old name here and would be the new one after a rebuild.

Canonical names always win a contested alias: an alias is only filed
when no tag actually carries that name, and when two tags claim the same
alias the more posted one takes it.
"""

import csv

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

logger = artifact.get_logger()

_TAGS_PATH = artifact.resource("danbooru-tags.txt")

_GROUPS = None  # lazy singleton: canonical name -> every spelling of it


def _load(path=_TAGS_PATH):
    """Build the alias groups, or an empty map if the dump is missing."""
    try:
        if path == _TAGS_PATH:
            path = artifact.bundled("danbooru-tags.txt")
        with open(path, newline="", encoding="utf-8") as f:
            all_rows = [r for r in csv.reader(f) if r]
    except OSError as e:
        logger.warning("[TagAlias] %s unreadable, aliases off (%s)", path, e)
        return {}

    # a name that exists is never an alias for something else, so the
    # canonical set has to be complete before the first alias is filed
    canonical = {row[0] for row in all_rows}
    rows = [r for r in all_rows if len(r) >= 4 and r[3]]

    def post_count(row):
        try:
            return int(row[2])
        except (IndexError, ValueError):
            return 0

    # ascending, so the biggest tag overwrites the smaller claimants
    rows.sort(key=post_count)

    owner = {}  # alias -> the tag that gets to keep it
    for row in rows:
        name = row[0]
        for alias in row[3].split(","):
            alias = alias.strip()
            if alias and alias != name and alias not in canonical:
                owner[alias] = name

    groups = {}
    for alias, name in owner.items():
        groups.setdefault(name, [name]).append(alias)
    logger.debug("[TagAlias] %d aliases over %d tags", len(owner), len(canonical))
    return groups


def groups():
    """canonical name -> [canonical, alias, ...], loaded on first use."""
    global _GROUPS
    if _GROUPS is None:
        _GROUPS = _load()
    return _GROUPS


def expand_index(index):
    """Teach a tag -> id map every other spelling of the tags it has.

    Mutates and returns `index`. Only spellings the map is missing are
    added, so a table that genuinely stores two members of one group
    (Danbooru has aliased tags apart before) keeps both meanings.
    """
    added = 0
    for name, members in groups().items():
        present = [m for m in members if m in index]
        if not present:
            continue
        # `members[0]` is the canonical name, so this prefers it whenever
        # the table has it and falls back to whichever spelling it does
        target = index[present[0]]
        for member in members:
            if member not in index:
                index[member] = target
                added += 1
    logger.debug(
        "[TagAlias] %d alias spellings added to a %d-tag index",
        added,
        len(index) - added,
    )
    return index
