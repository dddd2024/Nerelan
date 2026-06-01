from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

try:  # Support package imports in tests and direct subprocess execution.
    from .compare_probe import _candidate_to_gui_text, _terminate_target, _trigger_decrypt
except ImportError:  # pragma: no cover - exercised by direct subprocess execution
    from compare_probe import _candidate_to_gui_text, _terminate_target, _trigger_decrypt


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
        "final_artifact_write_failed": "candidate_artifact_write_failed",
    }.get(stage, "instrumentation_gap_but_environment_verified")


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
    candidate_invocation_health: dict[str, object] | None = None,
) -> dict[str, object]:
    event_sequence = event_sequence or []
    breakpoints = breakpoints if isinstance(breakpoints, list) else _empty_breakpoint_records(hook_points)
    hit_names = {str(event.get("name") or "") for event in event_sequence}
    lifecycle = lifecycle if isinstance(lifecycle, dict) else {}
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
            win = app.top_window()
            input_edit = win.child_window(auto_id="1001", control_type="Edit")
            decrypt_btn = win.child_window(auto_id="1000", control_type="Button")
            input_edit.set_edit_text(_candidate_to_gui_text(bytes.fromhex(candidate_hex).decode("latin1")))
            _trigger_decrypt(decrypt_btn)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            lifecycle.fail("ui_trigger_failed", error)
            return _blocked_payload(
                candidate_hex=candidate_hex,
                target=target,
                hook_points=hook_points,
                classification="ui_trigger_failed",
                target_launch=_target_launch(attempted=True, ok=True, pid=pid),
                breakpoints=breakpoints,
                event_sequence=hits,
                backend_import_ok=True,
                error=error,
                lifecycle=lifecycle.lifecycle(),
            )
        lifecycle.confirm("ui_trigger_ok")

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
        lifecycle.confirm("observation_wait_finished_or_timeout", hit_count=len(hits))
        breakpoints = _breakpoint_records(hook_points, installed, hits, install_errors)
        classification = _classify(
            launch_ok=True,
            breakpoints=breakpoints,
            events=hits,
            runtime_error=errors[-1] if errors else "",
        )
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
