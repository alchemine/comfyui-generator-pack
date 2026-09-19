"""Core logic: detect tag categories, build ban lists, filter generated tags.

Standalone (no ComfyUI dependency) so it can be unit-tested and reused.
"""

import re

try:
    from . import artifact, tag_category
    from .tag_data import (
        CLOTHES,
        CLOTHES_CONFLICTS,
        CATEGORIES,
        ACCESSORIES,
        PATTERNS,
        PATTERN_EXCEPTIONS,
    )
except ImportError:
    import artifact
    import tag_category
    from tag_data import (
        CLOTHES,
        CLOTHES_CONFLICTS,
        CATEGORIES,
        ACCESSORIES,
        PATTERNS,
        PATTERN_EXCEPTIONS,
    )

MODES = ("auto", "off", "ban_all")
CATEGORY_NAMES = (
    "clothes",
    "pose",
    "expression",
    "hair_length",
    "hair_style",
    "hair_color",
    "eye_color",
    "background",
)

_WEIGHT_RE = re.compile(r":[0-9.]+\s*$")


def normalize(tag):
    """Lowercase, underscores->spaces, strip weights/parens/backslashes."""
    t = tag.strip().lower()
    t = t.replace("\\(", "(").replace("\\)", ")")
    t = t.strip("()")
    t = _WEIGHT_RE.sub("", t)
    t = t.strip("()")
    t = t.replace("_", " ")
    return re.sub(r"\s+", " ", t).strip()


def split_prompt(prompt):
    return [normalize(t) for t in prompt.split(",") if normalize(t)]


# --- lookup tables ---------------------------------------------------------

_TAG_INDEX = {}  # tag -> (category, subcat or None)
for _sub, _tags in CLOTHES.items():
    for _t in _tags:
        _TAG_INDEX.setdefault(normalize(_t), ("clothes", _sub))
for _cat, _tags in CATEGORIES.items():
    for _t in _tags:
        _TAG_INDEX.setdefault(normalize(_t), (_cat, None))
for _t in ACCESSORIES:
    _TAG_INDEX.setdefault(normalize(_t), ("accessories", None))


def classify(tag):
    """Return (category, subcategory) for a normalized tag, or (None, None)."""
    if tag in _TAG_INDEX:
        return _TAG_INDEX[tag]
    if tag in PATTERN_EXCEPTIONS:
        return (None, None)
    for suffix, cat, sub in PATTERNS:
        # word-boundary match; compound words (sundress, microskirt) allowed
        # for longer suffixes only, to avoid e.g. "zebra" ~ "bra".
        if (
            tag == suffix
            or tag.endswith(" " + suffix)
            or (len(suffix) >= 5 and tag.endswith(suffix))
        ):
            return (cat, sub)
    return (None, None)


def detect(tags):
    """Map tags -> {category: set(tags)}; clothes get 'clothes/<subcat>' keys."""
    found = {}
    for t in tags:
        cat, sub = classify(t)
        if cat is None or cat == "accessories":
            continue
        key = "clothes/%s" % sub if cat == "clothes" else cat
        found.setdefault(key, set()).add(t)
    return found


# --- subject tags ----------------------------------------------------------

# Character-count/gender tags. They legitimately co-occur rarely with
# opposite-gender body tags (1boy vs large breasts: cos 0.82, lift 0.00),
# but that is not a same-axis substitution -- never remove them.
_SUBJECT_RE = re.compile(r"^\d+\+?\s*(boy|girl|other)s?$")  # 1boy, 2girls, 6+girls
_SUBJECT_TAGS = {
    "solo",
    "solo focus",
    "male focus",
    "female focus",
    "multiple boys",
    "multiple girls",
    "no humans",
    "everyone",
    "loli",
}


def is_subject(tag):
    """True for character count/gender tags (1boy, 2girls, solo, ...)."""
    return tag in _SUBJECT_TAGS or bool(_SUBJECT_RE.match(tag))


# --- co-occurrence ---------------------------------------------------------

_COOC_PATH = artifact.resource("tag_cooc.npz")
_COOC = None  # lazy: dict or False if unavailable

# tag_cooc.npz is not committed (26MB, rebuilt per data release); it is
# fetched from the matching GitHub release on first use, TIPO-style.
# Bump the tag + sha256 together when re-releasing the data.
_COOC_URL = artifact.url_for("data-v1.0.0", "tag_cooc.npz")
_COOC_SHA256 = "1ce3c2a76d2e0527f4b193fb190a794ad60e4e36005a9cceac4d5f6ab60e6e91"


def _load_cooc():
    """Load the precomputed neighbor table (see precompute_conflicts.py).

    For each tag it stores conflict-candidate pairs with
    (cosine, overlap, lift): cosine = PPMI-profile similarity ("same kind
    of tag"), lift = observed/expected co-occurrence ("do they avoid each
    other": lift << 1 = avoidance, >= 1 = attraction), overlap =
    count(a&b)/min(count(a),count(b)) (kept for reporting).
    """
    global _COOC
    if _COOC is None:
        try:
            import numpy as np

            artifact.ensure(_COOC_PATH, _COOC_URL, _COOC_SHA256, "tag_guard", "26MB")
            data = np.load(_COOC_PATH)
            tags = data["tags"].tolist()
            _COOC = {
                "index": {t: i for i, t in enumerate(tags)},
                "tags": tags,
                "indptr": data["nbr_indptr"],
                "ids": data["nbr_ids"],
                "cos": data["nbr_cos"],
                "ov": data["nbr_ov"],
                "lift": data["nbr_lift"],
            }
        except Exception:
            _COOC = False
    return _COOC


def pair_stats(tag_a, tag_b):
    """Return (cosine, overlap, lift) for a tag pair, or None if not stored.

    Not stored means the pair is no conflict candidate: either not
    context-similar, or they attract each other (lift >= 1).
    """
    data = _load_cooc()
    if not data:
        return None
    for a, b in ((tag_a, tag_b), (tag_b, tag_a)):
        i, j = data["index"].get(a), data["index"].get(b)
        if i is None or j is None:
            return None
        lo, hi = data["indptr"][i], data["indptr"][i + 1]
        ids = data["ids"][lo:hi]
        import numpy as np

        pos = np.nonzero(ids == j)[0]
        if pos.size:
            k = lo + int(pos[0])
            return (
                float(data["cos"][k]),
                float(data["ov"][k]),
                float(data["lift"][k]),
            )
    return None


# --- coarse buckets --------------------------------------------------------
# Buckets come from the same labels TagsGenerator samples with
# (resources/group/, via tag_category): the tag's category decides the
# bucket, and its rating level decides whether "nsfw" overrides that.
# Tags the labels do not cover fall back to the static tables above.
#
# The bucket names predate those categories and are kept as they are so
# existing workflows keep their wiring; `compositions` is appended
# rather than inserted for the same reason.

BUCKETS = (
    "characters",
    "clothes",
    "body",
    "expression",
    "pose",
    "background",
    "objects",
    "nsfw",
    "others",
    "compositions",
)

# category (categories_v1.0.json) -> bucket. creatures folds into
# objects, which is where the old mapping put cats, dogs and elves too.
_CATEGORY_BUCKET = {
    "characters": "characters",
    "expressions": "expression",
    "pose": "pose",
    "clothes": "clothes",
    "background": "background",
    "compositions": "compositions",
    "body": "body",
    "objects": "objects",
    "creatures": "objects",
    "etc": "others",
}

# rating level at or above which a tag is bucketed nsfw regardless of
# category: q and e. Level s (swimsuit, cleavage) stays with its
# category, as it did when nsfw was decided by wiki group.
_NSFW_LEVEL = 2

# tag_data classify() category -> bucket, for tags without a wiki group
_STATIC_BUCKET = {
    "clothes": "clothes",
    "accessories": "clothes",
    "pose": "pose",
    "expression": "expression",
    "eye_color": "expression",
    "hair_length": "body",
    "hair_style": "body",
    "hair_color": "body",
    "background": "background",
}


def bucket_of(tag):
    """Return the bucket name for a normalized tag."""
    if is_subject(tag):
        return "characters"

    labels = tag_category.load_labels()
    if labels:
        # unlabelled tags must not read as explicit here: this is a
        # description, not a filter, so an unknown tag falls through
        # rather than being called nsfw
        if labels.rating_of(tag, default=0) >= _NSFW_LEVEL:
            return "nsfw"
        if labels.knows(tag):
            bucket = _CATEGORY_BUCKET.get(labels.category_name(tag))
            if bucket and bucket != "others":
                return bucket

    cat, _sub = classify(tag)
    if cat is not None:
        return _STATIC_BUCKET.get(cat, "others")
    # last-resort suffix heuristics for common unmapped variants
    if tag.endswith(" hair"):
        return "body"
    if tag.endswith(" eyes"):
        return "expression"
    return "others"


def classify_tags(text):
    """Split a prompt and group its tags by bucket.

    Returns {bucket: [tag, ...]} with every bucket present (possibly
    empty), tags in input order, duplicates dropped.
    """
    out = {b: [] for b in BUCKETS}
    seen = set()
    for t in split_prompt(text):
        if t in seen:
            continue
        seen.add(t)
        out[bucket_of(t)].append(t)
    return out


def _is_clothes(tag):
    return bucket_of(tag) == "clothes"


# Lift-threshold curve endpoints: at cos == cos_th the threshold is
# lift_th; at cos == 1.0 it is lift_th * base. Exponential (convex)
# interpolation stays strict until cos is very high, where near-twin
# profiles (shoes vs boots at lift 0.40) justify a looser bar. Only
# clothes-vs-clothes pairs get a curve: the bucket is dense with true
# same-axis substitutes. For everything else the bar stays flat
# (base 1.0) — calibration_pairs shows high-cos non-clothes pairs
# (legs apart/sitting 0.91, outdoors/dark background 0.80) are
# compatible despite lift barely above lift_th, and every judged
# non-clothes conflict already sits below the flat bar (2026-07-25).
_LIFT_CURVE_BASE = 1.0
_LIFT_CURVE_BASE_CLOTHES = 2.5


def _pair_lift_th(cos, cos_th, lift_th, base):
    x = (cos - cos_th) / (1.0 - cos_th) if cos_th < 1.0 else 0.0
    x = min(max(x, 0.0), 1.0)
    return lift_th * base**x


def is_conflict(tag, ref_tags, cos_th=0.75, lift_th=0.2):
    """True if tag avoids some reference tag and they are the same kind
    of tag: either context-similar (cosine >= cos_th) or in the same
    static category. The lift bar rises exponentially with cosine, from
    lift_th at cos_th up to 2x (2.5x for clothes-vs-clothes pairs) at
    cos 1.0. Returns the conflicting ref or None.
    """
    tag_cat = classify(tag)[0]
    tag_clothes = _is_clothes(tag)
    for ref in ref_tags:
        if ref == tag:
            continue
        stats = pair_stats(tag, ref)
        if stats is None:
            continue
        cos, _ov, lift = stats
        same_cat = tag_cat is not None and tag_cat == classify(ref)[0]
        base = (
            _LIFT_CURVE_BASE_CLOTHES
            if tag_clothes and _is_clothes(ref)
            else _LIFT_CURVE_BASE
        )
        if lift < _pair_lift_th(cos, cos_th, lift_th, base) and (
            cos >= cos_th or same_cat
        ):
            return ref
    return None


def in_cooc_vocab(tag):
    data = _load_cooc()
    return bool(data) and tag in data["index"]


# Categories where one value excludes the others, safe for the static
# fallback. Background/pose/expression are NOT here: their tags combine
# freely (dark background + pond), which is what the lift metric handles.
_EXCLUSIVE_CATEGORIES = ("clothes", "hair_color", "eye_color", "hair_length")


def _static_conflict(tag, refs):
    """Fallback for tags outside the co-occurrence vocabulary (rare
    variants like 'white frilled dress'): conflict via classify() and
    the curated clothes subcategory table, exclusive categories only.
    Returns the conflicting ref or None.
    """
    cat, sub = classify(tag)
    if cat not in _EXCLUSIVE_CATEGORIES:
        return None
    for ref in refs:
        if ref == tag:
            continue
        ref_cat, ref_sub = classify(ref)
        if ref_cat != cat:
            continue
        if cat == "clothes":
            if sub in CLOTHES_CONFLICTS.get(ref_sub, ()):
                return ref
        else:
            return ref
    return None


def filter_by_conflicts(
    generated_prompt, locked_prompt="", cos_th=0.75, lift_th=0.2, restrict_category=None
):
    """Data-driven filter: drop generated tags that conflict with locked
    tags (or with earlier kept tags). No category lists required -- works
    for any tag in the co-occurrence vocabulary (e.g. day vs night).

    restrict_category: if set (a wiki bucket name, see BUCKETS),
    only tags in that bucket are candidates for removal.

    Returns (filtered_prompt, removed_tags_string).
    """
    locked = split_prompt(locked_prompt)
    # subject tags are never conflict references (1boy vs large breasts
    # looks like a conflict statistically but is not a substitution)
    refs = [r for r in dict.fromkeys(locked) if not is_subject(r)]
    locked_set = set(locked)

    kept, rows = [], []  # rows: (tag, ref, cos, lift, status)
    for raw in generated_prompt.split(","):
        t = normalize(raw)
        if not t:
            continue
        if t in locked_set:
            kept.append(raw.strip())
            continue
        if restrict_category is not None and bucket_of(t) != restrict_category:
            kept.append(raw.strip())
            rows.append((t,) + _nearest_ref(t, refs) + ("kept",))
            continue
        if is_subject(t):
            kept.append(raw.strip())
            continue
        if in_cooc_vocab(t):
            ref = is_conflict(t, refs, cos_th=cos_th, lift_th=lift_th)
            if ref is not None:
                cos, _ov, lift = pair_stats(t, ref)
                rows.append((t, ref, cos, lift, "REMOVED"))
            elif all(pair_stats(t, r) is None for r in refs):
                # in vocab but evidence-starved: rare tags (>=100 vocab)
                # often have no stored pair with any ref because the
                # expected co-occurrence never reaches E_MIN. Data said
                # nothing either way, so the static rule still applies
                # (a stored pair, even a compatible one, is data and
                # overrides static).
                ref = _static_conflict(t, refs)
                if ref is not None:
                    rows.append((t, ref, None, None, "REMOVED"))
        else:
            ref = _static_conflict(t, refs)
            if ref is not None:
                rows.append((t, ref, None, None, "REMOVED"))
        if ref is None:
            kept.append(raw.strip())
            rows.append((t,) + _nearest_ref(t, refs) + ("kept",))
            refs.append(t)

    return ", ".join(kept), _format_table(rows, cos_th, lift_th)


def _nearest_ref(tag, refs):
    """(ref, cos, lift) of the stored pair with the lowest lift: the
    strongest-avoidance pair. Blanks if no ref has a stored pair.
    """
    best, best_lift = (None, None, None), None
    for ref in refs:
        if ref == tag:
            continue
        stats = pair_stats(tag, ref)
        if stats is None:
            continue
        if best_lift is None or stats[2] < best_lift:
            best, best_lift = (ref, stats[0], stats[2]), stats[2]
    return best


_TABLE_MAX_ROWS = 20


def _format_table(rows, cos_th=0.75, lift_th=0.2):
    """Markdown table over non-fixed tags, cos descending (rows without
    stats last). Capped at _TABLE_MAX_ROWS: every REMOVED row is always
    shown, kept rows are randomly sampled to fill the rest.
    """
    if not rows:
        return ""
    # stars = which third of the passing range the value falls in:
    # cos:  [th, 1.0] split in 3      (* just past th ... *** near 1.0)
    # lift: [0, th_pair] split in 3   (* just under bar ... *** near 0)
    # th_pair is the pair's effective bar from the exponential lift
    # curve (rises with cos; larger base for clothes pairs), i.e. the
    # same bar is_conflict actually judged against.
    cos_stars = (cos_th, cos_th + (1 - cos_th) / 3, cos_th + 2 * (1 - cos_th) / 3)
    note = ""
    if len(rows) > _TABLE_MAX_ROWS:
        import random

        removed = [r for r in rows if r[4] == "REMOVED"]
        kept = [r for r in rows if r[4] != "REMOVED"]
        n_kept = max(0, _TABLE_MAX_ROWS - len(removed))
        note = "(showing %d of %d kept rows, sampled)" % (
            min(n_kept, len(kept)),
            len(kept),
        )
        rows = removed + random.sample(kept, min(n_kept, len(kept)))
    # lift ascending (strongest avoidance first); rows without stats last
    rows = sorted(rows, key=lambda r: float("inf") if r[3] is None else r[3])
    header = ("tag", "nearest", "cosine", "lift", "status", "category")
    cells = []
    for t, ref, cos, lift, status in rows:
        cat = "-"
        if ref is not None:
            b = bucket_of(t)
            if b != "others" and b == bucket_of(ref):
                cat = b
        if ref is None:
            cells.append((t, "-", "-", "-", status, cat))
        elif cos is None:
            cells.append((t, ref, "static", "-", status, cat))
        else:
            base = (
                _LIFT_CURVE_BASE_CLOTHES
                if _is_clothes(t) and _is_clothes(ref)
                else _LIFT_CURVE_BASE
            )
            th_pair = _pair_lift_th(cos, cos_th, lift_th, base)
            lift_stars = (th_pair, th_pair * 2 / 3, th_pair / 3)
            cos_cell = "*" * sum(cos >= s for s in cos_stars) + "%.2f" % cos
            lift_cell = "*" * sum(lift <= s for s in lift_stars) + "%.2f" % lift
            cells.append((t, ref, cos_cell, lift_cell, status, cat))
    widths = [max(len(r[i]) for r in [header] + cells) for i in range(6)]

    def fmt(row):
        # cos/lift right-aligned, text columns left-aligned
        out = [
            row[i].rjust(widths[i]) if i in (2, 3) else row[i].ljust(widths[i])
            for i in range(6)
        ]
        return "| %s |" % " | ".join(out)

    lines = [fmt(header), "|%s|" % "|".join("-" * (w + 2) for w in widths)]
    lines.extend(fmt(r) for r in cells)
    if note:
        lines.append(note)
    return "\n".join(lines)


# --- ban list --------------------------------------------------------------


# --- post filter -----------------------------------------------------------


def cooc_available():
    return bool(_load_cooc())


def build_ban_tags(
    prompt, modes=None, clothes_strict=False, use_underscores=False, extra_ban=""
):
    """Build a ban list from the locked prompt.

    modes: dict {category_name: "auto"|"off"|"ban_all"} (default: all "auto")
    Returns (ban_tags_string, report_string).
    """
    modes = dict(modes or {})
    for c in CATEGORY_NAMES:
        modes.setdefault(c, "auto")

    tags = split_prompt(prompt)
    tag_set = set(tags)
    found = detect(tags)
    ban = set()
    report = []

    # clothes
    mode = modes["clothes"]
    present_subs = {k.split("/")[1] for k in found if k.startswith("clothes/")}
    if mode == "ban_all":
        for sub, sub_tags in CLOTHES.items():
            ban.update(normalize(t) for t in sub_tags)
        report.append("clothes: ban_all")
    elif mode == "auto" and present_subs:
        banned_subs = set()
        for sub in present_subs:
            banned_subs |= CLOTHES_CONFLICTS[sub]
        if clothes_strict and present_subs & {"top", "bottom", "full"}:
            banned_subs.add("outerwear")
        for sub in banned_subs:
            ban.update(normalize(t) for t in CLOTHES[sub])
        detected = sorted(
            t for k, v in found.items() if k.startswith("clothes/") for t in v
        )
        report.append(
            "clothes: detected %s -> banning subcategories %s"
            % (", ".join(detected), ", ".join(sorted(banned_subs)))
        )

    # other categories
    for cat, cat_tags in CATEGORIES.items():
        mode = modes[cat]
        if mode == "ban_all":
            ban.update(normalize(t) for t in cat_tags)
            report.append("%s: ban_all" % cat)
        elif mode == "auto" and cat in found:
            ban.update(normalize(t) for t in cat_tags)
            report.append(
                "%s: detected %s -> banning rest of category"
                % (cat, ", ".join(sorted(found[cat])))
            )

    ban -= tag_set  # never ban what the user asked for
    ban.update(split_prompt(extra_ban))

    out = sorted(ban)
    if use_underscores:
        out = [t.replace(" ", "_") for t in out]
    if not report:
        report.append("nothing detected; ban list empty")
    return ", ".join(out), "\n".join(report)


def filter_generated(
    generated_prompt, locked_prompt="", modes=None, clothes_strict=False
):
    """Remove tags from generated_prompt that conflict with locked_prompt
    (or with earlier tags in generated_prompt itself). Static category
    rules only; see filter_by_conflicts for the data-driven version.

    Returns (filtered_prompt, removed_tags_string).
    """
    modes = dict(modes or {})
    for c in CATEGORY_NAMES:
        modes.setdefault(c, "auto")

    locked = split_prompt(locked_prompt)
    locked_set = set(locked)
    seen = detect(locked)  # seeded by locked prompt

    kept, removed = [], []
    for raw in generated_prompt.split(","):
        t = normalize(raw)
        if not t:
            continue
        if t in locked_set:
            kept.append(raw.strip())
            continue
        cat, sub = classify(t)
        drop = False
        if cat and cat != "accessories":
            if cat == "clothes":
                mode = modes["clothes"]
                if mode != "off":
                    present_subs = {
                        k.split("/")[1] for k in seen if k.startswith("clothes/")
                    }
                    conflict = set()
                    for s in present_subs:
                        conflict |= CLOTHES_CONFLICTS[s]
                    if clothes_strict and present_subs & {"top", "bottom", "full"}:
                        conflict.add("outerwear")
                    if mode == "ban_all" or sub in conflict:
                        drop = True
            else:
                mode = modes[cat]
                if mode == "ban_all" or (mode == "auto" and cat in seen):
                    drop = True
        if drop:
            removed.append(t)
        else:
            kept.append(raw.strip())
            if cat and cat != "accessories":
                key = "clothes/%s" % sub if cat == "clothes" else cat
                seen.setdefault(key, set()).add(t)

    return ", ".join(kept), ", ".join(removed)
