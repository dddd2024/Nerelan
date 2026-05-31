"""Tests for sample_corpus structure validation.

This module validates the structure and metadata of the curated sample corpus.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


CORPUS_DIR = Path(__file__).parent.parent / "sample_corpus" / "reverse"


class TestCorpusStructure:
    """Tests for corpus directory structure."""

    def test_corpus_directory_exists(self) -> None:
        """Verify sample_corpus/reverse/ directory exists."""
        assert CORPUS_DIR.exists(), f"Corpus directory {CORPUS_DIR} does not exist"
        assert CORPUS_DIR.is_dir(), f"{CORPUS_DIR} is not a directory"

    def test_manifest_exists(self) -> None:
        """Verify manifest.json exists and is valid JSON."""
        manifest_path = CORPUS_DIR / "manifest.json"
        assert manifest_path.exists(), "manifest.json not found"
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert "samples" in manifest, "manifest.json missing 'samples' key"
        assert len(manifest["samples"]) > 0, "manifest.json has no samples"

    def test_readme_exists(self) -> None:
        """Verify README.md exists."""
        readme_path = CORPUS_DIR / "README.md"
        assert readme_path.exists(), "README.md not found"
        content = readme_path.read_text()
        assert "safe_to_run=false" in content, "README missing safety notice"
        assert "upload_allowed=true" in content, "README missing upload policy"


class TestSampleStructure:
    """Tests for individual sample structure."""

    def get_all_case_dirs(self) -> list[Path]:
        """Get all case directories in the corpus."""
        if not CORPUS_DIR.exists():
            return []
        return [d for d in CORPUS_DIR.iterdir() if d.is_dir()]

    def test_no_root_exe_files(self) -> None:
        """Verify no loose .exe files in corpus root."""
        if not CORPUS_DIR.exists():
            pytest.skip("Corpus directory does not exist")
        exe_files = list(CORPUS_DIR.glob("*.exe"))
        assert len(exe_files) == 0, f"Found loose .exe files in corpus root: {exe_files}"

    @pytest.mark.parametrize(
        "required_file",
        ["sample.exe", "metadata.json", "case.json", "notes.md", "codex_task.md"],
    )
    def test_each_case_has_required_files(self, required_file: str) -> None:
        """Verify each case directory has all required files."""
        case_dirs = self.get_all_case_dirs()
        if not case_dirs:
            pytest.skip("No case directories found")

        for case_dir in case_dirs:
            file_path = case_dir / required_file
            assert file_path.exists(), f"{case_dir.name} missing {required_file}"


class TestMetadata:
    """Tests for sample metadata."""

    def get_all_metadata(self) -> list[tuple[str, dict]]:
        """Get all metadata.json contents."""
        if not CORPUS_DIR.exists():
            return []

        result = []
        for case_dir in CORPUS_DIR.iterdir():
            if not case_dir.is_dir():
                continue
            metadata_path = case_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    result.append((case_dir.name, json.load(f)))
        return result

    def test_metadata_has_required_fields(self) -> None:
        """Verify metadata.json has all required fields."""
        metadata_list = self.get_all_metadata()
        if not metadata_list:
            pytest.skip("No metadata files found")

        required_fields = [
            "case_id",
            "sample_filename",
            "sample_path",
            "sha256",
            "size_bytes",
            "upload_allowed",
            "safe_to_run",
        ]

        for case_id, metadata in metadata_list:
            for field in required_fields:
                assert field in metadata, f"{case_id} metadata missing {field}"

    def test_upload_allowed_is_true(self) -> None:
        """Verify all samples have upload_allowed=true."""
        metadata_list = self.get_all_metadata()
        if not metadata_list:
            pytest.skip("No metadata files found")

        for case_id, metadata in metadata_list:
            assert metadata.get("upload_allowed") is True, f"{case_id} upload_allowed is not True"

    def test_safe_to_run_is_false(self) -> None:
        """Verify all samples have safe_to_run=false."""
        metadata_list = self.get_all_metadata()
        if not metadata_list:
            pytest.skip("No metadata files found")

        for case_id, metadata in metadata_list:
            assert metadata.get("safe_to_run") is False, f"{case_id} safe_to_run is not False"

    def test_sample_path_format(self) -> None:
        """Verify sample_path uses relative format without local absolute paths."""
        metadata_list = self.get_all_metadata()
        if not metadata_list:
            pytest.skip("No metadata files found")

        for case_id, metadata in metadata_list:
            path = metadata.get("sample_path", "")
            # Should not contain Windows drive letters or absolute paths
            assert ":\\" not in path, f"{case_id} sample_path contains absolute Windows path"
            assert not path.startswith("/"), f"{case_id} sample_path starts with /"
            # Should start with sample_corpus/
            assert path.startswith("sample_corpus/"), f"{case_id} sample_path should start with sample_corpus/"


class TestManifestConsistency:
    """Tests for manifest.json consistency with actual samples."""

    def test_manifest_matches_actual_samples(self) -> None:
        """Verify manifest.json entries match actual case directories."""
        if not CORPUS_DIR.exists():
            pytest.skip("Corpus directory does not exist")

        manifest_path = CORPUS_DIR / "manifest.json"
        if not manifest_path.exists():
            pytest.skip("manifest.json not found")

        with open(manifest_path) as f:
            manifest = json.load(f)

        manifest_case_ids = {s["case_id"] for s in manifest.get("samples", [])}
        actual_case_ids = {d.name for d in CORPUS_DIR.iterdir() if d.is_dir()}

        # Remove non-case directories from actual
        actual_case_ids.discard("manifest.json")
        actual_case_ids.discard("README.md")

        assert manifest_case_ids == actual_case_ids, (
            f"Manifest case_ids {manifest_case_ids} do not match "
            f"actual directories {actual_case_ids}"
        )

    def test_manifest_sha256_matches_metadata(self) -> None:
        """Verify manifest sha256 values match individual metadata files."""
        if not CORPUS_DIR.exists():
            pytest.skip("Corpus directory does not exist")

        manifest_path = CORPUS_DIR / "manifest.json"
        if not manifest_path.exists():
            pytest.skip("manifest.json not found")

        with open(manifest_path) as f:
            manifest = json.load(f)

        manifest_samples = {s["case_id"]: s for s in manifest.get("samples", [])}

        for case_dir in CORPUS_DIR.iterdir():
            if not case_dir.is_dir():
                continue

            case_id = case_dir.name
            if case_id not in manifest_samples:
                continue

            metadata_path = case_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            with open(metadata_path) as f:
                metadata = json.load(f)

            manifest_sha256 = manifest_samples[case_id].get("sha256")
            metadata_sha256 = metadata.get("sha256")

            assert manifest_sha256 == metadata_sha256, (
                f"{case_id}: manifest sha256 {manifest_sha256} "
                f"does not match metadata sha256 {metadata_sha256}"
            )
