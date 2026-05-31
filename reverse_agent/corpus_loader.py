"""Corpus loader for reverse engineering samples.

This module provides functionality to load and validate the sample_corpus/reverse/
directory structure without executing any binaries.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CorpusCase:
    """Represents a single corpus case."""

    case_id: str
    sample_path: Path
    sha256: str
    size_bytes: int
    category: str
    tags: list[str]
    safe_to_run: bool
    upload_allowed: bool
    metadata_path: Path
    case_json_path: Path
    notes_path: Path
    codex_task_path: Path
    notes: str


def compute_sha256(path: Path) -> str:
    """Compute SHA256 hash of a file.

    Args:
        path: Path to the file

    Returns:
        Hex-encoded SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_manifest(corpus_dir: Path) -> dict[str, Any]:
    """Load manifest.json from corpus directory.

    Args:
        corpus_dir: Path to corpus directory

    Returns:
        Parsed manifest JSON

    Raises:
        FileNotFoundError: If manifest.json does not exist
        json.JSONDecodeError: If manifest.json is invalid
    """
    manifest_path = corpus_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {corpus_dir}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_corpus_cases(corpus_dir: Path) -> list[CorpusCase]:
    """Load all corpus cases from directory.

    Args:
        corpus_dir: Path to corpus directory

    Returns:
        List of CorpusCase objects

    Raises:
        FileNotFoundError: If manifest.json does not exist
        ValueError: If case data is invalid
    """
    manifest = load_manifest(corpus_dir)
    cases: list[CorpusCase] = []

    for sample_info in manifest.get("samples", []):
        case_id = sample_info["case_id"]
        case_dir = corpus_dir / case_id

        # Check required files exist
        metadata_path = case_dir / "metadata.json"
        case_json_path = case_dir / "case.json"
        notes_path = case_dir / "notes.md"
        codex_task_path = case_dir / "codex_task.md"
        sample_path = case_dir / "sample.exe"

        # Read metadata
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Read notes
        notes = ""
        if notes_path.exists():
            with open(notes_path, "r", encoding="utf-8") as f:
                notes = f.read()

        case = CorpusCase(
            case_id=case_id,
            sample_path=sample_path,
            sha256=metadata.get("sha256", ""),
            size_bytes=metadata.get("size_bytes", 0),
            category=metadata.get("category", "unknown"),
            tags=metadata.get("tags", []),
            safe_to_run=metadata.get("safe_to_run", False),
            upload_allowed=metadata.get("upload_allowed", True),
            metadata_path=metadata_path,
            case_json_path=case_json_path,
            notes_path=notes_path,
            codex_task_path=codex_task_path,
            notes=notes,
        )
        cases.append(case)

    return cases


def verify_case_files(case: CorpusCase) -> list[str]:
    """Verify all required files exist for a case.

    Args:
        case: CorpusCase to verify

    Returns:
        List of error messages (empty if all valid)
    """
    errors: list[str] = []

    required_files = [
        (case.sample_path, "sample.exe"),
        (case.metadata_path, "metadata.json"),
        (case.case_json_path, "case.json"),
        (case.notes_path, "notes.md"),
        (case.codex_task_path, "codex_task.md"),
    ]

    for path, name in required_files:
        if not path.exists():
            errors.append(f"Missing {name} for case {case.case_id}")

    return errors


def validate_corpus(corpus_dir: Path) -> dict[str, Any]:
    """Validate entire corpus directory.

    Performs comprehensive validation:
    1. manifest.json exists and is valid
    2. All required files exist for each case
    3. SHA256 hashes match
    4. File sizes match
    5. safe_to_run is false
    6. upload_allowed is true

    Args:
        corpus_dir: Path to corpus directory

    Returns:
        Validation result with status and errors
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "cases_checked": 0,
        "cases_valid": 0,
    }

    try:
        manifest = load_manifest(corpus_dir)
    except FileNotFoundError as e:
        result["valid"] = False
        result["errors"].append(str(e))
        return result
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["errors"].append(f"Invalid manifest.json: {e}")
        return result

    samples = manifest.get("samples", [])
    result["cases_checked"] = len(samples)

    for sample_info in samples:
        case_id = sample_info["case_id"]
        case_dir = corpus_dir / case_id

        # Check required files
        required = {
            "sample.exe": case_dir / "sample.exe",
            "metadata.json": case_dir / "metadata.json",
            "case.json": case_dir / "case.json",
            "notes.md": case_dir / "notes.md",
            "codex_task.md": case_dir / "codex_task.md",
        }

        for name, path in required.items():
            if not path.exists():
                result["valid"] = False
                result["errors"].append(f"[{case_id}] Missing {name}")

        # Validate sample.exe
        sample_path = case_dir / "sample.exe"
        if sample_path.exists():
            # Check SHA256
            expected_sha256 = sample_info.get("sha256", "")
            actual_sha256 = compute_sha256(sample_path)
            if expected_sha256 and actual_sha256 != expected_sha256:
                result["valid"] = False
                result["errors"].append(
                    f"[{case_id}] SHA256 mismatch: expected {expected_sha256[:16]}..., "
                    f"got {actual_sha256[:16]}..."
                )

            # Check size
            expected_size = sample_info.get("size_bytes", 0)
            actual_size = sample_path.stat().st_size
            if expected_size and actual_size != expected_size:
                result["valid"] = False
                result["errors"].append(
                    f"[{case_id}] Size mismatch: expected {expected_size}, got {actual_size}"
                )

        # Validate metadata
        metadata_path = case_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            if metadata.get("safe_to_run") is not False:
                result["valid"] = False
                result["errors"].append(
                    f"[{case_id}] safe_to_run must be false"
                )

            if metadata.get("upload_allowed") is not True:
                result["valid"] = False
                result["errors"].append(
                    f"[{case_id}] upload_allowed must be true"
                )

        if not any(e.startswith(f"[{case_id}]") for e in result["errors"]):
            result["cases_valid"] += 1

    return result
