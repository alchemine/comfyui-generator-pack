import re
from pathlib import Path

PACK_DIR = Path(__file__).resolve().parents[3]


def images(name):
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", (PACK_DIR / name).read_text())


def test_readmes_show_the_same_images():
    assert images("README_ko.md") == images("README.md")
