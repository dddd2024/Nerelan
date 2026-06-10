from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .evidence import (
    StructuredEvidence,
    base64_material_evidence,
    rc4_material_evidence,
    utf16le_material_evidence,
)

LogFn = Callable[[str], None]


@dataclass
class ToolAutomationConfig:
    enabled: bool = False
    ida_enabled: bool = True
    ida_executable: str = ""
    ida_script_path: str = ""
    ida_timeout_seconds: int = 180
    ollydbg_enabled: bool = False
    ollydbg_executable: str = ""
    ollydbg_script_path: str = ""
    ollydbg_timeout_seconds: int = 120


@dataclass
class ToolRunArtifact:
    tool_name: str
    enabled: bool
    attempted: bool
    success: bool
    command: str = ""
    summary: str = ""
    output_path: str = ""
    error: str = ""
    evidence: list[str] = field(default_factory=list)
    structured_evidence: list[StructuredEvidence] = field(default_factory=list)
    owner_profile: str = ""
    strategy_name: str = ""


def _maybe_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _structured_evidence_from_json(tool_name: str, data: dict[str, object]) -> list[StructuredEvidence]:
    items: list[StructuredEvidence] = []
    candidates = data.get("candidates", [])
    if isinstance(candidates, list):
        for item in candidates[:16]:
            if isinstance(item, dict):
                value = str(item.get("value", "")).strip()
                source = str(item.get("source", "")).strip() or tool_name
                confidence = _maybe_float(item.get("confidence"))
            else:
                value = str(item).strip()
                source = tool_name
                confidence = None
            if not value:
                continue
            items.append(
                StructuredEvidence(
                    kind="CandidateEvidence",
                    source_tool=source,
                    summary=f"{tool_name} candidate",
                    confidence=confidence,
                    derived_candidates=[value],
                    payload={"value": value},
                )
            )

    if any(key in data for key in ("compare_site", "lhs_wide_hex", "rhs_wide_hex", "input_text")):
        payload = {
            "compare_site": str(data.get("compare_site", "")).strip(),
            "input_text": str(data.get("input_text", "")),
            "lhs_ptr": str(data.get("lhs_ptr", "")),
            "rhs_ptr": str(data.get("rhs_ptr", "")),
            "compare_count": data.get("compare_count"),
            "lhs_wide_text": str(data.get("lhs_wide_text", "")),
            "lhs_wide_hex": str(data.get("lhs_wide_hex", "")),
            "rhs_wide_text": str(data.get("rhs_wide_text", "")),
            "rhs_wide_hex": str(data.get("rhs_wide_hex", "")),
            "runtime_ci_exact_wchars": data.get("runtime_ci_exact_wchars"),
            "runtime_ci_distance5": data.get("runtime_ci_distance5"),
            "runtime_lhs_prefix_hex": str(data.get("runtime_lhs_prefix_hex", "")),
            "runtime_lhs_prefix_hex_10": str(data.get("runtime_lhs_prefix_hex_10", "")),
            "runtime_lhs_prefix_hex_16": str(data.get("runtime_lhs_prefix_hex_16", "")),
            "runtime_lhs_prefix_bytes_captured": data.get("runtime_lhs_prefix_bytes_captured"),
            "compare_semantics_agree": data.get("compare_semantics_agree"),
            "offline_ci_exact_wchars": data.get("offline_ci_exact_wchars"),
            "offline_ci_distance5": data.get("offline_ci_distance5"),
            "offline_raw_prefix_hex": str(data.get("offline_raw_prefix_hex", "")),
        }
        items.append(
            StructuredEvidence(
                kind="RuntimeCompareEvidence",
                source_tool=tool_name,
                summary=str(data.get("summary", "")).strip() or f"{tool_name} compare capture",
                confidence=0.95 if payload["lhs_wide_hex"] else 0.55,
                payload=payload,
                derived_candidates=[
                    evidence.derived_candidates[0]
                    for evidence in items
                    if evidence.kind == "CandidateEvidence" and evidence.derived_candidates
                ][:4],
            )
        )

    strings = data.get("strings", [])
    if isinstance(strings, list) and strings:
        items.append(
            StructuredEvidence(
                kind="StaticStringEvidence",
                source_tool=tool_name,
                summary=f"{tool_name} extracted strings",
                confidence=0.7,
                payload={"strings": [str(item) for item in strings[:20]]},
            )
        )

    if any(key in data for key in ("compare_contexts", "control_id_contexts", "local_check_contexts")):
        items.append(
            StructuredEvidence(
                kind="ConstraintEvidence",
                source_tool=tool_name,
                summary=f"{tool_name} recovered comparison contexts",
                confidence=0.75,
                payload={
                    "compare_contexts": data.get("compare_contexts", []),
                    "control_id_contexts": data.get("control_id_contexts", []),
                    "local_check_contexts": data.get("local_check_contexts", []),
                },
            )
        )

    # Material evidence ingestion for Base64/RC4/UTF-16LE probes
    # Only ingest when explicit material fields are present; do not promote
    # compare capture alone to material proof.
    _ingest_material_evidence(tool_name, data, items)

    return items


def _ingest_material_evidence(
    tool_name: str,
    data: dict[str, object],
    items: list[StructuredEvidence],
) -> None:
    """Ingest Base64/RC4/UTF-16LE material evidence from JSON probe output.

    This helper looks for explicit material-probe fields and converts them
    to StructuredEvidence records. It does NOT treat compare capture or
    candidate lists alone as material proof.
    """
    # Base64 material evidence
    base64_fields = ("base64_construction_point", "base64_input_bytes_hex", "base64_output_chars")
    if any(key in data for key in base64_fields):
        chunk_boundary = data.get("base64_chunk_boundary_info")
        items.append(
            base64_material_evidence(
                source_tool=tool_name,
                construction_point=str(data.get("base64_construction_point", "")).strip(),
                input_bytes_hex=str(data.get("base64_input_bytes_hex", "")).strip(),
                output_chars=str(data.get("base64_output_chars", "")).strip(),
                chunk_boundary_info=chunk_boundary if isinstance(chunk_boundary, dict) else None,
                instruction_address=str(data.get("base64_instruction_address", "")).strip(),
                confidence=_maybe_float(data.get("base64_confidence")),
                derived_candidates=[
                    str(data.get("base64_derived_candidate", "")).strip()
                ] if data.get("base64_derived_candidate") else [],
            )
        )

    # RC4 material evidence
    rc4_fields = ("rc4_ksa_point", "rc4_prga_point", "rc4_key_material_hex")
    if any(key in data for key in rc4_fields):
        items.append(
            rc4_material_evidence(
                source_tool=tool_name,
                ksa_point=str(data.get("rc4_ksa_point", "")).strip(),
                prga_point=str(data.get("rc4_prga_point", "")).strip(),
                key_material_hex=str(data.get("rc4_key_material_hex", "")).strip(),
                input_bytes_hex=str(data.get("rc4_input_bytes_hex", "")).strip(),
                output_bytes_hex=str(data.get("rc4_output_bytes_hex", "")).strip(),
                instruction_address=str(data.get("rc4_instruction_address", "")).strip(),
                confidence=_maybe_float(data.get("rc4_confidence")),
                derived_candidates=[
                    str(data.get("rc4_derived_candidate", "")).strip()
                ] if data.get("rc4_derived_candidate") else [],
            )
        )

    # UTF-16LE material evidence
    utf16le_fields = ("utf16le_expansion_point", "utf16le_source_bytes_hex", "utf16le_wide_chars")
    if any(key in data for key in utf16le_fields):
        items.append(
            utf16le_material_evidence(
                source_tool=tool_name,
                expansion_point=str(data.get("utf16le_expansion_point", "")).strip(),
                source_bytes_hex=str(data.get("utf16le_source_bytes_hex", "")).strip(),
                wide_chars=str(data.get("utf16le_wide_chars", "")).strip(),
                instruction_address=str(data.get("utf16le_instruction_address", "")).strip(),
                confidence=_maybe_float(data.get("utf16le_confidence")),
                derived_candidates=[
                    str(data.get("utf16le_derived_candidate", "")).strip()
                ] if data.get("utf16le_derived_candidate") else [],
            )
        )


def _resolve_ida_executable(user_path: str) -> str:
    if user_path.strip():
        p = Path(user_path.strip())
        if not p.exists():
            return ""
        if p.is_file():
            return str(p)
        if p.is_dir():
            for name in ("idat64.exe", "idat.exe", "ida64.exe", "ida.exe"):
                candidate = p / name
                if candidate.exists() and candidate.is_file():
                    return str(candidate)
            return ""
    for candidate in ("idat64.exe", "idat.exe", "ida64.exe", "ida.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return ""


def _resolve_ida_script(user_path: str) -> str:
    if user_path.strip():
        p = Path(user_path.strip())
        return str(p) if p.exists() else ""
    default_script = Path(__file__).parent / "ida_scripts" / "collect_evidence.py"
    return str(default_script) if default_script.exists() else ""


def _resolve_ollydbg_executable(user_path: str) -> str:
    if user_path.strip():
        p = Path(user_path.strip())
        if not p.exists():
            return ""
        if p.is_file():
            return str(p)
        if p.is_dir():
            for name in ("ollydbg.exe", "OLLYDBG.EXE"):
                candidate = p / name
                if candidate.exists() and candidate.is_file():
                    return str(candidate)
            return ""
    for candidate in ("ollydbg.exe", "OLLYDBG.EXE"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return ""


def _resolve_ollydbg_script(user_path: str) -> str:
    if not user_path.strip():
        default_script = Path(__file__).parent / "olly_scripts" / "collect_evidence.py"
        return str(default_script) if default_script.exists() else ""
    p = Path(user_path.strip())
    if not p.exists() or not p.is_file():
        return ""
    return str(p)


def _resolve_compare_probe_script() -> str:
    script_path = Path(__file__).parent / "olly_scripts" / "compare_probe.py"
    return str(script_path) if script_path.exists() and script_path.is_file() else ""


def _populate_artifact_from_json_output(
    artifact: ToolRunArtifact,
    output_path: Path,
    tool_name: str,
) -> bool:
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        artifact.error = f"{tool_name} 证据文件解析失败：{exc}"
        artifact.summary = f"{tool_name} 输出不可解析。"
        return False

    if not isinstance(data, dict):
        artifact.error = f"{tool_name} 证据文件格式错误：顶层不是 JSON object。"
        artifact.summary = f"{tool_name} 输出不可解析。"
        return False

    evidence = data.get("evidence", [])
    if isinstance(evidence, list):
        artifact.evidence = [str(item) for item in evidence[:80]]
    artifact.structured_evidence = _structured_evidence_from_json(tool_name=tool_name, data=data)

    candidates = data.get("candidates", [])
    if isinstance(candidates, list):
        for item in candidates[:16]:
            if isinstance(item, dict):
                value = str(item.get("value", "")).strip()
                source = str(item.get("source", "")).strip()
                confidence = str(item.get("confidence", "")).strip()
                if value:
                    artifact.evidence.append(
                        f"runtime_candidate:{value}"
                        + (f" source={source}" if source else "")
                        + (f" confidence={confidence}" if confidence else "")
                    )
            else:
                value = str(item).strip()
                if value:
                    artifact.evidence.append(f"runtime_candidate:{value}")

    custom_summary = str(data.get("summary", "")).strip()
    if custom_summary:
        artifact.summary = custom_summary
    return True


def run_ida_evidence(
    file_path: Path,
    artifacts_dir: Path,
    log: LogFn,
    *,
    ida_executable: str = "",
    ida_script_path: str = "",
    timeout_seconds: int = 180,
) -> ToolRunArtifact:
    config = ToolAutomationConfig(
        enabled=True,
        ida_enabled=True,
        ida_executable=ida_executable,
        ida_script_path=ida_script_path,
        ida_timeout_seconds=timeout_seconds,
    )
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return _run_ida(file_path, config, artifacts_dir, log)


def run_tool_automation(
    file_path: Path,
    analysis_mode: str,
    config: ToolAutomationConfig,
    artifacts_dir: Path,
    log: LogFn,
) -> list[ToolRunArtifact]:
    artifacts: list[ToolRunArtifact] = []
    if not config.enabled:
        log("工具链自动分析未启用，跳过 IDA/OllyDbg。")
        return artifacts

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if config.ida_enabled:
        artifacts.append(
            run_ida_evidence(
                file_path=file_path,
                artifacts_dir=artifacts_dir,
                log=log,
                ida_executable=config.ida_executable,
                ida_script_path=config.ida_script_path,
                timeout_seconds=config.ida_timeout_seconds,
            )
        )

    auto_olly_enabled = (
        analysis_mode == "Dynamic Debug"
        and not config.ollydbg_enabled
        and bool(config.ollydbg_executable.strip())
        and bool(config.ollydbg_script_path.strip())
    )
    if auto_olly_enabled:
        log("检测到 OllyDbg 路径与脚本已配置，自动启用 OllyDbg 自动化。")

    if analysis_mode == "Dynamic Debug" and (config.ollydbg_enabled or auto_olly_enabled):
        artifacts.append(_run_ollydbg(file_path, config, artifacts_dir, log))
    elif analysis_mode != "Dynamic Debug" and (
        config.ollydbg_enabled
        or config.ollydbg_executable.strip()
        or config.ollydbg_script_path.strip()
    ):
        artifacts.append(
            ToolRunArtifact(
                tool_name="OllyDbg",
                enabled=True,
                attempted=False,
                success=False,
                summary="OllyDbg 已跳过（仅在动态调试模式执行）。",
            )
        )
    elif analysis_mode == "Dynamic Debug":
        artifacts.append(
            ToolRunArtifact(
                tool_name="OllyDbg",
                enabled=False,
                attempted=False,
                success=False,
                summary="OllyDbg 未启用（可勾选开关或同时配置路径+脚本自动启用）。",
                error="未满足 OllyDbg 运行条件。",
            )
        )

    return artifacts


def run_compare_probe(
    file_path: Path,
    artifacts_dir: Path,
    log: LogFn,
    timeout_seconds: int = 120,
    capture_prefix_bytes: int = 10,
) -> ToolRunArtifact:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact = ToolRunArtifact(
        tool_name="CompareProbe",
        enabled=True,
        attempted=False,
        success=False,
    )
    compare_probe_script = _resolve_compare_probe_script()
    if not compare_probe_script:
        artifact.error = "未找到 CompareProbe 脚本。"
        artifact.summary = "CompareProbe 未执行。"
        return artifact

    output_path = artifacts_dir / f"{file_path.stem}_compare_probe.json"
    log_path = artifacts_dir / f"{file_path.stem}_compare_probe.log"
    command_args = [
        sys.executable,
        compare_probe_script,
        "--target",
        str(file_path),
        "--out",
        str(output_path),
    ]
    normalized_capture_prefix_bytes = max(10, int(capture_prefix_bytes or 10))
    if normalized_capture_prefix_bytes != 10:
        command_args.extend(["--capture-prefix-bytes", str(normalized_capture_prefix_bytes)])
    artifact.command = " ".join(shlex.quote(a) for a in command_args)
    artifact.output_path = str(output_path)
    artifact.attempted = True
    log("正在执行 CompareProbe 动态比较提取...")

    try:
        proc = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        artifact.error = f"CompareProbe 超时（>{timeout_seconds} 秒）。"
        artifact.summary = "CompareProbe 超时。"
        return artifact

    combined_output = (
        f"[stdout]\n{proc.stdout or ''}\n\n[stderr]\n{proc.stderr or ''}".strip()
    )
    log_path.write_text(combined_output, encoding="utf-8", errors="replace")

    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "").strip()
        artifact.error = details[:2000] if details else "CompareProbe 未返回可读错误信息。"
        artifact.summary = f"CompareProbe 执行失败（退出码 {proc.returncode}）。"
        return artifact

    if output_path.exists():
        if not _populate_artifact_from_json_output(
            artifact=artifact,
            output_path=output_path,
            tool_name="CompareProbe",
        ):
            return artifact
        if not artifact.summary:
            artifact.summary = "CompareProbe 已完成。"
    else:
        artifact.summary = (
            "CompareProbe 已执行，但未生成证据文件。"
            f" 已写入日志：{log_path}"
        )

    artifact.success = True
    if f"CompareProbe日志: {log_path}" not in artifact.evidence:
        artifact.evidence.append(f"CompareProbe日志: {log_path}")
    return artifact


def _run_ida(
    file_path: Path,
    config: ToolAutomationConfig,
    artifacts_dir: Path,
    log: LogFn,
) -> ToolRunArtifact:
    artifact = ToolRunArtifact(
        tool_name="IDA",
        enabled=True,
        attempted=False,
        success=False,
    )
    ida_executable = _resolve_ida_executable(config.ida_executable)
    if not ida_executable:
        artifact.error = "未找到 IDA 可执行文件（请在界面配置 ida/idat 路径）。"
        artifact.summary = "IDA 自动分析未执行。"
        return artifact

    ida_script = _resolve_ida_script(config.ida_script_path)
    if not ida_script:
        artifact.error = "未找到 IDA 脚本（请在界面配置脚本路径）。"
        artifact.summary = "IDA 自动分析未执行。"
        return artifact

    output_path = artifacts_dir / f"{file_path.stem}_ida_evidence.json"
    ida_log_path = artifacts_dir / f"{file_path.stem}_ida.log"
    ida_database_path = artifacts_dir / f"{file_path.stem}_ida_database.i64"
    for suffix in (".i64", ".id0", ".id1", ".nam", ".til"):
        sidecar_path = ida_database_path.with_suffix(suffix)
        try:
            sidecar_path.unlink(missing_ok=True)
        except OSError:
            pass
    artifact.output_path = str(output_path)
    command_args = [
        ida_executable,
        "-A",
        f"-L{ida_log_path}",
        f"-o{ida_database_path}",
        f"-S{ida_script}",
        str(file_path),
    ]
    artifact.command = " ".join(shlex.quote(a) for a in command_args)
    artifact.attempted = True
    log("正在执行 IDA 自动化分析...")

    env = dict(os.environ)
    env["REVERSE_AGENT_IDA_OUT"] = str(output_path)

    try:
        proc = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=config.ida_timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired:
        artifact.error = f"IDA 执行超时（>{config.ida_timeout_seconds} 秒）。"
        artifact.summary = "IDA 自动分析超时。"
        return artifact

    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "").strip()
        if not details and ida_log_path.exists():
            details = ida_log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
        artifact.error = details[:2000] if details else "IDA 未返回可读错误信息。"
        artifact.summary = f"IDA 执行失败（退出码 {proc.returncode}）。"
        return artifact

    if not output_path.exists():
        artifact.error = "IDA 执行结束但未生成证据文件。"
        artifact.summary = "IDA 自动分析输出缺失。"
        return artifact

    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        artifact.error = f"IDA 证据文件解析失败：{exc}"
        artifact.summary = "IDA 输出不可解析。"
        return artifact

    strings = data.get("strings", [])[:40]
    funcs = data.get("functions", [])[:30]
    compare_contexts = data.get("compare_contexts", [])[:20]
    local_check_contexts = data.get("local_check_contexts", [])[:20]
    control_id_contexts = data.get("control_id_contexts", [])[:20]
    string_xrefs = data.get("string_xrefs", [])[:20]
    validation_function_candidates = data.get("validation_function_candidates", [])[:20]
    decompiler_snippets = data.get("decompiler_snippets", [])[:8]
    solver_hints = data.get("solver_hints", [])[:12]
    entry = str(data.get("entry", "")).strip()
    artifact.evidence = [
        *([f"IDA入口: {entry}"] if entry else []),
        *(f"IDA字符串: {s}" for s in strings),
        *(f"IDA函数: {f}" for f in funcs),
    ]
    for ctx in compare_contexts:
        if not isinstance(ctx, dict):
            continue
        call_ea = str(ctx.get("call_ea", "")).strip()
        callee = str(ctx.get("callee", "")).strip()
        caller = str(ctx.get("caller_func", "")).strip()
        ref_strings = str(ctx.get("ref_strings", "")).strip()
        call_disasm = str(ctx.get("call_disasm", "")).strip()
        nearby = str(ctx.get("nearby", "")).strip()
        parts = [
            f"IDA比较上下文: call={call_ea}" if call_ea else "IDA比较上下文",
            f"callee={callee}" if callee else "",
            f"caller={caller}" if caller else "",
            f"insn={call_disasm}" if call_disasm else "",
            f"strings={ref_strings}" if ref_strings else "",
            f"nearby={nearby}" if nearby else "",
        ]
        artifact.evidence.append(" ".join(p for p in parts if p))
    for ctx in local_check_contexts:
        if not isinstance(ctx, dict):
            continue
        call_ea = str(ctx.get("call_ea", "")).strip()
        callee = str(ctx.get("callee", "")).strip()
        caller = str(ctx.get("caller_func", "")).strip()
        ref_strings = str(ctx.get("ref_strings", "")).strip()
        call_disasm = str(ctx.get("call_disasm", "")).strip()
        nearby = str(ctx.get("nearby", "")).strip()
        imm_args = str(ctx.get("imm_args", "")).strip()
        parts = [
            f"IDA局部校验上下文: call={call_ea}" if call_ea else "IDA局部校验上下文",
            f"callee={callee}" if callee else "",
            f"caller={caller}" if caller else "",
            f"insn={call_disasm}" if call_disasm else "",
            f"strings={ref_strings}" if ref_strings else "",
            f"imm={imm_args}" if imm_args else "",
            f"nearby={nearby}" if nearby else "",
        ]
        artifact.evidence.append(" ".join(p for p in parts if p))
    for ctx in control_id_contexts:
        if not isinstance(ctx, dict):
            continue
        ea = str(ctx.get("ea", "")).strip()
        caller = str(ctx.get("caller_func", "")).strip()
        insn = str(ctx.get("insn", "")).strip()
        nearby = str(ctx.get("nearby", "")).strip()
        parts = [
            f"IDA控件ID上下文: ea={ea}" if ea else "IDA控件ID上下文",
            f"caller={caller}" if caller else "",
            f"insn={insn}" if insn else "",
            f"nearby={nearby}" if nearby else "",
        ]
        artifact.evidence.append(" ".join(p for p in parts if p))
    for ctx in string_xrefs:
        if not isinstance(ctx, dict):
            continue
        string_value = str(ctx.get("string", "")).strip()
        xref_ea = str(ctx.get("xref_ea", "")).strip()
        caller = str(ctx.get("caller_func", "")).strip()
        nearby = str(ctx.get("nearby", "")).strip()
        parts = [
            f"IDA字符串引用: xref={xref_ea}" if xref_ea else "IDA字符串引用",
            f"caller={caller}" if caller else "",
            f"string={string_value}" if string_value else "",
            f"nearby={nearby}" if nearby else "",
        ]
        artifact.evidence.append(" ".join(p for p in parts if p))
    for ctx in validation_function_candidates:
        if not isinstance(ctx, dict):
            continue
        func = str(ctx.get("function", "")).strip()
        reason = str(ctx.get("reason", "")).strip()
        score = str(ctx.get("score", "")).strip()
        parts = [
            f"IDA校验函数候选: function={func}" if func else "IDA校验函数候选",
            f"score={score}" if score else "",
            f"reason={reason}" if reason else "",
        ]
        artifact.evidence.append(" ".join(p for p in parts if p))
    for hint in solver_hints:
        if isinstance(hint, dict):
            value = str(hint.get("kind", "") or hint.get("hint", "")).strip()
            reason = str(hint.get("reason", "")).strip()
            artifact.evidence.append(
                " ".join(
                    part
                    for part in (
                        f"IDA求解提示: {value}" if value else "IDA求解提示",
                        f"reason={reason}" if reason else "",
                    )
                    if part
                )
            )
        else:
            value = str(hint).strip()
            if value:
                artifact.evidence.append(f"IDA求解提示: {value}")
    hexrays_available = bool(data.get("hexrays_available"))
    if decompiler_snippets:
        artifact.evidence.append(f"IDA反编译片段: {len(decompiler_snippets)} 条")
    artifact.success = True
    artifact.summary = (
        f"IDA 自动分析完成：字符串 {len(data.get('strings', []))} 条，"
        f"函数 {len(data.get('functions', []))} 个，"
        f"比较上下文 {len(data.get('compare_contexts', []))} 条，"
        f"局部校验上下文 {len(data.get('local_check_contexts', []))} 条，"
        f"控件ID上下文 {len(data.get('control_id_contexts', []))} 条，"
        f"字符串引用 {len(data.get('string_xrefs', []))} 条，"
        f"校验函数候选 {len(data.get('validation_function_candidates', []))} 个，"
        f"Hex-Rays 可用={hexrays_available}。"
    )
    return artifact


def _build_olly_script_command(
    script_path: str, ollydbg_executable: str, target_file: Path, output_path: Path
) -> list[str]:
    suffix = Path(script_path).suffix.lower()
    if suffix == ".py":
        return [
            sys.executable,
            script_path,
            "--olly",
            ollydbg_executable,
            "--target",
            str(target_file),
            "--out",
            str(output_path),
        ]
    if suffix == ".ps1":
        return [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            script_path,
            "-OllyPath",
            ollydbg_executable,
            "-TargetPath",
            str(target_file),
            "-OutputPath",
            str(output_path),
        ]
    return [
        script_path,
        "--olly",
        ollydbg_executable,
        "--target",
        str(target_file),
        "--out",
        str(output_path),
    ]


def _run_ollydbg(
    file_path: Path,
    config: ToolAutomationConfig,
    artifacts_dir: Path,
    log: LogFn,
) -> ToolRunArtifact:
    artifact = ToolRunArtifact(
        tool_name="OllyDbg",
        enabled=True,
        attempted=False,
        success=False,
    )
    ollydbg_executable = _resolve_ollydbg_executable(config.ollydbg_executable)
    if not ollydbg_executable:
        artifact.error = "未找到 OllyDbg 可执行文件（请在界面配置 ollydbg.exe 路径）。"
        artifact.summary = "OllyDbg 自动分析未执行。"
        return artifact

    olly_script = _resolve_ollydbg_script(config.ollydbg_script_path)
    if not olly_script:
        artifact.error = (
            "未找到 OllyDbg 自动化脚本。请提供脚本路径（支持 .py/.ps1/.bat/.cmd/.exe）。"
        )
        artifact.summary = "OllyDbg 自动分析未执行。"
        return artifact

    output_path = artifacts_dir / f"{file_path.stem}_ollydbg_evidence.json"
    log_path = artifacts_dir / f"{file_path.stem}_ollydbg.log"
    command_args = _build_olly_script_command(
        script_path=olly_script,
        ollydbg_executable=ollydbg_executable,
        target_file=file_path,
        output_path=output_path,
    )
    artifact.command = " ".join(shlex.quote(a) for a in command_args)
    artifact.output_path = str(output_path)
    artifact.attempted = True
    log("正在执行 OllyDbg 自动化脚本...")

    try:
        proc = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=config.ollydbg_timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        artifact.error = f"OllyDbg 自动化超时（>{config.ollydbg_timeout_seconds} 秒）。"
        artifact.summary = "OllyDbg 自动分析超时。"
        return artifact

    combined_output = (
        f"[stdout]\n{proc.stdout or ''}\n\n[stderr]\n{proc.stderr or ''}".strip()
    )
    log_path.write_text(combined_output, encoding="utf-8", errors="replace")

    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "").strip()
        artifact.error = details[:2000] if details else "OllyDbg 脚本未返回可读错误信息。"
        artifact.summary = f"OllyDbg 执行失败（退出码 {proc.returncode}）。"
        return artifact

    if output_path.exists():
        if not _populate_artifact_from_json_output(
            artifact=artifact,
            output_path=output_path,
            tool_name="OllyDbg",
        ):
            return artifact
        if not artifact.summary:
            artifact.summary = "OllyDbg 自动分析完成。"
    else:
        artifact.summary = (
            "OllyDbg 自动化脚本执行完成，但未生成证据文件。"
            f" 已写入日志：{log_path}"
        )

    artifact.success = True
    if str(log_path) not in artifact.evidence:
        artifact.evidence.append(f"OllyDbg日志: {log_path}")
    return artifact
