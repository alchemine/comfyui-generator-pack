"""Category and rating labels for the tag vocabulary.

Four JSON layers under resources/group/ answer, for any tag, "which
knob does this belong to" and "how explicit is it":

    tags_v1.0.json        tag  -> [danbooru wiki group, ...]
    hierarchy_v1.0.json   the wiki's group tree, plus the groups its
                          table of contents omits and five of our own
    categories_v1.0.json  which tree nodes each user-facing category
                          owns, and the order that resolves a tag
                          whose groups span several
    ratings_v1.0.json     tag  -> g/s/q/e, from rating-tier statistics

A tag's category is the first category in `priority` order owning any
of its groups; a tag with no known group falls to the last category.
Ratings are cumulative, so a level is a ceiling: asking for "s" admits
g and s tags.
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

        tree = load("hierarchy_v1.0.json")
        cats = load("categories_v1.0.json")
        self._groups = load("tags_v1.0.json")
        self._ratings = load("ratings_v1.0.json")

        self.names = list(cats["priority"])
        self._fallback = len(self.names) - 1  # "etc"

        children = {}

        def walk(node):
            for name, sub in node.items():
                children[name] = sub
                walk(sub)

        walk(tree)

        def descendants(name):
            out, stack = {name}, [children.get(name, {})]
            while stack:
                for key, sub in stack.pop().items():
                    out.add(key)
                    stack.append(sub)
            return out

        # group -> highest-priority category that owns it
        self._group_cat = {}
        for rank, name in enumerate(self.names):
            spec = cats["categories"].get(name, [])
            # a category is a list of tree nodes, or {include, exclude}
            # when it wants a node's subtree minus a branch of it: the
            # wiki files ears under the face, which is true anatomy and
            # useless here -- "rabbit ears" is not an expression
            if isinstance(spec, dict):
                roots = spec.get("include", [])
                blocked = set()
                for name_ in spec.get("exclude", []):
                    blocked |= descendants(name_)
            else:
                roots, blocked = spec, ()
            for root in roots:
                for group in descendants(root):
                    if group not in blocked and group not in self._group_cat:
                        self._group_cat[group] = rank

    def category_of(self, tag):
        """The category most of the tag's groups point at.

        Majority rather than strict priority, because wiki membership is
        noisy in a way priority amplifies: "beach" is filed under
        locations, water *and* swimsuit, and "building" under locations
        and the gerund list, so whichever category ranks highest would
        win on a single stray group. Ties fall back to priority order.
        """
        votes = {}
        for group in self._groups.get(normalize(tag), ()):
            rank = self._group_cat.get(group)
            if rank is not None:
                votes[rank] = votes.get(rank, 0) + 1
        if not votes:
            return self._fallback
        best = max(votes.values())
        return min(rank for rank, n in votes.items() if n == best)

    def rating_of(self, tag, default=3):
        """Rating level index, `default` when the tag has no label.

        Callers that mask by rating want the cautious default (explicit,
        so an unlabelled tag cannot slip into a mild request); callers
        that only describe a tag want the permissive one.
        """
        level = self._ratings.get(normalize(tag))
        return RATING_ORDER.index(level) if level in RATING_ORDER else default

    def category_name(self, tag):
        return self.names[self.category_of(tag)]

    def knows(self, tag):
        return normalize(tag) in self._groups

    def arrays(self, vocab):
        """(category index, rating level) arrays aligned to `vocab`."""
        import numpy as np

        cats = np.fromiter(
            (self.category_of(t) for t in vocab), dtype=np.int8, count=len(vocab)
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
