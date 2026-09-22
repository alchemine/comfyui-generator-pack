"""Find the Danbooru tags a sentence actually names.

A language model asked for tags invents spellings Danbooru never used
and pairs that contradict each other; a model trained to emit tags
cannot be told what not to say. This module goes the other way round:
the sentence is matched against the tag vocabulary, so nothing comes
back that is not a real tag, and nothing comes back that the sentence
did not say.

resources/danbooru-tags.txt (name, aliases) is loaded into two
in-memory FTS5 tables, one spelled as written and one under the porter
stemmer, and every 1- to 3-word run of the sentence is looked up as a
whole spelling: a run matches a tag only when it covers the tag's whole
name, so "ponytail" never pulls in "high ponytail". Longer runs win the
words they cover, so "low ponytail" is one tag, not two. The stemmed
table is what lets "sits" reach "sitting", and it is consulted only for
a run with an inflected word in it, because the stemmer also folds
"short" onto "shorts".

Danbooru files many aliases that are a name cut short -- "sitting on"
for sitting on person, "blonde" for blonde hair. Such an alias is
trusted only at the end of its run: "sitting on a chair" carries on
where the name would, and so means something else.

"no", "not" and "without" open a negated span that runs to the next
"and"/"but"/"with" or punctuation. The span is first tried as a tag of
its own -- "no hat" is an alias of missing headwear -- and whatever it
does not claim is left out, so "without a hat" contributes no hat.

Who is in the picture is counted rather than looked up: "a girl and two
boys" is 1girl and 2boys, and a lone person is also solo. The person
nouns are consumed by the count, so "a man" never reaches male focus
through its alias. An object pronoun after a verb -- "hugging him",
"looking at her" -- is someone else in the picture: it is read as
"another", which is how Danbooru spells it (looking at another), and it
takes solo away. The count is final: when it says solo, no stage may
answer with a tag spelled "another", and the next spelling or
definition down takes its place.

A phrase the vocabulary does not spell at all is looked for in the
Danbooru wiki instead: the first sentence of every general tag's page
(resources/wiki_definitions_v1.txt) is a third table, and a run of two
or more words no spelling claimed is matched against it, most posted
tag first -- "taking off" is in the definition of undressing. Only leftover
runs go there, never single words, because a definition names the
things around its tag too: "chair" sits in the definition of sitting,
and "surface" would reach it.

Every match is reported alongside the tags, with the spelling it came
in through and the tag's post count, so a wrong turn -- "taking off"
reaching takeoff through its alias "take-off" -- can be read off the
node rather than guessed at. min_count is the lever for that case, and
with takeoff under it the wiki stage gets its turn.
"""

import csv
import re
import sqlite3
from collections import namedtuple

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

logger = artifact.get_logger()

_WIKI_PATH = artifact.resource("wiki_definitions_v1.txt")
# not committed (2MB); fetched from the data release on first use. Built
# by playground/extract_wiki_definitions.py from the wiki dump.
_WIKI_URL = artifact.url_for("data-v1.1.0", "wiki_definitions_v1.txt")
_WIKI_SHA256 = "e05988eb614bc6ccb0eb21334217ab6d54e36b2193a14267b613f5c31d0ebf28"

MAX_WORDS = 3  # longest tag spelling looked up, in words
MIN_WIKI_WORDS = 2  # shortest leftover run the wiki is asked about
# words that carry no tag of their own and would otherwise split "hand on
# her hip" away from `hand on own hip`
SKIPPED = {
    "a",
    "an",
    "the",
    "she",
    "he",
    "they",
    "it",
    "her",
    "his",
    "their",
    "its",
    "my",
    "your",
    "is",
    "are",
    "was",
    "were",
}
NEGATIONS = {"no", "not"}
# object pronouns: after a verb they are someone else in the picture
OBJECTS = {"her", "him", "them"}
# a verb reaches its object through these too: "looking at him"
LINKS = {"at", "to", "with", "toward", "towards"}
# where a negated span ends; the sentence's own punctuation ends it too
BOUNDARIES = {"and", "but", "with", "while", "or", "then"}
# a run made of these alone ("and in") is not a phrase the wiki should
# be asked about
FUNCTION_WORDS = (
    BOUNDARIES
    | LINKS
    | {
        "in",
        "on",
        "of",
        "by",
        "for",
        "from",
        "off",
        "up",
        "down",
        "out",
        "over",
        "under",
    }
)

COUNTS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
}
PERSONS = {
    "girl": "girl",
    "woman": "girl",
    "lady": "girl",
    "boy": "boy",
    "man": "boy",
    "guy": "boy",
}
PLURALS = {
    "girls": "girl",
    "women": "girl",
    "ladies": "girl",
    "boys": "boy",
    "men": "boy",
    "guys": "boy",
}

_WORD_RE = re.compile(r"\w+")
_INFLECTED_RE = re.compile(r"(s|ing|ed)$")
# a run of words with no punctuation between them, so "no hat, red dress"
# keeps the dress
_CLAUSE_RE = re.compile(r"[^,.;:!?()\n]+")

_INDEX = None  # lazy singleton: sqlite connection with the three tables

# one row of the report: the words that matched, the tag they reached,
# the spelling they reached it through ("wiki" for a definition hit),
# its post count, and what became of it -- "kept", "below min_count",
# "blacklisted", "subject off"
Match = namedtuple("Match", "phrase tag spelling posts verdict")


def _load(path=None):
    """Build the spelling tables, or None if the dump is missing."""
    path = path or artifact.bundled("danbooru-tags.txt")
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.reader(f) if len(r) >= 3 and r[1] == "0"]
    except OSError as e:
        logger.warning("[TagSearch] %s unreadable, search off (%s)", path, e)
        return None

    # one row per spelling, so a run can be required to cover a whole
    # spelling by its word count; the tokenizers split on the same
    # non-word characters _WORD_RE does, which keeps the counts in step
    spellings = []
    for row in rows:
        name = row[0].replace("_", " ")
        name_words = _WORD_RE.findall(name)
        posts = int(row[2])
        aliases = row[3].split(",") if len(row) >= 4 else []
        for spelling in [name, *aliases]:
            spelling = spelling.strip().replace("_", " ")
            words = _WORD_RE.findall(spelling)
            if not 0 < len(words) <= MAX_WORDS:
                continue
            truncated = (
                len(words) < len(name_words) and words == name_words[: len(words)]
            )
            spellings.append((name, spelling, len(words), int(truncated), posts))

    db = sqlite3.connect(":memory:", check_same_thread=False)
    for table, tokenize in (("exact", "unicode61"), ("stemmed", "porter unicode61")):
        db.execute(
            "CREATE VIRTUAL TABLE %s USING fts5("
            "tag UNINDEXED, spelling, words UNINDEXED, truncated UNINDEXED, "
            "posts UNINDEXED, tokenize='%s')" % (table, tokenize)
        )
        db.executemany("INSERT INTO %s VALUES (?, ?, ?, ?, ?)" % table, spellings)
    db.execute(
        "CREATE VIRTUAL TABLE definitions USING fts5("
        "tag UNINDEXED, sentence, posts UNINDEXED, tokenize='porter unicode61')"
    )
    db.executemany(
        "INSERT INTO definitions VALUES (?, ?, ?)",
        _definitions({r[0]: int(r[2]) for r in rows}),
    )
    logger.debug("[TagSearch] %d spellings over %d tags", len(spellings), len(rows))
    return db


def _definitions(posts_of):
    """(tag, first wiki sentence, posts) rows, or none if the file is missing.

    The wiki stage is optional the way the statistics tables are: the
    node searches spellings alone rather than failing the workflow.
    """
    try:
        path = artifact.ensure(
            _WIKI_PATH, _WIKI_URL, _WIKI_SHA256, "TagsExtractor", "2MB"
        )
    except Exception as e:
        logger.warning(
            "[TagSearch] wiki definitions unavailable, spellings only: %s", e
        )
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            tag, _, sentence = line.rstrip("\n").partition("\t")
            if tag in posts_of:
                rows.append((tag.replace("_", " "), sentence, posts_of[tag]))
    return rows


def _index():
    global _INDEX
    if _INDEX is None:
        _INDEX = _load()
    return _INDEX


def _lookup(db, words, at_end, solo):
    """The most posted (tag, spelling, posts) spelled exactly `words`, or None.

    With one person in the picture a tag spelled with "another" cannot
    be it, so the next spelling down takes its place.
    """
    phrase = '"%s"' % " ".join(words)
    tables = ["exact"]
    if any(_INFLECTED_RE.search(w) for w in words):
        tables.append("stemmed")
    for table in tables:
        row = db.execute(
            "SELECT tag, spelling, posts FROM %s WHERE %s MATCH ? AND words = ? "
            "AND (truncated = 0 OR ?) AND (? OR tag NOT LIKE '%%another%%') "
            "ORDER BY posts DESC LIMIT 1" % (table, table),
            (phrase, len(words), at_end, not solo),
        ).fetchone()
        if row:
            return row
    return None


def _lookup_definition(db, words, min_count, solo):
    """The most posted tag whose wiki definition carries the phrase `words`.

    With one person in the picture a tag spelled with "another" cannot
    be it, so the next tag down takes its place.
    """
    return db.execute(
        "SELECT tag, posts FROM definitions WHERE definitions MATCH ? AND posts >= ? "
        "AND (? OR tag NOT LIKE '%another%') ORDER BY posts DESC LIMIT 1",
        ('"%s"' % " ".join(words), min_count, not solo),
    ).fetchone()


def _spans(words):
    """(start, end, negated) for each run of words a tag may be found in."""
    spans = []
    start = 0
    while start < len(words):
        if words[start] in BOUNDARIES:
            start += 1
            continue
        negated = words[start] in NEGATIONS
        end = start + 1
        while (
            end < len(words)
            and words[end] not in BOUNDARIES
            and (negated or words[end] not in NEGATIONS)
        ):
            end += 1
        spans.append((start, end, negated))
        start = end + 1 if end < len(words) and words[end] in BOUNDARIES else end
    return spans


def _match_span(db, words, negated, min_count, solo):
    """Matches in one span, longest spelling first, each word claimed once.

    A negated span may only yield the tag that starts on its negation
    word (`no hat`); the words it leaves unclaimed are what the sentence
    said is absent, so they yield nothing. A tag under `min_count` is
    reported but claims nothing, so a shorter run under it can still
    match. What no spelling claimed is then tried, in runs of two words
    or more, against the wiki definitions.
    """
    claimed = [False] * len(words)
    found = []  # (position, Match)
    for n in range(min(MAX_WORDS, len(words)), 0, -1):
        for i in range(len(words) - n + 1):
            if any(claimed[i : i + n]):
                continue
            if negated and i != 0:
                continue
            row = _lookup(db, words[i : i + n], i + n == len(words), solo)
            if row is None:
                continue
            tag, spelling, posts = row
            if posts < min_count:
                found.append(
                    (
                        i,
                        Match(
                            " ".join(words[i : i + n]),
                            tag,
                            spelling,
                            posts,
                            "below min_count",
                        ),
                    )
                )
                continue
            claimed[i : i + n] = [True] * n
            found.append(
                (i, Match(" ".join(words[i : i + n]), tag, spelling, posts, "kept"))
            )
    if not negated:
        for n in range(min(MAX_WORDS, len(words)), MIN_WIKI_WORDS - 1, -1):
            for i in range(len(words) - n + 1):
                if any(claimed[i : i + n]):
                    continue
                if all(w in FUNCTION_WORDS for w in words[i : i + n]):
                    continue
                row = _lookup_definition(db, words[i : i + n], min_count, solo)
                if row is None:
                    continue
                tag, posts = row
                claimed[i : i + n] = [True] * n
                found.append(
                    (i, Match(" ".join(words[i : i + n]), tag, "wiki", posts, "kept"))
                )
    return [m for _, m in sorted(found, key=lambda x: x[0])]


def _count_persons(words, counts):
    """Tally `words`' person nouns into `counts`; the words left over.

    A noun takes the number just before it ("two girls", "3 boys"); an
    unnumbered plural counts as many, an unnumbered singular as one.
    """
    rest = []
    for i, w in enumerate(words):
        kind = PERSONS.get(w) or PLURALS.get(w)
        if kind is None:
            rest.append(w)
            continue
        number = words[i - 1] if i else ""
        if number in COUNTS or number.isdigit():
            counts[kind] += int(COUNTS.get(number) or number)
            rest.pop()
        elif w in PLURALS:
            counts[kind] = float("inf")
        else:
            counts[kind] += 1
    return rest


def _mark_another(words, counts):
    """Read an object pronoun after a verb as "another", and count them.

    "hugging him" is a hug given to someone else, which is what Danbooru
    spells with another (looking at another, undressing another); the
    someone else is also one more person, so solo goes away.
    """
    out = []
    for i, w in enumerate(words):
        before = words[max(0, i - 2) : i]
        if before and w in OBJECTS:
            if before[-1].endswith("ing") or (
                len(before) == 2 and before[1] in LINKS and before[0].endswith("ing")
            ):
                counts["another"] = True
                w = "another"
        out.append(w)
    return out


def _subject_tags(counts):
    """The subject count tags for a tally, solo included when it is one."""
    tags = []
    for kind in ("girl", "boy"):
        n = counts[kind]
        if n == float("inf"):
            tags.append("multiple %ss" % kind)
        elif n >= 6:
            tags.append("6+%ss" % kind)
        elif n > 1:
            tags.append("%d%ss" % (n, kind))
        elif n == 1:
            tags.append("1%s" % kind)
    if counts["girl"] + counts["boy"] == 1 and not counts["another"]:
        tags.append("solo")
    return tags


def search(text, max_tags=20, blacklist=None, subject=True, min_count=100):
    """(tags, matches) for `text`: the Danbooru tags it names, in reading
    order and at most `max_tags`, and every match the search made.

    The person count (1girl, 2boys, solo) leads, as matches of its own;
    `subject` off drops it from the tags at the very end, after it has
    ruled on the rest. The person nouns are counted either way and
    never searched. `min_count` drops tags with fewer posts; `blacklist`
    is a compiled regex. Both drop before the count is taken, and both
    leave their trace in the matches.
    """
    db = _index()
    if db is None:
        return [], []

    # the count comes first, over the whole text, because it rules on
    # what the search may find afterwards
    counts = {"girl": 0, "boy": 0, "another": False}
    clauses = []
    for clause in _CLAUSE_RE.findall(text.lower()):
        words = _count_persons(_WORD_RE.findall(clause), counts)
        words = _mark_another(words, counts)
        clauses.append(
            ["no" if w == "without" else w for w in words if w not in SKIPPED]
        )
    subject_tags = _subject_tags(counts)
    solo = "solo" in subject_tags

    matches = [Match("(count)", t, t, None, "kept") for t in subject_tags]
    for words in clauses:
        for start, end, negated in _spans(words):
            matches.extend(_match_span(db, words[start:end], negated, min_count, solo))

    tags = []
    for i, m in enumerate(matches):
        if m.verdict != "kept":
            continue
        if blacklist and blacklist.search(m.tag):
            matches[i] = m._replace(verdict="blacklisted")
        elif not subject and m.phrase == "(count)":
            matches[i] = m._replace(verdict="subject off")
        elif m.tag not in tags:
            tags.append(m.tag)
    return tags[:max_tags], matches


def search_tags(text, max_tags=20, blacklist=None, subject=True, min_count=100):
    """The tags half of `search`."""
    return search(text, max_tags, blacklist, subject, min_count)[0]


def format_table(matches, min_count):
    """One line per match, the threshold below."""
    if not matches:
        return ""
    header = ("phrase", "tag", "via", "posts", "verdict")
    cells = [
        (
            m.phrase,
            m.tag,
            "-" if m.spelling == m.tag else m.spelling,
            "-" if m.posts is None else str(m.posts),
            m.verdict,
        )
        for m in matches
    ]
    widths = [
        max(len(row[col]) for row in [header] + cells) for col in range(len(header))
    ]

    def fmt(row):
        return "| %s |" % " | ".join(
            cell.rjust(w) if col == 3 else cell.ljust(w)
            for col, (cell, w) in enumerate(zip(row, widths))
        )

    lines = [fmt(header), "|%s|" % "|".join("-" * (w + 2) for w in widths)]
    lines += [fmt(c) for c in cells]
    lines.append("(min_count: %d)" % min_count)
    return "\n".join(lines)
