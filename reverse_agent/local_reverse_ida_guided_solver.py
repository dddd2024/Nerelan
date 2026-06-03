from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from reverse_agent.local_reverse_runtime import PREVIEW_LIMIT, run_probe

STAGE = "ida_summary_guided_solver_v1"
DEFAULT_RESULT = "project_state/local_reverse_ida_solver_result.json"
TARGET_HASH_RE = re.compile(r'"([0-9A-Za-z:]{32,80})"')

ProbeRunner = Callable[..., dict[str, Any]]


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    result = run_ida_guided_solver(
        ida_summary=_read_json(Path(args.ida_summary)),
        artifact_index=_read_json(Path(args.artifact_index)),
        policy=_read_json(Path(args.policy)),
        source_summary=str(Path(args.ida_summary)),
    )
    _write_json(Path(args.out), result)
    print(
        "local reverse IDA-guided solver: "
        f"status={result['status']} "
        f"targets={result['target_count']} "
        f"solved={result['solved_count']} "
        f"validated={result['validated_count']}"
    )
    return 2 if result["status"] == "BLOCKED" else 0


def run_ida_guided_solver(
    *,
    ida_summary: dict[str, Any],
    artifact_index: dict[str, Any],
    policy: dict[str, Any],
    source_summary: str = "project_state\\local_reverse_ida_summary.json",
    probe_runner: ProbeRunner = run_probe,
    preview_limit: int = PREVIEW_LIMIT,
) -> dict[str, Any]:
    targets = []
    blocked_reasons = _preflight(ida_summary, artifact_index)
    root = Path(str(policy.get("root") or "")).resolve()
    timeout = _policy_timeout(policy)
    runtime_allowed = bool(policy.get("runtime_allowed"))

    for summary_target in ida_summary.get("targets", []):
        target = solve_target(
            summary_target=summary_target,
            artifact_index=artifact_index,
            root=root,
            timeout=timeout,
            runtime_allowed=runtime_allowed,
            probe_runner=probe_runner,
            preview_limit=preview_limit,
            global_blocked_reasons=blocked_reasons,
        )
        targets.append(target)

    solved_count = sum(1 for target in targets if target.get("validation_status") == "validated")
    validated_count = sum(1 for target in targets if target.get("validation_status") == "validated")
    if blocked_reasons or any(target.get("validation_status") == "blocked" for target in targets):
        status = "BLOCKED"
    elif validated_count == len(targets) and targets:
        status = "SUCCESS"
    else:
        status = "PARTIAL"

    return {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "stage": STAGE,
        "status": status,
        "source_summary": source_summary,
        "target_count": len(targets),
        "solved_count": solved_count,
        "validated_count": validated_count,
        "runtime_validation_attempted_count": sum(
            1 for target in targets if target.get("validation_evidence")
        ),
        "blocked_reasons": blocked_reasons,
        "targets": targets,
    }


def solve_target(
    *,
    summary_target: dict[str, Any],
    artifact_index: dict[str, Any],
    root: Path,
    timeout: int,
    runtime_allowed: bool,
    probe_runner: ProbeRunner,
    preview_limit: int,
    global_blocked_reasons: list[str],
) -> dict[str, Any]:
    sample_id = str(summary_target.get("sample_id", ""))
    relative_path = str(summary_target.get("relative_path", ""))
    artifact_key = f"local_reverse_ida_evidence_{sample_id}"
    artifact_path, artifact_reasons = resolve_current_artifact(artifact_index, artifact_key)
    evidence, read_reasons = _read_artifact_evidence(artifact_path, artifact_key)
    resolution_reasons = artifact_reasons + read_reasons

    classification, profile, classification_evidence = classify_target(summary_target, evidence)
    candidate, candidate_source, candidate_reason = derive_candidate(profile, evidence)
    validation_status = "unverified"
    validation_evidence: list[dict[str, Any]] = []
    blocked_reason = ""
    next_action = next_action_for(profile, candidate, validation_status)

    if global_blocked_reasons:
        validation_status = "blocked"
        blocked_reason = "; ".join(global_blocked_reasons)
        next_action = "repair project_state local_reverse evidence registration"
    elif resolution_reasons:
        validation_status = "blocked"
        blocked_reason = "; ".join(resolution_reasons)
        next_action = "repair artifact_index local_reverse evidence path"
    elif not candidate:
        blocked_reason = candidate_reason
        next_action = next_action_for(profile, candidate, validation_status)
    elif runtime_allowed and _can_runtime_probe(profile):
        probe = validate_candidate(
            root=root,
            relative_path=relative_path,
            candidate=candidate,
            timeout=timeout,
            probe_runner=probe_runner,
            preview_limit=preview_limit,
        )
        validation_evidence.append(probe)
        validation_status = classify_validation(probe)
        if validation_status == "rejected":
            blocked_reason = "candidate rejected by bounded runtime probe"
        elif validation_status == "unverified":
            blocked_reason = "runtime probe did not emit a decisive success marker"
        else:
            blocked_reason = ""
        next_action = next_action_for(profile, candidate, validation_status)
    elif candidate:
        blocked_reason = "candidate derived statically but runtime validation was not attempted"

    return {
        "sample_id": sample_id,
        "relative_path": relative_path,
        "ida_evidence_path": str(artifact_path) if artifact_path else "",
        "classification": classification,
        "classification_evidence": classification_evidence,
        "selected_solver_profile": profile,
        "candidate": candidate,
        "candidate_source": candidate_source,
        "candidate_reason": candidate_reason,
        "validation_status": validation_status,
        "validation_evidence": validation_evidence,
        "blocked_reason": blocked_reason,
        "next_action": next_action,
    }


def classify_target(summary_target: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, str, list[str]]:
    text = _evidence_text(evidence).lower()
    compare_contexts = evidence.get("compare_contexts", [])
    snippets = [str(item.get("text", "")) for item in evidence.get("decompiler_snippets", []) if isinstance(item, dict)]
    snippet_text = "\n".join(snippets).lower()

    has_64_compare = any("40h" in str(ctx) or "0x40" in str(ctx) for ctx in compare_contexts)
    has_hex_format = "%08x" in text
    has_hash_target = bool(re.search(r"[0-9a-f]{64}", text))
    has_hash_flow = "source" in snippet_text or "sub_401005" in snippet_text or "hash" in text
    if has_64_compare and has_hex_format and has_hash_target and has_hash_flow:
        return (
            "sha256_hex_compare_with_post_hash_character_adjustment",
            "hash_hex_compare_static",
            [
                "IDA compare context shows _strncmp(..., 0x40)",
                "local call context shows sprintf with eight %08x words",
                "decompiler shows Source prefix copied into hash routine before 64-byte compare",
            ],
        )

    has_range_check = "source[i] < 65" in text and "source[i] > 122" in text
    has_increment = "++str1" in text or "++Str1" in _evidence_text(evidence)
    if has_64_compare and has_range_check and has_increment:
        return (
            "bounded_input_range_hash_output_increment_compare",
            "bounded_char_transform_inversion",
            [
                "IDA decompiler shows input byte range 65..122",
                "IDA decompiler shows post-transform ++Str1 over 64 bytes",
                "IDA compare context shows 64-byte _strncmp target",
            ],
        )

    has_pwd_string = "realpwd" in text or re.search(r"\bpwd\b", text) is not None
    has_api_compare = "writefile" in text and "lstrcmp" in text
    has_data_flow = bool(snippets) and ("str[" in snippet_text or "buffer" in snippet_text)
    if has_pwd_string and has_api_compare and has_data_flow:
        return (
            "api_assisted_password_write_and_compare",
            "direct_or_api_password_extraction",
            [
                "main_0 stores direct string realpwd",
                "sub_401100 XORs a 7-byte constant with user input before WriteFile",
                "main_0 compares buffered content through lstrcmpA",
            ],
        )

    if any("direct_strcmp" in str(item) for item in evidence.get("solver_hints", [])):
        return (
            "string_compare_direct",
            "string_compare_direct",
            ["IDA solver_hints include direct_strcmp"],
        )

    return (
        "needs_more_static_evidence",
        "needs_more_static_evidence",
        ["no supported IDA-guided profile matched current evidence"],
    )


def derive_candidate(profile: str, evidence: dict[str, Any]) -> tuple[str, str, str]:
    if profile == "direct_or_api_password_extraction":
        target = _quoted_string_named(evidence, "realpwd")
        constants = _xor_constants(evidence)
        if target and constants:
            candidate = "".join(chr(value ^ ord(target[idx])) for idx, value in enumerate(constants[: len(target)]))
            return (
                candidate,
                "ida_decompiler_xor_constant_to_direct_string",
                "XOR byte constants against direct string realpwd",
            )
        if target:
            return (
                target,
                "ida_decompiler_direct_string",
                "direct string found but XOR input relation was not recovered",
            )
    if profile == "hash_hex_compare_static":
        target = _compare_target(evidence)
        return (
            "",
            "ida_strncmp_hash_target",
            f"hash target {target} has no bounded preimage domain in current evidence",
        )
    if profile == "bounded_char_transform_inversion":
        target = _compare_target(evidence)
        return (
            "",
            "ida_range_and_transform_target",
            f"visible post-transform target {target} still depends on uninverted upstream hash routine",
        )
    return ("", "", "no evidence-backed candidate source for selected profile")


def validate_candidate(
    *,
    root: Path,
    relative_path: str,
    candidate: str,
    timeout: int,
    probe_runner: ProbeRunner,
    preview_limit: int,
) -> dict[str, Any]:
    path = (root / relative_path).resolve()
    if not _is_under_root(path, root):
        return {
            "probe_name": "candidate_static_1",
            "candidate": candidate,
            "validation_error": "PATH_OUTSIDE_ROOT",
            "timeout": False,
            "stdout_preview": "",
            "stderr_preview": "",
            "classification": "blocked",
        }
    if not path.exists() or not path.is_file():
        return {
            "probe_name": "candidate_static_1",
            "candidate": candidate,
            "validation_error": "SAMPLE_MISSING",
            "timeout": False,
            "stdout_preview": "",
            "stderr_preview": "",
            "classification": "blocked",
        }
    probe = probe_runner(
        path=path,
        probe_name="candidate_static_1",
        stdin_text=f"{candidate}\n",
        timeout=timeout,
        preview_limit=preview_limit,
    )
    return {
        "candidate": candidate,
        "probe_name": str(probe.get("probe_name", "")),
        "exit_code": probe.get("exit_code"),
        "timeout": bool(probe.get("timeout")),
        "classification": str(probe.get("classification", "")),
        "stdout_preview": str(probe.get("stdout_preview", "")),
        "stderr_preview": str(probe.get("stderr_preview", "")),
        "duration_ms": probe.get("duration_ms"),
    }


def classify_validation(probe: dict[str, Any]) -> str:
    if probe.get("validation_error") or str(probe.get("classification")) == "blocked":
        return "blocked"
    if probe.get("timeout"):
        return "unverified"
    text = f"{probe.get('stdout_preview', '')}\n{probe.get('stderr_preview', '')}".lower()
    has_strict_success = any(marker in text for marker in ("correct", "well done", "accepted", "congratulations"))
    has_failure = any(marker in text for marker in ("wrong", "fail", "invalid", "try again"))
    if has_strict_success and not has_failure:
        return "validated"
    if has_failure:
        return "rejected"
    return "unverified"


def next_action_for(profile: str, candidate: str, validation_status: str) -> str:
    if validation_status == "validated":
        return "record validated candidate and include it in final local_reverse handoff"
    if validation_status == "rejected":
        return "inspect the remaining compare/control-flow relation before trusting the static candidate"
    if profile == "hash_hex_compare_static":
        return "add bounded input-domain evidence or a symbolic/hash preimage constraint before candidate validation"
    if profile == "bounded_char_transform_inversion":
        return "recover or model the upstream hash/transform routine before attempting bounded inversion"
    if profile == "direct_or_api_password_extraction" and candidate:
        return "confirm candidate with a side-effect-controlled verifier or manual runtime transcript"
    if profile == "needs_more_static_evidence":
        return "collect more static comparison/data-flow evidence"
    return "review IDA evidence and refine solver profile"


def _preflight(ida_summary: dict[str, Any], artifact_index: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if ida_summary.get("status") != "SUCCESS":
        reasons.append("IDA_SUMMARY_NOT_SUCCESS")
    targets = ida_summary.get("targets", [])
    if not isinstance(targets, list) or len(targets) != 3:
        reasons.append("IDA_SUMMARY_TARGET_COUNT_NOT_3")
    _, summary_reasons = resolve_current_artifact(artifact_index, "local_reverse_ida_summary")
    reasons.extend(summary_reasons)
    return sorted(set(reasons))


def resolve_current_artifact(artifact_index: dict[str, Any], artifact_key: str) -> tuple[Path | None, list[str]]:
    latest_v2 = artifact_index.get("latest_artifacts_v2", {})
    if not isinstance(latest_v2, dict):
        return None, [f"ARTIFACT_V2_MISSING:{artifact_key}"]
    item = latest_v2.get(artifact_key)
    if not isinstance(item, dict):
        return None, [f"ARTIFACT_V2_MISSING:{artifact_key}"]
    freshness = str(item.get("freshness") or "unknown")
    if freshness != "current":
        return None, [f"ARTIFACT_NOT_CURRENT:{artifact_key}:{freshness}"]
    raw_path = str(item.get("path") or "")
    if not raw_path:
        return None, [f"ARTIFACT_PATH_MISSING:{artifact_key}"]
    path = Path(raw_path)
    if not path.exists() or not path.is_file():
        return path, [f"ARTIFACT_FILE_MISSING:{artifact_key}:{raw_path}"]
    return path, []


def _read_artifact_evidence(path: Path | None, artifact_key: str) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return {}, []
    try:
        return _read_json(path), []
    except json.JSONDecodeError:
        return {}, [f"ARTIFACT_JSON_INVALID:{artifact_key}:{path}"]


def _evidence_text(evidence: dict[str, Any]) -> str:
    return json.dumps(evidence, ensure_ascii=False)


def _compare_target(evidence: dict[str, Any]) -> str:
    text = _evidence_text(evidence)
    for match in TARGET_HASH_RE.findall(text):
        if len(match) >= 32 and "__GLOBAL" not in match:
            return match
    return ""


def _quoted_string_named(evidence: dict[str, Any], value: str) -> str:
    text = _evidence_text(evidence)
    return value if value in text else ""


def _xor_constants(evidence: dict[str, Any]) -> list[int]:
    text = "\n".join(
        str(item.get("text", ""))
        for item in evidence.get("decompiler_snippets", [])
        if isinstance(item, dict)
    )
    constants: list[int] = []
    for match in re.finditer(r"Str\[(\d+)\]\s*=\s*(-?\d+);", text):
        idx = int(match.group(1))
        value = int(match.group(2)) & 0xFF
        while len(constants) <= idx:
            constants.append(0)
        constants[idx] = value
    return constants


def _can_runtime_probe(profile: str) -> bool:
    return profile == "direct_or_api_password_extraction"


def _policy_timeout(policy: dict[str, Any]) -> int:
    default_timeout = int(policy.get("default_timeout_seconds") or 5)
    max_timeout = int(policy.get("max_timeout_seconds") or 15)
    return max(1, min(default_timeout, max_timeout))


def _is_under_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded IDA-summary-guided local reverse solver.")
    parser.add_argument("--ida-summary", default="project_state/local_reverse_ida_summary.json")
    parser.add_argument("--artifact-index", default="project_state/artifact_index.json")
    parser.add_argument("--policy", default="project_state/local_reverse_runtime_policy.json")
    parser.add_argument("--out", default=DEFAULT_RESULT)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
