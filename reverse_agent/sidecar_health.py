from __future__ import annotations

from typing import Any

LIFECYCLE_FIELDS = (
    "process_spawned_at_ms",
    "frida_attached_at_ms",
    "script_load_start_at_ms",
    "script_loaded_at_ms",
    "message_callback_registered_at_ms",
    "script_load_status",
    "script_load_error",
    "js_top_level_seen",
    "js_top_level_timestamp",
    "js_hooks_install_begin_seen",
    "js_hooks_installed_seen",
    "hooks_install_begin_at_ms",
    "hooks_installed_at_ms",
    "js_hook_install_exception_count",
    "js_hook_install_exception_messages",
    "script_load_to_hooks_installed_elapsed_ms",
    "script_load_to_ui_trigger_elapsed_ms",
    "ui_trigger_start_at_ms",
    "ui_trigger_end_at_ms",
    "ui_trigger_after_hooks_installed",
    "ui_trigger_epoch_ms",
    "hooks_ready_barrier_seen",
    "hooks_ready_barrier_wait_ms",
    "hooks_ready_before_ui_trigger",
    "ui_trigger_timing_status",
    "timeout_or_wait_reason",
    "waiting_for_observation_reason",
    "runtime_stage",
    "spawn_attach_resume_status",
    "ui_trigger_status",
)
SUBPROCESS_FIELDS = (
    "subprocess_command",
    "subprocess_cwd",
    "subprocess_returncode",
    "subprocess_timeout_seconds",
    "subprocess_timed_out",
    "subprocess_stdout_tail",
    "subprocess_stderr_tail",
)
FRIDA_FIELDS = ("python_exception_count", "frida_message_error_count")
HOOK_INSTALL_FIELDS = (
    "hook_install_status",
    "hook_count",
    "requested_hook_count",
    "hook_install_error_count",
    "hooks_installed_stage_seen",
    "hooks_installed_stage_hook_count",
    "per_hook_install_results",
    "hook_address_by_name",
    "hook_address_validation",
)
MESSAGE_BRIDGE_FIELDS = (
    "python_message_callback_registered_before_load",
    "python_message_count_total",
    "python_message_count_by_type",
    "python_message_decode_error_count",
    "python_message_last_payload",
)
OBSERVATION_FIELDS = (
    "helper_observation_count",
    "static_compare_observation_count",
    "observation_count",
    "post_ui_observation_count",
    "hook_hit_counts_by_name",
    "first_observation_timestamp_ms",
    "last_observation_timestamp_ms",
    "last_observation_hook_name",
    "same_process_compare_args_captured",
    "diagnostic_compare_args_captured",
    "module_base_resolution_status",
    "hook_not_hit_vs_hook_not_installed_classification",
    "same_process_provenance",
)
FALLBACK_FIELDS = (
    "compare_probe_fallback_used",
    "compare_probe_fallback_status",
    "compare_probe_fallback_command_or_path",
    "compare_probe_fallback_is_provenance",
)
CLASSIFICATION_FIELDS = (
    "instrumentation_failure_stage",
    "root_cause_hypothesis",
    "root_cause_evidence",
    "classification",
)


def _copy_known(raw: dict[str, object], keys: tuple[str, ...]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key in keys:
        if key in raw:
            value = raw.get(key)
            if value is not None:
                out[key] = value
    return out


def _int_value(value: object, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def classify_observation_delivery(rows: list[dict[str, object]] | tuple[dict[str, object], ...]) -> str:
    rows = [dict(row) for row in rows if isinstance(row, dict)]
    if not rows:
        return ""

    scripted_no_observations = any(
        str(row.get("scripted_hook_status") or "") == "scripted_hook_no_observations"
        for row in rows
    )
    if not scripted_no_observations:
        return ""

    target_mismatch_markers = {
        "module_base_resolution_status": {"failed", "missing", "unresolved", "not_resolved"},
        "spawn_attach_resume_status": {"spawn_failed", "attach_failed", "resume_failed", "failed"},
    }
    for field, bad_values in target_mismatch_markers.items():
        values = {str(row.get(field) or "").strip().lower() for row in rows if str(row.get(field) or "").strip()}
        if values & bad_values:
            return "arg0_target_path_or_process_mismatch"

    if any(_int_value(row.get("hook_install_error_count")) > 0 for row in rows):
        return "arg0_target_path_or_process_mismatch"

    message_error_seen = any(
        _int_value(row.get("frida_message_error_count")) > 0
        or _int_value(row.get("python_message_decode_error_count")) > 0
        for row in rows
    )
    hook_hit_seen = any(
        sum(_int_value(count) for count in dict(row.get("hook_hit_counts_by_name") or {}).values()) > 0
        for row in rows
        if isinstance(row.get("hook_hit_counts_by_name"), dict)
    )
    no_python_observation = all(_int_value(row.get("observation_count")) == 0 for row in rows)
    if hook_hit_seen and (message_error_seen or no_python_observation):
        return "message_bridge_dropped_observation"

    hooks_installed = all(
        str(row.get("hook_install_status") or "").strip() == "installed"
        or (
            bool(row.get("hooks_installed_seen") or row.get("hooks_installed_stage_seen"))
            and _int_value(row.get("hook_count")) >= _int_value(row.get("requested_hook_count"))
            and _int_value(row.get("requested_hook_count")) > 0
        )
        for row in rows
    )
    script_loaded = all(
        str(row.get("script_load_status") or "").strip() == "loaded"
        or bool(row.get("js_top_level_seen"))
        for row in rows
    )
    callback_ready = all(bool(row.get("python_message_callback_registered_before_load")) for row in rows)
    message_bridge_ready = all(_int_value(row.get("python_message_count_total")) > 0 for row in rows)
    ui_trigger_values = [str(row.get("ui_trigger_status") or "").strip() for row in rows]
    ui_trigger_field_present = any(bool(value) for value in ui_trigger_values)
    ui_triggered = bool(ui_trigger_values) and all(value == "button_triggered" for value in ui_trigger_values)
    ui_after_field_present = any("ui_trigger_after_hooks_installed" in row for row in rows)
    ui_after_hooks = all(bool(row.get("ui_trigger_after_hooks_installed")) for row in rows)
    timing_statuses = {
        str(row.get("ui_trigger_timing_status") or "").strip()
        for row in rows
        if str(row.get("ui_trigger_timing_status") or "").strip()
    }
    root_causes = {
        str(row.get("root_cause_hypothesis") or "").strip()
        for row in rows
        if str(row.get("root_cause_hypothesis") or "").strip()
    }

    if hooks_installed and script_loaded and callback_ready:
        if "not_triggered_hooks_ready_timeout" in ui_trigger_values:
            return "sidecar_runtime_precondition_failed"
        if ui_trigger_field_present and not ui_triggered:
            return "ui_trigger_not_executed"
        if (
            ui_triggered
            and ui_after_field_present
            and not ui_after_hooks
            and all(bool(row.get("hooks_ready_before_ui_trigger")) for row in rows)
        ):
            return "compare_arg_payload_schema_gap"
        if ui_triggered and ui_after_field_present and not ui_after_hooks:
            return "hooks_not_ready_before_ui_trigger"
        if (
            "hooks_ready_barrier_missing_before_ui_trigger" in root_causes
            or "hooks_ready_barrier_timeout_before_ui_trigger" in timing_statuses
            or "hooks_ready_missing_before_ui_trigger" in timing_statuses
            or "ui_trigger_started_before_hooks_ready" in timing_statuses
        ):
            return "hooks_not_ready_before_ui_trigger"
        if ui_triggered and not message_bridge_ready:
            return "message_bridge_dropped_observation"
        if message_bridge_ready and ui_triggered and no_python_observation and not message_error_seen:
            if hooks_installed and not hook_hit_seen:
                return "hook_installed_but_compare_call_not_reached_after_ui_trigger"
            return "ui_trigger_executed_but_compare_arg_observation_missing"
        return "inconclusive_with_missing_required_telemetry"

    return "inconclusive_with_missing_required_telemetry"


def normalize_sidecar_health(raw: dict[str, object] | None) -> dict[str, object]:
    raw = dict(raw or {})
    health = {
        "schema_version": 1,
        "lifecycle": _copy_known(raw, LIFECYCLE_FIELDS),
        "subprocess": _copy_known(raw, SUBPROCESS_FIELDS),
        "frida": _copy_known(raw, FRIDA_FIELDS),
        "hook_install": _copy_known(raw, HOOK_INSTALL_FIELDS),
        "message_bridge": _copy_known(raw, MESSAGE_BRIDGE_FIELDS),
        "observations": _copy_known(raw, OBSERVATION_FIELDS),
        "fallback": _copy_known(raw, FALLBACK_FIELDS),
        "classification": _copy_known(raw, CLASSIFICATION_FIELDS),
        "extra": {},
    }
    known: set[str] = set(
        LIFECYCLE_FIELDS
        + SUBPROCESS_FIELDS
        + FRIDA_FIELDS
        + HOOK_INSTALL_FIELDS
        + MESSAGE_BRIDGE_FIELDS
        + OBSERVATION_FIELDS
        + FALLBACK_FIELDS
        + CLASSIFICATION_FIELDS
    )
    extra: dict[str, object] = {}
    for key, value in raw.items():
        if key in known or key == "sidecar_health":
            continue
        extra[key] = value
    health["extra"] = extra
    return health


def summarize_sidecar_health(health: dict[str, object] | None) -> dict[str, object]:
    health = dict(health or {})
    summary: dict[str, object] = {}

    def _update_from(category_name: str, keys: tuple[str, ...]) -> None:
        category = health.get(category_name, {})
        if not isinstance(category, dict):
            return
        for key in keys:
            if key in category:
                value = category.get(key)
                if value is not None:
                    summary[key] = value

    _update_from("lifecycle", LIFECYCLE_FIELDS)
    _update_from("subprocess", SUBPROCESS_FIELDS)
    _update_from("frida", FRIDA_FIELDS)
    _update_from("hook_install", HOOK_INSTALL_FIELDS)
    _update_from("message_bridge", MESSAGE_BRIDGE_FIELDS)
    _update_from("observations", OBSERVATION_FIELDS)
    _update_from("fallback", FALLBACK_FIELDS)
    _update_from("classification", CLASSIFICATION_FIELDS)
    return summary


def merge_candidate_sidecar_health(
    candidate_payload: dict[str, object] | None,
    sidecar_payload: dict[str, object] | None,
) -> dict[str, object]:
    merged = dict(candidate_payload or {})
    merged["sidecar_health"] = normalize_sidecar_health(sidecar_payload)
    return merged
