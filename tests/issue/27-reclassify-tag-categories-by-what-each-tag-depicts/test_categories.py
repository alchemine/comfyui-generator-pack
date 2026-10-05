import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]

WIDGETS = (
    "subject",
    "body",
    "expressions",
    "pose",
    "clothes",
    "background",
    "bg_details",
    "framing",
)
HIDDEN = {"style", "text", "meta", "concept", "creatures"}

PROMPT = (
    "multiple views, character profile, (full body:0.8), cropped torso, "
    "turnaround, profile, from above, from below, text, emphasis lines, "
    "comic expression, variations, (wince:1.1), (>:\\(:1.1), (excited:1.1), "
    "(bored:1.1), (trembling:1.1), (notice lines:1.1), breasts"
)


@pytest.fixture(scope="module")
def pack():
    spec = importlib.util.spec_from_file_location(
        "comfyui_generator_pack",
        PACK_DIR / "__init__.py",
        submodule_search_locations=[str(PACK_DIR)],
    )
    pack = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = pack
    spec.loader.exec_module(pack)
    return pack


@pytest.fixture(scope="module")
def labels(pack):
    return sys.modules["comfyui_generator_pack.nodes.lib.tag_category"].load_labels()


@pytest.fixture
def spec_of(pack, monkeypatch):
    """Run TagsGenerator with only `on` switched on; return its categories spec."""
    tags = sys.modules["comfyui_generator_pack.nodes.tags"]
    seen = []

    def fake_suggest(text, **kwargs):
        seen.append(kwargs["categories"])
        return []

    monkeypatch.setattr(tags, "suggest_tags", fake_suggest)

    def run(*on):
        toggles = {w: w in on for w in WIDGETS}
        pack.NODE_CLASS_MAPPINGS["TagsGenerator"].execute(
            text="1girl", n=5, auto=True, **toggles
        )
        return seen[-1]

    return run


@pytest.mark.parametrize(
    "tag, category",
    [
        ("blue eyes", "eyes"),
        ("weapon", "objects"),
        ("cup", "objects"),
        ("lamp", "objects"),
        ("collarbone", "body"),
        ("comic", "style"),
        ("speech bubble", "text"),
        ("speed lines", "style"),
        ("puff of air", "expressions"),
        ("sweatdrop", "expressions"),
    ],
)
def test_labels_follow_depiction(labels, tag, category):
    assert labels.category_name(tag) == category


def test_background_widget_opens_only_background(spec_of):
    assert spec_of("background") == "background"


def test_bg_details_widget_opens_its_three(spec_of):
    assert spec_of("bg_details") == "objects+lighting+effects"


def test_widgets_never_open_hidden_categories(spec_of):
    opened = {c for group in spec_of(*WIDGETS).split(", ") for c in group.split("+")}
    assert len(opened) == 13
    assert not opened & HIDDEN


@pytest.mark.parametrize("seed", range(5))
def test_background_only_draws_background(pack, labels, seed):
    toggles = {w: w == "background" for w in WIDGETS}
    (out,) = pack.NODE_CLASS_MAPPINGS["TagsGenerator"].execute(
        text=PROMPT, n=10, auto=True, seed=seed, **toggles
    )
    given = {t.strip() for t in PROMPT.split(",")}
    added = [t for t in out.split(", ") if t not in given]
    assert added
    wrong = [
        t
        for t in added
        if labels.category_name(t.replace("\\(", "(").replace("\\)", ")"))
        != "background"
    ]
    assert not wrong
