import json
import pathlib
import subprocess
import sys


def test_phase0_sanity_end2end():
    # Run the script
    subprocess.check_call([sys.executable, "scripts/phase0_sanity/playground.py"])

    reports = pathlib.Path("reports")
    assert (reports / "phase0_sanity_result.json").exists()
    assert (reports / "phase0_sanity_metrics.json").exists()

    m = json.loads((reports / "phase0_sanity_metrics.json").read_text(encoding="utf-8"))
    assert m["json_error_rate"] == 0.0
    assert m["rouge_l"] >= 0.70

    # human proof
    proof = list(reports.glob("phase0_sanity_proof_*.md"))
    assert len(proof) >= 1
