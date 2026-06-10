from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

try:  # Support package imports in tests and direct script execution.
    from .compare_probe import _candidate_to_gui_text, _escape_runtime_text, _terminate_target, _trigger_decrypt
except ImportError:  # pragma: no cover - exercised by subprocess execution
    from compare_probe import _candidate_to_gui_text, _escape_runtime_text, _terminate_target, _trigger_decrypt


LHS_SLOT_OFFSET = 0x1170


HOOK_POINTS = (
    ("pre_lhs_slot_store", 0x253A),
    ("pre_handoff_call", 0x2554),
    ("handoff_helper_enter", 0x1B50),
    ("post_handoff_lhs_reload", 0x2559),
    ("pre_compare_push_esi", 0x258B),
    ("wide_flag_prefix_compare", 0x258C),
)


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
        "reason": str(item.get("reason", "")),
    }


def _normalize_observation(item: dict[str, object] | None) -> dict[str, object]:
    item = item or {}
    return {
        "hook_name": str(item.get("hook_name", "")),
        "address": str(item.get("address", "")),
        "module_offset": str(item.get("module_offset", "")),
        "registers": dict(item.get("registers", {})) if isinstance(item.get("registers"), dict) else {},
        "stack_preview_hex": str(item.get("stack_preview_hex", "")),
        "lhs_slot_ptr": str(item.get("lhs_slot_ptr", "")),
        "lhs_slot_preview_hex": str(item.get("lhs_slot_preview_hex", "")),
        "eax_ptr": str(item.get("eax_ptr", "")),
        "eax_preview_hex": str(item.get("eax_preview_hex", "")),
        "esi_ptr": str(item.get("esi_ptr", "")),
        "esi_preview_hex": str(item.get("esi_preview_hex", "")),
        "lhs_ptr": str(item.get("lhs_ptr", "")),
        "rhs_ptr": str(item.get("rhs_ptr", "")),
        "compare_count": item.get("compare_count"),
        "lhs_buffer_preview_hex": str(item.get("lhs_buffer_preview_hex", "")),
        "lhs_buffer_preview_utf16le": str(item.get("lhs_buffer_preview_utf16le", "")),
    }


def _hook_results_from_observations(observations: list[dict[str, object]]) -> dict[str, str]:
    names = {str(item.get("hook_name", "")) for item in observations}
    has_lhs_slot = any(str(item.get("lhs_slot_ptr", "")) for item in observations)
    has_compare_lhs = any(str(item.get("lhs_buffer_preview_hex", "")) for item in observations)
    return {
        "handoff_helper_enter": "available" if "handoff_helper_enter" in names else "unavailable",
        "handoff_helper_return": "available" if "handoff_helper_return" in names else "unavailable",
        "post_handoff_lhs_reload": "available" if "post_handoff_lhs_reload" in names else "unavailable",
        "compare_lhs_buffer": "available" if has_compare_lhs else "unavailable",
        "lhs_slot": "available" if has_lhs_slot else "unavailable",
    }


def _build_payload(
    *,
    success: bool,
    summary: str,
    candidate_hex: str = "",
    hook_points: list[dict[str, object]] | None = None,
    hook_observations: list[dict[str, object]] | None = None,
    hook_results: dict[str, str] | None = None,
    evidence: list[str] | None = None,
    error: str = "",
) -> dict[str, object]:
    observations = [_normalize_observation(item) for item in hook_observations or []]
    return {
        "success": success,
        "summary": summary,
        "candidate_hex": candidate_hex,
        "hook_points": hook_points or [],
        "hook_observations": observations,
        "hook_results": hook_results or _hook_results_from_observations(observations),
        "evidence": evidence or [],
        "error": error,
    }


def _write_payload(out_path: Path, payload: dict[str, object]) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Hook samplereverse compare lhs handoff points")
    parser.add_argument("--target", required=True, help="Path to target executable")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--points", required=True, help="Hook point JSON path")
    parser.add_argument("--probe-hex", required=True, help="Probe candidate as raw low-byte hex")
    parser.add_argument("--per-probe-timeout", type=float, default=2.2)
    args = parser.parse_args()

    target = Path(args.target)
    out_path = Path(args.out)
    points_path = Path(args.points)
    hook_points = _read_points(points_path)
    if not hook_points:
        hook_points = [
            {"name": name, "address": f"module+0x{offset:x}", "module_offset": offset, "reason": "default"}
            for name, offset in HOOK_POINTS
        ]
    evidence = [f"compare_handoff_probe:target={target}", f"compare_handoff_probe:points={points_path}"]

    if not target.exists():
        return _write_payload(
            out_path,
            _build_payload(
                success=False,
                summary="CompareHandoffProbe failed: target missing.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                evidence=[*evidence, "compare_handoff_probe:error=target_missing"],
                error="target_missing",
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
                summary="CompareHandoffProbe failed: missing frida or pywinauto.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                evidence=[*evidence, f"compare_handoff_probe:error={_escape_runtime_text(str(exc))}"],
                error=str(exc),
            ),
        )

    messages: list[dict[str, object]] = []
    script_errors: list[str] = []
    pid: int | None = None
    session = None
    app = None

    def on_message(message: dict[str, object], data: object) -> None:  # noqa: ANN401
        message_type = str(message.get("type", ""))
        if message_type == "send":
            payload = message.get("payload", {})
            if isinstance(payload, dict):
                messages.append(payload)
            return
        if message_type == "error":
            stack = str(message.get("stack", "")).strip()
            if stack:
                script_errors.append(stack)

    points_json = json.dumps(hook_points, ensure_ascii=True)
    script_source = f"""
const hookPoints = {points_json};
const lhsSlotOffset = ptr("{LHS_SLOT_OFFSET:#x}");
const helperOffset = 0x1b50;

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
        const raw = ptrValue.readByteArray(Math.min(Math.max(size, 16), 128));
        return hexBytes(raw);
    }} catch (error) {{
        return "";
    }}
}}

function readWide(ptrValue, size) {{
    try {{
        if (!ptrValue || ptrValue.isNull()) {{
            return "";
        }}
        let out = [];
        const limit = Math.min(Math.max(size, 10), 64);
        for (let i = 0; i < limit; i += 2) {{
            const value = ptrValue.add(i).readU16();
            if (value === 0) {{
                break;
            }}
            out.push(String.fromCharCode(value));
        }}
        return out.join("");
    }} catch (error) {{
        return "";
    }}
}}

function safePointer(value) {{
    try {{
        const p = ptr(value);
        return p;
    }} catch (error) {{
        return ptr(0);
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

function observe(name, address, context) {{
    const sp = ptr(context.sp || context.esp || 0);
    const bp = ptr(context.bp || context.ebp || 0);
    const eax = safePointer(context.eax || context.rax || 0);
    const esi = safePointer(context.esi || context.rsi || 0);
    let slotPtr = ptr(0);
    try {{
        slotPtr = bp.sub(lhsSlotOffset).readPointer();
    }} catch (error) {{
        slotPtr = ptr(0);
    }}
    let lhsPtr = ptr(0);
    let rhsPtr = ptr(0);
    let compareCount = 0;
    if (name === "wide_flag_prefix_compare") {{
        try {{
            lhsPtr = sp.readPointer();
            rhsPtr = sp.add(Process.pointerSize).readPointer();
            compareCount = sp.add(Process.pointerSize * 2).readU32();
        }} catch (error) {{
            lhsPtr = ptr(0);
        }}
    }}
    const primaryLhs = name === "wide_flag_prefix_compare" ? lhsPtr : (slotPtr.isNull() ? esi : slotPtr);
    send({{
        type: "compare_handoff_observation",
        hook_name: name,
        address: address.toString(),
        module_offset: "0x" + address.sub(Process.enumerateModules()[0].base).toString(16),
        registers: contextRegs(context),
        stack_preview_hex: readBytes(sp, 96),
        lhs_slot_ptr: slotPtr.toString(),
        lhs_slot_preview_hex: readBytes(slotPtr, 96),
        eax_ptr: eax.toString(),
        eax_preview_hex: readBytes(eax, 96),
        esi_ptr: esi.toString(),
        esi_preview_hex: readBytes(esi, 96),
        lhs_ptr: lhsPtr.toString(),
        rhs_ptr: rhsPtr.toString(),
        compare_count: compareCount,
        lhs_buffer_preview_hex: readBytes(primaryLhs, 96),
        lhs_buffer_preview_utf16le: readWide(primaryLhs, 96),
    }});
}}

const mainModule = Process.enumerateModules()[0];
for (const point of hookPoints) {{
    try {{
        const offset = Number(point.module_offset || 0);
        if (!offset) {{
            continue;
        }}
        const address = mainModule.base.add(offset);
        const name = String(point.name || ("module_0x" + offset.toString(16)));
        Interceptor.attach(address, {{
            onEnter(args) {{
                observe(name, address, this.context);
            }},
            onLeave(retval) {{
                if (offset === helperOffset || name === "handoff_helper_enter") {{
                    observe("handoff_helper_return", address, this.context);
                }}
            }}
        }});
    }} catch (error) {{
        send({{ type: "compare_handoff_error", hook_name: String(point.name || ""), error: String(error) }});
    }}
}}
"""

    try:
        pid = frida.spawn([str(target)])
        session = frida.attach(pid)
        script = session.create_script(script_source)
        script.on("message", on_message)
        script.load()
        frida.resume(pid)
        time.sleep(1.0)

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

        input_edit = win.child_window(auto_id="1001", control_type="Edit")
        decrypt_btn = win.child_window(auto_id="1000", control_type="Button")
        candidate = bytes.fromhex(args.probe_hex).decode("latin1")
        evidence.append(f"compare_handoff_probe:title={_escape_runtime_text(win.window_text() or '')}")
        evidence.append(f"compare_handoff_probe:probe_hex={args.probe_hex}")
        before_count = len(messages)
        input_edit.set_edit_text(_candidate_to_gui_text(candidate))
        _trigger_decrypt(decrypt_btn)

        deadline = time.monotonic() + max(0.3, float(args.per_probe_timeout))
        while time.monotonic() < deadline:
            if script_errors:
                raise RuntimeError(script_errors[-1])
            time.sleep(0.05)

        observations = [
            _normalize_observation(payload)
            for payload in messages[before_count:]
            if str(payload.get("type", "")) == "compare_handoff_observation"
        ]
        hook_errors = [
            str(payload.get("error", ""))
            for payload in messages[before_count:]
            if str(payload.get("type", "")) == "compare_handoff_error"
        ]
        if hook_errors:
            evidence.extend(f"compare_handoff_probe:hook_error={_escape_runtime_text(item)}" for item in hook_errors if item)
        evidence.append(f"compare_handoff_probe:hook_observations={len(observations)}")
        return _write_payload(
            out_path,
            _build_payload(
                success=True,
                summary="CompareHandoffProbe completed scripted handoff hook attempt.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                hook_observations=observations,
                evidence=evidence,
            ),
        )
    except Exception as exc:
        evidence.append(f"compare_handoff_probe:error={_escape_runtime_text(str(exc))}")
        return _write_payload(
            out_path,
            _build_payload(
                success=False,
                summary="CompareHandoffProbe execution failed.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                evidence=evidence,
                error=str(exc),
            ),
        )
    finally:
        _terminate_target(app, pid)
        try:
            if session is not None:
                session.detach()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
