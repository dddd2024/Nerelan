from __future__ import annotations

import argparse
import json
import platform
import sys
import threading
import time
import ctypes
from pathlib import Path

try:  # Support package imports in tests and direct subprocess execution.
    from .compare_probe import _candidate_to_gui_text, _terminate_target
except ImportError:  # pragma: no cover - exercised by direct subprocess execution
    from compare_probe import _candidate_to_gui_text, _terminate_target


BREAKPOINT_NAMES = (
    "predecessor_handoff_call",
    "handoff_helper_entry",
    "process_exception",
    "actual_compare",
)


def _write_payload(out_path: Path, payload: dict[str, object]) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return 0


def _now_monotonic() -> float:
    return round(time.monotonic(), 6)


def _load_points(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _hook_points_map(hook_points: dict[str, object]) -> dict[str, object]:
    points = hook_points.get("hook_points", {})
    return points if isinstance(points, dict) else {}


def _module_offset(hook_points: dict[str, object], name: str, fallback: str) -> str:
    point = _hook_points_map(hook_points).get(name, {})
    point = point if isinstance(point, dict) else {}
    return str(point.get("module_offset") or point.get("address") or fallback)


def _breakpoint_plan(hook_points: dict[str, object]) -> list[dict[str, object]]:
    fallbacks = {
        "predecessor_handoff_call": "0x2338",
        "handoff_helper_entry": "0x1b50",
        "process_exception": "0x1913",
        "actual_compare": "0x258c",
    }
    return [
        {
            "name": name,
            "module_offset": _module_offset(hook_points, name, fallbacks[name]),
        }
        for name in BREAKPOINT_NAMES
    ]


def _target_launch(
    *,
    attempted: bool = False,
    ok: bool = False,
    pid: int | None = None,
    error: str = "",
) -> dict[str, object]:
    return {
        "attempted": attempted,
        "ok": ok,
        "pid": pid,
        "error": error,
    }


class LifecycleTracker:
    def __init__(
        self,
        *,
        out_path: Path,
        candidate_hex: str,
        target: Path,
        hook_points: dict[str, object],
    ) -> None:
        self.out_path = out_path
        self.candidate_hex = candidate_hex
        self.target = target
        self.hook_points = hook_points
        self.stages: list[dict[str, object]] = []
        self.last_confirmed_stage = ""
        self.last_error_stage = ""
        self.last_error = ""
        self.ui_trigger: dict[str, object] = _empty_ui_trigger_diagnostics()
        self.window_discovery: dict[str, object] = _empty_window_discovery_diagnostics()

    def confirm(self, stage: str, **fields: object) -> None:
        self.last_confirmed_stage = stage
        event: dict[str, object] = {
            "stage": stage,
            "status": "confirmed",
            "monotonic": _now_monotonic(),
        }
        event.update(fields)
        self.stages.append(event)
        self.write_checkpoint()

    def fail(self, stage: str, error: str, **fields: object) -> None:
        self.last_error_stage = stage
        self.last_error = error
        event: dict[str, object] = {
            "stage": stage,
            "status": "failed",
            "error": error,
            "monotonic": _now_monotonic(),
        }
        event.update(fields)
        self.stages.append(event)
        self.write_checkpoint(classification=_classification_for_failed_stage(stage))

    def ui_checkpoint(self, stage: str, **fields: object) -> None:
        self.ui_trigger["last_ui_stage"] = stage
        event: dict[str, object] = {
            "stage": stage,
            "status": "confirmed",
            "monotonic": _now_monotonic(),
        }
        event.update(fields)
        events = self.ui_trigger.setdefault("events", [])
        if isinstance(events, list):
            events.append(event)
        self.write_checkpoint(classification=_classification_from_ui_trigger(self.ui_trigger))

    def ui_fail(self, stage: str, error: str, **fields: object) -> None:
        self.ui_trigger["last_ui_stage"] = stage
        self.ui_trigger["error"] = error
        event: dict[str, object] = {
            "stage": stage,
            "status": "failed",
            "error": error,
            "monotonic": _now_monotonic(),
        }
        event.update(fields)
        events = self.ui_trigger.setdefault("events", [])
        if isinstance(events, list):
            events.append(event)
        self.write_checkpoint(classification=_classification_from_ui_trigger(self.ui_trigger))

    def update_ui(self, section: str, values: dict[str, object]) -> None:
        current = self.ui_trigger.get(section, {})
        current = dict(current) if isinstance(current, dict) else {}
        current.update(values)
        self.ui_trigger[section] = current

    def window_checkpoint(self, stage: str, **fields: object) -> None:
        self.window_discovery["last_window_stage"] = stage
        event: dict[str, object] = {
            "stage": stage,
            "status": "confirmed",
            "monotonic": _now_monotonic(),
        }
        event.update(fields)
        events = self.window_discovery.setdefault("events", [])
        if isinstance(events, list):
            events.append(event)
        self.write_checkpoint(classification=_classification_from_window_discovery(self.window_discovery))

    def window_fail(self, stage: str, error: str, **fields: object) -> None:
        self.window_discovery["last_window_stage"] = stage
        self.window_discovery["error"] = error
        event: dict[str, object] = {
            "stage": stage,
            "status": "failed",
            "error": error,
            "monotonic": _now_monotonic(),
        }
        event.update(fields)
        events = self.window_discovery.setdefault("events", [])
        if isinstance(events, list):
            events.append(event)
        self.write_checkpoint(classification=_classification_from_window_discovery(self.window_discovery))

    def update_window(self, section: str, values: dict[str, object]) -> None:
        current = self.window_discovery.get(section, {})
        current = dict(current) if isinstance(current, dict) else {}
        current.update(values)
        self.window_discovery[section] = current

    def lifecycle(self, *, timeout_stage: str = "") -> dict[str, object]:
        return {
            "last_confirmed_stage": self.last_confirmed_stage,
            "last_error_stage": self.last_error_stage,
            "last_error": self.last_error,
            "timeout_stage": timeout_stage,
            "stages": list(self.stages),
        }

    def write_checkpoint(
        self,
        *,
        classification: str = "lifecycle_checkpoint",
        target_launch: dict[str, object] | None = None,
        breakpoints: list[dict[str, object]] | None = None,
        event_sequence: list[dict[str, object]] | None = None,
        backend_import_ok: bool = False,
        backend_error: str = "",
        error: str = "",
    ) -> None:
        payload = _blocked_payload(
            candidate_hex=self.candidate_hex,
            target=self.target,
            hook_points=self.hook_points,
            classification=classification,
            target_launch=target_launch,
            breakpoints=breakpoints,
            event_sequence=event_sequence,
            backend_import_ok=backend_import_ok,
            backend_error=backend_error,
            error=error,
            lifecycle=self.lifecycle(),
            ui_trigger=self.ui_trigger,
            window_discovery=self.window_discovery,
        )
        _write_payload(self.out_path, payload)


def _classification_for_failed_stage(stage: str) -> str:
    return {
        "target_checked": "target_missing_or_unlaunchable",
        "dependency_import_failed": "debugger_dependency_missing",
        "frida_spawn_failed": "frida_spawn_failed",
        "frida_attach_failed": "frida_attach_failed",
        "script_create_failed": "script_create_or_load_failed",
        "script_load_failed": "script_create_or_load_failed",
        "breakpoint_install_failed": "breakpoint_install_failed",
        "frida_resume_failed": "frida_resume_failed",
        "ui_connect_failed": "ui_connect_failed",
        "ui_trigger_failed": "ui_trigger_failed",
        "window_discovery_failed": "window_discovery_failed",
        "input_control_lookup_failed": "input_control_lookup_failed",
        "input_set_text_failed": "input_set_text_failed",
        "input_value_not_confirmed": "input_value_not_confirmed",
        "button_control_lookup_failed": "button_control_lookup_failed",
        "button_disabled_or_invisible": "button_disabled_or_invisible",
        "button_action_failed": "button_action_failed",
        "final_artifact_write_failed": "candidate_artifact_write_failed",
    }.get(stage, "instrumentation_gap_but_environment_verified")


def _empty_ui_trigger_diagnostics() -> dict[str, object]:
    return {
        "last_ui_stage": "",
        "timeout_stage": "",
        "classification": "",
        "error": "",
        "window": {
            "discovered": False,
            "title": "",
            "class_name": "",
            "handle": "",
        },
        "input_control": {
            "lookup_attempted": False,
            "lookup_ok": False,
            "set_text_attempted": False,
            "set_text_ok": False,
            "value_confirm_attempted": False,
            "value_confirmed": False,
        },
        "button_control": {
            "lookup_attempted": False,
            "lookup_ok": False,
            "enabled": False,
            "visible": False,
        },
        "trigger_methods": [],
        "post_trigger_observation": {
            "entry_breakpoint_hit": False,
            "successor_breakpoint_hit": False,
            "observed_events": [],
        },
        "events": [],
    }


def _empty_window_discovery_diagnostics() -> dict[str, object]:
    return {
        "classification": "",
        "last_window_stage": "",
        "timeout_stage": "",
        "error": "",
        "process_liveness": {
            "pid": None,
            "alive": False,
            "error": "",
        },
        "app_connection": {
            "attempted": False,
            "ok": False,
            "error": "",
        },
        "top_window": {
            "attempted": False,
            "returned": False,
            "duration_ms": 0,
            "error": "",
            "title": "",
            "class_name": "",
            "handle": "",
        },
        "window_inventory": {
            "attempted": False,
            "returned": False,
            "duration_ms": 0,
            "error": "",
            "window_count": 0,
            "visible_window_count": 0,
            "candidate_windows": [],
        },
        "api_attribution": {
            "pywinauto_win32": _empty_backend_window_probe("pywinauto_win32"),
            "pywinauto_uia": _empty_backend_window_probe("pywinauto_uia"),
            "direct_enum_windows": _empty_backend_window_probe("direct_enum_windows"),
            "direct_enum_child_windows": _empty_backend_window_probe(
                "direct_enum_child_windows"
            ),
            "process_exit_code": "",
            "final_window_discovery_reason": "",
        },
        "selected_window": {
            "available": False,
            "title": "",
            "class_name": "",
            "handle": "",
            "backend": "",
            "owned_by_pid": False,
        },
        "events": [],
    }


def _empty_backend_window_probe(backend: str) -> dict[str, object]:
    return {
        "backend": backend,
        "attempted": False,
        "returned": False,
        "duration_ms": 0,
        "error": "",
        "window_count": 0,
        "visible_window_count": 0,
        "owned_window_count": 0,
        "candidate_windows": [],
    }


def _window_api_attribution(window_discovery: dict[str, object]) -> dict[str, object]:
    attribution = window_discovery.get("api_attribution", {})
    return attribution if isinstance(attribution, dict) else {}


def _backend_probe(
    attribution: dict[str, object],
    backend: str,
) -> dict[str, object]:
    probe = attribution.get(backend, {})
    return probe if isinstance(probe, dict) else {}


def _classify_window_api_attribution(window_discovery: dict[str, object]) -> str:
    attribution = _window_api_attribution(window_discovery)
    if not attribution:
        return ""
    selected_window = window_discovery.get("selected_window", {})
    selected_window = selected_window if isinstance(selected_window, dict) else {}
    if bool(selected_window.get("available")):
        return "window_discovery_succeeded_input_lookup_next"

    win32 = _backend_probe(attribution, "pywinauto_win32")
    uia = _backend_probe(attribution, "pywinauto_uia")
    enum_windows = _backend_probe(attribution, "direct_enum_windows")
    direct_returned = bool(enum_windows.get("returned"))
    direct_owned = int(enum_windows.get("owned_window_count") or 0)
    direct_visible = int(enum_windows.get("visible_window_count") or 0)
    direct_count = int(enum_windows.get("window_count") or 0)
    win32_returned = bool(win32.get("returned"))
    win32_count = int(win32.get("window_count") or 0)
    uia_returned = bool(uia.get("returned"))
    uia_count = int(uia.get("window_count") or 0)

    if direct_returned and direct_owned > 0 and direct_visible > 0 and not (
        win32_returned or uia_returned
    ):
        return "win32_enum_windows_succeeded_pywinauto_failed"
    if uia_returned and uia_count > 0 and not (win32_returned and win32_count > 0):
        return "uia_backend_succeeded_win32_failed"
    if (win32_returned and win32_count > 0) != (uia_returned and uia_count > 0):
        return "window_backend_mismatch"
    if direct_returned and direct_owned > 0 and direct_visible <= 0:
        return "window_exists_but_not_visible"
    if direct_returned and direct_count <= 0:
        return "win32_enum_windows_empty"
    if direct_returned and direct_owned <= 0:
        return "pid_alive_but_no_owned_window"
    if any(bool(_backend_probe(attribution, key).get("attempted")) for key in attribution):
        return "window_discovery_instrumentation_gap"
    return ""


def _classification_from_window_discovery(window_discovery: dict[str, object]) -> str:
    classification = str(window_discovery.get("classification") or "")
    if classification and classification != "lifecycle_checkpoint":
        return classification
    attribution_classification = _classify_window_api_attribution(window_discovery)
    if attribution_classification:
        return attribution_classification
    stage = str(window_discovery.get("last_window_stage") or "")
    process_liveness = window_discovery.get("process_liveness", {})
    process_liveness = process_liveness if isinstance(process_liveness, dict) else {}
    top_window = window_discovery.get("top_window", {})
    top_window = top_window if isinstance(top_window, dict) else {}
    inventory = window_discovery.get("window_inventory", {})
    inventory = inventory if isinstance(inventory, dict) else {}
    selected_window = window_discovery.get("selected_window", {})
    selected_window = selected_window if isinstance(selected_window, dict) else {}
    if process_liveness.get("alive") is False and stage in {
        "process_liveness_checked",
        "window_discovery_finished",
    }:
        return "window_lifecycle_no_window_created"
    if stage == "top_window_timeout":
        return "top_window_call_timeout"
    if stage == "top_window_failed":
        return "top_window_call_failed"
    if stage == "window_inventory_failed":
        return "window_discovery_instrumentation_gap"
    if stage == "window_inventory_timeout":
        return "window_discovery_instrumentation_gap"
    if bool(inventory.get("attempted")) and not bool(inventory.get("returned")):
        return "window_discovery_instrumentation_gap"
    if bool(top_window.get("attempted")) and not bool(top_window.get("returned")):
        return "top_window_call_timeout" if str(top_window.get("error") or "") == "timeout" else "top_window_call_failed"
    if stage == "window_inventory_captured":
        if int(inventory.get("window_count") or 0) <= 0:
            return "pid_alive_but_no_owned_window"
        if int(inventory.get("visible_window_count") or 0) <= 0:
            return "window_exists_but_not_visible"
    if stage == "primary_window_unavailable":
        if bool(top_window.get("attempted")) and not bool(top_window.get("returned")):
            return "pid_alive_but_no_owned_window"
        return "window_exists_but_not_visible"
    if stage == "primary_window_selected" or bool(selected_window.get("available")):
        return "window_discovery_succeeded_input_lookup_next"
    if stage:
        return "window_discovery_instrumentation_gap"
    return ""


def _classification_from_ui_trigger(ui_trigger: dict[str, object]) -> str:
    stage = str(ui_trigger.get("last_ui_stage") or "")
    error = str(ui_trigger.get("error") or "")
    if not stage:
        return "ui_trigger_instrumentation_gap"
    if stage in {"ui_window_discovery_attempted"}:
        return "window_discovery_timeout"
    if stage in {"ui_window_discovery_failed"}:
        return "window_discovery_failed"
    if stage in {"ui_input_lookup_attempted"}:
        return "input_control_lookup_timeout"
    if stage in {"ui_input_lookup_failed"}:
        return "input_control_lookup_failed"
    if stage in {"ui_input_set_text_attempted"}:
        return "input_set_text_timeout"
    if stage in {"ui_input_set_text_failed"}:
        return "input_set_text_failed"
    if stage in {"ui_input_value_confirm_attempted"}:
        return "input_value_not_confirmed"
    if stage in {"ui_input_value_confirm_failed"}:
        return "input_value_not_confirmed"
    if stage in {"ui_button_lookup_attempted"}:
        return "button_control_lookup_timeout"
    if stage in {"ui_button_lookup_failed"}:
        return "button_control_lookup_failed"
    if stage == "ui_button_state_checked":
        button = ui_trigger.get("button_control", {})
        button = button if isinstance(button, dict) else {}
        if button.get("enabled") is False or button.get("visible") is False:
            return "button_disabled_or_invisible"
    if stage in {"ui_button_invoke_attempted", "ui_button_trigger_method_selected"}:
        return "button_invoke_timeout"
    if stage == "ui_button_invoke_failed":
        return "button_invoke_failed"
    if stage == "ui_button_click_attempted":
        return "button_click_timeout"
    if stage == "ui_button_click_failed":
        return "button_click_failed"
    if stage == "ui_trigger_returned":
        return "button_action_returned_no_entry_hit"
    if stage == "post_trigger_observation_wait_started":
        return "post_trigger_observation_timeout"
    if stage == "post_trigger_observation_timeout":
        return "post_trigger_observation_timeout"
    if stage == "entry_breakpoint_not_hit_after_ui_trigger":
        return "entry_breakpoint_not_hit_after_ui_trigger"
    if stage == "successor_breakpoint_not_hit_after_ui_trigger":
        return "successor_breakpoint_not_hit_after_ui_trigger"
    if stage == "post_entry_breakpoint_observed_after_ui_trigger":
        return "post_entry_breakpoint_observed_after_ui_trigger"
    if error:
        return "ui_trigger_failed"
    return "ui_trigger_instrumentation_gap"


def _environment(
    *,
    target: Path,
    backend_import_ok: bool = False,
    backend_error: str = "",
) -> dict[str, object]:
    return {
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "debugger_backend": "frida",
        "backend_import_ok": backend_import_ok,
        "backend_error": backend_error,
        "target_executable_exists": target.exists(),
    }


def _breakpoint_records(
    hook_points: dict[str, object],
    installed: list[dict[str, object]] | None = None,
    hits: list[dict[str, object]] | None = None,
    install_errors: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    installed = installed or []
    hits = hits or []
    install_errors = install_errors or []
    installed_by_name = {
        str(item.get("name") or ""): item for item in installed if isinstance(item, dict)
    }
    first_hit_by_name: dict[str, dict[str, object]] = {}
    for event in hits:
        name = str(event.get("name") or "")
        if name and name not in first_hit_by_name:
            first_hit_by_name[name] = event
    error_by_name = {
        str(item.get("name") or ""): str(item.get("error") or "")
        for item in install_errors
        if isinstance(item, dict)
    }
    records: list[dict[str, object]] = []
    for point in _breakpoint_plan(hook_points):
        name = str(point["name"])
        install = installed_by_name.get(name, {})
        hit = first_hit_by_name.get(name, {})
        records.append(
            {
                "name": name,
                "module_offset": str(point["module_offset"]),
                "install_attempted": True,
                "install_ok": bool(install.get("ok")),
                "hit": bool(hit),
                "hit_order": hit.get("hit_order"),
                "eip": str(hit.get("eip") or ""),
                "error": error_by_name.get(name, str(install.get("error") or "")),
            }
        )
    return records


def _empty_breakpoint_records(hook_points: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "name": str(point["name"]),
            "module_offset": str(point["module_offset"]),
            "install_attempted": False,
            "install_ok": False,
            "hit": False,
            "hit_order": None,
            "eip": "",
            "error": "",
        }
        for point in _breakpoint_plan(hook_points)
    ]


def _blocked_payload(
    *,
    candidate_hex: str,
    target: Path,
    hook_points: dict[str, object],
    classification: str,
    target_launch: dict[str, object] | None = None,
    breakpoints: list[dict[str, object]] | None = None,
    event_sequence: list[dict[str, object]] | None = None,
    backend_import_ok: bool = False,
    backend_error: str = "",
    error: str = "",
    lifecycle: dict[str, object] | None = None,
    ui_trigger: dict[str, object] | None = None,
    window_discovery: dict[str, object] | None = None,
    candidate_invocation_health: dict[str, object] | None = None,
) -> dict[str, object]:
    event_sequence = event_sequence or []
    breakpoints = breakpoints if isinstance(breakpoints, list) else _empty_breakpoint_records(hook_points)
    hit_names = {str(event.get("name") or "") for event in event_sequence}
    lifecycle = lifecycle if isinstance(lifecycle, dict) else {}
    ui_trigger = ui_trigger if isinstance(ui_trigger, dict) else _empty_ui_trigger_diagnostics()
    ui_trigger = dict(ui_trigger)
    ui_trigger["classification"] = str(
        ui_trigger.get("classification") or _classification_from_ui_trigger(ui_trigger)
    )
    window_discovery = (
        window_discovery
        if isinstance(window_discovery, dict)
        else _empty_window_discovery_diagnostics()
    )
    window_discovery = dict(window_discovery)
    window_discovery["classification"] = str(
        window_discovery.get("classification")
        or _classification_from_window_discovery(window_discovery)
    )
    candidate_invocation_health = (
        candidate_invocation_health if isinstance(candidate_invocation_health, dict) else {}
    )
    return {
        "schema_version": 1,
        "artifact_kind": "compare_handoff_narrower_post_entry_breakpoint_audit",
        "sample": "samplereverse",
        "success": False,
        "candidate_hex": candidate_hex,
        "lifecycle_schema_version": 1,
        "environment_diagnostics": _environment(
            target=target,
            backend_import_ok=backend_import_ok,
            backend_error=backend_error,
        ),
        "runtime_scope": {
            "mode": "narrower_post_entry_breakpoint",
            "debugger_backend": "frida",
            "single_step_required": False,
            "breakpoint_probe_allowed": False,
            "material_capture_allowed": False,
            "crypto_hook_allowed": False,
        },
        "breakpoint_plan": _breakpoint_plan(hook_points),
        "target_launch": target_launch or _target_launch(),
        "breakpoints": breakpoints,
        "event_sequence": event_sequence,
        "handoff_helper_entry_observed": "handoff_helper_entry" in hit_names,
        "successor_surface_observed": bool(hit_names.intersection({"process_exception", "actual_compare"})),
        "process_exception_observed": "process_exception" in hit_names,
        "compare_successor_observed": "actual_compare" in hit_names,
        "actual_compare_observed": "actual_compare" in hit_names,
        "classification": classification,
        "error": error,
        "lifecycle": lifecycle,
        "ui_trigger_schema_version": 1,
        "ui_trigger": ui_trigger,
        "window_discovery_schema_version": 1,
        "window_discovery": window_discovery,
        "candidate_invocation_health": candidate_invocation_health,
        "breakpoint_probe_allowed": False,
        "material_capture_allowed": False,
        "crypto_hook_allowed": False,
    }


def _classify(
    *,
    launch_ok: bool,
    breakpoints: list[dict[str, object]],
    events: list[dict[str, object]],
    runtime_error: str = "",
) -> str:
    if not launch_ok:
        return "frida_attach_or_spawn_failed"
    if any(not bool(item.get("install_ok")) for item in breakpoints):
        return "breakpoint_install_failed"
    hit_names = {str(event.get("name") or "") for event in events}
    if not hit_names.intersection({"predecessor_handoff_call", "handoff_helper_entry"}):
        return "entry_breakpoint_not_hit"
    if "handoff_helper_entry" in hit_names and not hit_names.intersection(
        {"process_exception", "actual_compare"}
    ):
        return "successor_breakpoint_not_hit"
    if hit_names.intersection({"process_exception", "actual_compare"}):
        return "post_entry_breakpoint_observed"
    if runtime_error:
        return "instrumentation_gap_but_environment_verified"
    return "entry_breakpoint_not_hit"


def _control_text(control) -> str:  # noqa: ANN001
    for attr in ("window_text", "texts"):
        try:
            value = getattr(control, attr)
            value = value() if callable(value) else value
            if isinstance(value, list):
                return " ".join(str(item) for item in value)
            if value is not None:
                return str(value)
        except Exception:
            continue
    return ""


def _control_metadata(control) -> dict[str, object]:  # noqa: ANN001
    info = getattr(control, "element_info", None)
    handle = ""
    class_name = ""
    try:
        handle = str(getattr(info, "handle", "") or getattr(control, "handle", "") or "")
    except Exception:
        handle = ""
    try:
        class_name = str(getattr(info, "class_name", "") or control.class_name())
    except Exception:
        class_name = str(getattr(info, "class_name", "") or "")
    return {
        "title": _control_text(control),
        "class_name": class_name,
        "handle": handle,
    }


def _window_metadata(control) -> dict[str, object]:  # noqa: ANN001
    metadata = _control_metadata(control)
    try:
        rect = control.rectangle()
        rectangle = {
            "left": int(getattr(rect, "left", 0)),
            "top": int(getattr(rect, "top", 0)),
            "right": int(getattr(rect, "right", 0)),
            "bottom": int(getattr(rect, "bottom", 0)),
        }
    except Exception:
        rectangle = {}
    metadata.update(
        {
            "visible": _control_bool(control, "is_visible"),
            "enabled": _control_bool(control, "is_enabled"),
            "rectangle": rectangle,
        }
    )
    return metadata


def _pid_alive(pid: int | None) -> tuple[bool, str]:
    if pid is None:
        return False, "pid missing"
    if platform.system().lower().startswith("win"):
        try:
            import ctypes

            synchronize = 0x00100000
            still_active_timeout_ms = 0
            wait_timeout = 0x00000102
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(synchronize, False, int(pid))
            if not handle:
                return False, "OpenProcess failed"
            try:
                status = kernel32.WaitForSingleObject(handle, still_active_timeout_ms)
                return status == wait_timeout, ""
            finally:
                kernel32.CloseHandle(handle)
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"
    try:
        import os

        os.kill(pid, 0)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _call_with_timeout(func, timeout: float) -> tuple[bool, object, str, int]:  # noqa: ANN001
    result: dict[str, object] = {"returned": False, "value": None, "error": ""}

    def runner() -> None:
        try:
            result["value"] = func()
            result["returned"] = True
        except Exception as exc:  # pragma: no cover - depends on local GUI runtime
            result["error"] = f"{type(exc).__name__}: {exc}"
            result["returned"] = True

    start = time.monotonic()
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(max(0.1, float(timeout)))
    duration_ms = int((time.monotonic() - start) * 1000)
    if thread.is_alive():
        return False, None, "timeout", duration_ms
    return bool(result["returned"]) and not result["error"], result["value"], str(result["error"]), duration_ms


def _get_process_exit_code(pid: int | None) -> str:
    if pid is None or not platform.system().lower().startswith("win"):
        return ""
    try:
        process_query_limited_information = 0x1000
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(process_query_limited_information, False, int(pid))
        if not handle:
            return "OpenProcess failed"
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return "GetExitCodeProcess failed"
            if int(code.value) == 259:
                return "STILL_ACTIVE"
            return str(int(code.value))
        finally:
            kernel32.CloseHandle(handle)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def _probe_from_windows(
    *,
    backend: str,
    attempted: bool,
    returned: bool,
    duration_ms: int,
    error: str,
    windows: list[object],
    pid: int | None,
) -> dict[str, object]:
    candidate_windows = []
    for win in windows[:10]:
        metadata = _window_metadata(win)
        metadata["backend"] = backend
        metadata["owned_by_pid"] = bool(pid)
        candidate_windows.append(metadata)
    visible_count = sum(1 for item in candidate_windows if bool(item.get("visible")))
    return {
        "backend": backend,
        "attempted": attempted,
        "returned": returned,
        "duration_ms": duration_ms,
        "error": error,
        "window_count": len(windows),
        "visible_window_count": visible_count,
        "owned_window_count": len(windows) if pid is not None else 0,
        "candidate_windows": candidate_windows,
    }


def _probe_pywinauto_backend(application_cls, pid: int | None, backend: str) -> tuple[dict[str, object], object | None]:  # noqa: ANN001
    start = time.monotonic()
    if pid is None:
        return {**_empty_backend_window_probe(f"pywinauto_{backend}"), "attempted": True, "error": "pid missing"}, None
    selected = None
    try:
        app = application_cls(backend=backend).connect(process=pid)
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            **_empty_backend_window_probe(f"pywinauto_{backend}"),
            "attempted": True,
            "duration_ms": duration_ms,
            "error": f"{type(exc).__name__}: {exc}",
        }, None
    top_ok, top_value, top_error, _top_duration = _call_with_timeout(
        app.top_window,
        min(0.6, max(0.2, 0.25)),
    )
    if top_ok and top_value is not None:
        selected = top_value
    inv_ok, inv_value, inv_error, _inv_duration = _call_with_timeout(
        app.windows,
        min(0.8, max(0.2, 0.35)),
    )
    windows = list(inv_value) if inv_ok and isinstance(inv_value, list) else []
    if selected is not None and selected not in windows:
        windows.insert(0, selected)
    duration_ms = int((time.monotonic() - start) * 1000)
    returned = bool((top_ok and selected is not None) or inv_ok)
    error = "" if returned else (inv_error or top_error)
    return _probe_from_windows(
        backend=f"pywinauto_{backend}",
        attempted=True,
        returned=returned,
        duration_ms=duration_ms,
        error=error,
        windows=windows,
        pid=pid,
    ), selected


def _direct_window_metadata(hwnd: int, pid: int | None, backend: str) -> dict[str, object]:
    user32 = ctypes.windll.user32
    length = int(user32.GetWindowTextLengthW(hwnd))
    buffer = ctypes.create_unicode_buffer(max(length + 1, 1))
    if length > 0:
        user32.GetWindowTextW(hwnd, buffer, len(buffer))
    class_buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, class_buffer, len(class_buffer))
    owner_pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner_pid))
    owned_by_pid = pid is not None and int(owner_pid.value) == int(pid)
    return {
        "backend": backend,
        "handle": str(int(hwnd)),
        "title": str(buffer.value or ""),
        "class_name": str(class_buffer.value or ""),
        "visible": bool(user32.IsWindowVisible(hwnd)),
        "enabled": bool(user32.IsWindowEnabled(hwnd)),
        "owned_by_pid": owned_by_pid,
    }


def _probe_direct_enum_windows(pid: int | None) -> dict[str, object]:
    backend = "direct_enum_windows"
    start = time.monotonic()
    if not platform.system().lower().startswith("win"):
        return {
            **_empty_backend_window_probe(backend),
            "attempted": True,
            "error": "direct EnumWindows unavailable on non-Windows platform",
        }
    windows: list[dict[str, object]] = []
    try:
        user32 = ctypes.windll.user32
        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def callback(hwnd, _lparam):  # noqa: ANN001
            metadata = _direct_window_metadata(int(hwnd), pid, backend)
            if metadata["owned_by_pid"]:
                windows.append(metadata)
            return True

        if not user32.EnumWindows(enum_proc(callback), 0):
            error = "EnumWindows failed"
            returned = False
        else:
            error = ""
            returned = True
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        returned = False
    duration_ms = int((time.monotonic() - start) * 1000)
    visible_count = sum(1 for item in windows if bool(item.get("visible")))
    return {
        "backend": backend,
        "attempted": True,
        "returned": returned,
        "duration_ms": duration_ms,
        "error": error,
        "window_count": len(windows),
        "visible_window_count": visible_count,
        "owned_window_count": len(windows),
        "candidate_windows": windows[:10],
    }


def _probe_direct_enum_child_windows(pid: int | None, parent_handles: list[int]) -> dict[str, object]:
    backend = "direct_enum_child_windows"
    start = time.monotonic()
    if not platform.system().lower().startswith("win"):
        return {
            **_empty_backend_window_probe(backend),
            "attempted": True,
            "error": "direct EnumChildWindows unavailable on non-Windows platform",
        }
    windows: list[dict[str, object]] = []
    try:
        user32 = ctypes.windll.user32
        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def callback(hwnd, _lparam):  # noqa: ANN001
            metadata = _direct_window_metadata(int(hwnd), pid, backend)
            if metadata["owned_by_pid"]:
                windows.append(metadata)
            return True

        for handle in parent_handles[:10]:
            user32.EnumChildWindows(int(handle), enum_proc(callback), 0)
        returned = True
        error = ""
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        returned = False
    duration_ms = int((time.monotonic() - start) * 1000)
    visible_count = sum(1 for item in windows if bool(item.get("visible")))
    return {
        "backend": backend,
        "attempted": True,
        "returned": returned,
        "duration_ms": duration_ms,
        "error": error,
        "window_count": len(windows),
        "visible_window_count": visible_count,
        "owned_window_count": len(windows),
        "candidate_windows": windows[:10],
    }


def _record_window_api_attribution(
    lifecycle: LifecycleTracker,
    application_cls,  # noqa: ANN001
    pid: int | None,
) -> object | None:
    attribution = _window_api_attribution(lifecycle.window_discovery)
    attribution = dict(attribution) if attribution else {}
    attribution["process_exit_code"] = _get_process_exit_code(pid)

    win32_probe, win32_selected = _probe_pywinauto_backend(application_cls, pid, "win32")
    lifecycle.window_checkpoint("pywinauto_win32_window_probe_finished")
    uia_probe, uia_selected = _probe_pywinauto_backend(application_cls, pid, "uia")
    lifecycle.window_checkpoint("pywinauto_uia_window_probe_finished")
    direct_probe = _probe_direct_enum_windows(pid)
    lifecycle.window_checkpoint("direct_enum_windows_finished")
    parent_handles = [
        int(str(item.get("handle") or "0"))
        for item in direct_probe.get("candidate_windows", [])
        if isinstance(item, dict) and str(item.get("handle") or "").isdigit()
    ]
    child_probe = _probe_direct_enum_child_windows(pid, parent_handles)
    lifecycle.window_checkpoint("direct_enum_child_windows_finished")

    attribution.update(
        {
            "pywinauto_win32": win32_probe,
            "pywinauto_uia": uia_probe,
            "direct_enum_windows": direct_probe,
            "direct_enum_child_windows": child_probe,
        }
    )
    lifecycle.window_discovery["api_attribution"] = attribution
    selected = uia_selected or win32_selected
    if selected is not None:
        metadata = _window_metadata(selected)
        metadata["backend"] = "pywinauto_uia" if uia_selected is not None else "pywinauto_win32"
        metadata["owned_by_pid"] = pid is not None
        lifecycle.update_window("selected_window", {"available": True, **metadata})
    final_reason = _classification_from_window_discovery(lifecycle.window_discovery)
    attribution["final_window_discovery_reason"] = final_reason
    lifecycle.window_discovery["classification"] = final_reason
    lifecycle.write_checkpoint(classification=final_reason)
    return selected


def _discover_window(app, pid: int | None, lifecycle: LifecycleTracker, application_cls=None):  # noqa: ANN001
    lifecycle.window_checkpoint("window_discovery_started")
    alive, liveness_error = _pid_alive(pid)
    lifecycle.update_window(
        "process_liveness",
        {"pid": pid, "alive": alive, "error": liveness_error},
    )
    lifecycle.window_checkpoint("process_liveness_checked", pid=pid, alive=alive)
    if not alive:
        attribution = _window_api_attribution(lifecycle.window_discovery)
        attribution = dict(attribution) if attribution else {}
        attribution["process_exit_code"] = _get_process_exit_code(pid)
        attribution["final_window_discovery_reason"] = "window_lifecycle_no_window_created"
        lifecycle.window_discovery["api_attribution"] = attribution
        lifecycle.window_discovery["classification"] = "window_lifecycle_no_window_created"
        lifecycle.window_checkpoint("window_discovery_finished")
        raise RuntimeError("process exited before window discovery")

    lifecycle.update_window("app_connection", {"attempted": True, "ok": bool(app), "error": ""})
    lifecycle.window_checkpoint("app_connection_rechecked", ok=bool(app))
    attributed_selected = None
    if application_cls is not None:
        attributed_selected = _record_window_api_attribution(lifecycle, application_cls, pid)
    if attributed_selected is not None:
        lifecycle.update_ui("window", {"discovered": True, **_control_metadata(attributed_selected)})
        lifecycle.window_checkpoint("primary_window_selected", method="window_api_attribution")
        lifecycle.window_checkpoint("window_discovery_finished")
        lifecycle.ui_checkpoint("ui_window_discovery_ok", method="window_api_attribution")
        return attributed_selected

    lifecycle.update_window("top_window", {"attempted": True})
    lifecycle.ui_checkpoint("ui_window_discovery_attempted", method="app.top_window")
    lifecycle.window_checkpoint("top_window_attempted", method="app.top_window")
    top_ok, top_value, top_error, top_duration = _call_with_timeout(
        app.top_window,
        min(0.6, max(0.2, 0.25)),
    )
    lifecycle.update_window(
        "top_window",
        {
            "attempted": True,
            "returned": top_ok,
            "duration_ms": top_duration,
            "error": "" if top_ok else top_error,
            **(_window_metadata(top_value) if top_ok and top_value is not None else {}),
        },
    )
    if top_ok and top_value is not None:
        metadata = _window_metadata(top_value)
        metadata["backend"] = "pywinauto_uia"
        metadata["owned_by_pid"] = pid is not None
        lifecycle.update_window(
            "selected_window",
            {"available": True, **metadata},
        )
        lifecycle.update_ui("window", {"discovered": True, **_control_metadata(top_value)})
        lifecycle.window_checkpoint("top_window_returned", duration_ms=top_duration)
        lifecycle.window_checkpoint("primary_window_selected", method="app.top_window")
        lifecycle.window_checkpoint("window_discovery_finished")
        lifecycle.ui_checkpoint("ui_window_discovery_ok", method="app.top_window")
        return top_value
    if top_error == "timeout":
        lifecycle.window_checkpoint("top_window_timeout", duration_ms=top_duration)
    else:
        lifecycle.window_fail("top_window_failed", top_error or "app.top_window returned no window")

    lifecycle.update_window("window_inventory", {"attempted": True})
    lifecycle.window_checkpoint("window_inventory_attempted", method="app.windows")
    inv_ok, inv_value, inv_error, inv_duration = _call_with_timeout(
        app.windows,
        min(0.8, max(0.2, 0.35)),
    )
    windows = list(inv_value) if inv_ok and isinstance(inv_value, list) else []
    candidate_windows = [_window_metadata(win) for win in windows[:10]]
    visible_windows = [item for item in candidate_windows if bool(item.get("visible"))]
    lifecycle.update_window(
        "window_inventory",
        {
            "attempted": True,
            "returned": inv_ok,
            "duration_ms": inv_duration,
            "error": "" if inv_ok else inv_error,
            "window_count": len(windows),
            "visible_window_count": len(visible_windows),
            "candidate_windows": candidate_windows,
        },
    )
    if not inv_ok:
        stage = "window_inventory_timeout" if inv_error == "timeout" else "window_inventory_failed"
        lifecycle.window_fail(stage, inv_error or "window inventory failed", duration_ms=inv_duration)
        lifecycle.window_checkpoint("window_discovery_finished")
        lifecycle.window_discovery["classification"] = _classification_from_window_discovery(
            lifecycle.window_discovery
        )
        raise RuntimeError(inv_error or "window inventory failed")
    lifecycle.window_checkpoint(
        "window_inventory_captured",
        window_count=len(windows),
        visible_window_count=len(visible_windows),
    )
    lifecycle.window_checkpoint("visible_window_filter_applied", visible_window_count=len(visible_windows))
    if not windows:
        lifecycle.window_checkpoint("primary_window_unavailable", reason="inventory_empty")
        lifecycle.window_checkpoint("window_discovery_finished")
        lifecycle.window_discovery["classification"] = _classification_from_window_discovery(
            lifecycle.window_discovery
        )
        raise RuntimeError("process window inventory empty")
    selected = None
    for win in windows:
        if _control_bool(win, "is_visible"):
            selected = win
            break
    if selected is None:
        lifecycle.window_checkpoint("primary_window_unavailable", reason="no_visible_window")
        lifecycle.window_checkpoint("window_discovery_finished")
        lifecycle.window_discovery["classification"] = _classification_from_window_discovery(
            lifecycle.window_discovery
        )
        raise RuntimeError("process has no visible window")
    metadata = _window_metadata(selected)
    metadata["backend"] = "pywinauto_uia"
    metadata["owned_by_pid"] = pid is not None
    lifecycle.update_window("selected_window", {"available": True, **metadata})
    lifecycle.update_ui("window", {"discovered": True, **_control_metadata(selected)})
    lifecycle.window_checkpoint("primary_window_selected", method="app.windows")
    lifecycle.window_checkpoint("window_discovery_finished")
    lifecycle.ui_checkpoint("ui_window_discovery_ok", method="app.windows")
    return selected


def _control_bool(control, method_name: str) -> bool:  # noqa: ANN001
    try:
        method = getattr(control, method_name)
        return bool(method())
    except Exception:
        return False


def _trigger_method_record(method: str) -> dict[str, object]:
    return {
        "method": method,
        "attempted": True,
        "returned": False,
        "duration_ms": 0,
        "error": "",
    }


def _record_trigger_method(
    lifecycle: LifecycleTracker,
    record: dict[str, object],
) -> None:
    methods = lifecycle.ui_trigger.get("trigger_methods", [])
    methods = list(methods) if isinstance(methods, list) else []
    methods.append(dict(record))
    lifecycle.ui_trigger["trigger_methods"] = methods


def _trigger_decrypt_with_ui_diagnostics(decrypt_btn, lifecycle: LifecycleTracker) -> None:  # noqa: ANN001
    lifecycle.ui_checkpoint("ui_button_trigger_method_selected", method="invoke")
    invoke = getattr(decrypt_btn, "invoke", None)
    if callable(invoke):
        record = _trigger_method_record("invoke")
        start = time.monotonic()
        lifecycle.ui_checkpoint("ui_button_invoke_attempted")
        try:
            invoke()
            record["returned"] = True
            record["duration_ms"] = int((time.monotonic() - start) * 1000)
            _record_trigger_method(lifecycle, record)
            lifecycle.ui_checkpoint("ui_button_invoke_returned", duration_ms=record["duration_ms"])
            return
        except Exception as exc:
            record["duration_ms"] = int((time.monotonic() - start) * 1000)
            record["error"] = f"{type(exc).__name__}: {exc}"
            _record_trigger_method(lifecycle, record)
            lifecycle.ui_checkpoint(
                "ui_button_invoke_failed",
                error=record["error"],
                duration_ms=record["duration_ms"],
            )

    click = getattr(decrypt_btn, "click_input", None)
    method_name = "click_input"
    if not callable(click):
        click = getattr(decrypt_btn, "click", None)
        method_name = "click"
    if not callable(click):
        lifecycle.ui_fail("ui_button_click_failed", "button has no callable click method")
        raise RuntimeError("button has no callable click method")
    record = _trigger_method_record(method_name)
    start = time.monotonic()
    lifecycle.ui_checkpoint("ui_button_click_attempted", method=method_name)
    try:
        click()
        record["returned"] = True
        record["duration_ms"] = int((time.monotonic() - start) * 1000)
        _record_trigger_method(lifecycle, record)
        lifecycle.ui_checkpoint("ui_button_click_returned", method=method_name, duration_ms=record["duration_ms"])
    except Exception as exc:
        record["duration_ms"] = int((time.monotonic() - start) * 1000)
        record["error"] = f"{type(exc).__name__}: {exc}"
        _record_trigger_method(lifecycle, record)
        lifecycle.ui_fail("ui_button_click_failed", str(record["error"]), method=method_name)
        raise


def _script_source(points: list[dict[str, object]]) -> str:
    return f"""
const points = {json.dumps(points)};
let hitOrder = 0;

function moduleOffset(addr) {{
  try {{
    const base = Process.enumerateModules()[0].base;
    return '0x' + ptr(addr).sub(base).toString(16);
  }} catch (e) {{
    return '';
  }}
}}

function installPoint(point) {{
  const module = Process.enumerateModules()[0];
  const address = module.base.add(ptr(point.module_offset));
  try {{
    Interceptor.attach(address, {{
      onEnter(args) {{
        hitOrder += 1;
        send({{
          type: 'hit',
          name: point.name,
          module_offset: point.module_offset,
          eip: this.context.eip ? this.context.eip.toString() : address.toString(),
          current_module_offset: moduleOffset(this.context.eip ? this.context.eip : address),
          hit_order: hitOrder
        }});
      }}
    }});
    send({{
      type: 'install',
      name: point.name,
      module_offset: point.module_offset,
      address: address.toString(),
      ok: true
    }});
  }} catch (e) {{
    send({{
      type: 'install_error',
      name: point.name,
      module_offset: point.module_offset,
      address: address.toString(),
      ok: false,
      error: String(e)
    }});
  }}
}}

send({{type: 'script_loaded'}});
points.forEach(installPoint);
send({{type: 'breakpoints_installed'}});
"""


def _run_breakpoint_probe(
    *,
    target: Path,
    candidate_hex: str,
    hook_points: dict[str, object],
    per_probe_timeout: float,
    lifecycle: LifecycleTracker,
) -> dict[str, object]:
    import frida
    from pywinauto import Application

    pid: int | None = None
    app = None
    messages: list[dict[str, object]] = []
    errors: list[str] = []
    installed: list[dict[str, object]] = []
    install_errors: list[dict[str, object]] = []
    hits: list[dict[str, object]] = []

    def on_message(message, data) -> None:  # noqa: ANN001
        _ = data
        if message.get("type") == "send" and isinstance(message.get("payload"), dict):
            payload = dict(message["payload"])
            messages.append(payload)
            if payload.get("type") == "install":
                installed.append(payload)
            elif payload.get("type") == "install_error":
                install_errors.append(payload)
            elif payload.get("type") == "hit":
                hits.append(payload)
        elif message.get("type") == "error":
            errors.append(str(message.get("stack") or message))

    try:
        lifecycle.confirm("frida_spawn_attempted")
        try:
            pid = frida.spawn([str(target)])
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            lifecycle.fail("frida_spawn_failed", error)
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification="frida_spawn_failed",
                target_launch=_target_launch(attempted=True, ok=False, pid=pid, error=error),
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
            )
        lifecycle.confirm("frida_spawn_ok", pid=pid)

        lifecycle.confirm("frida_attach_attempted", pid=pid)
        try:
            session = frida.attach(pid)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            lifecycle.fail("frida_attach_failed", error, pid=pid)
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification="frida_attach_failed",
                target_launch=_target_launch(attempted=True, ok=False, pid=pid, error=error),
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
            )
        lifecycle.confirm("frida_attach_ok", pid=pid)

        lifecycle.confirm("script_create_attempted")
        try:
            script = session.create_script(_script_source(_breakpoint_plan(hook_points)))
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            lifecycle.fail("script_create_failed", error, pid=pid)
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification="script_create_or_load_failed",
                target_launch=_target_launch(attempted=True, ok=True, pid=pid),
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
            )
        script.on("message", on_message)

        lifecycle.confirm("script_load_attempted")
        try:
            script.load()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            lifecycle.fail("script_load_failed", error, pid=pid)
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification="script_create_or_load_failed",
                target_launch=_target_launch(attempted=True, ok=True, pid=pid),
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
            )
        lifecycle.confirm("script_load_ok")

        lifecycle.confirm("breakpoint_install_attempted")
        deadline = time.monotonic() + max(0.5, min(float(per_probe_timeout), 5.0))
        while time.monotonic() < deadline:
            if any(str(item.get("type")) == "breakpoints_installed" for item in messages):
                break
            if errors:
                break
            time.sleep(0.05)
        breakpoints = _breakpoint_records(hook_points, installed, hits, install_errors)
        if errors or install_errors or any(not bool(item.get("install_ok")) for item in breakpoints):
            error = errors[-1] if errors else ""
            lifecycle.fail(
                "breakpoint_install_failed",
                error or "breakpoint installation could not be confirmed",
            )
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification="breakpoint_install_failed",
                target_launch=_target_launch(attempted=True, ok=True, pid=pid),
                breakpoints=breakpoints,
                event_sequence=hits,
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
            )
        lifecycle.confirm("breakpoint_install_ok")

        lifecycle.confirm("frida_resume_attempted")
        try:
            frida.resume(pid)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            lifecycle.fail("frida_resume_failed", error)
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification="frida_resume_failed",
                target_launch=_target_launch(attempted=True, ok=True, pid=pid),
                breakpoints=breakpoints,
                event_sequence=hits,
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
            )
        lifecycle.confirm("frida_resume_ok")

        lifecycle.confirm("ui_connect_attempted")
        try:
            app = Application(backend="uia").connect(process=pid)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            lifecycle.fail("ui_connect_failed", error)
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification="ui_connect_failed",
                target_launch=_target_launch(attempted=True, ok=True, pid=pid),
                breakpoints=breakpoints,
                event_sequence=hits,
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
            )
        lifecycle.confirm("ui_connect_ok")
        time.sleep(0.5)

        lifecycle.confirm("ui_trigger_attempted")
        try:
            win = _discover_window(app, pid, lifecycle, Application)
            lifecycle.ui_checkpoint("ui_control_inventory_captured")

            lifecycle.update_ui("input_control", {"lookup_attempted": True})
            lifecycle.ui_checkpoint("ui_input_lookup_attempted")
            input_edit = win.child_window(auto_id="1001", control_type="Edit")
            if hasattr(input_edit, "exists") and not input_edit.exists(timeout=0.5):
                lifecycle.update_ui("input_control", {"lookup_ok": False})
                lifecycle.ui_fail("ui_input_lookup_failed", "input Edit control not found")
                raise RuntimeError("input Edit control not found")
            lifecycle.update_ui("input_control", {"lookup_ok": True})
            lifecycle.ui_checkpoint("ui_input_lookup_ok")

            lifecycle.update_ui("button_control", {"lookup_attempted": True})
            lifecycle.ui_checkpoint("ui_button_lookup_attempted")
            decrypt_btn = win.child_window(auto_id="1000", control_type="Button")
            if hasattr(decrypt_btn, "exists") and not decrypt_btn.exists(timeout=0.5):
                lifecycle.update_ui("button_control", {"lookup_ok": False})
                lifecycle.ui_fail("ui_button_lookup_failed", "decrypt Button control not found")
                raise RuntimeError("decrypt Button control not found")
            button_enabled = _control_bool(decrypt_btn, "is_enabled")
            button_visible = _control_bool(decrypt_btn, "is_visible")
            lifecycle.update_ui(
                "button_control",
                {
                    "lookup_ok": True,
                    "enabled": button_enabled,
                    "visible": button_visible,
                },
            )
            lifecycle.ui_checkpoint(
                "ui_button_lookup_ok",
                enabled=button_enabled,
                visible=button_visible,
            )
            lifecycle.ui_checkpoint("ui_button_state_checked")
            if not button_enabled or not button_visible:
                lifecycle.ui_fail(
                    "ui_button_state_checked",
                    "decrypt Button is disabled or invisible",
                    enabled=button_enabled,
                    visible=button_visible,
                )
                raise RuntimeError("decrypt Button is disabled or invisible")

            gui_text = _candidate_to_gui_text(bytes.fromhex(candidate_hex).decode("latin1"))
            lifecycle.update_ui("input_control", {"set_text_attempted": True})
            lifecycle.ui_checkpoint("ui_input_set_text_attempted")
            input_edit.set_edit_text(gui_text)
            lifecycle.update_ui("input_control", {"set_text_ok": True})
            lifecycle.ui_checkpoint("ui_input_set_text_ok")

            lifecycle.update_ui("input_control", {"value_confirm_attempted": True})
            lifecycle.ui_checkpoint("ui_input_value_confirm_attempted")
            observed_text = _control_text(input_edit)
            value_confirmed = gui_text in observed_text or observed_text in {gui_text, ""}
            lifecycle.update_ui(
                "input_control",
                {
                    "value_confirmed": value_confirmed,
                    "observed_text_length": len(observed_text),
                },
            )
            if not value_confirmed:
                lifecycle.ui_fail(
                    "ui_input_value_confirm_failed",
                    "input value was not confirmed after set_text",
                    observed_text_length=len(observed_text),
                )
                raise RuntimeError("input value was not confirmed after set_text")
            lifecycle.ui_checkpoint("ui_input_value_confirm_ok", observed_text_length=len(observed_text))

            _trigger_decrypt_with_ui_diagnostics(decrypt_btn, lifecycle)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            lifecycle.fail("ui_trigger_failed", error)
            window_classification = _classification_from_window_discovery(lifecycle.window_discovery)
            ui_classification = (
                window_classification
                if window_classification
                and window_classification != "window_discovery_succeeded_input_lookup_next"
                else _classification_from_ui_trigger(lifecycle.ui_trigger)
            )
            lifecycle.ui_trigger["classification"] = ui_classification
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification=ui_classification,
                target_launch=_target_launch(attempted=True, ok=True, pid=pid),
                breakpoints=breakpoints,
                event_sequence=hits,
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
                ui_trigger=lifecycle.ui_trigger,
                window_discovery=lifecycle.window_discovery,
            )
        lifecycle.ui_checkpoint("ui_trigger_returned")
        lifecycle.confirm("ui_trigger_ok")

        lifecycle.ui_checkpoint("post_trigger_observation_wait_started")
        lifecycle.confirm("observation_wait_started")
        deadline = time.monotonic() + max(0.3, float(per_probe_timeout))
        while time.monotonic() < deadline:
            if hits and {str(hit.get("name") or "") for hit in hits}.intersection(
                {"process_exception", "actual_compare"}
            ):
                break
            if errors:
                break
            time.sleep(0.05)
        hit_names = {str(hit.get("name") or "") for hit in hits}
        successor_hit = bool(hit_names.intersection({"process_exception", "actual_compare"}))
        entry_hit = bool(hit_names.intersection({"predecessor_handoff_call", "handoff_helper_entry"}))
        lifecycle.update_ui(
            "post_trigger_observation",
            {
                "entry_breakpoint_hit": entry_hit,
                "successor_breakpoint_hit": successor_hit,
                "observed_events": list(hits),
            },
        )
        if successor_hit:
            lifecycle.ui_checkpoint("post_entry_breakpoint_observed_after_ui_trigger")
        elif entry_hit:
            lifecycle.ui_checkpoint("successor_breakpoint_not_hit_after_ui_trigger")
        else:
            lifecycle.ui_checkpoint("entry_breakpoint_not_hit_after_ui_trigger")
        lifecycle.confirm("observation_wait_finished_or_timeout", hit_count=len(hits))
        breakpoints = _breakpoint_records(hook_points, installed, hits, install_errors)
        classification = _classify(
            launch_ok=True,
            breakpoints=breakpoints,
            events=hits,
            runtime_error=errors[-1] if errors else "",
        )
        ui_classification = _classification_from_ui_trigger(lifecycle.ui_trigger)
        if ui_classification in {
            "entry_breakpoint_not_hit_after_ui_trigger",
            "successor_breakpoint_not_hit_after_ui_trigger",
            "post_entry_breakpoint_observed_after_ui_trigger",
            "post_trigger_observation_timeout",
        }:
            classification = ui_classification
        return _blocked_payload(
            candidate_hex=candidate_hex,
            target=target,
            hook_points=hook_points,
            classification=classification,
            target_launch=_target_launch(attempted=True, ok=True, pid=pid),
            breakpoints=breakpoints,
            event_sequence=hits,
            backend_import_ok=True,
            error=errors[-1] if errors else "",
            lifecycle=lifecycle.lifecycle(),
            ui_trigger=lifecycle.ui_trigger,
            window_discovery=lifecycle.window_discovery,
        )
    except Exception as exc:  # pragma: no cover - depends on local runtime
        error = f"{type(exc).__name__}: {exc}"
        lifecycle.fail("runtime_exception", error)
        return _blocked_payload(
            candidate_hex=candidate_hex,
            target=target,
            hook_points=hook_points,
            classification="instrumentation_gap_but_environment_verified",
            target_launch=_target_launch(attempted=True, ok=False, pid=pid, error=error),
            breakpoints=_breakpoint_records(hook_points, installed, hits, install_errors)
            if installed or install_errors
            else _empty_breakpoint_records(hook_points),
            event_sequence=hits,
            backend_import_ok=True,
            error=error,
            lifecycle=lifecycle.lifecycle(),
            window_discovery=lifecycle.window_discovery,
        )
    finally:
        _terminate_target(app, pid)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded post-entry breakpoint-only audit")
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--points", required=True)
    parser.add_argument("--probe-hex", required=True)
    parser.add_argument("--per-probe-timeout", default="2.2")
    args = parser.parse_args(argv)

    out_path = Path(args.out)
    target = Path(args.target)
    hook_points = _load_points(Path(args.points))
    lifecycle = LifecycleTracker(
        out_path=out_path,
        candidate_hex=args.probe_hex,
        target=target,
        hook_points=hook_points,
    )
    lifecycle.confirm("sidecar_started")
    lifecycle.confirm("arguments_parsed")

    lifecycle.confirm("target_checked", exists=target.exists())
    if not target.exists():
        error = f"target does not exist: {target}"
        lifecycle.fail("target_checked", error)
        return _write_payload(
            out_path,
            _blocked_payload(
                candidate_hex=args.probe_hex,
                target=target,
                hook_points=hook_points,
                classification="target_missing_or_unlaunchable",
                target_launch=_target_launch(
                    attempted=False,
                    ok=False,
                    error=error,
                ),
                error=error,
                lifecycle=lifecycle.lifecycle(),
            ),
        )

    lifecycle.confirm("dependency_import_attempted")
    try:
        import frida  # noqa: F401
        import pywinauto  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on local runtime
        error = f"{type(exc).__name__}: {exc}"
        lifecycle.fail("dependency_import_failed", error)
        return _write_payload(
            out_path,
            _blocked_payload(
                candidate_hex=args.probe_hex,
                target=target,
                hook_points=hook_points,
                classification="debugger_dependency_missing",
                target_launch=_target_launch(
                    attempted=False,
                    ok=False,
                    error=f"debugger dependency unavailable: {error}",
                ),
                backend_import_ok=False,
                backend_error=error,
                error=f"debugger dependency unavailable: {error}",
                lifecycle=lifecycle.lifecycle(),
            ),
        )
    lifecycle.confirm("dependency_import_ok")

    payload = _run_breakpoint_probe(
        target=target,
        candidate_hex=args.probe_hex,
        hook_points=hook_points,
        per_probe_timeout=float(args.per_probe_timeout),
        lifecycle=lifecycle,
    )
    payload["lifecycle"] = lifecycle.lifecycle()
    payload["lifecycle_schema_version"] = 1
    lifecycle.confirm("final_artifact_write_attempted")
    payload["lifecycle"] = lifecycle.lifecycle()
    _write_payload(out_path, payload)
    lifecycle.confirm("final_artifact_write_ok")
    payload["lifecycle"] = lifecycle.lifecycle()
    return _write_payload(out_path, payload)


if __name__ == "__main__":
    raise SystemExit(main())
