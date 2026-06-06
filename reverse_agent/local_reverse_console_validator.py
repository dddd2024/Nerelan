"""
Console Runtime Validator for local reverse samples.

Validates a static candidate against a console PE sample by running it via
subprocess, feeding the candidate to stdin, and observing stdout/stderr for
success/failure/length tokens.

Does NOT execute target binary at import time.
Does NOT contain sample-specific hardcoded algorithms.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _resolve_target_path(relative_path: str) -> Path | None:
    """Resolve target binary from known local reverse roots."""
    roots: list[Path] = []
    for env in ("LOCAL_REVERSE_ROOT", "REVERSE_ROOT"):
        val = os.environ.get(env, "").strip()
        if val:
            roots.append(Path(val))
    for drive in ("E:", "D:", "C:", "F:"):
        roots.append(Path(f"{drive}\\reverse"))
    roots.append(Path.home() / "reverse")

    for root in roots:
        candidate = root / relative_path
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_console_candidate(
    triage_path: Path,
    candidate_artifact_path: Path,
    candidate_field: str,
    success_token: str,
    failure_token: str,
    length_token: str,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """
    Run a console candidate validation and return a runtime validation artifact.

    Parameters
    ----------
    triage_path: Path to the static triage JSON artifact.
    candidate_artifact_path: Path to the candidate artifact JSON.
    candidate_field: Field name in candidate artifact that holds the candidate string.
    success_token: Exact substring expected in stdout/stderr on success.
    failure_token: Exact substring expected in stdout/stderr on wrong candidate.
    length_token: Exact substring expected in stdout/stderr on wrong length.
    timeout: Max seconds to wait for process output.

    Returns
    -------
    dict conforming to the runtime validation artifact schema.
    """
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    candidate_artifact = json.loads(candidate_artifact_path.read_text(encoding="utf-8"))

    sample_id: str = str(triage.get("sample_id", ""))
    relative_path: str = str(triage.get("relative_path", ""))
    triage_sha256: str = str(triage.get("sha256", ""))

    candidate: str | None = candidate_artifact.get(candidate_field)
    if candidate is not None:
        candidate = str(candidate)

    target_path = _resolve_target_path(relative_path) if relative_path else None

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "console_runtime_validation",
        "mainline": "reverse_solving",
        "source_artifacts": [
            candidate_artifact_path.name.replace(".json", ""),
        ],
        "source_artifact_freshness": "current",
        "relative_path": relative_path,
        "candidate_source_field": candidate_field,
        "candidate": candidate,
        "known_candidate": "",
        "executed_sample": False,
        "runtime_validated": False,
        "validation_status": "not_validated",
        "success_token": success_token,
        "failure_token": failure_token,
        "length_token": length_token,
        "success_observed": False,
        "failure_observed": False,
        "length_error_observed": False,
        "return_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "solved": False,
        "blocked_reason": "",
        "target_sha256": triage_sha256,
        "target_resolved_path": str(target_path) if target_path else None,
        "generated_at": _now_iso(),
    }

    if not candidate:
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "CANDIDATE_MISSING"
        return result

    if not target_path:
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "TARGET_MISSING"
        return result

    if not target_path.exists():
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "TARGET_MISSING"
        return result

    # Verify target SHA256 if available and non-empty
    if triage_sha256 and triage_sha256.strip():
        actual_sha = _sha256_file(target_path)
        if actual_sha.lower() != triage_sha256.lower():
            result["validation_status"] = "BLOCKED"
            result["blocked_reason"] = "TARGET_MISMATCH"
            result["target_actual_sha256"] = actual_sha
            return result

    # Build command: if target is a .py script, run via sys.executable;
    # otherwise run the binary directly (PE/console executable).
    if str(target_path).lower().endswith(".py"):
        cmd = [sys.executable, str(target_path)]
    else:
        cmd = [str(target_path)]

    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "UNSUPPORTED_RUNTIME"
        result["stderr_tail"] = str(exc)[:2000]
        return result

    stdout_text = ""
    stderr_text = ""
    return_code: int | None = None

    try:
        # Feed candidate + newline + newline to cover system("pause")
        stdin_payload = candidate + "\n\n"
        stdout_bytes, stderr_bytes = proc.communicate(
            input=stdin_payload, timeout=timeout
        )
        stdout_text = stdout_bytes or ""
        stderr_text = stderr_bytes or ""
        return_code = proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
        # stdout/stderr pipes are closed after communicate/timeout; use empty strings
        stdout_text = ""
        stderr_text = ""
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "TIMEOUT"
        result["stdout_tail"] = ""
        result["stderr_tail"] = ""
        result["return_code"] = proc.returncode
        return result
    except Exception as exc:
        if proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "DEPENDENCY_ERROR"
        result["stderr_tail"] = str(exc)[:2000]
        result["return_code"] = proc.returncode
        return result

    combined = stdout_text + stderr_text
    success_observed = success_token in combined
    failure_observed = failure_token in combined
    length_error_observed = length_token in combined

    result["executed_sample"] = True
    result["return_code"] = return_code
    result["stdout_tail"] = stdout_text[-2000:]
    result["stderr_tail"] = stderr_text[-2000:]
    result["success_observed"] = success_observed
    result["failure_observed"] = failure_observed
    result["length_error_observed"] = length_error_observed

    if success_observed and not failure_observed and not length_error_observed:
        result["validation_status"] = "VALIDATED_SUCCESS"
        result["runtime_validated"] = True
        result["known_candidate"] = candidate
        result["solved"] = True
    elif failure_observed or length_error_observed:
        result["validation_status"] = "VALIDATED_FAILURE"
        result["runtime_validated"] = True
        result["known_candidate"] = ""
        result["solved"] = False
    else:
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "AMBIGUOUS_OUTPUT"
        result["runtime_validated"] = False
        result["solved"] = False

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Console runtime validator for local reverse samples."
    )
    parser.add_argument("--triage", required=True, help="Path to static triage JSON.")
    parser.add_argument(
        "--candidate-artifact", required=True, help="Path to candidate artifact JSON."
    )
    parser.add_argument(
        "--candidate-field", default="static_candidate_text", help="Candidate field name."
    )
    parser.add_argument("--success-token", required=True, help="Success token substring.")
    parser.add_argument("--failure-token", required=True, help="Failure token substring.")
    parser.add_argument("--length-token", required=True, help="Length error token substring.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Subprocess timeout in seconds.")
    parser.add_argument("--out", required=True, help="Output JSON artifact path.")
    args = parser.parse_args(argv)

    result = validate_console_candidate(
        triage_path=Path(args.triage),
        candidate_artifact_path=Path(args.candidate_artifact),
        candidate_field=args.candidate_field,
        success_token=args.success_token,
        failure_token=args.failure_token,
        length_token=args.length_token,
        timeout=args.timeout,
    )

    out_path = Path(args.out)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Runtime validation artifact written to {out_path}")
    status = result["validation_status"]
    solved = result["solved"]
    print(f"Status: {status}, solved={solved}")
    return 0 if status in ("VALIDATED_SUCCESS", "VALIDATED_FAILURE") else 1


if __name__ == "__main__":
    sys.exit(main())
