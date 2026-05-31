from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SAMPLES_DIR = Path("local_reverse_samples")
DEFAULT_TAGS = ["local", "reverse", "auto_imported"]


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    try:
        if args.command == "add":
            result = add_sample(
                source_path=Path(args.path),
                samples_dir=Path(args.samples_dir),
                case_id=args.case_id,
            )
            print(f"created: {result['case_dir']}")
            print(f"case_id: {result['case_id']}")
            print(f"case_json: {result['case_json']}")
            return 0
        if args.command == "solve":
            result = solve_sample(
                case_id=args.case_id,
                samples_dir=Path(args.samples_dir),
                run_static_harness=args.run_static_harness,
            )
            print(f"codex_task: {result['codex_task']}")
            return 0
    except LocalSamplesError as exc:
        raise SystemExit(str(exc)) from exc

    parser.print_help()
    return 1


class LocalSamplesError(ValueError):
    pass


def add_sample(source_path: Path, samples_dir: Path = DEFAULT_SAMPLES_DIR, case_id: str | None = None) -> dict[str, str]:
    source = source_path.expanduser()
    if not source.exists():
        raise LocalSamplesError(f"sample path does not exist: {source_path}")
    if not source.is_file():
        raise LocalSamplesError(f"sample path is not a file: {source_path}")

    digest = _sha256_file(source)
    resolved_case_id = sanitize_case_id(case_id) if case_id else _generated_case_id(source.stem, digest)
    case_dir = samples_dir / resolved_case_id
    if case_dir.exists():
        raise LocalSamplesError(f"case_id already exists: {resolved_case_id}")

    sample_name = f"sample{source.suffix.lower()}"
    stored_sample = case_dir / sample_name
    case_dir.mkdir(parents=True)
    shutil.copy2(source, stored_sample)

    tags = list(DEFAULT_TAGS)
    case_payload = {
        "cases": [
            {
                "case_id": resolved_case_id,
                "input_value": _path_for_payload(stored_sample),
                "expected_flag": "",
                "category": "unknown",
                "tags": tags,
                "notes": "Auto-generated from local sample intake.",
            }
        ]
    }
    metadata_payload = {
        "case_id": resolved_case_id,
        "original_path": str(source.resolve()),
        "stored_sample_path": _path_for_payload(stored_sample),
        "sha256": digest,
        "size_bytes": stored_sample.stat().st_size,
        "created_at": _now_iso(),
        "category": "unknown",
        "tags": tags,
    }

    _write_json(case_dir / "case.json", case_payload)
    _write_json(case_dir / "metadata.json", metadata_payload)
    (case_dir / "notes.md").write_text(_notes_template(resolved_case_id), encoding="utf-8")

    return {
        "case_id": resolved_case_id,
        "case_dir": str(case_dir),
        "case_json": str(case_dir / "case.json"),
        "metadata_json": str(case_dir / "metadata.json"),
        "notes": str(case_dir / "notes.md"),
        "stored_sample": str(stored_sample),
    }


def solve_sample(
    case_id: str,
    samples_dir: Path = DEFAULT_SAMPLES_DIR,
    run_static_harness: bool = False,
) -> dict[str, str]:
    resolved_case_id = sanitize_case_id(case_id)
    case_dir = samples_dir / resolved_case_id
    metadata_path = case_dir / "metadata.json"
    case_json_path = case_dir / "case.json"
    if not case_dir.exists():
        raise LocalSamplesError(f"case_id not found: {resolved_case_id}")
    if not metadata_path.exists() or not case_json_path.exists():
        raise LocalSamplesError(f"case is missing metadata.json or case.json: {resolved_case_id}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    case_payload = json.loads(case_json_path.read_text(encoding="utf-8"))
    codex_task_path = case_dir / "codex_task.md"
    codex_task_path.write_text(
        _codex_task_template(
            case_id=resolved_case_id,
            samples_dir=samples_dir,
            case_json_path=case_json_path,
            metadata=metadata,
            case_payload=case_payload,
        ),
        encoding="utf-8",
    )

    if run_static_harness:
        run_static_harness_for_case(case_json_path, resolved_case_id)

    return {
        "case_id": resolved_case_id,
        "case_dir": str(case_dir),
        "case_json": str(case_json_path),
        "codex_task": str(codex_task_path),
    }


def run_static_harness_for_case(case_json_path: Path, case_id: str) -> int:
    from . import harness

    return harness.main(
        [
            "--dataset",
            str(case_json_path),
            "--run-name",
            f"local_{case_id}_static",
            "--analysis-mode",
            "Static Analysis",
            "--case-id",
            case_id,
        ]
    )


def sanitize_case_id(value: str | None) -> str:
    raw = (value or "").strip().lower()
    safe = re.sub(r"[^a-z0-9._-]+", "_", raw)
    safe = re.sub(r"_+", "_", safe).strip("._-")
    if not safe:
        raise LocalSamplesError("case_id is empty after sanitization")
    return safe


def _generated_case_id(stem: str, digest: str) -> str:
    return f"{sanitize_case_id(stem)}_{digest[:8]}"


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _path_for_payload(path: Path) -> str:
    return path.as_posix()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _notes_template(case_id: str) -> str:
    return f"""# {case_id}

## Notes

- Imported with `python -m reverse_agent.local_samples add`.
- Keep challenge-specific observations here.
- Do not commit files under `local_reverse_samples/`.
"""


def _codex_task_template(
    case_id: str,
    samples_dir: Path,
    case_json_path: Path,
    metadata: dict[str, Any],
    case_payload: dict[str, Any],
) -> str:
    stored_sample_path = str(metadata.get("stored_sample_path") or "")
    sha256 = str(metadata.get("sha256") or "")
    size_bytes = metadata.get("size_bytes")
    solver_path = samples_dir / case_id / "solver.py"
    harness_command = (
        f"python -m reverse_agent.harness --dataset {case_json_path} "
        f"--run-name local_{case_id}_static --analysis-mode \"Static Analysis\" --case-id {case_id}"
    )
    return f"""# Local Reverse Sample Task: {case_id}

## Sample

- case_id: `{case_id}`
- sample path: `{stored_sample_path}`
- sha256: `{sha256}`
- size_bytes: `{size_bytes}`
- case.json: `{case_json_path.as_posix()}`
- expected solver output: `{solver_path.as_posix()}`

## Harness

```powershell
{harness_command}
```

## First Pass

1. Inspect printable strings, imports, constants, compare points, hash clues, and encoding indicators.
2. Keep the first pass static and auditable.
3. Write any one-off solution code to `{solver_path.as_posix()}`.
4. Do not run IDA, OllyDbg, Frida, or other runtime probes unless the user explicitly authorizes it.
5. Do not commit `local_reverse_samples/` contents or the local `solver.py`.
6. If a reusable pattern appears, propose a future project strategy instead of modifying the current samplereverse strategy immediately.

## Case Payload

```json
{json.dumps(case_payload, ensure_ascii=False, indent=2)}
```
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register and bootstrap local reverse samples.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Register a local reverse sample.")
    add_parser.add_argument("path", help="Path to a local executable or challenge attachment.")
    add_parser.add_argument("--case-id", default="", help="Optional case id. Sanitized before use.")
    add_parser.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR), help="Local samples root directory.")

    solve_parser = subparsers.add_parser("solve", help="Generate a Codex task for a registered sample.")
    solve_parser.add_argument("case_id", help="Registered case id.")
    solve_parser.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR), help="Local samples root directory.")
    solve_parser.add_argument(
        "--run-static-harness",
        action="store_true",
        help="Also run the existing harness in Static Analysis mode without runtime tools.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
