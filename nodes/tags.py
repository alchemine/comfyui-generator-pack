"""Nodes in GeneratorPack/Tags.

Four classes are registered as nodes -- TagsGenerator, TagsConflictFilter,
ClassifyTags and GroupTags. ProcessTags, FilterTags, FilterSubtags and
ReplaceUnderscores carry no node surface: TagsGenerator runs its draw
through that pipeline before counting what survived.
"""

import re
import random
import numbers
import textwrap
from collections import defaultdict
from functools import wraps

import yaml

from .lib import artifact
from .lib.utils import get_logger, exception_handler, standardize_prompt
from .lib.tag_guard import (
    filter_generated,
    CATEGORY_NAMES,
    BUCKETS,
    classify_tags,
)
from .lib.tag_category import load_labels
from .lib.tag_veto import filter_by_veto, veto_available
from .lib.tag_suggest import (suggest_tags, suggest_available,
                              DEFAULT_MOMENTUM,
                              DEFAULT_REPETITION_PENALTY)


logger = get_logger()

# Danbooru rating names, mildest first. The node offers two more that
# are not ratings: "all" asks for no cap at all, and "random" draws one
# of these per seed, uniformly -- see the widget tooltip.
RATINGS = ("general", "sensitive", "questionable", "explicit")

# TagsGenerator's category widgets, in the order they appear on the node:
# the shares that make a prompt read like a picture rather than a list --
# who is in it, what they are doing and feeling, then their body, what it
# wears, and where it is.
#
# These six are what a prompt actually gets steered by; the label file's
# other categories are not worth a knob each, so background carries them
# (see CATEGORY_GROUPS) and creatures and etc are left out of the spec
# entirely.
#
# Category names are hardcoded rather than read from
# resources/group/categories_v1.0.json because INPUT_TYPES runs at import
# and loading the label tables costs more than this list is worth;
# tag_category.parse_categories resolves them against the file at sample
# time, so a rename there only costs the widget its effect, never an
# error.
CATEGORY_DEFAULTS = {
    "characters": 0.1,
    "pose": 0.2,
    "expressions": 0.1,
    "body": 0.3,
    "clothes": 0.2,
    "background": 0.1,
}
# What each widget actually turns. background stands for the scene around
# the subject: the props in it (objects) and how it is framed
# (compositions). The three share one budget rather than getting one
# each, so background at 0.1 is a tenth of the output for the whole
# setting -- objects alone will happily fill a prompt with furniture.
#
# characters is deliberately NOT in that group. The label file files the
# subject itself there -- 1girl, 1boy, solo, 2girls -- not just who else
# is in the scene, and those tags anchor everything downstream: without a
# gender anchor one male pick pulls the whole draw after it. Sharing the
# scene's single slot left them to lose a coin toss against furniture.
CATEGORY_GROUPS = {
    "background": ("background", "objects", "compositions"),
}

# Two categories are deliberately unreachable, and stay out of the spec
# because parse_categories only allows what it is given: creatures pulls
# toward animal-eared characters the prompt did not ask for, and etc is
# the unlabelled remainder, too scattershot to steer with.

# widget value meaning "allowed, no cap"; 0 turns the category off and a
# fraction caps the category's share of the output (0.3 = 30% of n)
CATEGORY_UNCAPPED = -1.0

# Each category gets two widgets: a toggle under its own name and the
# share under name + this. The toggle is the one people reach for, so it
# wins: off means off whatever the share says, which also lets a share
# be dialled in, switched off, and switched back on unchanged.
_SHARE_SUFFIX = "_share"


def _legacy_knobs(categories, momentum, repetition_penalty):
    """Accept the pre-rename widget names, then drop them.

    TagsGenerator collects its category shares as **kwargs, so an API
    workflow still sending "cohesion" or "repeat_decay" would not raise
    -- the stale name would be read as a category share and quietly cap
    a category that does not exist. Popping them here keeps those
    workflows running and keeps the spec clean either way.

    repeat_decay is the reciprocal: the penalty used to be a factor the
    odds were multiplied by, and is now the one they are divided by, so
    the direction matches every other repetition penalty.
    """
    if "cohesion" in categories:
        momentum = float(categories.pop("cohesion"))
    decay = categories.pop("repeat_decay", None)
    if decay is not None and float(decay) > 0:
        repetition_penalty = 1.0 / float(decay)
    return momentum, repetition_penalty


def _categories_spec(counts):
    """Build a parse_categories spec from the category widgets.

    A widget the caller left out falls back to its default, so a
    workflow saved before these existed still gets the balanced shares
    rather than an unrestricted draw.

    Every widget uncapped still yields a spec rather than "", because
    the excluded categories have to stay excluded. All-zero would read
    as "nothing allowed", which parse_categories cannot express and
    would silently mean "everything"; it is dropped to the defaults with
    a warning instead.
    """
    counts = {name: (counts.get(name + _SHARE_SUFFIX, default)
                     if counts.get(name, True) else 0.0)
              for name, default in CATEGORY_DEFAULTS.items()}
    if all(v == 0.0 for v in counts.values()):
        logger.warning(
            "[TagsGenerator] every category is off; sampling with the "
            "defaults instead -- switch at least one back on",
        )
        counts = dict(CATEGORY_DEFAULTS)
    parts = []
    for name, value in counts.items():
        if value == 0.0:
            continue
        # the categories a widget stands for are joined into one budget,
        # so background at 0.1 is a tenth of the output for the whole
        # setting rather than a tenth each for background, objects and
        # compositions
        group = "+".join(CATEGORY_GROUPS.get(name, (name,)))
        parts.append(group if value < 0 else f"{group}:{value}")
    return ", ".join(parts)


#################################################################
# Utility functions
#################################################################
# Wildcard form the blacklist expands: <color> becomes every value under
# the "color" key of resources/wildcards.yaml, joined into one
# alternation. Deliberately NOT the __color__ form the wildcard packs
# use -- their processors run upstream of this node and would resolve the
# token first, and they resolve it by *picking one* value, which is the
# opposite of what a blacklist wants. Angle brackets are syntax no
# wildcard processor claims, so the token survives them and arrives here
# intact. __key__ is still accepted for prompts that never pass through
# one.
_WILDCARD_FORMS = ("<{key}>", "__{key}__")


def blacklist_pattern(blacklist_tags: str) -> str:
    """Comma-separated blacklist -> one regex, or "" when it is empty.

    Each comma-separated token is its own regex ("tan$", "^solo$"), so
    they are joined with | rather than matched as one string. A token
    that will not compile is reported and matched literally instead, so
    one typo cannot silence the whole blacklist.
    """
    if not blacklist_tags or not blacklist_tags.strip():
        return ""
    with open(artifact.bundled("wildcards.yaml")) as f:
        wildcards = yaml.safe_load(f) or {}
    for key, values in wildcards.items():
        joined = f"({'|'.join(values)})"
        for form in _WILDCARD_FORMS:
            blacklist_tags = blacklist_tags.replace(form.format(key=key),
                                                    joined)
    patterns = []
    for t in (t.strip() for t in blacklist_tags.split(",")):
        if not t:
            continue
        try:
            re.compile(t)
        except re.error as exc:
            logger.warning(
                f"Invalid regex in blacklist token {t!r}: {exc}. "
                f"Falling back to literal match."
            )
            t = re.escape(t)
        patterns.append(t)
    return "|".join(patterns)


def log_prompt(func):
    """Log prompt input and output in a Unicode box table with class name, showing all lines. Now uses thinner lines, adds Node row, and prevents prompt truncation with word wrapping."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        col_width1, col_width2 = [10, 100]

        def format_multiline(label: str, text: str) -> str:
            lines = text.splitlines() or [""]
            out = []
            first_row = True
            for line in lines:
                wrapped = textwrap.wrap(line, width=col_width2) or [""]
                for i, wline in enumerate(wrapped):
                    if first_row and i == 0:
                        row = f"│ {label:<{col_width1-2}} │ {wline.ljust(col_width2)} │"
                    else:
                        row = f"│ {'':<{col_width1-2}} │ {wline.ljust(col_width2)} │"
                    out.append(row)
                    first_row = False
            return "\n".join(out)

        # Prepare inputs
        node_label = args[0].__name__
        input_val = kwargs["text"]
        result = func(*args, **kwargs)
        output_val = result[0]

        # NOTE. 2: space for tags
        top = f"┌{'─'*col_width1}┬{'─'*(2+col_width2)}┐"
        mid = f"├{'─'*col_width1}┼{'─'*(2+col_width2)}┤"
        bot = f"└{'─'*col_width1}┴{'─'*(2+col_width2)}┘"

        # Prepare table content
        node_row = format_multiline("Node", node_label)
        before = format_multiline("Before", input_val)
        after = format_multiline("After", output_val)
        if len(result) > 1:
            filtered_tags = result[1]
            filtered = format_multiline("Filtered", filtered_tags)
            contents = [node_row, before, after, filtered]
        else:
            contents = [node_row, before, after]

        # Log
        content = f"\n{mid}\n".join(contents)
        table = f"{top}\n{content}\n{bot}"
        logger.debug(f"\n{table}")
        return result

    return wrapper


#################################################################
# Base class
#################################################################
class BasePrompt:
    """Base class for Prompt nodes."""

    @staticmethod
    def normalize_tag(tag: str) -> str:
        """Normalize tag with 2 decimal places.

        Examples:
            Input: cat
            Output: (cat:1.00)

            Input: (cat:1.2)
            Output: (cat:1.20)

            Input: ((cat))
            Output: (cat:1.21)

            Input: [cat]
            Output: (cat:0.90)

            Input: [[cat]]
            Output: (cat:0.81)
        """
        tag = tag.strip()
        if match := re.search(r"^\(([^()]+):([-0-9. ]+)\)$", tag):
            # Example: (cat:1.20)
            tag, weight = match.groups()
        elif re.match(r"^[^\(\[]", tag):
            # Example: cat
            pass
        elif match := re.search(r"^(\(+)(.+)(\)+)$", tag):
            # Example: (cat), ((cat))
            tag = match.group(2)
        elif match := re.search(r"^(\[+)(.+)(\]+)$", tag):
            # Example: [cat], [[cat]]
            tag = match.group(2)
        else:
            # logger.warning(f"Unexpected tag format: {tag}")
            pass
        return tag

    @staticmethod
    def remove_weight(tag: str) -> str:
        """Remove weight from a tag.

        Examples:
            Input: (cat:1.20)
            Output: cat
        """
        tag = tag.strip()

        if match := re.search(r"^\(([^()]+):[0-9.-]+\)$", tag):
            # Example: (cat:1.20)
            tag = match.group(1)
        elif match := re.search(r"^\(([^()]+):[0-9.-]+:[0-9.-]+\)$", tag):
            # Example: (cat:1.20:1.30)
            tag = match.group(1)
        elif match := re.search(r"^([\(\[]+)(.+)([\)\]]+)$", tag):
            # Example: (cat), ((cat)), [cat], [[cat]]
            tag = match.group(2)
        else:
            pass
        return tag

    @staticmethod
    def split_tags(text: str) -> list[str]:
        """Split tags by comma, preserving commas inside parentheses.

        Examples:
            Input: "(masterpiece), (best quality:1.2), (highres, absurdres)"
            Output: ["(masterpiece)", " (best quality:1.2)", " (highres, absurdres)"]
        """
        result = []
        depth = 0
        current = ""
        for char in text:
            if char == "(":
                depth += 1
                current += char
            elif char == ")":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                result.append(current)
                current = ""
            else:
                current += char
        if current:
            result.append(current)
        return result

    @classmethod
    def preprocess_tags(cls, text: str, fixed_tags: str) -> tuple[str, str]:
        """Adjust fixed tags to be in the same order as tags in the text."""
        # 1. Adjust BREAK
        text = re.sub(r"(\(?BREAK:?[\d.-]*\)?)", "BREAK", text)
        fixed_tags = re.sub(r"(\(?BREAK:?[-\d.]*\)?)", "BREAK", fixed_tags)

        # 2. Unwrap weights
        text = standardize_prompt(text)
        fixed_tags = standardize_prompt(fixed_tags)

        # 3. Adjust fixed tags
        if fixed_tags:
            fixed_tags_set, fixed_tags_map = [], {}
            for t in re.split(r"BREAK|,", fixed_tags):
                if not t.strip():
                    continue
                normalized_tag = cls.normalize_tag(t)
                if normalized_tag not in fixed_tags_map:
                    fixed_tags_set.append(normalized_tag)
                    fixed_tags_map[normalized_tag] = t

            input_tags_set, input_tags_map = [], {}
            for t in re.split(r"BREAK|,", text):
                if not t.strip():
                    continue
                normalized_tag = cls.normalize_tag(t)
                if normalized_tag not in input_tags_map:
                    input_tags_set.append(normalized_tag)
                    input_tags_map[normalized_tag] = t

            added_texts = ",".join(
                [input_tags_map[t] for t in input_tags_set if t not in fixed_tags_set]
            )
            text = f"{fixed_tags},{added_texts}" if added_texts else fixed_tags

        return text, fixed_tags


#################################################################
# Nodes
#################################################################
class ProcessTags(BasePrompt):
    """Full process of tags from a prompt.

    Order of operations: ReplaceUnderscores -> FilterTags -> FilterSubtags
    """


    @classmethod
    @exception_handler
    def execute(
        cls,
        text: str,
        replace_underscores: bool = True,
        filter_tags: bool = True,
        filter_subtags: bool = True,
        blacklist_tags: str = "",
        fixed_tags: str = "",
    ) -> tuple[str, list[str]]:
        """Process tags from a prompt."""
        # Save original separators BEFORE preprocessing (standardize_prompt changes whitespace)
        original_parts = re.split(r"(\s*BREAK\s*)", text)
        separators = original_parts[1::2]

        text, fixed_tags = cls.preprocess_tags(text, fixed_tags)

        filtered_tags_list = []

        if replace_underscores:
            text = ReplaceUnderscores.execute(text=text)[0]

        if filter_tags:
            text, cur_filtered_tags = FilterTags.execute(
                text=text,
                blacklist_tags=blacklist_tags,
                fixed_tags=fixed_tags,
                preprocess=False,
            )
            if cur_filtered_tags:
                filtered_tags_list.append(cur_filtered_tags)

        if filter_subtags:
            text, cur_filtered_tags = FilterSubtags.execute(
                text=text, fixed_tags=fixed_tags, preprocess=False
            )
            if cur_filtered_tags:
                filtered_tags_list.append(cur_filtered_tags)

        # re-join on the separators the input used, so BREAK keeps its
        # original whitespace
        groups = text.split("BREAK")
        text = groups[0] if groups else ""
        for i, sep in enumerate(separators):
            if i + 1 < len(groups):
                text += sep + groups[i + 1]

        return (text, filtered_tags_list)


class FilterTags(BasePrompt):
    """Filter blacklisted tags from a prompt. Regular expression is used to match tags."""


    @classmethod
    @exception_handler
    @log_prompt
    def execute(
        cls,
        text: str,
        blacklist_tags: str = "",
        fixed_tags: str = "",
        preprocess: bool = True,
    ) -> tuple[str, str]:
        """Filter blacklisted tags from a prompt."""
        # 1. Split tokens by BREAK (preserve surrounding whitespace)
        # Save original separators BEFORE preprocessing (standardize_prompt changes whitespace)
        original_parts = re.split(r"(\s*BREAK\s*)", text)
        separators = original_parts[1::2]  # Original BREAK with surrounding whitespace

        if preprocess:
            text, fixed_tags = cls.preprocess_tags(text, fixed_tags)

        groups = text.split("BREAK")
        fixed_tags_set = {
            
                cls.normalize_tag(t)
                for t in re.split(r"BREAK|,", fixed_tags)
                if t.strip()
            
        }

        # 2. Compile blacklist
        pattern = blacklist_pattern(blacklist_tags)
        compiled_blacklist = re.compile(pattern if pattern else r"(?!)")

        # 3. Filter tags from blacklist from each group
        filtered_tag_list = []
        new_groups = []
        visited_tags = set()
        for group in groups:
            # Ignore empty tags
            original_tags = []
            for tag in group.split(","):
                if tag.strip() and tag not in visited_tags:
                    visited_tags.add(tag)
                    original_tags.append(tag)
            comp_tags = [
                (idx, cls.normalize_tag(t)) for idx, t in enumerate(original_tags)
            ]
            valid_idxs = []
            for idx, tag in comp_tags:
                if (
                    (tag in fixed_tags_set)
                    or not blacklist_tags
                    or (blacklist_tags and not compiled_blacklist.search(tag))
                ):
                    valid_idxs.append(idx)
            new_group = ",".join([original_tags[idx] for idx in sorted(valid_idxs)])
            new_groups.append(new_group.strip())
            filtered_tag_list.extend(
                [
                    original_tags[idx].strip()
                    for idx in range(len(original_tags))
                    if idx not in valid_idxs
                ]
            )

        # 4. Join groups by original BREAK separators (preserve whitespace)
        processed_text = new_groups[0] if new_groups else ""
        for i, sep in enumerate(separators):
            if i + 1 < len(new_groups):
                processed_text += sep + new_groups[i + 1]
        # Remove trailing comma before BREAK
        processed_text = re.sub(r",(\s*BREAK)", r"\1", processed_text)
        filtered_tags = ", ".join(filtered_tag_list)
        return (processed_text, filtered_tags)


class FilterSubtags(BasePrompt):
    """Filter subtags from a prompt.

    Examples:
        Input: dog, cat, white dog, black cat
        Output: white dog, black cat

        Input: (cat:0.9), (cat:1.1), black cat, (black cat)
        Output: (cat:0.9), (cat:1.1), black cat, (black cat)
    """


    @classmethod
    @exception_handler
    @log_prompt
    def execute(
        cls, text: str, fixed_tags: str = "", preprocess: bool = True
    ) -> tuple[str, str]:
        """Filter subtags from a prompt."""
        # 1. Split tokens by BREAK (preserve surrounding whitespace)
        # Save original separators BEFORE preprocessing (standardize_prompt changes whitespace)
        original_parts = re.split(r"(\s*BREAK\s*)", text)
        separators = original_parts[1::2]  # Original BREAK with surrounding whitespace

        if preprocess:
            text, fixed_tags = cls.preprocess_tags(text, fixed_tags)

        groups = text.split("BREAK")
        fixed_tags_set = {
            
                cls.normalize_tag(t)
                for t in re.split(r"BREAK|,", fixed_tags)
                if t.strip()
            
        }

        # 2. filter all subtags from each group
        filtered_tag_list = []
        new_groups = []
        visited_tags = set()
        for group in groups:
            # Ignore empty tags
            original_tags = []
            for tag in group.split(","):
                if tag.strip() and tag not in visited_tags:
                    visited_tags.add(tag)
                    original_tags.append(tag)
            comp_tags = [
                (idx, cls.normalize_tag(t)) for idx, t in enumerate(original_tags)
            ]
            valid_idxs = set()
            for idx, tag in sorted(
                comp_tags, key=lambda x: (len(x[1]), -x[0]), reverse=True
            ):
                if (tag in fixed_tags_set) or not any(
                    tag in comp_tags[valid_idx][1] for valid_idx in valid_idxs
                ):
                    valid_idxs.add(idx)
            new_group = ",".join([original_tags[idx] for idx in sorted(valid_idxs)])
            new_groups.append(new_group.strip())
            filtered_tag_list.extend(
                [
                    original_tags[idx].strip()
                    for idx in range(len(original_tags))
                    if idx not in valid_idxs
                ]
            )

        # 3. Join groups by original BREAK separators (preserve whitespace)
        processed_text = new_groups[0] if new_groups else ""
        for i, sep in enumerate(separators):
            if i + 1 < len(new_groups):
                processed_text += sep + new_groups[i + 1]
        # Remove trailing comma before BREAK
        processed_text = re.sub(r",(\s*BREAK)", r"\1", processed_text)
        filtered_tags = ", ".join(filtered_tag_list)
        return (processed_text, filtered_tags)


class ReplaceUnderscores(BasePrompt):
    """Replace underscores with spaces in a prompt.

    Examples:
        Input: dog_cat_white_dog_black_cat
        Output: dogcatwhitedogblackcat
    """


    @classmethod
    @exception_handler
    @log_prompt
    def execute(cls, text: str) -> tuple[str]:
        """Replace underscores with spaces in a prompt."""
        processed_text = text.replace("_", " ")
        return (processed_text,)


class TagsConflictFilter(BasePrompt):
    """Remove tags contradicting fixed tags (or earlier tags in the text).

    Veto layer over a tag generator: which tag is *best* is subjective,
    which tag is *impossible* is not. A tag is vetoed when its co-occurrence
    lift (observed / expected on 5.48M Danbooru solo posts) with some
    reference tag falls below lift_threshold, with expected co-occurrence
    >= 15 so an observed 0 is evidence, not chance. Composition tags
    (2girls, yuri, ...) are judged on the unfiltered corpus, and
    character-count/gender tags are only ever compared with each other.
    Fixed tags are assumed consistent and always kept; surviving generated
    tags immediately become references, so two mutually contradictory
    suggestions cannot both pass.

    lift_threshold is the filter's only tuned parameter (labeled pairs
    place the contradiction boundary in the 0.098-0.142 gap; raising it
    past ~0.13 starts vetoing compatible pairs).

    Falls back to static category rules (tag_data.py) when the veto
    artifact (tag_veto.npz) is missing.

    Examples:
        Input: text="bikini, waterfall, pond, dress, day, night", fixed_tags="bikini, waterfall, day"
        Output: ("bikini, waterfall, pond, day", <judgment table>)
    """

    INPUT_TYPES = lambda: {
        "required": {
            "text": ("STRING", {"forceInput": True}),
            "lift_threshold": (
                "FLOAT",
                {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01},
            ),
        },
        "optional": {
            "fixed_tags": ("STRING", {"default": ""}),
        },
    }
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("processed_text", "table")
    FUNCTION = "execute"
    CATEGORY = "GeneratorPack/Tags"

    @classmethod
    @exception_handler
    @log_prompt
    def execute(
        cls,
        text: str,
        lift_threshold: float = 0.1,
        fixed_tags: str = "",
    ) -> tuple[str, str]:
        """Remove tags contradicting fixed tags from a prompt."""
        if veto_available():
            processed_text, filtered_tags = filter_by_veto(
                text,
                fixed_prompt=fixed_tags,
                lift_th=lift_threshold,
            )
        else:
            logger.warning(
                "[TagsConflictFilter] tag_veto.npz not found; "
                "falling back to static category rules"
            )
            processed_text, filtered_tags = filter_generated(
                text,
                locked_prompt=fixed_tags,
                modes=dict.fromkeys(CATEGORY_NAMES, "auto"),
                clothes_strict=False,
            )
        return (processed_text, filtered_tags)

    @classmethod
    def IS_CHANGED(
        cls,
        text: str,
        lift_threshold: float = 0.1,
        fixed_tags: str = "",
    ) -> tuple:
        return (text, lift_threshold, fixed_tags)


def _split_tags(text):
    """Comma-separated prompt into a list of non-empty tags."""
    return [t.strip() for t in text.split(",") if t.strip()]


def _escape_brackets(tag):
    """Escape brackets in a generated tag so they stay literal.

    Every tag here comes from the Danbooru vocabulary, where a bracket
    is part of the name ("star (sky)", "ganyu (genshin impact)") and
    never emphasis, so escaping is unambiguous -- and necessary, since
    attention parsing would otherwise read the qualifier as a weight.
    """
    return re.sub(r"(?<!\\)([()\[\]])", r"\\\1", tag)


def _sort_by_category(items, order, tags_of):
    """Stable-sort `items` into the category order named by `order`.

    `order` is a comma separated list of category names from
    resources/group/categories_v1.0.json; `tags_of(item)` yields the tags
    that decide where the item belongs. An item goes where most of its
    tags point, so one stray member cannot drag it; ties fall to the
    earlier category. Items whose tags are unlabelled, or labelled with a
    category `order` leaves out, keep their original order behind the
    named ones.

    Returns `items` untouched when `order` names nothing usable or the
    label tables are missing, so an unset widget and an unreadable
    resource both cost the caller nothing.
    """
    wanted = [c.strip().lower() for c in order.replace("\n", ",").split(",")]
    wanted = [c for c in wanted if c]
    if not wanted:
        return items

    labels = load_labels()
    if not labels:
        logger.warning("category labels unavailable; leaving tag order alone")
        return items

    rank_of = {name: i for i, name in enumerate(wanted)}
    tail = len(wanted)

    def rank(item):
        votes = defaultdict(int)
        for tag in tags_of(item):
            bare = BasePrompt.remove_weight(tag).strip().strip("()")
            bare = bare.replace("\\(", "(").replace("\\)", ")")
            name = labels.category_name(bare)
            if name in rank_of:
                votes[rank_of[name]] += 1
        if not votes:
            return tail
        best = max(votes.values())
        return min(r for r, n in votes.items() if n == best)

    return sorted(items, key=rank)


class TagsGenerator(BasePrompt):
    """Generate tags that usually accompany the input tags.

    The other direction of TagsConflictFilter's statistic: lift far below 1
    means two tags avoid each other (veto), lift far above 1 means they
    attract. Tags are generated one per step, LM-style: the step
    distribution is naive Bayes over Danbooru solo-post co-occurrence
    (log P(tag) + sum of log lift against every context tag), each pick
    joins the context and re-conditions the next step, and vetoed
    candidates are masked so the output cannot contradict itself.

    temperature 0 = deterministic argmax; above 0, the usual sampling
    filters apply (top_k / top_p / min_p, applied in that order), and
    seed makes the draw reproducible.

    min_count drops rare tags from the candidates, counted within the
    requested rating tier rather than over the whole corpus, so asking
    for a milder rating also shrinks the pool. It defaults to the
    vocabulary floor, i.e. no filtering: three other mechanisms already
    hold rare tags back -- a candidate needs positive attraction from
    the prompt, log P(tag) penalises rare tags heavily, and the stored
    lift is smoothed so a pair seen once cannot look like a strong
    association. Raise it if a particular prompt keeps surfacing tags
    too obscure for your model to have learned.

    Five widgets restrict which knobs the output may turn: pose,
    expressions, body, clothes and background. Each takes a share of the
    output relative to the others, not a fraction of n: with only pose
    0.2 and expressions 0.1 switched on, a request for 10 tags comes
    back 7 pose and 3 expressions, because switching a category off
    hands its share to the ones still on rather than shrinking the
    result. -1 means allowed with no share of its own, 0 switches the
    category off, and the defaults -- body 0.3, pose 0.2, clothes 0.2,
    expressions 0.1, background 0.1 -- balance the node out of the box.

    Counts are split by largest remainder, so they add up to exactly
    what was asked for, and they apply just as well at n 0, where what
    they divide up is the target length drawn from the corpus. They are
    still ceilings rather than promises: a category with nothing left to
    say stops early, and the output comes back short with a warning.

    The widgets do not map one-to-one onto the categories in
    resources/group/categories_v1.0.json. background is the setting
    around the subject, so objects and compositions draw on its budget
    with it -- one share for the scene, not one each. creatures and etc
    are not exposed at all and never sampled.

    Capping matters because each pick re-conditions the next: choosing
    "office chair" makes "swivel chair" more likely, not less, so an
    unrestricted draw tends to pile up in whichever category the prompt
    pulls hardest. background 0.1 breaks that up.

    Three of them are easy to misread. pose owns the sex act groups, but
    explicitness is rating's job, not this one -- leaving pose on at
    rating "general" cannot surface them. clothes owns the job tags, so
    turning it off also drops "office lady" and "nurse". characters owns
    the subject itself, not just the company it keeps: it decides
    whether "1girl" and "solo" can appear at all, which is what anchors
    the gender of everything drawn after them -- and, less happily, the
    franchise grouping tags filed beside them.

    rating caps explicitness on both sides: the statistics come from the
    matching corpus slice, and tags whose own rating level exceeds the
    request are masked, so "general" cannot surface a tag Danbooru only
    applies to racier art. "all" draws one from seed with the mild pair
    (general/sensitive) sharing a third, questionable a third and
    explicit a third, so the choice is reproducible and a new seed
    rerolls the rating along with the tags.

    lift_threshold is the veto's only tuned parameter, the same knob
    TagsConflictFilter exposes and the same default: a candidate is banned
    when the corpus expected it alongside a reference tag often enough
    (>= 15 posts) and the pair still came in below this fraction of
    chance. 0.1 only catches pairs that essentially never co-occur, so
    raise it when the output keeps contradicting the prompt in ways the
    data merely discourages -- "no panties" and "lace-trimmed panties"
    sit at 0.15, six times rarer than chance but past a 0.1 cut. Vetoed
    candidates are replaced rather than dropped, so n still holds.

    repetition_penalty is the brake on momentum. Because a pick
    re-conditions the next one, the strongest neighbours of "blue skin"
    are the other skin colours and the strongest neighbours of "hands
    on own face" are "hands on own head" and "hands on own cheeks", so
    a draw can spend half its budget respelling one idea -- which the
    category quotas cannot stop, since those tags all sit in the same
    category. Each tag already in the prompt sharing a slot with a
    candidate divides its odds by repetition_penalty, so the second one
    needs twice the evidence and the third four times.

    A slot is the axis a tag varies along, read off its spelling. Most
    tags offer their last word: "blue skin" and "pale skin" share one.
    A tag built around a linking word splits in two, since either half
    can be the axis being respelled -- "hands on own face" is a "hands
    on" tag and an "on own face" tag, colliding with "hands on own
    head" through the first and with "blood on face" through the
    second. It is deliberately literal: "hands on own face" and
    "covering face" describe the same gesture, but noticing that is the
    co-occurrence data's job, not the speller's.

    momentum is how much each generated tag conditions the ones after
    it, against the prompt's own pull. At 0 every tag answers to the
    prompt alone and they have nothing to do with each other -- for
    "night, city, rain", mechanical arms beside oversized wings beside a
    leg tattoo. At 1.0 a pick counts for as much as a prompt tag and the
    output reads as one scene, at the risk of becoming its own subject:
    "chair" pulls "office chair" pulls "computer keyboard" until the bar
    the prompt asked for is an office. The default sits between them,
    where a raincoat can follow an umbrella but a category quota still
    stops any one axis from taking the prompt over.

    n 0 = auto length: a target tag count is drawn from the corpus
    length distribution, and generation also stops early when no
    candidate is at least twice as likely as chance given the context --
    the data has nothing left to say.

    blacklist is a regex matched against each candidate tag (spaced
    form, case-insensitive, substring search): "hair|eyes" drops every
    hair and eye tag, "^black " only the ones starting that way. It
    filters the candidates rather than the result, so n tags still come
    back. An unparseable pattern is logged and ignored. The same regex
    is handed to FilterTags below, so one field bans a tag on both ends
    -- write alternatives with "|" rather than commas to keep the two
    reading it the same way.

    rating caps the exposure level of the statistics themselves: the
    co-occurrence tables are built per cumulative rating tier (general <
    sensitive < questionable < explicit, each including the tiers below),
    so at rating "general" the sampler has never seen the associations
    that only exist in racier posts and cannot drift toward them.

    The generated tags then go through the ProcessTags pipeline --
    replace_underscores, filter_tags, filter_subtags, each switchable.
    It runs over the whole prompt with `text` as the fixed tags, so the
    input is never filtered and only the generated tags are at risk. n
    counts what survives: post-processing can drop a pick (a blacklist hit,
    or a tag the prompt already implies, like "dog" once "white dog" is
    there), so the sampler is asked again for as many as went missing.
    That works because it is deterministic given the seed and extends
    its own prefix rather than redrawing, so a top-up round only ever
    adds tags. It gives up after a few rounds and logs how many it got.

    Examples:
        Input: text="night, city, rain", n=5, temperature=0.0
        Output: "night, city, rain, cityscape, building, night sky, scenery, road"
        Input: text="1girl, beach", n=8, clothes=0.25, pose=0.25, rest 0
        Output: "1girl, beach, swimsuit, bikini, holding swim ring, holding beachball"
        Input: text="1girl, cafe", n=4, blacklist="holding|cup"
        Output: "1girl, cafe, food, table, chair, plate"
    """

    # Every widget carries its own one-liner: the docstring above is the
    # reference, but nobody reads it with the node in front of them.
    DESCRIPTION = (
        "Extends a prompt with tags that go with it, drawn from Danbooru "
        "co-occurrence statistics.\n\n"
        "The sampler picks one tag at a time. A tag is a candidate only if "
        "something in the prompt pulls it, it scores by how much rarer than "
        "chance that pull is, and tags the corpus shows the prompt avoiding "
        "are removed outright.\n\n"
        "Start with n and the six category shares; the rest are for when "
        "the output is wrong in a specific way. Hover any widget for what "
        "it does."
    )

    INPUT_TYPES = lambda: {
        "required": {
            "text": ("STRING", {
                "forceInput": True,
                "tooltip": "The prompt to extend. Its tags condition every "
                           "pick and are never filtered themselves. Tags "
                           "outside the 20,811-tag vocabulary are ignored "
                           "silently -- Danbooru spells a bar "
                           "'bar_(place)', not 'bar'.",
            }),
            "n": ("INT", {
                "default": 20, "min": 0, "max": 100,
                "tooltip": "How many tags to add, counted after "
                           "post-processing. 0 = auto: the length is drawn "
                           "from the corpus and generation also stops early "
                           "once nothing is clearly better than chance.",
            }),
            **{
                key: widget
                for name, share in CATEGORY_DEFAULTS.items()
                for key, widget in (
                    (name, ("BOOLEAN", {
                        "default": True,
                        "tooltip": "Allow %s tags at all. Switching it off "
                                   "hands its share to the categories still "
                                   "on rather than shrinking the output."
                                   % name,
                    })),
                    (name + _SHARE_SUFFIX, ("FLOAT", {
                        "default": share, "min": CATEGORY_UNCAPPED,
                        "max": 1.0, "step": 0.05,
                        "tooltip": "How much of the output %s may take, "
                                   "relative to the other categories that "
                                   "are on: with only pose 0.2 and "
                                   "expressions 0.1, ten tags come back 7 "
                                   "and 3. -1 = allowed with no share of "
                                   "its own." % name,
                    })),
                )
            },
            "lift_threshold": ("FLOAT", {
                "default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01,
                "tooltip": "Veto strength. A candidate is banned when the "
                           "corpus expected it alongside a prompt tag often "
                           "enough (>= 15 posts) and it still came in below "
                           "this fraction of chance. Raise it when the "
                           "output contradicts the prompt in ways the data "
                           "merely discourages; 0.1 only catches pairs that "
                           "essentially never co-occur.",
            }),
            "momentum": ("FLOAT", {
                "default": DEFAULT_MOMENTUM, "min": 0.0, "max": 1.0,
                "step": 0.05,
                "tooltip": "How much each generated tag conditions the ones "
                           "after it. 0 = every tag answers to the prompt "
                           "alone and they have nothing to do with each "
                           "other. 1 = a pick counts as much as a prompt "
                           "tag, so the output reads as one scene but can "
                           "wander off into its own subject.",
            }),
            "repetition_penalty": ("FLOAT", {
                "default": DEFAULT_REPETITION_PENALTY,
                "min": 1.0, "max": 10.0, "step": 0.1,
                "tooltip": "Divide a tag's odds by this for every tag "
                           "already in the prompt that varies along the "
                           "same axis -- the same last word ('<colour> "
                           "skin'), or the same half of a linking word "
                           "('hands on own face' / 'hands on own head'). "
                           "2.0 halves them each time, so a second needs "
                           "twice the evidence the first did and a third "
                           "needs four times; 1.0 turns it off. Counters "
                           "momentum, which pulls hardest along the axis "
                           "it just moved on. Exact repeats are blocked "
                           "outright and are not what this controls.",
            }),
            "rating": (list(RATINGS) + ["all", "random"], {
                "default": "all",
                "tooltip": "Explicitness ceiling, on both halves of the "
                           "statistic: the co-occurrence tables come from "
                           "the matching corpus slice, and tags rated above "
                           "the request are masked. It is a ceiling, not a "
                           "target, so a named rating also gets a nudge "
                           "toward itself -- 'explicit' would otherwise "
                           "merely permit rather than lean. 'all' caps and "
                           "favours nothing, leaving the prompt to decide: "
                           "a nude prompt draws explicit tags, a school "
                           "uniform one draws none. 'random' picks one of "
                           "the four from the seed instead, each equally "
                           "likely -- a capped draw every time, but a "
                           "different cap on the next seed.",
            }),
            "temperature": ("FLOAT", {
                "default": 1.0, "min": 0.0, "max": 5.0, "step": 0.05,
                "tooltip": "Sampling randomness. 0 = always take the best "
                           "candidate, which makes the seed irrelevant and "
                           "every run identical. Higher spreads the picks "
                           "over weaker candidates.",
            }),
            "top_k": ("INT", {
                "default": 50, "min": 0, "max": 500,
                "tooltip": "Sample from this many best candidates per step. "
                           "0 = no limit. Ignored at temperature 0.",
            }),
            "top_p": ("FLOAT", {
                "default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01,
                "tooltip": "Keep the best candidates adding up to this much "
                           "probability. 1.0 = no limit. Watch out for 0, "
                           "which leaves exactly one candidate and turns "
                           "sampling back into greedy picking.",
            }),
            "min_p": ("FLOAT", {
                "default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01,
                "tooltip": "Drop candidates below this fraction of the best "
                           "candidate's probability. 0 = off.",
            }),
            "min_count": ("INT", {
                "default": 100, "min": 100, "max": 1000000, "step": 100,
                "tooltip": "Ignore tags with fewer than this many posts in "
                           "the requested rating tier. The default is the "
                           "vocabulary floor, i.e. no filtering. Raise it "
                           "when a prompt keeps surfacing tags too obscure "
                           "for your model to have learned.",
            }),
        },
        "optional": {
            "replace_underscores": ("BOOLEAN", {
                "default": True,
                "tooltip": "Write tags as 'blue eyes' rather than "
                           "'blue_eyes'.",
            }),
            "filter_tags": ("BOOLEAN", {
                "default": True,
                "tooltip": "Drop duplicates and blacklisted tags from the "
                           "finished prompt.",
            }),
            "filter_subtags": ("BOOLEAN", {
                "default": True,
                "tooltip": "Drop tags another tag already implies, keeping "
                           "'white dog' over 'dog'. It can eat a pick the "
                           "sampler just made, which is why the node asks "
                           "for replacements until n survive.",
            }),
            "blacklist": ("STRING", {
                "default": "", "multiline": False,
                "tooltip": "Regex matched against each candidate tag in "
                           "spaced form, case-insensitively: 'hair|eyes' "
                           "drops every hair and eye tag. It filters "
                           "candidates rather than results, so n tags still "
                           "come back. Use '|', not commas.",
            }),
            "seed": (
                "INT",
                {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                 "control_after_generate": True,
                 "tooltip": "Reproducibility. The same seed and settings "
                            "always give the same tags -- unless "
                            "temperature is 0, where the seed does nothing "
                            "at all."},
            ),
            "category_order": ("STRING", {
                "default": "", "multiline": False,
                "tooltip": "Comma separated category names -- characters, "
                           "body, expressions, pose, clothes, background, "
                           "compositions, objects, creatures, etc. The "
                           "added tags come back in that order instead of "
                           "the order they were drawn, so the same "
                           "settings put the same kinds of tag in the same "
                           "place. Empty keeps the draw order; the input "
                           "prompt is never reordered.",
            }),
        },
    }
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "execute"
    CATEGORY = "GeneratorPack/Tags"

    # each top-up round asks the sampler for more tags; bounded so an
    # over-aggressive filter cannot spin here forever
    _MAX_ROUNDS = 5

    # ceiling on a top-up ask, as a multiple of n: past this the filters
    # are eating so much that drawing more is not the answer
    _MAX_ASKED_FACTOR = 8

    @classmethod
    def _postprocess(cls, prompt, text, blacklist, replace_underscores,
                     filter_tags, filter_subtags):
        """Run the ProcessTags pipeline over a prompt.

        `blacklist` serves both ends of the node -- the sampler masks the
        candidates it matches, FilterTags removes anything that slips
        through -- and the node's own `text` is what FilterTags and
        FilterSubtags treat as fixed, so post-processing only ever
        touches the generated tags.
        """
        if not (replace_underscores or filter_tags or filter_subtags):
            return prompt
        return ProcessTags.execute(
            text=prompt,
            replace_underscores=replace_underscores,
            filter_tags=filter_tags,
            filter_subtags=filter_subtags,
            blacklist_tags=blacklist,
            fixed_tags=text,
        )[0]

    @classmethod
    def _fill(cls, n, draw, process, base, seen):
        """Draw until `n` tags survive post-processing, or rounds run out.

        n is a promise about the finished prompt, not about the draw:
        post-processing runs inside the node precisely so the count asked
        for is the count returned, which means the shortfall it leaves
        has to be redrawn here.

        A bigger ask is not a superset of a smaller one -- the category
        quotas are shares of the ask, so raising it re-splits the budget
        and can even come back with fewer tags -- so each round is judged
        on its own and the best one wins.
        """
        wanted, asked, kept = max(n, 0), max(n, 0), []
        for attempt in range(cls._MAX_ROUNDS if wanted else 1):
            generated = draw(asked if wanted else n)
            processed = process(f"{base.strip().rstrip(',')}, "
                                + ", ".join(_escape_brackets(t)
                                            for t in generated))
            survived = [t for t in _split_tags(processed) if t not in seen]
            if len(survived) > len(kept):
                kept = survived
            if not wanted or len(kept) >= wanted:
                break
            # scale the next ask by the share of the last one that
            # survived rather than by the shortfall: the filters drop a
            # roughly constant fraction, so topping up by the missing
            # count alone gains a round at a time and runs out of rounds
            # before it converges. +attempt keeps it moving when nothing
            # was filtered and the sampler is the one falling short.
            asked = min(-(-asked * wanted // max(len(survived), 1))
                        + attempt + 1,
                        cls._MAX_ASKED_FACTOR * wanted + 16)
        if wanted and len(kept) < wanted:
            logger.warning(
                "[TagsGenerator] only %d of %d tags after %d rounds -- lower "
                "lift_threshold or min_count, or relax blacklist and "
                "categories", len(kept), wanted, cls._MAX_ROUNDS,
            )
        return kept[:wanted] if wanted else kept

    @classmethod
    @exception_handler
    @log_prompt
    def execute(
        cls,
        text: str,
        n: int = 10,
        lift_threshold: float = 0.1,
        rating: str = "all",
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.95,
        min_p: float = 0.0,
        seed: int = 0,
        min_count: int = 100,
        blacklist: str = "",
        replace_underscores: bool = True,
        filter_tags: bool = True,
        filter_subtags: bool = True,
        momentum: float = DEFAULT_MOMENTUM,
        repetition_penalty: float = DEFAULT_REPETITION_PENALTY,
        category_order: str = "",
        **categories: float,
    ) -> tuple[str]:
        """Append companion tags to a prompt."""
        # "random" is resolved here rather than in the sampler: drawn
        # from the seed, so a workflow stays reproducible and a new seed
        # rerolls the cap along with the tags. "all" reaches the sampler
        # as itself -- the one value that caps nothing and favours
        # nothing, leaving the prompt to decide how explicit the tags
        # are. The rest go down in danbooru letter form: g/s/q/e.
        if rating == "random":
            rating = random.Random(seed).choice(RATINGS)
            logger.debug("[TagsGenerator] random rating -> %s", rating)
        rating = rating if rating == "all" else rating[0]
        momentum, repetition_penalty = _legacy_knobs(
            categories, momentum, repetition_penalty)
        spec = _categories_spec(categories)

        def process(prompt):
            return cls._postprocess(prompt, text, blacklist,
                                    replace_underscores, filter_tags,
                                    filter_subtags)

        if not suggest_available():
            logger.warning(
                "[TagsGenerator] suggest artifact not found; passing through"
            )
            return (process(text),)

        # the sampler masks candidates with a single regex, so the widget
        # value has to be compiled the same way FilterTags compiles it --
        # wildcards expanded, commas turned into alternation. Passing it
        # raw made every comma-separated blacklist match nothing, which
        # left the whole list to the post-filter: the sampler kept
        # spending picks on tags that were about to be thrown away.
        blacklist_rx = blacklist_pattern(blacklist)

        # No quota_total: the category quotas are shares of the round's
        # own ask. Pinning them to n would cap the whole draw at n tags,
        # so a top-up round asking for more would get the same list back
        # and the shortfall could never be refilled.
        def draw(m):
            return suggest_tags(
                text, n=m, min_count=min_count, temperature=temperature,
                top_k=top_k, top_p=top_p, min_p=min_p, seed=seed,
                rating=rating, categories=spec, blacklist=blacklist_rx,
                lift_th=lift_threshold,
                momentum=momentum,
                repetition_penalty=repetition_penalty,
            )

        # the pipeline is applied to the whole prompt, so the kept tags are
        # whatever the combined pass adds on top of the processed input
        base = process(text)
        base_tags = _split_tags(base)
        kept = cls._fill(n, draw, process, base, set(base_tags))
        if not kept:
            return (base,)
        kept = _sort_by_category(kept, category_order, lambda t: (t,))
        return (", ".join(base_tags + kept),)

    @classmethod
    def IS_CHANGED(
        cls,
        text: str,
        n: int = 10,
        lift_threshold: float = 0.1,
        rating: str = "all",
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.95,
        min_p: float = 0.0,
        seed: int = 0,
        min_count: int = 100,
        blacklist: str = "",
        replace_underscores: bool = True,
        filter_tags: bool = True,
        filter_subtags: bool = True,
        momentum: float = DEFAULT_MOMENTUM,
        repetition_penalty: float = DEFAULT_REPETITION_PENALTY,
        category_order: str = "",
        **categories: float,
    ) -> tuple:
        momentum, repetition_penalty = _legacy_knobs(
            categories, momentum, repetition_penalty)
        return (text, n, lift_threshold, rating, temperature, top_k, top_p,
                min_p, seed, min_count, blacklist, replace_underscores,
                filter_tags, filter_subtags, momentum,
                repetition_penalty, category_order,
                tuple(sorted(categories.items())))


class ClassifyTags(BasePrompt):
    """Split prompt tags into coarse category outputs.

    Buckets come from the same labels TagsGenerator samples with
    (resources/group/): the tag's category picks the bucket, and its
    rating level sends questionable and explicit tags to "nsfw"
    instead. Tags the labels do not cover -- about 3% of the
    vocabulary, and well under 1% of real prompt tags by frequency --
    fall back to the static tag_data tables, then to "others".

    Examples:
        Input: text="1boy, serafuku, sitting, smile, classroom"
        Output: characters="1boy", clothes="serafuku", pose="sitting",
                expression="smile", background="classroom", ...
    """

    INPUT_TYPES = lambda: {
        "required": {
            "text": ("STRING", {"forceInput": True}),
        },
    }
    RETURN_TYPES = ("STRING",) * len(BUCKETS)
    RETURN_NAMES = BUCKETS
    FUNCTION = "execute"
    CATEGORY = "GeneratorPack/Tags"

    @classmethod
    @exception_handler
    def execute(cls, text: str) -> tuple:
        """Classify tags into buckets and return one string per bucket."""
        buckets = classify_tags(text)
        return tuple(", ".join(buckets[b]) for b in BUCKETS)

    @classmethod
    def IS_CHANGED(cls, text: str) -> tuple:
        return (text,)


# Families that read as one decorative motif, capped by shared first word.
PREFIX_TAGS_DEFAULT = "fur-trimmed, lace-trimmed, ribbon-trimmed, frilled"


class GroupTags(BasePrompt):
    """Lay tags out in groups, one group per line.

    Tags sharing a last word are gathered together, falling back to a shared
    first word; anything unique stays where it is. Groups keep the order their
    first member appeared in, and each group starts on a new line, so a long
    prompt reads as a handful of themed blocks instead of one wall of commas.

    Person and relationship tags (1girl, 2boys, hetero, ...) are hoisted to the
    front as their own line, since a model reads the leading tags as the frame
    for everything after them. This is the ordering `sort_special` used to do
    upstream, done here instead -- grouping rewrites tag order wholesale, so a
    sort applied before it does not survive.

    Weights are ignored when deciding what groups with what, so
    `(areola slip:1.1)` still joins `areola slip`.

    `cap` trims each group to at most that many tags (0 leaves them all).
    Capping lives here rather than upstream for two reasons: the groups it
    trims are then the same groups the output shows, and, being the last node
    in the chain, it counts what actually survived the blacklist instead of
    reserving slots for tags about to be dropped. Colour-bearing tags are the
    first to go, then the tail of the group.

    Examples:
        Input:  1girl, blue eyes, red eyes, standing, solo
        Output: 1girl, solo,
                blue eyes, red eyes,
                standing
    """

    # Person count and relationship tags -- the ones worth reading first.
    SPECIAL_PATTERN = (
        r"([\d]+girls?|multiple girls|[\d]+boys?|multiple boys|couple|hetero|yuri)"
    )
    # Dropped first when a group is over cap: a second colour of the same thing
    # adds less than a different thing.
    COLORS = (
        "black", "white", "aqua", "beige", "blue", "brown", "green", "grey",
        "lavender", "maroon", "pink", "purple", "red", "silver", "violet",
        "yellow", "multicolored",
    )

    INPUT_TYPES = lambda: {
        "required": {
            "text": ("STRING", {"forceInput": True}),
            "special_first": ("BOOLEAN", {"default": True}),
        },
        "optional": {
            "cap": ("INT", {"default": 0, "min": 0, "max": 100}),
            "prefix_tags": ("STRING", {"default": PREFIX_TAGS_DEFAULT}),
            "special_pattern": ("STRING", {"default": ""}),
            "category_order": ("STRING", {"default": ""}),
        },
    }
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("processed_text",)
    FUNCTION = "execute"
    CATEGORY = "GeneratorPack/Tags"

    @classmethod
    def _cap_prefixes(cls, tags: list[str], cap: int, prefixes: list[str]) -> list[str]:
        """Keep at most `cap` tags per decorative prefix, in order of appearance."""
        counts = defaultdict(int)
        out = []
        for t in tags:
            bare = cls.remove_weight(t)
            p = next((p for p in prefixes if bare.startswith(p)), None)
            if p is not None:
                if counts[p] >= cap:
                    continue
                counts[p] += 1
            out.append(t)
        return out

    @classmethod
    def _cap_group(cls, group: list[str], cap: int) -> list[str]:
        """Trim one group to `cap`, shedding colour-bearing tags first, then the tail."""
        if len(group) <= cap:
            return group
        has_color = lambda t: any(w in cls.COLORS for w in cls.remove_weight(t).split())
        order = [i for i, t in enumerate(group) if has_color(t)]
        order += range(len(group) - 1, -1, -1)
        dropped = set(list(dict.fromkeys(order))[: len(group) - cap])
        return [t for i, t in enumerate(group) if i not in dropped]

    @classmethod
    def _group(cls, tags: list[str]) -> list[list[str]]:
        """Bucket tags by shared last word, else shared first word, else alone."""
        keys = [cls.remove_weight(t).split(" ") for t in tags]
        first_cnt, last_cnt = defaultdict(int), defaultdict(int)
        for words in keys:
            first_cnt[words[0]] += 1
            last_cnt[words[-1]] += 1

        def key_of(words, i):
            if last_cnt[words[-1]] >= 2:
                return ("s", words[-1])
            if first_cnt[words[0]] >= 2:
                return ("p", words[0])
            return ("u", i)

        groups, order = defaultdict(list), []
        for i, (tag, words) in enumerate(zip(tags, keys)):
            k = key_of(words, i)
            if k not in groups:
                order.append(k)
            groups[k].append(tag)
        return [groups[k] for k in order]

    @classmethod
    def _order_groups(cls, groups: list[list[str]], order: str) -> list[list[str]]:
        """Sort the groups into the category order named by `order`."""
        return _sort_by_category(groups, order, lambda g: g)

    @classmethod
    @exception_handler
    def execute(
        cls,
        text: str,
        special_first: bool = True,
        cap: int = 0,
        prefix_tags: str = PREFIX_TAGS_DEFAULT,
        special_pattern: str = "",
        category_order: str = "",
    ) -> tuple[str]:
        """Cap each group, order them, then lay them out one per line."""
        tags = [t.strip() for t in cls.split_tags(text) if t.strip()]
        if not tags:
            return ("",)

        if cap > 0:
            prefixes = [p.strip() for p in prefix_tags.split(",") if p.strip()]
            tags = cls._cap_prefixes(tags, cap, prefixes)

        lines = []
        if special_first:
            pattern = special_pattern.strip() or cls.SPECIAL_PATTERN
            specials = [t for t in tags if re.search(pattern, cls.remove_weight(t))]
            if specials:
                lines.append(specials)
                tags = [t for t in tags if t not in specials]

        for group in cls._order_groups(cls._group(tags), category_order):
            lines.append(cls._cap_group(group, cap) if cap > 0 else group)
        return (",\n".join(", ".join(line) for line in lines if line),)

    @classmethod
    def IS_CHANGED(
        cls,
        text: str,
        special_first: bool = True,
        cap: int = 0,
        prefix_tags: str = PREFIX_TAGS_DEFAULT,
        special_pattern: str = "",
        category_order: str = "",
    ) -> tuple:
        return (text, special_first, cap, prefix_tags, special_pattern,
                category_order)


