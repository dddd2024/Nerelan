"""Bounded runtime boundary probe for cpp1_2f6fcb63.

Runs a small, fixed set of raw-stdin probes against the local trusted
sample to determine whether the runtime path agrees with or contradicts
the static success-boundary model.

Does NOT perform blind search, brute force, SMT, or candidate-pool
exploration.  Does NOT mark solved without strict success evidence.
Does NOT modify the binary, upload it, or allow network access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUCCESS_MARKERS = [
    "congratulations",
    "you are right",
    "correct",
    "success!",
]

FAILURE_MARKERS = [
    "wrong",
    "fail",
    "invalid",
    "incorrect",
    "error",
]

LOCAL_ROOT = Path(r"E:\reverse")

SAMPLE_ID = "cpp1_2f6fcb63"
SAMPLE_RELPATH = "逆向课程2023春01/CPP1.exe"
SAMPLE_SHA256 = "2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede"

# Probes: (name, stdin_hex)
# Note: CPP1.exe uses system("pause") which reads from console buffer via getch(),
# not from stdin. When stdin is piped, system("pause") loops printing
# "Press any key to continue". We still send the payload via stdin for scanf
# and append extra \r characters to try to satisfy any console reads.
PROBES = [
    ("baseline_18_A", "4141414141414141414141414141414141410d0a" + "0d" * 20),
    ("raw_inverse_AA", "5d5a1cde131557d7d69dde2417df245341410d0a" + "0d" * 20),
    ("raw_inverse_BB", "5d5a1cde131557d7d69dde2417df245342420d0a" + "0d" * 20),
]

PREVIEW_LIMIT = 16384


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _check_success_marker(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in SUCCESS_MARKERS)


def _check_failure_marker(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in FAILURE_MARKERS)


def _resolve_sample_path(inventory_path: Path | None) -> Path:
    """Resolve the sample path from inventory or default root."""
    if inventory_path is not None and inventory_path.exists():
        inventory = _load_json(inventory_path)
        for entry in inventory.get("entries", []):
            if entry.get("sample_id") == SAMPLE_ID:
                root = Path(inventory.get("source_root_label", str(LOCAL_ROOT)))
                if not root.exists():
                    root = LOCAL_ROOT
                return (root / entry["relative_path"]).resolve()
    return (LOCAL_ROOT / SAMPLE_RELPATH).resolve()


def _run_probe(
    *,
    sample_path: Path,
    probe_name: str,
    stdin_bytes: bytes,
    timeout: int,
) -> dict[str, Any]:
    """Run a single bounded probe against the sample."""
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [str(sample_path)],
            input=stdin_bytes,
            capture_output=True,
            timeout=timeout,
            cwd=str(sample_path.parent),
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout_text = completed.stdout.decode("utf-8", errors="replace")
        stderr_text = completed.stderr.decode("utf-8", errors="replace")

        success_seen = _check_success_marker(stdout_text + stderr_text)
        failure_seen = _check_failure_marker(stdout_text + stderr_text)

        return {
            "probe_name": probe_name,
            "stdin_hex": stdin_bytes.hex(),
            "timeout": False,
            "exit_code": completed.returncode,
            "stdout_preview": stdout_text[:PREVIEW_LIMIT],
            "stderr_preview": stderr_text[:PREVIEW_LIMIT],
            "duration_ms": duration_ms,
            "success_marker_seen": success_seen,
            "failure_marker_seen": failure_seen,
        }
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout_text = (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr_text = (exc.stderr or b"").decode("utf-8", errors="replace")
        success_seen = _check_success_marker(stdout_text + stderr_text)
        failure_seen = _check_failure_marker(stdout_text + stderr_text)

        return {
            "probe_name": probe_name,
            "stdin_hex": stdin_bytes.hex(),
            "timeout": True,
            "exit_code": None,
            "stdout_preview": stdout_text[:PREVIEW_LIMIT],
            "stderr_preview": stderr_text[:PREVIEW_LIMIT],
            "duration_ms": duration_ms,
            "success_marker_seen": success_seen,
            "failure_marker_seen": failure_seen,
        }
    except OSError as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        return {
            "probe_name": probe_name,
            "stdin_hex": stdin_bytes.hex(),
            "timeout": False,
            "exit_code": None,
            "stdout_preview": "",
            "stderr_preview": str(exc)[:PREVIEW_LIMIT],
            "duration_ms": duration_ms,
            "success_marker_seen": False,
            "failure_marker_seen": False,
        }


def run_boundary_probe(
    *,
    target_revalidation_path: Path,
    success_boundary_path: Path,
    inventory_path: Path | None,
    artifact_index_path: Path | None,
    out_path: Path,
    timeout_seconds: int = 5,
    decision_id: str = "",
    round_id: str = "",
) -> dict[str, Any]:
    """Main logic: run bounded probes and produce diagnostic artifact."""

    target_revalidation = _load_json(target_revalidation_path)
    success_boundary = _load_json(success_boundary_path)

    revalidation_status = target_revalidation.get("revalidation_status", "")
    if revalidation_status != "PASSED":
        result = _blocked_result(
            decision_id=decision_id,
            round_id=round_id,
            reason=f"TARGET_REVALIDATION_NOT_PASSED: {revalidation_status}",
        )
        _save_json(out_path, result)
        return result

    sample_path = _resolve_sample_path(inventory_path)

    if not sample_path.exists():
        result = _blocked_result(
            decision_id=decision_id,
            round_id=round_id,
            reason=f"SAMPLE_MISSING: {sample_path}",
        )
        _save_json(out_path, result)
        return result

    actual_sha = _sha256_file(sample_path)
    if actual_sha != SAMPLE_SHA256:
        result = _blocked_result(
            decision_id=decision_id,
            round_id=round_id,
            reason=f"SHA256_MISMATCH: expected={SAMPLE_SHA256} actual={actual_sha}",
        )
        _save_json(out_path, result)
        return result

    # Run probes
    probe_results = []
    for probe_name, stdin_hex in PROBES:
        stdin_bytes = bytes.fromhex(stdin_hex)
        result = _run_probe(
            sample_path=sample_path,
            probe_name=probe_name,
            stdin_bytes=stdin_bytes,
            timeout=timeout_seconds,
        )
        probe_results.append(result)

    # Determine verdict
    baseline = probe_results[0]
    candidate_probes = probe_results[1:]

    baseline_success = baseline["success_marker_seen"]

    candidate_success = False
    candidate_probe_name = None
    candidate_bytes_hex = None
    candidate_text = None
    static_boundary_contradicted = False

    for probe in candidate_probes:
        if probe["success_marker_seen"] and not baseline_success:
            candidate_success = True
            candidate_probe_name = probe["probe_name"]
            stdin_hex = probe["stdin_hex"]
            raw_bytes = bytes.fromhex(stdin_hex)
            candidate_bytes_hex = raw_bytes[:16].hex()
            if all(0x20 <= b <= 0x7E for b in raw_bytes[:16]):
                candidate_text = "".join(chr(b) for b in raw_bytes[:16])
            else:
                candidate_text = None
            static_boundary_contradicted = True
            break

    all_timeout = all(p["timeout"] for p in probe_results)
    any_io_error = any(
        p["exit_code"] is None and not p["timeout"] for p in probe_results
    )

    if candidate_success:
        verdict = "RUNTIME_CONTRADICTS_STATIC_NEEDS_TOOL_RECHECK"
        recommended_next_action = (
            "Runtime success observed with nonprintable inverse preimage, "
            "contradicting the static boundary model that predicted Destination[16] == 0x00 "
            "would prevent success. A separate tool/xref recheck round is needed "
            "to understand the control flow before marking solved."
        )
    elif baseline_success:
        verdict = "INCONCLUSIVE_TIMEOUT_OR_IO"
        recommended_next_action = (
            "Baseline probe also shows success marker; "
            "cannot distinguish candidate from baseline. "
            "Review binary success/failure output semantics."
        )
    elif all_timeout and not any(p["success_marker_seen"] for p in probe_results):
        press_any_key_seen = any(
            "press any key" in p.get("stdout_preview", "").lower()
            for p in probe_results
        )
        if press_any_key_seen:
            verdict = "INCONCLUSIVE_TIMEOUT_OR_IO"
            recommended_next_action = (
                "All probes timed out with 'Press any key to continue' loop. "
                "CPP1.exe uses system('pause') which reads from console buffer, "
                "not stdin. The comparison logic likely executed but output was "
                "overwritten by the pause loop. "
                "Recommend using a console automation tool (e.g., agent-browser, "
                "pexpect+wine, or x64dbg script) to interact with the program, "
                "or patch out the system('pause') calls for testing."
            )
        else:
            verdict = "INCONCLUSIVE_TIMEOUT_OR_IO"
            recommended_next_action = (
                "Runtime probes timed out or could not capture I/O. "
                "Check sample behavior manually or with a debugger before retrying."
            )
    elif any_io_error:
        verdict = "INCONCLUSIVE_TIMEOUT_OR_IO"
        recommended_next_action = (
            "Runtime probes encountered I/O errors. "
            "Check sample behavior manually or with a debugger before retrying."
        )
    else:
        verdict = "STATIC_BOUNDARY_CONFIRMED_NO_SUCCESS"
        recommended_next_action = (
            "No runtime probe succeeded; static boundary model confirmed. "
            "Recommend a separate static/tool recheck of control flow, "
            "SEH/division-by-zero path, or target boundary semantics "
            "before attempting another runtime round."
        )

    source_artifacts = {
        "target_revalidation": str(target_revalidation_path).replace("\\", "/"),
        "success_boundary_static_recheck": str(success_boundary_path).replace("\\", "/"),
    }
    source_freshness = {}
    if artifact_index_path and artifact_index_path.exists():
        artifact_index = _load_json(artifact_index_path)
        for key in artifact_index.get("latest_artifacts_v2", {}):
            if "target_bytes_revalidation" in key:
                entry = artifact_index["latest_artifacts_v2"][key]
                source_freshness["target_revalidation"] = {
                    "artifact_key": key,
                    "path": entry.get("path", ""),
                    "freshness": entry.get("freshness", ""),
                }
            if "success_boundary" in key:
                entry = artifact_index["latest_artifacts_v2"][key]
                source_freshness["success_boundary_static_recheck"] = {
                    "artifact_key": key,
                    "path": entry.get("path", ""),
                    "freshness": entry.get("freshness", ""),
                }

    executed_sample = any(not p["timeout"] and p["exit_code"] is not None for p in probe_results)

    result: dict[str, Any] = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "sample_id": SAMPLE_ID,
        "relative_path": SAMPLE_RELPATH,
        "sha256": SAMPLE_SHA256,
        "analysis_mode": "bounded_runtime_boundary_probe",
        "mainline": "reverse_solving",
        "executed_sample": executed_sample,
        "runtime_validated": candidate_success,
        "runtime_allowed_reason": "user_asserted_local_samples_pretested_no_virus",
        "runtime_policy": {
            "local_root": str(LOCAL_ROOT),
            "network_allowed": False,
            "max_executions": len(PROBES),
            "timeout_seconds": timeout_seconds,
            "sha256_check": True,
            "path_scope": "indexed_files_under_root_only",
        },
        "source_artifacts": source_artifacts,
        "source_artifact_freshness": source_freshness,
        "probes": probe_results,
        "baseline_probe_name": "baseline_18_A",
        "candidate_probe_name": candidate_probe_name,
        "candidate_bytes_hex": candidate_bytes_hex,
        "candidate_text": candidate_text,
        "static_boundary_contradicted": static_boundary_contradicted,
        "verdict": verdict,
        "recommended_next_action": recommended_next_action,
        "generated_at": _now_iso(),
    }

    _save_json(out_path, result)

    print(f"cpp1 runtime boundary probe: verdict={verdict}")
    print(f"  executed_sample={executed_sample}")
    print(f"  runtime_validated={candidate_success}")
    print(f"  static_boundary_contradicted={static_boundary_contradicted}")
    if candidate_bytes_hex:
        print(f"  candidate_bytes_hex={candidate_bytes_hex}")
    for p in probe_results:
        print(f"  probe={p['probe_name']} exit={p['exit_code']} timeout={p['timeout']} "
              f"success={p['success_marker_seen']} failure={p['failure_marker_seen']} "
              f"duration_ms={p['duration_ms']}")

    return result


def _blocked_result(
    *, decision_id: str, round_id: str, reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "sample_id": SAMPLE_ID,
        "relative_path": SAMPLE_RELPATH,
        "sha256": SAMPLE_SHA256,
        "analysis_mode": "bounded_runtime_boundary_probe",
        "mainline": "reverse_solving",
        "executed_sample": False,
        "runtime_validated": False,
        "runtime_allowed_reason": "user_asserted_local_samples_pretested_no_virus",
        "runtime_policy": {
            "local_root": str(LOCAL_ROOT),
            "network_allowed": False,
            "max_executions": 0,
            "timeout_seconds": 5,
            "sha256_check": True,
            "path_scope": "indexed_files_under_root_only",
        },
        "source_artifacts": {},
        "source_artifact_freshness": {},
        "probes": [],
        "baseline_probe_name": "baseline_18_A",
        "candidate_probe_name": None,
        "candidate_bytes_hex": None,
        "candidate_text": None,
        "static_boundary_contradicted": False,
        "verdict": "BLOCKED_RUNTIME_UNAVAILABLE",
        "recommended_next_action": f"Blocked: {reason}. Resolve before retrying runtime probe.",
        "generated_at": _now_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bounded runtime boundary probe for cpp1_2f6fcb63.",
    )
    parser.add_argument(
        "--target-revalidation",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json"),
    )
    parser.add_argument(
        "--success-boundary",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json"),
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("project_state/local_reverse_inventory.json"),
    )
    parser.add_argument(
        "--artifact-index",
        type=Path,
        default=Path("project_state/artifact_index.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json"),
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--decision-id",
        type=str,
        default="",
    )
    parser.add_argument(
        "--round-id",
        type=str,
        default="",
    )
    args = parser.parse_args()

    try:
        result = run_boundary_probe(
            target_revalidation_path=args.target_revalidation,
            success_boundary_path=args.success_boundary,
            inventory_path=args.inventory,
            artifact_index_path=args.artifact_index,
            out_path=args.out,
            timeout_seconds=args.timeout_seconds,
            decision_id=args.decision_id,
            round_id=args.round_id,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    verdict = result.get("verdict", "")
    if verdict == "BLOCKED_RUNTIME_UNAVAILABLE":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
