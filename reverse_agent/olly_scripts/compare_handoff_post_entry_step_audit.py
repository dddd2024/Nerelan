from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path


def _write_payload(out_path: Path, payload: dict[str, object]) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return 0


def _load_points(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _hook_points_map(hook_points: dict[str, object]) -> dict[str, object]:
    points = hook_points.get("hook_points", {})
    return points if isinstance(points, dict) else {}


def _hook_address(hook_points: dict[str, object], name: str, fallback: str) -> str:
    point = _hook_points_map(hook_points).get(name, {})
    point = point if isinstance(point, dict) else {}
    return str(point.get("module_offset") or point.get("address") or fallback)


def _environment_diagnostics(
    *,
    target: Path,
    backend: str = "unknown",
    backend_import_ok: bool = False,
    backend_error: str = "",
    target_launch_attempted: bool = False,
    target_launch_ok: bool = False,
    target_launch_error: str = "",
) -> dict[str, object]:
    return {
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "debugger_backend": backend,
        "backend_import_ok": backend_import_ok,
        "backend_error": backend_error,
        "target_executable_exists": target.exists(),
        "target_launch_attempted": target_launch_attempted,
        "target_launch_ok": target_launch_ok,
        "target_launch_error": target_launch_error,
    }


def _breakpoint_installation_diagnostics(hook_points: dict[str, object]) -> dict[str, object]:
    return {
        "predecessor_handoff_call": {
            "address": _hook_address(hook_points, "predecessor_handoff_call", "0x2338"),
            "install_attempted": False,
            "install_ok": False,
            "hit": False,
            "error": "",
        },
        "handoff_helper_entry": {
            "address": _hook_address(hook_points, "handoff_helper_entry", "0x1b50"),
            "install_attempted": False,
            "install_ok": False,
            "hit": False,
            "error": "",
        },
    }


def _single_step_diagnostics(
    *,
    step_attempted: bool = False,
    step_api_available: bool = False,
    step_count: int = 0,
    first_step_eip: str = "",
    last_step_eip: str = "",
    error: str = "",
) -> dict[str, object]:
    return {
        "step_attempted": step_attempted,
        "step_api_available": step_api_available,
        "step_count": step_count,
        "first_step_eip": first_step_eip,
        "last_step_eip": last_step_eip,
        "error": error,
    }


def _artifact_parse_diagnostics(out_path: Path) -> dict[str, object]:
    return {
        "raw_log_path": str(out_path.with_suffix(".log")),
        "raw_log_exists": out_path.with_suffix(".log").exists(),
        "parse_attempted": False,
        "parse_ok": False,
        "parse_error": "",
    }


def _blocked_payload(
    *,
    candidate_hex: str,
    max_steps: int,
    reason: str,
    detail: str,
    hook_points: dict[str, object],
    out_path: Path,
    environment_diagnostics: dict[str, object],
    breakpoint_installation_diagnostics: dict[str, object] | None = None,
    single_step_diagnostics: dict[str, object] | None = None,
) -> dict[str, object]:
    breakpoint_installation_diagnostics = (
        breakpoint_installation_diagnostics
        if isinstance(breakpoint_installation_diagnostics, dict)
        else _breakpoint_installation_diagnostics(hook_points)
    )
    single_step_diagnostics = (
        single_step_diagnostics
        if isinstance(single_step_diagnostics, dict)
        else _single_step_diagnostics()
    )
    return {
        "schema_version": 1,
        "artifact_kind": "compare_handoff_post_entry_step_runtime_audit",
        "success": False,
        "runtime_sidecar_executed": False,
        "candidate_hex": candidate_hex,
        "runtime_scope": {
            "sidecar": "compare_handoff_post_entry_step_audit.py",
            "max_steps_per_candidate": max_steps,
            "material_capture_allowed": False,
            "crypto_hook_allowed": False,
            "breakpoint_probe_allowed": False,
        },
        "max_steps_per_candidate": max_steps,
        "material_capture_allowed": False,
        "crypto_hook_allowed": False,
        "breakpoint_probe_allowed": False,
        "hook_points": hook_points,
        "environment_diagnostics": environment_diagnostics,
        "breakpoint_installation_diagnostics": breakpoint_installation_diagnostics,
        "single_step_diagnostics": single_step_diagnostics,
        "artifact_parse_diagnostics": _artifact_parse_diagnostics(out_path),
        "entry_context": {
            "predecessor_handoff_call_observed": False,
            "handoff_helper_entry_observed": False,
            "eip": "",
            "esp": "",
            "ebp": "",
            "stack_top_words": [],
            "return_target_candidate": "",
        },
        "post_entry_events": [],
        "branch_observation": {
            "observed": False,
            "branch_eip": "",
            "instruction": "",
            "eflags": "",
            "condition": "",
            "outcome": "unknown",
            "next_eip": "",
            "classification": reason,
        },
        "return_target_observation": {
            "observed": False,
            "value": "",
            "trust": "instrumentation_gap",
            "reason": detail,
        },
        "process_exception_observed": False,
        "compare_successor_observed": False,
        "actual_compare_observed": False,
        "post_entry_outcome": reason,
        "blocked_reason": reason,
        "error": detail,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded post-entry handoff step audit")
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--points", required=True)
    parser.add_argument("--probe-hex", required=True)
    parser.add_argument("--expected-eax-preview", default="")
    parser.add_argument("--per-probe-timeout", default="2.2")
    parser.add_argument("--max-steps", type=int, default=32)
    args = parser.parse_args(argv)

    _ = args.expected_eax_preview
    _ = args.per_probe_timeout
    out_path = Path(args.out)
    target = Path(args.target)
    hook_points = _load_points(Path(args.points))
    max_steps = max(1, min(int(args.max_steps), 32))

    if not target.exists():
        environment = _environment_diagnostics(
            target=target,
            backend="unknown",
            target_launch_attempted=True,
            target_launch_ok=False,
            target_launch_error=f"target does not exist: {target}",
        )
        return _write_payload(
            out_path,
            _blocked_payload(
                candidate_hex=args.probe_hex,
                max_steps=max_steps,
                reason="target_process_launch_failed",
                detail=f"target does not exist: {target}",
                hook_points=hook_points,
                out_path=out_path,
                environment_diagnostics=environment,
            ),
        )

    try:
        import frida  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on local runtime
        environment = _environment_diagnostics(
            target=target,
            backend="unavailable",
            backend_import_ok=False,
            backend_error=f"{type(exc).__name__}: {exc}",
            target_launch_attempted=False,
        )
        return _write_payload(
            out_path,
            _blocked_payload(
                candidate_hex=args.probe_hex,
                max_steps=max_steps,
                reason="debugger_backend_missing",
                detail=f"frida runtime unavailable: {exc}",
                hook_points=hook_points,
                out_path=out_path,
                environment_diagnostics=environment,
            ),
        )

    environment = _environment_diagnostics(
        target=target,
        backend="frida",
        backend_import_ok=True,
        target_launch_attempted=False,
    )
    return _write_payload(
        out_path,
        _blocked_payload(
            candidate_hex=args.probe_hex,
            max_steps=max_steps,
            reason="step_api_unavailable",
            detail=(
                "post-entry single-step runtime hook is available as a bounded sidecar "
                "contract, but no local Olly/Frida stepping implementation captured "
                "branch instruction, EFLAGS, or next EIP in this environment"
            ),
            hook_points=hook_points,
            out_path=out_path,
            environment_diagnostics=environment,
            single_step_diagnostics=_single_step_diagnostics(
                step_attempted=False,
                step_api_available=False,
                error="no local Olly/Frida single-step implementation is wired for this sidecar",
            ),
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
