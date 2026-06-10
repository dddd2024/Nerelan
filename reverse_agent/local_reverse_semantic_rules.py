from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.local_reverse_compare_site import TARGET_SAMPLE_IDS
from reverse_agent.local_reverse_runtime import PREVIEW_LIMIT, run_probe
from reverse_agent.local_reverse_string_solver import is_candidate_input, validation_succeeded

STAGE = "bounded_semantic_rule_extraction"
PREVIOUS_MISSING_EVIDENCE = "new_xref_candidates_failed_runtime_validation"
DEFAULT_MAX_RULES_PER_SAMPLE = 20
DEFAULT_MAX_CANDIDATES_PER_SAMPLE = 20
DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE = 20
SUPPORTED_MNEMONICS = {
    "add",
    "and",
    "call",
    "cmp",
    "je",
    "jge",
    "jg",
    "jl",
    "jle",
    "jmp",
    "jne",
    "jnz",
    "jz",
    "lea",
    "mov",
    "movsx",
    "or",
    "push",
    "sub",
    "test",
    "xor",
}
TRANSFORM_MNEMONICS = {"add", "sub", "xor"}
JUMP_MNEMONICS = {"je", "jne", "jz", "jnz", "jg", "jge", "jl", "jle", "jmp"}
BYTE_REGISTERS = {"al", "ah", "bl", "bh", "cl", "ch", "dl", "dh"}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    result = run_semantic_rule_extraction(
        corpus_index=_read_json(Path(args.corpus_index)),
        xref_result=_read_json(Path(args.xref_result)),
        policy=_read_json(Path(args.policy)),
        max_rules_per_sample=args.max_rules_per_sample,
        max_candidates_per_sample=args.max_candidates_per_sample,
        max_runtime_validations_per_sample=args.max_runtime_validations_per_sample,
        preview_limit=args.preview_limit,
    )
    _write_json(Path(args.out), result)

    print(
        "local reverse semantic rule extraction: "
        f"status={result['status']} "
        f"targets={result['target_count']} "
        f"solved={result['solved_count']}"
    )
    return 2 if result["status"] == "BLOCKED" else 0


def run_semantic_rule_extraction(
    *,
    corpus_index: dict[str, Any],
    xref_result: dict[str, Any],
    policy: dict[str, Any],
    max_rules_per_sample: int = DEFAULT_MAX_RULES_PER_SAMPLE,
    max_candidates_per_sample: int = DEFAULT_MAX_CANDIDATES_PER_SAMPLE,
    max_runtime_validations_per_sample: int = DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE,
    preview_limit: int = PREVIEW_LIMIT,
) -> dict[str, Any]:
    root = Path(str(policy.get("root") or corpus_index.get("root") or "")).resolve()
    runtime_allowed = bool(policy.get("runtime_allowed"))
    timeout = _policy_timeout(policy)
    corpus_by_id = {str(item.get("sample_id", "")): item for item in corpus_index.get("samples", [])}
    selected = select_xref_targets(xref_result)
    global_blocked: list[str] = []
    if not root.exists():
        global_blocked.append("ROOT_UNAVAILABLE")
    if not runtime_allowed:
        global_blocked.append("RUNTIME_NOT_ALLOWED_BY_POLICY")

    targets = []
    for previous in selected:
        target = extract_target(
            previous_target=previous,
            corpus_sample=corpus_by_id.get(str(previous.get("sample_id", ""))),
            root=root,
            runtime_allowed=runtime_allowed,
            timeout=timeout,
            preview_limit=preview_limit,
            max_rules_per_sample=max_rules_per_sample,
            max_candidates_per_sample=max_candidates_per_sample,
            max_runtime_validations_per_sample=max_runtime_validations_per_sample,
            global_blocked=global_blocked,
        )
        targets.append(target)

    blocked_reasons = sorted({reason for target in targets for reason in target.get("blocked_reasons", [])})
    solved_count = sum(1 for target in targets if target.get("solved"))
    if not targets or any(target.get("status") == "BLOCKED" for target in targets):
        status = "BLOCKED"
    elif solved_count == len(targets):
        status = "SUCCESS"
    else:
        status = "PARTIAL"

    return {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "stage": STAGE,
        "status": status,
        "target_count": len(targets),
        "solved_count": solved_count,
        "bounds": {
            "max_rules_per_sample": max_rules_per_sample,
            "max_candidates_per_sample": max_candidates_per_sample,
            "max_runtime_validations_per_sample": max_runtime_validations_per_sample,
        },
        "timeout_seconds": timeout,
        "blocked_reasons": blocked_reasons,
        "targets": targets,
    }


def select_xref_targets(xref_result: dict[str, Any]) -> list[dict[str, Any]]:
    selected = []
    for target in xref_result.get("targets", []):
        sample_id = str(target.get("sample_id", ""))
        if sample_id not in TARGET_SAMPLE_IDS:
            continue
        if target.get("solved") is True:
            continue
        if target.get("missing_evidence") != PREVIOUS_MISSING_EVIDENCE:
            continue
        selected.append(target)
    selected.sort(key=lambda item: str(item.get("sample_id", "")))
    return selected


def extract_target(
    *,
    previous_target: dict[str, Any],
    corpus_sample: dict[str, Any] | None,
    root: Path,
    runtime_allowed: bool,
    timeout: int,
    preview_limit: int,
    max_rules_per_sample: int,
    max_candidates_per_sample: int,
    max_runtime_validations_per_sample: int,
    global_blocked: list[str],
) -> dict[str, Any]:
    sample_id = str(previous_target.get("sample_id", ""))
    relative_path = str(previous_target.get("relative_path", ""))
    blocked_reasons = validate_target(
        previous_target=previous_target,
        corpus_sample=corpus_sample,
        root=root,
        runtime_allowed=runtime_allowed,
        global_blocked=global_blocked,
    )
    rules = extract_semantic_rules(previous_target, max_rules=max_rules_per_sample)
    previous_failed = collect_previous_failed_candidates(previous_target)
    candidates = build_semantic_candidates(
        rules=rules,
        previous_failed_candidates=previous_failed,
        max_candidates=max_candidates_per_sample,
    )

    validations: list[dict[str, Any]] = []
    solved = False
    solution = None
    runtime_evidence = None
    if not blocked_reasons:
        path = (root / relative_path).resolve()
        for candidate in candidates[:max_runtime_validations_per_sample]:
            probe = run_probe(
                path=path,
                probe_name=f"semantic_rule_candidate_{len(validations) + 1}",
                stdin_text=f"{candidate['candidate']}\n",
                timeout=timeout,
                preview_limit=preview_limit,
            )
            validation = {
                "candidate": candidate["candidate"],
                "source": candidate["source"],
                "rule_type": candidate.get("rule_type"),
                "rule_id": candidate.get("rule_id"),
                "revalidated_reason": candidate.get("revalidated_reason"),
                "probe": probe,
                "succeeded": validation_succeeded(probe),
            }
            validations.append(validation)
            if validation["succeeded"]:
                solved = True
                solution = candidate["candidate"]
                runtime_evidence = validation
                break

    missing_evidence = None if solved else classify_missing_evidence(rules, candidates, blocked_reasons)
    return {
        "sample_id": sample_id,
        "relative_path": relative_path,
        "sha256": str((corpus_sample or previous_target).get("sha256", "")),
        "previous_missing_evidence": previous_target.get("missing_evidence"),
        "semantic_rule_count": len(rules),
        "semantic_rules": rules,
        "generated_candidate_count": len(candidates),
        "generated_candidates": candidates,
        "validated_candidate_count": len(validations),
        "validation_results_preview": validations[:max_runtime_validations_per_sample],
        "solved": solved,
        "solution": solution,
        "runtime_evidence": runtime_evidence,
        "missing_evidence": missing_evidence,
        "next_action": next_action_for_missing_evidence(missing_evidence),
        "status": "BLOCKED" if blocked_reasons else ("SOLVED" if solved else "NO_CANDIDATE_VALIDATED"),
        "blocked_reasons": blocked_reasons,
    }


def validate_target(
    *,
    previous_target: dict[str, Any],
    corpus_sample: dict[str, Any] | None,
    root: Path,
    runtime_allowed: bool,
    global_blocked: list[str],
) -> list[str]:
    reasons = list(global_blocked)
    if not runtime_allowed and "RUNTIME_NOT_ALLOWED_BY_POLICY" not in reasons:
        reasons.append("RUNTIME_NOT_ALLOWED_BY_POLICY")
    if corpus_sample is None:
        reasons.append("MISSING_CORPUS_SAMPLE")
        return sorted(set(reasons))

    path = (root / str(corpus_sample.get("relative_path") or "")).resolve()
    if not _is_under_root(path, root):
        reasons.append("PATH_OUTSIDE_ROOT")
    if not path.exists():
        reasons.append("SAMPLE_MISSING")
    elif _sha256_file(path) != str(corpus_sample.get("sha256", "")):
        reasons.append("SHA256_MISMATCH")
    if str(corpus_sample.get("sample_id", "")) != str(previous_target.get("sample_id", "")):
        reasons.append("SAMPLE_ID_MISMATCH")
    return sorted(set(reasons))


def extract_semantic_rules(target: dict[str, Any], *, max_rules: int) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for window_index, window in enumerate(target.get("disassembly_windows", [])):
        instructions = [
            item
            for item in window.get("instructions", [])
            if str(item.get("mnemonic", "")).lower() in SUPPORTED_MNEMONICS
        ]
        for rule in extract_window_rules(window, instructions, window_index):
            key = _rule_key(rule)
            if key in seen:
                continue
            seen.add(key)
            rule["rule_id"] = f"rule_{len(rules) + 1:03d}"
            rules.append(rule)
            if len(rules) >= max_rules:
                return rules
    return rules


def extract_window_rules(
    window: dict[str, Any],
    instructions: list[dict[str, Any]],
    window_index: int,
) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for index, instruction in enumerate(instructions):
        mnemonic = str(instruction.get("mnemonic", "")).lower()
        op_str = str(instruction.get("op_str", "")).lower()
        operands = _split_operands(op_str)

        if "[" in op_str and "ebp" in op_str:
            access_size = _access_size(op_str)
            offset = _stack_offset(op_str)
            if offset is not None:
                rules.append(_rule(
                    "stack_buffer",
                    "medium" if access_size == "byte" else "low",
                    window,
                    window_index,
                    [instruction],
                    {"base": "ebp", "offset": offset, "access_size": access_size},
                    False,
                ))

        if mnemonic == "cmp" and len(operands) == 2:
            immediate = _parse_int(operands[1])
            if immediate is not None:
                source = [instruction]
                next_jump = _next_jump(instructions, index)
                if next_jump is not None:
                    source.append(next_jump)
                if _looks_like_length_or_loop_cmp(operands[0], immediate):
                    rules.append(_rule(
                        "loop_bound" if next_jump is not None else "length_check",
                        "medium" if next_jump is not None else "low",
                        window,
                        window_index,
                        source,
                        {
                            "left": operands[0],
                            "bound": immediate,
                            "branch": None if next_jump is None else next_jump.get("mnemonic"),
                            "branch_target": None if next_jump is None else next_jump.get("op_str"),
                        },
                        True,
                    ))
                if 0 <= immediate <= 0xFF:
                    rules.append(_rule(
                        "byte_cmp_const",
                        "medium" if _is_printable_byte(immediate) else "low",
                        window,
                        window_index,
                        source,
                        {"left": operands[0], "constant": immediate, "char": chr(immediate) if _is_printable_byte(immediate) else ""},
                        _is_printable_byte(immediate),
                    ))

        if mnemonic in {"mov", "movsx"} and len(operands) == 2:
            if operands[1].startswith("byte ptr ["):
                rules.append(_rule(
                    "byte_load",
                    "medium",
                    window,
                    window_index,
                    [instruction],
                    {"destination": operands[0], "source": operands[1], "stack_offset": _stack_offset(operands[1])},
                    False,
                ))
            if operands[0].startswith("byte ptr ["):
                immediate = _parse_int(operands[1])
                rules.append(_rule(
                    "byte_store",
                    "medium",
                    window,
                    window_index,
                    [instruction],
                    {
                        "destination": operands[0],
                        "source": operands[1],
                        "constant": immediate,
                        "char": chr(immediate) if immediate is not None and _is_printable_byte(immediate) else "",
                    },
                    immediate is not None and _is_printable_byte(immediate),
                ))

        if mnemonic in TRANSFORM_MNEMONICS and len(operands) == 2:
            immediate = _parse_int(operands[1])
            if immediate is not None and (operands[0] in BYTE_REGISTERS or operands[0].startswith("byte ptr [")):
                rules.append(_rule(
                    f"byte_{mnemonic}_const",
                    "medium",
                    window,
                    window_index,
                    [instruction],
                    {"target": operands[0], "constant": immediate},
                    True,
                ))

        replacement = _replacement_rule_at(window, instructions, window_index, index)
        if replacement is not None:
            rules.append(replacement)
    return rules


def build_semantic_candidates(
    *,
    rules: list[dict[str, Any]],
    previous_failed_candidates: set[str],
    max_candidates: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    length = _candidate_length(rules)
    for rule in rules:
        if not rule.get("candidate_generation_enabled"):
            continue
        for value, source in candidate_values_for_rule(rule, length):
            revalidated = value in previous_failed_candidates
            _add_candidate(
                candidates,
                value,
                source,
                rule,
                revalidated_reason="semantic_rule_derived" if revalidated else None,
            )
            if len(candidates) >= max_candidates:
                return candidates
    return candidates


def candidate_values_for_rule(rule: dict[str, Any], length: int | None) -> list[tuple[str, str]]:
    constraint = rule.get("inferred_constraint", {})
    rule_type = str(rule.get("rule_type", ""))
    values: list[tuple[str, str]] = []
    if rule_type == "byte_cmp_const":
        constant = constraint.get("constant")
        if isinstance(constant, int) and _is_printable_byte(constant):
            char = chr(constant)
            values.append((_shape_candidate(char, length), "semantic_byte_cmp_const"))
    elif rule_type in {"byte_add_const", "byte_sub_const", "byte_xor_const"}:
        constant = constraint.get("constant")
        if isinstance(constant, int):
            for observed in _likely_observed_bytes():
                original = _invert_transform(rule_type, observed, constant)
                if _is_printable_byte(original):
                    values.append((_shape_candidate(chr(original), length), f"semantic_{rule_type}_inverse"))
    elif rule_type == "replacement_rule":
        before = constraint.get("compare_constant")
        after = constraint.get("replacement_constant")
        if isinstance(before, int) and _is_printable_byte(before):
            values.append((_shape_candidate(chr(before), length), "semantic_replacement_before"))
        if isinstance(after, int) and _is_printable_byte(after):
            values.append((_shape_candidate(chr(after), length), "semantic_replacement_after"))
    elif rule_type == "byte_store":
        constant = constraint.get("constant")
        if isinstance(constant, int) and _is_printable_byte(constant):
            values.append((_shape_candidate(chr(constant), length), "semantic_byte_store_const"))
    return values


def collect_previous_failed_candidates(target: dict[str, Any]) -> set[str]:
    failed = set()
    for validation in target.get("validation_results_preview", []):
        candidate = str(validation.get("candidate", ""))
        if candidate:
            failed.add(candidate)
    for candidate in target.get("generated_candidates", []):
        value = str(candidate.get("candidate", ""))
        if value:
            failed.add(value)
    return failed


def classify_missing_evidence(
    rules: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    blocked_reasons: list[str],
) -> str:
    if blocked_reasons:
        return "blocked_precondition"
    if not rules:
        return "semantic_rule_not_found"
    if not any(rule.get("rule_type") == "byte_cmp_const" for rule in rules):
        return "compare_constants_incomplete"
    if any(str(rule.get("rule_type", "")).startswith("byte_") and str(rule.get("rule_type", "")).endswith("_const") for rule in rules) and not candidates:
        return "transform_rule_found_but_inverse_failed"
    if not candidates:
        return "needs_manual_address_seed"
    return "needs_symbolic_execution"


def next_action_for_missing_evidence(missing_evidence: str | None) -> str:
    actions = {
        None: "solution validated by semantic rule candidate",
        "blocked_precondition": "fix runtime/path/hash precondition before semantic validation",
        "semantic_rule_not_found": "seed a manual address or IDA decompiler summary for rule extraction",
        "transform_rule_found_but_inverse_failed": "inspect transform chain and compare constants manually",
        "compare_constants_incomplete": "extract additional compare constants from the current windows",
        "needs_symbolic_execution": "use bounded symbolic execution over extracted semantic windows",
        "needs_ida_decompiler_summary": "summarize decompiled validation function for this sample",
        "needs_manual_address_seed": "provide a manual validation-function address seed",
    }
    return actions.get(missing_evidence, "review semantic extraction artifact")


def _rule(
    rule_type: str,
    confidence: str,
    window: dict[str, Any],
    window_index: int,
    source_instructions: list[dict[str, Any]],
    inferred_constraint: dict[str, Any],
    candidate_generation_enabled: bool,
) -> dict[str, Any]:
    return {
        "rule_type": rule_type,
        "confidence": confidence,
        "source_window": {
            "window_index": window_index,
            "window_raw_start": window.get("window_raw_start"),
            "window_raw_end": window.get("window_raw_end"),
            "xref": window.get("xref"),
        },
        "source_instructions": [_instruction_view(item) for item in source_instructions],
        "inferred_constraint": inferred_constraint,
        "candidate_generation_enabled": candidate_generation_enabled,
    }


def _replacement_rule_at(
    window: dict[str, Any],
    instructions: list[dict[str, Any]],
    window_index: int,
    index: int,
) -> dict[str, Any] | None:
    instruction = instructions[index]
    if str(instruction.get("mnemonic", "")).lower() != "cmp":
        return None
    operands = _split_operands(str(instruction.get("op_str", "")).lower())
    if len(operands) != 2:
        return None
    compare_constant = _parse_int(operands[1])
    if compare_constant is None:
        return None
    nearby = instructions[index + 1:index + 5]
    jump = next((item for item in nearby if str(item.get("mnemonic", "")).lower() in JUMP_MNEMONICS), None)
    store = next((item for item in nearby if _is_byte_store_const(item)), None)
    if jump is None or store is None:
        return None
    store_operands = _split_operands(str(store.get("op_str", "")).lower())
    replacement_constant = _parse_int(store_operands[1]) if len(store_operands) == 2 else None
    if replacement_constant is None:
        return None
    return _rule(
        "replacement_rule",
        "medium",
        window,
        window_index,
        [instruction, jump, store],
        {
            "compare_left": operands[0],
            "compare_constant": compare_constant,
            "compare_char": chr(compare_constant) if _is_printable_byte(compare_constant) else "",
            "branch": jump.get("mnemonic"),
            "replacement_constant": replacement_constant,
            "replacement_char": chr(replacement_constant) if _is_printable_byte(replacement_constant) else "",
        },
        _is_printable_byte(compare_constant) or _is_printable_byte(replacement_constant),
    )


def _candidate_length(rules: list[dict[str, Any]]) -> int | None:
    bounds = []
    for rule in rules:
        if rule.get("rule_type") not in {"length_check", "loop_bound"}:
            continue
        bound = rule.get("inferred_constraint", {}).get("bound")
        if isinstance(bound, int) and 4 <= bound <= 64:
            bounds.append(bound)
    return min(bounds) if bounds else None


def _shape_candidate(char: str, length: int | None) -> str:
    size = length if length is not None and 4 <= length <= 64 else 4
    return char * size


def _likely_observed_bytes() -> list[int]:
    values = []
    for start, end in ((ord("0"), ord("9")), (ord("A"), ord("Z")), (ord("a"), ord("z"))):
        values.extend(range(start, end + 1))
    return values


def _invert_transform(rule_type: str, observed: int, constant: int) -> int:
    if rule_type == "byte_add_const":
        return (observed - constant) & 0xFF
    if rule_type == "byte_sub_const":
        return (observed + constant) & 0xFF
    if rule_type == "byte_xor_const":
        return observed ^ constant
    return observed


def _add_candidate(
    candidates: list[dict[str, Any]],
    value: str,
    source: str,
    rule: dict[str, Any],
    *,
    revalidated_reason: str | None,
) -> None:
    candidate = value.strip()
    if not is_candidate_input(candidate):
        return
    if any(existing["candidate"] == candidate for existing in candidates):
        return
    item = {
        "candidate": candidate,
        "source": source,
        "rule_id": rule.get("rule_id"),
        "rule_type": rule.get("rule_type"),
    }
    if revalidated_reason:
        item["revalidated_reason"] = revalidated_reason
    candidates.append(item)


def _rule_key(rule: dict[str, Any]) -> tuple[Any, ...]:
    constraint = rule.get("inferred_constraint", {})
    return (
        rule.get("rule_type"),
        json.dumps(constraint, sort_keys=True, ensure_ascii=True),
        tuple(item.get("address") for item in rule.get("source_instructions", [])),
    )


def _instruction_view(instruction: dict[str, Any]) -> dict[str, Any]:
    return {
        "address": instruction.get("address"),
        "rva": instruction.get("rva"),
        "mnemonic": instruction.get("mnemonic"),
        "op_str": instruction.get("op_str"),
    }


def _next_jump(instructions: list[dict[str, Any]], index: int) -> dict[str, Any] | None:
    for item in instructions[index + 1:index + 4]:
        if str(item.get("mnemonic", "")).lower() in JUMP_MNEMONICS:
            return item
    return None


def _looks_like_length_or_loop_cmp(left: str, immediate: int) -> bool:
    if not 1 <= immediate <= 512:
        return False
    return "dword ptr" in left or "ebp" in left or left in {"eax", "ecx", "edx", "esi", "edi"}


def _is_byte_store_const(instruction: dict[str, Any]) -> bool:
    if str(instruction.get("mnemonic", "")).lower() != "mov":
        return False
    operands = _split_operands(str(instruction.get("op_str", "")).lower())
    return len(operands) == 2 and operands[0].startswith("byte ptr [") and _parse_int(operands[1]) is not None


def _split_operands(op_str: str) -> list[str]:
    operands = []
    current = []
    depth = 0
    for char in op_str:
        if char == "[":
            depth += 1
        elif char == "]":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            operands.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        operands.append("".join(current).strip())
    return operands


def _parse_int(text: str) -> int | None:
    value = text.strip().lower()
    try:
        if value.startswith("0x"):
            return int(value, 16)
        if re.fullmatch(r"-?\d+", value):
            return int(value, 10)
    except ValueError:
        return None
    return None


def _stack_offset(op_str: str) -> int | None:
    match = re.search(r"\[\s*ebp\b[^\]]*?-\s*(0x[0-9a-f]+|\d+)", op_str.lower())
    if not match:
        return None
    return _parse_int(match.group(1))


def _access_size(op_str: str) -> str:
    text = op_str.lower()
    if "byte ptr" in text:
        return "byte"
    if "word ptr" in text:
        return "word"
    if "dword ptr" in text:
        return "dword"
    return "unknown"


def _is_printable_byte(value: int) -> bool:
    return 0x20 <= value <= 0x7E


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


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded local reverse semantic rule extraction.")
    parser.add_argument("--corpus-index", default="project_state/local_reverse_corpus_index.json")
    parser.add_argument("--xref-result", default="project_state/local_reverse_xref_disassembly_result.json")
    parser.add_argument("--policy", default="project_state/local_reverse_runtime_policy.json")
    parser.add_argument("--out", default="project_state/local_reverse_semantic_rule_result.json")
    parser.add_argument("--max-rules-per-sample", type=int, default=DEFAULT_MAX_RULES_PER_SAMPLE)
    parser.add_argument("--max-candidates-per-sample", type=int, default=DEFAULT_MAX_CANDIDATES_PER_SAMPLE)
    parser.add_argument(
        "--max-runtime-validations-per-sample",
        type=int,
        default=DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE,
    )
    parser.add_argument("--preview-limit", type=int, default=PREVIEW_LIMIT)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
