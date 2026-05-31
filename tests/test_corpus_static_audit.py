"""Tests for corpus_static_audit module."""

import json
import tempfile
from pathlib import Path

import pytest

from reverse_agent.corpus_static_audit import (
    generate_gap_report,
    main,
    run_audit,
)


class TestRunAudit:
    """Tests for run_audit function."""

    def test_run_audit_empty_corpus(self):
        """Test audit on empty corpus."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = run_audit(corpus_dir)

            assert result["schema_version"] == 1
            assert result["corpus_dir"] == str(corpus_dir)
            assert result["execution_policy"]["static_only"] is True
            assert result["execution_policy"]["executed_samples"] is False
            assert result["summary"]["total_cases"] == 0
            assert result["cases"] == []

    def test_run_audit_single_case(self):
        """Test audit on corpus with one case."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            case_id = "test_case"
            case_dir = corpus_dir / case_id
            case_dir.mkdir()

            # Create sample.exe
            sample_content = b"MZ" + b"\x00" * 100  # Fake PE
            with open(case_dir / "sample.exe", "wb") as f:
                f.write(sample_content)

            # Compute actual sha256 and size
            import hashlib
            actual_sha256 = hashlib.sha256(sample_content).hexdigest()
            actual_size = len(sample_content)

            # Create manifest with correct sha256 and size
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [
                    {
                        "case_id": case_id,
                        "path": str(case_dir / "sample.exe"),
                        "sha256": actual_sha256,
                        "size_bytes": actual_size,
                    }
                ],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create metadata with correct sha256 and size
            metadata = {
                "case_id": case_id,
                "sha256": actual_sha256,
                "size_bytes": actual_size,
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

            result = run_audit(corpus_dir)

            assert result["summary"]["total_cases"] == 1
            assert len(result["cases"]) == 1

            case_result = result["cases"][0]
            assert case_result["case_id"] == case_id
            assert case_result["sha256"] == actual_sha256
            assert case_result["status"] == "static_profiled"
            assert "static_features" in case_result
            assert "classification" in case_result

    def test_execution_policy_flags(self):
        """Test that execution policy flags are correctly set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir)
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            result = run_audit(corpus_dir)

            policy = result["execution_policy"]
            assert policy["executed_samples"] is False
            assert policy["runtime_probe_used"] is False
            assert policy["static_only"] is True


class TestGenerateGapReport:
    """Tests for generate_gap_report function."""

    def test_basic_report(self):
        """Test basic gap report generation."""
        audit_result = {
            "schema_version": 1,
            "generated_at": "2024-01-01T00:00:00",
            "corpus_dir": "test_corpus",
            "execution_policy": {
                "executed_samples": False,
                "runtime_probe_used": False,
                "static_only": True,
            },
            "cases": [],
            "summary": {
                "total_cases": 0,
                "classified_cases": 0,
                "unknown_cases": 0,
                "category_counts": {},
            },
        }

        report = generate_gap_report(audit_result)

        assert "Corpus Solver Gap Report" in report
        assert "test_corpus" in report
        assert "Static Analysis Only: True" in report
        assert "Total Samples: 0" in report

    def test_report_with_cases(self):
        """Test report generation with sample cases."""
        audit_result = {
            "schema_version": 1,
            "generated_at": "2024-01-01T00:00:00",
            "corpus_dir": "test_corpus",
            "execution_policy": {
                "executed_samples": False,
                "runtime_probe_used": False,
                "static_only": True,
            },
            "cases": [
                {
                    "case_id": "rc4_test",
                    "sha256": "abc123",
                    "size_bytes": 1000,
                    "static_features": {
                        "format": "pe",
                        "file_size": 1000,
                        "ascii_strings_sample": [],
                        "utf16_strings_sample": [],
                        "keyword_hits": [],
                        "crypto_hints": [],
                        "compare_hints": [],
                        "interesting_constants": [],
                        "entropy_hint": "medium",
                    },
                    "classification": {
                        "case_id": "rc4_test",
                        "predicted_category": "rc4_like",
                        "confidence": "low",
                        "evidence": [
                            {"type": "filename", "detail": "Contains rc4", "strength": "weak"}
                        ],
                        "recommended_next_step": "Analyze RC4",
                    },
                    "status": "static_profiled",
                }
            ],
            "summary": {
                "total_cases": 1,
                "classified_cases": 1,
                "unknown_cases": 0,
                "category_counts": {"rc4_like": 1},
            },
        }

        report = generate_gap_report(audit_result)

        assert "rc4_test" in report
        assert "rc4_like" in report
        assert "Category Distribution" in report
        assert "Capability Coverage" in report
        assert "Capability Gaps" in report

    def test_report_includes_recommendations(self):
        """Test that report includes recommendations."""
        audit_result = {
            "schema_version": 1,
            "generated_at": "2024-01-01T00:00:00",
            "corpus_dir": "test_corpus",
            "execution_policy": {
                "executed_samples": False,
                "runtime_probe_used": False,
                "static_only": True,
            },
            "cases": [],
            "summary": {
                "total_cases": 0,
                "classified_cases": 0,
                "unknown_cases": 0,
                "category_counts": {},
            },
        }

        report = generate_gap_report(audit_result)

        assert "Recommendations" in report
        assert "Next Steps" in report


class TestMain:
    """Tests for main CLI function."""

    def test_main_with_temp_corpus(self, capsys):
        """Test main function with temporary corpus."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir) / "corpus"
            corpus_dir.mkdir()
            out_path = Path(tmpdir) / "audit.json"
            gap_path = Path(tmpdir) / "gap.md"

            # Create empty manifest
            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Mock argv
            import sys
            old_argv = sys.argv
            try:
                sys.argv = [
                    "corpus_static_audit",
                    "--corpus-dir", str(corpus_dir),
                    "--out", str(out_path),
                    "--gap-report", str(gap_path),
                ]
                main()
            finally:
                sys.argv = old_argv

            # Check outputs were created
            assert out_path.exists()
            assert gap_path.exists()

            # Check JSON output
            with open(out_path) as f:
                result = json.load(f)
            assert result["schema_version"] == 1
            assert result["summary"]["total_cases"] == 0

            # Check markdown output
            with open(gap_path) as f:
                report = f.read()
            assert "Corpus Solver Gap Report" in report


class TestValidationRejection:
    """Tests for validation rejection."""

    def test_run_audit_rejects_invalid_corpus(self):
        """Test that run_audit rejects invalid corpus."""
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
                        "sha256": "wrong_hash",
                        "size_bytes": 0,
                    }
                ],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create sample.exe with different content
            with open(case_dir / "sample.exe", "w") as f:
                f.write("actual content")

            # Create metadata with wrong sha256
            metadata = {
                "case_id": case_id,
                "sha256": "wrong_hash",
                "size_bytes": 0,
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            with open(case_dir / "case.json", "w") as f:
                json.dump({"cases": []}, f)

            with open(case_dir / "notes.md", "w") as f:
                f.write("")

            with open(case_dir / "codex_task.md", "w") as f:
                f.write("")

            # Should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                run_audit(corpus_dir)
            assert "Corpus validation failed" in str(exc_info.value)

    def test_cli_rejects_invalid_corpus(self, capsys):
        """Test that CLI exits with error on invalid corpus."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir) / "corpus"
            corpus_dir.mkdir()
            out_path = Path(tmpdir) / "audit.json"

            # Create manifest with case that will fail validation
            case_id = "test_case"
            case_dir = corpus_dir / case_id
            case_dir.mkdir()

            manifest = {
                "schema_version": 1,
                "corpus_name": "test",
                "samples": [
                    {
                        "case_id": case_id,
                        "path": str(case_dir / "sample.exe"),
                        "sha256": "wrong_hash",
                        "size_bytes": 0,
                    }
                ],
            }
            with open(corpus_dir / "manifest.json", "w") as f:
                json.dump(manifest, f)

            # Create sample.exe
            with open(case_dir / "sample.exe", "w") as f:
                f.write("actual content")

            # Create metadata with wrong sha256
            metadata = {
                "case_id": case_id,
                "sha256": "wrong_hash",
                "size_bytes": 0,
                "safe_to_run": False,
                "upload_allowed": True,
            }
            with open(case_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

            with open(case_dir / "case.json", "w") as f:
                json.dump({"cases": []}, f)

            with open(case_dir / "notes.md", "w") as f:
                f.write("")

            with open(case_dir / "codex_task.md", "w") as f:
                f.write("")

            # Mock argv and test exit
            import sys
            old_argv = sys.argv
            old_exit = sys.exit
            exit_code = [None]

            def mock_exit(code):
                exit_code[0] = code
                raise SystemExit(code)

            sys.exit = mock_exit

            try:
                sys.argv = [
                    "corpus_static_audit",
                    "--corpus-dir", str(corpus_dir),
                    "--out", str(out_path),
                ]
                main()
            except SystemExit:
                pass
            finally:
                sys.argv = old_argv
                sys.exit = old_exit

            assert exit_code[0] == 1


class TestRealCorpus:
    """Tests against real corpus (if available)."""

    def test_audit_real_corpus(self):
        """Test audit on real corpus."""
        corpus_dir = Path("sample_corpus/reverse")
        if not corpus_dir.exists():
            pytest.skip("Real corpus not found")

        result = run_audit(corpus_dir)

        # Basic structure checks
        assert result["schema_version"] == 1
        assert "generated_at" in result
        assert result["execution_policy"]["static_only"] is True
        assert result["execution_policy"]["executed_samples"] is False

        # Should have cases
        assert result["summary"]["total_cases"] > 0
        assert len(result["cases"]) > 0

        # Each case should have required fields
        for case in result["cases"]:
            assert "case_id" in case
            assert "sha256" in case
            assert "static_features" in case
            assert "classification" in case
            assert case["status"] == "static_profiled"

            # Classification should have required fields
            classification = case["classification"]
            assert "predicted_category" in classification
            assert "confidence" in classification
            assert "recommended_next_step" in classification

    def test_gap_report_real_corpus(self):
        """Test gap report generation from real audit."""
        corpus_dir = Path("sample_corpus/reverse")
        if not corpus_dir.exists():
            pytest.skip("Real corpus not found")

        result = run_audit(corpus_dir)
        report = generate_gap_report(result)

        # Check report content
        assert "Corpus Solver Gap Report" in report
        assert "Execution Policy" in report
        assert "Summary" in report
        assert "Sample Details" in report
        assert "Current Capability Coverage" in report
        assert "Capability Gaps" in report
        assert "Recommendations" in report

        # Check that all cases are documented
        for case in result["cases"]:
            assert case["case_id"] in report
