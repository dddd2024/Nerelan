"""Tests for reverse_agent.local_reverse_single_sample_static_triage."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reverse_agent.local_reverse_single_sample_static_triage import (
    _blocked_artifact,
    _find_sample_root,
    _locate_sample,
    _now_iso,
    _parse_ida_evidence,
    _resolve_binary_path,
    _run_ida_static_triage,
    run_static_triage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# _find_sample_root
# ---------------------------------------------------------------------------

class TestFindSampleRoot:
    def test_returns_path_when_env_set_and_dir_exists(self, tmp_path: Path):
        with patch.dict("os.environ", {"LOCAL_REVERSE_ROOT": str(tmp_path)}):
            result = _find_sample_root()
            assert result is not None
            assert isinstance(result, Path)
            assert result == tmp_path

    def test_returns_none_when_no_candidate_exists(self):
        with patch.dict("os.environ", {"LOCAL_REVERSE_ROOT": ""}, clear=False):
            # Override all candidate checks by patching os.path.isdir
            with patch("os.path.isdir", return_value=False):
                result = _find_sample_root()
                assert result is None

    def test_returns_path_type(self):
        """Result, when not None, is always a Path instance."""
        with patch("os.path.isdir", return_value=False):
            result = _find_sample_root()
            # Either None or Path is acceptable
            if result is not None:
                assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# _locate_sample
# ---------------------------------------------------------------------------

class TestLocateSample:
    def test_sample_found_in_queue_and_inventory(self, tmp_path: Path):
        queue_data = {
            "items": [
                {
                    "sample_id": "cpp1_2f6fcb63",
                    "relative_path": "samples/cpp1_2f6fcb63.exe",
                    "sha256": "abcdef123456",
                    "size_bytes": 4096,
                    "file_type": "PE32",
                    "rank": 1,
                    "allowed_actions": ["static"],
                    "forbidden_actions": [],
                }
            ]
        }
        inventory_data = {
            "entries": [
                {
                    "sample_id": "cpp1_2f6fcb63",
                    "relative_path": "samples/cpp1_2f6fcb63.exe",
                    "sha256": "abcdef123456",
                    "size_bytes": 4096,
                    "guessed_file_type": "PE32 executable",
                    "category": "crackme",
                    "tags": ["cpp", "password"],
                }
            ]
        }
        queue_path = tmp_path / "queue.json"
        inv_path = tmp_path / "inventory.json"
        _write_json(queue_path, queue_data)
        _write_json(inv_path, inventory_data)

        result = _locate_sample("cpp1_2f6fcb63", queue_path, inv_path)

        assert result["queue"]["sample_id"] == "cpp1_2f6fcb63"
        assert result["inventory"]["sample_id"] == "cpp1_2f6fcb63"
        assert result["relative_path"] == "samples/cpp1_2f6fcb63.exe"
        assert result["sha256"] == "abcdef123456"
        assert result["size_bytes"] == 4096
        assert result["file_type"] == "PE32 executable"
        assert result["category"] == "crackme"
        assert result["tags"] == ["cpp", "password"]
        assert result["queue_rank"] == 1
        assert result["allowed_actions"] == ["static"]
        assert result["forbidden_actions"] == []

    def test_sample_not_found_returns_empty_dicts(self, tmp_path: Path):
        queue_data = {"items": []}
        inventory_data = {"entries": []}
        queue_path = tmp_path / "queue.json"
        inv_path = tmp_path / "inventory.json"
        _write_json(queue_path, queue_data)
        _write_json(inv_path, inventory_data)

        result = _locate_sample("nonexistent_id", queue_path, inv_path)

        assert result["queue"] == {}
        assert result["inventory"] == {}
        assert result["relative_path"] == ""
        assert result["sha256"] == ""
        assert result["size_bytes"] == 0
        assert result["file_type"] == ""
        assert result["category"] == ""
        assert result["tags"] == []
        assert result["queue_rank"] == -1

    def test_sample_only_in_inventory(self, tmp_path: Path):
        queue_data = {"items": []}
        inventory_data = {
            "entries": [
                {
                    "sample_id": "only_inv",
                    "relative_path": "samples/only_inv.exe",
                    "sha256": "invhash",
                    "size_bytes": 1024,
                    "guessed_file_type": "ELF",
                    "category": "keygen",
                    "tags": ["elf"],
                }
            ]
        }
        queue_path = tmp_path / "queue.json"
        inv_path = tmp_path / "inventory.json"
        _write_json(queue_path, queue_data)
        _write_json(inv_path, inventory_data)

        result = _locate_sample("only_inv", queue_path, inv_path)

        assert result["queue"] == {}
        assert result["inventory"]["sample_id"] == "only_inv"
        assert result["relative_path"] == "samples/only_inv.exe"
        assert result["sha256"] == "invhash"
        assert result["file_type"] == "ELF"
        assert result["category"] == "keygen"

    def test_missing_files_handled_gracefully(self, tmp_path: Path):
        queue_path = tmp_path / "no_queue.json"
        inv_path = tmp_path / "no_inventory.json"
        # Neither file exists

        result = _locate_sample("any_id", queue_path, inv_path)

        assert result["queue"] == {}
        assert result["inventory"] == {}
        assert result["relative_path"] == ""


# ---------------------------------------------------------------------------
# _resolve_binary_path
# ---------------------------------------------------------------------------

class TestResolveBinaryPath:
    def test_known_relative_path_resolves(self, tmp_path: Path):
        # Create a fake sample root with a binary
        samples_dir = tmp_path / "samples"
        samples_dir.mkdir()
        binary = samples_dir / "test.exe"
        binary.write_bytes(b"MZ")

        with patch(
            "reverse_agent.local_reverse_single_sample_static_triage._find_sample_root",
            return_value=tmp_path,
        ):
            result = _resolve_binary_path("samples/test.exe")

        assert result is not None
        assert isinstance(result, Path)
        assert result.exists()
        assert result == binary

    def test_empty_relative_path_returns_none(self):
        with patch(
            "reverse_agent.local_reverse_single_sample_static_triage._find_sample_root",
            return_value=Path("/fake"),
        ):
            result = _resolve_binary_path("")
            assert result is None

    def test_nonexistent_file_returns_none(self, tmp_path: Path):
        with patch(
            "reverse_agent.local_reverse_single_sample_static_triage._find_sample_root",
            return_value=tmp_path,
        ):
            result = _resolve_binary_path("no/such/file.exe")
            assert result is None

    def test_root_not_found_returns_none(self):
        with patch(
            "reverse_agent.local_reverse_single_sample_static_triage._find_sample_root",
            return_value=None,
        ):
            result = _resolve_binary_path("samples/something.exe")
            assert result is None


# ---------------------------------------------------------------------------
# _parse_ida_evidence
# ---------------------------------------------------------------------------

class TestParseIdaEvidence:
    def test_evidence_with_functions_strings_compare_contexts(self):
        evidence = {
            "strings": [
                {"value": "Correct!", "address": "0x401000"},
                {"value": "Wrong!", "address": "0x401010"},
                "plain string entry",
            ],
            "functions": [
                {"name": "main", "address": "0x401200"},
                {"name": "check_password", "address": "0x401300"},
            ],
            "compare_contexts": [
                {"type": "strcmp", "operand_a": "input", "operand_b": "secret"},
            ],
            "validation_function_candidates": ["check_password"],
            "solver_hints": [{"hint": "linear_comparison"}],
            "decompiler_snippets": ["int check_password(char *s) { return strcmp(s, secret); }"],
        }

        result = _parse_ida_evidence(evidence, exit_code=0)

        assert result["tool_status"] == "success"
        assert result["blocked_reason"] == ""
        assert result["source_tool"] == "IDA"
        assert result["exit_code"] == 0

        # Strings
        assert len(result["interesting_strings"]) == 3
        assert result["interesting_strings"][0]["value"] == "Correct!"
        assert result["interesting_strings"][0]["address"] == "0x401000"

        # Functions
        assert len(result["functions"]) == 2
        assert result["functions"][0]["name"] == "main"

        # Compare contexts
        assert len(result["compare_contexts"]) == 1
        assert result["compare_contexts"][0]["type"] == "strcmp"

        # Validation candidates
        assert result["validation_function_candidates"] == ["check_password"]

        # Solver hints
        assert len(result["solver_hints"]) == 1

        # Decompiler snippets
        assert len(result["decompiler_snippets"]) == 1

        # Hypotheses - compare_contexts present -> string_compare_password_checker
        assert "string_compare_password_checker" in result["solver_profile_hypotheses"]

    def test_scanf_functions_detected_as_input_apis(self):
        evidence = {
            "strings": [],
            "functions": [
                {"name": "scanf", "address": "0x401000"},
                {"name": "my_scanf_wrapper", "address": "0x401100"},
                {"name": "printf", "address": "0x401200"},
            ],
            "compare_contexts": [],
        }

        result = _parse_ida_evidence(evidence, exit_code=0)

        # scanf and my_scanf_wrapper should be detected as input APIs
        assert "scanf" in result["input_apis"]
        assert "my_scanf_wrapper" in result["input_apis"]
        # printf is not an input API
        assert "printf" not in result["input_apis"]

        # scanf -> hypotheses include scanf_input_validation
        assert "scanf_input_validation" in result["solver_profile_hypotheses"]
        # input_apis present -> standard_input_based
        assert "standard_input_based" in result["solver_profile_hypotheses"]

    def test_strcmp_functions_produce_hypotheses(self):
        evidence = {
            "strings": [],
            "functions": [
                {"name": "strcmp", "address": "0x401000"},
                {"name": "main", "address": "0x401100"},
            ],
            "compare_contexts": [],
        }

        result = _parse_ida_evidence(evidence, exit_code=0)

        assert "strcmp_direct_compare" in result["solver_profile_hypotheses"]

    def test_nonzero_exit_code_sets_blocked(self):
        evidence = {"strings": [], "functions": []}

        result = _parse_ida_evidence(evidence, exit_code=1)

        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "IDA_EXIT_CODE_1"
        assert result["exit_code"] == 1

    def test_string_truncation(self):
        """Strings longer than 200 chars are truncated."""
        long_string = "A" * 300
        evidence = {
            "strings": [{"value": long_string, "address": "0x1000"}],
            "functions": [],
        }

        result = _parse_ida_evidence(evidence, exit_code=0)

        assert len(result["interesting_strings"]) == 1
        assert len(result["interesting_strings"][0]["value"]) == 200

    def test_function_limit_30(self):
        """Only first 30 functions are included."""
        evidence = {
            "strings": [],
            "functions": [{"name": f"func_{i}", "address": f"0x{i:04x}"} for i in range(50)],
        }

        result = _parse_ida_evidence(evidence, exit_code=0)

        assert len(result["functions"]) == 30
        assert result["functions"][-1]["name"] == "func_29"


# ---------------------------------------------------------------------------
# _blocked_artifact
# ---------------------------------------------------------------------------

class TestBlockedArtifact:
    def test_produces_correct_structure(self):
        result = _blocked_artifact(
            sample_id="test_sample",
            relative_path="samples/test.exe",
            sha256="abc123",
            size_bytes=2048,
            file_type="PE32",
            category="crackme",
            tags=["test"],
            blocked_reason="SOME_REASON",
            detail="extra detail",
            source_tool="IDA",
            mainline="tool_integration",
        )

        # Required top-level fields
        assert result["schema_version"] == 1
        assert result["sample_id"] == "test_sample"
        assert result["relative_path"] == "samples/test.exe"
        assert result["analysis_mode"] == "single_sample_static_triage"
        assert result["mainline"] == "tool_integration"

        # Static-only invariants
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False

        # Candidate fields
        assert result["candidate"] is None
        assert result["known_candidate"] == ""

        # Blocked status
        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "SOME_REASON"
        assert result["blocked_detail"] == "extra detail"
        assert result["source_tool"] == "IDA"
        assert result["source_run"] == ""
        assert result["tool_provenance"] == {}

        # Metadata
        assert result["sha256"] == "abc123"
        assert result["size_bytes"] == 2048
        assert result["file_type"] == "PE32"
        assert result["category"] == "crackme"
        assert result["tags"] == ["test"]

        # generated_at is a non-empty ISO string
        assert isinstance(result["generated_at"], str)
        assert len(result["generated_at"]) > 0

        # Triage section present with empty lists
        triage = result["triage"]
        assert triage["input_apis"] == []
        assert triage["interesting_strings"] == []
        assert triage["functions"] == []
        assert triage["compare_contexts"] == []
        assert triage["validation_function_candidates"] == []
        assert triage["solver_profile_hypotheses"] == []
        assert triage["decompiler_snippets"] == []
        assert triage["solver_hints"] == []

        # recommended_next_action mentions the blocked reason
        assert "SOME_REASON" in result["recommended_next_action"]

    def test_default_optional_fields(self):
        """detail and source_tool default to empty strings."""
        result = _blocked_artifact(
            sample_id="s1",
            relative_path="",
            sha256="",
            size_bytes=0,
            file_type="",
            category="",
            tags=[],
            blocked_reason="REASON_X",
        )

        assert result["blocked_detail"] == ""
        assert result["source_tool"] == ""


class TestRunIdaStaticTriage:
    def test_ida_executable_missing_records_resolver_provenance(self, tmp_path: Path):
        with patch("reverse_agent.tool_runners._resolve_ida_executable", return_value=""), patch(
            "reverse_agent.tool_runners._resolve_ida_script",
            return_value=str(tmp_path / "collect_evidence.py"),
        ):
            result = _run_ida_static_triage(tmp_path / "sample.exe", tmp_path / "out")

        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "STATIC_TOOL_UNAVAILABLE: IDA executable not found"
        provenance = result["tool_provenance"]
        assert provenance["source_tool"] == "IDA"
        assert provenance["resolver"]["ida_executable_resolved"] is False
        assert provenance["resolver"]["ida_script_resolved"] is True
        assert provenance["ida_script"].endswith("collect_evidence.py")


# ---------------------------------------------------------------------------
# run_static_triage integration tests
# ---------------------------------------------------------------------------

class TestRunStaticTriageIntegration:
    def _make_queue_inv(self, tmp_path: Path, sample_id: str, relative_path: str = ""):
        queue_data: dict = {"items": []}
        if relative_path:
            queue_data["items"].append({
                "sample_id": sample_id,
                "relative_path": relative_path,
                "sha256": "deadbeef",
                "size_bytes": 8192,
                "file_type": "PE32",
                "rank": 5,
                "allowed_actions": ["static"],
                "forbidden_actions": [],
            })
        inventory_data: dict = {"entries": []}
        if relative_path:
            inventory_data["entries"].append({
                "sample_id": sample_id,
                "relative_path": relative_path,
                "sha256": "deadbeef",
                "size_bytes": 8192,
                "guessed_file_type": "PE32 executable",
                "category": "crackme",
                "tags": ["cpp"],
            })
        queue_path = tmp_path / "queue.json"
        inv_path = tmp_path / "inventory.json"
        _write_json(queue_path, queue_data)
        _write_json(inv_path, inventory_data)
        return queue_path, inv_path

    def test_sample_not_found_blocked(self, tmp_path: Path):
        """When sample is not in queue or inventory, returns BLOCKED/SAMPLE_NOT_FOUND."""
        queue_data = {"items": []}
        inventory_data = {"entries": []}
        queue_path = tmp_path / "queue.json"
        inv_path = tmp_path / "inventory.json"
        _write_json(queue_path, queue_data)
        _write_json(inv_path, inventory_data)
        out_path = tmp_path / "out.json"

        result = run_static_triage(
            sample_id="ghost_id",
            queue_path=queue_path,
            inventory_path=inv_path,
            artifact_index_path=None,
            out_path=out_path,
        )

        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "SAMPLE_NOT_FOUND_IN_QUEUE_OR_INVENTORY"
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
        # Output file was written
        assert out_path.exists()

    def test_binary_not_found_blocked(self, tmp_path: Path):
        """When binary cannot be resolved, returns BLOCKED/BINARY_NOT_FOUND."""
        queue_path, inv_path = self._make_queue_inv(
            tmp_path, "cpp1_abc", "samples/nonexistent.exe"
        )
        out_path = tmp_path / "out.json"

        # Patch _find_sample_root to return a real dir (but without the binary)
        fake_root = tmp_path / "fake_root"
        fake_root.mkdir()
        with patch(
            "reverse_agent.local_reverse_single_sample_static_triage._find_sample_root",
            return_value=fake_root,
        ):
            result = run_static_triage(
                sample_id="cpp1_abc",
                queue_path=queue_path,
                inventory_path=inv_path,
                artifact_index_path=None,
                out_path=out_path,
            )

        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "BINARY_NOT_FOUND"
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
        assert out_path.exists()

    def test_ida_blocked_propagates(self, tmp_path: Path):
        """When IDA returns blocked status, artifact is blocked with that reason."""
        queue_path, inv_path = self._make_queue_inv(
            tmp_path, "cpp1_blocked", "samples/blocked.exe"
        )
        out_path = tmp_path / "out.json"

        # Create the binary so path resolution succeeds
        fake_root = tmp_path / "fake_root"
        samples_dir = fake_root / "samples"
        samples_dir.mkdir(parents=True)
        (samples_dir / "blocked.exe").write_bytes(b"MZ")

        ida_mock_result = {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA executable not found",
            "source_tool": "IDA",
            "tool_provenance": {
                "source_tool": "IDA",
                "ida_executable": "",
                "ida_script": "collect_evidence.py",
            },
        }

        with patch(
            "reverse_agent.local_reverse_single_sample_static_triage._find_sample_root",
            return_value=fake_root,
        ), patch(
            "reverse_agent.local_reverse_single_sample_static_triage._run_ida_static_triage",
            return_value=ida_mock_result,
        ):
            result = run_static_triage(
                sample_id="cpp1_blocked",
                queue_path=queue_path,
                inventory_path=inv_path,
                artifact_index_path=None,
                out_path=out_path,
            )

        assert result["tool_status"] == "blocked"
        assert "STATIC_TOOL_UNAVAILABLE" in result["blocked_reason"]
        assert result["source_tool"] == "IDA"
        assert result["tool_provenance"]["ida_script"] == "collect_evidence.py"
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""

    def test_blocked_artifact_updates_artifact_index(self, tmp_path: Path):
        """Blocked static triage is still registered as current provenance."""
        queue_path, inv_path = self._make_queue_inv(
            tmp_path, "cpp1_blocked", "samples/blocked.exe"
        )
        out_path = tmp_path / "project_state" / "local_reverse_cpp1_blocked_static_triage.json"
        index_path = tmp_path / "project_state" / "artifact_index.json"
        decision_path = tmp_path / "project_state" / "decision_packet.md"
        decision_path.parent.mkdir(parents=True)
        decision_path.write_text(
            """```json decision_meta
{"round_id": "round_test_static_triage_v1"}
```
""",
            encoding="utf-8",
        )

        fake_root = tmp_path / "fake_root"
        samples_dir = fake_root / "samples"
        samples_dir.mkdir(parents=True)
        (samples_dir / "blocked.exe").write_bytes(b"MZ")

        with patch(
            "reverse_agent.local_reverse_single_sample_static_triage._find_sample_root",
            return_value=fake_root,
        ), patch(
            "reverse_agent.local_reverse_single_sample_static_triage._run_ida_static_triage",
            return_value={
                "tool_status": "blocked",
                "blocked_reason": "STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON",
                "source_tool": "IDA",
                "tool_provenance": {"exit_code": 0, "expected_evidence_path": "ida_evidence.json"},
            },
        ), patch(
            "reverse_agent.local_reverse_single_sample_static_triage._now_iso",
            return_value="2026-06-14T00:00:00Z",
        ):
            result = run_static_triage(
                sample_id="cpp1_blocked",
                queue_path=queue_path,
                inventory_path=inv_path,
                artifact_index_path=index_path,
                out_path=out_path,
            )

        assert result["tool_status"] == "blocked"
        assert result["source_run"] == "round_test_static_triage_v1"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        entry = index["latest_artifacts_v2"]["local_reverse_cpp1_blocked_static_triage"]
        assert entry["freshness"] == "current"
        assert entry["kind"] == "local_reverse_single_sample_static_triage"
        assert entry["sample_id"] == "cpp1_blocked"
        assert entry["source_run"] == "round_test_static_triage_v1"
        assert entry["tool_status"] == "blocked"
        assert entry["size_bytes"] == out_path.stat().st_size
        assert len(entry["sha256"]) == 64

    def test_ida_success_full_artifact(self, tmp_path: Path):
        """When IDA succeeds, artifact has triage dict with all expected keys."""
        queue_path, inv_path = self._make_queue_inv(
            tmp_path, "cpp1_ok", "samples/ok.exe"
        )
        out_path = tmp_path / "out.json"
        index_path = tmp_path / "artifact_index.json"

        # Create the binary
        fake_root = tmp_path / "fake_root"
        samples_dir = fake_root / "samples"
        samples_dir.mkdir(parents=True)
        (samples_dir / "ok.exe").write_bytes(b"MZ")

        ida_mock_result = {
            "tool_status": "success",
            "blocked_reason": "",
            "source_tool": "IDA",
            "exit_code": 0,
            "input_apis": ["scanf"],
            "interesting_strings": [{"address": "0x1000", "value": "password"}],
            "functions": [{"name": "main", "address": "0x2000"}],
            "compare_contexts": [{"type": "strcmp"}],
            "validation_function_candidates": ["check"],
            "solver_profile_hypotheses": ["string_compare_password_checker", "standard_input_based"],
            "decompiler_snippets": [],
            "solver_hints": [],
        }

        with patch(
            "reverse_agent.local_reverse_single_sample_static_triage._find_sample_root",
            return_value=fake_root,
        ), patch(
            "reverse_agent.local_reverse_single_sample_static_triage._run_ida_static_triage",
            return_value=ida_mock_result,
        ), patch(
            "reverse_agent.local_reverse_single_sample_static_triage._now_iso",
            return_value="2026-06-05T00:00:00Z",
        ):
            result = run_static_triage(
                sample_id="cpp1_ok",
                queue_path=queue_path,
                inventory_path=inv_path,
                artifact_index_path=index_path,
                out_path=out_path,
            )

        # Success status
        assert result["tool_status"] == "success"
        assert result["blocked_reason"] == ""

        # Static-only invariants
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""

        # Triage dict has all expected keys
        triage = result["triage"]
        expected_keys = [
            "input_apis",
            "interesting_strings",
            "functions",
            "compare_contexts",
            "validation_function_candidates",
            "solver_profile_hypotheses",
            "decompiler_snippets",
            "solver_hints",
        ]
        for key in expected_keys:
            assert key in triage, f"Missing triage key: {key}"

        # Values match IDA mock
        assert triage["input_apis"] == ["scanf"]
        assert len(triage["interesting_strings"]) == 1
        assert triage["compare_contexts"][0]["type"] == "strcmp"

        # Metadata
        assert result["sample_id"] == "cpp1_ok"
        assert result["relative_path"] == "samples/ok.exe"
        assert result["sha256"] == "deadbeef"
        assert result["size_bytes"] == 8192
        assert result["file_type"] == "PE32 executable"
        assert result["category"] == "crackme"
        assert result["tags"] == ["cpp"]
        assert result["queue_rank"] == 5
        assert result["generated_at"] == "2026-06-05T00:00:00Z"

        # recommended_next_action mentions compare context
        assert "Compare context" in result["recommended_next_action"]

        # Output file was written
        assert out_path.exists()
        index = json.loads(index_path.read_text(encoding="utf-8"))
        entry = index["latest_artifacts_v2"]["local_reverse_cpp1_ok_static_triage"]
        assert entry["freshness"] == "current"
        assert entry["kind"] == "local_reverse_single_sample_static_triage"
        assert entry["path"] == str(out_path).replace("\\", "/")
        assert entry["tool_status"] == "success"
