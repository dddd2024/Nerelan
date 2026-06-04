from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SAMPLES_ROOT = Path("E:/reverse")
DEFAULT_OUT = Path("project_state/local_reverse_inventory.json")
DEFAULT_GITHUB_OUT = Path("training_materials/local_reverse/inventory.json")
DEFAULT_CASES_DIR = Path("training_materials/local_reverse/cases")

# Categories guessed from filename / extension heuristics
CATEGORY_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)sha[_-]?256|sha256", "crypto/hash"),
    (r"(?i)md5|sha1|sha[_-]?1", "crypto/hash"),
    (r"(?i)rc4|aes|des|rsa", "crypto/cipher"),
    (r"(?i)base64|base32|hex", "encoding"),
    (r"(?i)cpp|c\+\+|vc\+\+", "cpp"),
    (r"(?i)delphi|vb6|\.net", "managed"),
    (r"(?i)crack|keygen|serial", "keygen"),
    (r"(?i)unpack|upx|vmprotect|themida", "packer"),
    (r"(?i)maze|game|puzzle", "game"),
]

EXTENSION_TYPE_MAP: dict[str, str] = {
    ".exe": "pe",
    ".dll": "pe",
    ".sys": "pe",
    ".bin": "raw",
    ".dat": "raw",
    ".txt": "text",
    ".json": "json",
    ".md": "markdown",
    ".py": "python",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c_header",
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    if args.command == "scan":
        result = scan_samples(
            samples_root=Path(args.samples_root),
            out_path=Path(args.out),
            github_out_path=Path(args.github_out) if args.github_out else None,
            cases_dir=Path(args.cases_dir) if args.cases_dir else None,
        )
        print(f"[inventory] scanned={result['scanned']} entries={result['entries']}")
        print(f"[inventory] local inventory: {result['local_inventory_path']}")
        if result.get("github_inventory_path"):
            print(f"[inventory] github inventory: {result['github_inventory_path']}")
        if result.get("cases_dir"):
            print(f"[inventory] cases dir: {result['cases_dir']}")
        return 0

    parser.print_help()
    return 1


def scan_samples(
    samples_root: Path,
    out_path: Path,
    github_out_path: Path | None = None,
    cases_dir: Path | None = None,
) -> dict[str, Any]:
    if not samples_root.exists():
        raise InventoryError(f"samples root does not exist: {samples_root}")

    entries: list[dict[str, Any]] = []
    github_entries: list[dict[str, Any]] = []
    case_files: list[Path] = []

    for path in sorted(_walk_files(samples_root)):
        rel = path.relative_to(samples_root)
        entry = _build_entry(path, rel, samples_root)
        entries.append(entry)

        github_entry = _build_github_entry(entry)
        github_entries.append(github_entry)

        if cases_dir:
            case_path = cases_dir / f"{entry['sample_id']}.json"
            case_payload = _build_case_payload(entry)
            case_path.parent.mkdir(parents=True, exist_ok=True)
            _write_json(case_path, case_payload)
            case_files.append(case_path)

    inventory = {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "samples_root": str(samples_root.resolve()),
        "entries": entries,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(out_path, inventory)

    if github_out_path:
        github_inventory = {
            "schema_version": 1,
            "generated_at": _now_iso(),
            "samples_root_hint": "LOCAL_REVERSE_ROOT",
            "entries": github_entries,
        }
        github_out_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(github_out_path, github_inventory)

    return {
        "scanned": len(entries),
        "entries": entries,
        "local_inventory_path": str(out_path),
        "github_inventory_path": str(github_out_path) if github_out_path else None,
        "cases_dir": str(cases_dir) if cases_dir else None,
    }


def _build_entry(path: Path, rel: Path, samples_root: Path) -> dict[str, Any]:
    stat = path.stat()
    digest = _sha256_file(path)
    ext = path.suffix.lower()
    guessed = _guess_file_type(path.name, ext)
    category = _guess_category(path.name)
    sample_id = _make_sample_id(rel, digest)
    return {
        "sample_id": sample_id,
        "display_name": path.name,
        "relative_path": str(rel.as_posix()),
        "sha256": digest,
        "size_bytes": stat.st_size,
        "extension": ext,
        "guessed_file_type": guessed,
        "category": category,
        "tags": _build_tags(category, guessed),
        "status": "indexed",
        "github_upload_policy": "metadata_only",
    }


def _build_github_entry(entry: dict[str, Any]) -> dict[str, Any]:
    # Strip any local absolute path leakage
    return {
        "sample_id": entry["sample_id"],
        "display_name": entry["display_name"],
        "relative_path": entry["relative_path"],
        "sha256": entry["sha256"],
        "size_bytes": entry["size_bytes"],
        "extension": entry["extension"],
        "guessed_file_type": entry["guessed_file_type"],
        "category": entry["category"],
        "tags": entry["tags"][:],
        "status": entry["status"],
        "github_upload_policy": entry["github_upload_policy"],
    }


def _build_case_payload(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "cases": [
            {
                "case_id": entry["sample_id"],
                "input_value": entry["relative_path"],
                "expected_flag": "",
                "category": entry["category"],
                "tags": entry["tags"][:],
                "notes": "Auto-generated from local reverse inventory.",
            }
        ]
    }


def _make_sample_id(rel: Path, digest: str) -> str:
    safe_name = re.sub(r"[^a-z0-9_-]+", "_", rel.stem.lower()).strip("_-") or "sample"
    return f"{safe_name}_{digest[:8]}"


def _guess_file_type(name: str, ext: str) -> str:
    return EXTENSION_TYPE_MAP.get(ext.lower(), "unknown")


def _guess_category(name: str) -> str:
    for pattern, cat in CATEGORY_PATTERNS:
        if re.search(pattern, name):
            return cat
    return "unknown"


def _build_tags(category: str, guessed: str) -> list[str]:
    tags = ["local", "reverse"]
    if category != "unknown":
        tags.append(category.replace("/", "_"))
    if guessed != "unknown":
        tags.append(guessed)
    return tags


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if root.is_file():
        return [root]
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append(path)
    return files


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class InventoryError(ValueError):
    pass


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local reverse sample metadata inventory scanner.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan samples root and generate inventory.")
    scan_parser.add_argument("--samples-root", default=str(DEFAULT_SAMPLES_ROOT), help="Root directory of local samples.")
    scan_parser.add_argument("--out", default=str(DEFAULT_OUT), help="Local inventory JSON output path.")
    scan_parser.add_argument("--github-out", default=str(DEFAULT_GITHUB_OUT), help="GitHub-safe inventory JSON output path.")
    scan_parser.add_argument("--cases-dir", default=str(DEFAULT_CASES_DIR), help="Directory to write harness-compatible case JSON files.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
