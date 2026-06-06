"""
Console Mature Backend Availability Probe for local reverse samples.

Detects whether the current environment has mature console interaction backends
available (pywinpty, winpty, wexpect, pexpect, Windows ConPTY API) without
importing or executing them. Does NOT run target binaries.

Does NOT execute target binary at import time.
Does NOT contain sample-specific hardcoded algorithms.
"""
from __future__ import annotations

import argparse
import ctypes
import importlib.util
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_python_backend_availability() -> dict[str, bool]:
    """Detect which mature Python console interaction packages are installed.

    Uses importlib.util.find_spec to check availability without importing.
    """
    return {
        "pywinpty_available": importlib.util.find_spec("pywinpty") is not None,
        "winpty_available": importlib.util.find_spec("winpty") is not None,
        "wexpect_available": importlib.util.find_spec("wexpect") is not None,
        "pexpect_available": importlib.util.find_spec("pexpect") is not None,
    }


def detect_windows_conpty_api_presence() -> dict[str, Any]:
    """Check whether Windows ConPTY API functions exist in kernel32.

    Only checks function name presence via ctypes.windll.kernel32.GetProcAddress.
    Does NOT create a pseudo console or start any process.
    """
    result: dict[str, Any] = {
        "conpty_api_available": False,
        "conpty_api_checked": False,
    }

    if sys.platform != "win32":
        result["conpty_api_checked"] = True
        return result

    try:
        kernel32 = ctypes.windll.kernel32
        for func_name in ("CreatePseudoConsole", "ClosePseudoConsole", "ResizePseudoConsole"):
            func_ptr = ctypes.windll.kernel32.GetProcAddress(
                kernel32._handle, ctypes.c_char_p(func_name.encode("ascii"))
            )
            if func_ptr is None:
                result["conpty_api_checked"] = True
                return result
        result["conpty_api_available"] = True
        result["conpty_api_checked"] = True
    except (AttributeError, OSError, ctypes.ArgumentError):
        result["conpty_api_checked"] = True

    return result


def detect_platform_info() -> dict[str, str | bool]:
    """Detect current platform information."""
    return {
        "windows_platform": sys.platform == "win32",
        "platform_system": platform.system(),
        "sys_platform": sys.platform,
        "os_name": os.name,
    }


def build_probe_artifact(
    runtime_artifact_path: Path,
    handoff_artifact_path: Path,
    triage_artifact_path: Path,
) -> dict[str, Any]:
    """Build the mature backend availability probe artifact."""
    # Load source artifacts
    runtime = json.loads(runtime_artifact_path.read_text(encoding="utf-8"))
    handoff = json.loads(handoff_artifact_path.read_text(encoding="utf-8"))
    triage = json.loads(triage_artifact_path.read_text(encoding="utf-8"))

    sample_id: str = str(runtime.get("sample_id", ""))
    candidate_input: str = str(runtime.get("candidate_input", ""))

    # Detect backends
    pkg_availability = detect_python_backend_availability()
    conpty_info = detect_windows_conpty_api_presence()
    platform_info = detect_platform_info()

    # Determine if any mature Windows-capable backend is available
    has_windows_backend = (
        pkg_availability["pywinpty_available"]
        or pkg_availability["winpty_available"]
        or pkg_availability["wexpect_available"]
        or conpty_info["conpty_api_available"]
    )

    # Determine probe status
    probe_status = "BLOCKED_SOURCE_ARTIFACT_MISMATCH"
    blocked_reason = ""
    recommended_backend = ""
    recommended_next_action = ""

    # Check source artifacts consistency
    if runtime.get("validation_status") != "AMBIGUOUS_OUTPUT":
        blocked_reason = f"runtime validation status is {runtime.get('validation_status')}, expected AMBIGUOUS_OUTPUT"
    elif runtime.get("solved") is not False:
        blocked_reason = "runtime artifact already solved"
    elif str(runtime.get("known_candidate", "")) != "":
        blocked_reason = "runtime artifact has known_candidate set"
    elif handoff.get("status") != "READY_FOR_RUNTIME_VALIDATION":
        blocked_reason = f"handoff status is {handoff.get('status')}, expected READY_FOR_RUNTIME_VALIDATION"
    elif triage.get("status") != "STATIC_TRIAGE_COMPLETE":
        blocked_reason = f"triage status is {triage.get('status')}, expected STATIC_TRIAGE_COMPLETE"
    elif not platform_info["windows_platform"]:
        probe_status = "BLOCKED_NON_WINDOWS_ENVIRONMENT"
        blocked_reason = "Not a Windows environment; PE interactive console validation not applicable"
    elif not has_windows_backend:
        probe_status = "BLOCKED_MATURE_BACKEND_MISSING"
        blocked_reason = "Windows platform but no mature backend available (pywinpty/winpty/wexpect/ConPTY API)"
    else:
        probe_status = "READY_FOR_MATURE_BACKEND_VALIDATION"
        # Determine preferred backend
        if pkg_availability["pywinpty_available"]:
            recommended_backend = "pywinpty"
            recommended_next_action = (
                "Use pywinpty for interactive-console validation. "
                "Design at most 2-run candidate/control validation for ippio vs negative control."
            )
        elif pkg_availability["winpty_available"]:
            recommended_backend = "winpty"
            recommended_next_action = (
                "Use winpty for interactive-console validation. "
                "Design at most 2-run candidate/control validation for ippio vs negative control."
            )
        elif pkg_availability["wexpect_available"]:
            recommended_backend = "wexpect"
            recommended_next_action = (
                "Use wexpect for interactive-console validation. "
                "Design at most 2-run candidate/control validation for ippio vs negative control."
            )
        elif conpty_info["conpty_api_available"]:
            recommended_backend = "windows_conpty_api"
            recommended_next_action = (
                "Windows ConPTY API is available. A thin ctypes wrapper (not a full runner) "
                "could be used for interactive-console validation. "
                "Design at most 2-run candidate/control validation for ippio vs negative control."
            )

    return {
        "schema_version": 1,
        "sample_id": sample_id,
        "analysis_mode": "console_mature_backend_availability_probe",
        "mainline": "tool_integration",
        "source_artifacts": [
            "local_reverse_cpp2_2f64e68d_runtime_pair_validation",
            "local_reverse_cpp2_2f64e68d_strcmp_handoff",
            "local_reverse_cpp2_2f64e68d_static_triage",
        ],
        "source_artifact_freshness": "current",
        "runtime_pair_validation_artifact": str(runtime_artifact_path),
        "strcmp_handoff_artifact": str(handoff_artifact_path),
        "static_triage_artifact": str(triage_artifact_path),
        "candidate_input": candidate_input,
        "previous_validation_status": str(runtime.get("validation_status", "")),
        "previous_outputs_differ": bool(runtime.get("outputs_differ", False)),
        "previous_runtime_validated": bool(runtime.get("runtime_validated", False)),
        "previous_known_candidate": str(runtime.get("known_candidate", "")),
        "previous_solved": bool(runtime.get("solved", False)),
        "mature_backend_priority": True,
        "preferred_backend_order": [
            "pywinpty_or_winpty",
            "wexpect",
            "windows_conpty_api_presence",
            "pexpect_posix_reference_only",
        ],
        **pkg_availability,
        **platform_info,
        **conpty_info,
        "no_custom_conpty_runner": True,
        "no_expect_state_machine": True,
        "no_terminal_emulator": True,
        "can_attempt_interactive_console_validation_next": probe_status == "READY_FOR_MATURE_BACKEND_VALIDATION",
        "probe_status": probe_status,
        "recommended_backend": recommended_backend,
        "recommended_next_action": recommended_next_action,
        "executed_target": False,
        "runtime_validated": False,
        "candidate": None,
        "known_candidate": "",
        "solved": False,
        "blocked_reason": blocked_reason,
        "generated_at": _now_iso(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Console mature backend availability probe for local reverse samples."
    )
    parser.add_argument(
        "--runtime-artifact", required=True, help="Path to runtime pair validation JSON."
    )
    parser.add_argument(
        "--handoff-artifact", required=True, help="Path to strcmp handoff JSON."
    )
    parser.add_argument(
        "--triage-artifact", required=True, help="Path to static triage JSON."
    )
    parser.add_argument("--out", required=True, help="Output probe artifact path.")
    args = parser.parse_args(argv)

    result = build_probe_artifact(
        runtime_artifact_path=Path(args.runtime_artifact),
        handoff_artifact_path=Path(args.handoff_artifact),
        triage_artifact_path=Path(args.triage_artifact),
    )

    out_path = Path(args.out)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Probe artifact written to {out_path}")
    print(f"probe_status={result['probe_status']}")
    print(f"recommended_backend={result['recommended_backend']}")
    print(f"can_attempt_interactive_console_validation_next={result['can_attempt_interactive_console_validation_next']}")
    return 0 if result["probe_status"] == "READY_FOR_MATURE_BACKEND_VALIDATION" else 1


if __name__ == "__main__":
    sys.exit(main())
