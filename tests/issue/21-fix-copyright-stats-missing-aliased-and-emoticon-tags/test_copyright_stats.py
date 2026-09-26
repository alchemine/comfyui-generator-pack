import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

PACK_DIR = Path(__file__).resolve().parents[3]
DATA = PACK_DIR / "resources" / "copyright_v1.npz"
VOCAB = PACK_DIR / "resources" / "suggest_v1.1.npz"


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
def tag_copyright(pack):
    return sys.modules["comfyui_generator_pack.nodes.lib.tag_copyright"]


@pytest.fixture(scope="module")
def posts():
    data = np.load(DATA)
    return dict(zip((str(t) for t in data["tags"]), data["n_posts"].tolist()))


@pytest.mark.parametrize(
    "tag", ["plugsuit_(evangelion)", "interface_headset_(evangelion)", "trap"]
)
def test_aliased_tag_has_posts(posts, tag):
    assert posts[tag] > 0


@pytest.mark.parametrize("tag", ["^_^", "=_=", "0_0", "u_u", "x_x"])
def test_emoticon_has_posts(posts, tag):
    assert posts[tag] > 0


def test_plugsuit_is_masked(tag_copyright):
    vocab = [str(t) for t in np.load(VOCAB)["tags"]]
    mask = tag_copyright.Copyright(vocab, path=str(DATA)).mask
    assert mask[vocab.index("plugsuit_(evangelion)")]


def test_code_pins_the_local_data(tag_copyright):
    assert hashlib.sha256(DATA.read_bytes()).hexdigest() == tag_copyright._SHA256
