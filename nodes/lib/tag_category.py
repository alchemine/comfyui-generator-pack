"""Category and rating labels for the tag vocabulary.

Two JSON files under resources/group/ answer, for any tag, "which
knob does this belong to" and "how explicit is it":

    categories_v2.2.json  tag  -> category, the part of the picture the
                          tag describes; `order` fixes the indices
    ratings_v1.0.json     tag  -> g/s/q/e, from rating-tier statistics

A tag the table does not list has no category. Ratings are
cumulative, so a level is a ceiling: asking for "s" admits g and s
tags.
"""

import json
import math
import os

try:
    from . import artifact
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact

RATING_ORDER = ("g", "s", "q", "e")

_DIR = artifact.resource("group")


def normalize(tag):
    return tag.strip().lower().replace("_", " ")


class Labels:
    """Tag -> category index and rating level, from the group JSONs."""

    def __init__(self, directory=_DIR):
        def load(name):
            path = (
                artifact.bundled("group", name)
                if directory == _DIR
                else os.path.join(directory, name)
            )
            with open(path, encoding="utf-8") as f:
                return json.load(f)

        cats = load("categories_v2.2.json")
        self._ratings = load("ratings_v1.0.json")

        self.names = list(cats["order"])
        rank_of = {name: i for i, name in enumerate(self.names)}
        self._category = {tag: rank_of[name] for tag, name in cats["tags"].items()}

    def category_of(self, tag):
        """Category index, None when the tag is unlabelled."""
        return self._category.get(normalize(tag))

    def rating_of(self, tag, default=3):
        """Rating level index, `default` when the tag has no label.

        Callers that mask by rating want the cautious default (explicit,
        so an unlabelled tag cannot slip into a mild request); callers
        that only describe a tag want the permissive one.
        """
        level = self._ratings.get(normalize(tag))
        return RATING_ORDER.index(level) if level in RATING_ORDER else default

    def category_name(self, tag):
        rank = self.category_of(tag)
        return None if rank is None else self.names[rank]

    def knows(self, tag):
        return normalize(tag) in self._category

    def arrays(self, vocab):
        """(category index, rating level) arrays aligned to `vocab`.

        An unlabelled tag gets index -1, which no category spec allows.
        """
        import numpy as np

        cats = np.fromiter(
            (self._category.get(normalize(t), -1) for t in vocab),
            dtype=np.int8,
            count=len(vocab),
        )
        levels = np.fromiter(
            (self.rating_of(t) for t in vocab), dtype=np.int8, count=len(vocab)
        )
        return cats, levels


@artifact.lazy
def load_labels():
    """The category/rating labels, or False when they are missing."""
    return Labels()


def parse_categories(spec, names):
    """Parse a category request into (allowed ranks, shares by group).

    "" or None          -> (None, None): everything allowed, no quota
    "pose, clothes"     -> only those, no limit on either
    "pose:2, body:3"    -> same, and the output is split between them in
                           that proportion
    "background+objects:1, pose:2" -> background and objects draw on one
                           shared budget, a third of the output

    Shares are weights relative to each other, not fractions of the tag
    count: what matters is that pose is worth twice what expressions is,
    so switching a category off hands its share to the ones still on
    instead of shrinking the result. resolve_quota turns them into
    counts once the length is known -- it is the only side that knows it.

    A group joined with "+" is one budget several categories draw on. It
    is what lets one widget stand for several label categories without
    each of them quietly getting the widget's share to itself.

    Unknown names are ignored; a spec that names nothing usable behaves
    like an empty spec so a typo cannot silence the generator.
    """
    if not spec or not spec.strip():
        return None, None
    rank_of = {name: i for i, name in enumerate(names)}
    allowed, groups = set(), []
    for item in spec.replace("\n", ",").split(","):
        item = item.strip()
        if not item:
            continue
        head, _, share = item.partition(":")
        ranks = tuple(
            r
            for r in (rank_of.get(part.strip().lower()) for part in head.split("+"))
            if r is not None
        )
        if not ranks:
            continue
        allowed.update(ranks)
        share = share.strip()
        if not share:
            continue
        try:
            value = float(share)
        except ValueError:
            continue
        if value > 0.0:
            groups.append((ranks, value))
    if not allowed:
        return None, None
    return allowed, (groups or None)


def resolve_quota(groups, total):
    """Split `total` tags between the groups, in proportion to their shares.

    Largest remainder, so the counts add up to exactly `total` rather
    than to whatever independent rounding happens to produce: two groups
    at 2 and 1 over ten tags are 7 and 3, not 7 and 4. That makes a
    share a budget the sampler fills, which is how anyone setting one
    reads it -- "pose 2, expressions 1" means two thirds of the output
    is pose.

    Returns {rank: (group key, cap)} so the caller can count a pick
    against the budget its category draws on, whether that budget
    belongs to one category or several.
    """
    if not groups or total <= 0:
        return None
    weight = sum(share for _, share in groups)
    if weight <= 0:
        return None
    exact = [share / weight * total for _, share in groups]
    caps = [int(math.floor(v)) for v in exact]
    spare = total - sum(caps)
    # hand the leftovers to whoever was rounded down hardest
    for k in sorted(range(len(groups)), key=lambda i: exact[i] - caps[i], reverse=True)[
        :spare
    ]:
        caps[k] += 1
    out = {}
    for key, ((ranks, _), cap) in enumerate(zip(groups, caps)):
        for rank in ranks:
            out[rank] = (key, cap)
    return out
