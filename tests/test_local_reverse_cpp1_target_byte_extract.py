"""Tests for reverse_agent.local_reverse_cpp1_target_byte_extract."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reverse_agent.local_reverse_cpp1_target_byte_extract import (
    _blocked_artifact,
    _build_evidence_notes,
    _extract_forward_transform,
    _find_sample_root,
    _parse_extraction,
    _resolve_binary_path,
    run_target_bytes_current_revalidation,
    run_target_provenance_recheck,
    run_target_byte_extraction,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def _write_minimal_pe_with_target(path: Path, target_bytes: bytes) -> None:
    data = bytearray(b"\0" * 0x2000)
    data[0:2] = b"MZ"
    data[0x3C:0x40] = (0x80).to_bytes(4, "little")
    data[0x80:0x84] = b"PE\0\0"
    coff = 0x84
    data[coff + 2:coff + 4] = (1).to_bytes(2, "little")
    data[coff + 16:coff + 18] = (0xE0).to_bytes(2, "little")
    optional = coff + 20
    data[optional:optional + 2] = (0x10B).to_bytes(2, "little")
    data[optional + 28:optional + 32] = (0x400000).to_bytes(4, "little")
    section = optional + 0xE0
    data[section:section + 8] = b".data\0\0\0"
    data[section + 8:section + 12] = (0x2000).to_bytes(4, "little")
    data[section + 12:section + 16] = (0x29000).to_bytes(4, "little")
    data[section + 16:section + 20] = (0x2000).to_bytes(4, "little")
    data[section + 20:section + 24] = (0x400).to_bytes(4, "little")
    target_offset = 0x400 + 0xA30
    data[target_offset - 0x40:target_offset + 0x40 + 18] = bytes(
        (i * 7) & 0xFF for i in range(0x40 + 0x40 + 18)
    )
    data[target_offset:target_offset + len(target_bytes)] = target_bytes
    path.write_bytes(data)


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
            with patch("os.path.isdir", return_value=False):
                result = _find_sample_root()
                assert result is None

    def test_returns_path_type(self):
        """Result, when not None, is always a Path instance."""
        with patch("os.path.isdir", return_value=False):
            result = _find_sample_root()
            if result is not None:
                assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# _resolve_binary_path
# ---------------------------------------------------------------------------

class TestResolveBinaryPath:
    def test_known_relative_path_resolves(self, tmp_path: Path):
        samples_dir = tmp_path / "samples"
        samples_dir.mkdir()
        binary = samples_dir / "test.exe"
        binary.write_bytes(b"MZ")

        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=tmp_path,
        ):
            result = _resolve_binary_path("samples/test.exe")

        assert result is not None
        assert isinstance(result, Path)
        assert result.exists()
        assert result == binary

    def test_empty_relative_path_returns_none(self):
        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=Path("/fake"),
        ):
            result = _resolve_binary_path("")
            assert result is None

    def test_nonexistent_file_returns_none(self, tmp_path: Path):
        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=tmp_path,
        ):
            result = _resolve_binary_path("no/such/file.exe")
            assert result is None

    def test_root_not_found_returns_none(self):
        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=None,
        ):
            result = _resolve_binary_path("samples/something.exe")
            assert result is None


# ---------------------------------------------------------------------------
# _parse_extraction
# ---------------------------------------------------------------------------

class TestParseExtraction:
    def test_named_data_found_populates_target_bytes(self):
        extract_data = {
            "named_data": {
                "found": True,
                "name": "byte_429A30",
                "address": "0x429A30",
                "length": 16,
                "bytes_hex": "deadbeef" * 4,
                "bytes": [0xDE, 0xAD, 0xBE, 0xEF] * 4,
            },
            "function": {
                "found": False,
                "name": "",
                "address": "",
                "pseudocode": "",
            },
            "compare_context": {},
        }

        result = _parse_extraction(extract_data, exit_code=0)

        assert result["tool_status"] == "success"
        assert result["blocked_reason"] == ""
        assert result["source_tool"] == "IDA"
        assert result["exit_code"] == 0
        assert result["target_symbol"] == "byte_429A30"
        assert result["target_address"] == "0x429A30"
        assert result["target_length"] == 16
        assert result["target_bytes_hex"] == "deadbeef" * 4
        assert result["target_bytes"] == [0xDE, 0xAD, 0xBE, 0xEF] * 4

    def test_named_data_not_found_sets_blocked(self):
        extract_data = {
            "named_data": {"found": False},
            "function": {"found": False},
            "compare_context": {},
        }

        result = _parse_extraction(extract_data, exit_code=0)

        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "TARGET_BYTES_NOT_FOUND"
        assert result["target_bytes"] == []
        assert result["target_bytes_hex"] == ""

    def test_function_found_populates_pseudocode(self):
        extract_data = {
            "named_data": {
                "found": True,
                "name": "byte_429A30",
                "address": "0x429A30",
                "length": 16,
                "bytes_hex": "aabbccdd",
                "bytes": [0xAA, 0xBB, 0xCC, 0xDD],
            },
            "function": {
                "found": True,
                "name": "_main_0",
                "address": "0x401000",
                "pseudocode": "int __cdecl main(int argc, const char **argv)",
            },
            "compare_context": {
                "compare_expression": "Destination[i] == byte_429A30[i]",
                "loop_context": "for (i = 0; i < 16; ++i)",
            },
        }

        result = _parse_extraction(extract_data, exit_code=0)

        assert result["main_function"] == "_main_0"
        assert result["main_function_address"] == "0x401000"
        assert result["main_pseudocode"] == "int __cdecl main(int argc, const char **argv)"
        assert result["compare_expression"] == "Destination[i] == byte_429A30[i]"
        assert result["loop_context"] == "for (i = 0; i < 16; ++i)"

    def test_nonzero_exit_code_sets_blocked(self):
        extract_data = {
            "named_data": {"found": True, "name": "x", "address": "", "length": 0, "bytes_hex": "", "bytes": []},
            "function": {"found": False},
            "compare_context": {},
        }

        result = _parse_extraction(extract_data, exit_code=2)

        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "IDA_EXIT_CODE_2"
        assert result["exit_code"] == 2


# ---------------------------------------------------------------------------
# _extract_forward_transform
# ---------------------------------------------------------------------------

class TestExtractForwardTransform:
    def test_pseudocode_with_bit_manipulation_formula(self):
        pseudocode = """
        v5 = (Str[i] & 3) | (16 * (Str[i] & 0x0C)) | ((Str[i] & 0xF0) >> 2);
        """
        result = _extract_forward_transform(pseudocode)

        assert result["input_buffer"] == "Str"
        assert result["work_buffer"] == "Destination"
        assert result["copy_length"] == 16
        assert "& 3" in result["formula_c"]
        assert "& 0x0C" in result["formula_c"]
        assert ">> 2" in result["formula_c"]
        assert "nibble/bit-level transform detected" in result["notes"]

    def test_empty_pseudocode_returns_default_formula(self):
        result = _extract_forward_transform("")

        # When pseudocode is empty, formula_c stays empty (default is only applied
        # after scanning lines and not finding a match)
        assert result["formula_c"] == ""
        assert result["notes"] == []

    def test_pseudocode_without_formula_returns_default(self):
        """Pseudocode without bit-manipulation pattern gets default formula."""
        result = _extract_forward_transform("int main() { return 0; }")

        assert result["formula_c"] == "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)"
        assert "formula from static triage evidence" in result["notes"]

    def test_pseudocode_with_alternative_formula_pattern(self):
        pseudocode = "v3 = (buf[i] & 3) | ((buf[i] & 0x0C) * 16) | ((buf[i] & 0xF0) >> 2);"
        result = _extract_forward_transform(pseudocode)

        assert "& 3" in result["formula_c"]
        assert "* 16" in result["formula_c"]
        assert "& 0xF0" in result["formula_c"]
        assert "nibble/bit-level transform detected" in result["notes"]

    def test_length_check_and_copy_operation_notes(self):
        pseudocode = """
        if (len != 18) return 0;
        strncpy(Destination, Str, 16);
        """
        result = _extract_forward_transform(pseudocode)

        assert any("length check found" in note for note in result["notes"])
        assert any("copy operation" in note for note in result["notes"])


# ---------------------------------------------------------------------------
# _build_evidence_notes
# ---------------------------------------------------------------------------

class TestBuildEvidenceNotes:
    def test_length_discrepancy_detected(self):
        pseudocode = """
        if (strlen(input) != 18) return 0;
        if (len == 16) return 1;
        """
        notes = _build_evidence_notes(pseudocode)

        assert any("length discrepancy" in note for note in notes)
        assert any("18" in note and "16" in note for note in notes)

    def test_division_anomaly_detected(self):
        pseudocode = """
        v9 = some_value;
        result = value / v9;
        """
        notes = _build_evidence_notes(pseudocode)

        assert any("division operation detected" in note for note in notes)
        assert any("potential anti-debug trap" in note for note in notes)

    def test_memory_check_detected(self):
        pseudocode = """
        if (memory check failed) exit(-1);
        """
        notes = _build_evidence_notes(pseudocode)

        assert any("memory check string found" in note for note in notes)

    def test_empty_pseudocode_returns_empty_notes(self):
        notes = _build_evidence_notes("")
        assert notes == []

    def test_no_anomalies_returns_empty_notes(self):
        pseudocode = "int main() { return 0; }"
        notes = _build_evidence_notes(pseudocode)
        assert notes == []


# ---------------------------------------------------------------------------
# _blocked_artifact
# ---------------------------------------------------------------------------

class TestBlockedArtifact:
    def test_produces_correct_structure(self):
        result = _blocked_artifact(
            sample_id="test_sample",
            blocked_reason="SOME_REASON",
            detail="extra detail",
            source_tool="IDA",
        )

        # Required top-level fields
        assert result["schema_version"] == 1
        assert result["sample_id"] == "test_sample"
        assert result["relative_path"] == ""
        assert result["analysis_mode"] == "target_compare_byte_extraction"
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

        # Default transform structure
        forward = result["forward_transform"]
        assert forward["input_buffer"] == "Str"
        assert forward["work_buffer"] == "Destination"
        assert forward["copy_length"] == 16
        assert forward["formula_c"] == "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)"
        assert forward["compare_expression"] == "Destination[i] == byte_429A30[i]"
        assert forward["notes"] == []

        # Empty target bytes
        assert result["target_bytes"] == []
        assert result["target_bytes_hex"] == ""
        assert result["target_length"] == 0

        # generated_at is a non-empty ISO string
        assert isinstance(result["generated_at"], str)
        assert len(result["generated_at"]) > 0

        # recommended_next_action mentions the blocked reason
        assert "SOME_REASON" in result["recommended_next_action"]

    def test_default_optional_fields(self):
        """detail and source_tool default to empty strings."""
        result = _blocked_artifact(
            sample_id="s1",
            blocked_reason="REASON_X",
        )

        assert result["blocked_detail"] == ""
        assert result["source_tool"] == ""


# ---------------------------------------------------------------------------
# run_target_byte_extraction integration tests
# ---------------------------------------------------------------------------

class TestRunTargetByteExtractionIntegration:
    def _make_triage_inv(self, tmp_path: Path, sample_id: str, relative_path: str = ""):
        triage_data: dict = {"relative_path": relative_path} if relative_path else {}
        inventory_data: dict = {"entries": []}
        if relative_path:
            inventory_data["entries"].append({
                "sample_id": sample_id,
                "relative_path": relative_path,
                "sha256": "deadbeef",
                "size_bytes": 8192,
            })
        triage_path = tmp_path / "triage.json"
        inv_path = tmp_path / "inventory.json"
        _write_json(triage_path, triage_data)
        _write_json(inv_path, inventory_data)
        return triage_path, inv_path

    def test_sample_not_in_triage_blocked(self, tmp_path: Path):
        """When sample is not in triage or inventory, returns BLOCKED/SAMPLE_NOT_FOUND_IN_TRIAGE_OR_INVENTORY."""
        triage_data = {}
        inventory_data = {"entries": []}
        triage_path = tmp_path / "triage.json"
        inv_path = tmp_path / "inventory.json"
        _write_json(triage_path, triage_data)
        _write_json(inv_path, inventory_data)
        out_path = tmp_path / "out.json"

        result = run_target_byte_extraction(
            sample_id="ghost_id",
            triage_path=triage_path,
            inventory_path=inv_path,
            out_path=out_path,
        )

        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "SAMPLE_NOT_FOUND_IN_TRIAGE_OR_INVENTORY"
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
        assert out_path.exists()


class TestTargetBytesCurrentRevalidation:
    def _write_sources(self, tmp_path: Path) -> dict[str, Path]:
        target_bytes = [0xD5, 0x96, 0xC4, 0xF6, 0x07, 0x45, 0x57, 0x77, 0x76, 0xE5, 0xF6, 0x48, 0x47, 0xF7, 0x48, 0x17]
        pseudocode = """int __cdecl main_0(int argc, const char **argv, const char **envp)
{
  signed int v4;
  char Str[20];
  int i;
  printf("Please input the password : ");
  scanf("%s", Str);
  v4 = strlen(Str);
  if ( v4 != 18 )
    printf("Sorry,you are wrong!\\n");
  strncpy(Destination, Str, 0x10u);
  for ( i = 0; i < v4; ++i )
    Destination[i] = Destination[i] & 3 | (16 * (Destination[i] & 0xC)) | ((Destination[i] & 0xF0) >> 2);
  for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i )
    ;
  if ( i == 16 )
    printf("Congratulations! You are right!\\n");
  return -1;
}
"""
        triage_path = tmp_path / "project_state" / "local_reverse_cpp1_2f6fcb63_static_triage.json"
        target_path = tmp_path / "project_state" / "local_reverse_cpp1_2f6fcb63_target_bytes.json"
        index_path = tmp_path / "project_state" / "artifact_index.json"
        out_path = tmp_path / "project_state" / "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json"
        _write_json(
            triage_path,
            {
                "schema_version": 1,
                "sample_id": "cpp1_2f6fcb63",
                "relative_path": "逆向课程2023春01/CPP1.exe",
                "sha256": "2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede",
                "tool_status": "success",
                "source_tool": "IDA",
                "executed_sample": False,
                "static_only": True,
                "runtime_validated": False,
                "candidate": None,
                "known_candidate": "",
                "triage": {
                    "decompiler_snippets": [
                        {
                            "function": "_main_0",
                            "entry_ea": "0x401190",
                            "text": pseudocode,
                        }
                    ]
                },
            },
        )
        _write_json(
            target_path,
            {
                "schema_version": 1,
                "sample_id": "cpp1_2f6fcb63",
                "relative_path": "逆向课程2023春01/CPP1.exe",
                "analysis_mode": "target_compare_byte_extraction",
                "mainline": "tool_integration",
                "executed_sample": False,
                "static_only": True,
                "runtime_validated": False,
                "tool_status": "success",
                "blocked_reason": "",
                "source_tool": "IDA",
                "target_symbol": "byte_429A30",
                "target_address": "0x00429A30",
                "target_length": 16,
                "target_bytes_hex": bytes(target_bytes).hex(),
                "target_bytes": target_bytes,
                "main_function": "_main_0",
                "main_function_address": "0x00401190",
                "main_pseudocode": pseudocode,
                "forward_transform": {
                    "input_buffer": "Str",
                    "work_buffer": "Destination",
                    "copy_length": 16,
                    "formula_c": "(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)",
                    "compare_expression": "Destination[i] == byte_429A30[i]",
                    "notes": ["length check found: if ( v4 != 18 )"],
                },
                "compare_expression": "for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i )",
                "candidate": None,
                "known_candidate": "",
            },
        )
        _write_json(
            index_path,
            {
                "schema_version": 1,
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    "local_reverse_cpp1_2f6fcb63_static_triage": {
                        "kind": "local_reverse_single_sample_static_triage",
                        "path": str(triage_path).replace("\\", "/"),
                        "freshness": "current",
                        "source_run": "round_static_triage",
                        "sample_id": "cpp1_2f6fcb63",
                    }
                },
                "artifact_refs": {},
            },
        )
        return {
            "triage": triage_path,
            "target": target_path,
            "index": index_path,
            "out": out_path,
        }

    def test_current_revalidation_success_writes_artifact_without_ida_or_candidate(self, tmp_path: Path):
        paths = self._write_sources(tmp_path)
        before_target = paths["target"].read_text(encoding="utf-8")

        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._now_iso",
            return_value="2026-06-14T10:00:00Z",
        ):
            result = run_target_bytes_current_revalidation(
                target_bytes_path=paths["target"],
                triage_path=paths["triage"],
                artifact_index_path=paths["index"],
                out_path=paths["out"],
                source_run="round_dynamic_revalidation",
            )

        assert result["analysis_mode"] == "target_bytes_current_revalidation"
        assert result["mainline"] == "tool_integration"
        assert result["revalidation_status"] == "PASSED"
        assert result["executed_sample"] is False
        assert result["static_only"] is True
        assert result["runtime_validated"] is False
        assert result["ida_used_this_round"] is False
        assert result["sample_executed_this_round"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
        assert result["target_bytes_hex"] == "d596c4f60745577776e5f64847f74817"
        assert result["forward_transform"]["copy_length"] == 16
        assert all(check["status"] == "PASSED" for check in result["revalidation_checks"])
        assert "solver/reverse_solving decision" in result["recommended_next_action"]
        assert paths["target"].read_text(encoding="utf-8") == before_target
        assert paths["out"].exists()

    def test_current_revalidation_updates_artifact_index_with_dynamic_source_run(self, tmp_path: Path):
        paths = self._write_sources(tmp_path)

        result = run_target_bytes_current_revalidation(
            target_bytes_path=paths["target"],
            triage_path=paths["triage"],
            artifact_index_path=paths["index"],
            out_path=paths["out"],
            source_run="round_custom_source",
        )

        index = json.loads(paths["index"].read_text(encoding="utf-8"))
        entry = index["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_target_bytes_revalidation"]
        assert entry["freshness"] == "current"
        assert entry["kind"] == "target_bytes_current_revalidation"
        assert entry["path"] == str(paths["out"]).replace("\\", "/")
        assert entry["source_run"] == "round_custom_source"
        assert entry["sample_id"] == "cpp1_2f6fcb63"
        assert len(entry["sha256"]) == 64
        assert result["source_artifact_freshness"]["current_static_triage"]["freshness"] == "current"
        assert result["source_artifact_freshness"]["old_target_bytes"]["freshness"] == "not_registered"

    def test_current_revalidation_mismatch_fails_not_success(self, tmp_path: Path):
        paths = self._write_sources(tmp_path)
        target = json.loads(paths["target"].read_text(encoding="utf-8"))
        target["sample_id"] = "wrong_sample"
        target["target_bytes"][0] = 0
        paths["target"].write_text(json.dumps(target, indent=2), encoding="utf-8")

        result = run_target_bytes_current_revalidation(
            target_bytes_path=paths["target"],
            triage_path=paths["triage"],
            artifact_index_path=paths["index"],
            out_path=paths["out"],
            source_run="round_dynamic_revalidation",
        )

        assert result["revalidation_status"] == "FAILED"
        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "REVALIDATION_FIELD_MISMATCH"
        assert "sample_id" in result["mismatched_fields"]
        assert "target_bytes_hex" in result["mismatched_fields"]
        assert result["candidate"] is None
        assert result["known_candidate"] == ""


class TestTargetProvenanceRecheck(TestRunTargetByteExtractionIntegration):
    def _write_sources(self, tmp_path: Path) -> dict[str, Path]:
        target_bytes = bytes.fromhex("d596c4f60745577776e5f64847f74817")
        binary = tmp_path / "CPP1.exe"
        _write_minimal_pe_with_target(binary, target_bytes)

        artifact_index_path = tmp_path / "artifact_index.json"
        target_path = tmp_path / "target_bytes.json"
        transform_path = tmp_path / "transform.json"
        signed_path = tmp_path / "signed.json"
        ida_path = tmp_path / "ida.json"
        out_path = tmp_path / "target_provenance.json"

        source_entries = {
            "local_reverse_cpp1_2f6fcb63_target_bytes": str(target_path),
            "local_reverse_cpp1_2f6fcb63_transform_recheck": str(transform_path),
            "local_reverse_cpp1_2f6fcb63_signed_transform_recheck": str(signed_path),
            "local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck": str(ida_path),
        }
        _write_json(
            artifact_index_path,
            {
                "schema_version": 1,
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    key: {
                        "path": value,
                        "freshness": "current",
                        "source_run": "round_source",
                        "sample_id": "cpp1_2f6fcb63",
                    }
                    for key, value in source_entries.items()
                },
                "artifact_refs": {},
            },
        )
        _write_json(
            target_path,
            {
                "schema_version": 1,
                "sample_id": "cpp1_2f6fcb63",
                "relative_path": "CPP1.exe",
                "target_symbol": "byte_429A30",
                "target_address": "0x00429A30",
                "target_length": 16,
                "target_bytes_hex": target_bytes.hex(),
                "target_bytes": list(target_bytes),
                "executed_sample": False,
                "static_only": True,
                "runtime_validated": False,
                "candidate": None,
                "known_candidate": "",
            },
        )
        _write_json(
            transform_path,
            {
                "schema_version": 1,
                "sample_id": "cpp1_2f6fcb63",
                "executed_sample": False,
                "static_only": True,
                "runtime_validated": False,
                "candidate": None,
                "known_candidate": "",
            },
        )
        _write_json(
            signed_path,
            {
                "schema_version": 1,
                "sample_id": "cpp1_2f6fcb63",
                "executed_sample": False,
                "static_only": True,
                "runtime_validated": False,
                "model_comparison_all_256": {
                    "models_equivalent_after_u8_truncation": True,
                },
                "static_preimage_status": {
                    "complete_printable_preimage": False,
                },
                "candidate": None,
                "known_candidate": "",
            },
        )
        _write_json(
            ida_path,
            {
                "schema_version": 1,
                "sample_id": "cpp1_2f6fcb63",
                "executed_sample": False,
                "static_only": True,
                "runtime_validated": False,
                "bounded_instruction_evidence": {
                    "target_xref_context": {
                        "target_name": "byte_429A30",
                        "target_address": "0x00429A30",
                        "xrefs": [
                            {
                                "from": "0x004010E7",
                                "type": "data",
                                "in_main": False,
                                "basic_block": None,
                                "window": [],
                            },
                            {
                                "from": "0x004012BE",
                                "type": "data",
                                "in_main": True,
                                "basic_block": 9,
                                "window": [
                                    {"address": "0x004012BE", "mnemonic": "movsx"},
                                    {"address": "0x004012C5", "mnemonic": "cmp"},
                                ],
                            },
                        ],
                    }
                },
                "candidate": None,
                "known_candidate": "",
            },
        )
        return {
            "artifact_index": artifact_index_path,
            "target": target_path,
            "transform": transform_path,
            "signed": signed_path,
            "ida": ida_path,
            "out": out_path,
            "binary": binary,
        }

    def test_target_provenance_recheck_confirms_raw_target_and_no_candidate(self, tmp_path: Path):
        paths = self._write_sources(tmp_path)

        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._resolve_binary_path",
            return_value=paths["binary"],
        ):
            result = run_target_provenance_recheck(
                target_bytes_path=paths["target"],
                transform_recheck_path=paths["transform"],
                signed_transform_recheck_path=paths["signed"],
                ida_control_flow_path=paths["ida"],
                artifact_index_path=paths["artifact_index"],
                out_path=paths["out"],
            )

        assert result["analysis_mode"] == "target_byte_provenance_recheck"
        assert result["mainline"] == "reverse_solving"
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
        assert result["ida_used_this_round"] is False
        assert result["used_existing_ida_interface"] is True
        assert result["new_ida_runner_created"] is False
        assert result["section_name"] == ".data"
        assert result["current_target_matches_raw_data"] is True
        assert result["confirmed_target_bytes_hex"] == "d596c4f60745577776e5f64847f74817"
        assert result["provenance_verdict"] in {
            "CONFIRMED_NO_PRINTABLE_PREIMAGE",
            "ALTERNATIVE_PRINTABLE_SPAN_FOUND_NEEDS_REVIEW",
        }
        assert result["printable_preimage_feasibility_by_span"]["span_count"] > 0
        assert result["printable_preimage_feasibility_by_span"]["current_span"]["relative_start"] == 0
        assert result["printable_preimage_feasibility_by_span"]["current_span"]["length"] == 16
        assert all(
            -0x40 <= span["relative_start"] <= 0x40
            and span["length"] in {16, 18}
            for span in result["nearby_candidate_spans"]
        )
        assert result["signed_compare_notes"]["does_not_imply_target_extraction_error"] is True
        assert result["compare_xrefs"][0]["from"] == "0x004012BE"
        assert paths["out"].exists()

        index = json.loads(paths["artifact_index"].read_text(encoding="utf-8"))
        entry = index["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_target_provenance_recheck"]
        assert entry["freshness"] == "current"
        assert entry["source_run"] == "round_20260605_cpp1_target_byte_provenance_recheck_v1"
        assert entry["sample_id"] == "cpp1_2f6fcb63"

    def test_target_provenance_recheck_blocks_when_source_not_current(self, tmp_path: Path):
        paths = self._write_sources(tmp_path)
        index = json.loads(paths["artifact_index"].read_text(encoding="utf-8"))
        index["latest_artifacts_v2"]["local_reverse_cpp1_2f6fcb63_target_bytes"]["freshness"] = "stale"
        paths["artifact_index"].write_text(json.dumps(index), encoding="utf-8")

        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._resolve_binary_path",
            return_value=paths["binary"],
        ), pytest.raises(ValueError, match="not current"):
            run_target_provenance_recheck(
                target_bytes_path=paths["target"],
                transform_recheck_path=paths["transform"],
                signed_transform_recheck_path=paths["signed"],
                ida_control_flow_path=paths["ida"],
                artifact_index_path=paths["artifact_index"],
                out_path=paths["out"],
            )
        assert not paths["out"].exists()

    def test_binary_not_found_blocked(self, tmp_path: Path):
        """When binary cannot be resolved, returns BLOCKED/BINARY_NOT_FOUND."""
        triage_path, inv_path = self._make_triage_inv(
            tmp_path, "cpp1_abc", "samples/nonexistent.exe"
        )
        out_path = tmp_path / "out.json"

        fake_root = tmp_path / "fake_root"
        fake_root.mkdir()
        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=fake_root,
        ):
            result = run_target_byte_extraction(
                sample_id="cpp1_abc",
                triage_path=triage_path,
                inventory_path=inv_path,
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

    def test_ida_success_with_bytes_full_artifact(self, tmp_path: Path):
        """When IDA succeeds with target bytes, artifact is fully populated."""
        triage_path, inv_path = self._make_triage_inv(
            tmp_path, "cpp1_ok", "samples/ok.exe"
        )
        out_path = tmp_path / "out.json"

        fake_root = tmp_path / "fake_root"
        samples_dir = fake_root / "samples"
        samples_dir.mkdir(parents=True)
        (samples_dir / "ok.exe").write_bytes(b"MZ")

        ida_mock_result = {
            "tool_status": "success",
            "blocked_reason": "",
            "source_tool": "IDA",
            "exit_code": 0,
            "target_symbol": "byte_429A30",
            "target_address": "0x429A30",
            "target_length": 16,
            "target_bytes_hex": "deadbeef" * 4,
            "target_bytes": [0xDE, 0xAD, 0xBE, 0xEF] * 4,
            "main_function": "_main_0",
            "main_function_address": "0x401000",
            "main_pseudocode": "v5 = (Str[i] & 3) | (16 * (Str[i] & 0x0C)) | ((Str[i] & 0xF0) >> 2);",
            "compare_expression": "Destination[i] == byte_429A30[i]",
            "loop_context": "for (i = 0; i < 16; ++i)",
        }

        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=fake_root,
        ), patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._run_ida_extraction",
            return_value=ida_mock_result,
        ), patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._now_iso",
            return_value="2026-06-05T00:00:00Z",
        ):
            result = run_target_byte_extraction(
                sample_id="cpp1_ok",
                triage_path=triage_path,
                inventory_path=inv_path,
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

        # Target bytes populated
        assert result["target_bytes_hex"] == "deadbeef" * 4
        assert result["target_bytes"] == [0xDE, 0xAD, 0xBE, 0xEF] * 4
        assert result["target_length"] == 16
        assert result["target_symbol"] == "byte_429A30"
        assert result["target_address"] == "0x429A30"

        # Forward transform has formula
        forward = result["forward_transform"]
        assert forward["formula_c"] != ""
        assert "& 3" in forward["formula_c"]

        # Metadata
        assert result["sample_id"] == "cpp1_ok"
        assert result["relative_path"] == "samples/ok.exe"
        assert result["generated_at"] == "2026-06-05T00:00:00Z"

        # recommended_next_action mentions inverse transform
        assert "inverse-transform" in result["recommended_next_action"].lower() or "handoff" in result["recommended_next_action"].lower()

        # Output file was written
        assert out_path.exists()

    def test_ida_success_but_no_bytes_blocked(self, tmp_path: Path):
        """When IDA succeeds but no target bytes found, returns BLOCKED/TARGET_BYTES_NOT_FOUND."""
        triage_path, inv_path = self._make_triage_inv(
            tmp_path, "cpp1_nobytes", "samples/nobytes.exe"
        )
        out_path = tmp_path / "out.json"

        fake_root = tmp_path / "fake_root"
        samples_dir = fake_root / "samples"
        samples_dir.mkdir(parents=True)
        (samples_dir / "nobytes.exe").write_bytes(b"MZ")

        ida_mock_result = {
            "tool_status": "success",
            "blocked_reason": "",
            "source_tool": "IDA",
            "exit_code": 0,
            "target_symbol": "byte_429A30",
            "target_address": "",
            "target_length": 0,
            "target_bytes_hex": "",
            "target_bytes": [],
            "main_function": "_main_0",
            "main_function_address": "",
            "main_pseudocode": "",
            "compare_expression": "",
            "loop_context": "",
        }

        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=fake_root,
        ), patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._run_ida_extraction",
            return_value=ida_mock_result,
        ):
            result = run_target_byte_extraction(
                sample_id="cpp1_nobytes",
                triage_path=triage_path,
                inventory_path=inv_path,
                out_path=out_path,
            )

        assert result["tool_status"] == "blocked"
        # Zero bytes is also "incomplete" (0 < 16), so INCOMPLETE_TARGET_BYTES is the correct reason
        assert result["blocked_reason"] == "INCOMPLETE_TARGET_BYTES"
        assert result["expected_target_length"] == 16
        assert result["target_length"] == 0
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
        assert out_path.exists()

    def test_ida_incomplete_bytes_blocked(self, tmp_path: Path):
        """When IDA returns fewer bytes than expected (e.g. 1 < 16), returns BLOCKED/INCOMPLETE_TARGET_BYTES."""
        triage_path, inv_path = self._make_triage_inv(
            tmp_path, "cpp1_incomplete", "samples/incomplete.exe"
        )
        out_path = tmp_path / "out.json"

        fake_root = tmp_path / "fake_root"
        samples_dir = fake_root / "samples"
        samples_dir.mkdir(parents=True)
        (samples_dir / "incomplete.exe").write_bytes(b"MZ")

        ida_mock_result = {
            "tool_status": "success",
            "blocked_reason": "",
            "source_tool": "IDA",
            "exit_code": 0,
            "target_symbol": "byte_429A30",
            "target_address": "0x00429A30",
            "target_length": 1,
            "target_bytes_hex": "d5",
            "target_bytes": [0xD5],
            "main_function": "_main_0",
            "main_function_address": "0x401000",
            "main_pseudocode": "v5 = (Str[i] & 3) | (16 * (Str[i] & 0x0C)) | ((Str[i] & 0xF0) >> 2);",
            "compare_expression": "Destination[i] == byte_429A30[i]",
            "loop_context": "for (i = 0; i < 16; ++i)",
        }

        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=fake_root,
        ), patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._run_ida_extraction",
            return_value=ida_mock_result,
        ):
            result = run_target_byte_extraction(
                sample_id="cpp1_incomplete",
                triage_path=triage_path,
                inventory_path=inv_path,
                out_path=out_path,
            )

        assert result["tool_status"] == "blocked"
        assert result["blocked_reason"] == "INCOMPLETE_TARGET_BYTES"
        assert result["expected_target_length"] == 16
        assert result["target_length"] == 1
        assert result["target_bytes_hex"] == "d5"
        assert result["target_bytes"] == [0xD5]
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
        assert out_path.exists()

    def test_ida_blocked_propagates(self, tmp_path: Path):
        """When IDA returns blocked status, artifact is blocked with that reason."""
        triage_path, inv_path = self._make_triage_inv(
            tmp_path, "cpp1_blocked", "samples/blocked.exe"
        )
        out_path = tmp_path / "out.json"

        fake_root = tmp_path / "fake_root"
        samples_dir = fake_root / "samples"
        samples_dir.mkdir(parents=True)
        (samples_dir / "blocked.exe").write_bytes(b"MZ")

        ida_mock_result = {
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_UNAVAILABLE: IDA executable not found",
            "source_tool": "IDA",
        }

        with patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._find_sample_root",
            return_value=fake_root,
        ), patch(
            "reverse_agent.local_reverse_cpp1_target_byte_extract._run_ida_extraction",
            return_value=ida_mock_result,
        ):
            result = run_target_byte_extraction(
                sample_id="cpp1_blocked",
                triage_path=triage_path,
                inventory_path=inv_path,
                out_path=out_path,
            )

        assert result["tool_status"] == "blocked"
        assert "STATIC_TOOL_UNAVAILABLE" in result["blocked_reason"]
        assert result["source_tool"] == "IDA"
        assert result["static_only"] is True
        assert result["executed_sample"] is False
        assert result["runtime_validated"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
