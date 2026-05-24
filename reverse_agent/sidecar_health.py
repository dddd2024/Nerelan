from __future__ import annotations

from typing import Any

LIFECYCLE_FIELDS = (
    "script_load_status",
    "script_load_error",
    "js_top_level_seen",
    "js_top_level_timestamp",
    "js_hooks_install_begin_seen",
    "js_hooks_installed_seen",
    "js_hook_install_exception_count",
    "js_hook_install_exception_messages",
    "script_load_to_hooks_installed_elapsed_ms",
    "script_load_to_ui_trigger_elapsed_ms",
    "ui_trigger_after_hooks_installed",
    "ui_trigger_epoch_ms",
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
