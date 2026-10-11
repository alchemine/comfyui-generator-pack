import importlib.util
import sys
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def weight():
    spec = importlib.util.spec_from_file_location(
        "comfyui_generator_pack",
        PACK_DIR / "__init__.py",
        submodule_search_locations=[str(PACK_DIR)],
    )
    pack = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = pack
    spec.loader.exec_module(pack)
    node = pack.NODE_CLASS_MAPPINGS["WeightTags"]

    def run(text, **kwargs):
        return node.execute(text=text, **kwargs)[0]

    return run


def test_line_breaks_stay(weight):
    text = "1girl,\n:3,\nbook, holding book,\nlibrary"
    assert weight(text, expressions=True, expressions_weight=1.1) == (
        "1girl,\n(:3:1.1),\nbook, holding book,\nlibrary"
    )


def test_missing_spaces_stay(weight):
    assert weight("1girl,:3,library", expressions=True, expressions_weight=1.1) == (
        "1girl,(:3:1.1),library"
    )


def test_trailing_comma_stays(weight):
    assert weight("1girl, :3,", expressions=True, expressions_weight=1.1) == (
        "1girl, (:3:1.1),"
    )
