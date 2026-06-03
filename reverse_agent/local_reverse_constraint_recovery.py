from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from reverse_agent.local_reverse_ida_guided_solver import (
    _is_under_root,
    _policy_timeout,
    _preflight,
    _read_artifact_evidence,
    classify_validation,
    resolve_current_artifact,
)
from reverse_agent.local_reverse_runtime import PREVIEW_LIMIT, run_probe

STAGE = "local_reverse_constraint_recovery_sprint_v1"
DEFAULT_RESULT = "project_state/local_reverse_constraint_recovery_result.json"
MAX_CANDIDATES_PER_TARGET = 64
MAX_VALIDATIONS_TOTAL = 192
TARGET_RE = re.compile(r'"([0-9A-Za-z:]{32,80})"')

ProbeRunner = Callable[..., dict[str, Any]]


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    result = run_constraint_recovery(
        ida_summary=_read_json(Path(args.ida_summary)),
        artifact_index=_read_json(Path(args.artifact_index)),
        solver_result=_read_json(Path(args.solver_result)),
        policy=_read_json(Path(args.policy)),
        source_solver_result=str(Path(args.solver_result)),
    )
    _write_json(Path(args.out), result)
    print(
        "local reverse constraint recovery: "
        f"status={result['status']} "
        f"targets={result['target_count']} "
        f"candidates={result['candidate_count']} "
        f"validated={result['validated_count']}"
    )
    return 2 if result["status"] == "BLOCKED" else 0


def run_constraint_recovery(
    *,
    ida_summary: dict[str, Any],
    artifact_index: dict[str, Any],
    solver_result: dict[str, Any],
    policy: dict[str, Any],
    source_solver_result: str = "project_state\\local_reverse_ida_solver_result.json",
    probe_runner: ProbeRunner = run_probe,
    preview_limit: int = PREVIEW_LIMIT,
    max_candidates_per_target: int = MAX_CANDIDATES_PER_TARGET,
    max_total_validations: int = MAX_VALIDATIONS_TOTAL,
) -> dict[str, Any]:
    blocked_reasons = _preflight(ida_summary, artifact_index)
    root = Path(str(policy.get("root") or "")).resolve()
    runtime_allowed = bool(policy.get("runtime_allowed"))
    timeout = _policy_timeout(policy)

    solver_targets = {
        str(item.get("sample_id", "")): item for item in solver_result.get("targets", [])
    }
    remaining_validations = max_total_validations
    targets: list[dict[str, Any]] = []
    for summary_target in ida_summary.get("targets", []):
        target, remaining_validations = recover_target(
            summary_target=summary_target,
            solver_target=solver_targets.get(str(summary_target.get("sample_id", "")), {}),
            artifact_index=artifact_index,
            root=root,
            timeout=timeout,
            runtime_allowed=runtime_allowed,
            probe_runner=probe_runner,
            preview_limit=preview_limit,
            global_blocked_reasons=blocked_reasons,
            max_candidates_per_target=max_candidates_per_target,
            remaining_validations=remaining_validations,
        )
        targets.append(target)

    candidate_count = sum(len(target.get("candidates", [])) for target in targets)
    validated_count = sum(1 for target in targets if target.get("validated_candidate"))
    blocked_targets = [t for t in targets if t.get("constraint_status") == "blocked"]
    if blocked_reasons or not targets or len(blocked_targets) == len(targets):
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
        "source_solver_result": source_solver_result,
        "target_count": len(targets),
        "candidate_count": candidate_count,
        "validated_count": validated_count,
        "targets": targets,
    }


def recover_target(
    *,
    summary_target: dict[str, Any],
    solver_target: dict[str, Any],
    artifact_index: dict[str, Any],
    root: Path,
    timeout: int,
    runtime_allowed: bool,
    probe_runner: ProbeRunner,
    preview_limit: int,
    global_blocked_reasons: list[str],
    max_candidates_per_target: int,
    remaining_validations: int,
) -> tuple[dict[str, Any], int]:
    sample_id = str(summary_target.get("sample_id", ""))
    relative_path = str(summary_target.get("relative_path", ""))
    classification = str(solver_target.get("classification", ""))
    artifact_key = f"local_reverse_ida_evidence_{sample_id}"
    artifact_path, artifact_reasons = resolve_current_artifact(artifact_index, artifact_key)
    evidence, read_reasons = _read_artifact_evidence(artifact_path, artifact_key)
    resolution_reasons = artifact_reasons + read_reasons

    recovered_constraints: list[dict[str, Any]] = []
    candidate_generation = {
        "strategy": "none",
        "count": 0,
        "bounded_reason": "",
    }
    candidates: list[dict[str, Any]] = []
    validation_results: list[dict[str, Any]] = []
    validated_candidate = ""
    blocked_reason = ""
    next_action = ""
    constraint_status = "partial"

    if global_blocked_reasons:
        constraint_status = "blocked"
        blocked_reason = "; ".join(global_blocked_reasons)
        next_action = "repair project_state local_reverse evidence registration"
    elif resolution_reasons:
        constraint_status = "blocked"
        blocked_reason = "; ".join(resolution_reasons)
        next_action = "repair artifact_index local_reverse evidence path"
    else:
        constraints, candidates, candidate_generation, blocked_reason, next_action = recover_constraints(
            sample_id=sample_id,
            classification=classification,
            evidence=evidence,
            max_candidates=max_candidates_per_target,
        )
        recovered_constraints.extend(constraints)
        if blocked_reason:
            constraint_status = "blocked"
        elif candidates:
            constraint_status = "recovered"
        else:
            constraint_status = "partial"

    if (
        constraint_status != "blocked"
        and candidates
        and runtime_allowed
        and remaining_validations > 0
    ):
        validation_results, validated_candidate, remaining_validations = validate_candidates(
            candidates=candidates,
            root=root,
            relative_path=relative_path,
            timeout=timeout,
            probe_runner=probe_runner,
            preview_limit=preview_limit,
            remaining_validations=remaining_validations,
        )
        if validated_candidate:
            blocked_reason = ""
            constraint_status = "recovered"
        elif validation_results:
            blocked_reason = "candidate rejected by bounded runtime probe"
            next_action = (
                "inspect sub_40100A hook data flow and confirm file compare source"
                if classification.startswith("api_")
                else next_action
            )

    return (
        {
            "sample_id": sample_id,
            "relative_path": relative_path,
            "classification": classification or "unknown",
            "constraint_status": constraint_status,
            "recovered_constraints": recovered_constraints,
            "candidate_generation": candidate_generation,
            "candidates": candidates,
            "validation_results": validation_results,
            "validated_candidate": validated_candidate,
            "blocked_reason": blocked_reason,
            "next_action": next_action or "collect additional static evidence",
        },
        remaining_validations,
    )


def recover_constraints(
    *,
    sample_id: str,
    classification: str,
    evidence: dict[str, Any],
    max_candidates: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], str, str]:
    if classification == "api_assisted_password_write_and_compare":
        return recover_cpp1_constraints(evidence, max_candidates)
    if classification == "bounded_input_range_hash_output_increment_compare":
        return recover_cpp2_constraints(evidence)
    if classification == "sha256_hex_compare_with_post_hash_character_adjustment":
        return recover_sha_constraints(evidence)
    return (
        [{"kind": "missing_profile", "detail": "no constraint recovery for profile"}],
        [],
        {"strategy": "none", "count": 0, "bounded_reason": "unsupported classification"},
        "UNSUPPORTED_CLASSIFICATION",
        "add classification-specific constraint recovery",
    )


def recover_cpp1_constraints(
    evidence: dict[str, Any],
    max_candidates: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], str, str]:
    constants = _extract_xor_constants(evidence)
    literal_targets = _extract_literal_targets(evidence, min_len=3, max_len=16)
    preferred_targets = [text for text in literal_targets if text in {"realpwd", "pwd.txt"}]
    if not preferred_targets:
        preferred_targets = [text for text in literal_targets if "pwd" in text.lower()]
    constraints = [
        {"kind": "xor_constants", "value": constants},
        {"kind": "hook_detail", "value": "WriteFile patched to sub_40100A before file write"},
    ]
    if preferred_targets:
        constraints.append({"kind": "string_targets", "value": preferred_targets})

    if not constants or not preferred_targets:
        return (
            constraints,
            [],
            {"strategy": "none", "count": 0, "bounded_reason": "missing xor constants or target strings"},
            "MISSING_XOR_RELATION",
            "recover WriteFile hook and target string data flow",
        )

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for target in preferred_targets:
        if len(target) != len(constants):
            continue
        candidate = "".join(chr(constant ^ ord(target[idx])) for idx, constant in enumerate(constants))
        if candidate in seen:
            continue
        seen.add(candidate)
        candidates.append(
            {
                "candidate": candidate,
                "source_relation": "xor_constants_against_literal",
                "constants_used": constants,
                "string_target": target,
                "transform_formula": "candidate[i] = constants[i] XOR target[i]",
                "why_bounded": "constants and target strings recovered from IDA decompiler evidence",
                "validation_status": "unverified",
            }
        )
        if len(candidates) >= max_candidates:
            break

    candidate_generation = {
        "strategy": "xor_constants_against_evidence_strings",
        "count": len(candidates),
        "bounded_reason": "targets derived from realpwd/pwd.txt literals in IDA evidence",
    }
    blocked_reason = "" if candidates else "NO_BOUNDED_CANDIDATE"
    next_action = (
        "inspect sub_40100A hook data flow and confirm file compare source"
        if candidates
        else "recover hook stub sub_40100A decompiler snippet"
    )
    return constraints, candidates, candidate_generation, blocked_reason, next_action


def recover_cpp2_constraints(
    evidence: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], str, str]:
    snippet = _extract_snippet(evidence, "_main_0")
    input_range = _extract_input_range(snippet)
    min_length = _extract_min_length(snippet)
    prefix_length = _extract_prefix_length(snippet)
    target = _extract_compare_target(evidence)
    target_before_increment = _decrement_string(target, wrap_hex=False) if target else ""
    constraints = [
        {"kind": "input_range", "value": input_range},
        {"kind": "min_length", "value": min_length},
        {"kind": "prefix_length", "value": prefix_length},
        {"kind": "compare_target", "value": target},
        {"kind": "target_before_increment", "value": target_before_increment},
        {"kind": "hash_function", "value": "sub_401005"},
    ]
    blocked_reason = "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005"
    next_action = "recover sub_401005 transform or bounded dictionary before inversion"
    return (
        constraints,
        [],
        {"strategy": "none", "count": 0, "bounded_reason": blocked_reason},
        blocked_reason,
        next_action,
    )


def recover_sha_constraints(
    evidence: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], str, str]:
    snippet = _extract_snippet(evidence, "_main_0")
    min_length = _extract_min_length(snippet)
    prefix_length = _extract_prefix_length(snippet)
    target = _extract_compare_target(evidence)
    target_before_increment = _decrement_string(target, wrap_hex=True) if target else ""
    constraints = [
        {"kind": "min_length", "value": min_length},
        {"kind": "prefix_length", "value": prefix_length},
        {"kind": "compare_target", "value": target},
        {"kind": "target_before_increment", "value": target_before_increment},
        {"kind": "hash_function", "value": "sub_401005"},
        {"kind": "post_increment_wrap", "value": "hex_wrap"},
    ]
    blocked_reason = "NO_BOUNDED_HASH_PREIMAGE_DOMAIN"
    next_action = "targeted static re-extraction of input length/domain or request problem statement hint"
    return (
        constraints,
        [],
        {"strategy": "none", "count": 0, "bounded_reason": blocked_reason},
        blocked_reason,
        next_action,
    )


def validate_candidates(
    *,
    candidates: list[dict[str, Any]],
    root: Path,
    relative_path: str,
    timeout: int,
    probe_runner: ProbeRunner,
    preview_limit: int,
    remaining_validations: int,
) -> tuple[list[dict[str, Any]], str, int]:
    validation_results: list[dict[str, Any]] = []
    validated_candidate = ""
    path = (root / relative_path).resolve()
    if not _is_under_root(path, root) or not path.exists():
        for candidate in candidates:
            candidate["validation_status"] = "blocked"
        return (
            [
                {
                    "candidate": "",
                    "validation_status": "blocked",
                    "validation_error": "PATH_UNAVAILABLE",
                }
            ],
            "",
            remaining_validations,
        )

    for candidate in candidates:
        if remaining_validations <= 0:
            candidate["validation_status"] = "blocked"
            continue
        probe = probe_runner(
            path=path,
            probe_name=f"candidate_{len(validation_results) + 1}",
            stdin_text=f"{candidate['candidate']}\n",
            timeout=timeout,
            preview_limit=preview_limit,
        )
        remaining_validations -= 1
        validation_status = classify_validation(probe)
        candidate["validation_status"] = validation_status
        result = {
            "candidate": candidate["candidate"],
            "probe_name": probe.get("probe_name"),
            "exit_code": probe.get("exit_code"),
            "timeout": probe.get("timeout"),
            "classification": probe.get("classification"),
            "stdout_preview": probe.get("stdout_preview"),
            "stderr_preview": probe.get("stderr_preview"),
            "duration_ms": probe.get("duration_ms"),
            "validation_status": validation_status,
        }
        validation_results.append(result)
        if validation_status == "validated":
            validated_candidate = candidate["candidate"]
            break
    return validation_results, validated_candidate, remaining_validations


def _extract_compare_target(evidence: dict[str, Any]) -> str:
    for ctx in evidence.get("compare_contexts", []):
        for value in (ctx.get("ref_strings"), ctx.get("nearby")):
            match = TARGET_RE.search(str(value))
            if match:
                return match.group(1)
    for snippet in evidence.get("decompiler_snippets", []):
        if isinstance(snippet, dict):
            match = TARGET_RE.search(str(snippet.get("text", "")))
            if match:
                return match.group(1)
    return ""


def _extract_snippet(evidence: dict[str, Any], function_name: str) -> str:
    for snippet in evidence.get("decompiler_snippets", []):
        if isinstance(snippet, dict) and snippet.get("function") == function_name:
            return str(snippet.get("text", ""))
    return ""


def _extract_input_range(snippet: str) -> str:
    match = re.search(r"Source\[i\]\s*<\s*(\d+)\s*\|\|\s*Source\[i\]\s*>\s*(\d+)", snippet)
    if match:
        return f"{match.group(1)}..{match.group(2)}"
    return ""


def _extract_min_length(snippet: str) -> int | None:
    match = re.search(r"strlen\(Source\)\s*>=\s*(\d+)", snippet)
    if match:
        return int(match.group(1))
    match = re.search(r"if\s*\(\s*v\d+\s*>=\s*(\d+)\s*\)", snippet)
    if match:
        return int(match.group(1))
    return None


def _extract_prefix_length(snippet: str) -> int | None:
    match = re.search(r"strncpy\([^,]+,\s*Source,\s*(\d+)u\)", snippet)
    if match:
        return int(match.group(1))
    return None


def _decrement_string(value: str, *, wrap_hex: bool) -> str:
    if not value:
        return ""
    lowered = value.lower()
    result = []
    for idx, char in enumerate(lowered):
        if wrap_hex:
            if char == "0":
                result.append("9")
                continue
            if char == "a":
                result.append("f")
                continue
        code = ord(char) - 1
        result.append(chr(code))
    return "".join(result)


def _extract_xor_constants(evidence: dict[str, Any]) -> list[int]:
    constants: list[int] = []
    for snippet in evidence.get("decompiler_snippets", []):
        if not isinstance(snippet, dict):
            continue
        text = str(snippet.get("text", ""))
        for match in re.finditer(r"Str\[(\d+)\]\s*=\s*(-?\d+);", text):
            idx = int(match.group(1))
            value = int(match.group(2)) & 0xFF
            while len(constants) <= idx:
                constants.append(0)
            constants[idx] = value
    return constants


def _extract_literal_targets(evidence: dict[str, Any], *, min_len: int, max_len: int) -> list[str]:
    literals: set[str] = set()
    for snippet in evidence.get("decompiler_snippets", []):
        if not isinstance(snippet, dict):
            continue
        for match in re.finditer(r'"([^"\r\n]{%d,%d})"' % (min_len, max_len), str(snippet.get("text", ""))):
            literals.add(match.group(1))
    for ctx in evidence.get("local_check_contexts", []):
        for value in (ctx.get("ref_strings"), ctx.get("nearby")):
            for match in re.finditer(r"([A-Za-z0-9_.]{%d,%d})" % (min_len, max_len), str(value)):
                literals.add(match.group(1))
    return sorted(literals)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recover local reverse constraints and generate candidates.")
    parser.add_argument("--ida-summary", default="project_state/local_reverse_ida_summary.json")
    parser.add_argument("--artifact-index", default="project_state/artifact_index.json")
    parser.add_argument("--solver-result", default="project_state/local_reverse_ida_solver_result.json")
    parser.add_argument("--policy", default="project_state/local_reverse_runtime_policy.json")
    parser.add_argument("--out", default=DEFAULT_RESULT)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
