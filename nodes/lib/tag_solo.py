"""Solo guard: what a one-person prompt cannot contain.

The tables everywhere else in this pack are statistical, and for the
subject count that runs out. tag_subject catches what two subject tags
rule out between them, and it works -- "1girl, solo" bans 113 tags, all
of them the second character's body or clothes: 1boy, beard, cat boy,
male underwear. What it never catches is the second character's *doing*:

    solo x rape          no stored conflict pair
    solo x sex           no stored conflict pair
    solo x hetero        no stored conflict pair

Not a gap in the data but a fact about it. Danbooru tags those on solo
pictures often enough -- the partner off-frame, a POV crop, implied
rape -- that the pair is not statistically surprising, so no amount of
corpus would flag it. TagVeto could not weigh it either: it only
compares subject tags against subject tags, since matching a subject
against an ordinary tag floods on pairs like 1boy x large breasts.

So this is a rule, not a measurement, and it is spelled out in
resources/solo_conflict.txt rather than learned. Two of them:

  * a tag naming "another" needs another person. The word is the
    evidence, and it covers 140 tags -- half of which the statistics
    already miss -- without anyone listing them.

  * a tag on the [multi_person] list needs one too, for reasons its
    spelling does not carry: hug, headpat, interlocked fingers.

Both hold only while the prompt's subject tags add up to one person.
[male_anatomy] answers a different question -- whose body, not how
many -- and applies when that one person is a girl and nothing in the
prompt says otherwise. Its negations ("no penis", "no testicles") are
on it too: a tag naming male anatomy to deny it still puts the word in
front of the model, which is the confusion the veto exists to avoid.
"""
import re

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

_PATH = artifact.resource("solo_conflict.txt")

# "another" is the one multi-person marker reliable enough to read off
# the spelling: every tag carrying it -- "grabbing another's hand",
# "undressing another" -- names a second person by definition, and no
# solo tag borrows the word. Cheaper and more complete than listing all
# 140, and it keeps covering new ones after a data release.
_ANOTHER = "another"

_COUNT_RE = re.compile(r"^(\d+)\+?(girl|boy|other)s?$")

# Anything that says the one person is not simply a girl, and so takes
# the male-anatomy veto off. "crossdressing" is deliberately absent: a
# girl in boys' clothes is still a girl, and "otoko no ko" already
# covers the other reading.
_NOT_FEMALE_ONLY = frozenset({
    "futanari", "newhalf", "otoko no ko", "male focus", "multiple boys",
    "1boy", "2boys", "3boys", "4boys", "5boys", "6+boys",
})

# Subject tags that put more than one character in the picture whatever
# the counts say, so a prompt carrying one is never "alone".
_CROWD = frozenset({
    "solo focus", "multiple girls", "multiple boys", "multiple others",
    "everyone",
})


@artifact.lazy
def _sections():
    """{section: frozenset(tags)} from the resource file.

    artifact.lazy makes a missing or malformed file degrade to False --
    the guard then does nothing, which is the same contract every other
    table here honours.
    """
    sections, name = {}, None
    with open(artifact.bundled("solo_conflict.txt"), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                name = line[1:-1]
                sections[name] = set()
            elif name:
                sections[name].add(line)
    return {k: frozenset(v) for k, v in sections.items()}


def context(tags):
    """(one person only, that person is a girl) for a prompt.

    "solo" is the direct statement and outranks the counts, which is
    what lets "1girl, solo" and a bare "1girl" both qualify. "solo
    focus" is the opposite claim -- one subject among others -- so it
    disqualifies however the counts read.
    """
    tags = {t.replace("_", " ").strip().lower() for t in tags if t}
    if tags & _CROWD:
        return False, False
    counted = [m for m in map(_COUNT_RE.match, tags) if m]
    if "solo" not in tags and sum(int(m.group(1)) for m in counted) != 1:
        return False, False
    # a bare "solo" says one person without saying whose body it is, so
    # the male-anatomy veto waits for a count tag to name a girl
    female = not (tags & _NOT_FEMALE_ONLY) and any(
        m.group(2) == "girl" for m in counted)
    return True, female


def masks(vocab):
    """(multi-person veto, male-anatomy veto) as arrays over `vocab`.

    Both are properties of the vocabulary rather than of any one
    prompt, so the caller builds them once and picks per prompt -- see
    TagSuggest.solo_masks. A missing file costs the lists but not the
    "another" rule, which needs nothing but the spelling.
    """
    import numpy as np
    sections = _sections() or {}
    multi = sections.get("multi_person", frozenset())
    male = sections.get("male_anatomy", frozenset())
    spelled = [t.replace("_", " ") for t in vocab]
    return (np.array([_ANOTHER in t or t in multi for t in spelled]),
            np.array([t in male for t in spelled]))
