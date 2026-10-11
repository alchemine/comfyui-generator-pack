import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
LIB_DIR = PACK_DIR / "nodes" / "lib"

sys.path.insert(0, str(LIB_DIR))
import tag_guard  # noqa: E402


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


@pytest.mark.parametrize("tag", ["amiya", "ganyu", "amiya (arknights)"])
def test_bare_name_is_a_character(tag):
    assert tag_guard.bucket_of(tag) == "character"


@pytest.mark.parametrize("tag", ["rose", "cat"])
def test_general_tag_stays_general(tag):
    assert tag_guard.bucket_of(tag) != "character"


def test_node_output(pack):
    node = pack.NODE_CLASS_MAPPINGS["ClassifyTags"]
    out = dict(
        zip(node.RETURN_NAMES, node.execute(text="amiya \\(arknights\\), amiya"))
    )
    assert out["character"] == "amiya (arknights), amiya"
