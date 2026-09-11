import os
import sys
import tempfile
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TECHNICAL_DIR = PROJECT_ROOT / "multi_agent_lit_review" / "technical_agent"

from multi_agent_lit_review.technical_agent.benchmark import run_reproducible_benchmark

def test_technical_agent_benchmark_execution():
    """Verifies that the technical agent benchmark script executes and returns valid metrics."""
    results = run_reproducible_benchmark()
    assert "1_traditional_manual_fitting" in results
    assert "2_single_pass_baseline" in results
    assert "3_single_agent_script" in results
    assert "4_specialist_multi_agent_system" in results

    sys4 = results["4_specialist_multi_agent_system"]
    assert "rmse_prey" in sys4
    assert "rmse_predator" in sys4
    assert "runtime_seconds" in sys4
    assert sys4["convergence_success"] is True

    json_path = TECHNICAL_DIR / "benchmark_results.json"
    assert json_path.exists()
