"""Oracle-backed runtime classifier for local reverse samples.

Consumes an oracle artifact and a raw runtime artifact to classify
candidate/control runs based on ANSI-stripped stdout substring matching.

Does NOT execute target samples. Does NOT hardcode sample-specific data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return ANSI_ESCAPE_RE.sub("", text)


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def extract_oracle_signals(oracle: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Extract success and failure signal strings from oracle artifact."""
    success_signals: list[str] = []
    failure_signals: list[str] = []

    success_path = oracle.get("success_path", {})
    failure_path = oracle.get("failure_path", {})

    for sig in success_path.get("observable_signals", []):
        if sig.get("type") == "stdout_string" and sig.get("value"):
            success_signals.append(sig["value"])

    for sig in failure_path.get("observable_signals", []):
        if sig.get("type") == "stdout_string" and sig.get("value"):
            failure_signals.append(sig["value"])

    return success_signals, failure_signals


def classify_run(
    stdout: str,
    success_signals: list[str],
    failure_signals: list[str],
) -> dict[str, Any]:
    """Classify a single run's stdout against oracle signals."""
    cleaned = strip_ansi(stdout)
    result: dict[str, Any] = {
        "cleaned_stdout": cleaned,
        "success_matched": False,
        "failure_matched": False,
        "matched_success_signals": [],
        "matched_failure_signals": [],
        "classification": "UNKNOWN",
    }

    for sig in success_signals:
        if sig in cleaned:
            result["success_matched"] = True
            result["matched_success_signals"].append(sig)

    for sig in failure_signals:
        if sig in cleaned:
            result["failure_matched"] = True
            result["matched_failure_signals"].append(sig)

    if result["success_matched"] and not result["failure_matched"]:
        result["classification"] = "SUCCESS"
    elif result["failure_matched"] and not result["success_matched"]:
        result["classification"] = "FAILURE"
    elif result["success_matched"] and result["failure_matched"]:
        result["classification"] = "AMBIGUOUS_BOTH"
    else:
        result["classification"] = "NO_SIGNAL"

    return result


def classify_runtime_pair(
    oracle_path: Path,
    runtime_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Classify a runtime pair validation using oracle signals."""
    oracle = load_json(oracle_path)
    runtime = load_json(runtime_path)

    success_signals, failure_signals = extract_oracle_signals(oracle)

    candidate_run = runtime.get("candidate_run", {})
    control_run = runtime.get("negative_control_run", {})

    candidate_classification = classify_run(
        candidate_run.get("stdout_tail", ""),
        success_signals,
        failure_signals,
    )
    control_classification = classify_run(
        control_run.get("stdout_tail", ""),
        success_signals,
        failure_signals,
    )

    candidate_accepted = candidate_classification["classification"] == "SUCCESS"
    control_rejected = control_classification["classification"] == "FAILURE"

    if candidate_accepted and control_rejected:
        validation_status = "VALIDATED_SUCCESS"
        runtime_validated = True
        solved = True
        known_candidate = runtime.get("candidate_input", "")
        candidate = known_candidate
    elif candidate_classification["classification"] == "NO_SIGNAL" or control_classification["classification"] == "NO_SIGNAL":
        validation_status = "AMBIGUOUS_OUTPUT"
        runtime_validated = False
        solved = False
        known_candidate = ""
        candidate = None
    else:
        validation_status = "VALIDATED_FAILURE"
        runtime_validated = True
        solved = False
        known_candidate = ""
        candidate = None

    artifact: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": runtime.get("sample_id", ""),
        "mainline": "reverse_solving",
        "analysis_mode": "oracle_backed_runtime_validation",
        "source_artifacts": [
            Path(oracle_path).name.replace(".json", ""),
            Path(runtime_path).name.replace(".json", ""),
        ],
        "source_artifact_freshness": "current",
        "oracle_artifact": str(oracle_path),
        "runtime_artifact": str(runtime_path),
        "executed_sample": runtime.get("executed_sample", False),
        "runtime_validated": runtime_validated,
        "validation_status": validation_status,
        "candidate_input": runtime.get("candidate_input", ""),
        "negative_control_input": runtime.get("negative_control_input", ""),
        "backend": runtime.get("backend", ""),
        "max_runs": runtime.get("max_runs", 0),
        "candidate_run": {
            "input": candidate_run.get("input", ""),
            "executed": candidate_run.get("executed", False),
            "timed_out": candidate_run.get("timed_out", False),
            "return_code": candidate_run.get("return_code"),
            "raw_stdout_tail": candidate_run.get("stdout_tail", ""),
            "raw_stderr_tail": candidate_run.get("stderr_tail", ""),
            "cleaned_stdout": candidate_classification["cleaned_stdout"],
            "classification": candidate_classification["classification"],
            "matched_success_signals": candidate_classification["matched_success_signals"],
            "matched_failure_signals": candidate_classification["matched_failure_signals"],
        },
        "negative_control_run": {
            "input": control_run.get("input", ""),
            "executed": control_run.get("executed", False),
            "timed_out": control_run.get("timed_out", False),
            "return_code": control_run.get("return_code"),
            "raw_stdout_tail": control_run.get("stdout_tail", ""),
            "raw_stderr_tail": control_run.get("stderr_tail", ""),
            "cleaned_stdout": control_classification["cleaned_stdout"],
            "classification": control_classification["classification"],
            "matched_success_signals": control_classification["matched_success_signals"],
            "matched_failure_signals": control_classification["matched_failure_signals"],
        },
        "candidate_accepted": candidate_accepted,
        "control_rejected": control_rejected,
        "candidate": candidate,
        "known_candidate": known_candidate,
        "solved": solved,
        "blocked_reason": "" if validation_status == "VALIDATED_SUCCESS" else runtime.get("blocked_reason", ""),
        "target_sha256": runtime.get("target_sha256", ""),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    save_json(out_path, artifact)
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify runtime pair validation using oracle signals."
    )
    parser.add_argument("--oracle", required=True, help="Path to oracle artifact JSON")
    parser.add_argument("--runtime", required=True, help="Path to runtime artifact JSON")
    parser.add_argument("--out", required=True, help="Output path for classification artifact")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    artifact = classify_runtime_pair(
        oracle_path=Path(args.oracle),
        runtime_path=Path(args.runtime),
        out_path=Path(args.out),
    )

    print(
        f"oracle-backed classification: status={artifact['validation_status']} "
        f"candidate_accepted={artifact['candidate_accepted']} "
        f"control_rejected={artifact['control_rejected']} "
        f"solved={artifact['solved']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
