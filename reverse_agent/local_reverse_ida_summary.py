from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from reverse_agent.local_reverse_compare_site import TARGET_SAMPLE_IDS
from reverse_agent.tool_runners import ToolRunArtifact, run_ida_evidence

STAGE = "local_reverse_ida_evidence_integration"
PREVIOUS_MISSING_EVIDENCE = "needs_symbolic_execution"
DEFAULT_ARTIFACTS_DIR = "solve_reports/tool_artifacts/local_reverse_ida_evidence_integration_v1"
NEXT_ACTION = "ida_summary_guided_solver_v1"

IdaRunner = Callable[..., ToolRunArtifact]


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    result = run_local_reverse_ida_summary(
        corpus_index=_read_json(Path(args.corpus_index)),
        semantic_result=_read_json(Path(args.semantic_result)),
        policy=_read_json(Path(args.policy)),
        artifacts_dir=Path(args.artifacts_dir),
        ida_executable=args.ida_path,
        ida_script_path=args.ida_script_path,
        timeout_seconds=args.timeout_seconds,
    )
    _write_json(Path(args.out), result)
    print(
        "local reverse IDA evidence integration: "
        f"status={result['status']} "
        f"targets={result['target_count']} "
        f"ida_available={result['ida_available']}"
    )
    return 0


def run_local_reverse_ida_summary(
    *,
    corpus_index: dict[str, Any],
    semantic_result: dict[str, Any],
    policy: dict[str, Any],
    artifacts_dir: Path | str = DEFAULT_ARTIFACTS_DIR,
    ida_executable: str = "",
    ida_script_path: str = "",
    timeout_seconds: int | None = None,
    ida_runner: IdaRunner = run_ida_evidence,
) -> dict[str, Any]:
    root = Path(str(policy.get("root") or corpus_index.get("root") or "")).resolve()
    corpus_by_id = {str(item.get("sample_id", "")): item for item in corpus_index.get("samples", [])}
    selected_targets = select_ida_targets(semantic_result)
    bounded_timeout = _policy_timeout(policy, timeout_seconds)
    artifacts_root = Path(artifacts_dir)

    targets: list[dict[str, Any]] = []
    ida_available = True

    for previous_target in selected_targets:
        sample_id = str(previous_target.get("sample_id", ""))
        corpus_sample = corpus_by_id.get(sample_id, {})
        target = _target_skeleton(previous_target, corpus_sample)
        sample_path, preflight_reasons = _resolve_target_path(root, corpus_sample, previous_target)
        if preflight_reasons:
            target["ida_status"] = "blocked"
            target["blocked_reasons"] = preflight_reasons
            targets.append(target)
            continue

        target_artifacts_dir = artifacts_root / sample_id
        artifact = ida_runner(
            file_path=sample_path,
            artifacts_dir=target_artifacts_dir,
            log=lambda _: None,
            ida_executable=ida_executable,
            ida_script_path=ida_script_path,
            timeout_seconds=bounded_timeout,
        )
        target["ida_output_path"] = artifact.output_path

        if not artifact.attempted and "IDA" in artifact.error:
            ida_available = False
            target["ida_status"] = "blocked"
            target["blocked_reasons"] = ["BLOCKED_BY_IDA_UNAVAILABLE"]
            target["error"] = artifact.error
        elif not artifact.success:
            target["ida_status"] = "failed" if artifact.attempted else "blocked"
            target["blocked_reasons"] = ["IDA_RUN_FAILED" if artifact.attempted else "IDA_RUN_BLOCKED"]
            target["error"] = artifact.error
        else:
            target.update(_summarize_ida_output(Path(artifact.output_path)))
            target["ida_status"] = "success"
            target["blocked_reasons"] = []
            target["next_action"] = NEXT_ACTION
        targets.append(target)

    target_count = len(targets)
    success_count = sum(1 for target in targets if target.get("ida_status") == "success")
    status = _overall_status(targets)
    return {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "stage": STAGE,
        "status": status,
        "target_count": target_count,
        "ida_available": ida_available and target_count > 0,
        "hexrays_available_any": any(bool(target.get("hexrays_available")) for target in targets),
        "success_count": success_count,
        "targets": targets,
    }


def select_ida_targets(semantic_result: dict[str, Any]) -> list[dict[str, Any]]:
    selected = []
    for target in semantic_result.get("targets", []):
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


def _target_skeleton(previous_target: dict[str, Any], corpus_sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_id": str(previous_target.get("sample_id", "")),
        "relative_path": str(corpus_sample.get("relative_path") or previous_target.get("relative_path", "")),
        "previous_missing_evidence": previous_target.get("missing_evidence"),
        "ida_status": "blocked",
        "blocked_reasons": [],
        "ida_output_path": "",
        "hexrays_available": False,
        "strings_summary": [],
        "compare_contexts_summary": [],
        "local_check_contexts_summary": [],
        "string_xrefs_summary": [],
        "validation_function_candidates": [],
        "decompiler_snippets": [],
        "solver_hints": [],
        "next_action": "",
    }


def _resolve_target_path(
    root: Path,
    corpus_sample: dict[str, Any],
    previous_target: dict[str, Any],
) -> tuple[Path, list[str]]:
    reasons: list[str] = []
    relative_path = str(corpus_sample.get("relative_path") or previous_target.get("relative_path", ""))
    sample_path = (root / relative_path).resolve()
    if not root.exists():
        reasons.append("ROOT_UNAVAILABLE")
    if not _is_under_root(sample_path, root):
        reasons.append("PATH_OUTSIDE_ROOT")
    if not sample_path.exists() or not sample_path.is_file():
        reasons.append("SAMPLE_FILE_MISSING")
    expected_sha = str(corpus_sample.get("sha256") or previous_target.get("sha256", "")).lower()
    if sample_path.exists() and sample_path.is_file() and expected_sha:
        actual_sha = _sha256_file(sample_path)
        if actual_sha.lower() != expected_sha:
            reasons.append("SHA256_MISMATCH")
    return sample_path, reasons


def _summarize_ida_output(output_path: Path) -> dict[str, Any]:
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "ida_status": "failed",
            "blocked_reasons": ["IDA_OUTPUT_PARSE_FAILED"],
            "error": str(exc),
        }
    if not isinstance(data, dict):
        return {
            "ida_status": "failed",
            "blocked_reasons": ["IDA_OUTPUT_PARSE_FAILED"],
            "error": "IDA output top-level JSON is not an object.",
        }
    return {
        "hexrays_available": bool(data.get("hexrays_available")),
        "strings_summary": _bounded_values(data.get("strings", []), limit=20),
        "compare_contexts_summary": _bounded_contexts(data.get("compare_contexts", []), limit=12),
        "local_check_contexts_summary": _bounded_contexts(data.get("local_check_contexts", []), limit=12),
        "string_xrefs_summary": _bounded_contexts(data.get("string_xrefs", []), limit=12),
        "validation_function_candidates": _bounded_contexts(
            data.get("validation_function_candidates", []),
            limit=10,
        ),
        "decompiler_snippets": _bounded_snippets(data.get("decompiler_snippets", []), limit=4),
        "solver_hints": _bounded_contexts(data.get("solver_hints", []), limit=8),
    }


def _bounded_values(values: object, *, limit: int) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value)[:240] for value in values[:limit]]


def _bounded_contexts(values: object, *, limit: int) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    bounded = []
    for value in values[:limit]:
        if isinstance(value, dict):
            bounded.append({str(key): _small_value(item) for key, item in value.items()})
        else:
            bounded.append({"value": _small_value(value)})
    return bounded


def _bounded_snippets(values: object, *, limit: int) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    snippets = []
    for value in values[:limit]:
        if isinstance(value, dict):
            snippet = {str(key): _small_value(item) for key, item in value.items() if key != "text"}
            if "text" in value:
                snippet["text"] = str(value["text"])[:900]
            snippets.append(snippet)
        else:
            snippets.append({"value": _small_value(value)})
    return snippets


def _small_value(value: object) -> Any:
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    if isinstance(value, list):
        return [_small_value(item) for item in value[:8]]
    if isinstance(value, dict):
        return {str(key): _small_value(item) for key, item in list(value.items())[:12]}
    return str(value)[:360]


def _overall_status(targets: list[dict[str, Any]]) -> str:
    if not targets:
        return "BLOCKED"
    success_count = sum(1 for target in targets if target.get("ida_status") == "success")
    if success_count == len(targets):
        return "SUCCESS"
    if success_count:
        return "PARTIAL"
    return "BLOCKED"


def _policy_timeout(policy: dict[str, Any], requested_timeout: int | None) -> int:
    default_timeout = int(policy.get("default_timeout_seconds") or 5)
    max_timeout = int(policy.get("max_timeout_seconds") or 15)
    timeout = requested_timeout if requested_timeout and requested_timeout > 0 else max(default_timeout, 1)
    return max(1, min(int(timeout), max_timeout))


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
    parser = argparse.ArgumentParser(description="Run bounded local reverse IDA evidence integration.")
    parser.add_argument("--corpus-index", default="project_state/local_reverse_corpus_index.json")
    parser.add_argument("--semantic-result", default="project_state/local_reverse_semantic_rule_result.json")
    parser.add_argument("--policy", default="project_state/local_reverse_runtime_policy.json")
    parser.add_argument("--out", default="project_state/local_reverse_ida_summary.json")
    parser.add_argument("--artifacts-dir", default=DEFAULT_ARTIFACTS_DIR)
    parser.add_argument("--ida-path", default="")
    parser.add_argument("--ida-script-path", default="")
    parser.add_argument("--timeout-seconds", type=int, default=None)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
