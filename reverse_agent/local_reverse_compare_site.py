from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.local_reverse_runtime import PREVIEW_LIMIT, run_probe
from reverse_agent.local_reverse_string_solver import (
    FAILURE_MARKERS,
    MISSING_EVIDENCE,
    NEGATIVE_RESULT,
    SUCCESS_MARKERS,
    is_candidate_input,
    validation_succeeded,
)

STAGE = "bounded_compare_site_static_extraction"
TARGET_SAMPLE_IDS = {
    "4c69f173f2bd0211",
    "bcbd9979db015bfd",
    "18019fca52b389fe",
}
DEFAULT_MAX_NEW_CANDIDATES_PER_SAMPLE = 30
DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE = 30
STRING_SCAN_LIMIT = 3000
SUCCESS_HINTS = tuple(dict.fromkeys((*SUCCESS_MARKERS, "congratulations", "you are right")))
FAILURE_HINTS = tuple(dict.fromkeys((*FAILURE_MARKERS, "try it again", "hang on")))
PROMPT_HINTS = (
    "give me",
    "input",
    "password",
    "please",
    "press any key",
    "your answer",
    "your flag",
)
COMPARE_IMPORT_HINTS = {
    "strcmp",
    "strncmp",
    "stricmp",
    "strcmpi",
    "lstrcmp",
    "lstrcmpa",
    "lstrcmpw",
    "memcmp",
    "comparestring",
}
COMPARE_TEXT_HINTS = (
    "strcmp",
    "strncmp",
    "memcmp",
    "compare",
    "correct",
    "success",
    "wrong",
    "try again",
)


@dataclass(frozen=True)
class ExtractedString:
    value: str
    encoding: str
    offset: int


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    result = run_compare_site_extraction(
        corpus_index=_read_json(Path(args.corpus_index)),
        benchmark=_read_json(Path(args.benchmark)),
        string_result=_read_json(Path(args.string_result)),
        policy=_read_json(Path(args.policy)),
        max_new_candidates_per_sample=args.max_new_candidates_per_sample,
        max_runtime_validations_per_sample=args.max_runtime_validations_per_sample,
        preview_limit=args.preview_limit,
    )
    _write_json(Path(args.out), result)

    print(
        "local reverse compare-site extraction: "
        f"status={result['status']} "
        f"targets={result['target_count']} "
        f"solved={result['solved_count']}"
    )
    return 2 if result["status"] == "BLOCKED" else 0


def run_compare_site_extraction(
    *,
    corpus_index: dict[str, Any],
    benchmark: dict[str, Any],
    string_result: dict[str, Any],
    policy: dict[str, Any],
    max_new_candidates_per_sample: int = DEFAULT_MAX_NEW_CANDIDATES_PER_SAMPLE,
    max_runtime_validations_per_sample: int = DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE,
    preview_limit: int = PREVIEW_LIMIT,
) -> dict[str, Any]:
    root = Path(str(policy.get("root") or corpus_index.get("root") or "")).resolve()
    timeout = _policy_timeout(policy)
    runtime_allowed = bool(policy.get("runtime_allowed"))
    corpus_by_id = {str(item.get("sample_id", "")): item for item in corpus_index.get("samples", [])}
    benchmark_by_id = {str(item.get("sample_id", "")): item for item in benchmark.get("samples", [])}
    previous_targets = select_previous_unsolved_targets(string_result)
    blocked_reasons: list[str] = []

    if not root.exists():
        blocked_reasons.append("ROOT_UNAVAILABLE")
    if not runtime_allowed:
        blocked_reasons.append("RUNTIME_NOT_ALLOWED_BY_POLICY")

    targets = []
    for previous in previous_targets:
        target = extract_target(
            previous_target=previous,
            corpus_sample=corpus_by_id.get(str(previous.get("sample_id", ""))),
            benchmark_sample=benchmark_by_id.get(str(previous.get("sample_id", ""))),
            root=root,
            runtime_allowed=runtime_allowed,
            timeout=timeout,
            preview_limit=preview_limit,
            max_new_candidates_per_sample=max_new_candidates_per_sample,
            max_runtime_validations_per_sample=max_runtime_validations_per_sample,
            global_blocked=bool(blocked_reasons),
        )
        targets.append(target)
        blocked_reasons.extend(target.get("blocked_reasons", []))

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
        "max_new_candidates_per_sample": max_new_candidates_per_sample,
        "max_runtime_validations_per_sample": max_runtime_validations_per_sample,
        "timeout_seconds": timeout,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "targets": targets,
    }


def select_previous_unsolved_targets(string_result: dict[str, Any]) -> list[dict[str, Any]]:
    selected = []
    for target in string_result.get("targets", []):
        sample_id = str(target.get("sample_id", ""))
        if sample_id not in TARGET_SAMPLE_IDS:
            continue
        if target.get("solved") is True:
            continue
        if target.get("negative_result") != NEGATIVE_RESULT:
            continue
        if target.get("missing_evidence") != MISSING_EVIDENCE:
            continue
        selected.append(target)
    selected.sort(key=lambda item: str(item.get("sample_id", "")))
    return selected


def extract_target(
    *,
    previous_target: dict[str, Any],
    corpus_sample: dict[str, Any] | None,
    benchmark_sample: dict[str, Any] | None,
    root: Path,
    runtime_allowed: bool,
    timeout: int,
    preview_limit: int,
    max_new_candidates_per_sample: int,
    max_runtime_validations_per_sample: int,
    global_blocked: bool,
) -> dict[str, Any]:
    sample_id = str(previous_target.get("sample_id", ""))
    relative_path = str(previous_target.get("relative_path", ""))
    blocked_reasons = validate_target(
        previous_target=previous_target,
        corpus_sample=corpus_sample,
        benchmark_sample=benchmark_sample,
        root=root,
        runtime_allowed=runtime_allowed,
        global_blocked=global_blocked,
    )
    base = {
        "sample_id": sample_id,
        "relative_path": relative_path,
        "sha256": str((corpus_sample or previous_target).get("sha256", "")),
        "previous_negative_result": previous_target.get("negative_result"),
        "previous_missing_evidence": previous_target.get("missing_evidence"),
        "compare_site_status": "blocked" if blocked_reasons else "not_found",
        "compare_site_evidence": {},
        "strings_summary": _empty_strings_summary(),
        "new_candidate_count": 0,
        "validated_candidate_count": 0,
        "solved": False,
        "solution": None,
        "runtime_evidence": None,
        "missing_evidence": "blocked_precondition" if blocked_reasons else "compare_site_not_found",
        "next_action": "fix blocked precondition before compare-site extraction"
        if blocked_reasons
        else "bounded IDA/capstone compare-site extraction",
        "status": "BLOCKED" if blocked_reasons else "NO_CANDIDATE_VALIDATED",
        "blocked_reasons": blocked_reasons,
    }
    if blocked_reasons or corpus_sample is None:
        return base

    path = (root / str(corpus_sample.get("relative_path") or "")).resolve()
    data = path.read_bytes()
    strings = extract_strings_with_offsets(data, max_count=STRING_SCAN_LIMIT)
    strings_summary = summarize_strings(strings)
    compare_evidence = collect_compare_site_evidence(data, strings)
    previous_candidates = {
        str(item.get("candidate", ""))
        for item in previous_target.get("validation_results_preview", [])
        if item.get("candidate")
    }
    candidates = build_new_candidates(
        strings_summary=strings_summary,
        previous_candidates=previous_candidates,
        max_candidates=max_new_candidates_per_sample,
    )

    validation_results = []
    solved_probe: dict[str, Any] | None = None
    validations = min(len(candidates), max_runtime_validations_per_sample)
    for candidate in candidates[:validations]:
        probe = run_probe(
            path=path,
            probe_name=f"compare_site_candidate_{len(validation_results) + 1}",
            stdin_text=f"{candidate['candidate']}\n",
            timeout=timeout,
            preview_limit=preview_limit,
        )
        success = validation_succeeded(probe)
        validation = {
            "candidate": candidate["candidate"],
            "source": candidate["source"],
            "probe_name": probe["probe_name"],
            "exit_code": probe["exit_code"],
            "timeout": probe["timeout"],
            "classification": probe["classification"],
            "success": success,
            "stdout_preview": probe["stdout_preview"],
            "stderr_preview": probe["stderr_preview"],
            "duration_ms": probe["duration_ms"],
        }
        validation_results.append(validation)
        if success:
            solved_probe = validation
            break

    solved = solved_probe is not None
    missing_evidence = None if solved else classify_missing_evidence(compare_evidence, strings_summary, candidates)
    compare_site_status = "found" if compare_evidence.get("found") else "not_found"
    base.update({
        "compare_site_status": compare_site_status,
        "compare_site_evidence": compare_evidence,
        "strings_summary": strings_summary,
        "new_candidate_count": len(candidates),
        "validated_candidate_count": len(validation_results),
        "new_candidate_sources": summarize_candidate_sources(candidates),
        "validation_results_preview": validation_results[:10],
        "solved": solved,
        "solution": solved_probe["candidate"] if solved_probe else None,
        "runtime_evidence": solved_probe,
        "missing_evidence": missing_evidence,
        "next_action": next_action_for_missing(missing_evidence),
        "status": "SOLVED" if solved else "NO_CANDIDATE_VALIDATED",
    })
    return base


def validate_target(
    *,
    previous_target: dict[str, Any],
    corpus_sample: dict[str, Any] | None,
    benchmark_sample: dict[str, Any] | None,
    root: Path,
    runtime_allowed: bool,
    global_blocked: bool,
) -> list[str]:
    reasons: list[str] = []
    if global_blocked:
        reasons.append("GLOBAL_RUNTIME_PRECONDITION_FAILED")
    if not runtime_allowed:
        reasons.append("RUNTIME_NOT_ALLOWED_BY_POLICY")
    if corpus_sample is None:
        reasons.append("MISSING_CORPUS_SAMPLE")
        return reasons
    if benchmark_sample is None:
        reasons.append("MISSING_BENCHMARK_SAMPLE")
    elif str(benchmark_sample.get("solve_readiness")) != "ready_static_string_compare":
        reasons.append("BENCHMARK_SAMPLE_NOT_READY_STATIC_STRING_COMPARE")
    if str(previous_target.get("sample_id")) not in TARGET_SAMPLE_IDS:
        reasons.append("TARGET_NOT_IN_SCOPE")

    path = (root / str(corpus_sample.get("relative_path") or "")).resolve()
    if not _is_under_root(path, root):
        reasons.append("PATH_OUTSIDE_ROOT")
    if not path.exists():
        reasons.append("SAMPLE_MISSING")
    elif _sha256_file(path) != str(corpus_sample.get("sha256", "")):
        reasons.append("SHA256_MISMATCH")
    return reasons


def extract_strings_with_offsets(data: bytes, *, min_length: int = 4, max_count: int = STRING_SCAN_LIMIT) -> list[ExtractedString]:
    strings: list[ExtractedString] = []
    for match in re.finditer(rb"[\x20-\x7E]{%d,}" % min_length, data):
        strings.append(ExtractedString(match.group().decode("ascii", errors="replace"), "ascii", match.start()))
        if len(strings) >= max_count:
            return strings
    for match in re.finditer(rb"(?:[\x20-\x7E]\x00){%d,}" % min_length, data):
        strings.append(ExtractedString(match.group().decode("utf-16le", errors="replace"), "utf16le", match.start()))
        if len(strings) >= max_count:
            return strings
    return strings


def summarize_strings(strings: list[ExtractedString]) -> dict[str, list[dict[str, Any]]]:
    summary = _empty_strings_summary()
    for item in strings:
        lower = item.value.lower()
        entry = {"value": item.value[:160], "encoding": item.encoding, "offset": item.offset}
        if any(hint in lower for hint in PROMPT_HINTS):
            _append_limited(summary["prompt_strings"], entry)
        if any(hint in lower for hint in FAILURE_HINTS):
            _append_limited(summary["failure_strings"], entry)
        if any(hint in lower for hint in SUCCESS_HINTS):
            _append_limited(summary["success_strings"], entry)
        if is_candidate_input(item.value):
            _append_limited(summary["candidate_constant_strings"], entry, limit=100)
    return summary


def collect_compare_site_evidence(data: bytes, strings: list[ExtractedString]) -> dict[str, Any]:
    imports = collect_compare_imports(data)
    keyword_hits = []
    for item in strings:
        lower = item.value.lower()
        if any(hint in lower for hint in COMPARE_TEXT_HINTS):
            keyword_hits.append({"value": item.value[:160], "encoding": item.encoding, "offset": item.offset})
        if len(keyword_hits) >= 20:
            break
    return {
        "found": bool(imports or keyword_hits),
        "compare_imports": imports,
        "compare_keyword_strings": keyword_hits,
        "disassembly_backend": optional_disassembly_backend_status(),
    }


def collect_compare_imports(data: bytes) -> list[str]:
    try:
        import pefile  # type: ignore

        pe = pefile.PE(data=data, fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
    except Exception:
        return []

    imports: list[str] = []
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        for imported in getattr(entry, "imports", []):
            name = getattr(imported, "name", None)
            if not name:
                continue
            decoded = name.decode("ascii", errors="ignore")
            if decoded.lower() in COMPARE_IMPORT_HINTS:
                imports.append(decoded)
    return sorted(set(imports))


def optional_disassembly_backend_status() -> dict[str, Any]:
    try:
        import capstone  # noqa: F401  # type: ignore

        return {"capstone": "available", "used": False, "reason": "bytes_and_import_evidence_sufficient_for_bounded_round"}
    except Exception:
        return {"capstone": "missing", "used": False, "reason": "optional_backend_unavailable"}


def build_new_candidates(
    *,
    strings_summary: dict[str, list[dict[str, Any]]],
    previous_candidates: set[str],
    max_candidates: int,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for source in ("candidate_constant_strings", "success_strings"):
        for item in strings_summary.get(source, []):
            value = str(item.get("value", "")).strip()
            if value in previous_candidates:
                continue
            if not is_candidate_input(value):
                continue
            if any(existing["candidate"] == value for existing in candidates):
                continue
            candidates.append({"candidate": value, "source": source})
            if len(candidates) >= max_candidates:
                return candidates
    return candidates


def classify_missing_evidence(
    compare_evidence: dict[str, Any],
    strings_summary: dict[str, list[dict[str, Any]]],
    candidates: list[dict[str, str]],
) -> str:
    if not compare_evidence.get("found"):
        return "compare_site_not_found"
    if not strings_summary.get("candidate_constant_strings"):
        return "target_constant_not_found"
    if candidates:
        return "new_candidates_failed_runtime_validation"
    if strings_summary.get("success_strings") and not compare_evidence.get("compare_imports"):
        return "success_string_found_but_no_xref_backend"
    if not candidates:
        return "new_candidate_not_found"
    return "new_candidate_not_found"


def next_action_for_missing(missing_evidence: str | None) -> str | None:
    if missing_evidence is None:
        return None
    actions = {
        "compare_site_not_found": "bounded IDA/capstone compare-site extraction",
        "target_constant_not_found": "extract compare target constant or input length constraint",
        "success_string_found_but_no_xref_backend": "add bounded xref extraction around success and failure strings",
        "new_candidate_not_found": "add bounded compare-site immediate/string operand extraction",
        "new_candidates_failed_runtime_validation": "inspect compare-site xrefs before generating more candidates",
        "blocked_precondition": "fix blocked precondition before compare-site extraction",
    }
    return actions.get(missing_evidence, "bounded compare-site follow-up")


def summarize_candidate_sources(candidates: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate["source"]] = counts.get(candidate["source"], 0) + 1
    return [{"source": source, "count": count} for source, count in sorted(counts.items())]


def _empty_strings_summary() -> dict[str, list[dict[str, Any]]]:
    return {
        "prompt_strings": [],
        "failure_strings": [],
        "success_strings": [],
        "candidate_constant_strings": [],
    }


def _append_limited(values: list[dict[str, Any]], entry: dict[str, Any], limit: int = 20) -> None:
    if len(values) >= limit:
        return
    if any(existing.get("value") == entry.get("value") for existing in values):
        return
    values.append(entry)


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
    parser = argparse.ArgumentParser(description="Run bounded local reverse compare-site static extraction.")
    parser.add_argument("--corpus-index", default="project_state/local_reverse_corpus_index.json")
    parser.add_argument("--benchmark", default="project_state/local_reverse_solve_benchmark.json")
    parser.add_argument("--string-result", default="project_state/local_reverse_string_solver_result.json")
    parser.add_argument("--policy", default="project_state/local_reverse_runtime_policy.json")
    parser.add_argument("--out", default="project_state/local_reverse_compare_site_result.json")
    parser.add_argument("--max-new-candidates-per-sample", type=int, default=DEFAULT_MAX_NEW_CANDIDATES_PER_SAMPLE)
    parser.add_argument("--max-runtime-validations-per-sample", type=int, default=DEFAULT_MAX_RUNTIME_VALIDATIONS_PER_SAMPLE)
    parser.add_argument("--preview-limit", type=int, default=PREVIEW_LIMIT)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
