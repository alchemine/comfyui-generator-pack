import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def archive(tmp_path_factory):
    """The names in the zip `comfy node publish` would upload, built from a clone.

    A clone, so that node.zip and whatever else the working tree holds stay out
    of it; .comfyignore is copied over so the test also sees an uncommitted one.
    """
    clone = tmp_path_factory.mktemp("clone") / "pack"
    subprocess.run(["git", "clone", "-q", str(PACK_DIR), str(clone)], check=True)
    if (PACK_DIR / ".comfyignore").exists():
        shutil.copy(PACK_DIR / ".comfyignore", clone)
    subprocess.run(
        ["uvx", "--from", "comfy-cli", "comfy", "--skip-prompt", "--no-enable-telemetry", "node", "pack"],
        cwd=clone,
        check=True,
        capture_output=True,
    )  # fmt: skip
    return zipfile.ZipFile(clone / "node.zip").namelist()


pytestmark = pytest.mark.skipif(
    shutil.which("uvx") is None, reason="uvx builds the archive"
)


def test_the_archive_carries_no_docs_or_tests(archive):
    assert [n for n in archive if n.startswith(("docs/", "tests/"))] == []


def test_the_archive_still_carries_the_pack(archive):
    assert {
        "__init__.py",
        "pyproject.toml",
        "nodes/tags.py",
        "nodes/lib/tag_solo.py",
    } <= set(archive)
