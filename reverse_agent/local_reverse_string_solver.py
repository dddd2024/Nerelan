from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.local_reverse_runtime import PREVIEW_LIMIT, run_probe
from reverse_agent.static_feature_extractor import (
    extract_ascii_strings,
    extract_utf16le_strings,
)

SOLVER_FAMILY = "string_compare_static_solver_v1"
DEFAULT_MAX_CANDIDATES_PER_SAMPLE = 50
NEGATIVE_RESULT = "NO_CANDIDATE_VALIDATED"
MISSING_EVIDENCE = "needs_compare_constant_or_disassembly"
NEXT_ACTION = "bounded compare-site static extraction"

SUCCESS_MARKERS = (
    "accepted",
    "congratulation",
    "congratulations",
    "correct",
    "good job",
    "right",
    "success",
    "you win",
    "well done",
)
FAILURE_MARKERS = (
    "fail",
    "failed",
    "hang on",
    "incorrect",
    "invalid",
    "nope",
    "sorry",
    "try again",
    "wrong",
)
NOISE_PHRASES = (
    "any key",
    "application",
    "cannot open",
    "correct string",
    "copyright",
    "debug",
    "delete",
    "error",
    "fail",
    "failure",
    "give me",
    "input",
    "invalid",
    "library",
    "microsoft",
    "password",
    "please",
    "press",
    "program",
    "runtime",
    "sorry",
    "success",
    "try again",
    "usage",
    "warning",
    "wrong",
    "your answer",
    "your flag",
)
PE_NOISE = (
    ".bat",
    ".cmd",
    ".com",
    ".data",
    ".exe",
    ".rdata",
    ".reloc",
    ".rsrc",
    ".text",
    ".tls",
    "kernel32",
    "msvcr",
    "user32",
    "advapi",
    "api-ms-",
    "dll",
    "manifest",
    "pdb",
)
FLAG_RE = re.compile(r"(?:flag|ctf)\{[^}\r\n]{1,80}\}", re.IGNORECASE)
PRINTABLE_RE = re.compile(r"^[ -~]+$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_@{}$!?.:+\-]{4,64}$")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    corpus_index = _read_json(Path(args.corpus_index))
    benchmark = _read_json(Path(args.benchmark))
    policy = _read_json(Path(args.policy))
    result = run_string_solver(
        corpus_index=corpus_index,
        benchmark=benchmark,
        policy=policy,
        max_candidates_per_sample=args.max_candidates_per_sample,
        preview_limit=args.preview_limit,
    )
    _write_json(Path(args.out), result)

    print(
        "local reverse string solver: "
        f"status={result['status']} "
        f"targets={result['target_count']} "
        f"solved={result['solved_count']}"
    )
    return 2 if result["status"] == "BLOCKED" else 0


def run_string_solver(
    *,
    corpus_index: dict[str, Any],
    benchmark: dict[str, Any],
    policy: dict[str, Any],
    max_candidates_per_sample: int = DEFAULT_MAX_CANDIDATES_PER_SAMPLE,
    preview_limit: int = PREVIEW_LIMIT,
) -> dict[str, Any]:
    root = Path(str(policy.get("root") or corpus_index.get("root") or "")).resolve()
    timeout = _policy_timeout(policy)
    runtime_allowed = bool(policy.get("runtime_allowed"))
    targets: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []

    if not runtime_allowed:
        blocked_reasons.append("RUNTIME_NOT_ALLOWED_BY_POLICY")
    if not root.exists():
        blocked_reasons.append("ROOT_UNAVAILABLE")

    corpus_by_id = {str(item.get("sample_id", "")): item for item in corpus_index.get("samples", [])}
    benchmark_by_id = {str(item.get("sample_id", "")): item for item in benchmark.get("samples", [])}

    for recommendation in benchmark.get("recommended_next_challenges", []):
        target = solve_target(
            recommendation=recommendation,
            corpus_sample=corpus_by_id.get(str(recommendation.get("sample_id", ""))),
            benchmark_sample=benchmark_by_id.get(str(recommendation.get("sample_id", ""))),
            root=root,
            runtime_allowed=runtime_allowed,
            timeout=timeout,
            preview_limit=preview_limit,
            max_candidates_per_sample=max_candidates_per_sample,
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
        "solver_family": SOLVER_FAMILY,
        "status": status,
        "target_count": len(targets),
        "solved_count": solved_count,
        "max_candidates_per_sample": max_candidates_per_sample,
        "timeout_seconds": timeout,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "targets": targets,
    }


def solve_target(
    *,
    recommendation: dict[str, Any],
    corpus_sample: dict[str, Any] | None,
    benchmark_sample: dict[str, Any] | None,
    root: Path,
    runtime_allowed: bool,
    timeout: int,
    preview_limit: int,
    max_candidates_per_sample: int,
    global_blocked: bool = False,
) -> dict[str, Any]:
    sample_id = str(recommendation.get("sample_id", ""))
    relative_path = str(recommendation.get("relative_path", ""))
    blocked_reasons = validate_target(
        recommendation=recommendation,
        corpus_sample=corpus_sample,
        benchmark_sample=benchmark_sample,
        root=root,
        runtime_allowed=runtime_allowed,
        global_blocked=global_blocked,
    )
    base = {
        "sample_id": sample_id,
        "relative_path": relative_path,
        "sha256": str((corpus_sample or benchmark_sample or {}).get("sha256", "")),
        "solve_readiness": str(recommendation.get("solve_readiness", "")),
        "candidate_count": 0,
        "validated_candidate_count": 0,
        "solved": False,
        "solution": None,
        "candidate_sources": [],
        "validation_results_preview": [],
        "negative_result": NEGATIVE_RESULT,
        "missing_evidence": MISSING_EVIDENCE,
        "next_action": NEXT_ACTION,
        "status": "BLOCKED" if blocked_reasons else "NO_CANDIDATE_VALIDATED",
        "blocked_reasons": blocked_reasons,
    }
    if blocked_reasons or corpus_sample is None:
        return base

    path = (root / str(corpus_sample.get("relative_path") or "")).resolve()
    data = path.read_bytes()
    candidates = build_candidates(
        data=data,
        relative_path=relative_path,
        benchmark_sample=benchmark_sample or {},
        max_candidates=max_candidates_per_sample,
    )
    validation_results = []
    solved_probe: dict[str, Any] | None = None
    for candidate in candidates:
        probe = run_probe(
            path=path,
            probe_name=f"candidate_{len(validation_results) + 1}",
            stdin_text=f"{candidate['candidate']}\n",
            timeout=timeout,
            preview_limit=preview_limit,
        )
        is_success = validation_succeeded(probe)
        validation_results.append({
            "candidate": candidate["candidate"],
            "source": candidate["source"],
            "probe_name": probe["probe_name"],
            "exit_code": probe["exit_code"],
            "timeout": probe["timeout"],
            "classification": probe["classification"],
            "success": is_success,
            "stdout_preview": probe["stdout_preview"],
            "stderr_preview": probe["stderr_preview"],
            "duration_ms": probe["duration_ms"],
        })
        if is_success:
            solved_probe = validation_results[-1]
            break

    solved = solved_probe is not None
    base.update({
        "candidate_count": len(candidates),
        "validated_candidate_count": len(validation_results),
        "candidate_sources": summarize_candidate_sources(candidates),
        "validation_results_preview": validation_results[:10],
        "solved": solved,
        "solution": solved_probe["candidate"] if solved_probe else None,
        "status": "SOLVED" if solved else "NO_CANDIDATE_VALIDATED",
        "negative_result": None if solved else NEGATIVE_RESULT,
        "missing_evidence": None if solved else MISSING_EVIDENCE,
    })
    if solved_probe:
        base["probe_name"] = solved_probe["probe_name"]
        base["stdout_success_preview"] = solved_probe["stdout_preview"]
        base["validation_duration_ms"] = solved_probe["duration_ms"]
    return base


def validate_target(
    *,
    recommendation: dict[str, Any],
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
    if str(recommendation.get("solve_readiness")) != "ready_static_string_compare":
        reasons.append("RECOMMENDATION_NOT_READY_STATIC_STRING_COMPARE")
    if corpus_sample is None:
        reasons.append("MISSING_CORPUS_SAMPLE")
        return reasons
    if benchmark_sample is None:
        reasons.append("MISSING_BENCHMARK_SAMPLE")
    elif str(benchmark_sample.get("solve_readiness")) != "ready_static_string_compare":
        reasons.append("BENCHMARK_SAMPLE_NOT_READY_STATIC_STRING_COMPARE")

    path = (root / str(corpus_sample.get("relative_path") or "")).resolve()
    if not _is_under_root(path, root):
        reasons.append("PATH_OUTSIDE_ROOT")
    if not path.exists():
        reasons.append("SAMPLE_MISSING")
    elif _sha256_file(path) != str(corpus_sample.get("sha256", "")):
        reasons.append("SHA256_MISMATCH")
    return reasons


def build_candidates(
    *,
    data: bytes,
    relative_path: str,
    benchmark_sample: dict[str, Any],
    max_candidates: int,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    strings = extract_ascii_strings(data, min_length=4, max_count=2000)
    strings.extend(extract_utf16le_strings(data, min_length=4, max_count=1000))

    for value in strings:
        for match in FLAG_RE.findall(value):
            _add_candidate(candidates, match, "flag_like_static_string")
    for value in strings:
        _add_candidate(candidates, value.strip(), "static_string")
    for runtime_result in benchmark_sample.get("runtime_results", []):
        for line in _runtime_output_lines(runtime_result):
            _add_candidate(candidates, line, "runtime_output_string")
    for value in _path_hint_candidates(relative_path):
        _add_candidate(candidates, value, "path_hint")

    candidates.sort(key=lambda item: candidate_rank(item))
    return candidates[:max_candidates]


def validation_succeeded(probe: dict[str, Any]) -> bool:
    if probe.get("timeout"):
        return False
    text = f"{probe.get('stdout_preview', '')}\n{probe.get('stderr_preview', '')}".lower()
    has_success = any(marker in text for marker in SUCCESS_MARKERS)
    has_failure = any(marker in text for marker in FAILURE_MARKERS)
    return has_success and not has_failure


def summarize_candidate_sources(candidates: list[dict[str, str]]) -> list[dict[str, Any]]:
    summary: dict[str, int] = {}
    for candidate in candidates:
        source = candidate["source"]
        summary[source] = summary.get(source, 0) + 1
    return [{"source": source, "count": count} for source, count in sorted(summary.items())]


def candidate_rank(candidate: dict[str, str]) -> tuple[int, int, str]:
    source_rank = {
        "flag_like_static_string": 0,
        "static_string": 1,
        "runtime_output_string": 2,
        "path_hint": 3,
    }.get(candidate["source"], 9)
    return (source_rank, len(candidate["candidate"]), candidate["candidate"].lower())


def _add_candidate(candidates: list[dict[str, str]], value: str, source: str) -> None:
    candidate = value.strip().strip("\"'")
    if not is_candidate_input(candidate):
        return
    if any(existing["candidate"] == candidate for existing in candidates):
        return
    candidates.append({"candidate": candidate, "source": source})


def is_candidate_input(value: str) -> bool:
    if not (4 <= len(value) <= 64):
        return False
    if not PRINTABLE_RE.match(value):
        return False
    lower = value.lower()
    if any(phrase in lower for phrase in NOISE_PHRASES):
        return False
    if any(phrase in lower for phrase in PE_NOISE):
        return False
    if value.startswith("."):
        return False
    if "%" in value or "\\" in value or "/" in value:
        return False
    if FLAG_RE.fullmatch(value):
        return True
    return TOKEN_RE.fullmatch(value) is not None


def _runtime_output_lines(runtime_result: dict[str, Any]) -> list[str]:
    text = f"{runtime_result.get('stdout_preview', '')}\n{runtime_result.get('stderr_preview', '')}"
    return [line.strip() for line in text.splitlines() if line.strip()]


def _path_hint_candidates(relative_path: str) -> list[str]:
    stem = Path(relative_path).stem
    compact = re.sub(r"[^A-Za-z0-9_]+", "", stem)
    values = [stem, compact, compact.lower(), compact.upper()]
    return [value for value in dict.fromkeys(values) if value]


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
    parser = argparse.ArgumentParser(description="Run bounded local reverse string-compare solver.")
    parser.add_argument("--corpus-index", default="project_state/local_reverse_corpus_index.json")
    parser.add_argument("--benchmark", default="project_state/local_reverse_solve_benchmark.json")
    parser.add_argument("--policy", default="project_state/local_reverse_runtime_policy.json")
    parser.add_argument("--out", default="project_state/local_reverse_string_solver_result.json")
    parser.add_argument("--max-candidates-per-sample", type=int, default=DEFAULT_MAX_CANDIDATES_PER_SAMPLE)
    parser.add_argument("--preview-limit", type=int, default=PREVIEW_LIMIT)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
