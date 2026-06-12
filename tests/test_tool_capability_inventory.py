"""Tests for tool_capability_inventory module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from reverse_agent.tool_capability_inventory import (
    _build_gap_report,
    _build_inventory,
    _grep_keyword,
    _now_iso,
    _source_files,
    build,
)


class TestSourceFiles:
    def test_returns_python_files(self):
        files = _source_files("*.py")
        assert len(files) > 0
        for f in files:
            assert f.suffix == ".py"

    def test_includes_reverse_agent_dir(self):
        files = _source_files("*.py")
        paths = [str(f) for f in files]
        assert any("reverse_agent" in p.replace("\\", "/") for p in paths)

    def test_includes_tests_dir(self):
        files = _source_files("*.py")
        paths = [str(f) for f in files]
        assert any("tests" in p.replace("\\", "/") for p in paths)


class TestGrepKeyword:
    def test_finds_ida(self):
        files = _source_files("*.py")
        hits = _grep_keyword(files, "ida")
        assert len(hits) > 0
        paths = [h["path"] for h in hits]
        assert any("tool_runners" in p.replace("\\", "/") for p in paths)

    def test_finds_structured_evidence(self):
        files = _source_files("*.py")
        hits = _grep_keyword(files, "StructuredEvidence")
        assert len(hits) > 0
        paths = [h["path"] for h in hits]
        assert any("evidence.py" in p.replace("\\", "/") for p in paths)

    def test_no_hits_for_nonsense(self):
        files = _source_files("*.py")
        # Exclude test file itself from search to avoid self-reference
        files = [f for f in files if "test_tool_capability_inventory" not in str(f)]
        hits = _grep_keyword(files, "zzzznonexistentkeywordzzzz")
        assert len(hits) == 0

    def test_hit_has_required_fields(self):
        files = _source_files("*.py")
        hits = _grep_keyword(files, "harness")
        assert len(hits) > 0
        for h in hits:
            assert "path" in h
            assert "match_count" in h
            assert "sample_lines" in h
            assert h["match_count"] > 0
            assert len(h["sample_lines"]) <= 5


class TestBuildInventory:
    def test_returns_valid_structure(self):
        inv = _build_inventory("test_decision", "test_round")
        assert inv["schema_version"] == 1
        assert inv["decision_id"] == "test_decision"
        assert inv["round_id"] == "test_round"
        assert "generated_at" in inv
        assert "capabilities" in inv
        assert "summary" in inv
        assert "scan_scope" in inv

    def test_covers_all_11_capabilities(self):
        inv = _build_inventory("test_decision", "test_round")
        assert len(inv["capabilities"]) == 11

    def test_capability_names(self):
        inv = _build_inventory("test_decision", "test_round")
        names = [c["capability_name"] for c in inv["capabilities"]]
        expected = [
            "IDA / IDAPython",
            "Ghidra",
            "OllyDbg / x64dbg / debugger",
            "strings / file / objdump / radare2",
            "solver templates",
            "symbolic / constraint solver (Z3 / angr)",
            "harness",
            "sample metadata",
            "artifact_index",
            "StructuredEvidence conversion",
            "GUI / CLI configuration",
        ]
        assert names == expected

    def test_each_capability_has_required_fields(self):
        inv = _build_inventory("test_decision", "test_round")
        required_fields = [
            "capability_name", "tool_family", "existing_entrypoints",
            "existing_tests", "artifact_outputs", "structured_evidence_mapping",
            "freshness_policy", "current_status", "do_not_duplicate",
            "safe_next_action",
        ]
        for cap in inv["capabilities"]:
            for field in required_fields:
                assert field in cap, f"Missing field '{field}' in capability '{cap['capability_name']}'"

    def test_current_status_valid(self):
        inv = _build_inventory("test_decision", "test_round")
        valid_statuses = {"implemented", "partial", "planned", "missing", "unknown"}
        for cap in inv["capabilities"]:
            assert cap["current_status"] in valid_statuses, \
                f"Invalid status '{cap['current_status']}' for '{cap['capability_name']}'"

    def test_summary_counts_match(self):
        inv = _build_inventory("test_decision", "test_round")
        s = inv["summary"]
        assert s["total_capabilities"] == len(inv["capabilities"])
        assert s["implemented"] + s["partial"] + s["planned"] + s["missing"] + s["unknown"] == s["total_capabilities"]

    def test_ida_is_implemented(self):
        inv = _build_inventory("test_decision", "test_round")
        ida = next(c for c in inv["capabilities"] if c["capability_name"] == "IDA / IDAPython")
        assert ida["current_status"] == "implemented"

    def test_ghidra_is_missing(self):
        inv = _build_inventory("test_decision", "test_round")
        ghidra = next(c for c in inv["capabilities"] if c["capability_name"] == "Ghidra")
        assert ghidra["current_status"] == "missing"

    def test_harness_is_implemented(self):
        inv = _build_inventory("test_decision", "test_round")
        harness = next(c for c in inv["capabilities"] if c["capability_name"] == "harness")
        assert harness["current_status"] == "implemented"

    def test_artifact_index_is_implemented(self):
        inv = _build_inventory("test_decision", "test_round")
        ai = next(c for c in inv["capabilities"] if c["capability_name"] == "artifact_index")
        assert ai["current_status"] == "implemented"

    def test_structured_evidence_is_implemented(self):
        inv = _build_inventory("test_decision", "test_round")
        se = next(c for c in inv["capabilities"] if c["capability_name"] == "StructuredEvidence conversion")
        assert se["current_status"] == "implemented"

    def test_scan_scope_has_file_count(self):
        inv = _build_inventory("test_decision", "test_round")
        assert inv["scan_scope"]["total_files_scanned"] > 0


class TestBuildGapReport:
    def test_returns_valid_structure(self):
        inv = _build_inventory("test_decision", "test_round")
        gap = _build_gap_report("test_decision", "test_round", inv)
        assert gap["schema_version"] == 1
        assert gap["decision_id"] == "test_decision"
        assert gap["round_id"] == "test_round"
        assert "evidence_usage_boundary" in gap
        assert "evidence_mappings" in gap
        assert "evidence_gaps" in gap
        assert "triage_prerequisites" in gap
        assert "summary" in gap

    def test_evidence_usage_boundary_has_four_levels(self):
        inv = _build_inventory("test_decision", "test_round")
        gap = _build_gap_report("test_decision", "test_round", inv)
        boundary = gap["evidence_usage_boundary"]
        assert "current" in boundary
        assert "stale" in boundary
        assert "missing" in boundary
        assert "unknown" in boundary

    def test_summary_counts_consistent(self):
        inv = _build_inventory("test_decision", "test_round")
        gap = _build_gap_report("test_decision", "test_round", inv)
        s = gap["summary"]
        assert s["total_capabilities_assessed"] == len(inv["capabilities"])
        assert s["total_gaps"] == len(gap["evidence_gaps"])

    def test_has_triage_prerequisites(self):
        inv = _build_inventory("test_decision", "test_round")
        gap = _build_gap_report("test_decision", "test_round", inv)
        assert len(gap["triage_prerequisites"]) > 0
        tp = gap["triage_prerequisites"][0]
        assert "action" in tp
        assert "minimum_requirements" in tp
        assert "adapter_schema_fields_needed" in tp
        assert "current_blockers" in tp

    def test_evidence_gaps_are_actionable(self):
        inv = _build_inventory("test_decision", "test_round")
        gap = _build_gap_report("test_decision", "test_round", inv)
        for g in gap["evidence_gaps"]:
            assert "capability" in g
            assert "gap_type" in g
            assert "description" in g
            assert "safe_next_action" in g


class TestBuild:
    def test_build_creates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            result = build(
                state_dir=state_dir,
                decision_id="test_decision",
                round_id="test_round",
            )
            inv_path = Path(result["inventory_path"])
            gap_path = Path(result["gap_report_path"])
            assert inv_path.exists()
            assert gap_path.exists()

    def test_build_output_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            result = build(
                state_dir=state_dir,
                decision_id="test_decision",
                round_id="test_round",
            )
            inv = json.loads(Path(result["inventory_path"]).read_text(encoding="utf-8"))
            gap = json.loads(Path(result["gap_report_path"]).read_text(encoding="utf-8"))
            assert inv["schema_version"] == 1
            assert gap["schema_version"] == 1
            assert inv["decision_id"] == "test_decision"
            assert gap["decision_id"] == "test_decision"

    def test_build_reads_decision_id_from_packet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            # Write a minimal decision_packet.md
            dp = state_dir / "decision_packet.md"
            dp.write_text(
                '```json decision_meta\n'
                '{"decision_id": "dp_test_id", "round_id": "dp_test_round"}\n'
                '```\n',
                encoding="utf-8",
            )
            result = build(state_dir=state_dir)
            inv = json.loads(Path(result["inventory_path"]).read_text(encoding="utf-8"))
            assert inv["decision_id"] == "dp_test_id"
            assert inv["round_id"] == "dp_test_round"


class TestNowIso:
    def test_returns_string(self):
        result = _now_iso()
        assert isinstance(result, str)
        assert "T" in result
        assert "Z" in result
