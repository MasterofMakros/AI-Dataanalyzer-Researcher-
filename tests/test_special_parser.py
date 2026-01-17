import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECIAL_PARSER_PATH = ROOT / "infra" / "docker" / "special-parser"
sys.path.insert(0, str(SPECIAL_PARSER_PATH))

import special_parser_core  # noqa: E402

SAMPLES_DIR = ROOT / "data" / "samples" / "special-parser"


def _assert_result(result):
    assert result.success is True
    assert result.metadata
    assert result.preview
    assert result.derived_text


def test_parse_3d_obj():
    result = special_parser_core.parse_file(SAMPLES_DIR / "sample.obj", "3d")
    _assert_result(result)
    assert result.metadata.get("vertex_count") == 4
    # The sample has 1 quad face (4 vertices per face).
    assert result.metadata.get("face_count") == 1


def test_parse_cad_step():
    result = special_parser_core.parse_file(SAMPLES_DIR / "sample.step", "cad")
    _assert_result(result)
    assert result.metadata.get("schema") == "AP203"


def test_parse_gis_geojson():
    result = special_parser_core.parse_file(SAMPLES_DIR / "sample.geojson", "gis")
    _assert_result(result)
    assert result.metadata.get("feature_count") == 1


def test_parse_font_woff():
    result = special_parser_core.parse_file(SAMPLES_DIR / "sample.woff", "fonts")
    _assert_result(result)
    assert result.metadata.get("format") == "woff"
