"""
Console Pair Runtime Validator for local reverse samples.

Runs a static candidate and a same-length negative control against a console
PE sample, compares stdout/stderr/return_code, and conservatively determines
validation status.

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


def _generate_negative_control(candidate: str) -> str:
    """Generate a same-length negative control by mutating the first printable char."""
    if not candidate:
        return ""
    chars = list(candidate)
    for i, ch in enumerate(chars):
        if ch.isprintable() and ch != " ":
            # Shift first printable char by 1 (e.g., 'i' -> 'j')
            new_ord = ord(ch) + 1
            if new_ord > 126:
                new_ord = 33  # wrap to '!'
            chars[i] = chr(new_ord)
            return "".join(chars)
    # Fallback: change first char to 'x'
    chars[0] = "x"
    return "".join(chars)


def _run_single(
    target_path: Path, input_text: str, timeout: float = 10.0
) -> dict[str, Any]:
    """Run target binary once with given input, return run record."""
    run: dict[str, Any] = {
        "input": input_text,
        "executed": False,
        "timed_out": False,
        "return_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }

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
        run["stderr_tail"] = str(exc)[:2000]
        return run

    try:
        stdin_payload = input_text + "\n\n"
        stdout_bytes, stderr_bytes = proc.communicate(
            input=stdin_payload, timeout=timeout
        )
        run["executed"] = True
        run["return_code"] = proc.returncode
        run["stdout_tail"] = (stdout_bytes or "")[-2000:]
        run["stderr_tail"] = (stderr_bytes or "")[-2000:]
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
        run["timed_out"] = True
        run["executed"] = True
        run["return_code"] = proc.returncode
    except Exception as exc:
        if proc and proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
        run["stderr_tail"] = str(exc)[:2000]

    return run


def validate_console_pair(
    triage_path: Path,
    candidate_artifact_path: Path,
    candidate_field: str,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """
    Run paired console validation: candidate vs negative control.

    Parameters
    ----------
    triage_path: Path to the static triage JSON artifact.
    candidate_artifact_path: Path to the candidate artifact JSON.
    candidate_field: Field name in candidate artifact that holds the candidate string.
    timeout: Max seconds to wait for each process.

    Returns
    -------
    dict conforming to the runtime pair validation artifact schema.
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

    negative_control = _generate_negative_control(candidate) if candidate else ""

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "console_runtime_pair_validation",
        "mainline": "reverse_solving",
        "source_artifacts": [
            candidate_artifact_path.name.replace(".json", ""),
            triage_path.name.replace(".json", ""),
        ],
        "source_artifact_freshness": "current",
        "source_candidate_artifact": str(candidate_artifact_path),
        "source_triage_artifact": str(triage_path),
        "relative_path": relative_path,
        "sha256": triage_sha256,
        "candidate_source_field": candidate_field,
        "candidate_input": candidate,
        "negative_control_input": negative_control,
        "negative_control_strategy": "single_char_mutation",
        "max_runs": 2,
        "executed_sample": False,
        "runtime_validated": False,
        "validation_status": "not_validated",
        "candidate_run": {
            "input": candidate,
            "executed": False,
            "timed_out": False,
            "return_code": None,
            "stdout_tail": "",
            "stderr_tail": "",
        },
        "negative_control_run": {
            "input": negative_control,
            "executed": False,
            "timed_out": False,
            "return_code": None,
            "stdout_tail": "",
            "stderr_tail": "",
        },
        "outputs_differ": False,
        "success_reason": "",
        "failure_reason": "",
        "candidate": None,
        "known_candidate": "",
        "solved": False,
        "blocked_reason": "",
        "target_sha256": triage_sha256,
        "target_resolved_path": str(target_path) if target_path else None,
        "generated_at": _now_iso(),
    }

    # Pre-flight checks
    if not candidate:
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "CANDIDATE_MISSING"
        return result

    if not negative_control or negative_control == candidate:
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

    if triage_sha256 and triage_sha256.strip():
        actual_sha = _sha256_file(target_path)
        if actual_sha.lower() != triage_sha256.lower():
            result["validation_status"] = "BLOCKED"
            result["blocked_reason"] = "TARGET_MISMATCH"
            result["target_actual_sha256"] = actual_sha
            return result

    # Run candidate
    candidate_run = _run_single(target_path, candidate, timeout)
    result["candidate_run"] = candidate_run

    # Run negative control
    control_run = _run_single(target_path, negative_control, timeout)
    result["negative_control_run"] = control_run

    result["executed_sample"] = candidate_run["executed"] or control_run["executed"]

    # Check for timeout/blocking conditions
    if candidate_run["timed_out"] or control_run["timed_out"]:
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "TIMEOUT"
        result["failure_reason"] = "One or both runs timed out."
        return result

    if not candidate_run["executed"] or not control_run["executed"]:
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = "UNSUPPORTED_RUNTIME"
        result["failure_reason"] = "One or both runs failed to execute."
        return result

    # Compare outputs
    stdout_diff = candidate_run["stdout_tail"] != control_run["stdout_tail"]
    stderr_diff = candidate_run["stderr_tail"] != control_run["stderr_tail"]
    rc_diff = candidate_run["return_code"] != control_run["return_code"]
    outputs_differ = stdout_diff or stderr_diff or rc_diff
    result["outputs_differ"] = outputs_differ

    if not outputs_differ:
        # No observable difference - conservative: AMBIGUOUS_OUTPUT
        result["validation_status"] = "AMBIGUOUS_OUTPUT"
        result["blocked_reason"] = "AMBIGUOUS_OUTPUT"
        result["runtime_validated"] = False
        result["candidate"] = None
        result["known_candidate"] = ""
        result["solved"] = False
        result["candidate_accepted"] = False
        result["control_rejected"] = False
        result["failure_reason"] = (
            "Candidate and negative control produced identical stdout, stderr, "
            "and return code. Cannot conservatively determine acceptance/rejection."
        )
        return result

    # Outputs differ - try to determine if candidate was accepted and control rejected
    # Heuristic: if candidate has a different (presumably better) outcome than control
    candidate_accepted = False
    control_rejected = False

    # If return codes differ, candidate having 0 is a positive signal
    if rc_diff:
        if candidate_run["return_code"] == 0 and control_run["return_code"] != 0:
            candidate_accepted = True
            control_rejected = True
        elif candidate_run["return_code"] != 0 and control_run["return_code"] == 0:
            # Control succeeded but candidate didn't - candidate is wrong
            result["validation_status"] = "VALIDATED_FAILURE"
            result["runtime_validated"] = True
            result["candidate"] = None
            result["known_candidate"] = ""
            result["solved"] = False
            result["candidate_accepted"] = False
            result["control_rejected"] = False
            result["failure_reason"] = (
                f"Negative control return_code={control_run['return_code']} but "
                f"candidate return_code={candidate_run['return_code']}. "
                "Candidate appears to be rejected."
            )
            return result

    # If stdout differs, check for success/failure indicators
    if stdout_diff and not candidate_accepted:
        # Simple heuristic: if candidate stdout is longer or contains different content
        # but we can't determine semantic meaning, stay conservative
        pass

    if candidate_accepted and control_rejected:
        result["validation_status"] = "VALIDATED_SUCCESS"
        result["runtime_validated"] = True
        result["candidate"] = candidate
        result["known_candidate"] = candidate
        result["solved"] = True
        result["candidate_accepted"] = True
        result["control_rejected"] = True
        result["success_reason"] = (
            f"Candidate return_code={candidate_run['return_code']}, "
            f"control return_code={control_run['return_code']}. "
            f"stdout differ={stdout_diff}, stderr differ={stderr_diff}."
        )
    else:
        # Outputs differ but we can't clearly determine acceptance/rejection
        result["validation_status"] = "AMBIGUOUS_OUTPUT"
        result["blocked_reason"] = "AMBIGUOUS_OUTPUT"
        result["runtime_validated"] = False
        result["candidate"] = None
        result["known_candidate"] = ""
        result["solved"] = False
        result["candidate_accepted"] = False
        result["control_rejected"] = False
        result["failure_reason"] = (
            "Outputs differ but cannot conservatively determine "
            "candidate acceptance vs control rejection."
        )

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Console pair runtime validator for local reverse samples."
    )
    parser.add_argument("--triage", required=True, help="Path to static triage JSON.")
    parser.add_argument(
        "--candidate-artifact", required=True, help="Path to candidate artifact JSON."
    )
    parser.add_argument(
        "--candidate-field", default="static_candidate_text", help="Candidate field name."
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Subprocess timeout in seconds.")
    parser.add_argument("--out", required=True, help="Output JSON artifact path.")
    args = parser.parse_args(argv)

    result = validate_console_pair(
        triage_path=Path(args.triage),
        candidate_artifact_path=Path(args.candidate_artifact),
        candidate_field=args.candidate_field,
        timeout=args.timeout,
    )

    out_path = Path(args.out)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Runtime pair validation artifact written to {out_path}")
    status = result["validation_status"]
    solved = result["solved"]
    print(f"Status: {status}, solved={solved}")
    return 0 if status in ("VALIDATED_SUCCESS", "VALIDATED_FAILURE") else 1


if __name__ == "__main__":
    sys.exit(main())
