from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

try:  # Support package imports in tests and direct script execution.
    from .compare_probe import _candidate_to_gui_text, _escape_runtime_text, _terminate_target, _trigger_decrypt
except ImportError:  # pragma: no cover - exercised by subprocess execution
    from compare_probe import _candidate_to_gui_text, _escape_runtime_text, _terminate_target, _trigger_decrypt


FRAME_SLOT_OFFSETS = (0x1160, 0x1164, 0x1168, 0x116C, 0x1170)
WRITE_RING_LIMIT = 4096


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
    error: str = "",
) -> dict[str, object]:
    observations = [_normalize_observation(item) for item in hook_observations or []]
    return {
        "success": success,
        "summary": summary,
        "candidate_hex": candidate_hex,
        "hook_points": hook_points or [],
        "hook_observations": observations,
        "write_monitor_health": dict(write_monitor_health or {}),
        "write_ring_buffer": list(write_ring_buffer or []),
        "evidence": evidence or [],
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
    ]

    if not target.exists():
        return _write_payload(
            out_path,
            _build_payload(
                success=False,
                summary="ComparePreCompareHandoffTargetProbe failed: target missing.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                evidence=[*evidence, "compare_pre_compare_handoff_target_probe:error=target_missing"],
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
                summary="ComparePreCompareHandoffTargetProbe failed: missing frida or pywinauto.",
                candidate_hex=args.probe_hex,
                hook_points=hook_points,
                evidence=[*evidence, f"compare_pre_compare_handoff_target_probe:error={_escape_runtime_text(str(exc))}"],
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
        const event = {{
            sequence: writeSequence++,
            address: address.toString(),
            address_u64: pointerValue(address),
            size: Number(descriptor.size || Process.pointerSize),
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
        if (!itemStart || !rangesIntersect(itemStart, itemSize, arg0Start, arg0Size)) {{
            continue;
        }}
        out.push(Object.assign({{}}, item, {{
            intersects_arg0: true,
            arg0_value: String(arg0.value || ""),
            arg0_preview_hex: previewHex,
            after_preview_hex: readBytes(safePointer(item.address || 0), 96),
        }}));
    }}
    return out.slice(-64);
}}

function writeMonitorHealth(filteredWrites) {{
    return {{
        enabled: Boolean(writeRingEnabled),
        followed_thread_count: writeMonitorFollowedThreadCount,
        raw_write_count: writeMonitorRawWriteCount,
        ring_capacity: writeRingLimit,
        eviction_count: writeMonitorEvictionCount,
        descriptor_decode_failures: writeMonitorDescriptorDecodeFailures,
        address_decode_failures: writeMonitorAddressDecodeFailures,
        follow_failures: writeMonitorFollowFailures,
        last_raw_write_samples: lastRawWriteSamples.slice(-8),
        filtered_intersecting_write_count: filteredWrites ? filteredWrites.length : 0,
    }};
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
    const isHelperCompare = pointName === "compare_helper_entry" || pointName === "actual_compare_entry";
    const isStaticCompareCallsite = pointName === "static_compare_callsite";
    const compareSlots = isStaticCompareCallsite
        ? compareCallsiteSlots(sp, address, mainModule.base)
        : isHelperCompare
            ? compareEntrySlots(sp, mainModule.base)
            : [];
    const filteredWrites = isStaticCompareCallsite ? filteredWriteRing(compareSlots) : [];
    send({{
        type: "compare_pre_compare_handoff_target_observation",
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
        write_monitor_health: isStaticCompareCallsite ? writeMonitorHealth(filteredWrites) : {{}},
        write_ring_buffer: filteredWrites,
    }});
}}

const mainModule = Process.enumerateModules()[0];
if (writeRingEnabled) {{
    try {{
        for (const thread of Process.enumerateThreads()) {{
            try {{
                Stalker.follow(thread.id, {{
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
            }} catch (error) {{
                writeMonitorFollowFailures++;
            }}
        }}
    }} catch (error) {{
        send({{ type: "compare_pre_compare_handoff_target_error", hook_name: "write_ring_buffer", error: String(error) }});
    }}
}}
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
for (const point of hookPoints) {{
    try {{
        const offset = Number(point.module_offset || 0);
        if (!offset) {{
            continue;
        }}
        const address = mainModule.base.add(offset);
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
    }} catch (error) {{
        send({{ type: "compare_pre_compare_handoff_target_error", hook_name: String(point.name || ""), error: String(error) }});
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
        evidence.append(f"compare_pre_compare_handoff_target_probe:title={_escape_runtime_text(win.window_text() or '')}")
        evidence.append(f"compare_pre_compare_handoff_target_probe:probe_hex={args.probe_hex}")
        input_edit.set_edit_text(_candidate_to_gui_text(candidate))
        _trigger_decrypt(decrypt_btn)

        deadline = time.monotonic() + max(0.3, float(args.per_probe_timeout))
        while time.monotonic() < deadline:
            if script_errors:
                raise RuntimeError(script_errors[-1])
            time.sleep(0.05)
    except Exception as exc:
        script_errors.append(_escape_runtime_text(str(exc)))
    finally:
        try:
            if session is not None:
                session.detach()
        except Exception:
            pass
        if pid is not None:
            _terminate_target(app, pid)

    observations = [
        item
        for item in messages
        if str(item.get("type", "")) == "compare_pre_compare_handoff_target_observation"
    ]
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
    errors = [
        f"{item.get('hook_name', '')}:{item.get('error', '')}"
        for item in messages
        if str(item.get("type", "")) == "compare_pre_compare_handoff_target_error"
    ]
    success = bool(observations) and not script_errors
    summary = (
        "ComparePreCompareHandoffTargetProbe captured bounded handoff observations."
        if observations
        else "ComparePreCompareHandoffTargetProbe did not capture bounded handoff observations."
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
            evidence=[*evidence, *errors, *script_errors],
            error="; ".join([*errors, *script_errors]),
        ),
    )


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
