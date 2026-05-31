"""Tests for sample_corpus structure validation.

This module validates the structure and metadata of the curated sample corpus.
"""

from __future__ import annotations

import hashlib
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

    def test_sample_file_sha256_matches_metadata(self) -> None:
        """Verify actual sample.exe sha256 matches metadata."""
        metadata_list = self.get_all_metadata()
        if not metadata_list:
            pytest.skip("No metadata files found")

        for case_id, metadata in metadata_list:
            sample_path = CORPUS_DIR / case_id / "sample.exe"
            if not sample_path.exists():
                pytest.skip(f"{case_id} sample.exe not found")

            actual_sha256 = hashlib.sha256(sample_path.read_bytes()).hexdigest()
            expected_sha256 = metadata.get("sha256", "")
            assert actual_sha256 == expected_sha256, (
                f"{case_id}: actual sha256 {actual_sha256} does not match metadata {expected_sha256}"
            )

    def test_sample_file_size_matches_metadata(self) -> None:
        """Verify actual sample.exe size matches metadata."""
        metadata_list = self.get_all_metadata()
        if not metadata_list:
            pytest.skip("No metadata files found")

        for case_id, metadata in metadata_list:
            sample_path = CORPUS_DIR / case_id / "sample.exe"
            if not sample_path.exists():
                pytest.skip(f"{case_id} sample.exe not found")

            actual_size = sample_path.stat().st_size
            expected_size = metadata.get("size_bytes", 0)
            assert actual_size == expected_size, (
                f"{case_id}: actual size {actual_size} does not match metadata {expected_size}"
            )

    def test_metadata_sample_path_points_to_existing_file(self) -> None:
        """Verify metadata.sample_path points to an existing file."""
        metadata_list = self.get_all_metadata()
        if not metadata_list:
            pytest.skip("No metadata files found")

        for case_id, metadata in metadata_list:
            sample_path_str = metadata.get("sample_path", "")
            # Convert relative path to absolute
            sample_path = Path(__file__).parent.parent / sample_path_str.replace("/", os.sep)
            assert sample_path.exists(), f"{case_id}: sample_path {sample_path_str} does not exist"


class TestCaseJson:
    """Tests for case.json content."""

    def get_all_case_json(self) -> list[tuple[str, dict]]:
        """Get all case.json contents."""
        if not CORPUS_DIR.exists():
            return []

        result = []
        for case_dir in CORPUS_DIR.iterdir():
            if not case_dir.is_dir():
                continue
            case_json_path = case_dir / "case.json"
            if case_json_path.exists():
                with open(case_json_path) as f:
                    result.append((case_dir.name, json.load(f)))
        return result

    def test_case_json_input_value_uses_corpus_path(self) -> None:
        """Verify case.json input_value uses sample_corpus/reverse/ path."""
        case_list = self.get_all_case_json()
        if not case_list:
            pytest.skip("No case.json files found")

        for case_id, case_data in case_list:
            cases = case_data.get("cases", [])
            if not cases:
                continue
            case = cases[0]
            input_value = case.get("input_value", "")
            assert input_value.startswith("sample_corpus/reverse/"), (
                f"{case_id}: input_value should start with sample_corpus/reverse/"
            )

    def test_case_json_does_not_reference_local_reverse_samples(self) -> None:
        """Verify case.json does not contain old local_reverse_samples paths."""
        case_list = self.get_all_case_json()
        if not case_list:
            pytest.skip("No case.json files found")

        for case_id, case_data in case_list:
            case_json_str = json.dumps(case_data)
            assert "local_reverse_samples" not in case_json_str, (
                f"{case_id}: case.json still references local_reverse_samples"
            )

    def test_case_json_input_value_matches_metadata_sample_path(self) -> None:
        """Verify case.json input_value matches metadata.sample_path."""
        if not CORPUS_DIR.exists():
            pytest.skip("Corpus directory does not exist")

        for case_dir in CORPUS_DIR.iterdir():
            if not case_dir.is_dir():
                continue

            case_id = case_dir.name
            case_json_path = case_dir / "case.json"
            metadata_path = case_dir / "metadata.json"

            if not case_json_path.exists() or not metadata_path.exists():
                continue

            with open(case_json_path) as f:
                case_data = json.load(f)
            with open(metadata_path) as f:
                metadata = json.load(f)

            case_input_value = case_data.get("cases", [{}])[0].get("input_value", "")
            metadata_sample_path = metadata.get("sample_path", "")

            assert case_input_value == metadata_sample_path, (
                f"{case_id}: case.json input_value {case_input_value} does not match "
                f"metadata.sample_path {metadata_sample_path}"
            )


class TestCodexTask:
    """Tests for codex_task.md content."""

    def get_all_codex_tasks(self) -> list[tuple[str, str]]:
        """Get all codex_task.md contents."""
        if not CORPUS_DIR.exists():
            return []

        result = []
        for case_dir in CORPUS_DIR.iterdir():
            if not case_dir.is_dir():
                continue
            task_path = case_dir / "codex_task.md"
            if task_path.exists():
                result.append((case_dir.name, task_path.read_text()))
        return result

    def test_codex_task_uses_corpus_path(self) -> None:
        """Verify codex_task.md uses sample_corpus/reverse/ paths."""
        task_list = self.get_all_codex_tasks()
        if not task_list:
            pytest.skip("No codex_task.md files found")

        for case_id, content in task_list:
            assert f"sample_corpus/reverse/{case_id}/sample.exe" in content, (
                f"{case_id}: codex_task.md should reference sample_corpus/reverse/{case_id}/sample.exe"
            )

    def test_codex_task_does_not_reference_old_paths(self) -> None:
        """Verify codex_task.md does not contain old local_reverse_samples paths."""
        task_list = self.get_all_codex_tasks()
        if not task_list:
            pytest.skip("No codex_task.md files found")

        for case_id, content in task_list:
            assert f"local_reverse_samples/{case_id}/sample.exe" not in content, (
                f"{case_id}: codex_task.md still references local_reverse_samples/{case_id}/sample.exe"
            )
            assert f"local_reverse_samples\\{case_id}\\sample.exe" not in content, (
                f"{case_id}: codex_task.md still references local_reverse_samples\\{case_id}\\sample.exe"
            )


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
