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


def test_character_follows_subject(pack):
    node = pack.NODE_CLASS_MAPPINGS["ClassifyTags"]
    assert tuple(node.RETURN_NAMES) == BUCKETS


@pytest.mark.parametrize(
    "tag, bucket",
    [
        ("ganyu (genshin impact)", "character"),
        ("hatsune miku", "character"),
        ("ganyu", "character"),
        ("1girl", "subject"),
        ("smile", "expressions"),
    ],
)
def test_bucket(tag, bucket):
    assert tag_guard.bucket_of(tag) == bucket


def test_node_output(pack):
    node = pack.NODE_CLASS_MAPPINGS["ClassifyTags"]
    out = dict(
        zip(
            node.RETURN_NAMES,
            node.execute(text="1girl, ganyu \\(genshin impact\\), smile"),
        )
    )
    assert out["character"] == "ganyu (genshin impact)"
    assert out["others"] == ""
