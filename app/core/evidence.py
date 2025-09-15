from pathlib import Path
import datetime
import hashlib
import json

EVID_DIR = Path("reports/trial_tasks")


def write_evidence(trace_id: str, payload: dict) -> None:
    """mdとjsonlにEvidenceを保存（日別集約）。"""
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    body = {"trace_id": trace_id, "created_at": ts + "Z", **payload}

    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
    md = EVID_DIR / f"{trace_id}_{ts}.md"
    md.write_text(
        "# Task Evidence\n\n"
        f"- trace_id: {trace_id}\n- created_at: {ts}Z\n- sha256: {digest}\n\n"
        "```json\n" + json.dumps(body, indent=2) + "\n```\n"
    )
    jl = EVID_DIR / f"tasks_{ts[:8]}.jsonl"
    with jl.open("a") as f:
        f.write(json.dumps(body) + "\n")
