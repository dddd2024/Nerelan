"""Tool capability inventory builder.

Scans the repository source code and project_state to produce a structured
tool capability inventory and a StructuredEvidence gap report.

Does NOT run external reverse engineering tools or sample binaries.
Only reads repository source files, tests, and project_state JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REVERSE_AGENT_DIR = REPO_ROOT / "reverse_agent"
TESTS_DIR = REPO_ROOT / "tests"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _source_files(pattern: str = "*.py") -> list[Path]:
    """Return all Python source files under reverse_agent/ and tests/."""
    results: list[Path] = []
    for base in (REVERSE_AGENT_DIR, TESTS_DIR):
        if base.is_dir():
            results.extend(sorted(base.rglob(pattern)))
    return results


def _grep_keyword(files: list[Path], keyword: str) -> list[dict[str, Any]]:
    """Return files and line counts matching a keyword (case-insensitive)."""
    hits: list[dict[str, Any]] = []
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = [(i + 1, line.rstrip()) for i, line in enumerate(text.splitlines()) if pattern.search(line)]
        if lines:
            hits.append({
                "path": str(f.relative_to(REPO_ROOT)),
                "match_count": len(lines),
                "sample_lines": lines[:5],
            })
    return hits


def _build_inventory(
    decision_id: str,
    round_id: str,
) -> dict[str, Any]:
    """Build the tool capability inventory by scanning source code."""
    files = _source_files("*.py")

    capabilities = [
        {
            "capability_name": "IDA / IDAPython",
            "tool_family": "disassembler_decompiler",
            "existing_entrypoints": _grep_keyword(files, "ida"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "ida"),
            "artifact_outputs": [
                "IDA JSON evidence (decompiled pseudocode, function list, string xrefs)",
                "IDA-guided solver artifacts",
                "Static triage artifacts from IDA evidence",
            ],
            "structured_evidence_mapping": {
                "status": "partial",
                "details": "tool_runners.py parses IDA JSON output into ToolRunArtifact with structured_evidence list; evidence.py provides StructuredEvidence dataclass and factory functions; local_reverse_single_sample_static_triage.py consumes IDA JSON for triage",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "artifact_index.json tracks freshness per artifact; stale/missing tags prevent reuse as current evidence",
            },
            "current_status": "implemented",
            "do_not_duplicate": "IDA runner in tool_runners.py, IDA scripts in ida_scripts/, IDA evidence parsing, IDA-guided solver, forced IDA extract, IDA summary module",
            "safe_next_action": "extend IDA script library for new sample profiles; add IDA evidence schema validation",
        },
        {
            "capability_name": "Ghidra",
            "tool_family": "disassembler_decompiler",
            "existing_entrypoints": _grep_keyword(files, "ghidra"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "ghidra"),
            "artifact_outputs": [],
            "structured_evidence_mapping": {
                "status": "missing",
                "details": "no Ghidra headless analyzer, script runner, or evidence adapter exists in the codebase",
            },
            "freshness_policy": {
                "status": "missing",
                "details": "no Ghidra artifacts to track freshness for",
            },
            "current_status": "missing",
            "do_not_duplicate": "",
            "safe_next_action": "add Ghidra headless analyzer runner and evidence adapter if Ghidra becomes available; reuse StructuredEvidence from evidence.py",
        },
        {
            "capability_name": "OllyDbg / x64dbg / debugger",
            "tool_family": "dynamic_debugger",
            "existing_entrypoints": _grep_keyword(files, "ollydbg") + _grep_keyword(files, "x64dbg") + _grep_keyword(files, "debugger"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "ollydbg") + _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "x64dbg"),
            "artifact_outputs": [
                "OllyDbg evidence JSON (compare probes, material hooks, breakpoint audits)",
                "Runtime compare evidence",
                "Post-handoff branch outcome audits",
            ],
            "structured_evidence_mapping": {
                "status": "partial",
                "details": "tool_runners.py parses OllyDbg JSON output into ToolRunArtifact with structured_evidence; olly_scripts/ contains 28 audit/probe scripts; ollydbg_preflight.py provides non-invasive configuration check",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "artifact_index.json tracks freshness per artifact; stale/missing tags prevent reuse as current evidence",
            },
            "current_status": "implemented",
            "do_not_duplicate": "OllyDbg runner in tool_runners.py, OllyDbg preflight in ollydbg_preflight.py, 28 OllyDbg scripts in olly_scripts/, GUI debugger config in gui.py",
            "safe_next_action": "add x64dbg-specific script adapter if x64dbg becomes primary debugger; extend probe library for new sample types",
        },
        {
            "capability_name": "strings / file / objdump / radare2",
            "tool_family": "static_analysis_tools",
            "existing_entrypoints": (
                _grep_keyword(files, "strings")
                + _grep_keyword(files, "objdump")
                + _grep_keyword(files, "radare2")
            ),
            "existing_tests": (
                _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "strings")
                + _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "objdump")
            ),
            "artifact_outputs": [
                "ASCII/UTF-16LE string extraction (pure Python in static_feature_extractor.py)",
                "Keyword hit detection",
                "Base64-like string detection",
            ],
            "structured_evidence_mapping": {
                "status": "partial",
                "details": "static_feature_extractor.py provides pure Python string extraction (no external tool dependency); no StructuredEvidence factory for generic string extraction results; no file/objdump/radare2 integration",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "static features are computed on-demand; no artifact freshness tracking needed for pure Python extraction",
            },
            "current_status": "partial",
            "do_not_duplicate": "pure Python string extraction in static_feature_extractor.py",
            "safe_next_action": "add StructuredEvidence factory for static string extraction results; add radare2/objdump runner if needed for new architectures",
        },
        {
            "capability_name": "solver templates",
            "tool_family": "solver",
            "existing_entrypoints": _grep_keyword(files, "sample_solver"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "sample_solver"),
            "artifact_outputs": [
                "Candidate lists from solver profiles",
                "Solver gap reports",
            ],
            "structured_evidence_mapping": {
                "status": "partial",
                "details": "sample_solver.py provides generic solver framework; local_reverse_solver_profiles.py provides profile dispatch; corpus_static_audit.py generates gap reports",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "solver results tracked via artifact_index.json",
            },
            "current_status": "implemented",
            "do_not_duplicate": "sample_solver.py, local_reverse_solver_profiles.py, local_reverse_string_solver.py, samplereverse_z3.py, advanced_solvers.py",
            "safe_next_action": "extend solver profiles for new sample categories; add solver result schema validation",
        },
        {
            "capability_name": "symbolic / constraint solver (Z3 / angr)",
            "tool_family": "symbolic_execution",
            "existing_entrypoints": _grep_keyword(files, "z3") + _grep_keyword(files, "angr") + _grep_keyword(files, "constraint"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "z3") + _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "constraint"),
            "artifact_outputs": [
                "Z3 constraint solutions (samplereverse_z3.py)",
                "angr symbolic execution results (advanced_solvers.py)",
                "Constraint recovery artifacts (local_reverse_constraint_recovery.py)",
            ],
            "structured_evidence_mapping": {
                "status": "partial",
                "details": "samplereverse_z3.py uses z3 with graceful import fallback; advanced_solvers.py uses angr with graceful import fallback; local_reverse_constraint_recovery.py dispatches constraint recovery; no StructuredEvidence factory for Z3/angr results",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "constraint recovery results tracked via artifact_index.json",
            },
            "current_status": "implemented",
            "do_not_duplicate": "samplereverse_z3.py, advanced_solvers.py, local_reverse_constraint_recovery.py",
            "safe_next_action": "add StructuredEvidence factory for symbolic solver results; extend constraint recovery for new transform types",
        },
        {
            "capability_name": "harness",
            "tool_family": "test_orchestration",
            "existing_entrypoints": _grep_keyword(files, "harness"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "harness"),
            "artifact_outputs": [
                "Case result JSON (per-candidate validation)",
                "Artifact manifest JSON",
                "Run manifest JSON",
                "Summary JSON",
            ],
            "structured_evidence_mapping": {
                "status": "partial",
                "details": "harness.py orchestrates compare-aware campaigns; produces case results and artifact manifests; artifact_index.json registers harness outputs",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "harness run artifacts tracked via artifact_index.json with freshness tags",
            },
            "current_status": "implemented",
            "do_not_duplicate": "harness.py, harness CLI, harness compare/resume/resource-budget tests",
            "safe_next_action": "extend harness for new sample profiles; add structured evidence output per case",
        },
        {
            "capability_name": "sample metadata",
            "tool_family": "metadata_management",
            "existing_entrypoints": _grep_keyword(files, "metadata"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "metadata"),
            "artifact_outputs": [
                "Sample metadata JSON (sha256, category, tags, training_status)",
                "Inventory JSON (local_reverse_inventory.py)",
                "Training status JSON",
                "Training next queue JSON",
                "Capability review JSON",
            ],
            "structured_evidence_mapping": {
                "status": "partial",
                "details": "local_reverse_inventory.py builds inventory from LOCAL_REVERSE_ROOT; local_samples.py manages sample metadata; corpus_loader.py loads corpus cases; no StructuredEvidence factory for metadata",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "training status and inventory regenerated on demand; artifact_index.json tracks derived artifacts",
            },
            "current_status": "implemented",
            "do_not_duplicate": "local_reverse_inventory.py, local_samples.py, corpus_loader.py, corpus_classifier.py, local_reverse_training_status.py, local_reverse_training_review.py",
            "safe_next_action": "add StructuredEvidence factory for sample metadata; extend inventory for new sample sources",
        },
        {
            "capability_name": "artifact_index",
            "tool_family": "artifact_tracking",
            "existing_entrypoints": _grep_keyword(files, "artifact_index"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "artifact_index"),
            "artifact_outputs": [
                "artifact_index.json (central artifact registry with freshness, SHA256, size)",
            ],
            "structured_evidence_mapping": {
                "status": "implemented",
                "details": "project_state.py builds and manages artifact_index.json; project_gate.py reads artifact_index for gate checks; tracks freshness (current/stale/missing), SHA256, size_bytes, source_run",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "artifact_index.json IS the freshness policy implementation; stale/missing artifacts cannot be used as current evidence per project_gate.py rules",
            },
            "current_status": "implemented",
            "do_not_duplicate": "artifact_index build/parse in project_state.py, artifact_index reads in project_gate.py",
            "safe_next_action": "extend artifact_index schema for new artifact kinds; add automated freshness re-validation",
        },
        {
            "capability_name": "StructuredEvidence conversion",
            "tool_family": "evidence_standardization",
            "existing_entrypoints": _grep_keyword(files, "StructuredEvidence"),
            "existing_tests": _grep_keyword([f for f in files if f.is_relative_to(TESTS_DIR)], "StructuredEvidence"),
            "artifact_outputs": [
                "StructuredEvidence instances (kind, source_tool, summary, payload, confidence, derived_candidates)",
                "Evidence kind constants (CandidateEvidence, RuntimeCompareEvidence, StaticStringEvidence, etc.)",
            ],
            "structured_evidence_mapping": {
                "status": "implemented",
                "details": "evidence.py defines StructuredEvidence dataclass and factory functions for Base64/RC4/UTF16LE material evidence; tool_runners.py parses tool output into StructuredEvidence; strategies and pipeline consume StructuredEvidence",
            },
            "freshness_policy": {
                "status": "implemented",
                "details": "StructuredEvidence is an in-memory data structure; persistence is via artifact_index.json registered artifacts",
            },
            "current_status": "implemented",
            "do_not_duplicate": "evidence.py StructuredEvidence dataclass and factories, tool_runners.py parsing",
            "safe_next_action": "add StructuredEvidence factories for static string extraction, Z3/angr results, harness case results; add JSON serialization schema",
        },
        {
            "capability_name": "GUI / CLI configuration",
            "tool_family": "user_interface",
            "existing_entrypoints": _grep_keyword(files, "tkinter") + _grep_keyword(files, "argparse"),
            "existing_tests": [],
            "artifact_outputs": [
                "GUI configuration (gui.py - tkinter-based)",
                "CLI interfaces (harness.py, pipeline.py, project_state.py, project_gate.py, local_reverse_inventory.py, corpus_static_audit.py, etc.)",
            ],
            "structured_evidence_mapping": {
                "status": "missing",
                "details": "GUI/CLI are configuration and execution entry points; they do not produce StructuredEvidence directly",
            },
            "freshness_policy": {
                "status": "not_applicable",
                "details": "GUI/CLI are entry points, not artifacts",
            },
            "current_status": "implemented",
            "do_not_duplicate": "gui.py (tkinter), argparse CLIs in harness.py, pipeline.py, project_state.py, project_gate.py, local_reverse_inventory.py, corpus_static_audit.py, local_reverse_single_sample_static_triage.py, local_reverse_constraint_recovery.py, local_reverse_training_status.py, local_reverse_training_review.py",
            "safe_next_action": "consolidate CLI entry points under a unified command group if needed",
        },
    ]

    return {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "generated_at": _now_iso(),
        "scan_scope": {
            "directories": ["reverse_agent/", "tests/"],
            "file_pattern": "*.py",
            "total_files_scanned": len(files),
        },
        "capabilities": capabilities,
        "summary": {
            "total_capabilities": len(capabilities),
            "implemented": sum(1 for c in capabilities if c["current_status"] == "implemented"),
            "partial": sum(1 for c in capabilities if c["current_status"] == "partial"),
            "planned": sum(1 for c in capabilities if c["current_status"] == "planned"),
            "missing": sum(1 for c in capabilities if c["current_status"] == "missing"),
            "unknown": sum(1 for c in capabilities if c["current_status"] == "unknown"),
        },
    }


def _build_gap_report(
    decision_id: str,
    round_id: str,
    inventory: dict[str, Any],
) -> dict[str, Any]:
    """Build the StructuredEvidence gap report based on the inventory."""
    evidence_gaps: list[dict[str, Any]] = []
    evidence_mappings: list[dict[str, Any]] = []
    triage_prerequisites: list[dict[str, Any]] = []

    for cap in inventory["capabilities"]:
        name = cap["capability_name"]
        se = cap["structured_evidence_mapping"]
        status = cap["current_status"]

        if se["status"] == "implemented":
            evidence_mappings.append({
                "capability": name,
                "tool_output_registrable_in_artifact_index": True,
                "structured_evidence_available": True,
                "details": se["details"],
            })
        elif se["status"] == "partial":
            evidence_mappings.append({
                "capability": name,
                "tool_output_registrable_in_artifact_index": True,
                "structured_evidence_available": False,
                "gap_description": f"{name} tool output can be registered in artifact_index but lacks full StructuredEvidence mapping",
                "details": se["details"],
            })
            evidence_gaps.append({
                "capability": name,
                "gap_type": "missing_structured_evidence_factory",
                "description": f"{name} produces tool output that can be registered in artifact_index but does not have a StructuredEvidence factory for standardized evidence exchange",
                "safe_next_action": f"add StructuredEvidence factory in evidence.py for {name} output",
            })
        elif se["status"] == "missing":
            if status == "missing":
                evidence_mappings.append({
                    "capability": name,
                    "tool_output_registrable_in_artifact_index": False,
                    "structured_evidence_available": False,
                    "gap_description": f"{name} has no tool integration; no output to register or map",
                    "details": se["details"],
                })
            else:
                evidence_gaps.append({
                    "capability": name,
                    "gap_type": "missing_structured_evidence_factory",
                    "description": f"{name} has tool integration but no StructuredEvidence mapping",
                    "safe_next_action": f"add StructuredEvidence factory in evidence.py for {name} output",
                })

    # Triage prerequisites for primary_queue bounded_static_triage
    triage_prerequisites.append({
        "action": "bounded_static_triage",
        "minimum_requirements": [
            "IDA executable configured and reachable (tool_runners.py IDA runner)",
            "IDA script path set (ida_scripts/collect_evidence.py or equivalent)",
            "LOCAL_REVERSE_ROOT environment variable pointing to sample directory",
            "local_reverse_inventory.json up to date (run local_reverse_inventory.py)",
            "local_reverse_training_status.json up to date (run local_reverse_training_status.py)",
        ],
        "adapter_schema_fields_needed": [
            "tool_capability_inventory.json: capability entry for IDA with current_status=implemented",
            "structured_evidence_gap_report.json: evidence mapping for IDA output",
            "artifact_index.json: freshness tracking for static triage artifacts",
        ],
        "current_blockers": [
            "IDA must be installed and configured on the system",
            "IDA script must produce valid JSON evidence",
            "local_reverse_training_next_queue.json must have inventory_only samples with allowed_next_action containing bounded_static_triage",
        ],
    })

    return {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "generated_at": _now_iso(),
        "evidence_usage_boundary": {
            "current": "artifacts with freshness=current in artifact_index.json; produced by validated tool runs in the current or recent rounds",
            "stale": "artifacts with freshness=stale; can be referenced as historical context but NOT as current evidence for decision-making",
            "missing": "artifacts with freshness=missing; cannot be used as evidence; must be regenerated or marked as not needed",
            "unknown": "capabilities or artifacts not yet inventoried; must be assessed before use",
        },
        "evidence_mappings": evidence_mappings,
        "evidence_gaps": evidence_gaps,
        "triage_prerequisites": triage_prerequisites,
        "summary": {
            "total_capabilities_assessed": len(inventory["capabilities"]),
            "with_full_structured_evidence": sum(1 for m in evidence_mappings if m.get("structured_evidence_available")),
            "registrable_but_missing_se": sum(1 for m in evidence_mappings if not m.get("structured_evidence_available") and m.get("tool_output_registrable_in_artifact_index")),
            "not_registrable": sum(1 for m in evidence_mappings if not m.get("tool_output_registrable_in_artifact_index")),
            "total_gaps": len(evidence_gaps),
        },
    }


def build(
    state_dir: Path | str = "project_state",
    out_inventory: Path | str | None = None,
    out_gap_report: Path | str | None = None,
    decision_id: str = "",
    round_id: str = "",
) -> dict[str, Any]:
    """Build tool capability inventory and gap report.

    Returns a dict with 'inventory' and 'gap_report' keys.
    """
    state_dir = Path(state_dir)
    if out_inventory is None:
        out_inventory = state_dir / "tool_capability_inventory.json"
    if out_gap_report is None:
        out_gap_report = state_dir / "structured_evidence_gap_report.json"
    out_inventory = Path(out_inventory)
    out_gap_report = Path(out_gap_report)

    # Try to read decision_id and round_id from decision_packet if not provided
    if not decision_id or not round_id:
        dp_path = state_dir / "decision_packet.md"
        if dp_path.exists():
            try:
                dp_text = dp_path.read_text(encoding="utf-8")
                m_id = re.search(r'"decision_id"\s*:\s*"([^"]+)"', dp_text)
                m_round = re.search(r'"round_id"\s*:\s*"([^"]+)"', dp_text)
                if m_id and not decision_id:
                    decision_id = m_id.group(1)
                if m_round and not round_id:
                    round_id = m_round.group(1)
            except Exception:
                pass

    inventory = _build_inventory(decision_id, round_id)
    gap_report = _build_gap_report(decision_id, round_id, inventory)

    out_inventory.parent.mkdir(parents=True, exist_ok=True)
    out_gap_report.parent.mkdir(parents=True, exist_ok=True)

    with open(out_inventory, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    with open(out_gap_report, "w", encoding="utf-8") as f:
        json.dump(gap_report, f, indent=2, ensure_ascii=False)

    return {
        "inventory_path": str(out_inventory),
        "gap_report_path": str(out_gap_report),
        "inventory": inventory,
        "gap_report": gap_report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build tool capability inventory and gap report")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build inventory and gap report")
    build_parser.add_argument("--state-dir", default="project_state", help="Path to project_state directory")
    build_parser.add_argument("--out-inventory", default=None, help="Output path for inventory JSON")
    build_parser.add_argument("--out-gap-report", default=None, help="Output path for gap report JSON")
    build_parser.add_argument("--decision-id", default="", help="Decision ID to embed in artifacts")
    build_parser.add_argument("--round-id", default="", help="Round ID to embed in artifacts")

    # Also support direct invocation without subcommand for backward compatibility
    parser.add_argument("--state-dir", default="project_state", help="Path to project_state directory")
    parser.add_argument("--out-inventory", default=None, help="Output path for inventory JSON")
    parser.add_argument("--out-gap-report", default=None, help="Output path for gap report JSON")
    parser.add_argument("--decision-id", default="", help="Decision ID to embed in artifacts")
    parser.add_argument("--round-id", default="", help="Round ID to embed in artifacts")

    args = parser.parse_args()

    # If subcommand is 'build' or no subcommand given, run build
    if args.command == "build" or args.command is None:
        result = build(
            state_dir=args.state_dir,
            out_inventory=args.out_inventory,
            out_gap_report=args.out_gap_report,
            decision_id=args.decision_id,
            round_id=args.round_id,
        )

        print(f"inventory: {result['inventory_path']}")
        print(f"gap_report: {result['gap_report_path']}")
        inv = result["inventory"]
        print(f"capabilities: {inv['summary']['total_capabilities']} total, "
              f"{inv['summary']['implemented']} implemented, "
              f"{inv['summary']['partial']} partial, "
              f"{inv['summary']['missing']} missing")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
