import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
LIB_DIR = PACK_DIR / "nodes" / "lib"

sys.path.insert(0, str(LIB_DIR))
import tag_guard  # noqa: E402

BUCKETS = (
    "subject",
    "character",
    "pose",
    "expressions",
    "body",
    "clothes",
    "background",
    "bg_details",
    "framing",
    "others",
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


def test_outputs_follow_tags_generator(pack):
    node = pack.NODE_CLASS_MAPPINGS["ClassifyTags"]
    assert tuple(node.RETURN_NAMES) == BUCKETS
    assert node.RETURN_TYPES == ("STRING",) * len(BUCKETS)


@pytest.mark.parametrize(
    "tag, bucket",
    [
        ("1girl", "subject"),
        ("sitting", "pose"),
        (":3", "expressions"),
        ("long hair", "body"),
        ("blue eyes", "body"),
        ("shirt", "clothes"),
        ("library", "background"),
        ("cup", "bg_details"),
        ("sunlight", "bg_details"),
        ("light particles", "bg_details"),
        ("from above", "framing"),
        ("monochrome", "others"),
        ("dragon", "others"),
        ("highres", "others"),
    ],
)
def test_bucket_follows_the_category_group(tag, bucket):
    assert tag_guard.bucket_of(tag) == bucket


@pytest.mark.parametrize(
    "tag, bucket", [("sex", "pose"), ("nipples", "body"), ("nude", "clothes")]
)
def test_rating_does_not_override_the_category(tag, bucket):
    assert tag_guard.bucket_of(tag) == bucket


def test_node_outputs(pack):
    node = pack.NODE_CLASS_MAPPINGS["ClassifyTags"]
    out = dict(zip(node.RETURN_NAMES, node.execute(text="1girl, sitting, cup")))
    assert out["subject"] == "1girl"
    assert out["pose"] == "sitting"
    assert out["bg_details"] == "cup"
