"""TagVeto: drop suggested tags that contradict the reference tags.

Runtime port of playground/experiments/veto.ipynb. Built on
danbooru2026_clean (5.48M solo posts, 8,320 general tags).

Which suggestion is *best* is subjective; which suggestion is
*impossible* is not. Two frequent tags that almost never share a post
are mutually exclusive in practice, which shows up as
lift = observed / expected co-occurrence far below 1.

Judgment rules (see the notebook for the measurements behind each):
  - veto when lift < lift_th. The E gate (expected co-occurrence >= 15,
    below which an observed 0 proves nothing) is baked into the artifact.
  - composition tags (2girls, yuri, ...) are judged on the unfiltered
    corpus: the solo corpus starves them and makes their lift
    arithmetically 1.0.
  - character-count/gender tags are only compared with each other
    (1boy vs large_breasts is avoidance, not substitution).
  - fixed tags are assumed consistent and always kept; surviving
    suggestions immediately become references.

lift_th is the only tuned parameter.
"""

import re
from collections import namedtuple
from functools import lru_cache

try:
    from . import artifact, tag_alias
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    import artifact
    import tag_alias

E_MIN = 15.0
DEFAULT_LIFT_TH = 0.1

_VETO_PATH = artifact.resource("tag_veto.npz")
# not committed (13MB); fetched from the data release on first use
_VETO_URL = artifact.url_for("data-v1.0.0", "tag_veto.npz")
_VETO_SHA256 = "3fb3603bcadef8e8add34eb742836215e3c98264cbcdec7007b16c2215b4bb37"


# --- tag normalization -----------------------------------------------------

_WEIGHT_RE = re.compile(r":\s*-?[0-9.]+\s*$")
_SUBJECT_RE = re.compile(r"^\d+\+?(boy|girl|other)s?$")
_SUBJECT_TAGS = {
    "solo",
    "solo_focus",
    "male_focus",
    "female_focus",
    "multiple_boys",
    "multiple_girls",
    "multiple_others",
    "no_humans",
    "everyone",
}


def normalize(tag):
    """Prompt token -> Danbooru form: '(blonde hair:1.2)' -> 'blonde_hair'.

    Emphasis and weight are peeled off together, alternating until
    nothing more comes away. Weight is anchored to the end of the
    string, so stripping it once before the brackets leaves "(blonde
    hair:1.2)" as "blonde_hair:1.2" -- a tag no vocabulary has, silently
    dropping from the context the very tag the weight says matters most.

    The weight may be negative: "(particles:-1.2)" is a prompt asking
    for less of something, and leaving the minus unmatched left the tag
    as "particles:-1.2" -- out of every vocabulary, so the request was
    dropped rather than honoured. See weight_of for reading it.

    Renaming is deliberately not done here: which of a tag's spellings
    is the live one is a property of the table being asked, so each
    table folds the alias group onto its own vocabulary instead (see
    tag_alias.expand_index).
    """
    t = tag.strip().lower().replace("\\(", "(").replace("\\)", ")")
    previous = None
    while previous != t:
        previous = t
        t = _WEIGHT_RE.sub("", t).strip()
        if t.startswith("(") and t.endswith(")"):
            t = t[1:-1].strip()
    return re.sub(r"\s+", "_", t.replace("_", " ").strip())


def weight_of(tag):
    """The weight a prompt token carries, 1.0 when it names none.

    Only the outermost weight is read: "((blonde hair:1.2))" is 1.2 to
    everything here, since bracket emphasis multiplies on the diffusion
    side and means nothing to a co-occurrence table.
    """
    t = tag.strip().lower().replace("\\(", "(").replace("\\)", ")")
    while True:
        m = _WEIGHT_RE.search(t)
        if m:
            try:
                return float(m.group(0).lstrip(":").strip())
            except ValueError:
                return 1.0
        if t.startswith("(") and t.endswith(")"):
            t = t[1:-1].strip()
            continue
        return 1.0


def split_prompt_tags(prompt):
    """Prompt text -> its tags, with grouping brackets resolved.

    Commas inside an emphasis group belong to the group, not to the
    prompt: "1girl, (mother and son, age difference)" is three tags, not
    a "(mother and son" and an "age difference)". Splitting on every
    comma leaves those two halves unbalanced, and neither survives
    normalize() -- the group vanishes from the context entirely, which
    is the opposite of what wrapping it was meant to do.

    Escaped brackets are part of the tag ("bar \\(place\\)") and never
    group, so only unescaped ones open and close a level.
    """
    tags, depth, start = [], 0, 0
    for i, ch in enumerate(prompt):
        if ch == "(" and (i == 0 or prompt[i - 1] != "\\"):
            depth += 1
        elif ch == ")" and (i == 0 or prompt[i - 1] != "\\"):
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            tags.append(prompt[start:i])
            start = i + 1
    tags.append(prompt[start:])

    out = []
    for tag in tags:
        stripped = tag.strip()
        # a group is only worth reopening when it holds several tags;
        # "(blonde hair:1.2)" is one tag and normalize() handles it
        if stripped.startswith("(") and stripped.endswith(")") and "," in stripped:
            inner = _WEIGHT_RE.sub("", stripped[1:-1].strip()).strip()
            out.extend(split_prompt_tags(inner))
        elif stripped:
            out.append(tag)
    return out


@lru_cache(maxsize=None)
def is_subject(tag):
    """Character-count/gender tags (1boy, 2girls, solo, ...)."""
    return tag in _SUBJECT_TAGS or bool(_SUBJECT_RE.match(tag))


# --- the filter ------------------------------------------------------------

Verdict = namedtuple("Verdict", "raw tag keep source ref lift")


class TagVeto:
    """Judge suggestions against reference tags using tag_veto.npz."""

    def __init__(self, path=_VETO_PATH):
        import numpy as np

        self._np = np
        if path == _VETO_PATH:
            artifact.ensure(path, _VETO_URL, _VETO_SHA256, "TagVeto", "13MB")
        data = np.load(path)

        self.vocab = [str(t) for t in data["tags"]]
        # aliases resolve to the same row, so a prompt may spell a tag
        # any way Danbooru ever has; self.vocab stays the real names
        self.index = tag_alias.expand_index({t: i for i, t in enumerate(self.vocab)})
        self._n = len(self.vocab)

        # exclusion pairs (lift < 0.5), stored as a sorted array of
        # i*n+j keys (i < j) for binary-search lookup: a dict would cost
        # ~10x the memory for 1.5M pairs.
        keys = data["pair_a"].astype(np.int64) * self._n + data["pair_b"]
        order = np.argsort(keys)
        self._pair_keys = keys[order]
        self._pair_lift = data["pair_lift"].astype(np.float32)[order]

        # composition tags: co-occurrence rows over the unfiltered corpus
        self._starved = {str(t): row for row, t in enumerate(data["starved"])}
        # the same two facts per vocabulary entry, as arrays, so
        # conflict_mask can ask them of every candidate at once
        self._starved_row = np.array(
            [self._starved.get(t, -1) for t in self.vocab], dtype=np.int64
        )
        self._is_subject_row = np.array([is_subject(t) for t in self.vocab], dtype=bool)
        self._cooc_all = data["starved_cooc"]
        self._counts_all = data["counts_all"].astype(np.float64)
        self._n_all = float(data["n_all"])

        # bridge pairs (blue_eyes + red_eyes -> heterochromia): the
        # overlap is a named situation. Informational only -- gating the
        # filter on them buys 0.06pp for a second parameter.
        self.bridges = {
            frozenset((self.vocab[i], self.vocab[j])): self.vocab[t]
            for i, j, t in zip(data["bridge_a"], data["bridge_b"], data["bridge_t"])
        }

    # --- pair level -------------------------------------------------------

    def pair_lift(self, a, b):
        """lift for a pair, or None when the data says nothing:
        out of vocabulary, not stored (lift >= 0.5), or below the E gate.
        None always means "no veto"."""
        if a not in self.index or b not in self.index:
            return None
        if a in self._starved or b in self._starved:
            return self._lift_unfiltered(a, b)
        return self._lift_stored(a, b)

    def _lift_stored(self, a, b):
        i, j = sorted((self.index[a], self.index[b]))
        key = i * self._n + j
        pos = int(self._np.searchsorted(self._pair_keys, key))
        if pos < len(self._pair_keys) and self._pair_keys[pos] == key:
            return float(self._pair_lift[pos])
        return None

    def _lift_unfiltered(self, a, b):
        """Lift over all posts, for pairs involving a composition tag."""
        if a not in self._starved:
            a, b = b, a
        row, j = self._starved[a], self.index[b]
        observed = float(self._cooc_all[row, j])
        expected = self._counts_all[self.index[a]] * self._counts_all[j] / self._n_all
        if expected < E_MIN:
            return None
        return observed / expected

    def conflict(self, cand, refs, lift_th=DEFAULT_LIFT_TH):
        """First reference tag that cand contradicts, or None."""
        cand_subject = is_subject(cand)  # same for every ref
        for ref in refs:
            if ref == cand or is_subject(ref) != cand_subject:
                continue
            lift = self.pair_lift(cand, ref)
            if lift is not None and lift < lift_th:
                return ref
        return None

    def conflict_mask(self, cand_ids, ref, lift_th=DEFAULT_LIFT_TH):
        """Which of `cand_ids` contradict one reference tag.

        Same verdict as conflict() gives for a single ref, computed over
        the whole candidate array at once. The sampler asks this of
        every candidate at every step, so as a Python loop over
        pair_lift it was the most expensive thing it did; vectorised it
        is ~40x cheaper for the same answers.

        cand_ids are indices into this table's own vocabulary, -1 for
        tags it does not know (never a conflict, since pair_lift returns
        None for them and None means no veto). Returns a bool array of
        the same length.
        """
        np = self._np
        out = np.zeros(len(cand_ids), dtype=bool)
        ri = self.index.get(ref)
        if ri is None:
            return out

        # who gets judged: in the table, not the reference itself, and
        # on the same side of the subject/not-subject line -- the guard
        # conflict() applies one pair at a time
        judged = (
            (cand_ids >= 0)
            & (cand_ids != ri)
            & (self._is_subject_row[np.maximum(cand_ids, 0)] == is_subject(ref))
        )
        idx = np.nonzero(judged)[0]
        if not len(idx):
            return out
        j = cand_ids[idx]

        # Two sources, as in pair_lift: composition ("starved") tags are
        # judged over the unfiltered corpus because the solo-post matrix
        # has almost no rows for them, and either side being one sends
        # the pair that way. Everything else comes from the stored pairs.
        lift = np.ones(len(idx), dtype=np.float64)  # 1.0 = no veto
        starved_ref = self._starved.get(ref)
        starved_j = self._starved_row[j]
        unfiltered = (
            np.ones(len(idx), dtype=bool) if starved_ref is not None else starved_j >= 0
        )

        sel = np.nonzero(unfiltered)[0]
        if len(sel):
            # whichever side owns a row supplies it; when both do, the
            # scalar path prefers the candidate's, so match that
            own = starved_j[sel] >= 0
            row = np.where(own, starved_j[sel], starved_ref or 0)
            owner = np.where(own, j[sel], ri)
            other = np.where(own, ri, j[sel])
            observed = self._cooc_all[row, other].astype(np.float64)
            expected = self._counts_all[owner] * self._counts_all[other] / self._n_all
            with np.errstate(divide="ignore", invalid="ignore"):
                # below the E gate the corpus has no sample to judge with
                lift[sel] = np.where(expected >= E_MIN, observed / expected, 1.0)

        rest = np.nonzero(~unfiltered)[0]
        if len(rest):
            a = np.minimum(j[rest], ri).astype(np.int64)
            b = np.maximum(j[rest], ri).astype(np.int64)
            keys = a * self._n + b
            pos = np.searchsorted(self._pair_keys, keys)
            pos = np.minimum(pos, len(self._pair_keys) - 1)
            hit = self._pair_keys[pos] == keys
            lift[rest] = np.where(hit, self._pair_lift[pos], 1.0)

        out[idx] = lift < lift_th
        return out

    def vocab_ids(self, tags):
        """Map tags onto this table's vocabulary once, -1 where absent."""
        np = self._np
        return np.array([self.index.get(t, -1) for t in tags], dtype=np.int64)

    def bridge_for(self, a, b):
        """The tag naming this pair's situation, if the data has one."""
        return self.bridges.get(frozenset((a, b)))

    # --- prompt level -----------------------------------------------------

    def judge(self, inputs, suggestions, lift_th=DEFAULT_LIFT_TH):
        """Judge (raw, tag) suggestions against (raw, tag) inputs.

        Inputs are always kept. A surviving suggestion joins the
        references, so two mutually contradictory suggestions cannot
        both pass; suggestion order (the generator's ranking) decides
        which one wins. Returns a list of Verdict rows.
        """
        rows, seen, refs = [], set(), []

        for raw, tag in inputs:
            if tag and tag not in seen:
                seen.add(tag)
                refs.append(tag)
                rows.append(Verdict(raw, tag, True, "input", None, None))

        for raw, tag in suggestions:
            if not tag or tag in seen:
                continue
            seen.add(tag)
            ref = self.conflict(tag, refs, lift_th)
            if ref is None:
                refs.append(tag)
                rows.append(Verdict(raw, tag, True, "suggestion", None, None))
            else:
                rows.append(
                    Verdict(
                        raw, tag, False, "suggestion", ref, self.pair_lift(tag, ref)
                    )
                )
        return rows


# --- module-level API ------------------------------------------------------


@artifact.lazy
def load_veto():
    """The veto table, or False when the artifact is missing."""
    return TagVeto()


def veto_available():
    return bool(load_veto())


def filter_by_veto(generated_prompt, fixed_prompt="", lift_th=DEFAULT_LIFT_TH):
    """Drop generated tags that contradict the fixed tags (or earlier
    surviving generated tags). Returns (filtered_prompt, report_table).
    """
    veto = load_veto()
    rows = veto.judge(_split(fixed_prompt), _split(generated_prompt), lift_th)
    kept = [r.raw for r in rows if r.keep]
    return ", ".join(kept), _format_table(rows, veto, lift_th)


def _split(prompt):
    pairs = [(raw.strip(), normalize(raw)) for raw in prompt.split(",")]
    return [(raw, tag) for raw, tag in pairs if tag]


# --- report table ----------------------------------------------------------

_TABLE_MAX_ROWS = 20


def _table_cell(row, veto):
    if not row.keep:
        return (
            row.tag,
            row.ref,
            "%.3f" % row.lift,
            "VETOED",
            veto.bridge_for(row.tag, row.ref) or "-",
        )
    verdict = "kept" if row.tag in veto.index else "kept (OOV)"
    return (row.tag, "-", "-", verdict, "-")


def _format_table(rows, veto, lift_th):
    """One line per suggestion. Every VETOED row is shown; kept rows are
    sampled to stay under _TABLE_MAX_ROWS."""
    cells = [_table_cell(r, veto) for r in rows if r.source == "suggestion"]
    if not cells:
        return ""

    if len(cells) > _TABLE_MAX_ROWS:
        import random

        vetoed = [c for c in cells if c[3] == "VETOED"]
        kept = [c for c in cells if c[3] != "VETOED"]
        cells = vetoed + random.sample(
            kept, min(max(0, _TABLE_MAX_ROWS - len(vetoed)), len(kept))
        )

    header = ("tag", "vs", "lift", "verdict", "bridge")
    widths = [
        max(len(row[col]) for row in [header] + cells) for col in range(len(header))
    ]

    def fmt(row):
        return "| %s |" % " | ".join(
            cell.rjust(w) if col == 2 else cell.ljust(w)
            for col, (cell, w) in enumerate(zip(row, widths))
        )

    lines = [fmt(header), "|%s|" % "|".join("-" * (w + 2) for w in widths)]
    lines += [fmt(c) for c in cells]
    lines.append(
        "(veto: lift < %.2f, E >= %.0f; bridge = the tag naming "
        "the overlap, informational only)" % (lift_th, E_MIN)
    )
    return "\n".join(lines)
