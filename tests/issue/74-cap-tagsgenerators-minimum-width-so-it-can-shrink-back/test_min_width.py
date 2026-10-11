from pathlib import Path

PACK_DIR = Path(__file__).resolve().parents[3]
JS = PACK_DIR / "web" / "js" / "tags_generator_categories.js"


def test_compute_size_is_capped():
    source = JS.read_text(encoding="utf-8")
    assert "prototype.computeSize" in source
    assert "spec.width ?? w" not in source
