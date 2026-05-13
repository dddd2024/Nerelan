import json
import zipfile
from pathlib import Path

from reverse_agent.project_state import archive_round, build_project_state, main, pack_context


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_minimal_harness_run(reports_dir: Path, run_name: str = "samplereverse_stalled") -> Path:
    run_dir = reports_dir / "harness_runs" / run_name
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        run_dir / "summary.json",
        {
            "run_name": run_name,
            "run_dir": str(run_dir),
            "error_cases": 0,
            "case_result_paths": [str(run_dir / "case_results" / "samplereverse.json")],
        },
    )
    _write_json(
        run_dir / "run_manifest.json",
        {
            "run_name": run_name,
            "status": "completed",
            "case_ids": ["samplereverse"],
        },
    )
    _write_json(
        run_dir / "case_results" / "samplereverse.json",
        {
            "case_id": "samplereverse",
            "status": "completed_no_expected",
            "profile_name": "samplereverse",
            "matched_profiles": ["samplereverse"],
            "applied_strategies": ["CompareAwareSearchStrategy"],
            "error": "",
        },
    )
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_frontier_summary.json",
        {
            "frontier_active_lane": "frontier_exact1",
            "frontier_stall_stage": "pair_pool",
            "frontier_exact1_stall_reason": "distance_not_improved",
            "frontier_converged_reason": "distance_not_improved",
            "frontier_anchor_candidates": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "compare_semantics_agree": True,
                    "frontier_role": "exact2_seed",
                },
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "runtime_ci_exact_wchars": 1,
                    "runtime_ci_distance5": 258,
                    "compare_semantics_agree": True,
                    "frontier_role": "exact1_frontier",
                },
            ],
        },
    )
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_strata_summary.json",
        {
            "frontier_stall_stage": "pair_pool",
            "frontier_exact1_stall_reason": "distance_not_improved",
            "best_exact2_runtime": {
                "candidate_hex": "78d540b49c59077041414141414141",
                "cand8_hex": "78d540b49c590770",
                "runtime_ci_exact_wchars": 2,
                "runtime_ci_distance5": 246,
                "compare_semantics_agree": True,
            },
            "best_frontier_runtime": {
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
                "cand8_hex": "5a3e7f46ddd474d0",
                "runtime_ci_exact_wchars": 1,
                "runtime_ci_distance5": 258,
                "compare_semantics_agree": True,
                "frontier_role": "exact1_frontier",
            },
        },
    )
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_guided_pool_result.json",
        {"large_payload": "SOLVE_REPORTS_FULL_SENTINEL"},
    )
    _write_json(
        artifacts_dir / "samplereverse_compare_aware_guided_pool_validation.json",
        {"validations": [{"candidate_hex": "5a3e7f46ddd474d041414141414141"}]},
    )
    return run_dir


def test_build_missing_solve_reports_does_not_crash_and_writes_files(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"

    build_project_state(
        reports_dir=tmp_path / "missing_reports",
        state_dir=state_dir,
        sample="samplereverse",
    )

    expected = {
        "artifact_index.json",
        "current_state.json",
        "negative_results.json",
        "model_gate.json",
        "task_packet.json",
    }
    assert expected.issubset({item.name for item in state_dir.iterdir()})
    assert (state_dir / "decision_packet.md").exists()
    assert (state_dir / "codex_execution_report.md").exists()
    assert (state_dir / "README.md").exists()
    assert (state_dir / "rounds" / ".gitkeep").exists()
    assert _read_json(state_dir / "artifact_index.json")["missing"] == ["reports_dir"]
    assert _read_json(state_dir / "model_gate.json")["should_call_model"] is False


def test_project_state_indexes_pre_rc4_material_probe_and_negative_result(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_pre_rc4")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "pre_rc4_material_probe" / "pre_rc4_material_probe.json",
        {
            "artifact_kind": "pre_rc4_material_probe",
            "classification": "material_capture_unreliable",
            "runtime_backed_count": 0,
            "candidate_count": 3,
            "probe_points": {
                "base64_material": "unavailable",
                "rc4_ksa_key": "unavailable",
                "compare_buffer": "unavailable",
            },
            "rc4_key_status": "unknown",
            "rc4_input_status": "unknown",
            "first_divergence_stage": "unknown",
            "offline_runtime_agreement_table": [],
            "producer_material_relation_table": [],
            "next_bounded_action": "switch to manual breakpoints",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["pre_rc4_material_probe"].endswith("pre_rc4_material_probe.json")
    assert current_state["current_bottleneck"]["stage"] == "pre_rc4_material_probe"
    assert current_state["latest_pre_rc4_material_probe"]["classification"] == "material_capture_unreliable"
    assert current_state["latest_pre_rc4_material_probe"]["first_divergence_stage"] == "unknown"
    assert any("memory-scan lower-level pre-RC4" in item["direction"] for item in negative_results)


def test_project_state_indexes_base64_rc4_breakpoint_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_breakpoint")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "base64_rc4_breakpoint_probe" / "base64_rc4_breakpoint_probe.json",
        {
            "artifact_kind": "base64_rc4_breakpoint_probe",
            "classification": "breakpoint_probe_partial",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hook_event_count": 3,
            "static_point_summary": {"base64": {"count": 1, "hookable_count": 1}},
            "hook_results": {
                "base64_input": "unavailable",
                "base64_output": "unavailable",
                "rc4_key": "unavailable",
                "rc4_input": "unavailable",
                "rc4_output": "unavailable",
                "compare_buffer": "available",
            },
            "first_captured_material_kind": "compare_buffer",
            "next_bottleneck": "compare-only capture",
            "next_bounded_action": "manual breakpoints",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["base64_rc4_breakpoint_probe"].endswith(
        "base64_rc4_breakpoint_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "base64_rc4_breakpoint_probe"
    assert current_state["latest_base64_rc4_breakpoint_probe"]["classification"] == "breakpoint_probe_partial"
    assert current_state["latest_base64_rc4_breakpoint_probe"]["hook_event_count"] == 3
    assert current_state["latest_base64_rc4_breakpoint_probe"]["first_captured_material_kind"] == "compare_buffer"
    assert current_state["latest_base64_rc4_breakpoint_probe"]["next_bottleneck"] == "compare-only capture"
    assert "static_points" not in current_state["latest_base64_rc4_breakpoint_probe"]
    assert any("scripted Base64/RC4 breakpoint probe" in item["direction"] for item in negative_results)


def test_project_state_indexes_base64_rc4_static_point_discovery(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_static")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "base64_rc4_static_point_discovery.json",
        {
            "artifact_kind": "base64_rc4_static_point_discovery",
            "classification": "manual_disassembly_required",
            "hookable_count": 2,
            "instruction_confirmed_count": 0,
            "by_kind": {
                "base64": {"count": 1, "hookable_count": 1, "instruction_confirmed_count": 0},
                "encrypted_const": {"count": 1, "hookable_count": 1, "instruction_confirmed_count": 0},
            },
            "best_points": [
                {
                    "kind": "base64",
                    "module_offset": "0x3000",
                    "rva": "0x3000",
                    "instruction": "",
                    "hookable": True,
                    "confidence": "high",
                    "evidence": ["standard alphabet"],
                    "classification": "hookable_but_unconfirmed",
                }
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "confirm the ambiguous Base64/RC4 offsets in IDA/x64dbg before rerunning breakpoint probe",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["base64_rc4_static_point_discovery"].endswith(
        "base64_rc4_static_point_discovery.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "base64_rc4_static_point_discovery"
    latest = current_state["latest_static_point_discovery"]
    assert latest["classification"] == "manual_disassembly_required"
    assert latest["hookable_count"] == 2
    assert latest["by_kind"]["base64"]["hookable_count"] == 1
    assert latest["best_points"][0]["module_offset"] == "0x3000"
    assert any("static point discovery" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_stack_pivot_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_stack_pivot")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_stack_pivot_probe" / "compare_stack_pivot_probe.json",
        {
            "artifact_kind": "compare_stack_pivot_probe",
            "classification": "compare_stack_pivot_complete",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "utf16le_payload_available_count": 3,
            "hook_results": {
                "utf16le_payload": "available_from_compare_stack",
                "compare_buffer": "available",
            },
            "static_audit": {
                "classification": "static_anchor_confirmed",
                "compare_site": {
                    "expected_call_rva": "0x258c",
                    "actual_call_rva": "0x258c",
                    "helper_rva": "0x1028ac",
                },
            },
            "next_hook_points": [{"name": "post_handoff_lhs_reload", "module_offset": 0x2559}],
            "next_bounded_action": "hook module+0x1b50",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_stack_pivot_probe"].endswith(
        "compare_stack_pivot_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_stack_pivot_probe"
    latest = current_state["latest_compare_stack_pivot_probe"]
    assert latest["classification"] == "compare_stack_pivot_complete"
    assert latest["utf16le_payload_available_count"] == 3
    assert any("compare stack pivot hook points" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_handoff_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_handoff")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_probe" / "compare_handoff_probe.json",
        {
            "artifact_kind": "compare_handoff_probe",
            "classification": "handoff_capture_partial",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hook_results": {
                "handoff_helper_enter": "available",
                "handoff_helper_return": "unavailable",
                "post_handoff_lhs_reload": "available",
                "compare_lhs_buffer": "available",
                "lhs_slot": "available",
            },
            "compare_stack_pivot_audit": {
                "compare_call_rva": "0x258c",
                "handoff_helper_rva": "0x1b50",
                "post_handoff_reload_rva": "0x2559",
                "lhs_slot": "[ebp-0x1170]",
                "static_anchor_valid": True,
                "reason": [],
            },
            "next_bounded_action": "perform a narrower backward slice from 0x401b50 helper arguments",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_probe"].endswith("compare_handoff_probe.json")
    assert current_state["current_bottleneck"]["stage"] == "compare_handoff_probe"
    latest = current_state["latest_compare_handoff_probe"]
    assert latest["classification"] == "handoff_capture_partial"
    assert latest["hook_results"]["post_handoff_lhs_reload"] == "available"
    assert any("compare handoff probe" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_handoff_slice_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_handoff_slice")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_slice_probe" / "compare_handoff_slice_probe.json",
        {
            "artifact_kind": "compare_handoff_slice_probe",
            "classification": "wrong_reload_anchor",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hook_results": {
                "handoff_helper_enter": "available",
                "handoff_helper_return": "available",
                "post_handoff_lhs_reload": "unavailable",
                "post_handoff_after_reload": "available",
                "compare_lhs_buffer": "available",
                "lhs_slot": "available",
            },
            "static_audit": {
                "classification": "static_anchor_confirmed",
                "prior_reload_anchor": "module+0x2559",
                "corrected_post_helper_probe": "helper onLeave plus module+0x255c fallback",
            },
            "cross_candidate_summary": {
                "relation_counts": {"helper_return_eax_preview_matches_compare_lhs": 3},
            },
            "next_bounded_action": "replace module+0x2559 with an instruction-confirmed post-helper hook point",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_slice_probe"].endswith(
        "compare_handoff_slice_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_handoff_slice_probe"
    assert current_state["current_bottleneck"]["reason"] == "wrong_reload_anchor"
    latest = current_state["latest_compare_handoff_slice_probe"]
    assert latest["classification"] == "wrong_reload_anchor"
    assert latest["hook_results"]["post_handoff_after_reload"] == "available"
    assert any("helper slice" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_handoff_return_site_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_return_site")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_handoff_return_site_probe" / "compare_handoff_return_site_probe.json",
        {
            "artifact_kind": "compare_handoff_return_site_probe",
            "classification": "wrong_helper_assumption",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hook_results": {
                "handoff_helper_enter": "available",
                "handoff_helper_return": "available",
                "helper_return_site": "available",
                "wide_flag_prefix_compare": "available",
                "compare_call_args": "available",
            },
            "static_audit": {
                "classification": "static_return_site_audit_complete",
                "hook_point_audit": [
                    {
                        "name": "post_handoff_after_reload",
                        "module_offset": "0x255c",
                        "boundary_status": "inside_instruction",
                    }
                ],
            },
            "cross_candidate_summary": {
                "relation_counts": {"helper_enter_return_is_0x233d": 3},
                "target_flag_side_counts": {"arg0": 3},
            },
            "next_bounded_action": "move to the next bounded pre-compare handoff target",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_handoff_return_site_probe"].endswith(
        "compare_handoff_return_site_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_handoff_return_site_probe"
    assert current_state["current_bottleneck"]["reason"] == "wrong_helper_assumption"
    latest = current_state["latest_compare_handoff_return_site_probe"]
    assert latest["classification"] == "wrong_helper_assumption"
    assert latest["hook_results"]["compare_call_args"] == "available"
    assert any("return-site audit" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_producer_trace_probe_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_producer_trace")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "base64_rc4_static_point_discovery.json",
        {
            "artifact_kind": "base64_rc4_static_point_discovery",
            "classification": "hookable_points_found",
            "breakpoint_probe_allowed": False,
        },
    )
    _write_json(
        artifacts_dir / "base64_rc4_breakpoint_probe" / "base64_rc4_breakpoint_probe.json",
        {
            "artifact_kind": "base64_rc4_breakpoint_probe",
            "classification": "base64_rc4_static_points_unavailable",
            "hook_results": {"compare_buffer": "available"},
        },
    )
    _write_json(
        artifacts_dir / "compare_producer_trace_probe" / "compare_producer_trace_probe.json",
        {
            "artifact_kind": "compare_producer_trace_probe",
            "classification": "compare_producer_trace_captured",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "candidate_material_count": 3,
            "candidate_materials": [
                {
                    "kind": "compare_buffer",
                    "address": "0x36dce20",
                    "preview_hex": "46006c004464830d311c",
                    "evidence": ["matches compare arg"],
                }
            ],
            "write_source_trace_count": 1,
            "write_source_trace": [
                {
                    "source_module_offset": "0x253a",
                    "instruction": "mov dword ptr [ebp - 0x1170], eax",
                    "classification": "compare_buffer_write_source",
                }
            ],
            "material_hook_candidate_count": 0,
            "material_hook_candidates": [],
            "breakpoint_probe_allowed": False,
            "hook_results": {
                "producer_return_site": "available",
                "compare_helper_entry": "available",
                "compare_entry_args": "available",
            },
            "hook_miss_classification": {
                "missed_hooks": "post_handoff_lhs_reload, pre_compare_push_esi",
                "classification": "wrapper/alternate compare path",
            },
            "static_audit": {
                "classification": "static_producer_trace_audit_complete",
                "producer_window": {"start_rva": "0x2310", "end_rva": "0x2365"},
            },
            "cross_candidate_summary": {
                "relation_counts": {"producer_eax_matches_compare_arg_ptr": 3},
                "target_flag_side_counts": {"entry_arg1": 3},
            },
            "next_bounded_action": "derive candidate-side byte constraints from the actual compare helper entry args",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_producer_trace_probe"].endswith(
        "compare_producer_trace_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_producer_trace_probe"
    assert current_state["current_bottleneck"]["reason"] == "compare_producer_trace_captured"
    latest = current_state["latest_compare_producer_trace_probe"]
    assert latest["classification"] == "compare_producer_trace_captured"
    assert latest["candidate_material_count"] == 3
    assert latest["best_material_candidates"][0]["kind"] == "compare_buffer"
    assert latest["write_source_trace_count"] == 1
    assert latest["material_hook_candidate_count"] == 0
    assert latest["breakpoint_probe_allowed"] is False
    assert latest["hook_results"]["compare_helper_entry"] == "available"
    assert latest["hook_miss_classification"]["classification"] == "wrapper/alternate compare path"
    assert any("producer trace" in item["direction"] for item in negative_results)


def test_project_state_indexes_compare_producer_material_confirmation_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_material_confirmation")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_producer_trace_probe" / "compare_producer_trace_probe.json",
        {
            "artifact_kind": "compare_producer_trace_probe",
            "classification": "upstream_material_candidate_found",
            "candidate_material_count": 3,
            "breakpoint_probe_allowed": False,
        },
    )
    _write_json(
        artifacts_dir / "compare_producer_material_confirmation.json",
        {
            "artifact_kind": "compare_producer_material_confirmation",
            "classification": "material_confirmation_inconclusive",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "instruction_confirmation_table": [
                {
                    "hook_name": "producer_return_site",
                    "module_offset": "0x233d",
                    "instruction": "mov edx, dword ptr [ebp - 0x116c]",
                    "observed_count": 3,
                    "candidate_dependent_eax": True,
                    "instruction_confirmed": True,
                    "hookable": True,
                }
            ],
            "material_source_trace": [
                {
                    "hook_name": "producer_return_site",
                    "module_offset": "0x233d",
                    "classification": "expected_candidate_material_seen",
                }
            ],
            "confirmed_material_hook_candidate_count": 0,
            "confirmed_material_hook_candidates": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "manually inspect producer offsets 0x2320, 0x2338, 0x234e, and 0x2355",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_producer_material_confirmation"].endswith(
        "compare_producer_material_confirmation.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_producer_material_confirmation"
    assert current_state["current_bottleneck"]["reason"] == "material_confirmation_inconclusive"
    latest = current_state["latest_compare_producer_material_confirmation"]
    assert latest["classification"] == "material_confirmation_inconclusive"
    assert latest["runtime_backed_count"] == 3
    assert latest["instruction_confirmation_table"][0]["hook_name"] == "producer_return_site"
    assert latest["material_source_trace"][0]["module_offset"] == "0x233d"
    assert latest["breakpoint_probe_allowed"] is False
    assert any("producer material confirmation" in item["direction"] for item in negative_results)


def test_project_state_indexes_pre_compare_handoff_target_probe_and_negative_cache(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_pre_compare_handoff")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "compare_pre_compare_handoff_target_probe.json",
        {
            "artifact_kind": "compare_pre_compare_handoff_target_probe",
            "classification": "wrong_window",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "hit_summary": {
                "hit_producer_return_site_count": 3,
                "hit_producer_pre_candidate_push_count": 3,
                "hit_producer_pre_output_call_count": 0,
                "hit_producer_pre_second_call_count": 0,
                "hit_compare_helper_entry_count": 3,
            },
            "hook_miss_classification": "branch_exits_before_output_calls",
            "candidate_dependent_fields": {"producer_return_site.eax_preview_hex": True},
            "relation_counts": {"producer_return_site.eax_to_arg0.ptr_matches": 3},
            "relation_table": [{"candidate_hex": "78d540b49c59077041414141414141"}],
            "material_hook_candidate_count": 0,
            "material_hook_candidates": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "inspect branch/call outcome after 0x233d",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_pre_compare_handoff_target_probe"].endswith(
        "compare_pre_compare_handoff_target_probe.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_pre_compare_handoff_target_probe"
    assert current_state["current_bottleneck"]["reason"] == "wrong_window"
    latest = current_state["latest_compare_pre_compare_handoff_target_probe"]
    assert latest["classification"] == "wrong_window"
    assert latest["hook_miss_classification"] == "branch_exits_before_output_calls"
    assert latest["relation_counts"]["producer_return_site.eax_to_arg0.ptr_matches"] == 3
    assert any("0x401b50 -> 0x2559" in item["direction"] for item in negative_results)


def test_project_state_indexes_function_semantic_audit_and_negative_cache(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="samplereverse_function_semantics")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    _write_json(
        artifacts_dir / "function_semantic_audit" / "function_semantic_audit.json",
        {
            "artifact_kind": "function_semantic_audit",
            "classification": "runtime_instrumentation_required",
            "sample": "samplereverse",
            "profile": "samplereverse",
            "target_functions": ["0x4019e0", "0x401b50", "0x4018cd", "0x401be3"],
            "function_count": 4,
            "functions": [
                {
                    "function": "0x401b50",
                    "semantic_guess": "unknown_but_bounded",
                    "confidence": "medium",
                    "candidate_dependent": False,
                    "instruction_confirmed": True,
                    "hookable": True,
                    "material_hook_candidate_status": "blocked_missing_candidate_dependent_output",
                }
            ],
            "material_hook_candidate_count": 0,
            "material_hook_candidates": [],
            "breakpoint_probe_allowed": False,
            "top_semantic_guesses": [
                {
                    "function": "0x401b50",
                    "semantic_guess": "unknown_but_bounded",
                    "confidence": "medium",
                }
            ],
            "next_bounded_action": "confirm the 0x401b50 return path",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["function_semantic_audit"].endswith("function_semantic_audit.json")
    assert current_state["current_bottleneck"]["stage"] == "function_semantic_audit"
    assert current_state["current_bottleneck"]["reason"] == "runtime_instrumentation_required"
    latest = current_state["latest_function_semantic_audit"]
    assert latest["function_count"] == 4
    assert latest["material_hook_candidate_count"] == 0
    assert latest["breakpoint_probe_allowed"] is False
    assert current_state["function_semantics"]["0x401b50"]["material_hook_candidate_status"] == (
        "blocked_missing_candidate_dependent_output"
    )
    assert any(item.get("scope") == "function_semantics" for item in negative_results)


def test_project_state_indexes_material_hook_runtime_validation_and_bottleneck(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_mhrv")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "material_hook_runtime_validation").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "material_hook_runtime_validation" / "material_hook_runtime_validation.json",
        {
            "artifact_kind": "material_hook_runtime_validation",
            "classification": "BLOCKED",
            "runtime_backed_count": 4,
            "candidate_count": 4,
            "validated_hooks": [],
            "blocked_hooks": [
                {
                    "hook_name": "producer_return_site",
                    "module_offset": "0x233d",
                    "classification": "candidate_dependent_but_not_transform_material",
                    "hit_count": 4,
                    "candidate_dependent": True,
                    "connects_to_transform_chain": False,
                }
            ],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "keep Base64/RC4 breakpoint probe blocked",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["material_hook_runtime_validation"].endswith(
        "material_hook_runtime_validation.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "material_hook_runtime_validation"
    assert current_state["current_bottleneck"]["reason"] == "BLOCKED"
    latest = current_state["latest_material_hook_runtime_validation"]
    assert latest["classification"] == "BLOCKED"
    assert latest["candidate_count"] == 4
    assert latest["validated_hook_count"] == 0
    assert latest["blocked_hook_count"] == 1
    assert latest["breakpoint_probe_allowed"] is False
    assert any(item.get("scope") == "material_hook_runtime_validation" for item in negative_results)


def test_project_state_indexes_post_handoff_branch_outcome_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_post_handoff")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "post_handoff_branch_outcome_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "post_handoff_branch_outcome_audit" / "post_handoff_branch_outcome_audit.json",
        {
            "artifact_kind": "post_handoff_branch_outcome_audit",
            "classification": "post_handoff_window_rejected",
            "source_pre_compare_handoff_classification": "next_handoff_target_identified",
            "source_pre_compare_handoff_hook_miss_classification": "branch_exits_before_output_calls",
            "source_material_hook_runtime_classification": "REJECTED",
            "failed_material_hook_hypotheses": [
                {
                    "hook_name": "producer_return_site",
                    "module_offset": "0x233d",
                    "classification": "not_reached",
                }
            ],
            "window": {
                "downstream_transform_calls_reached": False,
                "rows": [
                    {"hook_name": "producer_return_site", "module_offset": "0x233d", "observed_count": 3},
                    {"hook_name": "producer_pre_output_call", "module_offset": "0x234e", "observed_count": 0},
                ],
            },
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "audit the 0x233d -> 0x2346 follow-up branch/call outcome",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["post_handoff_branch_outcome_audit"].endswith(
        "post_handoff_branch_outcome_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "post_handoff_branch_outcome_audit"
    assert current_state["current_bottleneck"]["reason"] == "post_handoff_window_rejected"
    latest = current_state["latest_post_handoff_branch_outcome_audit"]
    assert latest["classification"] == "post_handoff_window_rejected"
    assert latest["source_material_hook_runtime_classification"] == "REJECTED"
    assert latest["failed_material_hook_hypotheses"][0]["module_offset"] == "0x233d"
    assert latest["downstream_transform_calls_reached"] is False
    assert any(item.get("scope") == "post_handoff_branch_outcome_audit" for item in negative_results)


def test_project_state_indexes_compare_lhs_producer_audit_and_negative_cache(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = _make_minimal_harness_run(reports_dir, run_name="sr_lhs_prod")
    artifacts_dir = run_dir / "reports" / "tool_artifacts" / "samplereverse"
    (artifacts_dir / "compare_lhs_producer_audit").mkdir(parents=True, exist_ok=True)
    _write_json(
        artifacts_dir / "compare_lhs_producer_audit" / "compare_lhs_producer_audit.json",
        {
            "artifact_kind": "compare_lhs_producer_audit",
            "classification": "producer_window_rejected",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "checked_windows": [
                {
                    "hook_name": "pre_lhs_slot_store",
                    "module_offset": "0x253a",
                    "runtime_backed_count": 3,
                    "candidate_dependent": True,
                    "connects_to_compare_lhs": False,
                }
            ],
            "relations": {
                "slot_to_compare_arg": "rejected",
                "eax_to_slot": "rejected",
                "esi_to_compare_arg": "rejected",
                "helper_return_to_lhs": "rejected",
            },
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "move earlier than 0x253a..0x258b",
        },
    )

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    assert artifact_index["latest_artifacts"]["compare_lhs_producer_audit"].endswith(
        "compare_lhs_producer_audit.json"
    )
    assert current_state["current_bottleneck"]["stage"] == "compare_lhs_producer_audit"
    assert current_state["current_bottleneck"]["reason"] == "producer_window_rejected"
    latest = current_state["latest_compare_lhs_producer_audit"]
    assert latest["classification"] == "producer_window_rejected"
    assert latest["candidate_count"] == 3
    assert latest["runtime_backed_count"] == 3
    assert latest["relations"]["slot_to_compare_arg"] == "rejected"
    assert latest["breakpoint_probe_allowed"] is False
    assert any(item.get("scope") == "compare_lhs_producer_audit" for item in negative_results)


def test_build_generates_state_files_and_artifact_index(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    artifact_index = _read_json(state_dir / "artifact_index.json")
    assert artifact_index["latest_harness_run"]
    assert artifact_index["latest_summary"].endswith("summary.json")
    assert len(artifact_index["latest_case_results"]) == 1
    assert artifact_index["latest_artifacts"]["frontier_summary"].endswith(
        "samplereverse_compare_aware_frontier_summary.json"
    )
    assert artifact_index["latest_artifacts"]["guided_pool_validation"].endswith(
        "samplereverse_compare_aware_guided_pool_validation.json"
    )


def test_current_state_negative_results_model_gate_and_task_packet_are_generated(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    current_state = _read_json(state_dir / "current_state.json")
    negative_results = _read_json(state_dir / "negative_results.json")
    model_gate = _read_json(state_dir / "model_gate.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert current_state["active_strategy"] == "CompareAwareSearchStrategy"
    assert current_state["best_candidates"]["exact2"]["runtime_ci_exact_wchars"] == 2
    assert current_state["current_bottleneck"]["stage"] == "pair_pool"
    assert any(item["severity"] == "hard_block" for item in negative_results)
    assert model_gate["should_call_model"] is True
    assert model_gate["context_level"] == 2
    assert task_packet["task"] == "Generate next decision for exact1 pair_pool bottleneck"
    assert task_packet["sufficiency_check"]["has_runtime_validation"] is True
    assert task_packet["expected_gpt_output"] == "project_state/decision_packet.md"
    assert "do not commit full solve_reports directory" in task_packet["do_not_do"]


def test_task_packet_omits_full_progress_log_and_full_solve_reports(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    progress_log = tmp_path / "PROJECT_PROGRESS_LOG.txt"
    progress_log.write_text("VERY_LONG_SECRET_PROGRESS_LOG_SENTINEL", encoding="utf-8")
    _make_minimal_harness_run(reports_dir)

    build_project_state(
        reports_dir=reports_dir,
        state_dir=state_dir,
        sample="samplereverse",
        progress_log=progress_log,
    )

    packet_text = (state_dir / "task_packet.json").read_text(encoding="utf-8")
    assert "VERY_LONG_SECRET_PROGRESS_LOG_SENTINEL" not in packet_text
    assert "SOLVE_REPORTS_FULL_SENTINEL" not in packet_text
    task_packet = _read_json(state_dir / "task_packet.json")
    assert "artifact_refs" in task_packet
    assert any(item["name"] == "full solve_reports" for item in task_packet["omitted"])


def test_model_gate_returns_false_when_artifacts_are_missing(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    run_dir = reports_dir / "harness_runs" / "incomplete"
    _write_json(run_dir / "summary.json", {"run_name": "incomplete", "error_cases": 0})
    _write_json(run_dir / "run_manifest.json", {"run_name": "incomplete", "status": "completed"})
    _write_json(run_dir / "case_results" / "samplereverse.json", {"status": "completed_no_expected"})

    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    model_gate = _read_json(state_dir / "model_gate.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    assert model_gate["should_call_model"] is False
    assert model_gate["next_local_action"] == "collect_artifacts"
    assert task_packet["task"] == "collect_missing_evidence"
    assert "frontier_summary" in model_gate["missing_evidence"]


def test_windows_path_style_outputs_are_compatible(tmp_path: Path) -> None:
    reports_dir = tmp_path / "solve_reports"
    state_dir = tmp_path / "project_state"
    _make_minimal_harness_run(reports_dir)

    build_project_state(
        reports_dir=Path(str(reports_dir)),
        state_dir=Path(str(state_dir)),
        sample="samplereverse",
        run_name="samplereverse_stalled",
    )

    artifact_index = _read_json(state_dir / "artifact_index.json")
    assert Path(artifact_index["latest_summary"]).name == "summary.json"
    assert Path(artifact_index["latest_artifacts"]["frontier_summary"]).name == (
        "samplereverse_compare_aware_frontier_summary.json"
    )


def test_new_round_status_and_archive_round_create_expected_files(tmp_path: Path, capsys) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")

    assert main(["status", "--state-dir", str(state_dir)]) == 0
    output = capsys.readouterr().out
    assert "latest_harness_run:" in output
    assert "expected_gpt_output:" in output

    result = archive_round(state_dir=state_dir)
    round_dir = state_dir / "rounds" / "round_001"
    assert result["round_id"] == "round_001"
    assert round_dir.exists()
    assert (round_dir / "current_state.json").exists()
    assert (round_dir / "artifact_index.json").exists()
    assert (round_dir / "negative_results.json").exists()
    assert (round_dir / "model_gate.json").exists()
    assert (round_dir / "task_packet.json").exists()
    assert (round_dir / "decision_packet.md").exists()
    assert (round_dir / "codex_execution_report.md").exists()
    assert (round_dir / "git_diff.patch").exists()
    assert (round_dir / "pytest_result.txt").exists()


def test_archive_round_does_not_overwrite_existing_round(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    archive_round(state_dir=state_dir)
    sentinel = state_dir / "rounds" / "round_001" / "sentinel.txt"
    sentinel.write_text("keep me", encoding="utf-8")

    result = archive_round(state_dir=state_dir)

    assert result["round_id"] == "round_002"
    assert sentinel.read_text(encoding="utf-8") == "keep me"
    assert (state_dir / "rounds" / "round_002" / "task_packet.json").exists()


def test_pack_contains_only_allowed_project_state_files(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    reports_dir = tmp_path / "solve_reports"
    _make_minimal_harness_run(reports_dir)
    (reports_dir / "secret.exe").write_bytes(b"MZ")
    (tmp_path / ".env").write_text("API_KEY=secret", encoding="utf-8")
    build_project_state(reports_dir=reports_dir, state_dir=state_dir, sample="samplereverse")
    archive_round(state_dir=state_dir)
    out_path = tmp_path / "gpt_context_pack.zip"

    result = pack_context(state_dir=state_dir, out_path=out_path)

    assert out_path.exists()
    assert "project_state/task_packet.json" in result["files"]
    with zipfile.ZipFile(out_path) as archive:
        names = archive.namelist()
    assert "project_state/current_state.json" in names
    assert "project_state/decision_packet.md" in names
    assert any(name.endswith("git_diff.patch") for name in names)
    assert not any(name.startswith("solve_reports/") for name in names)
    assert not any(name.endswith(".exe") for name in names)
    assert ".env" not in names
