"""Utility module for nodes."""

import re
import logging
import tomllib
from pathlib import Path
from functools import wraps


#################################################################
# Constants
#################################################################
ROOT_DIR = Path(__file__).parent.parent.parent

RESOURCES_DIR = ROOT_DIR / "resources"


def _package_name() -> str:
    """Read the pack name from `pyproject.toml`, falling back to the directory."""
    try:
        with open(ROOT_DIR / "pyproject.toml", "rb") as f:
            return tomllib.load(f)["project"]["name"]
    except Exception:
        return ROOT_DIR.name


PACKAGE_NAME = _package_name()


#################################################################
# Logger setup
#################################################################
# One logger for the whole pack, so the level is set in one place:
#     logging.getLogger(PACKAGE_NAME).setLevel(logging.DEBUG)
# The per-node label comes from the message, not from the logger name:
# `logger.info("[TagsGenerator] ...")` renders as `[<pack>/TagsGenerator]`.
# Untagged lines fall back to the module the call came from.
_NODE_TAG_RE = re.compile(r"^\[([^\]]+)\]\s*")


class _NodeTagFormatter(logging.Formatter):
    def format(self, record):
        message = record.getMessage()
        match = _NODE_TAG_RE.match(message)
        if match:
            node = match.group(1)
            message = message[match.end():]
        else:
            node = record.module
        original = (record.msg, record.args)
        record.msg = f"[{PACKAGE_NAME}/{node}] {message}"
        record.args = ()
        try:
            return super().format(record)
        finally:
            record.msg, record.args = original


def get_logger(level: int = logging.INFO) -> logging.Logger:
    """Return the pack-wide logger, configuring its handler on first call."""
    logger = logging.getLogger(PACKAGE_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        # INFO/WARNING/ERROR are the levels actually used; 7 fits the longest.
        handler.setFormatter(_NodeTagFormatter(
            "%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False  # Prevent duplicate logs from root logger
    return logger


#################################################################
# Utility functions
#################################################################
def exception_handler(func):
    """Handle unexpected exceptions in a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            get_logger().error("unexpected error in '%s'", func.__name__,
                               exc_info=True)
            raise

    return wrapper


attn_syntax = (
    r"\\\(|"
    r"\\\)|"
    r"\\\[|"
    r"\\]|"
    r"\\\\|"
    r"\\|"
    r"\(|"
    r"\[|"
    r":\s*([+-]?[.\d]+)\s*\)|"
    r"\)|"
    r"]|"
    r"[^\\()\[\]:]+|"
    r":"
)
re_attention = re.compile(attn_syntax, re.X)
re_break = re.compile(r"\s*\bBREAK\b\s*", re.S)


# NOTE: prompt attention parsing is taken from KohakuBlueleaf's
# https://github.com/KohakuBlueleaf/z-tipo-extension/blob/6c6bd9f40bca42f9bbab8b1e7a2ba51cb0d5424b/nodes/tipo.py#L63
def parse_prompt_attention(text):
    r"""
    Parses a string with attention tokens and returns a list of pairs: text and its associated weight.
    Accepted tokens are:
      (abc) - increases attention to abc by a multiplier of 1.1
      (abc:3.12) - increases attention to abc by a multiplier of 3.12
      [abc] - decreases attention to abc by a multiplier of 1.1
      \( - literal character '('
      \[ - literal character '['
      \) - literal character ')'
      \] - literal character ']'
      \\ - literal character '\'
      anything else - just text

    >>> parse_prompt_attention('normal text')
    [['normal text', 1.0]]
    >>> parse_prompt_attention('an (important) word')
    [['an ', 1.0], ['important', 1.1], [' word', 1.0]]
    >>> parse_prompt_attention('(unbalanced')
    [['unbalanced', 1.1]]
    >>> parse_prompt_attention('\(literal\]')
    [['(literal]', 1.0]]
    >>> parse_prompt_attention('(unnecessary)(parens)')
    [['unnecessaryparens', 1.1]]
    >>> parse_prompt_attention('a (((house:1.3)) [on] a (hill:0.5), sun, (((sky))).')
    [['a ', 1.0],
     ['house', 1.5730000000000004],
     [' ', 1.1],
     ['on', 1.0],
     [' a ', 1.1],
     ['hill', 0.55],
     [', sun, ', 1.1],
     ['sky', 1.4641000000000006],
     ['.', 1.1]]
    """
    res = []
    round_brackets = []
    square_brackets = []

    round_bracket_multiplier = 1.1
    square_bracket_multiplier = 1 / 1.1

    def multiply_range(start_position, multiplier):
        for p in range(start_position, len(res)):
            res[p][1] *= multiplier

    for m in re_attention.finditer(text):
        text = m.group(0)
        weight = m.group(1)
        if text.startswith(r"\\"):
            res.append([text[1:], 1.0])
        elif text == r"(":
            round_brackets.append(len(res))
        elif text == r"[":
            square_brackets.append(len(res))
        elif weight is not None and round_brackets:
            multiply_range(round_brackets.pop(), float(weight))
        elif text == r")" and round_brackets:
            multiply_range(round_brackets.pop(), round_bracket_multiplier)
        elif text == r"]" and square_brackets:
            multiply_range(square_brackets.pop(), square_bracket_multiplier)
        else:
            parts = re.split(re_break, text)
            for i, part in enumerate(parts):
                if i > 0:
                    res.append(["BREAK", 1.0])
                res.append([part, 1.0])

    for pos in round_brackets:
        multiply_range(pos, round_bracket_multiplier)

    for pos in square_brackets:
        multiply_range(pos, square_bracket_multiplier)

    if len(res) == 0:
        res = [["", 1.0]]

    # merge runs of identical weights
    i = 0
    while i + 1 < len(res):
        if res[i][1] == res[i + 1][1]:
            res[i][0] += res[i + 1][0]
            res.pop(i + 1)
        else:
            i += 1

    return res


# A Danbooru qualifier binds straight onto the tag it disambiguates --
# "star_(sky)", "ganyu_(genshin_impact)" -- with no space before the
# bracket, which is what separates it from A1111 emphasis: "(cat)",
# "1girl, (blue eyes:1.2)" and even "star (sky)" all keep meaning
# emphasis because a comma or a space precedes the bracket. Already
# escaped "\(" is left alone: the backslash is not a word character.
DANBOORU_QUALIFIER = re.compile(r"(?<=\w)\(([^()]*)\)")


def escape_qualifiers(text: str) -> str:
    """Escape the brackets of Danbooru qualifiers so they stay literal.

    Without this, attention parsing reads the qualifier as emphasis and
    "star_(sky)" comes back out as "star_(sky:1.1)" -- the tag silently
    gains a weight it never asked for.
    """
    return DANBOORU_QUALIFIER.sub(r"\\(\1\\)", text)


def standardize_prompt(text: str) -> str:
    # Handle :3
    text = re.sub(r":3\)", r":3:1.1)", text)
    text = escape_qualifiers(text)
    attentions = parse_prompt_attention(text)
    result = ""
    for tag, weight in attentions:
        if weight != 1:
            tag = re.sub(
                r"[^,\n\s]+(?:\s+[^,\n\s]+)*",
                rf"(\g<0>:{round(weight, 2)})",
                tag,
            )
        result = f"{result}{tag}"
    return result
