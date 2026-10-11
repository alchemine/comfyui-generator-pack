from pathlib import Path

PACK_DIR = Path(__file__).resolve().parents[3]
JS = PACK_DIR / "web" / "js" / "tags_generator_categories.js"


def test_tagsgenerator_width_is_pinned():
    source = JS.read_text(encoding="utf-8")
    assert "width: 210" in source
    assert "spec.width" in source
