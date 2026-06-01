from __future__ import annotations

import argparse
import json
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


def _blocked_payload(
    *,
    candidate_hex: str,
    max_steps: int,
    reason: str,
    detail: str,
    hook_points: dict[str, object],
) -> dict[str, object]:
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
        "hook_points": hook_points,
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
        return _write_payload(
            out_path,
            _blocked_payload(
                candidate_hex=args.probe_hex,
                max_steps=max_steps,
                reason="missing_environment",
                detail=f"target does not exist: {target}",
                hook_points=hook_points,
            ),
        )

    try:
        import frida  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on local runtime
        return _write_payload(
            out_path,
            _blocked_payload(
                candidate_hex=args.probe_hex,
                max_steps=max_steps,
                reason="runtime_unavailable",
                detail=f"frida runtime unavailable: {exc}",
                hook_points=hook_points,
            ),
        )

    return _write_payload(
        out_path,
        _blocked_payload(
            candidate_hex=args.probe_hex,
            max_steps=max_steps,
            reason="instrumentation_gap",
            detail=(
                "post-entry single-step runtime hook is available as a bounded sidecar "
                "contract, but no local Olly/Frida stepping implementation captured "
                "branch instruction, EFLAGS, or next EIP in this environment"
            ),
            hook_points=hook_points,
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
