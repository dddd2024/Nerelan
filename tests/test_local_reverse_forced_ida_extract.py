"""Tests for reverse_agent.local_reverse_forced_ida_extract.

These tests mock the IDA subprocess to avoid actually running IDA.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reverse_agent.local_reverse_forced_ida_extract import (
    _run_forced_ida_extraction,
    run_forced_extraction,
)


def _make_handoff() -> dict:
    return {
        "schema_version": 1,
        "status": "PARTIAL",
        "validated_candidates": [
            {
                "sample_id": "bcbd9979db015bfd",
                "candidate": "hookapi",
                "validation_status": "validated",
            }
        ],
        "unresolved_targets": [
            {
                "sample_id": "18019fca52b389fe",
                "relative_path": "逆向课程2024春01/sha_256.exe",
                "blocked_reason": "NO_BOUNDED_HASH_PREIMAGE_DOMAIN",
                "constraint_status": "blocked",
            },
            {
                "sample_id": "4c69f173f2bd0211",
                "relative_path": "逆向课程2022春02/CPP2.exe",
                "blocked_reason": "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005",
                "constraint_status": "blocked",
            },
        ],
    }


def _make_artifact_index() -> dict:
    return {
        "latest_artifacts_v2": {
            "local_reverse_ida_evidence_18019fca52b389fe": {
                "kind": "local_reverse_ida_evidence_18019fca52b389fe",
                "path": "solve_reports\\tool_artifacts\\local_reverse_ida_evidence_integration_v1\\18019fca52b389fe\\sha_256_ida_evidence.json",
                "freshness": "current",
                "sample_id": "18019fca52b389fe",
            },
            "local_reverse_ida_evidence_4c69f173f2bd0211": {
                "kind": "local_reverse_ida_evidence_4c69f173f2bd0211",
                "path": "solve_reports\\tool_artifacts\\local_reverse_ida_evidence_integration_v1\\4c69f173f2bd0211\\CPP2_ida_evidence.json",
                "freshness": "current",
                "sample_id": "4c69f173f2bd0211",
            },
        }
    }


def _make_policy() -> dict:
    return {"root": "E:\\reverse"}


def _make_forced_extract_json(thunk: bool = True, has_real_pseudocode: bool = True) -> dict:
    if thunk:
        return {
            "schema_version": 1,
            "hexrays_available": True,
            "function_count": 1,
            "extracted_count": 1,
            "functions": [
                {
                    "function_name": "sub_401005",
                    "resolved": True,
                    "entry_ea": "0x401005",
                    "pseudocode": "int __cdecl sub_401005(char *Buffer, void *a2, size_t a3)\n{\n  return sub_401B20(Buffer, a2, a3);\n}\n",
                    "disassembly": ["jmp     sub_401B20"],
                    "constants": [],
                    "callgraph": [
                        {"caller_ea": "0x401005", "callee_ea": "0x401b20", "callee_name": "sub_401B20"}
                    ],
                    "string_refs": [],
                    "error": "",
                }
            ],
        }
    return {
        "schema_version": 1,
        "hexrays_available": True,
        "function_count": 1,
        "extracted_count": 1,
        "functions": [
            {
                "function_name": "sub_401005",
                "resolved": True,
                "entry_ea": "0x401005",
                "pseudocode": "void sub_401005(char *out, int in, int len) { /* hash */ }" if has_real_pseudocode else "",
                "disassembly": ["push ebp", "mov ebp, esp"],
                "constants": [64, 256],
                "callgraph": [],
                "string_refs": [],
                "error": "",
            }
        ],
    }


def _make_thunk_extract_json() -> dict:
    return {
        "schema_version": 1,
        "hexrays_available": True,
        "function_count": 1,
        "extracted_count": 1,
        "functions": [
            {
                "function_name": "sub_401B20",
                "resolved": True,
                "entry_ea": "0x401b20",
                "pseudocode": 'int __cdecl sub_401B20(char *Buffer, void *Src, size_t Size)\n{\n  ...\n  sprintf(Buffer, "%08x%08x%08x%08x%08x%08x%08x%08x", ...);\n  ...\n}\n',
                "disassembly": ["push ebp", "mov ebp, esp"],
                "constants": [64, 8],
                "callgraph": [
                    {"caller_ea": "0x401b20", "callee_ea": "0x40100a", "callee_name": "sub_40100A"}
                ],
                "string_refs": [
                    {"ea": "0x428150", "string": "%08x%08x%08x%08x%08x%08x%08x%08x", "ref_ea": "0x401c07"}
                ],
                "error": "",
            }
        ],
    }


class TestRunForcedIdaExtraction:
    @patch("reverse_agent.local_reverse_forced_ida_extract._resolve_ida_executable")
    @patch("subprocess.run")
    def test_ida_not_found(self, mock_run, mock_resolve):
        mock_resolve.return_value = ""
        artifact = _run_forced_ida_extraction(
            binary_path=Path("test.exe"),
            script_path=Path("script.py"),
            output_path=Path("out.json"),
            function_names=["sub_401005"],
        )
        assert artifact.success is False
        assert "not found" in artifact.error.lower()

    @patch("reverse_agent.local_reverse_forced_ida_extract._resolve_ida_executable")
    @patch("subprocess.run")
    def test_successful_extraction(self, mock_run, mock_resolve, tmp_path: Path):
        mock_resolve.return_value = "ida.exe"
        output_path = tmp_path / "out.json"
        output_path.write_text(json.dumps(_make_forced_extract_json(thunk=False)))
        (tmp_path / "script.py").write_text("# mock script")
        (tmp_path / "test.exe").write_text("mock binary")

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        artifact = _run_forced_ida_extraction(
            binary_path=tmp_path / "test.exe",
            script_path=tmp_path / "script.py",
            output_path=output_path,
            function_names=["sub_401005"],
        )
        assert artifact.success is True
        assert "1/1" in artifact.summary


class TestRunForcedExtraction:
    @patch("reverse_agent.local_reverse_forced_ida_extract._run_forced_ida_extraction")
    def test_only_sha256_and_cpp2_selected(self, mock_run, tmp_path: Path):
        """Only sha_256 and CPP2 are selected, not Cpp1."""
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        policy_path = tmp_path / "policy.json"
        out_path = tmp_path / "out.json"

        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index()))
        policy_path.write_text(json.dumps(_make_policy()))

        def mock_run_impl(*, binary_path, script_path, output_path, function_names, timeout_seconds):
            artifact = MagicMock()
            artifact.success = True
            artifact.summary = "IDA forced extraction: 1/1 functions decompiled"
            artifact.error = ""
            artifact.evidence = []
            # Write output
            if "sub_401B20" in function_names:
                output_path.write_text(json.dumps(_make_thunk_extract_json()))
            else:
                output_path.write_text(json.dumps(_make_forced_extract_json(thunk=True)))
            return artifact

        mock_run.side_effect = mock_run_impl

        result = run_forced_extraction(ai_path, handoff_path, out_path, policy_path)

        assert result["target_count"] == 2
        assert len(result["targets"]) == 2
        ids = {t["sample_id"] for t in result["targets"]}
        assert ids == {"18019fca52b389fe", "4c69f173f2bd0211"}

    @patch("reverse_agent.local_reverse_forced_ida_extract._run_forced_ida_extraction")
    def test_thunk_detection(self, mock_run, tmp_path: Path):
        """sub_401005 thunk should be detected and sub_401B20 extracted."""
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        policy_path = tmp_path / "policy.json"
        out_path = tmp_path / "out.json"

        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index()))
        policy_path.write_text(json.dumps(_make_policy()))

        def mock_run_impl(*, binary_path, script_path, output_path, function_names, timeout_seconds):
            artifact = MagicMock()
            artifact.success = True
            artifact.summary = "IDA forced extraction: 1/1 functions decompiled"
            artifact.error = ""
            artifact.evidence = []
            if "sub_401B20" in function_names:
                output_path.write_text(json.dumps(_make_thunk_extract_json()))
            else:
                output_path.write_text(json.dumps(_make_forced_extract_json(thunk=True)))
            return artifact

        mock_run.side_effect = mock_run_impl

        result = run_forced_extraction(ai_path, handoff_path, out_path, policy_path)

        for t in result["targets"]:
            assert t["sub_401005_is_thunk"] is True
            assert t["sub_401005_thunk_target"] == "sub_401B20"
            assert "SHA-256" in t["transform_inferred"]
            assert t["blocker_resolved"] is True

    @patch("reverse_agent.local_reverse_forced_ida_extract._run_forced_ida_extraction")
    def test_sha256_transform_inferred(self, mock_run, tmp_path: Path):
        """SHA-256 transform should be inferred from 8x %08x sprintf."""
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        policy_path = tmp_path / "policy.json"
        out_path = tmp_path / "out.json"

        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index()))
        policy_path.write_text(json.dumps(_make_policy()))

        def mock_run_impl(*, binary_path, script_path, output_path, function_names, timeout_seconds):
            artifact = MagicMock()
            artifact.success = True
            artifact.summary = "IDA forced extraction: 1/1 functions decompiled"
            artifact.error = ""
            artifact.evidence = []
            if "sub_401B20" in function_names:
                output_path.write_text(json.dumps(_make_thunk_extract_json()))
            else:
                output_path.write_text(json.dumps(_make_forced_extract_json(thunk=True)))
            return artifact

        mock_run.side_effect = mock_run_impl

        result = run_forced_extraction(ai_path, handoff_path, out_path, policy_path)

        for t in result["targets"]:
            assert "SHA-256" in t["transform_inferred"]

    @patch("reverse_agent.local_reverse_forced_ida_extract._run_forced_ida_extraction")
    def test_blocker_resolved_when_transform_recovered(self, mock_run, tmp_path: Path):
        """blocker_resolved should be True when real transform is recovered."""
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        policy_path = tmp_path / "policy.json"
        out_path = tmp_path / "out.json"

        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index()))
        policy_path.write_text(json.dumps(_make_policy()))

        def mock_run_impl(*, binary_path, script_path, output_path, function_names, timeout_seconds):
            artifact = MagicMock()
            artifact.success = True
            artifact.summary = "IDA forced extraction: 1/1 functions decompiled"
            artifact.error = ""
            artifact.evidence = []
            if "sub_401B20" in function_names:
                output_path.write_text(json.dumps(_make_thunk_extract_json()))
            else:
                output_path.write_text(json.dumps(_make_forced_extract_json(thunk=True)))
            return artifact

        mock_run.side_effect = mock_run_impl

        result = run_forced_extraction(ai_path, handoff_path, out_path, policy_path)

        for t in result["targets"]:
            assert t["blocker_resolved"] is True
            assert t["extraction_status"] == "recovered"

    @patch("reverse_agent.local_reverse_forced_ida_extract._run_forced_ida_extraction")
    def test_hookapi_not_overridden(self, mock_run, tmp_path: Path):
        """hookapi in handoff must not be overridden or re-validated."""
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        policy_path = tmp_path / "policy.json"
        out_path = tmp_path / "out.json"

        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index()))
        policy_path.write_text(json.dumps(_make_policy()))

        def mock_run_impl(*, binary_path, script_path, output_path, function_names, timeout_seconds):
            artifact = MagicMock()
            artifact.success = True
            artifact.summary = "IDA forced extraction: 1/1 functions decompiled"
            artifact.error = ""
            artifact.evidence = []
            if "sub_401B20" in function_names:
                output_path.write_text(json.dumps(_make_thunk_extract_json()))
            else:
                output_path.write_text(json.dumps(_make_forced_extract_json(thunk=True)))
            return artifact

        mock_run.side_effect = mock_run_impl

        result = run_forced_extraction(ai_path, handoff_path, out_path, policy_path)

        ids = {t["sample_id"] for t in result["targets"]}
        assert "bcbd9979db015bfd" not in ids
        for t in result["targets"]:
            assert t.get("validated_candidate", "") != "hookapi"

    @patch("reverse_agent.local_reverse_forced_ida_extract._run_forced_ida_extraction")
    def test_output_target_count_2(self, mock_run, tmp_path: Path):
        """Output target_count must be 2."""
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        policy_path = tmp_path / "policy.json"
        out_path = tmp_path / "out.json"

        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index()))
        policy_path.write_text(json.dumps(_make_policy()))

        def mock_run_impl(*, binary_path, script_path, output_path, function_names, timeout_seconds):
            artifact = MagicMock()
            artifact.success = True
            artifact.summary = "IDA forced extraction: 1/1 functions decompiled"
            artifact.error = ""
            artifact.evidence = []
            if "sub_401B20" in function_names:
                output_path.write_text(json.dumps(_make_thunk_extract_json()))
            else:
                output_path.write_text(json.dumps(_make_forced_extract_json(thunk=True)))
            return artifact

        mock_run.side_effect = mock_run_impl

        result = run_forced_extraction(ai_path, handoff_path, out_path, policy_path)

        assert result["target_count"] == 2

    @patch("reverse_agent.local_reverse_forced_ida_extract._run_forced_ida_extraction")
    def test_ida_failure_blocked(self, mock_run, tmp_path: Path):
        """IDA failure should result in blocked status."""
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        policy_path = tmp_path / "policy.json"
        out_path = tmp_path / "out.json"

        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index()))
        policy_path.write_text(json.dumps(_make_policy()))

        def mock_run_impl(*, binary_path, script_path, output_path, function_names, timeout_seconds):
            artifact = MagicMock()
            artifact.success = False
            artifact.error = "IDA timeout"
            artifact.summary = "IDA forced extraction timed out"
            artifact.evidence = []
            return artifact

        mock_run.side_effect = mock_run_impl

        result = run_forced_extraction(ai_path, handoff_path, out_path, policy_path)

        for t in result["targets"]:
            assert t["extraction_status"] == "blocked"
            assert t["blocker_resolved"] is False
            assert "timeout" in t["next_action"].lower() or "failed" in t["next_action"].lower()
