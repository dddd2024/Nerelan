from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:  # Support package imports in tests and direct script execution.
    from .compare_probe import _candidate_to_gui_text, _escape_runtime_text, _terminate_target, _trigger_decrypt
except ImportError:  # pragma: no cover - exercised by subprocess execution
    from compare_probe import _candidate_to_gui_text, _escape_runtime_text, _terminate_target, _trigger_decrypt


FRAME_SLOT_OFFSETS = (0x1160, 0x1164, 0x1168, 0x116C, 0x1170)
WRITE_RING_LIMIT = 4096


def _artifact_kind_for_script() -> str:
    if Path(sys.argv[0]).stem == "compare_lhs_last_writer_provenance":
        return "compare_lhs_last_writer_provenance_audit"
    return "compare_pre_compare_handoff_target_probe"


def _normalize_hook_point(item: dict[str, object] | None) -> dict[str, object]:
    item = item or {}
    module_offset = item.get("module_offset")
    try:
        module_offset_int = int(module_offset) if module_offset is not None else None
    except (TypeError, ValueError):
        module_offset_int = None
    return {
        "name": str(item.get("name", "")),
        "address": str(item.get("address", "")),
        "module_offset": module_offset_int,
        "instruction": str(item.get("instruction", "")),
        "reason": str(item.get("reason", "")),
        "role": str(item.get("role", "")),
        "capture_leave": bool(item.get("capture_leave")),
        "capture_write_ring": bool(item.get("capture_write_ring")),
    }


def _normalize_observation(item: dict[str, object] | None) -> dict[str, object]:
    item = item or {}
    return {
        "hook_name": str(item.get("hook_name", "")),
        "address": str(item.get("address", "")),
        "module_offset": str(item.get("module_offset", "")),
        "instruction": str(item.get("instruction", "")),
        "registers": dict(item.get("registers", {})) if isinstance(item.get("registers"), dict) else {},
        "stack_words": list(item.get("stack_words", [])) if isinstance(item.get("stack_words"), list) else [],
        "frame_slots": list(item.get("frame_slots", [])) if isinstance(item.get("frame_slots"), list) else [],
        "eax_ptr": str(item.get("eax_ptr", "")),
        "eax_preview_hex": str(item.get("eax_preview_hex", "")),
        "ecx_ptr": str(item.get("ecx_ptr", "")),
        "ecx_preview_hex": str(item.get("ecx_preview_hex", "")),
        "edx_ptr": str(item.get("edx_ptr", "")),
        "edx_preview_hex": str(item.get("edx_preview_hex", "")),
        "esi_ptr": str(item.get("esi_ptr", "")),
        "esi_preview_hex": str(item.get("esi_preview_hex", "")),
        "edi_ptr": str(item.get("edi_ptr", "")),
        "edi_preview_hex": str(item.get("edi_preview_hex", "")),
        "compare_args": dict(item.get("compare_args", {})) if isinstance(item.get("compare_args"), dict) else {},
        "compare_entry": dict(item.get("compare_entry", {})) if isinstance(item.get("compare_entry"), dict) else {},
        "argument_previews": dict(item.get("argument_previews", {}))
        if isinstance(item.get("argument_previews"), dict)
        else {},
        "expected_eax_preview_hex": str(item.get("expected_eax_preview_hex", "")),
        "matched_expected_eax": bool(item.get("matched_expected_eax")),
        "event": str(item.get("event", "")),
        "return_address": str(item.get("return_address", "")),
        "return_address_module_offset": str(item.get("return_address_module_offset", "")),
        "current_module_offset": str(item.get("current_module_offset", "")),
        "return_value": str(item.get("return_value", "")),
        "exception": dict(item.get("exception", {})) if isinstance(item.get("exception"), dict) else {},
        "write_monitor_health": dict(item.get("write_monitor_health", {}))
        if isinstance(item.get("write_monitor_health"), dict)
        else {},
        "write_ring_buffer": list(item.get("write_ring_buffer", []))
        if isinstance(item.get("write_ring_buffer"), list)
        else [],
    }


def _build_payload(
    *,
    success: bool,
    summary: str,
    candidate_hex: str = "",
    hook_points: list[dict[str, object]] | None = None,
    hook_observations: list[dict[str, object]] | None = None,
    write_monitor_health: dict[str, object] | None = None,
    write_ring_buffer: list[dict[str, object]] | None = None,
    evidence: list[str] | None = None,
    hook_install_status: str = "",
    hook_count: int = 0,
    requested_hook_count: int = 0,
    script_load_status: str = "",
    script_load_error: str = "",
    python_exception_count: int = 0,
    frida_message_error_count: int = 0,
    hook_install_error_count: int = 0,
    hooks_installed_stage_seen: bool = False,
    hooks_installed_stage_hook_count: int = 0,
    per_hook_install_results: list[dict[str, object]] | None = None,
    js_top_level_seen: bool = False,
    js_top_level_timestamp: object = "",
    js_hooks_install_begin_seen: bool = False,
    js_hooks_installed_seen: bool = False,
    js_hook_install_exception_count: int = 0,
    js_hook_install_exception_messages: list[str] | None = None,
    python_message_callback_registered_before_load: bool = False,
    python_message_count_total: int = 0,
    python_message_count_by_type: dict[str, int] | None = None,
    python_message_decode_error_count: int = 0,
    python_message_last_payload: dict[str, object] | None = None,
    module_base_resolution_status: str = "",
    hook_address_by_name: dict[str, str] | None = None,
    hook_address_validation: list[dict[str, object]] | None = None,
    process_spawned_at_ms: object = None,
    frida_attached_at_ms: object = None,
    script_load_start_at_ms: object = None,
    script_loaded_at_ms: object = None,
    message_callback_registered_at_ms: object = None,
    hooks_install_begin_at_ms: object = None,
    hooks_installed_at_ms: object = None,
    script_load_to_hooks_installed_elapsed_ms: object = None,
    script_load_to_ui_trigger_elapsed_ms: object = None,
    ui_trigger_start_at_ms: object = None,
    ui_trigger_end_at_ms: object = None,
    ui_trigger_after_hooks_installed: bool = False,
    ui_trigger_epoch_ms: object = None,
    hooks_ready_barrier_seen: bool = False,
    hooks_ready_barrier_wait_ms: object = None,
    hooks_ready_before_ui_trigger: bool = False,
    ui_trigger_timing_status: str = "",
    timeout_or_wait_reason: str = "",
    observation_count: int = 0,
    post_ui_observation_count: int = 0,
    hook_hit_counts_by_name: dict[str, int] | None = None,
    first_observation_timestamp_ms: object = None,
    last_observation_timestamp_ms: object = None,
    last_observation_hook_name: str = "",
    waiting_for_observation_reason: str = "",
    hook_not_hit_vs_hook_not_installed_classification: str = "",
    spawn_attach_resume_status: str = "",
    ui_trigger_status: str = "",
    helper_observation_count: int = 0,
    static_compare_observation_count: int = 0,
    root_cause_hypothesis: str = "",
    root_cause_evidence: list[str] | None = None,
    runtime_stage: str = "",
    error: str = "",
) -> dict[str, object]:
    observations = [_normalize_observation(item) for item in hook_observations or []]
    return {
        "schema_version": 1,
        "artifact_kind": _artifact_kind_for_script(),
        "success": success,
        "summary": summary,
        "candidate_hex": candidate_hex,
        "hook_points": hook_points or [],
        "hook_observations": observations,
        "write_monitor_health": dict(write_monitor_health or {}),
        "write_ring_buffer": list(write_ring_buffer or []),
        "evidence": evidence or [],
        "hook_install_status": hook_install_status,
        "hook_count": hook_count,
        "requested_hook_count": requested_hook_count,
        "script_load_status": script_load_status,
        "script_load_error": script_load_error,
        "python_exception_count": python_exception_count,
        "frida_message_error_count": frida_message_error_count,
        "hook_install_error_count": hook_install_error_count,
        "hooks_installed_stage_seen": hooks_installed_stage_seen,
        "hooks_installed_stage_hook_count": hooks_installed_stage_hook_count,
        "per_hook_install_results": list(per_hook_install_results or []),
        "js_top_level_seen": js_top_level_seen,
        "js_top_level_timestamp": js_top_level_timestamp,
        "js_hooks_install_begin_seen": js_hooks_install_begin_seen,
        "js_hooks_installed_seen": js_hooks_installed_seen,
        "js_hook_install_exception_count": js_hook_install_exception_count,
        "js_hook_install_exception_messages": list(js_hook_install_exception_messages or []),
        "python_message_callback_registered_before_load": python_message_callback_registered_before_load,
        "python_message_count_total": python_message_count_total,
        "python_message_count_by_type": dict(python_message_count_by_type or {}),
        "python_message_decode_error_count": python_message_decode_error_count,
        "python_message_last_payload": dict(python_message_last_payload or {}),
        "module_base_resolution_status": module_base_resolution_status,
        "hook_address_by_name": dict(hook_address_by_name or {}),
        "hook_address_validation": list(hook_address_validation or []),
        "process_spawned_at_ms": process_spawned_at_ms,
        "frida_attached_at_ms": frida_attached_at_ms,
        "script_load_start_at_ms": script_load_start_at_ms,
        "script_loaded_at_ms": script_loaded_at_ms,
        "message_callback_registered_at_ms": message_callback_registered_at_ms,
        "hooks_install_begin_at_ms": hooks_install_begin_at_ms,
        "hooks_installed_at_ms": hooks_installed_at_ms,
        "script_load_to_hooks_installed_elapsed_ms": script_load_to_hooks_installed_elapsed_ms,
        "script_load_to_ui_trigger_elapsed_ms": script_load_to_ui_trigger_elapsed_ms,
        "ui_trigger_start_at_ms": ui_trigger_start_at_ms,
        "ui_trigger_end_at_ms": ui_trigger_end_at_ms,
        "ui_trigger_after_hooks_installed": ui_trigger_after_hooks_installed,
        "ui_trigger_epoch_ms": ui_trigger_epoch_ms,
        "hooks_ready_barrier_seen": hooks_ready_barrier_seen,
        "hooks_ready_barrier_wait_ms": hooks_ready_barrier_wait_ms,
        "hooks_ready_before_ui_trigger": hooks_ready_before_ui_trigger,
        "ui_trigger_timing_status": ui_trigger_timing_status,
        "timeout_or_wait_reason": timeout_or_wait_reason,
        "observation_count": observation_count,
        "post_ui_observation_count": post_ui_observation_count,
        "hook_hit_counts_by_name": dict(hook_hit_counts_by_name or {}),
        "first_observation_timestamp_ms": first_observation_timestamp_ms,
        "last_observation_timestamp_ms": last_observation_timestamp_ms,
        "last_observation_hook_name": last_observation_hook_name,
        "waiting_for_observation_reason": waiting_for_observation_reason,
        "hook_not_hit_vs_hook_not_installed_classification": hook_not_hit_vs_hook_not_installed_classification,
        "spawn_attach_resume_status": spawn_attach_resume_status,
        "ui_trigger_status": ui_trigger_status,
        "helper_observation_count": helper_observation_count,
        "static_compare_observation_count": static_compare_observation_count,
        "root_cause_hypothesis": root_cause_hypothesis,
        "root_cause_evidence": root_cause_evidence or [],
        "runtime_stage": runtime_stage,
        "error": error,
    }


def _write_payload(out_path: Path, payload: dict[str, object]) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return 0


def _read_points(path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    raw_points = payload.get("hook_points", [])
    if not isinstance(raw_points, list):
        return []
    return [_normalize_hook_point(item) for item in raw_points if isinstance(item, dict)]


def _initial_write_monitor_health(hook_points: list[dict[str, object]]) -> dict[str, object]:
    requested = any(bool(point.get("capture_write_ring")) for point in hook_points)
    return {
        "observed": False,
        "enabled": requested,
        "requested": requested,
        "activation_status": "script_started",
        "runtime_stage": "script_started",
        "followed_thread_count": 0,
        "raw_write_count": 0,
        "ring_capacity": WRITE_RING_LIMIT if requested else 0,
        "eviction_count": 0,
        "descriptor_decode_failures": 0,
        "address_decode_failures": 0,
        "follow_failures": 0,
        "last_raw_write_samples": [],
        "filtered_intersecting_write_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe bounded pre-compare handoff targets for samplereverse")
    parser.add_argument("--target", required=True, help="Path to target executable")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--points", required=True, help="Hook point JSON path")
    parser.add_argument("--probe-hex", required=True, help="Probe candidate as raw low-byte hex")
    parser.add_argument("--expected-eax-preview", default="", help="Producer trace EAX preview expected for this candidate")
    parser.add_argument("--per-probe-timeout", type=float, default=2.2)
    args = parser.parse_args()

    target = Path(args.target)
    out_path = Path(args.out)
    points_path = Path(args.points)
    hook_points = _read_points(points_path)
    evidence = [
        f"compare_pre_compare_handoff_target_probe:target={target}",
        f"compare_pre_compare_handoff_target_probe:points={points_path}",
        "compare_pre_compare_handoff_target_probe:runtime_stage=arguments_parsed",
    ]

    if not target.exists():
        return _write_payload(
            out_path,
            _build_payload(
                success=False,
                summary="ComparePreCompareHandoffTargetProbe failed: target missing.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                evidence=[
                    *evidence,
                    "compare_pre_compare_handoff_target_probe:runtime_stage=target_missing",
                    "compare_pre_compare_handoff_target_probe:error=target_missing",
                ],
                runtime_stage="target_missing",
                error="target_missing",
            ),
        )

    _write_payload(
        out_path,
        _build_payload(
            success=False,
            summary="ComparePreCompareHandoffTargetProbe importing runtime dependencies.",
            candidate_hex=args.probe_hex,
            hook_points=hook_points,
            evidence=[*evidence, "compare_pre_compare_handoff_target_probe:runtime_stage=importing_dependencies"],
            requested_hook_count=len(hook_points),
            script_load_status="not_started",
            spawn_attach_resume_status="not_started",
            ui_trigger_status="not_started",
            runtime_stage="importing_dependencies",
        ),
    )
    try:
        import frida
        from pywinauto import Application
    except Exception as exc:
        return _write_payload(
            out_path,
            _build_payload(
                success=False,
                summary="ComparePreCompareHandoffTargetProbe failed: missing frida or pywinauto.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                evidence=[
                    *evidence,
                    "compare_pre_compare_handoff_target_probe:runtime_stage=dependency_import_failed",
                    f"compare_pre_compare_handoff_target_probe:error={_escape_runtime_text(str(exc))}",
                ],
                runtime_stage="dependency_import_failed",
                error=str(exc),
            ),
        )

    _write_payload(
        out_path,
        _build_payload(
            success=False,
            summary="ComparePreCompareHandoffTargetProbe started; waiting for bounded handoff observations.",
            candidate_hex=args.probe_hex,
            hook_points=hook_points,
            write_monitor_health=_initial_write_monitor_health(hook_points),
            evidence=[*evidence, "compare_pre_compare_handoff_target_probe:script_started"],
            requested_hook_count=len(hook_points),
            script_load_status="not_started",
            spawn_attach_resume_status="not_started",
            ui_trigger_status="not_started",
            runtime_stage="script_started",
        ),
    )

    messages: list[dict[str, object]] = []
    frida_message_errors: list[str] = []
    python_exceptions: list[str] = []
    python_message_decode_error_count = 0
    python_message_callback_count = 0
    python_message_last_payload: dict[str, object] = {}
    python_message_callback_registered_before_load = False
    process_spawned_at_ms: int | None = None
    frida_attached_at_ms: int | None = None
    script_load_start_at_ms: int | None = None
    script_loaded_at_ms: int | None = None
    message_callback_registered_at_ms: int | None = None
    hooks_install_begin_at_ms: int | None = None
    hooks_installed_at_ms: int | None = None
    script_load_monotonic: float | None = None
    hooks_installed_monotonic: float | None = None
    ui_trigger_monotonic: float | None = None
    ui_trigger_start_monotonic: float | None = None
    ui_trigger_start_at_ms: int | None = None
    ui_trigger_end_at_ms: int | None = None
    ui_trigger_epoch_ms: int | None = None
    hooks_ready_barrier_seen = False
    hooks_ready_barrier_wait_ms: float | None = None
    hooks_ready_before_ui_trigger = False
    ui_trigger_timing_status = ""
    timeout_or_wait_reason = ""
    runtime_stage = "script_started"
    script_load_status = "not_started"
    script_load_error = ""
    spawn_attach_resume_status = "not_started"
    ui_trigger_status = "not_started"
    pid: int | None = None
    session = None
    app = None

    def epoch_ms() -> int:
        return int(time.time() * 1000)

    def bridge_snapshot() -> dict[str, object]:
        stage_messages = [
            item
            for item in messages
            if str(item.get("type", "")) == "compare_pre_compare_handoff_target_stage"
        ]
        count_by_type: dict[str, int] = {}
        for item in messages:
            item_type = str(item.get("type", "")).strip() or "unknown"
            count_by_type[item_type] = count_by_type.get(item_type, 0) + 1
        js_top_level_messages = [
            item for item in stage_messages if str(item.get("runtime_stage", "")) == "js_top_level"
        ]
        js_hooks_install_begin_messages = [
            item for item in stage_messages if str(item.get("runtime_stage", "")) == "hooks_install_begin"
        ]
        js_hooks_installed_messages = [
            item for item in stage_messages if str(item.get("runtime_stage", "")) == "hooks_installed"
        ]
        hook_install_messages = [
            item
            for item in messages
            if str(item.get("type", "")) == "compare_pre_compare_handoff_target_hook_install_result"
        ]
        per_hook_results = [
            {
                "name": str(item.get("name", "")),
                "module_offset": str(item.get("module_offset", "")),
                "install_status": str(item.get("install_status", "")),
                "address": str(item.get("address", "")),
                "address_validation": str(item.get("address_validation", "")),
                "error": str(item.get("error", "")),
            }
            for item in hook_install_messages
        ]
        module_base_resolution_status = ""
        hook_address_by_name: dict[str, str] = {}
        hook_address_validation: list[dict[str, object]] = []
        for item in stage_messages:
            if str(item.get("module_base_resolution_status", "")).strip():
                module_base_resolution_status = str(item.get("module_base_resolution_status", "")).strip()
            raw_by_name = item.get("hook_address_by_name", {})
            if isinstance(raw_by_name, dict):
                hook_address_by_name.update({str(key): str(value) for key, value in raw_by_name.items()})
            raw_validation = item.get("hook_address_validation", [])
            if isinstance(raw_validation, list):
                hook_address_validation = [dict(row) for row in raw_validation if isinstance(row, dict)]
        return {
            "js_top_level_seen": bool(js_top_level_messages),
            "js_top_level_timestamp": js_top_level_messages[-1].get("timestamp_ms", "") if js_top_level_messages else "",
            "js_hooks_install_begin_seen": bool(js_hooks_install_begin_messages),
            "js_hooks_installed_seen": bool(js_hooks_installed_messages),
            "hooks_install_begin_at_ms": js_hooks_install_begin_messages[-1].get("timestamp_ms", None)
            if js_hooks_install_begin_messages
            else None,
            "hooks_installed_at_ms": js_hooks_installed_messages[-1].get("timestamp_ms", None)
            if js_hooks_installed_messages
            else None,
            "hook_count": max(
                [int(item.get("hook_count", 0) or 0) for item in js_hooks_installed_messages] or [0]
            ),
            "hooks_installed_stage_seen": bool(js_hooks_installed_messages),
            "hooks_installed_stage_hook_count": max(
                [int(item.get("hook_count", 0) or 0) for item in js_hooks_installed_messages] or [0]
            ),
            "per_hook_install_results": per_hook_results,
            "hook_install_error_count": sum(1 for item in per_hook_results if item["install_status"] == "failed"),
            "python_message_count_by_type": count_by_type,
            "module_base_resolution_status": module_base_resolution_status,
            "hook_address_by_name": hook_address_by_name,
            "hook_address_validation": hook_address_validation,
        }

    def write_progress_payload(stage: str) -> None:
        health = _initial_write_monitor_health(hook_points)
        health["runtime_stage"] = stage
        if stage not in {"script_started", "importing_dependencies"}:
            health["activation_status"] = stage
        bridge = bridge_snapshot()
        _write_payload(
            out_path,
            _build_payload(
                success=False,
                summary=f"ComparePreCompareHandoffTargetProbe runtime stage: {stage}.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                write_monitor_health=health,
                evidence=[*evidence, f"compare_pre_compare_handoff_target_probe:runtime_stage={stage}"],
                hook_install_status="installed"
                if bool(bridge.get("hooks_installed_stage_seen"))
                and int(bridge.get("hook_count", 0) or 0) >= len(hook_points)
                and len(hook_points) > 0
                else "",
                hook_count=int(bridge.get("hook_count", 0) or 0),
                requested_hook_count=len(hook_points),
                hook_install_error_count=int(bridge.get("hook_install_error_count", 0) or 0),
                hooks_installed_stage_seen=bool(bridge.get("hooks_installed_stage_seen")),
                hooks_installed_stage_hook_count=int(bridge.get("hooks_installed_stage_hook_count", 0) or 0),
                per_hook_install_results=bridge.get("per_hook_install_results", []),
                script_load_status=script_load_status,
                script_load_error=script_load_error,
                js_top_level_seen=bool(bridge.get("js_top_level_seen")),
                js_top_level_timestamp=bridge.get("js_top_level_timestamp", ""),
                js_hooks_install_begin_seen=bool(bridge.get("js_hooks_install_begin_seen")),
                js_hooks_installed_seen=bool(bridge.get("js_hooks_installed_seen")),
                python_message_callback_registered_before_load=python_message_callback_registered_before_load,
                python_message_count_total=python_message_callback_count,
                python_message_count_by_type=bridge.get("python_message_count_by_type", {}),
                python_message_decode_error_count=python_message_decode_error_count,
                python_message_last_payload=python_message_last_payload,
                module_base_resolution_status=str(bridge.get("module_base_resolution_status", "")),
                hook_address_by_name=bridge.get("hook_address_by_name", {}),
                hook_address_validation=bridge.get("hook_address_validation", []),
                process_spawned_at_ms=process_spawned_at_ms,
                frida_attached_at_ms=frida_attached_at_ms,
                script_load_start_at_ms=script_load_start_at_ms,
                script_loaded_at_ms=script_loaded_at_ms,
                message_callback_registered_at_ms=message_callback_registered_at_ms,
                hooks_install_begin_at_ms=bridge.get("hooks_install_begin_at_ms", None),
                hooks_installed_at_ms=bridge.get("hooks_installed_at_ms", None),
                ui_trigger_start_at_ms=ui_trigger_start_at_ms,
                ui_trigger_end_at_ms=ui_trigger_end_at_ms,
                ui_trigger_after_hooks_installed=bool(hooks_ready_before_ui_trigger),
                ui_trigger_epoch_ms=ui_trigger_epoch_ms,
                hooks_ready_barrier_seen=hooks_ready_barrier_seen,
                hooks_ready_barrier_wait_ms=hooks_ready_barrier_wait_ms,
                hooks_ready_before_ui_trigger=hooks_ready_before_ui_trigger,
                ui_trigger_timing_status=ui_trigger_timing_status,
                timeout_or_wait_reason=timeout_or_wait_reason,
                spawn_attach_resume_status=spawn_attach_resume_status,
                ui_trigger_status=ui_trigger_status,
                runtime_stage=stage,
            ),
        )

    def on_message(message: dict[str, object], data: object) -> None:  # noqa: ANN401
        nonlocal hooks_installed_at_ms, hooks_installed_monotonic, python_message_callback_count
        nonlocal python_message_decode_error_count, python_message_last_payload
        python_message_callback_count += 1
        message_type = str(message.get("type", ""))
        if message_type == "send":
            payload = message.get("payload", {})
            if isinstance(payload, dict):
                messages.append(payload)
                python_message_last_payload = dict(payload)
                if str(payload.get("runtime_stage", "")) == "hooks_installed":
                    hooks_installed_monotonic = time.monotonic()
                    try:
                        hooks_installed_at_ms = int(payload.get("timestamp_ms", 0) or 0) or epoch_ms()
                    except (TypeError, ValueError):
                        hooks_installed_at_ms = epoch_ms()
            else:
                python_message_decode_error_count += 1
            return
        if message_type == "error":
            stack = str(message.get("stack", "")).strip()
            if stack:
                frida_message_errors.append(stack)
            else:
                description = str(message.get("description", "")).strip()
                if description:
                    frida_message_errors.append(description)
            python_message_last_payload = {
                "type": "frida_error",
                "description": str(message.get("description", "")).strip(),
                "stack": str(message.get("stack", "")).strip(),
            }

    def observation_messages() -> list[dict[str, object]]:
        return [
            item
            for item in messages
            if str(item.get("type", "")) == "compare_pre_compare_handoff_target_observation"
        ]

    def has_compare_args(item: dict[str, object]) -> bool:
        compare_args = item.get("compare_args", {})
        return isinstance(compare_args, dict) and isinstance(compare_args.get("args"), list) and bool(compare_args["args"])

    def static_compare_observations() -> list[dict[str, object]]:
        return [
            item
            for item in observation_messages()
            if str(item.get("hook_name", "")) == "static_compare_callsite"
        ]

    def helper_observed() -> bool:
        return any(
            str(item.get("hook_name", "")) == "handoff_helper_candidate"
            for item in observation_messages()
        )

    points_json = json.dumps(hook_points, ensure_ascii=True)
    expected_preview = str(args.expected_eax_preview or "").strip().lower()
    script_source = f"""
const hookPoints = {points_json};
const expectedEaxPreview = "{expected_preview}";
const frameSlotOffsets = {json.dumps(list(FRAME_SLOT_OFFSETS))};
const writeRingEnabled = hookPoints.some(point => Boolean(point.capture_write_ring));
const writeRingLimit = {WRITE_RING_LIMIT};
const writeRing = [];
const lastRawWriteSamples = [];
let writeSequence = 0;
let writeMonitorFollowedThreadCount = 0;
let writeMonitorRawWriteCount = 0;
let writeMonitorEvictionCount = 0;
let writeMonitorDescriptorDecodeFailures = 0;
let writeMonitorAddressDecodeFailures = 0;
let writeMonitorFollowFailures = 0;
let writeMonitorActivationStatus = writeRingEnabled ? "waiting_for_hook_observation" : "disabled";
let writeMonitorSelectedThreadId = "";
let writeMonitorFollowAttemptStage = "";

function sendStage(fields) {{
    try {{
        const payload = Object.assign({{
            type: "compare_pre_compare_handoff_target_stage",
            timestamp_ms: Date.now(),
        }}, fields || {{}});
        send(payload);
    }} catch (error) {{
    }}
}}

function hexBytes(raw) {{
    if (!raw) {{
        return "";
    }}
    const bytes = new Uint8Array(raw);
    let out = [];
    for (let i = 0; i < bytes.length; i++) {{
        out.push(("0" + bytes[i].toString(16)).slice(-2));
    }}
    return out.join("");
}}

function readBytes(ptrValue, size) {{
    try {{
        if (!ptrValue || ptrValue.isNull()) {{
            return "";
        }}
        const raw = ptrValue.readByteArray(Math.min(Math.max(size, 16), 160));
        return hexBytes(raw);
    }} catch (error) {{
        return "";
    }}
}}

function safePointer(value) {{
    try {{
        return ptr(value);
    }} catch (error) {{
        return ptr(0);
    }}
}}

function moduleOffsetText(value, moduleBase) {{
    try {{
        return "0x" + value.sub(moduleBase).toString(16);
    }} catch (error) {{
        return "";
    }}
}}

function pointerValue(value) {{
    try {{
        if (!value || value.isNull()) {{
            return 0;
        }}
        return parseInt(value.toString(), 16);
    }} catch (error) {{
        return 0;
    }}
}}

function rangesIntersect(aStart, aSize, bStart, bSize) {{
    const aEnd = aStart + Math.max(aSize || 1, 1);
    const bEnd = bStart + Math.max(bSize || 1, 1);
    return aStart < bEnd && bStart < aEnd;
}}

function contextRegisterValue(context, name) {{
    try {{
        if (!name) {{
            return ptr(0);
        }}
        const normalized = String(name).toLowerCase();
        if (context[normalized] !== undefined) {{
            return safePointer(context[normalized]);
        }}
        const aliases = {{
            eip: "pc",
            rip: "pc",
            esp: "sp",
            rsp: "sp",
            ebp: "bp",
            rbp: "bp",
        }};
        const alias = aliases[normalized] || "";
        if (alias && context[alias] !== undefined) {{
            return safePointer(context[alias]);
        }}
    }} catch (error) {{
    }}
    return ptr(0);
}}

function operandSizeBytes(instruction, operand) {{
    try {{
        if (operand && operand.size) {{
            return Number(operand.size);
        }}
    }} catch (error) {{
    }}
    const text = String(instruction || "").toLowerCase();
    if (text.indexOf("xmmword ptr") >= 0) {{
        return 16;
    }}
    if (text.indexOf("qword ptr") >= 0) {{
        return 8;
    }}
    if (text.indexOf("dword ptr") >= 0) {{
        return 4;
    }}
    if (text.indexOf("word ptr") >= 0) {{
        return 2;
    }}
    if (text.indexOf("byte ptr") >= 0) {{
        return 1;
    }}
    return Process.pointerSize;
}}

function memoryWriteDescriptor(instruction) {{
    try {{
        const operands = instruction.operands || [];
        if (!operands.length) {{
            return null;
        }}
        const operand = operands[0];
        const access = String(operand.access || "");
        if (operand.type !== "mem" || (access && access.indexOf("w") < 0)) {{
            return null;
        }}
        const mem = operand.value || {{}};
        return {{
            base: String(mem.base || ""),
            index: String(mem.index || ""),
            scale: Number(mem.scale || 1),
            disp: Number(mem.disp || mem.displacement || 0),
            size: operandSizeBytes(instruction, operand),
            instruction: instruction.toString(),
            module_offset: moduleOffsetText(instruction.address, mainModule.base),
            address: instruction.address.toString(),
        }};
    }} catch (error) {{
        writeMonitorDescriptorDecodeFailures++;
        return null;
    }}
}}

function memoryAddressFromDescriptor(context, descriptor) {{
    try {{
        let value = 0;
        if (descriptor.base) {{
            value += pointerValue(contextRegisterValue(context, descriptor.base));
        }}
        if (descriptor.index) {{
            value += pointerValue(contextRegisterValue(context, descriptor.index)) * Number(descriptor.scale || 1);
        }}
        if (descriptor.disp) {{
            value += Number(descriptor.disp || 0);
        }}
        return ptr(value);
    }} catch (error) {{
        writeMonitorAddressDecodeFailures++;
        return ptr(0);
    }}
}}

function recordMemoryWrite(context, descriptor) {{
    if (!writeRingEnabled || !descriptor) {{
        return;
    }}
    try {{
        const address = memoryAddressFromDescriptor(context, descriptor);
        if (!address || address.isNull()) {{
            writeMonitorAddressDecodeFailures++;
            return;
        }}
        writeMonitorRawWriteCount++;
        let threadId = "";
        try {{
            threadId = String(Process.getCurrentThreadId());
        }} catch (error) {{
            threadId = "";
        }}
        const event = {{
            sequence: writeSequence++,
            address: address.toString(),
            address_u64: pointerValue(address),
            size: Number(descriptor.size || Process.pointerSize),
            thread_id: threadId,
            instruction_address: descriptor.address,
            module_offset: descriptor.module_offset,
            instruction: descriptor.instruction,
            before_preview_hex: readBytes(address, 96),
        }};
        writeRing.push(event);
        lastRawWriteSamples.push({{
            sequence: event.sequence,
            address: event.address,
            size: event.size,
            instruction_address: event.instruction_address,
            module_offset: event.module_offset,
            instruction: event.instruction,
            before_preview_hex: event.before_preview_hex,
        }});
        if (lastRawWriteSamples.length > 8) {{
            lastRawWriteSamples.shift();
        }}
        if (writeRing.length > writeRingLimit) {{
            writeRing.shift();
            writeMonitorEvictionCount++;
        }}
    }} catch (error) {{
        writeMonitorAddressDecodeFailures++;
    }}
}}

function filteredWriteRing(compareSlots) {{
    if (!writeRingEnabled || !compareSlots || compareSlots.length < 2) {{
        return [];
    }}
    const arg0 = compareSlots[1] || {{}};
    const arg0Start = pointerValue(safePointer(arg0.value || 0));
    const previewHex = String(arg0.preview_hex || "");
    const arg0Size = Math.max(Math.floor(previewHex.length / 2), 16);
    if (!arg0Start) {{
        return [];
    }}
    let out = [];
    for (const item of writeRing) {{
        const itemStart = Number(item.address_u64 || 0);
        const itemSize = Number(item.size || 1);
        const intersectsArg0 = Boolean(itemStart && rangesIntersect(itemStart, itemSize, arg0Start, arg0Size));
        const itemEnd = itemStart + Math.max(itemSize || 1, 1);
        const arg0End = arg0Start + Math.max(arg0Size || 1, 1);
        let distanceToArg0 = 0;
        let boundedFailureReason = "";
        if (!itemStart) {{
            boundedFailureReason = "write_address_unavailable";
        }} else if (intersectsArg0) {{
            boundedFailureReason = "";
        }} else if (itemEnd <= arg0Start) {{
            distanceToArg0 = arg0Start - itemEnd;
            boundedFailureReason = "write_before_arg0_window";
        }} else {{
            distanceToArg0 = itemStart - arg0End;
            boundedFailureReason = "write_after_arg0_window";
        }}
        out.push(Object.assign({{}}, item, {{
            raw_write_observed: true,
            intersects_arg0: intersectsArg0,
            arg0_value: String(arg0.value || ""),
            arg0_preview_hex: previewHex,
            arg0_size: arg0Size,
            distance_to_arg0: distanceToArg0,
            bounded_failure_reason: boundedFailureReason,
            after_preview_hex: readBytes(safePointer(item.address || 0), 96),
        }}));
    }}
    return out.slice(-64);
}}

function writeMonitorHealth(filteredWrites) {{
    let intersectingWriteCount = 0;
    if (filteredWrites) {{
        for (const item of filteredWrites) {{
            if (item && item.intersects_arg0) {{
                intersectingWriteCount++;
            }}
        }}
    }}
    return {{
        observed: true,
        enabled: Boolean(writeRingEnabled),
        activation_status: writeMonitorActivationStatus,
        selected_thread_id: String(writeMonitorSelectedThreadId || ""),
        follow_attempt_stage: String(writeMonitorFollowAttemptStage || ""),
        followed_thread_count: writeMonitorFollowedThreadCount,
        raw_write_count: writeMonitorRawWriteCount,
        ring_capacity: writeRingLimit,
        eviction_count: writeMonitorEvictionCount,
        descriptor_decode_failures: writeMonitorDescriptorDecodeFailures,
        address_decode_failures: writeMonitorAddressDecodeFailures,
        follow_failures: writeMonitorFollowFailures,
        last_raw_write_samples: lastRawWriteSamples.slice(-8),
        filtered_intersecting_write_count: intersectingWriteCount,
        attributed_write_count: filteredWrites ? filteredWrites.length : 0,
    }};
}}

function startWriteRingForThread(threadId, stage) {{
    if (!writeRingEnabled) {{
        writeMonitorActivationStatus = "disabled";
        return;
    }}
    if (writeMonitorFollowedThreadCount > 0) {{
        return;
    }}
    writeMonitorFollowAttemptStage = String(stage || "hook_observed");
    writeMonitorSelectedThreadId = String(threadId || "");
    try {{
        Stalker.follow(threadId, {{
            transform(iterator) {{
                let instruction = iterator.next();
                while (instruction !== null) {{
                    const descriptor = memoryWriteDescriptor(instruction);
                    if (descriptor) {{
                        iterator.putCallout(function(context) {{
                            recordMemoryWrite(context, descriptor);
                        }});
                    }}
                    iterator.keep();
                    instruction = iterator.next();
                }}
            }},
        }});
        writeMonitorFollowedThreadCount++;
        writeMonitorActivationStatus = "following_current_thread";
    }} catch (error) {{
        writeMonitorFollowFailures++;
        writeMonitorActivationStatus = "follow_failed";
        send({{ type: "compare_pre_compare_handoff_target_error", hook_name: "write_ring_buffer", error: String(error) }});
    }}
}}

function sendWriteMonitorHealth() {{
    try {{
        send({{
            type: "compare_pre_compare_handoff_target_write_monitor_health",
            write_monitor_health: writeMonitorHealth([]),
            write_ring_buffer: writeRing.slice(-64),
        }});
    }} catch (error) {{
    }}
}}

function contextRegs(context) {{
    let regs = {{}};
    for (const name of ["eax", "ebx", "ecx", "edx", "esi", "edi", "esp", "ebp", "eip", "rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rsp", "rbp", "rip"]) {{
        try {{
            if (context[name] !== undefined) {{
                regs[name] = context[name].toString();
            }}
        }} catch (error) {{
        }}
    }}
    return regs;
}}

function stackWords(sp, moduleBase) {{
    let out = [];
    for (let i = 0; i < 8; i++) {{
        try {{
            const slot = sp.add(i * Process.pointerSize);
            const value = slot.readPointer();
            out.push({{
                index: i,
                esp_relative: "+0x" + (i * Process.pointerSize).toString(16),
                value: value.toString(),
                module_offset: moduleOffsetText(value, moduleBase),
                preview_hex: readBytes(value, 96),
            }});
        }} catch (error) {{
        }}
    }}
    return out;
}}

function frameSlots(bp, moduleBase) {{
    let out = [];
    for (const offset of frameSlotOffsets) {{
        try {{
            const slot = bp.sub(ptr(offset));
            const value = slot.readPointer();
            out.push({{
                name: "[ebp-0x" + offset.toString(16) + "]",
                offset: "-0x" + offset.toString(16),
                address: slot.toString(),
                value: value.toString(),
                module_offset: moduleOffsetText(value, moduleBase),
                preview_hex: readBytes(value, 128),
            }});
        }} catch (error) {{
        }}
    }}
    return out;
}}

function compareEntrySlots(sp, moduleBase) {{
    let slots = [];
    for (let i = 0; i < 4; i++) {{
        try {{
            const slot = sp.add(i * Process.pointerSize);
            const value = slot.readPointer();
            slots.push({{
                index: i,
                role: i === 0 ? "return_address" : "arg" + (i - 1).toString(),
                value: value.toString(),
                module_offset: moduleOffsetText(value, moduleBase),
                preview_hex: readBytes(value, 128),
            }});
        }} catch (error) {{
        }}
    }}
    return slots;
}}

function compareCallsiteSlots(sp, address, moduleBase) {{
    let slots = [{{
        index: 0,
        role: "return_address",
        value: address.toString(),
        module_offset: moduleOffsetText(address, moduleBase),
        preview_hex: "",
    }}];
    for (let i = 0; i < 3; i++) {{
        try {{
            const slot = sp.add(i * Process.pointerSize);
            if (i === 2) {{
                slots.push({{
                    index: i + 1,
                    role: "arg" + i.toString(),
                    value_u32: slot.readU32(),
                }});
            }} else {{
                const value = slot.readPointer();
                slots.push({{
                    index: i + 1,
                    role: "arg" + i.toString(),
                    value: value.toString(),
                    module_offset: moduleOffsetText(value, moduleBase),
                    preview_hex: readBytes(value, 128),
                }});
            }}
        }} catch (error) {{
        }}
    }}
    return slots;
}}

function observe(point, address, context, eventName, extra) {{
    extra = extra || {{}};
    const mainModule = Process.enumerateModules()[0];
    let currentThreadId = "";
    try {{
        currentThreadId = Process.getCurrentThreadId();
    }} catch (error) {{
        currentThreadId = "";
    }}
    const sp = ptr(context.sp || context.esp || 0);
    const bp = ptr(context.bp || context.ebp || 0);
    const eax = safePointer(context.eax || context.rax || 0);
    const ecx = safePointer(context.ecx || context.rcx || 0);
    const edx = safePointer(context.edx || context.rdx || 0);
    const esi = safePointer(context.esi || context.rsi || 0);
    const edi = safePointer(context.edi || context.rdi || 0);
    const ip = safePointer(context.eip || context.rip || context.pc || 0);
    const eaxPreview = readBytes(eax, 128);
    const pointName = String(point.name || "");
    if (writeRingEnabled && eventName !== "leave" && currentThreadId !== "") {{
        startWriteRingForThread(currentThreadId, pointName || "hook_observed");
    }}
    const isHelperCompare = pointName === "compare_helper_entry" || pointName === "actual_compare_entry";
    const isStaticCompareCallsite = pointName === "static_compare_callsite";
    const compareSlots = isStaticCompareCallsite
        ? compareCallsiteSlots(sp, address, mainModule.base)
        : isHelperCompare
            ? compareEntrySlots(sp, mainModule.base)
            : [];
    const filteredWrites = isStaticCompareCallsite ? filteredWriteRing(compareSlots) : [];
    const observationWriteRing = isStaticCompareCallsite ? filteredWrites : writeRing.slice(-64);
    const tracePointByName = {{
        old_lhs_slot_store: "slot_writer",
        pre_compare_lhs_push: "pre_push_esi",
        pre_compare_push_esi: "pre_push_esi",
        post_handoff_lhs_reload: "reload_source",
        initial_lhs_reload: "reload_source",
        final_lhs_reload: "reload_source",
        static_compare_callsite: "actual_compare",
    }};
    const arg0TracePoint = {{
        role: tracePointByName[pointName] || "",
        site: moduleOffsetText(address, mainModule.base),
        hook_name: pointName,
        event: eventName || "enter",
        esi_value: esi.toString(),
        esi_preview_hex: readBytes(esi, 128),
        eax_value: eax.toString(),
        eax_preview_hex: eaxPreview,
        frame_slots: frameSlots(bp, mainModule.base),
        compare_args: compareSlots.length > 0 ? compareSlots.slice(1).map((slot, index) => Object.assign({{}}, slot, {{
            index: index,
            role: "arg" + index.toString(),
        }})) : [],
        write_ring_buffer: observationWriteRing,
    }};
    send({{
        type: "compare_pre_compare_handoff_target_observation",
        timestamp_ms: Date.now(),
        hook_name: pointName,
        event: eventName || "enter",
        address: address.toString(),
        module_offset: moduleOffsetText(address, mainModule.base),
        instruction: String(point.instruction || ""),
        registers: contextRegs(context),
        stack_words: stackWords(sp, mainModule.base),
        frame_slots: frameSlots(bp, mainModule.base),
        eax_ptr: eax.toString(),
        eax_preview_hex: eaxPreview,
        ecx_ptr: ecx.toString(),
        ecx_preview_hex: readBytes(ecx, 128),
        edx_ptr: edx.toString(),
        edx_preview_hex: readBytes(edx, 128),
        esi_ptr: esi.toString(),
        esi_preview_hex: readBytes(esi, 128),
        edi_ptr: edi.toString(),
        edi_preview_hex: readBytes(edi, 128),
        compare_entry: compareSlots.length > 0 ? {{ slots: compareSlots }} : {{}},
        compare_args: compareSlots.length > 0 ? {{ args: compareSlots.slice(1).map((slot, index) => Object.assign({{}}, slot, {{
            index: index,
            role: "arg" + index.toString(),
        }})) }} : {{}},
        expected_eax_preview_hex: expectedEaxPreview,
        matched_expected_eax: expectedEaxPreview.length > 0 && eaxPreview.toLowerCase().startsWith(expectedEaxPreview.slice(0, 32)),
        return_address: String(extra.return_address || ""),
        return_address_module_offset: String(extra.return_address_module_offset || ""),
        current_module_offset: moduleOffsetText(ip, mainModule.base),
        return_value: String(extra.return_value || ""),
        exception: extra.exception || {{}},
        write_monitor_health: writeMonitorHealth(filteredWrites),
        write_ring_buffer: observationWriteRing,
        arg0_final_data_writer_trace_point: arg0TracePoint,
    }});
}}

let mainModule = null;
let moduleBaseResolutionStatus = "not_started";
let moduleBaseText = "";
let hookAddressByName = {{}};
let hookAddressValidation = [];
sendStage({{
    runtime_stage: "js_top_level",
    js_top_level_seen: true,
    requested_hook_count: hookPoints.length,
}});
try {{
    mainModule = Process.enumerateModules()[0];
    moduleBaseResolutionStatus = mainModule && mainModule.base ? "resolved" : "missing";
    moduleBaseText = mainModule && mainModule.base ? mainModule.base.toString() : "";
}} catch (error) {{
    moduleBaseResolutionStatus = "failed";
    send({{ type: "compare_pre_compare_handoff_target_error", hook_name: "module_base", error: String(error) }});
}}
sendStage({{
    runtime_stage: "module_base_resolved",
    module_base_resolution_status: moduleBaseResolutionStatus,
    module_base: moduleBaseText,
    requested_hook_count: hookPoints.length,
}});
sendWriteMonitorHealth();
if (writeRingEnabled) {{
    setInterval(sendWriteMonitorHealth, 100);
}}
try {{
    Process.setExceptionHandler(function(details) {{
        const address = safePointer(details.address || 0);
        const context = details.context || {{}};
        observe({{ name: "process_exception", instruction: String(details.type || "exception") }}, address, context, "exception", {{
            exception: {{
                type: String(details.type || ""),
                address: address.toString(),
                memory: details.memory ? String(details.memory.address || "") : "",
            }},
        }});
        return false;
    }});
}} catch (error) {{
}}
let installedHookCount = 0;
sendStage({{
    runtime_stage: "hooks_install_begin",
    module_base_resolution_status: moduleBaseResolutionStatus,
    module_base: moduleBaseText,
    requested_hook_count: hookPoints.length,
}});
try {{
    for (const point of hookPoints) {{
        try {{
            const offset = Number(point.module_offset || 0);
            if (!offset) {{
                const skipped = {{
                    name: String(point.name || ""),
                    module_offset: String(point.module_offset || ""),
                    install_status: "skipped_invalid_offset",
                    address: "",
                    address_validation: "invalid_offset",
                    error: "missing_or_zero_module_offset",
                }};
                hookAddressValidation.push(skipped);
                send(Object.assign({{ type: "compare_pre_compare_handoff_target_hook_install_result" }}, skipped));
                continue;
            }}
            if (!mainModule || !mainModule.base) {{
                const missing = {{
                    name: String(point.name || ""),
                    module_offset: "0x" + offset.toString(16),
                    install_status: "failed",
                    address: "",
                    address_validation: "module_base_unavailable",
                    error: "module_base_unavailable",
                }};
                hookAddressValidation.push(missing);
                send(Object.assign({{ type: "compare_pre_compare_handoff_target_hook_install_result" }}, missing));
                send({{ type: "compare_pre_compare_handoff_target_error", hook_name: String(point.name || ""), error: "module_base_unavailable" }});
                continue;
            }}
            const address = mainModule.base.add(offset);
            const pointName = String(point.name || "");
            hookAddressByName[pointName] = address.toString();
            Interceptor.attach(address, {{
                onEnter(args) {{
                    try {{
                        const sp = ptr(this.context.sp || this.context.esp || 0);
                        this.returnAddressForAudit = sp.readPointer();
                    }} catch (error) {{
                        this.returnAddressForAudit = ptr(0);
                    }}
                    observe(point, address, this.context, "enter", {{
                        return_address: this.returnAddressForAudit.toString(),
                        return_address_module_offset: moduleOffsetText(this.returnAddressForAudit, mainModule.base),
                    }});
                }},
                onLeave(retval) {{
                    if (!point.capture_leave) {{
                        return;
                    }}
                    observe(point, address, this.context, "leave", {{
                        return_address: this.returnAddressForAudit ? this.returnAddressForAudit.toString() : "",
                        return_address_module_offset: this.returnAddressForAudit ? moduleOffsetText(this.returnAddressForAudit, mainModule.base) : "",
                        return_value: retval ? retval.toString() : "",
                    }});
                }},
            }});
            installedHookCount++;
            const installed = {{
                name: pointName,
                module_offset: "0x" + offset.toString(16),
                install_status: "installed",
                address: address.toString(),
                address_validation: "resolved",
                error: "",
            }};
            hookAddressValidation.push(installed);
            send(Object.assign({{ type: "compare_pre_compare_handoff_target_hook_install_result" }}, installed));
        }} catch (error) {{
            const offsetText = point.module_offset ? "0x" + Number(point.module_offset).toString(16) : "";
            let addressText = "";
            try {{
                addressText = mainModule && mainModule.base && point.module_offset ? mainModule.base.add(Number(point.module_offset)).toString() : "";
            }} catch (addressError) {{
                addressText = "";
            }}
            const failed = {{
                name: String(point.name || ""),
                module_offset: offsetText,
                install_status: "failed",
                address: addressText,
                address_validation: addressText ? "resolved_attach_failed" : "address_unavailable",
                error: String(error),
            }};
            hookAddressValidation.push(failed);
            send(Object.assign({{ type: "compare_pre_compare_handoff_target_hook_install_result" }}, failed));
            send({{ type: "compare_pre_compare_handoff_target_error", hook_name: String(point.name || ""), error: String(error) }});
        }}
    }}
}} catch (error) {{
    send({{ type: "compare_pre_compare_handoff_target_error", hook_name: "hook_install_loop", error: String(error) }});
}}
sendStage({{
    runtime_stage: "hooks_installed",
    hook_count: installedHookCount,
    requested_hook_count: hookPoints.length,
    module_base_resolution_status: moduleBaseResolutionStatus,
    module_base: moduleBaseText,
    hook_address_by_name: hookAddressByName,
    hook_address_validation: hookAddressValidation,
}});
"""

    try:
        runtime_stage = "spawning_target"
        write_progress_payload(runtime_stage)
        pid = frida.spawn([str(target)])
        process_spawned_at_ms = epoch_ms()
        spawn_attach_resume_status = "spawned"
        runtime_stage = "attaching_frida"
        write_progress_payload(runtime_stage)
        session = frida.attach(pid)
        frida_attached_at_ms = epoch_ms()
        spawn_attach_resume_status = "attached"
        runtime_stage = "creating_script"
        write_progress_payload(runtime_stage)
        script = session.create_script(script_source)
        script.on("message", on_message)
        python_message_callback_registered_before_load = True
        message_callback_registered_at_ms = epoch_ms()
        runtime_stage = "loading_script"
        script_load_status = "loading"
        script_load_start_at_ms = epoch_ms()
        script_load_monotonic = time.monotonic()
        write_progress_payload(runtime_stage)
        script.load()
        script_loaded_at_ms = epoch_ms()
        script_load_status = "loaded"
        runtime_stage = "script_loaded"
        write_progress_payload(runtime_stage)
        runtime_stage = "resuming_target"
        write_progress_payload(runtime_stage)
        frida.resume(pid)
        spawn_attach_resume_status = "resumed"
        runtime_stage = "waiting_for_hooks_ready"
        write_progress_payload(runtime_stage)
        barrier_start = time.monotonic()
        barrier_deadline = barrier_start + 1.0
        while hooks_installed_monotonic is None and time.monotonic() < barrier_deadline:
            time.sleep(0.02)
        hooks_ready_barrier_wait_ms = round((time.monotonic() - barrier_start) * 1000, 3)
        hooks_ready_barrier_seen = hooks_installed_monotonic is not None
        hooks_ready_before_ui_trigger = hooks_ready_barrier_seen
        if hooks_ready_barrier_seen:
            ui_trigger_timing_status = "hooks_ready_before_ui_trigger"
        else:
            ui_trigger_timing_status = "hooks_ready_barrier_timeout_before_ui_trigger"
            timeout_or_wait_reason = "hooks_installed_not_observed_before_ui_trigger_within_existing_window"
            runtime_stage = "hooks_ready_barrier_timeout_before_ui_trigger"
            ui_trigger_status = "not_triggered_hooks_ready_timeout"
            write_progress_payload(runtime_stage)
            raise RuntimeError(timeout_or_wait_reason)
        runtime_stage = "connecting_window"
        ui_trigger_status = "connecting_window"
        write_progress_payload(runtime_stage)
        app = Application(backend="uia").connect(process=pid)
        win = None
        last_exc = None
        for _ in range(60):
            try:
                win = app.top_window()
                if win.window_text() or win.exists(timeout=0.1):
                    break
            except Exception as exc:  # pragma: no cover - best effort UI attach
                last_exc = exc
                time.sleep(0.1)
        if win is None:
            raise RuntimeError(f"cannot connect target window: {last_exc}")

        runtime_stage = "preparing_input"
        ui_trigger_status = "window_connected"
        write_progress_payload(runtime_stage)
        input_edit = win.child_window(auto_id="1001", control_type="Edit")
        decrypt_btn = win.child_window(auto_id="1000", control_type="Button")
        candidate = bytes.fromhex(args.probe_hex).decode("latin1")
        evidence.append(f"compare_pre_compare_handoff_target_probe:title={_escape_runtime_text(win.window_text() or '')}")
        evidence.append(f"compare_pre_compare_handoff_target_probe:probe_hex={args.probe_hex}")
        input_edit.set_edit_text(_candidate_to_gui_text(candidate))
        ui_trigger_status = "input_injected"
        runtime_stage = "triggering_candidate"
        write_progress_payload(runtime_stage)
        ui_trigger_start_monotonic = time.monotonic()
        ui_trigger_start_at_ms = epoch_ms()
        _trigger_decrypt(decrypt_btn)
        ui_trigger_status = "button_triggered"
        ui_trigger_monotonic = time.monotonic()
        ui_trigger_end_at_ms = epoch_ms()
        ui_trigger_epoch_ms = ui_trigger_end_at_ms
        hooks_ready_before_ui_trigger = (
            hooks_installed_monotonic is not None
            and ui_trigger_start_monotonic is not None
            and ui_trigger_start_monotonic >= hooks_installed_monotonic
        )
        if hooks_ready_before_ui_trigger:
            ui_trigger_timing_status = "hooks_ready_before_ui_trigger"
        elif hooks_installed_monotonic is None:
            ui_trigger_timing_status = "hooks_ready_missing_before_ui_trigger"
            timeout_or_wait_reason = timeout_or_wait_reason or "hooks_installed_not_observed_before_ui_trigger"
        else:
            ui_trigger_timing_status = "ui_trigger_started_before_hooks_ready"
            timeout_or_wait_reason = "ui_trigger_started_before_hooks_ready"

        runtime_stage = "waiting_for_observation"
        write_progress_payload(runtime_stage)
        deadline = time.monotonic() + max(0.3, float(args.per_probe_timeout))
        while time.monotonic() < deadline:
            if frida_message_errors:
                runtime_stage = "frida_message_error"
                break
            static_observations = static_compare_observations()
            if any(has_compare_args(item) for item in static_observations):
                runtime_stage = "static_compare_callsite_observed"
                break
            if static_observations:
                runtime_stage = "static_compare_callsite_observed_no_args"
                break
            if helper_observed():
                runtime_stage = "helper_observed_waiting_for_static_compare"
            time.sleep(0.05)
    except Exception as exc:
        python_error = _escape_runtime_text(str(exc))
        python_exceptions.append(python_error)
        if runtime_stage in {"creating_script", "loading_script"}:
            script_load_error = python_error
            script_load_status = "failed"
    finally:
        if runtime_stage == "helper_observed_waiting_for_static_compare":
            runtime_stage = "stop_condition_before_compare"
        if runtime_stage not in {"static_compare_callsite_observed", "static_compare_callsite_observed_no_args"}:
            evidence.append(f"compare_pre_compare_handoff_target_probe:runtime_stage={runtime_stage}")
        try:
            if session is not None:
                session.detach()
        except Exception:
            pass
        if pid is not None:
            _terminate_target(app, pid)

    observations = observation_messages()
    health_messages = [
        item
        for item in messages
        if str(item.get("type", "")) == "compare_pre_compare_handoff_target_write_monitor_health"
    ]
    latest_health = {}
    latest_ring: list[dict[str, object]] = []
    if health_messages:
        health = health_messages[-1].get("write_monitor_health", {})
        ring = health_messages[-1].get("write_ring_buffer", [])
        latest_health = dict(health) if isinstance(health, dict) else {}
        latest_ring = [dict(item) for item in ring if isinstance(item, dict)] if isinstance(ring, list) else []
    if latest_health:
        latest_health["runtime_stage"] = runtime_stage
    elif hook_points:
        latest_health = _initial_write_monitor_health(hook_points)
        latest_health["runtime_stage"] = runtime_stage
        if runtime_stage == "waiting_for_observation":
            latest_health["activation_status"] = "waiting_for_hook_observation"
    hook_install_errors = [
        f"{item.get('hook_name', '')}:{item.get('error', '')}"
        for item in messages
        if str(item.get("type", "")) == "compare_pre_compare_handoff_target_error"
    ]
    hook_install_result_messages = [
        item
        for item in messages
        if str(item.get("type", "")) == "compare_pre_compare_handoff_target_hook_install_result"
    ]
    per_hook_install_results = []
    for item in hook_install_result_messages:
        per_hook_install_results.append(
            {
                "name": str(item.get("name", "")),
                "module_offset": str(item.get("module_offset", "")),
                "install_status": str(item.get("install_status", "")),
                "address": str(item.get("address", "")),
                "address_validation": str(item.get("address_validation", "")),
                "error": str(item.get("error", "")),
            }
        )
    frida_message_error_count = len(frida_message_errors)
    python_exception_count = len(python_exceptions)
    hook_install_error_count = sum(
        1 for item in per_hook_install_results if str(item.get("install_status", "")) == "failed"
    )
    stage_messages = [
        item
        for item in messages
        if str(item.get("type", "")) == "compare_pre_compare_handoff_target_stage"
    ]
    hooks_installed_stage_seen = False
    hooks_installed_stage_hook_count = 0
    if stage_messages:
        evidence.extend(
            f"compare_pre_compare_handoff_target_probe:runtime_stage={item.get('runtime_stage', '')}"
            for item in stage_messages
        )
    evidence.append(f"compare_pre_compare_handoff_target_probe:final_runtime_stage={runtime_stage}")
    static_observations = [
        item for item in observations if str(item.get("hook_name", "")) == "static_compare_callsite"
    ]
    hook_hit_counts_by_name: dict[str, int] = {}
    observation_timestamps: list[int] = []
    post_ui_observation_count = 0
    for item in observations:
        hook_name = str(item.get("hook_name", "")).strip() or "unknown"
        hook_hit_counts_by_name[hook_name] = hook_hit_counts_by_name.get(hook_name, 0) + 1
        try:
            timestamp_ms = int(item.get("timestamp_ms", 0) or 0)
        except (TypeError, ValueError):
            timestamp_ms = 0
        if timestamp_ms > 0:
            observation_timestamps.append(timestamp_ms)
            if ui_trigger_epoch_ms is not None and timestamp_ms >= ui_trigger_epoch_ms:
                post_ui_observation_count += 1
    observation_count = len(observations)
    first_observation_timestamp_ms = min(observation_timestamps) if observation_timestamps else None
    last_observation_timestamp_ms = max(observation_timestamps) if observation_timestamps else None
    last_observation_hook_name = str(observations[-1].get("hook_name", "")) if observations else ""
    helper_observation_count = sum(
        1 for item in observations if str(item.get("hook_name", "")) == "handoff_helper_candidate"
    )
    static_compare_observation_count = len(static_observations)
    hook_count = 0
    requested_hook_count = len(hook_points)
    if stage_messages:
        for item in stage_messages:
            if str(item.get("runtime_stage", "")) == "hooks_installed":
                hooks_installed_stage_seen = True
            try:
                hook_count = max(hook_count, int(item.get("hook_count", 0) or 0))
            except (TypeError, ValueError):
                pass
            try:
                requested_hook_count = max(
                    requested_hook_count,
                    int(item.get("requested_hook_count", 0) or 0),
                )
            except (TypeError, ValueError):
                pass
    hooks_installed_stage_hook_count = hook_count if hooks_installed_stage_seen else 0
    python_message_count_by_type: dict[str, int] = {}
    for item in messages:
        item_type = str(item.get("type", "")).strip() or "unknown"
        python_message_count_by_type[item_type] = python_message_count_by_type.get(item_type, 0) + 1
    js_top_level_messages = [item for item in stage_messages if str(item.get("runtime_stage", "")) == "js_top_level"]
    js_hooks_install_begin_messages = [
        item for item in stage_messages if str(item.get("runtime_stage", "")) == "hooks_install_begin"
    ]
    js_hooks_installed_messages = [
        item for item in stage_messages if str(item.get("runtime_stage", "")) == "hooks_installed"
    ]
    js_top_level_seen = bool(js_top_level_messages)
    js_top_level_timestamp = js_top_level_messages[-1].get("timestamp_ms", "") if js_top_level_messages else ""
    js_hooks_install_begin_seen = bool(js_hooks_install_begin_messages)
    js_hooks_installed_seen = bool(js_hooks_installed_messages)
    if js_hooks_install_begin_messages:
        try:
            hooks_install_begin_at_ms = int(js_hooks_install_begin_messages[-1].get("timestamp_ms", 0) or 0) or None
        except (TypeError, ValueError):
            hooks_install_begin_at_ms = None
    if js_hooks_installed_messages:
        try:
            hooks_installed_at_ms = int(js_hooks_installed_messages[-1].get("timestamp_ms", 0) or 0) or None
        except (TypeError, ValueError):
            hooks_installed_at_ms = hooks_installed_at_ms
    js_hook_install_exception_messages = [
        str(item.get("error", ""))
        for item in per_hook_install_results
        if str(item.get("install_status", "")) == "failed" and str(item.get("error", "")).strip()
    ]
    js_hook_install_exception_count = len(js_hook_install_exception_messages)
    module_base_resolution_status = ""
    hook_address_by_name: dict[str, str] = {}
    hook_address_validation: list[dict[str, object]] = []
    if stage_messages:
        for item in stage_messages:
            if str(item.get("module_base_resolution_status", "")).strip():
                module_base_resolution_status = str(item.get("module_base_resolution_status", "")).strip()
            raw_by_name = item.get("hook_address_by_name", {})
            if isinstance(raw_by_name, dict):
                hook_address_by_name.update({str(key): str(value) for key, value in raw_by_name.items()})
            raw_validation = item.get("hook_address_validation", [])
            if isinstance(raw_validation, list):
                hook_address_validation = [dict(row) for row in raw_validation if isinstance(row, dict)]
    if not hook_address_by_name:
        hook_address_by_name = {
            str(item.get("name", "")): str(item.get("address", ""))
            for item in per_hook_install_results
            if str(item.get("name", "")).strip() and str(item.get("address", "")).strip()
        }
    if not hook_address_validation:
        hook_address_validation = [dict(item) for item in per_hook_install_results]
    script_load_to_hooks_installed_elapsed_ms = None
    if script_load_monotonic is not None and hooks_installed_monotonic is not None:
        script_load_to_hooks_installed_elapsed_ms = round((hooks_installed_monotonic - script_load_monotonic) * 1000, 3)
    script_load_to_ui_trigger_elapsed_ms = None
    if script_load_monotonic is not None and ui_trigger_monotonic is not None:
        script_load_to_ui_trigger_elapsed_ms = round((ui_trigger_monotonic - script_load_monotonic) * 1000, 3)
    ui_trigger_after_hooks_installed = (
        ui_trigger_monotonic is not None
        and hooks_installed_monotonic is not None
        and ui_trigger_monotonic >= hooks_installed_monotonic
    )
    hooks_ready_before_ui_trigger = (
        hooks_installed_monotonic is not None
        and ui_trigger_start_monotonic is not None
        and ui_trigger_start_monotonic >= hooks_installed_monotonic
    )
    if not ui_trigger_timing_status:
        if hooks_ready_before_ui_trigger:
            ui_trigger_timing_status = "hooks_ready_before_ui_trigger"
        elif ui_trigger_monotonic is not None and hooks_installed_monotonic is None:
            ui_trigger_timing_status = "hooks_ready_missing_before_ui_trigger"
            timeout_or_wait_reason = timeout_or_wait_reason or "hooks_installed_not_observed_before_ui_trigger"
        elif ui_trigger_monotonic is not None:
            ui_trigger_timing_status = "ui_trigger_started_before_hooks_ready"
            timeout_or_wait_reason = timeout_or_wait_reason or "ui_trigger_started_before_hooks_ready"
    if not timeout_or_wait_reason and runtime_stage == "waiting_for_observation":
        timeout_or_wait_reason = "bounded_wait_ended_without_static_compare_observation"
    installed_results = [
        item for item in per_hook_install_results if str(item.get("install_status", "")) == "installed"
    ]
    failed_results = [
        item for item in per_hook_install_results if str(item.get("install_status", "")) == "failed"
    ]
    skipped_results = [
        item
        for item in per_hook_install_results
        if str(item.get("install_status", "")).startswith("skipped")
    ]
    if hooks_installed_stage_seen and hook_count == requested_hook_count and requested_hook_count > 0:
        hook_install_status = "installed"
    elif installed_results and (failed_results or skipped_results or hook_count < requested_hook_count):
        hook_install_status = "partial_or_failed"
    elif failed_results or (hooks_installed_stage_seen and hook_count == 0):
        hook_install_status = "failed_or_not_confirmed"
    elif not hooks_installed_stage_seen:
        hook_install_status = "not_confirmed_stage_missing"
    else:
        hook_install_status = "not_confirmed"
    if hook_install_errors and hook_install_status == "installed":
        hook_install_status = "partial_or_failed" if hook_count > 0 else "failed_or_not_confirmed"

    root_cause_hypothesis = ""
    root_cause_evidence: list[str] = []
    if not static_observations:
        if frida_message_errors:
            root_cause_hypothesis = "frida_message_error"
            root_cause_evidence.extend(f"frida_message_error={item}" for item in frida_message_errors[:3])
        elif script_load_status == "loaded" and python_message_callback_registered_before_load and not js_top_level_seen:
            root_cause_hypothesis = "js_top_level_not_seen"
            root_cause_evidence.append("script_load_status=loaded")
            root_cause_evidence.append("python_message_callback_registered_before_load=true")
            root_cause_evidence.append("js_top_level_seen=false")
        elif script_load_status == "loaded" and js_top_level_seen and not js_hooks_install_begin_seen:
            root_cause_hypothesis = "message_bridge_incomplete"
            root_cause_evidence.append("js_top_level_seen=true")
            root_cause_evidence.append("js_hooks_install_begin_seen=false")
            root_cause_evidence.append(f"python_message_count_total={python_message_callback_count}")
        elif script_load_status == "failed":
            if "SyntaxError" in script_load_error or "compile" in script_load_error.lower():
                root_cause_hypothesis = "js_compile_error"
            else:
                root_cause_hypothesis = "script_load_failed"
            root_cause_evidence.append(f"script_load_error={script_load_error}")
        elif not hooks_installed_stage_seen and script_load_status == "loaded":
            root_cause_hypothesis = "hooks_installed_stage_missing_after_script_load"
            root_cause_evidence.append("hooks_installed_stage_seen=false")
            root_cause_evidence.append("script_load_status=loaded")
            root_cause_evidence.append(f"js_top_level_seen={str(js_top_level_seen).lower()}")
            root_cause_evidence.append(f"js_hooks_install_begin_seen={str(js_hooks_install_begin_seen).lower()}")
            root_cause_evidence.append(
                "stage message missing: JS did not reach hooks_installed send, message handler did not receive it, or process ended before stage emission"
            )
        elif hooks_installed_stage_seen and hook_count == 0:
            root_cause_hypothesis = "hook_loop_completed_zero_installed"
            root_cause_evidence.append("hooks_installed_stage_seen=true")
            root_cause_evidence.append("hook loop completed with zero installed")
        elif hook_install_status != "installed":
            root_cause_hypothesis = "hook_install_failed" if hook_install_error_count else "timeout_before_hook_install"
            root_cause_evidence.append(f"hook_install_status={hook_install_status}")
            root_cause_evidence.append(f"script_load_status={script_load_status}")
            root_cause_evidence.append(f"requested_hook_count={requested_hook_count}")
        elif spawn_attach_resume_status != "resumed":
            root_cause_hypothesis = "spawn_attach_resume_failed"
            root_cause_evidence.append(f"spawn_attach_resume_status={spawn_attach_resume_status}")
        elif ui_trigger_status != "button_triggered":
            root_cause_hypothesis = "ui_trigger_failed"
            root_cause_evidence.append(f"ui_trigger_status={ui_trigger_status}")
        elif not hooks_ready_before_ui_trigger:
            root_cause_hypothesis = "hooks_ready_barrier_missing_before_ui_trigger"
            root_cause_evidence.append(f"hooks_ready_barrier_seen={str(hooks_ready_barrier_seen).lower()}")
            root_cause_evidence.append(f"hooks_ready_before_ui_trigger={str(hooks_ready_before_ui_trigger).lower()}")
            root_cause_evidence.append(f"ui_trigger_timing_status={ui_trigger_timing_status}")
            if timeout_or_wait_reason:
                root_cause_evidence.append(f"timeout_or_wait_reason={timeout_or_wait_reason}")
        elif hooks_installed_stage_seen and hook_install_status == "installed" and observation_count <= 0:
            root_cause_hypothesis = "hook_installed_but_not_hit_after_ui_trigger"
            root_cause_evidence.append("hooks_installed_stage_seen=true")
            root_cause_evidence.append("hook_install_status=installed")
            root_cause_evidence.append("ui_trigger_status=button_triggered")
            root_cause_evidence.append("observation_count=0")
            root_cause_evidence.append("no same-process hook observation captured after UI trigger before bounded timeout")
        elif helper_observation_count <= 0:
            root_cause_hypothesis = "timeout_after_ui_trigger_before_helper"
            root_cause_evidence.append("helper_observation_count=0")
        else:
            root_cause_hypothesis = "helper_hook_reached_but_static_compare_missing"
            root_cause_evidence.append(f"helper_observation_count={helper_observation_count}")
        root_cause_evidence.extend(
            [
                f"runtime_stage={runtime_stage}",
                f"hook_count={hook_count}",
                f"requested_hook_count={requested_hook_count}",
                f"hooks_installed_stage_seen={str(hooks_installed_stage_seen).lower()}",
                f"hooks_installed_stage_hook_count={hooks_installed_stage_hook_count}",
                f"script_load_status={script_load_status}",
                f"js_top_level_seen={str(js_top_level_seen).lower()}",
                f"js_hooks_install_begin_seen={str(js_hooks_install_begin_seen).lower()}",
                f"js_hooks_installed_seen={str(js_hooks_installed_seen).lower()}",
                f"python_message_callback_registered_before_load={str(python_message_callback_registered_before_load).lower()}",
                f"python_message_count_total={python_message_callback_count}",
                f"python_message_decode_error_count={python_message_decode_error_count}",
                f"module_base_resolution_status={module_base_resolution_status}",
                f"python_exception_count={python_exception_count}",
                f"frida_message_error_count={frida_message_error_count}",
                f"hook_install_error_count={hook_install_error_count}",
                f"spawn_attach_resume_status={spawn_attach_resume_status}",
                f"ui_trigger_status={ui_trigger_status}",
                f"hooks_ready_barrier_seen={str(hooks_ready_barrier_seen).lower()}",
                f"hooks_ready_before_ui_trigger={str(hooks_ready_before_ui_trigger).lower()}",
                f"ui_trigger_timing_status={ui_trigger_timing_status}",
                f"timeout_or_wait_reason={timeout_or_wait_reason}",
                f"observation_count={observation_count}",
                f"post_ui_observation_count={post_ui_observation_count}",
                f"static_compare_observation_count={static_compare_observation_count}",
            ]
        )
    waiting_for_observation_reason = root_cause_hypothesis if runtime_stage == "waiting_for_observation" else ""
    if (
        root_cause_hypothesis == "hook_installed_but_not_hit_after_ui_trigger"
        or hook_install_status == "installed"
        and hooks_installed_stage_seen
        and not static_observations
    ):
        hook_not_hit_vs_hook_not_installed_classification = "hook_not_hit"
    elif hook_install_status in {"failed_or_not_confirmed", "partial_or_failed"} or hook_install_error_count:
        hook_not_hit_vs_hook_not_installed_classification = "hook_not_installed"
    elif not hooks_installed_stage_seen:
        hook_not_hit_vs_hook_not_installed_classification = "install_ack_missing"
    else:
        hook_not_hit_vs_hook_not_installed_classification = "inconclusive"
    success = bool(static_observations) and not frida_message_errors and not python_exceptions
    summary = (
        "ComparePreCompareHandoffTargetProbe captured the bounded static compare callsite."
        if static_observations
        else "ComparePreCompareHandoffTargetProbe did not reach the bounded static compare callsite."
    )
    return _write_payload(
        out_path,
        _build_payload(
            success=success,
            summary=summary,
            candidate_hex=args.probe_hex,
            hook_points=hook_points,
            hook_observations=observations,
            write_monitor_health=latest_health,
            write_ring_buffer=latest_ring,
            evidence=[*evidence, *hook_install_errors, *frida_message_errors, *python_exceptions],
            hook_install_status=hook_install_status,
            hook_count=hook_count,
            requested_hook_count=requested_hook_count,
            script_load_status=script_load_status,
            script_load_error=script_load_error,
            python_exception_count=python_exception_count,
            frida_message_error_count=frida_message_error_count,
            hook_install_error_count=hook_install_error_count,
            hooks_installed_stage_seen=hooks_installed_stage_seen,
            hooks_installed_stage_hook_count=hooks_installed_stage_hook_count,
            per_hook_install_results=per_hook_install_results,
            js_top_level_seen=js_top_level_seen,
            js_top_level_timestamp=js_top_level_timestamp,
            js_hooks_install_begin_seen=js_hooks_install_begin_seen,
            js_hooks_installed_seen=js_hooks_installed_seen,
            js_hook_install_exception_count=js_hook_install_exception_count,
            js_hook_install_exception_messages=js_hook_install_exception_messages,
            python_message_callback_registered_before_load=python_message_callback_registered_before_load,
            python_message_count_total=python_message_callback_count,
            python_message_count_by_type=python_message_count_by_type,
            python_message_decode_error_count=python_message_decode_error_count,
            python_message_last_payload=python_message_last_payload,
            module_base_resolution_status=module_base_resolution_status,
            hook_address_by_name=hook_address_by_name,
            hook_address_validation=hook_address_validation,
            process_spawned_at_ms=process_spawned_at_ms,
            frida_attached_at_ms=frida_attached_at_ms,
            script_load_start_at_ms=script_load_start_at_ms,
            script_loaded_at_ms=script_loaded_at_ms,
            message_callback_registered_at_ms=message_callback_registered_at_ms,
            hooks_install_begin_at_ms=hooks_install_begin_at_ms,
            hooks_installed_at_ms=hooks_installed_at_ms,
            script_load_to_hooks_installed_elapsed_ms=script_load_to_hooks_installed_elapsed_ms,
            script_load_to_ui_trigger_elapsed_ms=script_load_to_ui_trigger_elapsed_ms,
            ui_trigger_start_at_ms=ui_trigger_start_at_ms,
            ui_trigger_end_at_ms=ui_trigger_end_at_ms,
            ui_trigger_after_hooks_installed=ui_trigger_after_hooks_installed,
            ui_trigger_epoch_ms=ui_trigger_epoch_ms,
            hooks_ready_barrier_seen=hooks_ready_barrier_seen,
            hooks_ready_barrier_wait_ms=hooks_ready_barrier_wait_ms,
            hooks_ready_before_ui_trigger=hooks_ready_before_ui_trigger,
            ui_trigger_timing_status=ui_trigger_timing_status,
            timeout_or_wait_reason=timeout_or_wait_reason,
            observation_count=observation_count,
            post_ui_observation_count=post_ui_observation_count,
            hook_hit_counts_by_name=hook_hit_counts_by_name,
            first_observation_timestamp_ms=first_observation_timestamp_ms,
            last_observation_timestamp_ms=last_observation_timestamp_ms,
            last_observation_hook_name=last_observation_hook_name,
            waiting_for_observation_reason=waiting_for_observation_reason,
            hook_not_hit_vs_hook_not_installed_classification=hook_not_hit_vs_hook_not_installed_classification,
            spawn_attach_resume_status=spawn_attach_resume_status,
            ui_trigger_status=ui_trigger_status,
            helper_observation_count=helper_observation_count,
            static_compare_observation_count=static_compare_observation_count,
            root_cause_hypothesis=root_cause_hypothesis,
            root_cause_evidence=root_cause_evidence,
            runtime_stage=runtime_stage,
            error="; ".join([*hook_install_errors, *frida_message_errors, *python_exceptions]),
        ),
    )


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
