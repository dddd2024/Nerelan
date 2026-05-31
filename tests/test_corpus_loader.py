"""Tests for corpus_loader module."""

import json
import tempfile
from pathlib import Path

import pytest

from reverse_agent.corpus_loader import (
    CorpusCase,
    compute_sha256,
    load_corpus_cases,
    load_manifest,
    validate_corpus,
    verify_case_files,
)


class TestComputeSha256:
    """Tests for compute_sha256 function."""

    def test_compute_sha256_basic(self):
        """Test SHA256 computation for a simple file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("hello world")
            temp_path = Path(f.name)

        try:
            result = compute_sha256(temp_path)
            expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
            assert result == expected
        finally:
            temp_path.unlink()

    def test_compute_sha256_empty_file(self):
        """Test SHA256 computation for an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = compute_sha256(temp_path)
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert result == expected
        finally:
            temp_path.unlink()


class TestLoadManifest:
    """Tests for load_manifest function."""

    def test_load_manifest_success(self):
        """Test loading a valid manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [],
            }
            manifest_path = corpus_dir / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)

            result = load_manifest(corpus_dir)
            assert result["corpus_name"] == "test"
            assert result["samples"] == []

    def test_load_manifest_not_found(self):
        """Test loading a missing manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            with pytest.raises(FileNotFoundError):
                load_manifest(corpus_dir)

    def test_load_manifest_invalid_json(self):
        """Test loading an invalid manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            manifest_path = corpus_dir / "manifest.json"
            with open(manifest_path, "w") as f:
                f.write("not valid json")

            with pytest.raises(json.JSONDecodeError):
                load_manifest(corpus_dir)


class TestLoadCorpusCases:
    """Tests for load_corpus_cases function."""

    def test_load_empty_corpus(self):
        """Test loading an empty corpus."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            cases = load_corpus_cases(corpus_dir)
            assert cases == []

    def test_load_single_case(self):
        """Test loading a corpus with one case."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            case_id = "test_case"
            case_dir = corpus_dir / case_id
            case_dir.mkdir()

            # Create manifest
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [
                    {
                        "case_id": case_id,
                        "path": str(case_dir / "sample.exe"),
                        "sha256": "abc123",
                        "size_bytes": 100,
                    }
                ],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create required files
            metadata = {
                "case_id": case_id,
                "sha256": "abc123",
                "size_bytes": 100,
                "category": "test",
                "tags": ["test"],
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            with open(case_dir / "case.json", "w") as f:
                json.dump({"cases": []}, f)

            with open(case_dir / "notes.md", "w") as f:
                f.write("Test notes")

            with open(case_dir / "codex_task.md", "w") as f:
                f.write("Test task")

            cases = load_corpus_cases(corpus_dir)
            assert len(cases) == 1
            assert cases[0].case_id == case_id
            assert cases[0].sha256 == "abc123"
            assert cases[0].safe_to_run is False
            assert cases[0].upload_allowed is True


class TestVerifyCaseFiles:
    """Tests for verify_case_files function."""

    def test_verify_complete_case(self):
        """Test verifying a complete case with all files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir)
            case = CorpusCase(
                case_id="test",
                sample_path=case_dir / "sample.exe",
                sha256="",
                size_bytes=0,
                category="",
                tags=[],
                safe_to_run=False,
                upload_allowed=True,
                metadata_path=case_dir / "metadata.json",
                case_json_path=case_dir / "case.json",
                notes_path=case_dir / "notes.md",
                codex_task_path=case_dir / "codex_task.md",
                notes="",
            )

            # Create all required files
            for path in [
                case.sample_path,
                case.metadata_path,
                case.case_json_path,
                case.notes_path,
                case.codex_task_path,
            ]:
                path.touch()

            errors = verify_case_files(case)
            assert errors == []

    def test_verify_missing_files(self):
        """Test verifying a case with missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir)
            case = CorpusCase(
                case_id="test",
                sample_path=case_dir / "sample.exe",
                sha256="",
                size_bytes=0,
                category="",
                tags=[],
                safe_to_run=False,
                upload_allowed=True,
                metadata_path=case_dir / "metadata.json",
                case_json_path=case_dir / "case.json",
                notes_path=case_dir / "notes.md",
                codex_task_path=case_dir / "codex_task.md",
                notes="",
            )

            errors = verify_case_files(case)
            assert len(errors) == 5
            assert all("Missing" in e for e in errors)


class TestValidateCorpus:
    """Tests for validate_corpus function."""

    def test_validate_empty_corpus(self):
        """Test validating an empty corpus."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = validate_corpus(corpus_dir)
            assert result["valid"] is True
            assert result["cases_checked"] == 0
            assert result["cases_valid"] == 0

    def test_validate_missing_manifest(self):
        """Test validating a corpus without manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert "manifest.json not found" in result["errors"][0]

    def test_validate_safe_to_run_constraint(self):
        """Test that safe_to_run must be false."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            case_id = "test_case"
            case_dir = corpus_dir / case_id
            case_dir.mkdir()

            # Create manifest
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [
                    {
                        "case_id": case_id,
                        "path": str(case_dir / "sample.exe"),
                        "sha256": "",
                        "size_bytes": 0,
                    }
                ],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create metadata with safe_to_run=True (invalid)
            metadata = {
                "case_id": case_id,
                "sha256": "",
                "size_bytes": 0,
                "safe_to_run": True,  # Invalid
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            with open(case_dir / "case.json", "w") as f:
                json.dump({}, f)

            with open(case_dir / "notes.md", "w") as f:
                f.write("")

            with open(case_dir / "codex_task.md", "w") as f:
                f.write("")

            with open(case_dir / "sample.exe", "w") as f:
                f.write("")

            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert any("safe_to_run must be false" in e for e in result["errors"])

    def test_validate_upload_allowed_constraint(self):
        """Test that upload_allowed must be true."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            case_id = "test_case"
            case_dir = corpus_dir / case_id
            case_dir.mkdir()

            # Create manifest
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [
                    {
                        "case_id": case_id,
                        "path": str(case_dir / "sample.exe"),
                        "sha256": "",
                        "size_bytes": 0,
                    }
                ],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create metadata with upload_allowed=False (invalid)
            metadata = {
                "case_id": case_id,
                "sha256": "",
                "size_bytes": 0,
                "safe_to_run": False,
                "upload_allowed": False,  # Invalid
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            with open(case_dir / "case.json", "w") as f:
                json.dump({}, f)

            with open(case_dir / "notes.md", "w") as f:
                f.write("")

            with open(case_dir / "codex_task.md", "w") as f:
                f.write("")

            with open(case_dir / "sample.exe", "w") as f:
                f.write("")

            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert any("upload_allowed must be true" in e for e in result["errors"])


class TestRealCorpus:
    """Tests against the real sample_corpus/reverse/ directory."""

    def test_load_real_corpus(self):
        """Test loading the real corpus."""
        corpus_dir = Path("sample_corpus/reverse")
        if not corpus_dir.exists():
            pytest.skip("Real corpus not found")

        cases = load_corpus_cases(corpus_dir)
        assert len(cases) > 0

        # Verify all cases have required properties
        for case in cases:
            assert case.case_id
            assert case.sha256
            assert case.size_bytes > 0
            assert case.safe_to_run is False
            assert case.upload_allowed is True

    def test_validate_real_corpus(self):
        """Test validating the real corpus."""
        corpus_dir = Path("sample_corpus/reverse")
        if not corpus_dir.exists():
            pytest.skip("Real corpus not found")

        result = validate_corpus(corpus_dir)
        assert result["valid"] is True, f"Validation errors: {result['errors']}"
        assert result["cases_checked"] == result["cases_valid"]


class TestValidateCorpusPathValidation:
    """Tests for validate_corpus path validation."""

    def _create_basic_corpus(self, tmpdir: str, case_id: str = "test_case") -> Path:
        """Create a basic valid corpus structure."""
        corpus_dir = Path(tmpdir)
        case_dir = corpus_dir / case_id
        case_dir.mkdir()

        # Create manifest
        manifest = {
            "schema_version": 1,
            "corpus_name": "test",
            "samples": [
                {
                    "case_id": case_id,
                    "path": str(case_dir / "sample.exe"),
                    "sha256": "",
                    "size_bytes": 0,
                }
            ],
        }
        with open(corpus_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        # Create sample.exe
        with open(case_dir / "sample.exe", "w") as f:
            f.write("")

        # Create notes.md and codex_task.md
        with open(case_dir / "notes.md", "w") as f:
            f.write("")
        with open(case_dir / "codex_task.md", "w") as f:
            f.write("")

        return case_dir

    def test_validate_corpus_sha256_mismatch(self):
        """Test that sha256 mismatch is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            case_id = "test_case"
            case_dir = corpus_dir / case_id
            case_dir.mkdir()

            # Create sample.exe with some content
            with open(case_dir / "sample.exe", "w") as f:
                f.write("actual content here")

            # Create manifest with WRONG sha256 (mismatch with actual file)
            import hashlib
            wrong_sha256 = "0" * 64  # Wrong hash
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [
                    {
                        "case_id": case_id,
                        "path": str(case_dir / "sample.exe"),
                        "sha256": wrong_sha256,
                        "size_bytes": 0,
                    }
                ],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create metadata
            metadata = {
                "case_id": case_id,
                "sha256": wrong_sha256,
                "size_bytes": 0,
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            # Create case.json
            with open(case_dir / "case.json", "w") as f:
                json.dump({"cases": []}, f)

            with open(case_dir / "notes.md", "w") as f:
                f.write("")

            with open(case_dir / "codex_task.md", "w") as f:
                f.write("")

            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert any("SHA256 mismatch" in e for e in result["errors"])

    def test_validate_corpus_size_mismatch(self):
        """Test that size mismatch is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            case_id = "test_case"
            case_dir = corpus_dir / case_id
            case_dir.mkdir()

            # Write some content to sample.exe
            content = "some content here"
            with open(case_dir / "sample.exe", "w") as f:
                f.write(content)
            actual_size = len(content)

            # Create manifest with WRONG size
            wrong_size = 99999
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [
                    {
                        "case_id": case_id,
                        "path": str(case_dir / "sample.exe"),
                        "sha256": "",
                        "size_bytes": wrong_size,  # Wrong size
                    }
                ],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create metadata
            metadata = {
                "case_id": case_id,
                "sha256": "",
                "size_bytes": wrong_size,
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            # Create case.json
            with open(case_dir / "case.json", "w") as f:
                json.dump({"cases": []}, f)

            with open(case_dir / "notes.md", "w") as f:
                f.write("")

            with open(case_dir / "codex_task.md", "w") as f:
                f.write("")

            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert any("Size mismatch" in e for e in result["errors"])

    def test_validate_metadata_sample_path_absolute(self):
        """Test that absolute sample_path is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = self._create_basic_corpus(tmpdir)
            case_id = "test_case"

            # Create metadata with absolute sample_path
            metadata = {
                "case_id": case_id,
                "sha256": "",
                "size_bytes": 0,
                "sample_path": "/absolute/path/to/sample.exe",
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            # Create case.json
            with open(case_dir / "case.json", "w") as f:
                json.dump({"cases": []}, f)

            corpus_dir = Path(tmpdir)
            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert any("sample_path must be relative" in e for e in result["errors"])

    def test_validate_metadata_sample_path_local_reverse_samples(self):
        """Test that sample_path containing local_reverse_samples is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = self._create_basic_corpus(tmpdir)
            case_id = "test_case"

            # Create metadata with sample_path containing local_reverse_samples
            metadata = {
                "case_id": case_id,
                "sha256": "",
                "size_bytes": 0,
                "sample_path": "local_reverse_samples/test/sample.exe",
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            # Create case.json
            with open(case_dir / "case.json", "w") as f:
                json.dump({"cases": []}, f)

            corpus_dir = Path(tmpdir)
            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert any("local_reverse_samples" in e for e in result["errors"])

    def test_validate_case_json_input_value_mismatch(self):
        """Test that case.json input_value with .. is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = self._create_basic_corpus(tmpdir)
            case_id = "test_case"

            # Create valid metadata
            metadata = {
                "case_id": case_id,
                "sha256": "",
                "size_bytes": 0,
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            # Create case.json with input_value containing ..
            case_data = {
                "cases": [
                    {
                        "input_value": "../escaped/path/sample.exe"
                    }
                ]
            }
            with open(case_dir / "case.json", "w") as f:
                json.dump(case_data, f)

            corpus_dir = Path(tmpdir)
            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert any("input_value must not contain '..'" in e for e in result["errors"])

    def test_validate_case_json_input_value_local_reverse_samples(self):
        """Test that case.json input_value containing local_reverse_samples is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = self._create_basic_corpus(tmpdir)
            case_id = "test_case"

            # Create valid metadata
            metadata = {
                "case_id": case_id,
                "sha256": "",
                "size_bytes": 0,
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            # Create case.json with input_value containing local_reverse_samples
            case_data = {
                "cases": [
                    {
                        "input_value": "local_reverse_samples/test/sample.exe"
                    }
                ]
            }
            with open(case_dir / "case.json", "w") as f:
                json.dump(case_data, f)

            corpus_dir = Path(tmpdir)
            result = validate_corpus(corpus_dir)
            assert result["valid"] is False
            assert any("local_reverse_samples" in e for e in result["errors"])
