from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.static_feature_extractor import (
    extract_ascii_strings,
    extract_utf16le_strings,
)

DEFAULT_ROOT = Path(r"E:\reverse")
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024
DEFAULT_MAX_PROBE_BYTES = 1024 * 1024
DEFAULT_MAX_SAMPLES = 5000
TRIAGE_TAGS = [
    "xor",
    "shift",
    "array_compare",
    "strcmp",
    "serial_check",
    "base64",
    "rc4",
    "des",
    "aes",
    "hash",
    "packed_or_obfuscated",
    "unknown",
]
SKIP_DIRS = {
    ".git",
    ".hg",
    ".idea",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
}
SKIP_EXTENSIONS = {
    ".i64",
    ".id0",
    ".id1",
    ".id2",
    ".nam",
    ".til",
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    root = Path(args.root)
    result = scan_corpus(
        root=root,
        max_file_size=args.max_file_size,
        max_probe_bytes=args.max_probe_bytes,
        max_samples=args.max_samples,
    )
    training_state = build_training_state(result)

    _write_json(Path(args.out), result)
    _write_json(Path(args.training_state), training_state)

    print(
        "local reverse corpus: "
        f"status={training_state['status']} "
        f"samples={result['sample_count']} "
        f"root={result['root']}"
    )
    if training_state["blocked_reason"]:
        print(f"blocked_reason={training_state['blocked_reason']}")
    return 2 if training_state["status"] == "BLOCKED" else 0


def scan_corpus(
    root: Path = DEFAULT_ROOT,
    *,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    max_probe_bytes: int = DEFAULT_MAX_PROBE_BYTES,
    max_samples: int = DEFAULT_MAX_SAMPLES,
) -> dict[str, Any]:
    root = root.expanduser()
    root_exists = root.exists() and root.is_dir()
    generated_at = _now_iso()
    samples: list[dict[str, Any]] = []
    scan_errors: list[str] = []
    limit_reached = False

    if root_exists:
        for path in _iter_files(root):
            if len(samples) >= max_samples:
                limit_reached = True
                break
            try:
                samples.append(
                    build_sample_record(
                        path,
                        root=root,
                        max_file_size=max_file_size,
                        max_probe_bytes=max_probe_bytes,
                    )
                )
            except OSError as exc:
                scan_errors.append(f"{_relative_path(path, root)}: {exc}")

    notes = []
    if not root_exists:
        notes.append("root_missing_or_not_directory")
    if limit_reached:
        notes.append("sample_limit_reached")
    if scan_errors:
        notes.append("some_files_unreadable")

    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "root": str(root),
        "root_exists": root_exists,
        "sample_count": len(samples),
        "max_file_size": max_file_size,
        "max_probe_bytes": max_probe_bytes,
        "max_samples": max_samples,
        "sample_limit_reached": limit_reached,
        "scan_errors": scan_errors[:50],
        "notes": notes,
        "samples": samples,
    }


def build_sample_record(
    path: Path,
    *,
    root: Path,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    max_probe_bytes: int = DEFAULT_MAX_PROBE_BYTES,
) -> dict[str, Any]:
    stat = path.stat()
    relative_path = _relative_path(path, root)
    digest = _sha256_file(path)
    probe = _read_probe(path, max_probe_bytes=max_probe_bytes)
    file_kind = detect_file_kind(path, probe)
    triage_tags, confidence, notes = triage_sample(
        path=path,
        data=probe,
        file_kind=file_kind,
        size_bytes=stat.st_size,
        max_file_size=max_file_size,
    )
    if stat.st_size > max_file_size:
        notes.append("triage_probe_only_large_file")

    return {
        "sample_id": digest[:16],
        "relative_path": relative_path,
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "sha256": digest,
        "mtime": _mtime_iso(stat.st_mtime),
        "file_kind": file_kind,
        "triage_tags": triage_tags,
        "triage_confidence": confidence,
        "safe_to_run": False,
        "notes": notes,
    }


def detect_file_kind(path: Path, data: bytes) -> str:
    suffix = path.suffix.lower()
    if data.startswith(b"MZ"):
        return _pe_kind(data)
    if suffix == ".py":
        return "python"
    if suffix in {".ps1", ".bat", ".cmd", ".sh", ".js"}:
        return "script"
    if suffix in {".c", ".cc", ".cpp", ".h", ".hpp", ".txt", ".md", ".json", ".xml"}:
        return "source_or_notes"
    if suffix in {".exe", ".dll"}:
        return "possible_pe"
    if _looks_text(data):
        return "text"
    return "unknown"


def triage_sample(
    *,
    path: Path,
    data: bytes,
    file_kind: str,
    size_bytes: int,
    max_file_size: int,
) -> tuple[list[str], str, list[str]]:
    notes: list[str] = []
    evidence = " ".join([path.name, *_bounded_strings(data)]).lower()
    tags: set[str] = set()

    keyword_map = {
        "xor": ("xor", "^ 0x", "^0x"),
        "shift": ("shift", "caesar", "rot13", "rot "),
        "strcmp": ("strcmp", "strncmp", "memcmp", "compare", "password", "input", "correct", "wrong", "success", "flag"),
        "serial_check": ("serial", "license", "keygen", "registration"),
        "base64": ("base64", "base32", "base16", "atob", "btoa"),
        "rc4": ("rc4", "ksa", "prga"),
        "des": ("des", "desenc", "3des"),
        "aes": ("aes", "rijndael"),
        "hash": ("md5", "sha1", "sha256", "sha512", "hash", "digest"),
    }
    for tag, needles in keyword_map.items():
        if any(needle in evidence for needle in needles):
            tags.add(tag)

    if re.search(r"(0x[0-9a-f]{2}\s*,\s*){3,}0x[0-9a-f]{2}", evidence):
        tags.add("array_compare")
    if re.search(r"\[[0-9,\s]{8,}\]", evidence) and ("cmp" in evidence or "check" in evidence):
        tags.add("array_compare")
    if _has_base64_alphabet(data):
        tags.add("base64")
    if file_kind in {"pe32", "pe64", "pe_candidate", "possible_pe"}:
        notes.append("static_pe_or_executable_candidate")
    if size_bytes > max_file_size:
        notes.append("over_max_file_size_no_full_static_triage")
    if _high_entropy_probe(data):
        tags.add("packed_or_obfuscated")
        notes.append("high_entropy_probe")

    if not tags:
        tags.add("unknown")

    ordered = [tag for tag in TRIAGE_TAGS if tag in tags]
    non_unknown_count = len([tag for tag in ordered if tag != "unknown"])
    confidence = "high" if non_unknown_count >= 3 else "medium" if non_unknown_count >= 2 else "low"
    return ordered, confidence, notes


def build_training_state(corpus_index: dict[str, Any]) -> dict[str, Any]:
    samples = corpus_index.get("samples", [])
    root_exists = bool(corpus_index.get("root_exists"))
    scan_errors = corpus_index.get("scan_errors", [])
    sample_count = int(corpus_index.get("sample_count") or 0)

    if not root_exists:
        status = "BLOCKED"
        blocked_reason = "BLOCKED_BY_LOCAL_PATH_UNAVAILABLE"
    elif sample_count == 0:
        status = "PARTIAL"
        blocked_reason = "NO_READABLE_SAMPLES_FOUND"
    elif corpus_index.get("sample_limit_reached") or scan_errors:
        status = "PARTIAL"
        blocked_reason = ""
    else:
        status = "READY"
        blocked_reason = ""

    tag_counts = Counter()
    for sample in samples:
        for tag in sample.get("triage_tags", []):
            tag_counts[tag] += 1

    return {
        "schema_version": 1,
        "generated_at": corpus_index.get("generated_at") or _now_iso(),
        "training_profile": "local_reverse_simple_training",
        "root": corpus_index.get("root", ""),
        "status": status,
        "sample_count": sample_count,
        "triage_summary": {tag: tag_counts.get(tag, 0) for tag in TRIAGE_TAGS},
        "recommended_next_samples": recommend_next_samples(samples),
        "blocked_reason": blocked_reason,
        "notes": corpus_index.get("notes", []),
    }


def recommend_next_samples(samples: list[dict[str, Any]], limit: int = 5) -> list[dict[str, str]]:
    ranked = sorted(samples, key=_recommendation_key)
    recommendations: list[dict[str, str]] = []
    for sample in ranked:
        tags = [tag for tag in sample.get("triage_tags", []) if tag != "unknown"]
        if not tags:
            continue
        recommendations.append({
            "sample_id": str(sample.get("sample_id", "")),
            "relative_path": str(sample.get("relative_path", "")),
            "reason": _recommendation_reason(sample, tags),
            "proposed_solver_family": _solver_family(tags),
        })
        if len(recommendations) >= limit:
            break
    return recommendations


def _recommendation_key(sample: dict[str, Any]) -> tuple[int, int, str]:
    tags = [tag for tag in sample.get("triage_tags", []) if tag != "unknown"]
    simple_rank = 0 if any(tag in tags for tag in ("xor", "shift", "strcmp", "array_compare", "base64")) else 1
    return (simple_rank, int(sample.get("size_bytes") or 0), str(sample.get("relative_path") or ""))


def _recommendation_reason(sample: dict[str, Any], tags: list[str]) -> str:
    kind = sample.get("file_kind", "unknown")
    size = sample.get("size_bytes", 0)
    return f"{kind} sample, {size} bytes, static triage tags: {', '.join(tags[:4])}"


def _solver_family(tags: list[str]) -> str:
    if "xor" in tags or "array_compare" in tags:
        return "xor_array_static_solver"
    if "shift" in tags:
        return "shift_or_affine_static_solver"
    if "strcmp" in tags or "serial_check" in tags:
        return "string_compare_static_solver"
    if "base64" in tags:
        return "encoding_static_solver"
    if "rc4" in tags or "des" in tags or "aes" in tags:
        return "crypto_static_triage_plan"
    if "hash" in tags:
        return "hash_constant_static_solver"
    return "manual_static_triage"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a static local reverse corpus index.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Local corpus root to scan.")
    parser.add_argument(
        "--out",
        default="project_state/local_reverse_corpus_index.json",
        help="Path for corpus index JSON.",
    )
    parser.add_argument(
        "--training-state",
        default="project_state/local_reverse_training_state.json",
        help="Path for training state JSON.",
    )
    parser.add_argument("--max-file-size", type=int, default=DEFAULT_MAX_FILE_SIZE)
    parser.add_argument("--max-probe-bytes", type=int, default=DEFAULT_MAX_PROBE_BYTES)
    parser.add_argument("--max-samples", type=int, default=DEFAULT_MAX_SAMPLES)
    return parser


def _iter_files(root: Path):
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_EXTENSIONS:
            continue
        if path.is_file():
            yield path


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _read_probe(path: Path, *, max_probe_bytes: int) -> bytes:
    with path.open("rb") as handle:
        return handle.read(max_probe_bytes)


def _bounded_strings(data: bytes) -> list[str]:
    return [
        *extract_ascii_strings(data, min_length=4, max_count=100),
        *extract_utf16le_strings(data, min_length=4, max_count=50),
    ]


def _pe_kind(data: bytes) -> str:
    if len(data) < 64:
        return "pe_candidate"
    pe_offset = int.from_bytes(data[60:64], "little", signed=False)
    if pe_offset + 6 > len(data) or data[pe_offset:pe_offset + 4] != b"PE\x00\x00":
        return "pe_candidate"
    machine = int.from_bytes(data[pe_offset + 4:pe_offset + 6], "little", signed=False)
    if machine == 0x14C:
        return "pe32"
    if machine == 0x8664:
        return "pe64"
    return "pe_candidate"


def _looks_text(data: bytes) -> bool:
    if not data:
        return False
    sample = data[:4096]
    printable = sum(1 for byte in sample if byte in b"\r\n\t" or 32 <= byte <= 126)
    return printable / len(sample) > 0.85


def _has_base64_alphabet(data: bytes) -> bool:
    return b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/" in data


def _high_entropy_probe(data: bytes) -> bool:
    if len(data) < 4096:
        return False
    sample = data[:65536]
    unique = len(set(sample))
    return unique > 220


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _mtime_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
