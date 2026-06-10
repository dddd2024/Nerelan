from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_POLICY = {
    "schema_version": 1,
    "root": r"E:\reverse",
    "runtime_allowed": True,
    "allowance_source": "user_asserted_pretested_no_virus",
    "allowed_extensions": [".exe"],
    "path_scope": "indexed_files_under_root_only",
    "network_allowed": False,
    "copy_binary_into_repo": False,
    "default_timeout_seconds": 5,
    "max_timeout_seconds": 15,
    "stdin_probe_limit": 8,
}
PROBES = [
    ("run_no_input", None),
    ("run_with_empty_line", "\n"),
    ("run_with_test", "test\n"),
    ("run_with_123456", "123456\n"),
    ("run_with_password", "password\n"),
    ("run_with_flag_test", "flag_test\n"),
    ("run_with_AAAA", "AAAA\n"),
    ("run_with_16_A", "AAAAAAAAAAAAAAAA\n"),
]
PREVIEW_LIMIT = 4096


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    corpus_index = _read_json(Path(args.corpus_index))
    policy_path = Path(args.policy)
    policy = load_or_build_policy(policy_path, corpus_index)
    benchmark = run_benchmark(
        corpus_index=corpus_index,
        policy=policy,
        timeout_seconds=args.timeout_seconds,
        preview_limit=args.preview_limit,
    )
    _write_json(Path(args.out), benchmark)

    print(
        "local reverse runtime benchmark: "
        f"status={benchmark['status']} "
        f"challenges={benchmark['challenge_count']} "
        f"executed={benchmark['executed_count']} "
        f"skipped={benchmark['skipped_count']} "
        f"timeouts={benchmark['timeout_count']}"
    )
    return 2 if benchmark["status"] == "BLOCKED" else 0


def load_or_build_policy(policy_path: Path, corpus_index: dict[str, Any]) -> dict[str, Any]:
    if policy_path.exists():
        policy = _read_json(policy_path)
    else:
        policy = dict(DEFAULT_POLICY)
        policy["generated_at"] = _now_iso()
        policy["root"] = str(corpus_index.get("root") or DEFAULT_POLICY["root"])
        _write_json(policy_path, policy)
    return policy


def run_benchmark(
    *,
    corpus_index: dict[str, Any],
    policy: dict[str, Any],
    timeout_seconds: int | None = None,
    preview_limit: int = PREVIEW_LIMIT,
) -> dict[str, Any]:
    root = Path(str(policy.get("root") or corpus_index.get("root") or "")).resolve()
    runtime_allowed = bool(policy.get("runtime_allowed"))
    allowed_extensions = {str(item).lower() for item in policy.get("allowed_extensions", [".exe"])}
    configured_timeout = int(timeout_seconds or policy.get("default_timeout_seconds") or 5)
    max_timeout = int(policy.get("max_timeout_seconds") or 15)
    timeout = max(1, min(configured_timeout, max_timeout))
    probe_limit = int(policy.get("stdin_probe_limit") or len(PROBES))
    probes = PROBES[:max(1, min(probe_limit, len(PROBES)))]

    samples: list[dict[str, Any]] = []
    challenge_count = 0
    executed_count = 0
    skipped_count = 0
    timeout_count = 0
    solved_count = 0
    blocked_reasons: list[str] = []

    if not root.exists():
        return _blocked_benchmark(corpus_index, policy, "ROOT_UNAVAILABLE")

    for sample in corpus_index.get("samples", []):
        if not _is_challenge_binary(sample, allowed_extensions):
            continue
        challenge_count += 1
        sample_result = benchmark_sample(
            sample=sample,
            root=root,
            runtime_allowed=runtime_allowed,
            timeout=timeout,
            probes=probes,
            preview_limit=preview_limit,
        )
        samples.append(sample_result)
        if sample_result["runtime_status"] == "executed":
            executed_count += 1
        else:
            skipped_count += 1
        if any(item.get("timeout") for item in sample_result.get("runtime_results", [])):
            timeout_count += 1
        if sample_result.get("solved"):
            solved_count += 1
        if sample_result["runtime_status"] in {"blocked", "skipped"}:
            blocked_reasons.extend(sample_result.get("blocked_reasons", []))

    if challenge_count == 0:
        status = "BLOCKED"
        blocked_reasons.append("NO_CHALLENGE_BINARIES")
    elif executed_count == 0:
        status = "BLOCKED"
    elif skipped_count or blocked_reasons:
        status = "PARTIAL"
    else:
        status = "READY"

    return {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "root": str(root),
        "status": status,
        "challenge_count": challenge_count,
        "executed_count": executed_count,
        "skipped_count": skipped_count,
        "timeout_count": timeout_count,
        "solved_count": solved_count,
        "timeout_seconds": timeout,
        "probe_count": len(probes),
        "blocked_reasons": sorted(set(blocked_reasons)),
        "samples": samples,
        "recommended_next_challenges": recommend_next_challenges(samples),
    }


def benchmark_sample(
    *,
    sample: dict[str, Any],
    root: Path,
    runtime_allowed: bool,
    timeout: int,
    probes: list[tuple[str, str | None]],
    preview_limit: int,
) -> dict[str, Any]:
    relative_path = str(sample.get("relative_path") or "")
    path = (root / relative_path).resolve()
    blocked_reasons: list[str] = []

    if not runtime_allowed:
        blocked_reasons.append("RUNTIME_NOT_ALLOWED_BY_POLICY")
    if not _is_under_root(path, root):
        blocked_reasons.append("PATH_OUTSIDE_ROOT")
    if not path.exists():
        blocked_reasons.append("SAMPLE_MISSING")
    elif _sha256_file(path) != sample.get("sha256"):
        blocked_reasons.append("SHA256_MISMATCH")

    if blocked_reasons:
        return _sample_result(
            sample,
            "blocked",
            [],
            blocked_reasons,
            runtime_allowed=False,
        )

    runtime_results = []
    for probe_name, stdin_text in probes:
        result = run_probe(
            path=path,
            probe_name=probe_name,
            stdin_text=stdin_text,
            timeout=timeout,
            preview_limit=preview_limit,
        )
        runtime_results.append(result)
        if result["timeout"]:
            break

    runtime_status = "executed" if runtime_results else "skipped"
    return _sample_result(
        sample,
        runtime_status,
        runtime_results,
        blocked_reasons,
        runtime_allowed=runtime_allowed and runtime_status == "executed",
    )


def run_probe(
    *,
    path: Path,
    probe_name: str,
    stdin_text: str | None,
    timeout: int,
    preview_limit: int,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            _command_for_path(path),
            input=stdin_text,
            text=True,
            capture_output=True,
            timeout=timeout,
            cwd=str(path.parent),
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout_preview = _preview(completed.stdout or "", preview_limit)
        stderr_preview = _preview(completed.stderr or "", preview_limit)
        classification = classify_probe_result(
            exit_code=completed.returncode,
            timeout=False,
            stdout=stdout_preview,
            stderr=stderr_preview,
        )
        return {
            "probe_name": probe_name,
            "stdin": "" if stdin_text is None else stdin_text,
            "exit_code": completed.returncode,
            "timeout": False,
            "stdout_preview": stdout_preview,
            "stderr_preview": stderr_preview,
            "duration_ms": duration_ms,
            "classification": classification,
        }
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        return {
            "probe_name": probe_name,
            "stdin": "" if stdin_text is None else stdin_text,
            "exit_code": None,
            "timeout": True,
            "stdout_preview": _preview(_decode_process_output(exc.stdout), preview_limit),
            "stderr_preview": _preview(_decode_process_output(exc.stderr), preview_limit),
            "duration_ms": duration_ms,
            "classification": "timeout",
        }
    except OSError as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        return {
            "probe_name": probe_name,
            "stdin": "" if stdin_text is None else stdin_text,
            "exit_code": None,
            "timeout": False,
            "stdout_preview": "",
            "stderr_preview": _preview(str(exc), preview_limit),
            "duration_ms": duration_ms,
            "classification": "blocked_runtime_error",
        }


def classify_probe_result(*, exit_code: int | None, timeout: bool, stdout: str, stderr: str) -> str:
    if timeout:
        return "timeout"
    text = f"{stdout}\n{stderr}".lower()
    if exit_code is not None and exit_code < 0:
        return "crash"
    if any(word in text for word in ("correct", "success", "wrong", "fail", "invalid", "password", "input", "flag")):
        return "prints_success_failure"
    if "enter" in text or "please" in text:
        return "asks_for_input"
    if not stdout and not stderr and exit_code == 0:
        return "silent_exit"
    if not stdout and not stderr:
        return "gui_or_no_console"
    return "runtime_output"


def solve_readiness(sample: dict[str, Any], runtime_results: list[dict[str, Any]]) -> str:
    tags = set(sample.get("triage_tags", []))
    classifications = {item.get("classification") for item in runtime_results}
    if "blocked_runtime_error" in classifications:
        return "blocked_runtime_error"
    if "timeout" in classifications:
        return "needs_gui_interaction"
    if "strcmp" in tags or "serial_check" in tags:
        return "ready_static_string_compare"
    if "xor" in tags or "array_compare" in tags:
        return "ready_xor_array_static"
    if "shift" in tags:
        return "ready_shift_static"
    if tags & {"des", "rc4", "aes", "base64", "hash"}:
        return "ready_crypto_known_family"
    if "packed_or_obfuscated" in tags:
        return "needs_disassembly"
    return "unknown"


def next_action_for_readiness(readiness: str) -> str:
    actions = {
        "ready_static_string_compare": "extract compare strings/constants and validate a candidate input",
        "ready_xor_array_static": "extract byte arrays and build a small static xor/array solver",
        "ready_shift_static": "extract target string and brute-force shift/affine variants",
        "ready_crypto_known_family": "extract key/ciphertext constants for the identified crypto family",
        "needs_disassembly": "inspect imports, strings, and compare sites before solver implementation",
        "needs_gui_interaction": "classify GUI behavior manually; avoid complex automation in this round",
        "blocked_runtime_error": "inspect runtime error before retrying benchmark",
        "unknown": "perform manual static triage",
    }
    return actions.get(readiness, actions["unknown"])


def recommend_next_challenges(samples: list[dict[str, Any]], limit: int = 3) -> list[dict[str, str]]:
    ranked = sorted(samples, key=_challenge_key)
    recommendations = []
    for sample in ranked:
        if sample.get("runtime_status") != "executed":
            continue
        recommendations.append({
            "sample_id": str(sample.get("sample_id", "")),
            "relative_path": str(sample.get("relative_path", "")),
            "solve_readiness": str(sample.get("solve_readiness", "unknown")),
            "next_action": str(sample.get("next_action", "")),
        })
        if len(recommendations) >= limit:
            break
    return recommendations


def _sample_result(
    sample: dict[str, Any],
    runtime_status: str,
    runtime_results: list[dict[str, Any]],
    blocked_reasons: list[str],
    *,
    runtime_allowed: bool,
) -> dict[str, Any]:
    readiness = solve_readiness(sample, runtime_results)
    return {
        "sample_id": sample.get("sample_id", ""),
        "relative_path": sample.get("relative_path", ""),
        "sha256": sample.get("sha256", ""),
        "artifact_role": sample.get("artifact_role", "unknown"),
        "triage_tags": sample.get("triage_tags", []),
        "runtime_allowed": runtime_allowed,
        "runtime_status": runtime_status,
        "blocked_reasons": blocked_reasons,
        "runtime_results": runtime_results,
        "solve_readiness": readiness,
        "next_action": next_action_for_readiness(readiness),
        "solved": False,
    }


def _blocked_benchmark(corpus_index: dict[str, Any], policy: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "root": str(policy.get("root") or corpus_index.get("root") or ""),
        "status": "BLOCKED",
        "challenge_count": 0,
        "executed_count": 0,
        "skipped_count": 0,
        "timeout_count": 0,
        "solved_count": 0,
        "blocked_reasons": [reason],
        "samples": [],
        "recommended_next_challenges": [],
    }


def _is_challenge_binary(sample: dict[str, Any], allowed_extensions: set[str]) -> bool:
    return (
        sample.get("artifact_role") == "challenge_binary"
        and str(sample.get("extension") or "").lower() in allowed_extensions
    )


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


def _preview(text: str, limit: int) -> str:
    return text[:limit]


def _decode_process_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _command_for_path(path: Path) -> list[str]:
    if path.suffix.lower() == ".py":
        return [sys.executable, str(path)]
    return [str(path)]


def _challenge_key(sample: dict[str, Any]) -> tuple[int, int, str]:
    readiness = sample.get("solve_readiness", "unknown")
    readiness_rank = {
        "ready_static_string_compare": 0,
        "ready_xor_array_static": 1,
        "ready_shift_static": 2,
        "ready_crypto_known_family": 3,
        "needs_disassembly": 4,
        "needs_gui_interaction": 5,
        "blocked_runtime_error": 6,
        "unknown": 7,
    }.get(str(readiness), 7)
    timeout_rank = 1 if any(item.get("timeout") for item in sample.get("runtime_results", [])) else 0
    return (readiness_rank, timeout_rank, str(sample.get("relative_path") or ""))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded local reverse runtime benchmark.")
    parser.add_argument("--corpus-index", default="project_state/local_reverse_corpus_index.json")
    parser.add_argument("--policy", default="project_state/local_reverse_runtime_policy.json")
    parser.add_argument("--out", default="project_state/local_reverse_solve_benchmark.json")
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--preview-limit", type=int, default=PREVIEW_LIMIT)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
