"""
NarraSeed Integration Tests
Tests the complete pipeline: CSV → Normalize → PELT → DTW → Foundry IQ → LLM → Render
"""

import io
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from backend.arc_matcher import match_arc, generate_arc_templates
from backend.changepoint import detect_turning_points
from backend.foundry_iq import get_narrative_template
from backend.narrative import generate_narrative
from backend.preprocessor import normalize_timeseries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_normalize_timeseries():
    """Test basic timeseries normalization."""
    raw_data = [(1, 2.8), (2, 2.85), (3, 2.9), (4, 3.5), (5, 3.6), (6, 3.7), (7, 3.8), (8, 3.9), (9, 4.0)]
    result = normalize_timeseries(raw_data)
    assert result["stats"]["n_points"] == 9
    assert min(result["y_normalized"]) == 0.0
    assert max(result["y_normalized"]) == 1.0
    logger.info(f"✅ Normalization test passed: {result['stats']}")


def test_normalize_constant_values():
    """Test handling of constant values."""
    data = [(0, 5), (1, 5), (2, 5)]
    result = normalize_timeseries(data)
    assert result["stats"]["min"] == 5
    assert result["stats"]["max"] == 5
    logger.info("✅ Constant value handling passed")


def test_detect_turning_points():
    """Test turning point detection."""
    values = np.array([0.0, 0.04, 0.08, 0.58, 0.67, 0.75, 0.83, 0.92, 1.0])
    points = detect_turning_points(values, pen=1.0)
    assert isinstance(points, list)
    assert all("direction" in p for p in points)
    logger.info(f"✅ Turning points detected: {len(points)} points")


def test_detect_no_turning_points_flat():
    """Test flat series."""
    values = np.array([0.5] * 10)
    points = detect_turning_points(values)
    assert isinstance(points, list)
    logger.info("✅ Flat series handling passed")


def test_match_arc_rags_to_riches():
    """Test arc matching for upward trend."""
    arc = match_arc([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    assert arc["arc_name"] == "Rags to Riches"
    assert arc["confidence"] >= 0.0
    logger.info(f"✅ Arc matching (Rags to Riches): {arc['arc_name']} ({arc['confidence']:.2%})")


def test_match_arc_tragedy():
    """Test arc matching for downward trend."""
    arc = match_arc([1.0, 0.8, 0.6, 0.4, 0.2, 0.0])
    assert arc["arc_name"] in ["Tragedy", "Icarus"]
    logger.info(f"✅ Arc matching (downward): {arc['arc_name']} ({arc['confidence']:.2%})")


def test_all_arc_templates_exist():
    """Test that all 6 narrative templates exist."""
    templates = generate_arc_templates()
    assert len(templates) == 6
    expected = {"Rags to Riches", "Tragedy", "Icarus", "Man in a Hole", "Phoenix", "Oedipus"}
    assert set(templates.keys()) == expected
    logger.info(f"✅ All 6 arc templates available: {list(templates.keys())}")


def test_foundry_iq_template_retrieval():
    """Test Foundry IQ template retrieval."""
    result = get_narrative_template("Phoenix")
    assert "narrative_guidelines" in result
    assert "opening_template" in result
    assert "climax_template" in result
    assert "resolution_template" in result
    assert "citation" in result
    logger.info(f"✅ Foundry IQ template retrieved: {result['citation']['source']}")


def test_foundry_iq_fallback():
    """Test Foundry IQ fallback for unknown arc."""
    result = get_narrative_template("UnknownArc12345")
    assert "narrative_guidelines" in result
    assert "citation" in result
    logger.info(f"✅ Foundry IQ fallback: {result['citation']['retrieval_method']}")


def test_narrative_generation():
    """Test narrative generation."""
    data = [(i, y) for i, y in enumerate([0.1, 0.2, 0.4, 0.7, 0.5])]
    turning_points = [
        {"index": 2, "severity": 0.5, "direction": "growth", "value_before": 0.2, "value_after": 0.4}
    ]
    foundry = {
        "narrative_guidelines": "Generate an inspiring story of growth",
        "opening_template": "It began...",
        "climax_template": "Then came...",
        "resolution_template": "In the end...",
        "citation": {"source": "Test", "document_id": "test-1"}
    }
    
    result = generate_narrative("Rags to Riches", data, turning_points, foundry, "dramatic")
    
    assert "story" in result
    assert "arc" in result
    assert "citations" in result
    assert result["arc"] == "Rags to Riches"
    assert result["grounding"]["foundry_iq_used"] is True
    logger.info(f"✅ Narrative generated: {len(result['story'])} chars, {len(result['citations'])} citations")


def test_end_to_end_pipeline():
    """Test complete pipeline from data to narrative."""
    # Create sample data
    csv_data = io.StringIO("""Time,Value
0,10
1,15
2,18
3,22
4,25
5,23
6,20
7,19
""")
    csv_data.seek(0)
    
    # Step 1: Normalize
    df = pd.read_csv(csv_data)
    data = list(zip(df.iloc[:, 0].astype(float), df.iloc[:, 1].astype(float)))
    normalized = normalize_timeseries(data)
    logger.info(f"Step 1 ✅: Normalized {len(data)} data points")
    
    # Step 2: Detect turning points
    values = np.asarray(normalized["y_normalized"], dtype=float)
    turning_points = detect_turning_points(values)
    logger.info(f"Step 2 ✅: Detected {len(turning_points)} turning points")
    
    # Step 3: Match arc
    arc_result = match_arc(normalized["y_normalized"])
    logger.info(f"Step 3 ✅: Matched arc '{arc_result['arc_name']}' ({arc_result['confidence']:.2%})")
    
    # Step 4: Get Foundry IQ template
    foundry = get_narrative_template(arc_result["arc_name"])
    logger.info(f"Step 4 ✅: Retrieved Foundry IQ template from {foundry['citation']['source']}")
    
    # Step 5: Generate narrative
    narrative = generate_narrative(
        arc_result["arc_name"],
        data,
        turning_points,
        foundry,
        "dramatic"
    )
    logger.info(f"Step 5 ✅: Generated narrative ({len(narrative['story'])} chars)")
    
    # Verify all fields present
    assert "story" in narrative
    assert "citations" in narrative
    assert len(narrative["citations"]) > 0
    assert narrative["grounding"]["foundry_iq_used"] is True
    
    logger.info("✅✅✅ COMPLETE PIPELINE TEST PASSED ✅✅✅")


if __name__ == "__main__":
    test_normalize_timeseries()
    test_normalize_constant_values()
    test_detect_turning_points()
    test_detect_no_turning_points_flat()
    test_match_arc_rags_to_riches()
    test_match_arc_tragedy()
    test_all_arc_templates_exist()
    test_foundry_iq_template_retrieval()
    test_foundry_iq_fallback()
    test_narrative_generation()
    test_end_to_end_pipeline()
    print("\n🎉 All tests passed! NarraSeed pipeline is operational.")
