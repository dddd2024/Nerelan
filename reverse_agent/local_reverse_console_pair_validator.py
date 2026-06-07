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
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _is_winpty_available() -> bool:
    """Check if the winpty module (from pywinpty) is importable."""
    return importlib.util.find_spec("winpty") is not None


def _build_console_backend_capabilities() -> dict[str, dict[str, object]]:
    """Build console backend capabilities with dynamic winpty detection."""
    winpty_avail = _is_winpty_available()
    return {
        "subprocess": {
            "available": True,
            "validator_supported": True,
            "mature_interactive_console": False,
            "readiness_policy": "basic_subprocess_fallback",
            "reason": (
                "Existing pair validator uses subprocess for bounded candidate/control "
                "runs; it is not a mature interactive console backend for ambiguous "
                "Windows console flows."
            ),
        },
        "pywinauto": {
            "available": False,
            "validator_supported": False,
            "mature_interactive_console": False,
            "readiness_policy": "capability_only_until_adapter_exists",
            "reason": (
                "pywinauto dependency may exist, but no pywinauto-backed console "
                "validator is implemented."
            ),
        },
        "winpty": {
            "available": winpty_avail,
            "validator_supported": winpty_avail,
            "mature_interactive_console": winpty_avail,
            "readiness_policy": "mature_interactive_console_backend" if winpty_avail else "winpty_not_installed",
            "reason": (
                "winpty/pywinpty provides a mature pseudo-terminal backend for "
                "Windows console applications."
                if winpty_avail
                else "winpty module not found; install pywinpty to enable."
            ),
        },
    }


# Module-level cache, rebuilt on each call to get_console_backend_capabilities()
_CONSOLE_BACKEND_CAPABILITIES_CACHE: dict[str, dict[str, object]] | None = None


def get_console_backend_capabilities() -> dict[str, dict[str, object]]:
    """Return JSON-serializable console backend capabilities.

    The returned mapping is detached from the module-level registry so callers
    cannot accidentally mutate the source of truth.
    Winpty availability is checked dynamically via importlib.
    """
    global _CONSOLE_BACKEND_CAPABILITIES_CACHE  # noqa: PLW0603
    _CONSOLE_BACKEND_CAPABILITIES_CACHE = _build_console_backend_capabilities()
    return copy.deepcopy(_CONSOLE_BACKEND_CAPABILITIES_CACHE)


def is_console_backend_validator_supported(name: str) -> bool:
    """Return whether a named backend has validator support."""
    capabilities = get_console_backend_capabilities()
    entry = capabilities.get(name.strip().lower(), {})
    return bool(entry.get("validator_supported", False))


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


def _run_single_winpty(
    target_path: Path, input_text: str, timeout: float = 10.0
) -> dict[str, Any]:
    """Run target binary once using winpty pseudo-terminal backend.

    Uses the winpty library (from pywinpty) to spawn the target inside a
    pseudo-terminal and drive a bounded read/write lifecycle.

    Returns a run record with the same schema as _run_single().
    """
    run: dict[str, Any] = {
        "input": input_text,
        "executed": False,
        "timed_out": False,
        "return_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "backend": "winpty",
        "failure_stage": "",
    }

    try:
        import winpty
    except ImportError:
        run["stderr_tail"] = "winpty module not available"
        run["failure_stage"] = "import"
        return run

    pty = None
    try:
        pty = winpty.PTY(80, 24)
    except Exception as exc:
        run["stderr_tail"] = f"winpty PTY creation failed: {exc}"[:2000]
        run["failure_stage"] = "pty_create"
        return run

    if str(target_path).lower().endswith(".py"):
        appname = Path(sys.executable).name
        cmdline = subprocess.list2cmdline([str(target_path)])
    else:
        cmd = [str(target_path)]
        appname = str(target_path)
        cmdline = subprocess.list2cmdline(cmd)
    output_chunks: list[str] = []

    def _record_stderr(message: str) -> None:
        if run["stderr_tail"]:
            run["stderr_tail"] = f"{run['stderr_tail']}\n{message}"[-2000:]
        else:
            run["stderr_tail"] = message[-2000:]

    def _read_available(stage: str) -> None:
        try:
            chunk = pty.read(blocking=False)
        except Exception as exc:
            if not run["failure_stage"]:
                run["failure_stage"] = stage
            _record_stderr(f"winpty read failed: {exc}")
            raise
        if chunk:
            output_chunks.append(chunk)

    def _call_pty_method_bounded(method_name: str, stage: str, limit: float = 1.0) -> None:
        method = getattr(pty, method_name, None)
        if not method:
            return
        errors: list[BaseException] = []

        def _target() -> None:
            try:
                method()
            except BaseException as exc:  # pragma: no cover - surfaced below
                errors.append(exc)

        worker = threading.Thread(target=_target, daemon=True)
        worker.start()
        worker.join(timeout=limit)
        if worker.is_alive():
            if not run["failure_stage"]:
                run["failure_stage"] = stage
            _record_stderr(f"winpty {method_name} timed out during {stage}")
            return
        if errors:
            if not run["failure_stage"]:
                run["failure_stage"] = stage
            _record_stderr(f"winpty {method_name} failed: {errors[0]}")

    try:
        spawned = pty.spawn(appname, cmdline=cmdline, cwd=str(target_path.parent))
        if not spawned:
            run["failure_stage"] = "spawn"
            _record_stderr("winpty spawn returned false")
            return run
        run["executed"] = True

        deadline = time.monotonic() + max(timeout, 0.1)
        _read_available("read_before_input")

        stdin_payload = input_text + "\r\n\r\n"
        try:
            pty.write(stdin_payload)
        except Exception:
            run["failure_stage"] = "write"
            raise

        while True:
            _read_available("read_loop")
            if not pty.isalive():
                break
            if time.monotonic() >= deadline:
                run["timed_out"] = True
                run["failure_stage"] = "timeout"
                _call_pty_method_bounded("cancel_io", "timeout_cancel")
                break
            time.sleep(0.05)

        drain_deadline = time.monotonic() + 0.25
        while time.monotonic() < drain_deadline:
            try:
                _read_available("read_drain")
            except Exception:
                break
            if not pty.isalive():
                break
            time.sleep(0.05)

        if not run["timed_out"]:
            try:
                run["return_code"] = pty.get_exitstatus()
            except Exception as exc:
                run["failure_stage"] = run["failure_stage"] or "exitstatus"
                _record_stderr(f"winpty get_exitstatus failed: {exc}")

    except Exception as exc:
        if not run["failure_stage"]:
            run["failure_stage"] = "exception"
        _record_stderr(str(exc)[:2000])
    finally:
        if output_chunks:
            run["stdout_tail"] = "".join(output_chunks)[-2000:]
        _call_pty_method_bounded("close", "close")

    return run


def validate_console_pair(
    triage_path: Path,
    candidate_artifact_path: Path,
    candidate_field: str,
    timeout: float = 10.0,
    backend: str = "subprocess",
) -> dict[str, Any]:
    """
    Run paired console validation: candidate vs negative control.

    Parameters
    ----------
    triage_path: Path to the static triage JSON artifact.
    candidate_artifact_path: Path to the candidate artifact JSON.
    candidate_field: Field name in candidate artifact that holds the candidate string.
    timeout: Max seconds to wait for each process.
    backend: Console backend to use ("subprocess" or "winpty").

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
        "backend": backend,
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

    # Backend support check
    backend_normalized = backend.strip().lower()
    if not is_console_backend_validator_supported(backend_normalized):
        result["validation_status"] = "BLOCKED"
        result["blocked_reason"] = f"UNSUPPORTED_BACKEND:{backend_normalized}"
        return result

    # Select runner based on backend
    if backend_normalized == "winpty":
        runner = _run_single_winpty
    else:
        runner = _run_single

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
    candidate_run = runner(target_path, candidate, timeout)
    result["candidate_run"] = candidate_run

    # Run negative control
    control_run = runner(target_path, negative_control, timeout)
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
    parser.add_argument(
        "--backend",
        default="subprocess",
        choices=["subprocess", "winpty"],
        help="Console backend to use (default: subprocess).",
    )
    parser.add_argument("--out", required=True, help="Output JSON artifact path.")
    args = parser.parse_args(argv)

    result = validate_console_pair(
        triage_path=Path(args.triage),
        candidate_artifact_path=Path(args.candidate_artifact),
        candidate_field=args.candidate_field,
        timeout=args.timeout,
        backend=args.backend,
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
