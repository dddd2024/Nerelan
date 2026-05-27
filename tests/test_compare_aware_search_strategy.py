import json
import subprocess
from pathlib import Path

import pytest

from reverse_agent.evidence import StructuredEvidence
from reverse_agent.function_semantics import FUNCTION_SEMANTIC_AUDIT_FILE_NAME
from reverse_agent.profiles.samplereverse import SamplereverseProfile
from reverse_agent.samplereverse_z3 import _optimize_ready, solve_targeted_prefix8
from reverse_agent.strategies import compare_aware_search
from reverse_agent.strategies.base import StrategyResult
from reverse_agent.strategies.compare_aware_search import (
    BASE64_RC4_BREAKPOINT_PROBE_FILE_NAME,
    BASE64_RC4_STATIC_POINT_DISCOVERY_FILE_NAME,
    BRIDGE_RESULT_FILE_NAME,
    COMPARE_HANDOFF_PROBE_FILE_NAME,
    COMPARE_HANDOFF_RETURN_SITE_PROBE_FILE_NAME,
    COMPARE_HANDOFF_SLICE_PROBE_FILE_NAME,
    COMPARE_HOOK_PATH_REACHABILITY_AUDIT_FILE_NAME,
    COMPARE_CALLSITE_REANCHOR_AND_LHS_PROVENANCE_AUDIT_FILE_NAME,
    COMPARE_ESI_SOURCE_WINDOW_AUDIT_FILE_NAME,
    COMPARE_LHS_PRODUCER_AUDIT_FILE_NAME,
    COMPARE_LHS_SLOT_WRITER_PREDECESSOR_AUDIT_FILE_NAME,
    COMPARE_LHS_SLOT_WRITER_SOURCE_AUDIT_FILE_NAME,
    COMPARE_LHS_UPSTREAM_WRITER_AUDIT_FILE_NAME,
    COMPARE_LHS_LAST_WRITER_PROVENANCE_AUDIT_FILE_NAME,
    COMPARE_REAL_LHS_PROVENANCE_AUDIT_FILE_NAME,
    COMPARE_PRE_COMPARE_HANDOFF_TARGET_PROBE_FILE_NAME,
    COMPARE_PRODUCER_MATERIAL_CONFIRMATION_FILE_NAME,
    COMPARE_PRODUCER_TRACE_PROBE_FILE_NAME,
    COMPARE_STACK_PIVOT_PROBE_FILE_NAME,
    CompareAwareSearchStrategy,
    DYNAMIC_COMPARE_PATH_PROBE_FILE_NAME,
    FRONTIER_ANCHOR_MODE,
    FRONTIER_EXACT0_SUBMODE,
    FRONTIER_EXACT1_SUBMODE,
    FRONTIER_MAX_ANCHORS,
    GUIDED_POOL_EXPLORATION_SLOTS,
    GUIDED_POOL_TOP_VALUES,
    H1_H3_BOUNDARY_CANDIDATE_LIMIT,
    H1_H3_BOUNDARY_VALIDATION_FILE_NAME,
    MATERIAL_HOOK_RUNTIME_VALIDATION_FILE_NAME,
    POST_HANDOFF_BRANCH_OUTCOME_AUDIT_FILE_NAME,
    POST_HANDOFF_EXCEPTION_UNWIND_AUDIT_FILE_NAME,
    PRE_RC4_MATERIAL_PROBE_FILE_NAME,
    PROFILE_TRANSFORM_AUDIT_CANDIDATE_LIMIT,
    PROFILE_TRANSFORM_HYPOTHESIS_MATRIX_FILE_NAME,
    PROJECTED_PRESERVE_SECOND_HOP_ROLE,
    RESULT_FILE_NAME,
    TRANSFORM_TRACE_CONSISTENCY_FILE_NAME,
    VALIDATION_FILE_NAME,
    _alternate_locked_pair_positions_for_exact1,
    _annotate_frontier_improvement_gate,
    _candidate_sort_key,
    _collect_validation_entries,
    _collect_frontier_promoted_anchors,
    _diverse_validation_candidates,
    _exact1_projected_competition_reason_from_runs,
    _exact1_projected_competition_summary,
    _extract_hot_positions,
    _feedback_value_pools_from_frontier_entries,
    _frontier_anchor_candidates,
    _frontier_continuation_candidates,
    _guided_pool_beam_entries,
    _improved_frontier_candidates,
    _mine_exact1_lineage_value_sources,
    _exact2_basin_smt_diagnostic_payload,
    _prefix_boundary_breakdown_from_prefix,
    _refine_anchor_plan,
    _select_smt_base_entry,
    _validated_projected_preserve_second_hop_candidates,
    build_compare_callsite_reanchor_and_lhs_provenance_audit_payload,
    build_compare_lhs_producer_audit_payload,
    build_compare_lhs_slot_writer_predecessor_audit_payload,
    build_compare_lhs_slot_writer_source_audit_payload,
    build_compare_lhs_upstream_writer_audit_payload,
    build_compare_lhs_last_writer_provenance_audit_payload,
    build_compare_hook_path_reachability_audit_payload,
    build_compare_esi_source_window_audit_payload,
    build_compare_real_lhs_provenance_audit_payload,
    build_post_handoff_branch_outcome_audit_payload,
    build_post_handoff_exception_unwind_audit_payload,
    build_function_semantic_audit_payload,
    run_compare_aware_smt,
    run_base64_rc4_breakpoint_probe,
    run_base64_rc4_static_point_discovery,
    run_compare_handoff_probe,
    run_compare_handoff_return_site_probe,
    run_compare_handoff_slice_probe,
    run_compare_callsite_reanchor_and_lhs_provenance_audit,
    run_compare_lhs_producer_audit,
    run_compare_lhs_slot_writer_predecessor_audit,
    run_compare_lhs_slot_writer_source_audit,
    run_compare_lhs_upstream_writer_audit,
    run_compare_lhs_last_writer_provenance_audit,
    run_compare_hook_path_reachability_audit,
    run_compare_esi_source_window_audit,
    run_compare_real_lhs_provenance_audit,
    run_compare_pre_compare_handoff_target_probe,
    run_compare_producer_material_confirmation_probe,
    run_compare_producer_trace_probe,
    run_compare_stack_pivot_probe,
    run_dynamic_compare_path_probe,
    run_exact2_basin_value_pool_evaluation,
    run_h1_h3_boundary_validation,
    run_function_semantic_audit,
    run_material_hook_runtime_validation,
    run_post_handoff_branch_outcome_audit,
    run_post_handoff_exception_unwind_audit,
    run_pre_rc4_material_probe,
    run_profile_transform_hypothesis_audit,
    run_transform_trace_consistency_diagnostic,
    validate_compare_aware_results,
    resolve_compare_aware_anchors,
)
from reverse_agent.tool_runners import ToolRunArtifact
from reverse_agent.transforms.samplereverse import (
    SamplereverseTransformModel,
    score_compare_prefix,
    trace_candidate_transform,
)


def test_score_compare_prefix_counts_known_exact2_basins() -> None:
    assert score_compare_prefix(bytes.fromhex("66006c0038ac00000000"))["ci_exact_wchars"] == 2
    assert score_compare_prefix(bytes.fromhex("46004c007e4000000000"))["ci_exact_wchars"] == 2


def test_prefix_boundary_breakdown_explains_exact2_exact1_and_projected() -> None:
    exact2 = _prefix_boundary_breakdown_from_prefix(
        bytes.fromhex("46006c004464830d311c"),
        candidate_hex="78d540b49c59077041414141414141",
    )
    exact1 = _prefix_boundary_breakdown_from_prefix(
        bytes.fromhex("460061357f0b8c688502"),
        candidate_hex="5a3e7f46ddd474d041414141414141",
    )
    projected = _prefix_boundary_breakdown_from_prefix(
        bytes.fromhex("74934b156ba69ef3370f"),
        candidate_hex="5a3f7f46ddd474d041414141414141",
    )

    assert exact2["ci_exact_wchars"] == 2
    assert [item["exact_ci"] for item in exact2["wchar_deltas"][:3]] == [True, True, False]
    assert exact2["wchar_deltas"][2]["raw_pair_hex"] == "4464"
    assert exact2["wchar_deltas"][2]["target_pair_hex"] == "6100"
    assert exact1["ci_exact_wchars"] == 1
    assert [item["exact_ci"] for item in exact1["wchar_deltas"][:2]] == [True, False]
    assert projected["ci_exact_wchars"] == 0
    assert projected["wchar_deltas"][0]["raw_pair_hex"] == "7493"


def test_trace_candidate_transform_records_layout_boundaries_and_known_runtime_prefix() -> None:
    trace = trace_candidate_transform("78d540b49c59077041414141414141")

    assert trace["valid"] is True
    assert trace["candidate_raw_bytes"]["hex"] == "78d540b49c59077041414141414141"
    assert trace["candidate_layout"]["candidate_length_bytes"] == 15
    assert trace["candidate_layout"]["prefix_hex"] == "78d540b49c590770"
    assert trace["candidate_layout"]["suffix_is_all_A"] is True
    assert trace["nibble_expansion"]["prefix_expanded_length_bytes"] == 16
    assert trace["utf16_payload"]["prefix_raw_length_bytes"] == 32
    assert trace["base64_boundary"]["prefix_ends_on_base64_chunk_boundary"] is False
    assert trace["base64_boundary"]["prefix_last_chunk_raw_remainder"] == 2
    assert trace["rc4"]["key_length_bytes"] == trace["rc4"]["key_source_base64_chars"]
    assert trace["rc4"]["decrypt_prefix_hex"].startswith("46006c004464830d311c")
    assert trace["compare_boundary"]["raw_prefix_hex_10"] == "46006c004464830d311c"
    assert trace["compare_boundary"]["compare_window_hex"] == "46006c004464830d311c"
    assert trace["compare_boundary"]["ci_exact_wchars"] == 2
    assert len(trace["prefix_length_table"]) == 10
    assert trace["prefix_length_table"][0]["candidate_prefix_len_bytes"] == 1
    assert trace["prefix_length_table"][9]["candidate_prefix_len_bytes"] == 10
    assert {"utf16le_hex", "base64_text", "base64_len", "rc4_input_len"} <= set(
        trace["prefix_length_table"][7]
    )
    assert [item["exact_ci"] for item in trace["compare_boundary"]["wchar_deltas"][:3]] == [
        True,
        True,
        False,
    ]


def test_solve_targeted_prefix8_records_bounded_value_pools_with_base_value() -> None:
    if not _optimize_ready():
        pytest.skip("z3 optimize is not installed")

    base_anchor = "78d540b49c590770"
    result = solve_targeted_prefix8(
        base_anchor=base_anchor,
        variable_byte_positions=[0],
        variable_nibble_positions=[],
        value_pools={0: [0x00]},
        timeout_ms=10,
    )

    assert result.attempted is True
    assert any("value_pools=0:78/00" in item for item in result.evidence or [])
    assert result.diagnostics
    assert result.diagnostics["solver_type"] == "Optimize"
    assert result.diagnostics["timeout_ms"] == 10
    assert result.diagnostics["symbolic_compare_bytes"] == 10
    assert result.diagnostics["value_pool_sizes"]["0"] == 2


def test_score_prefix_exposes_long_window_structure_metrics() -> None:
    metrics = SamplereverseTransformModel().score_prefix(
        bytes.fromhex(
            "66006c00610067007b00410042005f007d00"
            "11223344556677889900aabbccddeeff"
        )
    )

    assert metrics["raw_prefix_hex"] == "66006c00610067007b00"
    assert metrics["raw_prefix_hex_64"].startswith("66006c00610067007b00410042005f007d00")
    assert metrics["wide_ascii_contiguous_16"] >= 8
    assert metrics["wide_ascii_total_16"] >= 8
    assert metrics["wide_zero_high_pairs_16"] >= 8
    assert metrics["flaglike_tail_pairs_16"] == 3


def test_candidate_sort_key_uses_long_window_tiebreakers() -> None:
    transform_model = SamplereverseTransformModel()
    stronger = {
        "candidate_hex": "111111111111111141414141414141",
        "raw_prefix_hex_64": "66006c00610067007b00410042005f007d00",
        "raw_prefix_hex": "66006c00610067007b00",
        "ci_exact_wchars": 5,
        "ci_distance5": 0,
        "raw_distance10": 0,
    }
    weaker = {
        "candidate_hex": "222222222222222241414141414141",
        "raw_prefix_hex_64": "66006c00610067007b00ff00ff00ff00",
        "raw_prefix_hex": "66006c00610067007b00",
        "ci_exact_wchars": 5,
        "ci_distance5": 0,
        "raw_distance10": 0,
    }

    assert _candidate_sort_key(stronger, transform_model) < _candidate_sort_key(weaker, transform_model)


def test_collect_validation_entries_prefers_explicit_validation_candidates() -> None:
    payload = {
        "top_entries": [
            {
                "candidate_hex": "aaaaaaaaaaaaaaaa41414141414141",
                "raw_prefix_hex": "66006c00000000000000",
                "ci_exact_wchars": 2,
                "ci_distance5": 999,
                "raw_distance10": 999,
            }
        ],
        "validation_candidates": [
            {
                "candidate_hex": "bbbbbbbbbbbbbbbb41414141414141",
                "raw_prefix_hex": "66006c00610000000000",
                "ci_exact_wchars": 3,
                "ci_distance5": 100,
                "raw_distance10": 100,
            },
            {
                "candidate_hex": "cccccccccccccccc41414141414141",
                "raw_prefix_hex": "66006c00610067000000",
                "ci_exact_wchars": 4,
                "ci_distance5": 10,
                "raw_distance10": 10,
            },
        ],
    }

    entries = _collect_validation_entries(payload, SamplereverseTransformModel(), validate_top=1)

    assert [entry["candidate_hex"] for entry in entries] == ["bbbbbbbbbbbbbbbb41414141414141"]


def test_diverse_validation_candidates_keeps_cross_basin_frontier() -> None:
    entries = [
        {
            "candidate_hex": "78d540b49c59077041414141414141",
            "raw_prefix_hex": "46006c004464830d311c",
            "ci_exact_wchars": 2,
            "ci_distance5": 246,
            "raw_distance10": 304,
        },
        {
            "candidate_hex": "95a3f65dcedb629041414141414141",
            "raw_prefix_hex": "6600583a481ab842862c",
            "ci_exact_wchars": 1,
            "ci_distance5": 305,
            "raw_distance10": 331,
        },
        {
            "candidate_hex": "e80c7471d342f6f041414141414141",
            "raw_prefix_hex": "7d0b4e0148099e048930",
            "ci_exact_wchars": 0,
            "ci_distance5": 174,
            "raw_distance10": 220,
        },
    ]

    frontier = _diverse_validation_candidates(
        entries,
        transform_model=SamplereverseTransformModel(),
        validate_top=4,
    )

    assert [entry["candidate_hex"] for entry in frontier] == [
        "78d540b49c59077041414141414141",
        "95a3f65dcedb629041414141414141",
        "e80c7471d342f6f041414141414141",
    ]


def test_frontier_guided_validation_candidates_preserve_projected_handoff_slot() -> None:
    guided_entries = [
        {
            "candidate_hex": f"{idx:016x}41414141414141",
            "cand8_hex": f"{idx:016x}",
            "ci_exact_wchars": 1,
            "ci_distance5": 200 + idx,
            "raw_distance10": 300 + idx,
        }
        for idx in range(1, 12)
    ]
    handoff = {
        "candidate_hex": "5a3f7f46ddd474d041414141414141",
        "cand8_hex": "5a3f7f46ddd474d0",
        "ci_exact_wchars": 0,
        "ci_distance5": 740,
        "raw_distance10": 820,
        "pair_candidate_origin": "exact1_projected_preserve_lane",
        "pair_projected_boundary_role": "projected_winner_with_base",
        "pair_projected_winner_gate_status": "projected_winner_promoted_to_near_local",
    }

    selected = compare_aware_search._frontier_guided_validation_candidates(
        [*guided_entries, handoff],
        [handoff],
        validate_top=10,
    )

    assert len(selected) == 10
    assert selected[-1]["cand8_hex"] == "5a3f7f46ddd474d0"
    assert selected[-1]["frontier_role"] == "projected_preserve_handoff"
    assert guided_entries[9]["cand8_hex"] not in {item["cand8_hex"] for item in selected}


def test_resolve_compare_aware_anchors_keeps_new_default_anchor_first(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_recent_compare_aware_payloads",
        lambda limit=16: [
            {
                "top_entries": [
                    {"candidate_hex": "4a78f0eaeb4f13b041414141414141"},
                    {"candidate_hex": "0123456789abcde041414141414141"},
                ]
            }
        ],
    )

    anchors = resolve_compare_aware_anchors(SamplereverseTransformModel(), ["4a78f0eaeb4f13b0"])

    assert anchors[:3] == [
        "78d540b49c590770",
        "4a78f0eaeb4f13b0",
        "95a3f65dcedb6290",
    ]
    assert "0123456789abcde0" in anchors


def test_extract_hot_positions_dedupes_and_limits_to_five() -> None:
    pair_entries = [
        {"positions_or_nibbles": [0, 1]},
        {"positions_or_nibbles": [0, 2]},
        {"positions_or_nibbles": [0, 3]},
        {"positions_or_nibbles": [1, 4]},
        {"positions_or_nibbles": [2, 4]},
        {"positions_or_nibbles": [5, 6]},
        {"positions_or_nibbles": [5, 7]},
        {"positions_or_nibbles": [6, 7]},
    ]

    hot = _extract_hot_positions(pair_entries, max_positions=5)

    assert hot == [0, 1, 2, 4, 5]


def test_refine_anchor_plan_only_keeps_main_promoted_and_frontier() -> None:
    anchors, sources = _refine_anchor_plan(
        "78d540b49c590770",
        [
            "789d40b49c310770",
            "95a3f65dcedb6290",
            "789d40b49c310770",
        ],
    )

    assert anchors == [
        "78d540b49c590770",
        "789d40b49c310770",
        "95a3f65dcedb6290",
    ]
    assert sources == {
        "78d540b49c590770": "seed_anchor",
        "789d40b49c310770": "bridge_promoted",
        "95a3f65dcedb6290": "bridge_promoted",
    }


def test_validate_compare_aware_results_persists_extended_runtime_prefix_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    compare_probe_script = tmp_path / "compare_probe.py"
    compare_probe_script.write_text("# mock compare probe\n", encoding="utf-8")
    result_path = tmp_path / RESULT_FILE_NAME
    result_path.write_text(
        json.dumps(
            {
                "validation_candidates": [
                    {
                        "candidate_hex": "78d540b49c59077041414141414141",
                        "cand8_hex": "78d540b49c590770",
                        "raw_prefix_hex": "46006c004464830d311c",
                        "ci_exact_wchars": 2,
                        "ci_distance5": 246,
                        "raw_distance10": 304,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    calls: list[list[str]] = []

    def fake_run(command, capture_output, text, encoding, errors):
        calls.append(list(command))
        compare_out = Path(command[command.index("--out") + 1])
        compare_out.write_text(
            json.dumps(
                {
                    "summary": "compare ok",
                    "lhs_wide_hex": "46006c004464830d311c112233445566",
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "runtime_lhs_prefix_hex": "46006c004464830d311c112233445566",
                    "runtime_lhs_prefix_hex_10": "46006c004464830d311c",
                    "runtime_lhs_prefix_hex_16": "46006c004464830d311c112233445566",
                    "runtime_lhs_prefix_bytes_captured": 16,
                    "compare_semantics_agree": True,
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(compare_aware_search, "_compare_probe_script_path", lambda: compare_probe_script)
    monkeypatch.setattr(compare_aware_search.subprocess, "run", fake_run)

    validation_path, validations = validate_compare_aware_results(
        target=target,
        artifacts_dir=tmp_path / "validation",
        result_path=result_path,
        transform_model=SamplereverseTransformModel(),
        validate_top=1,
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    written = json.loads(validation_path.read_text(encoding="utf-8"))
    assert validations[0]["runtime_lhs_prefix_hex"] == "46006c004464830d311c112233445566"
    assert validations[0]["runtime_lhs_prefix_hex_10"] == "46006c004464830d311c"
    assert validations[0]["runtime_lhs_prefix_hex_16"] == "46006c004464830d311c112233445566"
    assert validations[0]["runtime_lhs_prefix_bytes_captured"] == 16
    assert written["validations"][0]["runtime_lhs_prefix_hex_16"] == "46006c004464830d311c112233445566"
    assert "--capture-prefix-bytes" in calls[0]
    assert calls[0][calls[0].index("--capture-prefix-bytes") + 1] == "64"


def test_compare_aware_strategy_stops_after_bridge_progress(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")

    bridge_result = {
        "pairscan_path": str(tmp_path / "pairscan_summary.json"),
        "bridge_result_path": str(tmp_path / BRIDGE_RESULT_FILE_NAME),
        "bridge_validation_path": str(tmp_path / "bridge_validation.json"),
        "bridge_entries": [
            {
                "stage": "triad",
                "base_anchor": "78d540b49c590770",
                "positions_or_nibbles": [1, 3, 4],
                "candidate_hex": "7883401f9c59077041414141414141",
                "cand8_hex": "7883401f9c590770",
                "raw_prefix_hex": "46003e1dfd2bb62a3d09",
                "exact": 3,
                "dist4": 10,
                "dist6": 20,
                "dist10": 30,
                "ci_exact_wchars": 3,
                "ci_distance5": 120,
                "raw_distance10": 30,
            }
        ],
        "bridge_validations": [
            {
                "candidate_hex": "7883401f9c59077041414141414141",
                "cand8_hex": "7883401f9c590770",
                "compare_semantics_agree": True,
                "runtime_ci_exact_wchars": 3,
                "runtime_ci_distance5": 120,
                "compare_summary": "bridge ok",
            }
        ],
        "hot_positions": [1, 3, 4],
        "hot_nibbles": [2, 3, 6, 7, 10],
    }

    monkeypatch.setattr(compare_aware_search, "run_compare_aware_bridge", lambda **kwargs: bridge_result)
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_refine",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("refine should be skipped")),
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_smt",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("smt should be skipped")),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
    )

    assert result.candidates == []
    assert [artifact.tool_name for artifact in result.artifacts] == [
        "CompareAwareBridge",
        "CompareAwareBridgeValidation",
    ]
    assert result.metadata["completed_stage"] == "bridge"


def test_compare_aware_strategy_stops_after_guided_pool_progress(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")

    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: {
            "pairscan_path": str(tmp_path / "pairscan_summary.json"),
            "bridge_result_path": str(tmp_path / BRIDGE_RESULT_FILE_NAME),
            "bridge_validation_path": str(tmp_path / "bridge_validation.json"),
            "bridge_entries": [],
            "bridge_validations": [],
            "hot_positions": [0, 1, 2],
            "hot_nibbles": [0, 1, 2, 3, 4],
        },
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_guided_pool",
        lambda **kwargs: {
            "guided_pool_result_path": str(tmp_path / "guided_pool_result.json"),
            "guided_pool_validation_path": str(tmp_path / "guided_pool_validation.json"),
            "guided_entries": [
                {
                    "stage": "guided_pool",
                    "base_anchor": "78d540b49c590770",
                    "positions_or_nibbles": [0, 1, 2, 3, 4],
                    "candidate_hex": "7883401f9c59077041414141414141",
                    "cand8_hex": "7883401f9c590770",
                    "raw_prefix_hex": "46003e1dfd2bb62a3d09",
                    "raw_prefix_hex_64": "46003e1dfd2bb62a3d09",
                    "ci_exact_wchars": 3,
                    "ci_distance5": 120,
                    "raw_distance10": 30,
                }
            ],
            "guided_validations": [
                {
                    "candidate_hex": "7883401f9c59077041414141414141",
                    "cand8_hex": "7883401f9c590770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 3,
                    "runtime_ci_distance5": 120,
                    "compare_summary": "guided pool ok",
                }
            ],
            "positions": [0, 1, 2, 3, 4],
            "value_pools": {"0": [0x78], "1": [0x83]},
            "beam_limit": 16,
        },
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_refine",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("refine should be skipped")),
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_smt",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("smt should be skipped")),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
    )

    assert [artifact.tool_name for artifact in result.artifacts] == [
        "CompareAwareBridge",
        "CompareAwareBridgeValidation",
        "CompareAwareGuidedPool",
        "CompareAwareGuidedPoolValidation",
    ]
    assert result.metadata["completed_stage"] == "guided_pool"


def test_compare_aware_strategy_runs_refine_then_smt_and_uses_promoted_anchors(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: {
            "pairscan_path": str(tmp_path / "pairscan_summary.json"),
            "bridge_result_path": str(tmp_path / BRIDGE_RESULT_FILE_NAME),
            "bridge_validation_path": str(tmp_path / "bridge_validation.json"),
            "bridge_entries": [
                {
                    "stage": "triad",
                    "base_anchor": "78d540b49c590770",
                    "positions_or_nibbles": [1, 3, 4],
                    "candidate_hex": "789d40b49c31077041414141414141",
                    "cand8_hex": "789d40b49c310770",
                    "raw_prefix_hex": "6600439ab22150168897",
                    "exact": 2,
                    "dist4": 50,
                    "dist6": 80,
                    "dist10": 120,
                    "ci_exact_wchars": 2,
                    "ci_distance5": 260,
                    "raw_distance10": 120,
                }
            ],
            "bridge_validations": [
                {
                    "candidate_hex": "789d40b49c31077041414141414141",
                    "cand8_hex": "789d40b49c310770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 260,
                    "compare_summary": "bridge no progress",
                }
            ],
            "hot_positions": [1, 3, 4],
            "hot_nibbles": [2, 3, 6, 7, 10],
        },
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_guided_pool",
        lambda **kwargs: {
            "guided_pool_result_path": str(tmp_path / "guided_pool_result.json"),
            "guided_pool_validation_path": str(tmp_path / "guided_pool_validation.json"),
            "guided_entries": [
                {
                    "stage": "guided_pool",
                    "base_anchor": "78d540b49c590770",
                    "positions_or_nibbles": [0, 1, 2, 3, 4],
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "raw_prefix_hex": "46006c004464830d311c",
                    "raw_prefix_hex_64": "46006c004464830d311c",
                    "ci_exact_wchars": 2,
                    "ci_distance5": 246,
                    "raw_distance10": 304,
                }
            ],
            "guided_validations": [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "compare_summary": "guided plateau",
                }
            ],
            "positions": [0, 1, 2, 3, 4],
            "value_pools": {"0": [0x78]},
            "beam_limit": 16,
        },
    )

    def fake_run_compare_aware_refine(
        *,
        artifacts_dir: Path,
        search_budget: int,
        seed: int,
        anchors: list[str],
        snapshot_interval: int,
        log,
    ) -> Path:
        _ = search_budget, seed, snapshot_interval, log
        captured["refine_anchors"] = anchors
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / RESULT_FILE_NAME
        out.write_text(
            json.dumps(
                {
                    "best": {
                        "candidate_hex": "78d540b49c59077041414141414141",
                        "cand8_hex": "78d540b49c590770",
                        "raw_prefix_hex": "46006c004464830d311c",
                        "ci_exact_wchars": 2,
                        "ci_distance5": 246,
                        "raw_distance10": 304,
                    },
                    "top_entries": [
                        {
                            "candidate_hex": "78d540b49c59077041414141414141",
                            "cand8_hex": "78d540b49c590770",
                            "raw_prefix_hex": "46006c004464830d311c",
                            "ci_exact_wchars": 2,
                            "ci_distance5": 246,
                            "raw_distance10": 304,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return out

    def fake_validate_compare_aware_results(
        *,
        target: Path,
        artifacts_dir: Path,
        result_path: Path,
        transform_model: SamplereverseTransformModel,
        validate_top: int,
        per_probe_timeout: float,
        log,
        output_file_name: str = VALIDATION_FILE_NAME,
        compare_output_prefix: str = "samplereverse_compare_aware_compare",
    ) -> tuple[Path, list[dict[str, object]]]:
        _ = target, artifacts_dir, transform_model, validate_top, per_probe_timeout, log, compare_output_prefix
        out = result_path.parent / output_file_name
        validations = [
            {
                "candidate_hex": "78d540b49c59077041414141414141",
                "cand8_hex": "78d540b49c590770",
                "compare_semantics_agree": True,
                "runtime_ci_exact_wchars": 2,
                "runtime_ci_distance5": 246,
                "compare_summary": "refine plateau",
            }
        ]
        out.write_text(json.dumps({"validations": validations}, ensure_ascii=False), encoding="utf-8")
        return out, validations

    def fake_run_compare_aware_smt(**kwargs):
        captured["smt_base"] = kwargs["base_entry"]["cand8_hex"]
        return {
            "result_path": str(tmp_path / "smt_result.json"),
            "validation_path": str(tmp_path / "smt_validation.json"),
            "entry": {
                "stage": "smt",
                "base_anchor": "78d540b49c590770",
                "positions_or_nibbles": [1, 3, 4],
                "candidate_hex": "78d540b49c59077041414141414141",
                "cand8_hex": "78d540b49c590770",
                "raw_prefix_hex": "46006c004464830d311c",
                "exact": 2,
                "dist4": 50,
                "dist6": 80,
                "dist10": 120,
                "ci_exact_wchars": 2,
                "ci_distance5": 246,
                "raw_distance10": 304,
            },
            "validations": [],
            "payload": {
                "summary": "smt attempted",
                "variable_byte_positions": [1, 3, 4],
                "variable_nibble_positions": [2, 3, 6],
            },
        }

    monkeypatch.setattr(compare_aware_search, "run_compare_aware_refine", fake_run_compare_aware_refine)
    monkeypatch.setattr(compare_aware_search, "validate_compare_aware_results", fake_validate_compare_aware_results)
    monkeypatch.setattr(compare_aware_search, "run_compare_aware_smt", fake_run_compare_aware_smt)

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
    )

    assert captured["refine_anchors"] == [
        "78d540b49c590770",
        "789d40b49c310770",
        "95a3f65dcedb6290",
    ]
    assert captured["smt_base"] == "78d540b49c590770"
    assert result.metadata["completed_stage"] in {
        "transform_trace_consistency",
        "dynamic_compare_path_probe",
        "pre_rc4_material_probe",
        "base64_rc4_static_point_discovery",
        "base64_rc4_breakpoint_probe",
        "compare_stack_pivot_probe",
        "compare_handoff_probe",
            "compare_handoff_slice_probe",
            "compare_handoff_return_site_probe",
            "compare_producer_trace_probe",
            "compare_producer_material_confirmation",
            "function_semantic_audit",
            "material_hook_runtime_validation",
            "post_handoff_branch_outcome_audit",
            "compare_lhs_producer_audit",
            "compare_lhs_upstream_writer_audit",
            "compare_real_lhs_provenance_audit",
            "compare_esi_source_window_audit",
            "compare_lhs_slot_writer_source_audit",
            "compare_lhs_slot_writer_predecessor_audit",
            "post_handoff_exception_unwind_audit",
            "h1_h3_boundary_validation",
        }
    assert result.metadata["smt"]["payload"]["exact2_basin_smt"]["base_anchor"] == "78d540b49c590770"
    assert result.metadata["transform_trace_consistency"]["payload"]["classification"] in {
        "transform_model_confirmed",
        "evidence_insufficient",
        "transform_mismatch_found",
    }
    if result.metadata["h1_h3_boundary_validation"]:
        assert result.metadata["h1_h3_boundary_validation"]["payload"]["classification"] in {
            "h1_h3_boundary_contrast_exhausted_no_gain",
            "h1_h3_boundary_contrast_improved",
        }
    smt_payload = json.loads((tmp_path / "smt_result.json").read_text(encoding="utf-8"))
    assert smt_payload["exact2_basin_smt"]["base_anchor"] == "78d540b49c590770"
    assert smt_payload["exact2_basin_smt"]["prefix_boundary"]["ci_exact_wchars"] == 2
    assert any(artifact.tool_name == "CompareAwareSMT" for artifact in result.artifacts)


def test_guided_pool_uses_bounded_single_byte_pools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    captured: dict[str, object] = {}

    def fake_top_compare_aware_single_byte_entries(*, base_anchor, positions, transform_model, top_k=12):
        _ = transform_model
        base_bytes = bytes.fromhex(base_anchor)
        captured["positions"] = list(positions)
        captured["top_k"] = top_k
        return {
            pos: [
                {
                    "candidate_hex": bytes(base_bytes).hex() + "41414141414141",
                    "cand8_hex": bytes(base_bytes).hex(),
                    "mutated_position": pos,
                    "mutated_byte_value": base_bytes[pos],
                    "ci_exact_wchars": 2,
                    "ci_distance5": 246,
                    "raw_distance10": 304,
                    "wide_ascii_contiguous_16": 2,
                    "wide_ascii_total_16": 2,
                    "wide_zero_high_pairs_16": 2,
                    "flaglike_tail_pairs_16": 0,
                },
                {
                    "candidate_hex": (
                        bytes(base_bytes[:pos] + bytes([(base_bytes[pos] + 1) & 0xFF]) + base_bytes[pos + 1 :]).hex()
                        + "41414141414141"
                    ),
                    "cand8_hex": bytes(base_bytes[:pos] + bytes([(base_bytes[pos] + 1) & 0xFF]) + base_bytes[pos + 1 :]).hex(),
                    "mutated_position": pos,
                    "mutated_byte_value": (base_bytes[pos] + 1) & 0xFF,
                    "ci_exact_wchars": 1,
                    "ci_distance5": 300 + pos,
                    "raw_distance10": 320 + pos,
                    "wide_ascii_contiguous_16": 1,
                    "wide_ascii_total_16": 1,
                    "wide_zero_high_pairs_16": 1,
                    "flaglike_tail_pairs_16": 0,
                },
            ]
            for pos in positions
        }

    def fake_validate_compare_aware_results(**kwargs):
        out = Path(kwargs["artifacts_dir"]) / VALIDATION_FILE_NAME
        validations: list[dict[str, object]] = []
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"validations": validations}), encoding="utf-8")
        return out, validations

    monkeypatch.setattr(
        compare_aware_search,
        "_top_compare_aware_single_byte_entries",
        fake_top_compare_aware_single_byte_entries,
    )
    monkeypatch.setattr(compare_aware_search, "validate_compare_aware_results", fake_validate_compare_aware_results)

    result = compare_aware_search.run_compare_aware_guided_pool(
        target=target,
        artifacts_dir=tmp_path / "guided_pool",
        base_anchor="78d540b49c590770",
        bridge_entries=[
            {"candidate_hex": "789940b49c59077041414141414141"},
            {"candidate_hex": "78d541b49c59077041414141414141"},
            {"candidate_hex": "78d540b59c59077041414141414141"},
        ],
        transform_model=SamplereverseTransformModel(),
        validate_top=1,
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    assert captured["top_k"] == GUIDED_POOL_TOP_VALUES
    assert captured["positions"] == list(range(8))
    assert all(0 <= pos < 5 for pos in result["positions"])
    assert len(result["positions"]) <= 5
    assert Path(result["guided_pool_result_path"]).exists()


def test_guided_pool_beam_entries_keeps_small_exploration_tail() -> None:
    transform_model = SamplereverseTransformModel()
    candidates = [
        {
            "candidate_hex": "78d540b49c59077041414141414141",
            "raw_prefix_hex_64": "66006c00610067007b00",
            "raw_prefix_hex": "66006c00610067007b00",
            "ci_exact_wchars": 2,
            "ci_distance5": 246,
            "raw_distance10": 304,
            "wide_ascii_contiguous_16": 2,
            "wide_ascii_total_16": 2,
            "wide_zero_high_pairs_16": 2,
            "flaglike_tail_pairs_16": 0,
        },
        {
            "candidate_hex": "78d540b49c59077141414141414141",
            "raw_prefix_hex_64": "46006c00440000000000",
            "raw_prefix_hex": "46006c00440000000000",
            "ci_exact_wchars": 0,
            "ci_distance5": 250,
            "raw_distance10": 280,
            "wide_ascii_contiguous_16": 1,
            "wide_ascii_total_16": 1,
            "wide_zero_high_pairs_16": 1,
            "flaglike_tail_pairs_16": 0,
        },
        {
            "candidate_hex": "78d540b49c59077241414141414141",
            "raw_prefix_hex_64": "46006c00450000000000",
            "raw_prefix_hex": "46006c00450000000000",
            "ci_exact_wchars": 0,
            "ci_distance5": 255,
            "raw_distance10": 281,
            "wide_ascii_contiguous_16": 1,
            "wide_ascii_total_16": 1,
            "wide_zero_high_pairs_16": 1,
            "flaglike_tail_pairs_16": 0,
        },
    ]

    beam, stats = _guided_pool_beam_entries(
        candidates=candidates,
        transform_model=transform_model,
        exact_floor=1,
        anchor_mode=FRONTIER_ANCHOR_MODE,
        exploration_slots=GUIDED_POOL_EXPLORATION_SLOTS,
    )

    assert beam[0]["candidate_hex"] == "78d540b49c59077041414141414141"
    assert len(beam) == 3
    assert stats["primary_kept"] == 1
    assert stats["exploratory_kept"] == 2
    assert stats["floor_matched"] == 1


def test_frontier_anchor_candidates_keep_exact2_exact1_exact0_representatives() -> None:
    validations = [
        {
            "candidate_hex": "78d540b49c59077041414141414141",
            "cand8_hex": "78d540b49c590770",
            "runtime_ci_exact_wchars": 2,
            "runtime_ci_distance5": 246,
            "compare_semantics_agree": True,
        },
        {
            "candidate_hex": "95a3f65dcedb629041414141414141",
            "cand8_hex": "95a3f65dcedb6290",
            "runtime_ci_exact_wchars": 1,
            "runtime_ci_distance5": 305,
            "compare_semantics_agree": True,
        },
        {
            "candidate_hex": "a47a0a74bd35355041414141414141",
            "cand8_hex": "a47a0a74bd353550",
            "runtime_ci_exact_wchars": 0,
            "runtime_ci_distance5": 208,
            "compare_semantics_agree": True,
        },
    ]

    anchors = _frontier_anchor_candidates(validations)

    assert anchors == [
        {
            "anchor": "78d540b49c590770",
            "frontier_role": "exact2_seed",
            "candidate_hex": "78d540b49c59077041414141414141",
            "runtime_ci_exact_wchars": 2,
            "runtime_ci_distance5": 246,
            "compare_semantics_agree": True,
            "source_anchor": "78d540b49c590770",
            "anchor_mode": "exact2",
            "frontier_submode": "",
            "anchor_lineage": "exact2_seed(78d540b49c590770)",
        },
        {
            "anchor": "95a3f65dcedb6290",
            "frontier_role": "exact1_frontier",
            "candidate_hex": "95a3f65dcedb629041414141414141",
            "runtime_ci_exact_wchars": 1,
            "runtime_ci_distance5": 305,
            "compare_semantics_agree": True,
            "source_anchor": "95a3f65dcedb6290",
            "anchor_mode": "frontier",
            "frontier_submode": FRONTIER_EXACT1_SUBMODE,
            "anchor_lineage": "exact1_frontier(95a3f65dcedb6290)",
        },
        {
            "anchor": "a47a0a74bd353550",
            "frontier_role": "exact0_frontier",
            "candidate_hex": "a47a0a74bd35355041414141414141",
            "runtime_ci_exact_wchars": 0,
            "runtime_ci_distance5": 208,
            "compare_semantics_agree": True,
            "source_anchor": "a47a0a74bd353550",
            "anchor_mode": "frontier",
            "frontier_submode": FRONTIER_EXACT0_SUBMODE,
            "anchor_lineage": "exact0_frontier(a47a0a74bd353550)",
        },
    ]


def test_collect_frontier_promoted_anchors_uses_context_lineage() -> None:
    validations = [
        {
            "candidate_hex": "a47a0a74bd35355041414141414141",
            "cand8_hex": "a47a0a74bd353550",
            "runtime_ci_exact_wchars": 0,
            "runtime_ci_distance5": 208,
            "compare_semantics_agree": True,
        }
    ]

    anchors = _collect_frontier_promoted_anchors(
        validations,
        context_entries=[
            {
                "candidate_hex": "a47a0a74bd35355041414141414141",
                "cand8_hex": "a47a0a74bd353550",
                "source_anchor": "f649b64b5e97dbd0",
                "anchor_mode": "frontier",
                "anchor_lineage": "exact0_frontier(f649b64b5e97dbd0) -> refine(frontier)",
            }
        ],
    )

    assert anchors[0]["source_anchor"] == "f649b64b5e97dbd0"
    assert anchors[0]["anchor_lineage"] == "exact0_frontier(f649b64b5e97dbd0) -> refine(frontier)"
    assert anchors[0]["frontier_submode"] == FRONTIER_EXACT0_SUBMODE


def test_annotate_frontier_improvement_gate_marks_only_strict_distance_or_raw_improvement() -> None:
    annotated = _annotate_frontier_improvement_gate(
        [
            {"candidate_hex": "a" * 30, "ci_distance5": 200, "raw_distance10": 260},
            {"candidate_hex": "b" * 30, "ci_distance5": 210, "raw_distance10": 250},
            {"candidate_hex": "c" * 30, "ci_distance5": 210, "raw_distance10": 280},
        ],
        baseline_entry={"ci_distance5": 210, "raw_distance10": 270},
    )

    assert [item["improvement_gate_passed"] for item in annotated] == [True, True, False]


def test_annotate_frontier_improvement_gate_allows_exact1_raw_improvement_without_exact_regression() -> None:
    annotated = _annotate_frontier_improvement_gate(
        [
            {"candidate_hex": "a" * 30, "ci_distance5": 258, "raw_distance10": 300, "ci_exact_wchars": 1},
            {"candidate_hex": "b" * 30, "ci_distance5": 258, "raw_distance10": 300, "ci_exact_wchars": 0},
        ],
        baseline_entry={"ci_distance5": 258, "raw_distance10": 310, "ci_exact_wchars": 1},
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
    )

    assert [item["improvement_gate_passed"] for item in annotated] == [True, False]


def test_feedback_value_pools_merge_improved_pair_and_triad_values() -> None:
    pools, sources = _feedback_value_pools_from_frontier_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1, 2],
        position_profiles={
            0: [{"mutated_byte_value": 0x11}, {"mutated_byte_value": 0x22}],
            1: [{"mutated_byte_value": 0x33}],
            2: [{"mutated_byte_value": 0x44}],
        },
        pair_frontier_pool=[
            {
                "pair_positions": [0, 1],
                "pair_values": [0x99, 0x88],
                "improvement_gate_passed": True,
            },
            {
                "pair_positions": [0, 2],
                "pair_values": [0x99, 0x77],
                "improvement_gate_passed": True,
            },
        ],
        triad_frontier_pool=[
            {
                "pair_positions": [0, 1],
                "pair_values": [0x99, 0x88],
                "triad_positions": [0, 1, 2],
                "triad_value": 0x66,
                "improvement_gate_passed": True,
            }
        ],
        incoming_feedback_value_pools={1: [0x55]},
        frontier_submode=FRONTIER_EXACT0_SUBMODE,
    )

    assert pools[0][:4] == [0x5A, 0x11, 0x22, 0x99]
    assert 0x55 in pools[1]
    assert 0x66 in pools[2]
    assert sources["1"]["incoming_feedback"] == [0x55]
    assert sources["0"]["improved_pair_values"] == [0x99]
    assert sources["2"]["improved_triad_values"] == [0x66]


def test_feedback_value_pools_exact1_ignores_incoming_feedback_and_keeps_small_perturbations() -> None:
    pools, sources = _feedback_value_pools_from_frontier_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1],
        position_profiles={
            0: [{"mutated_byte_value": 0x11}, {"mutated_byte_value": 0x22}, {"mutated_byte_value": 0x33}],
            1: [{"mutated_byte_value": 0x44}],
        },
        pair_frontier_pool=[
            {
                "pair_positions": [0, 1],
                "pair_values": [0x99, 0x88],
                "improvement_gate_passed": True,
            }
        ],
        triad_frontier_pool=[],
        incoming_feedback_value_pools={0: [0xEE], 1: [0xDD]},
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
    )

    assert 0xEE not in pools[0]
    assert 0xDD not in pools[1]
    assert 0x99 in pools[0]
    assert sources["0"]["incoming_feedback"] == []
    assert sources["0"]["small_perturbation_values"][:3] == [0x5A, 0x59, 0x5B]


def test_mine_exact1_lineage_value_sources_prefers_exact1_lineage_and_source_diff() -> None:
    values, counts, origins, summary = _mine_exact1_lineage_value_sources(
        base_anchor="5a3e7f46ddd474d0",
        source_anchor="78d540b49c590770",
        positions=[0, 1, 2],
        transform_model=SamplereverseTransformModel(),
        lineage_entries=[
            {
                "candidate_hex": "5a997f46ddd474d041414141414141",
                "cand8_hex": "5a997f46ddd474d0",
                "ci_exact_wchars": 1,
                "source_anchor": "78d540b49c590770",
                "frontier_submode": FRONTIER_EXACT1_SUBMODE,
            },
            {
                "candidate_hex": "88997f46ddd474d041414141414141",
                "cand8_hex": "88997f46ddd474d0",
                "ci_exact_wchars": 0,
                "source_anchor": "78d540b49c590770",
                "frontier_submode": FRONTIER_EXACT0_SUBMODE,
            },
        ],
    )

    assert values[0][0] == 0x78
    assert 0x99 in values[1]
    assert 0x88 not in values[0]
    assert counts[1][0x99] >= 1
    assert "source_anchor_diff" in origins[0]
    assert summary["positions"]["1"]["values"]


def test_exact1_neighbor_value_maps_projects_distant_sources_into_local_candidates() -> None:
    projection_details: dict[str, object] = {}
    preserve, escape = compare_aware_search._exact1_neighbor_value_maps(
        base_value=0x5A,
        profile_values=[0x33],
        incoming_values=[0x99],
        lineage_values=[0x78, 0x51],
        projection_details=projection_details,
    )

    assert 0x78 not in escape
    assert 0x99 not in escape
    assert 0x59 in escape
    assert any(origin.endswith("_projected") for origin in escape[0x59])
    assert 0x5C in escape
    assert any(origin.endswith("_projected") for origin in escape[0x5C])
    assert 0x78 in projection_details["raw_source_present_but_too_far"]
    assert 0x99 in projection_details["raw_source_present_but_too_far"]
    assert sorted(projection_details["projected_values"]) == [0x58, 0x59, 0x5B, 0x5C]
    assert projection_details["projected_direction"]["92"] == "positive_projection"
    assert projection_details["projected_step"]["92"] == 2
    assert "lineage_projected" in projection_details["projected_origins"]["92"]


def test_top_compare_aware_pair_entries_exact1_respects_locked_pairs_and_feedback_values() -> None:
    pair_profiles, generation_details = compare_aware_search._top_compare_aware_pair_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1, 2, 3],
        position_profiles={
            0: [{"mutated_byte_value": 0x33}],
            1: [{"mutated_byte_value": 0x18}],
            2: [{"mutated_byte_value": 0x75}],
            3: [{"mutated_byte_value": 0x8F}],
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        locked_pair_positions=[(0, 1), (1, 3)],
        incoming_feedback_value_pools={0: [0x99], 1: [0x88]},
        lineage_value_pools={0: [0x78, 0x51], 1: [0xD5, 0x99], 3: [0x07]},
        lineage_value_counts={0: {0x78: 2}, 1: {0xD5: 1}},
        lineage_value_origins={0: ["source_anchor_diff"], 1: ["lineage_context"], 3: ["recent_payload"]},
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
        },
        top_per_pair=2,
    )

    assert set(pair_profiles.keys()) == {(0, 1), (1, 3)}
    assert all(entry["pair_positions"] == [0, 1] for entry in pair_profiles[(0, 1)])
    assert all(entry["pair_positions"] == [1, 3] for entry in pair_profiles[(1, 3)])
    assert generation_details["pair_escape_mode"] == "exact1_dual_lane"
    assert "0,1" in generation_details["pair_preserve_pool"]
    assert generation_details["pair_escape_pool_strategy"] == "exact1_local_neighbors"
    assert generation_details["pair_escape_source_values"]["0,1"]["0"][0] == 0x78
    assert "source_anchor_diff" in generation_details["pair_escape_source_origins"]["0,1"]["0"]
    assert generation_details["pair_escape_source_projected_values"]["0,1"]["0"] == [0x59, 0x58, 0x5B, 0x5C]
    assert "lineage_projected" in generation_details["pair_escape_source_projected_origins"]["0,1"]["0"]["92"]
    assert 0x78 in generation_details["pair_escape_source_reject_reasons"]["0,1"]["0"]["raw_source_present_but_too_far"]
    assert generation_details["lineage_projection_summary"]["0,1"]["0"]["projected_local_value_generated"]
    assert generation_details["pair_escape_source_projected_direction"]["0,1"]["0"]["92"] == "positive_projection"
    assert generation_details["pair_escape_source_projected_step"]["0,1"]["0"]["92"] == 2
    assert 0x33 not in generation_details["pair_escape_pool"]["0,1"]["0"]
    assert 0x18 not in generation_details["pair_escape_pool"]["0,1"]["1"]
    assert all(
        abs(int(value) - 0x5A) <= compare_aware_search.EXACT1_ESCAPE_NEIGHBOR_RADIUS
        for value in generation_details["pair_escape_pool"]["0,1"]["0"]
    )
    assert generation_details["pair_neighbor_generation_summary"]["0,1"]["escape_neighbor_mode"] == "escape_neighbors"


def test_top_compare_aware_pair_entries_exact1_pair_local_sources_do_not_share_values() -> None:
    _, generation_details = compare_aware_search._top_compare_aware_pair_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1, 2, 3],
        position_profiles={0: [], 1: [], 2: [], 3: []},
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        locked_pair_positions=[(0, 1), (0, 3)],
        incoming_feedback_value_pools={},
        lineage_value_pools={0: [0x78], 1: [], 3: [0x07]},
        lineage_value_counts={0: {0x78: 1}, 3: {0x07: 1}},
        lineage_value_origins={0: ["source_anchor_diff"], 3: ["recent_payload"]},
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
        },
    )

    assert generation_details["pair_escape_source_values"]["0,1"]["1"] == []
    assert generation_details["pair_escape_source_values"]["0,3"]["3"] == [0x07]


def test_top_compare_aware_pair_entries_exact1_keeps_escape_lane_in_pair_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_exact1_neighbor_value_maps",
        lambda *, base_value, profile_values, incoming_values, lineage_values: (
            {int(base_value) & 0xFF: ["anchor"]},
            {0x5A: ["anchor"], 0x3B: ["escape_neighbor"]}
            if (int(base_value) & 0xFF) == 0x3E
            else {int(base_value) & 0xFF: ["anchor"]},
        ),
    )

    def fake_eval(candidate_hex: str, transform_model) -> dict[str, object]:
        cand8 = candidate_hex[:16]
        second_byte = int(cand8[2:4], 16)
        if cand8 == "5a3e7f46ddd474d0":
            return {
                "candidate_hex": candidate_hex,
                "cand8_hex": cand8,
                "ci_exact_wchars": 1,
                "ci_distance5": 258,
                "raw_distance10": 290,
                "pair_wide_ascii_contiguous_8": 1,
                "pair_wide_zero_high_pairs_8": 1,
                "pair_flaglike_tail_pairs_8": 0,
            }
        if second_byte == 0x3B:
            return {
                "candidate_hex": candidate_hex,
                "cand8_hex": cand8,
                "ci_exact_wchars": 0,
                "ci_distance5": 252,
                "raw_distance10": 282,
                "pair_wide_ascii_contiguous_8": 2,
                "pair_wide_zero_high_pairs_8": 2,
                "pair_flaglike_tail_pairs_8": 1,
            }
        return {
            "candidate_hex": candidate_hex,
            "cand8_hex": cand8,
            "ci_exact_wchars": 0,
            "ci_distance5": 300,
            "raw_distance10": 320,
            "pair_wide_ascii_contiguous_8": 0,
            "pair_wide_zero_high_pairs_8": 0,
            "pair_flaglike_tail_pairs_8": 0,
        }

    monkeypatch.setattr(compare_aware_search, "_evaluate_candidate_hex", fake_eval)

    pair_profiles, generation_details = compare_aware_search._top_compare_aware_pair_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1],
        position_profiles={0: [], 1: []},
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        locked_pair_positions=[(0, 1)],
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        top_per_pair=2,
    )

    kept_escape = generation_details["pair_profile_kept_escape"]["0,1"]
    assert kept_escape
    assert kept_escape[0]["cand8_hex"] == "5a3b7f46ddd474d0"
    assert kept_escape[0]["pair_candidate_origin"] == "exact1_escape_neighbors"
    assert kept_escape[0]["pair_neighbor_mode"] == "escape_neighbors"
    assert kept_escape[0]["pair_mutation_radius"] <= compare_aware_search.EXACT1_ESCAPE_NEIGHBOR_RADIUS
    assert kept_escape[0]["pair_value_origin_by_pos"]["1"] == ["escape_neighbor"]
    assert any(entry["pair_escape_mode"] == "escape" for entry in pair_profiles[(0, 1)])
    assert generation_details["pair_profile_drop_reasons"]["0,1"]["escape"] == "profile_kept"


def test_top_compare_aware_pair_entries_exact1_soft_guard_promotes_one_low_radius_value(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_exact1_neighbor_value_maps",
        lambda *, base_value, profile_values, incoming_values, lineage_values: (
            {int(base_value) & 0xFF: ["anchor"]},
            {int(base_value) & 0xFF: ["anchor"], (int(base_value) + 2) & 0xFF: ["soft"], (int(base_value) + 3) & 0xFF: ["soft2"]},
        ),
    )

    def fake_eval(candidate_hex: str, transform_model) -> dict[str, object]:
        cand8 = candidate_hex[:16]
        return {
            "candidate_hex": candidate_hex,
            "cand8_hex": cand8,
            "ci_exact_wchars": 0 if cand8 != "5a3e7f46ddd474d0" else 1,
            "ci_distance5": 500,
            "raw_distance10": 520,
            "pair_wide_ascii_contiguous_8": 0,
            "pair_wide_zero_high_pairs_8": 0,
            "pair_flaglike_tail_pairs_8": 0,
        }

    monkeypatch.setattr(compare_aware_search, "_evaluate_candidate_hex", fake_eval)

    pair_profiles, generation_details = compare_aware_search._top_compare_aware_pair_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1],
        position_profiles={0: [], 1: []},
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        locked_pair_positions=[(0, 1)],
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        top_per_pair=4,
    )

    guard = generation_details["pair_single_byte_guard_status_counts"]["0,1"]
    assert guard["0"]["guard_soft_rejected"] >= 1
    assert generation_details["pair_guard_soft_promoted_values"]["0,1"]["0"] == [0x5C]
    assert generation_details["pair_guard_nonbase_starved"]["0,1"]["0"] is False
    assert generation_details["pair_guard_soft_quality_band"]["0,1"]["0"]["92"] == "distance_explosive_soft"
    assert generation_details["pair_guard_soft_distance_delta"]["0,1"]["0"]["92"] == 242
    assert generation_details["pair_guard_soft_raw_delta"]["0,1"]["0"]["92"] == 230
    assert generation_details["pair_guard_soft_structure_delta"]["0,1"]["0"]["92"] == [-1, -1, 0, 0, 0, 0]
    assert 0x5C in generation_details["pair_escape_pool"]["0,1"]["0"]
    assert any(0x5C in entry["pair_values"] for entry in generation_details["pair_profile_escape_entries"]["0,1"])
    assert any(entry["pair_escape_mode"] == "escape" for entry in pair_profiles[(0, 1)])


def test_top_compare_aware_pair_entries_exact1_soft_guard_prefers_better_quality_over_smaller_radius(monkeypatch) -> None:
    def fake_maps(*, base_value, profile_values, incoming_values, lineage_values):
        base = int(base_value) & 0xFF
        if base == 0x5A:
            return (
                {base: ["anchor"]},
                {
                    base: ["anchor"],
                    (base + 2) & 0xFF: ["escape_neighbor"],
                    (base + 4) & 0xFF: ["escape_neighbor"],
                },
            )
        return ({base: ["anchor"]}, {base: ["anchor"]})

    monkeypatch.setattr(compare_aware_search, "_exact1_neighbor_value_maps", fake_maps)

    def fake_eval(candidate_hex: str, transform_model) -> dict[str, object]:
        cand8 = candidate_hex[:16]
        left = int(cand8[:2], 16)
        if left == 0x5C:
            distance = 520
            raw = 540
            pair_rank = (0, 0, 0)
        elif left == 0x5E:
            distance = 380
            raw = 400
            pair_rank = (1, 1, 0)
        else:
            distance = 500
            raw = 520
            pair_rank = (0, 0, 0)
        return {
            "candidate_hex": candidate_hex,
            "cand8_hex": cand8,
            "ci_exact_wchars": 0 if cand8 != "5a3e7f46ddd474d0" else 1,
            "ci_distance5": distance,
            "raw_distance10": raw,
            "pair_wide_ascii_contiguous_8": pair_rank[0],
            "pair_wide_zero_high_pairs_8": pair_rank[1],
            "pair_flaglike_tail_pairs_8": pair_rank[2],
        }

    monkeypatch.setattr(compare_aware_search, "_evaluate_candidate_hex", fake_eval)

    pair_profiles, generation_details = compare_aware_search._top_compare_aware_pair_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1],
        position_profiles={0: [], 1: []},
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        locked_pair_positions=[(0, 1)],
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        top_per_pair=4,
    )

    assert generation_details["pair_guard_soft_promoted_values"]["0,1"]["0"] == [0x5E]
    assert generation_details["pair_guard_soft_quality_band"]["0,1"]["0"]["94"] == "local_compatible_soft"
    assert generation_details["pair_guard_soft_quality_band"]["0,1"]["0"]["92"] == "distance_explosive_soft"
    ranked = generation_details["pair_guard_soft_rank_summary"]["0,1"]["0"]
    assert ranked[0]["value"] == 0x5E
    assert ranked[0]["quality_band"] == "local_compatible_soft"
    assert any(entry["pair_values"][0] == 0x5E for entry in generation_details["pair_profile_escape_entries"]["0,1"])
    assert any(entry["pair_values"][0] == 0x5E for entry in pair_profiles[(0, 1)])


def test_top_compare_aware_pair_entries_exact1_soft_guard_prefers_projected_origin_over_escape_neighbor(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_exact1_neighbor_value_maps",
        lambda *, base_value, profile_values, incoming_values, lineage_values: (
            {int(base_value) & 0xFF: ["anchor"]},
            (
                {
                    int(base_value) & 0xFF: ["anchor"],
                    (int(base_value) - 3) & 0xFF: ["escape_neighbor"],
                    (int(base_value) + 3) & 0xFF: ["lineage_projected"],
                }
                if (int(base_value) & 0xFF) == 0x5A
                else {int(base_value) & 0xFF: ["anchor"]}
            ),
        ),
    )

    def fake_eval(candidate_hex: str, transform_model) -> dict[str, object]:
        cand8 = candidate_hex[:16]
        left = int(cand8[:2], 16)
        if left in {0x57, 0x5D}:
            distance = 430
            raw = 450
            pair_rank = (0, 1, 0)
        else:
            distance = 500
            raw = 520
            pair_rank = (0, 0, 0)
        return {
            "candidate_hex": candidate_hex,
            "cand8_hex": cand8,
            "ci_exact_wchars": 0 if cand8 != "5a3e7f46ddd474d0" else 1,
            "ci_distance5": distance,
            "raw_distance10": raw,
            "pair_wide_ascii_contiguous_8": pair_rank[0],
            "pair_wide_zero_high_pairs_8": pair_rank[1],
            "pair_flaglike_tail_pairs_8": pair_rank[2],
        }

    monkeypatch.setattr(compare_aware_search, "_evaluate_candidate_hex", fake_eval)

    _, generation_details = compare_aware_search._top_compare_aware_pair_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1],
        position_profiles={0: [], 1: []},
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        locked_pair_positions=[(0, 1)],
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        top_per_pair=4,
    )

    assert generation_details["pair_guard_soft_promoted_values"]["0,1"]["0"] == [0x5D]
    ranked = generation_details["pair_guard_soft_rank_summary"]["0,1"]["0"]
    assert ranked[0]["value"] == 0x5D
    assert ranked[0]["origins"] == ["lineage_projected"]


def test_top_compare_aware_pair_entries_exact1_projected_family_competition_prefers_best_projected_value(monkeypatch) -> None:
    def fake_maps(*, base_value, profile_values, incoming_values, lineage_values, projection_details=None):
        if projection_details is not None:
            projection_details.update(
                {
                    "raw_source_present_but_too_far": [0x20, 0xE0],
                    "projected_values": [0x59, 0x58, 0x5B, 0x5C],
                    "projected_origins": {
                        "89": ["lineage_projected"],
                        "88": ["lineage_projected"],
                        "91": ["lineage_projected"],
                        "92": ["lineage_projected"],
                    },
                    "projected_direction": {
                        "89": "negative_projection",
                        "88": "negative_projection",
                        "91": "positive_projection",
                        "92": "positive_projection",
                    },
                    "projected_step": {"89": 1, "88": 2, "91": 1, "92": 2},
                }
            )
        return (
            {int(base_value) & 0xFF: ["anchor"]},
            {
                int(base_value) & 0xFF: ["anchor"],
                0x59: ["lineage_projected"],
                0x58: ["lineage_projected"],
                0x5B: ["lineage_projected"],
                0x5C: ["lineage_projected"],
            },
        )

    monkeypatch.setattr(compare_aware_search, "_exact1_neighbor_value_maps_with_optional_details", fake_maps)

    def fake_eval(candidate_hex: str, transform_model) -> dict[str, object]:
        cand8 = candidate_hex[:16]
        left = int(cand8[:2], 16)
        mapping = {
            0x59: (330, 340, (1, 1, 0)),
            0x58: (390, 410, (0, 1, 0)),
            0x5B: (320, 330, (1, 1, 0)),
            0x5C: (420, 430, (0, 0, 0)),
        }
        distance, raw, pair_rank = mapping.get(left, (500, 520, (0, 0, 0)))
        return {
            "candidate_hex": candidate_hex,
            "cand8_hex": cand8,
            "ci_exact_wchars": 0 if cand8 != "5a3e7f46ddd474d0" else 1,
            "ci_distance5": distance,
            "raw_distance10": raw,
            "pair_wide_ascii_contiguous_8": pair_rank[0],
            "pair_wide_zero_high_pairs_8": pair_rank[1],
            "pair_flaglike_tail_pairs_8": pair_rank[2],
        }

    monkeypatch.setattr(compare_aware_search, "_evaluate_candidate_hex", fake_eval)

    _, generation_details = compare_aware_search._top_compare_aware_pair_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1],
        position_profiles={0: [], 1: []},
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        locked_pair_positions=[(0, 1)],
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        top_per_pair=4,
    )

    assert generation_details["pair_escape_source_projected_kept_values"]["0,1"]["0"] == [0x5B]
    assert generation_details["pair_escape_source_projected_dropped_values"]["0,1"]["0"] == [0x59, 0x58, 0x5C]
    assert generation_details["pair_escape_source_projected_quality_band"]["0,1"]["0"]["89"] == "projected_local_compatible"
    assert generation_details["pair_escape_source_projected_quality_band"]["0,1"]["0"]["92"] == "projected_distance_explosive"
    assert generation_details["pair_projected_competitive_status"]["0,1"]["0"] == "projected_beats_neighbor"
    assert generation_details["pair_projected_competitive_winner"]["0,1"]["0"]["value"] == 0x5B
    assert generation_details["pair_guard_soft_promoted_values"]["0,1"]["0"] == [0x5B]
    preserve_lane = generation_details["pair_projected_preserve_candidates"]["0,1"]
    assert preserve_lane
    assert preserve_lane[0]["pair_candidate_origin"] == "exact1_projected_preserve_lane"
    assert preserve_lane[0]["pair_projected_boundary_role"] == "projected_winner_with_base"


def test_top_compare_aware_pair_entries_exact1_projected_family_competition_reports_raw_loss(monkeypatch) -> None:
    def fake_maps(*, base_value, profile_values, incoming_values, lineage_values, projection_details=None):
        if projection_details is not None:
            projection_details.update(
                {
                    "raw_source_present_but_too_far": [0x20],
                    "projected_values": [0x5D],
                    "projected_origins": {"93": ["lineage_projected"]},
                    "projected_direction": {"93": "positive_projection"},
                    "projected_step": {"93": 1},
                }
            )
        base = int(base_value) & 0xFF
        return (
            {base: ["anchor"]},
            {
                base: ["anchor"],
                0x5D: ["lineage_projected"],
                0x57: ["escape_neighbor"],
            },
        )

    monkeypatch.setattr(compare_aware_search, "_exact1_neighbor_value_maps_with_optional_details", fake_maps)

    def fake_eval(candidate_hex: str, transform_model) -> dict[str, object]:
        cand8 = candidate_hex[:16]
        left = int(cand8[:2], 16)
        if left == 0x5D:
            distance = 420
            raw = 470
            pair_rank = (1, 1, 0)
        elif left == 0x57:
            distance = 420
            raw = 430
            pair_rank = (1, 1, 0)
        else:
            distance = 500
            raw = 520
            pair_rank = (0, 0, 0)
        return {
            "candidate_hex": candidate_hex,
            "cand8_hex": cand8,
            "ci_exact_wchars": 0 if cand8 != "5a3e7f46ddd474d0" else 1,
            "ci_distance5": distance,
            "raw_distance10": raw,
            "pair_wide_ascii_contiguous_8": pair_rank[0],
            "pair_wide_zero_high_pairs_8": pair_rank[1],
            "pair_flaglike_tail_pairs_8": pair_rank[2],
        }

    monkeypatch.setattr(compare_aware_search, "_evaluate_candidate_hex", fake_eval)

    _, generation_details = compare_aware_search._top_compare_aware_pair_entries(
        base_anchor="5a3e7f46ddd474d0",
        positions=[0, 1],
        position_profiles={0: [], 1: []},
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        locked_pair_positions=[(0, 1)],
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        top_per_pair=4,
    )

    assert generation_details["pair_projected_competitive_status"]["0,1"]["0"] == "projected_loses_on_raw"
    assert generation_details["pair_projected_blocked_by_neighbor"]["0,1"]["0"]["value"] == 0x57
    assert generation_details["pair_guard_soft_promoted_values"]["0,1"]["0"] == [0x57]


def test_diverse_pair_frontier_pool_exact1_drops_exact_regression_without_distance_escape(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    selected, drop_reasons, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 1): [
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "ci_exact_wchars": 1,
                    "ci_distance5": 258,
                    "raw_distance10": 290,
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x3E],
                },
                {
                    "candidate_hex": "333e7f46ddd474d041414141414141",
                    "cand8_hex": "333e7f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 258,
                    "raw_distance10": 280,
                    "pair_wide_ascii_contiguous_8": 0,
                    "pair_wide_zero_high_pairs_8": 0,
                    "pair_flaglike_tail_pairs_8": 0,
                    "pair_positions": [0, 1],
                    "pair_values": [0x33, 0x3E],
                },
                {
                    "candidate_hex": "5a187f46ddd474d041414141414141",
                    "cand8_hex": "5a187f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 230,
                    "raw_distance10": 260,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 2,
                    "pair_wide_zero_high_pairs_8": 2,
                    "pair_flaglike_tail_pairs_8": 1,
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x18],
                },
            ]
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        baseline_entry={
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        keep_limit=3,
    )

    assert any(entry["cand8_hex"] == "5a3e7f46ddd474d0" for entry in selected)
    assert any(entry["cand8_hex"] == "5a187f46ddd474d0" for entry in selected)
    assert all(entry["cand8_hex"] != "333e7f46ddd474d0" for entry in selected)
    assert diagnostics["pair_gate_kept_escape"]
    assert diagnostics["pair_gate_kept_escape"][0]["cand8_hex"] == "5a187f46ddd474d0"
    assert diagnostics["pair_escape_source_statuses"]["0,1"] == "gate_kept_escape"
    assert diagnostics["pair_best_escape_candidate"]["cand8_hex"] == "5a187f46ddd474d0"


def test_diverse_pair_frontier_pool_exact1_records_escape_ranked_out(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    selected, drop_reasons, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 1): [
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "ci_exact_wchars": 1,
                    "ci_distance5": 258,
                    "raw_distance10": 290,
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x3E],
                },
                {
                    "candidate_hex": "5a187f46ddd474d041414141414141",
                    "cand8_hex": "5a187f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 230,
                    "raw_distance10": 260,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 2,
                    "pair_wide_zero_high_pairs_8": 2,
                    "pair_flaglike_tail_pairs_8": 1,
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x18],
                },
            ],
            (0, 2): [
                {
                    "candidate_hex": "5a387f46ddd474d041414141414141",
                    "cand8_hex": "5a387f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 228,
                    "raw_distance10": 255,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 3,
                    "pair_wide_zero_high_pairs_8": 2,
                    "pair_flaglike_tail_pairs_8": 1,
                    "pair_positions": [0, 2],
                    "pair_values": [0x5A, 0x38],
                },
            ],
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        keep_limit=2,
    )

    assert len(selected) == 2
    assert all(entry["pair_escape_mode"] == "escape" for entry in selected)
    assert "escape_signal_but_ranked_out" not in drop_reasons
    assert diagnostics["pair_escape_source_statuses"]["0,2"] == "gate_kept_escape"
    assert diagnostics["pair_escape_status_by_lane"]["0,2"]["local_escape"] == "gate_kept_escape"


def test_diverse_pair_frontier_pool_exact1_allows_borderline_local_escape(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    selected, drop_reasons, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 1): [
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "ci_exact_wchars": 1,
                    "ci_distance5": 258,
                    "raw_distance10": 290,
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x3E],
                },
                {
                    "candidate_hex": "5a417f46ddd474d041414141414141",
                    "cand8_hex": "5a417f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 330,
                    "raw_distance10": 310,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 0,
                    "pair_wide_zero_high_pairs_8": 0,
                    "pair_flaglike_tail_pairs_8": 0,
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x41],
                },
            ]
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        keep_limit=2,
    )

    assert any(entry["cand8_hex"] == "5a417f46ddd474d0" for entry in selected)
    assert not diagnostics["pair_gate_kept_escape"]
    assert diagnostics["pair_borderline_escape_candidates"][0]["cand8_hex"] == "5a417f46ddd474d0"
    assert diagnostics["pair_borderline_escape_candidates"][0]["pair_escape_status"] == "borderline"
    assert diagnostics["pair_borderline_escape_candidates"][0]["pair_escape_quality_band"] == "near_local_escape"
    assert diagnostics["pair_near_local_escape_candidates"][0]["cand8_hex"] == "5a417f46ddd474d0"
    assert diagnostics["pair_near_local_escape_count"] == 1
    assert diagnostics["pair_wide_local_escape_count"] == 0
    assert diagnostics["pair_escape_status_by_lane"]["0,1"]["local_escape"] == "gate_borderline_escape"
    assert diagnostics["pair_escape_source_statuses"]["0,1"] == "gate_borderline_escape"
    assert diagnostics["pair_local_escape_borderline_count"] == 1
    assert drop_reasons == {}


def test_diverse_pair_frontier_pool_exact1_keeps_wide_local_escape_diagnostic_only(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    selected, drop_reasons, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 2): [
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "ci_exact_wchars": 1,
                    "ci_distance5": 258,
                    "raw_distance10": 290,
                    "pair_positions": [0, 2],
                    "pair_values": [0x5A, 0x7F],
                },
                {
                    "candidate_hex": "563e7b46ddd474d041414141414141",
                    "cand8_hex": "563e7b46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 558,
                    "raw_distance10": 558,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 0,
                    "pair_wide_zero_high_pairs_8": 0,
                    "pair_flaglike_tail_pairs_8": 0,
                    "pair_positions": [0, 2],
                    "pair_values": [0x56, 0x7B],
                    "pair_mutation_radius": 4,
                },
            ]
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        keep_limit=2,
    )

    assert all(entry["cand8_hex"] != "563e7b46ddd474d0" for entry in selected)
    assert diagnostics["pair_wide_local_escape_candidates"][0]["cand8_hex"] == "563e7b46ddd474d0"
    assert diagnostics["pair_wide_local_escape_candidates"][0]["pair_escape_quality_band"] == "wide_local_escape"
    assert not diagnostics["pair_near_local_escape_candidates"]
    assert diagnostics["pair_escape_source_statuses"]["0,2"] == "gate_filtered_wide_local_escape"
    assert diagnostics["pair_wide_local_escape_count"] == 1
    assert drop_reasons["gate_filtered_wide_local_escape"] == 1


def test_diverse_pair_frontier_pool_exact1_reports_projected_winner_mixed_with_neighbor_wide(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    selected, drop_reasons, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 2): [
                {
                    "candidate_hex": "5b3e7b46ddd474d041414141414141",
                    "cand8_hex": "5b3e7b46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 558,
                    "raw_distance10": 558,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 0,
                    "pair_wide_zero_high_pairs_8": 0,
                    "pair_flaglike_tail_pairs_8": 0,
                    "pair_positions": [0, 2],
                    "pair_values": [0x5B, 0x7B],
                    "pair_mutation_radius": 4,
                    "pair_projected_winner_available": [
                        {"position": 0, "value": 0x5B, "base_value": 0x5A}
                    ],
                    "pair_projected_winner_contributions": [
                        {
                            "position": 0,
                            "value": 0x5B,
                            "paired_position": 2,
                            "paired_value": 0x7B,
                            "paired_source": "neighbor",
                        }
                    ],
                },
            ]
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        keep_limit=2,
    )

    assert not selected
    assert diagnostics["pair_wide_local_escape_candidates"][0]["pair_projected_winner_gate_status"] == (
        "projected_winner_mixed_with_neighbor_wide"
    )
    assert diagnostics["pair_projected_winner_gate_status_counts"]["0,2"][
        "projected_winner_mixed_with_neighbor_wide"
    ] == 1
    assert drop_reasons["gate_filtered_wide_local_escape"] == 1


def test_diverse_pair_frontier_pool_exact1_promotes_projected_boundary_base_to_near_local(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    selected, drop_reasons, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 2): [
                {
                    "candidate_hex": "5b3e7f46ddd474d041414141414141",
                    "cand8_hex": "5b3e7f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 330,
                    "raw_distance10": 330,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 0,
                    "pair_wide_zero_high_pairs_8": 0,
                    "pair_flaglike_tail_pairs_8": 0,
                    "pair_positions": [0, 2],
                    "pair_values": [0x5B, 0x7F],
                    "pair_mutation_radius": 1,
                    "pair_candidate_origin": "exact1_projected_preserve_lane",
                    "pair_projected_boundary_role": "projected_winner_with_base",
                    "pair_projected_winner_available": [
                        {"position": 0, "value": 0x5B, "base_value": 0x5A}
                    ],
                    "pair_projected_winner_contributions": [
                        {
                            "position": 0,
                            "value": 0x5B,
                            "paired_position": 2,
                            "paired_value": 0x7F,
                            "paired_source": "base",
                        }
                    ],
                },
            ]
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        keep_limit=2,
    )

    assert any(entry["cand8_hex"] == "5b3e7f46ddd474d0" for entry in selected)
    assert diagnostics["pair_near_local_escape_candidates"][0]["pair_projected_winner_gate_status"] == (
        "projected_winner_promoted_to_near_local"
    )
    assert diagnostics["pair_projected_preserve_entries"][0]["pair_projected_boundary_role"] == (
        "projected_winner_with_base"
    )
    assert drop_reasons == {}


def test_diverse_pair_frontier_pool_exact1_projected_preserve_gets_handoff_slot_when_pool_tight(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    selected, drop_reasons, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 2): [
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "ci_exact_wchars": 1,
                    "ci_distance5": 258,
                    "raw_distance10": 290,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 1,
                    "pair_wide_zero_high_pairs_8": 1,
                    "pair_flaglike_tail_pairs_8": 0,
                    "pair_positions": [0, 2],
                    "pair_values": [0x5A, 0x7F],
                    "pair_mutation_radius": 0,
                },
                {
                    "candidate_hex": "5b3e7f46ddd474d041414141414141",
                    "cand8_hex": "5b3e7f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 330,
                    "raw_distance10": 330,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 0,
                    "pair_wide_zero_high_pairs_8": 0,
                    "pair_flaglike_tail_pairs_8": 0,
                    "pair_positions": [0, 2],
                    "pair_values": [0x5B, 0x7F],
                    "pair_mutation_radius": 1,
                    "pair_candidate_origin": "exact1_projected_preserve_lane",
                    "pair_projected_boundary_role": "projected_winner_with_base",
                    "pair_projected_winner_available": [
                        {"position": 0, "value": 0x5B, "base_value": 0x5A}
                    ],
                    "pair_projected_winner_contributions": [
                        {
                            "position": 0,
                            "value": 0x5B,
                            "paired_position": 2,
                            "paired_value": 0x7F,
                            "paired_source": "base",
                        }
                    ],
                },
            ]
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        keep_limit=1,
    )

    assert selected[0]["cand8_hex"] == "5b3e7f46ddd474d0"
    assert diagnostics["pair_projected_preserve_entries"][0]["cand8_hex"] == "5b3e7f46ddd474d0"
    assert diagnostics["pair_projected_preserve_entries"][0]["pair_projected_winner_gate_status"] == (
        "projected_winner_promoted_to_near_local"
    )
    assert drop_reasons == {}


def test_exact1_pair_set_selection_prefers_near_local_over_wide_borderline() -> None:
    near_result = {
        "pair_frontier_pool": [],
        "pair_drop_reasons": {},
        "pair_frontier_diagnostics": {
            "pair_gate_kept_escape": [],
            "pair_near_local_escape_candidates": [{"ci_distance5": 330}],
            "pair_wide_local_escape_count": 0,
            "pair_best_local_escape": {"0,1": {"pair_escape_signal_score": 7}},
        },
    }
    wide_result = {
        "pair_frontier_pool": [],
        "pair_drop_reasons": {},
        "pair_frontier_diagnostics": {
            "pair_gate_kept_escape": [],
            "pair_near_local_escape_candidates": [],
            "pair_borderline_escape_candidates": [{"ci_distance5": 558}],
            "pair_wide_local_escape_count": 1,
            "pair_best_local_escape": {"0,2": {"pair_escape_signal_score": 7}},
        },
    }

    assert compare_aware_search._exact1_pair_set_selection_key(near_result) < compare_aware_search._exact1_pair_set_selection_key(wide_result)


def test_diverse_pair_frontier_pool_exact1_tracks_local_and_hard_escape_per_pair(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    _, drop_reasons, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 1): [
                {
                    "candidate_hex": "5a187f46ddd474d041414141414141",
                    "cand8_hex": "5a187f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 258,
                    "raw_distance10": 292,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 2,
                    "pair_wide_zero_high_pairs_8": 2,
                    "pair_flaglike_tail_pairs_8": 1,
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x18],
                },
                {
                    "candidate_hex": "a4707f46ddd474d041414141414141",
                    "cand8_hex": "a4707f46ddd474d0",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 677,
                    "raw_distance10": 675,
                    "pair_escape_mode": "escape",
                    "pair_wide_ascii_contiguous_8": 0,
                    "pair_wide_zero_high_pairs_8": 0,
                    "pair_flaglike_tail_pairs_8": 0,
                    "pair_positions": [0, 1],
                    "pair_values": [0xA4, 0x70],
                },
            ]
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        keep_limit=2,
    )

    assert diagnostics["pair_escape_lane_counts"]["0,1"] == {"local_escape": 1, "hard_escape": 1}
    assert diagnostics["pair_escape_status_by_lane"]["0,1"]["local_escape"] == "gate_kept_escape"
    assert diagnostics["pair_escape_status_by_lane"]["0,1"]["hard_escape"] == "gate_filtered_hard_escape"
    assert diagnostics["pair_best_local_escape"]["0,1"]["cand8_hex"] == "5a187f46ddd474d0"
    assert diagnostics["pair_best_hard_escape"]["0,1"]["cand8_hex"] == "a4707f46ddd474d0"
    assert drop_reasons["gate_filtered_hard_escape"] == 1


def test_diverse_pair_frontier_pool_exact1_reports_profile_ranked_out_before_frontier_gate(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_guided_sort_key",
        lambda entry, transform_model, **kwargs: (
            int(entry.get("ci_distance5", 1 << 30)),
            int(entry.get("raw_distance10", 1 << 30)),
            -int(entry.get("ci_exact_wchars", 0)),
            str(entry.get("candidate_hex", "")),
        ),
    )
    _, _, diagnostics = compare_aware_search._diverse_pair_frontier_pool(
        {
            (0, 1): [
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "ci_exact_wchars": 1,
                    "ci_distance5": 258,
                    "raw_distance10": 290,
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x3E],
                }
            ]
        },
        transform_model=SamplereverseTransformModel(),
        anchor_mode=FRONTIER_ANCHOR_MODE,
        frontier_submode=FRONTIER_EXACT1_SUBMODE,
        pair_profile_details={
            "pair_profile_escape_entries": {
                "0,1": [
                    {
                        "candidate_hex": "5a187f46ddd474d041414141414141",
                        "cand8_hex": "5a187f46ddd474d0",
                        "pair_positions": [0, 1],
                        "pair_values": [0x5A, 0x18],
                    }
                ]
            },
            "pair_profile_kept_escape": {"0,1": []},
            "pair_profile_kept_preserve": {"0,1": []},
            "pair_profile_preserve_entries": {"0,1": []},
            "pair_profile_drop_reasons": {"0,1": {"escape": "profile_ranked_out"}},
            "pair_profile_truncation_summary": {"0,1": {"escape_total": 1, "escape_kept": 0}},
        },
        baseline_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
        },
        keep_limit=1,
    )

    assert diagnostics["pair_escape_source_statuses"]["0,1"] == "profile_ranked_out"


def test_alternate_locked_pair_positions_for_exact1_prefers_local_escape_heavy_pairs() -> None:
    alternate, details = _alternate_locked_pair_positions_for_exact1(
        primary_locked_pairs=[(0, 1), (0, 2), (0, 3)],
        source_details={
            "candidate_pairs": [[0, 1], [1, 2], [2, 3], [3, 4]],
        },
        pair_gate_input_summary={
            "1,2": [
                {"pair_escape_lane": "local_escape"},
                {"pair_escape_lane": "local_escape"},
            ],
            "2,3": [
                {"pair_escape_lane": "local_escape"},
            ],
            "0,3": [
                {"pair_escape_lane": "hard_escape"},
            ],
        },
    )

    assert alternate[0] == (1, 2)
    assert (2, 3) in alternate
    assert all(pair not in {(0, 1), (0, 2), (0, 3)} for pair in alternate)
    assert details["local_escape_counts"]["1,2"] == 2


def test_exact1_pair_escape_signal_classifies_hard_and_local_escape() -> None:
    hard_signal = compare_aware_search._exact1_pair_escape_signal(
        {
            "candidate_hex": "a43e7f3bddd474d041414141414141",
            "cand8_hex": "a43e7f3bddd474d0",
            "ci_exact_wchars": 0,
            "ci_distance5": 677,
            "raw_distance10": 675,
            "pair_positions": [0, 3],
            "pair_values": [0xA4, 0x3B],
            "pair_wide_ascii_contiguous_8": 0,
            "pair_wide_zero_high_pairs_8": 0,
            "pair_flaglike_tail_pairs_8": 0,
        },
        {
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_positions": [0, 3],
            "pair_values": [0x5A, 0x46],
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        transform_model=SamplereverseTransformModel(),
    )
    local_signal = compare_aware_search._exact1_pair_escape_signal(
        {
            "candidate_hex": "5a187f46ddd474d041414141414141",
            "cand8_hex": "5a187f46ddd474d0",
            "ci_exact_wchars": 0,
            "ci_distance5": 230,
            "raw_distance10": 260,
            "pair_positions": [0, 1],
            "pair_values": [0x5A, 0x18],
            "pair_wide_ascii_contiguous_8": 2,
            "pair_wide_zero_high_pairs_8": 2,
            "pair_flaglike_tail_pairs_8": 1,
        },
        {
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "raw_distance10": 290,
            "pair_positions": [0, 1],
            "pair_values": [0x5A, 0x3E],
            "pair_wide_ascii_contiguous_8": 1,
            "pair_wide_zero_high_pairs_8": 1,
            "pair_flaglike_tail_pairs_8": 0,
        },
        transform_model=SamplereverseTransformModel(),
    )

    assert hard_signal["lane"] == "hard_escape"
    assert hard_signal["passed"] is False
    assert hard_signal["status"] == "reject"
    assert local_signal["lane"] == "local_escape"
    assert local_signal["passed"] is True
    assert local_signal["status"] == "keep"


def test_improved_frontier_candidates_only_promote_runtime_improved_lineages() -> None:
    improved = _improved_frontier_candidates(
        [
            {
                "candidate_hex": "78d540b49c59077041414141414141",
                "cand8_hex": "78d540b49c590770",
                "compare_semantics_agree": True,
                "runtime_ci_exact_wchars": 2,
                "runtime_ci_distance5": 246,
            },
            {
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
                "cand8_hex": "5a3e7f46ddd474d0",
                "compare_semantics_agree": True,
                "runtime_ci_exact_wchars": 1,
                "runtime_ci_distance5": 258,
                "source_anchor": "f649b64b5e97dbd0",
                "frontier_role": "exact1_frontier",
            },
            {
                "candidate_hex": "788940b49c59077041414141414141",
                "cand8_hex": "788940b49c590770",
                "compare_semantics_agree": True,
                "runtime_ci_exact_wchars": 0,
                "runtime_ci_distance5": 293,
                "source_anchor": "788940b49c590770",
                "frontier_role": "exact0_frontier",
            },
        ],
        context_entries=[
            {
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
                "cand8_hex": "5a3e7f46ddd474d0",
                "source_anchor": "f649b64b5e97dbd0",
                "anchor_mode": "frontier",
                "anchor_lineage": "exact0_frontier(f649b64b5e97dbd0) -> refine(frontier)",
            },
            {
                "candidate_hex": "788940b49c59077041414141414141",
                "cand8_hex": "788940b49c590770",
                "source_anchor": "788940b49c590770",
                "anchor_mode": "frontier",
                "anchor_lineage": "exact0_frontier(788940b49c590770)",
            },
        ],
        baseline_validations=[
            {
                "candidate_hex": "f649b64b5e97dbd041414141414141",
                "cand8_hex": "f649b64b5e97dbd0",
                "runtime_ci_exact_wchars": 0,
                "runtime_ci_distance5": 280,
                "compare_semantics_agree": True,
            },
            {
                "candidate_hex": "788940b49c59077041414141414141",
                "cand8_hex": "788940b49c590770",
                "runtime_ci_exact_wchars": 0,
                "runtime_ci_distance5": 293,
                "compare_semantics_agree": True,
            },
        ],
    )

    assert [item["anchor"] for item in improved] == ["5a3e7f46ddd474d0"]
    assert improved[0]["improvement_gate_passed"] is True


def test_validated_projected_preserve_handoff_can_seed_second_hop_composition() -> None:
    candidates = _validated_projected_preserve_second_hop_candidates(
        [
            {
                "candidate_hex": "5a3f7f46ddd474d041414141414141",
                "cand8_hex": "5a3f7f46ddd474d0",
                "frontier_role": "projected_preserve_handoff",
                "compare_semantics_agree": True,
                "runtime_ci_exact_wchars": 0,
                "runtime_ci_distance5": 740,
                "offline_raw_distance10": 772,
            }
        ],
        context_entries=[
            {
                "candidate_hex": "5a3f7f46ddd474d041414141414141",
                "cand8_hex": "5a3f7f46ddd474d0",
                "source_anchor": "78d540b49c590770",
                "anchor_mode": FRONTIER_ANCHOR_MODE,
                "anchor_lineage": "exact2_seed(78d540b49c590770) -> guided(frontier)",
                "pair_candidate_origin": "exact1_projected_preserve_lane",
                "pair_projected_boundary_role": "projected_winner_with_base",
                "pair_projected_winner_gate_status": "projected_winner_promoted_to_near_local",
            }
        ],
    )

    assert len(candidates) == 1
    assert candidates[0]["anchor"] == "5a3f7f46ddd474d0"
    assert candidates[0]["frontier_role"] == PROJECTED_PRESERVE_SECOND_HOP_ROLE
    assert candidates[0]["frontier_submode"] == FRONTIER_EXACT1_SUBMODE
    assert candidates[0]["source_anchor"] == "78d540b49c590770"
    assert candidates[0]["improvement_gate_passed"] is False

    continuation, reason, used_second_hop = _frontier_continuation_candidates(
        improved_frontier_candidates=[],
        second_hop_frontier_candidates=candidates,
        frontier_converged_reason="distance_not_improved",
        iteration_index=1,
    )

    assert reason == "continue"
    assert used_second_hop is True
    assert continuation[0]["frontier_role"] == PROJECTED_PRESERVE_SECOND_HOP_ROLE


def test_second_hop_composition_does_not_admit_compare_disagree_candidate() -> None:
    candidates = _validated_projected_preserve_second_hop_candidates(
        [
            {
                "candidate_hex": "5a3f7f46ddd474d041414141414141",
                "cand8_hex": "5a3f7f46ddd474d0",
                "frontier_role": "projected_preserve_handoff",
                "compare_semantics_agree": False,
                "runtime_ci_exact_wchars": 0,
                "runtime_ci_distance5": 740,
            }
        ],
        context_entries=[
            {
                "candidate_hex": "5a3f7f46ddd474d041414141414141",
                "cand8_hex": "5a3f7f46ddd474d0",
                "pair_candidate_origin": "exact1_projected_preserve_lane",
                "pair_projected_boundary_role": "projected_winner_with_base",
                "pair_projected_winner_gate_status": "projected_winner_promoted_to_near_local",
            }
        ],
    )

    assert candidates == []


def test_second_hop_composition_does_not_expand_budget() -> None:
    validations = []
    context_entries = []
    for idx in range(FRONTIER_MAX_ANCHORS + 3):
        cand8 = f"5a3f7f46ddd47{idx:02x}0"[:16]
        candidate_hex = f"{cand8}41414141414141"
        validations.append(
            {
                "candidate_hex": candidate_hex,
                "cand8_hex": cand8,
                "frontier_role": "projected_preserve_handoff",
                "compare_semantics_agree": True,
                "runtime_ci_exact_wchars": 0,
                "runtime_ci_distance5": 740 + idx,
            }
        )
        context_entries.append(
            {
                "candidate_hex": candidate_hex,
                "cand8_hex": cand8,
                "source_anchor": "78d540b49c590770",
                "pair_candidate_origin": "exact1_projected_preserve_lane",
                "pair_projected_boundary_role": "projected_winner_with_base",
                "pair_projected_winner_gate_status": "projected_winner_promoted_to_near_local",
            }
        )

    candidates = _validated_projected_preserve_second_hop_candidates(
        validations,
        context_entries=context_entries,
    )

    assert len(candidates) == max(1, FRONTIER_MAX_ANCHORS - 1)


def test_select_smt_base_entry_prefers_better_compare_agree_frontier() -> None:
    selected = _select_smt_base_entry(
        best_exact2_entry={"runtime_ci_distance5": 246},
        frontier_validations=[
            {
                "candidate_hex": "a47a0a74bd35355041414141414141",
                "cand8_hex": "a47a0a74bd353550",
                "runtime_ci_exact_wchars": 0,
                "runtime_ci_distance5": 208,
                "offline_raw_distance10": 266,
                "compare_semantics_agree": True,
            }
        ],
        fallback_entry={"cand8_hex": "78d540b49c590770"},
    )

    assert selected["cand8_hex"] == "a47a0a74bd353550"
    assert selected["ci_distance5"] == 208


def test_exact1_projected_competition_summary_marks_single_byte_bottleneck_when_pair_sets_have_no_winner() -> None:
    summary = _exact1_projected_competition_summary(
        pair_stage_stats={
            "projected_beats_neighbor_count": 0,
            "pair_gate_kept_escape": 0,
            "pair_near_local_escape_count": 0,
            "pair_wide_local_escape_count": 2,
        },
        pair_set_comparison_summary={
            "primary_pair_set": {"projected_beats_neighbor_count": 0},
            "alternate_pair_set": {"projected_beats_neighbor_count": 0},
        },
    )

    assert summary == {
        "stall_reason": "single_byte_projected_competition",
        "pair_set_diagnosis": "pair_set_not_limiting_single_byte_competition",
        "projected_beats_neighbor_count": 0,
        "pair_gate_kept_escape_count": 0,
        "near_local_escape_count": 0,
        "wide_local_escape_count": 2,
    }


def test_exact1_projected_competition_reason_prefers_pair_refine_after_projected_winner() -> None:
    reason = _exact1_projected_competition_reason_from_runs(
        [
            {
                "pair_stage_stats": {
                    "exact1_projected_competition_summary": {
                        "stall_reason": "single_byte_projected_competition"
                    }
                }
            },
            {
                "pair_stage_stats": {
                    "exact1_projected_competition_summary": {
                        "stall_reason": "pair_refine_after_projected_winner"
                    }
                }
            },
        ]
    )

    assert reason == "pair_refine_after_projected_winner"


def test_select_smt_base_entry_prefers_exact1_frontier_over_exact0_distance_basin() -> None:
    selected = _select_smt_base_entry(
        best_exact2_entry={"runtime_ci_distance5": 246},
        frontier_validations=[
            {
                "candidate_hex": "a47a0a74bd35355041414141414141",
                "cand8_hex": "a47a0a74bd353550",
                "runtime_ci_exact_wchars": 0,
                "runtime_ci_distance5": 208,
                "offline_raw_distance10": 266,
                "compare_semantics_agree": True,
            },
            {
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
                "cand8_hex": "5a3e7f46ddd474d0",
                "runtime_ci_exact_wchars": 1,
                "runtime_ci_distance5": 258,
                "offline_raw_distance10": 300,
                "compare_semantics_agree": True,
                "frontier_role": "exact1_frontier",
            },
        ],
        fallback_entry={"cand8_hex": "78d540b49c590770"},
    )

    assert selected["cand8_hex"] == "5a3e7f46ddd474d0"
    assert selected["frontier_submode"] == FRONTIER_EXACT1_SUBMODE


def test_exact2_basin_smt_diagnostic_does_not_replace_primary_frontier_base() -> None:
    diagnostic = _exact2_basin_smt_diagnostic_payload(
        best_exact2_entry={
            "candidate_hex": "78d540b49c59077041414141414141",
            "cand8_hex": "78d540b49c590770",
            "runtime_lhs_prefix_hex_10": "46006c004464830d311c",
            "runtime_ci_exact_wchars": 2,
            "runtime_ci_distance5": 246,
            "offline_raw_distance10": 304,
            "compare_semantics_agree": True,
        },
        primary_smt_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "frontier_submode": FRONTIER_EXACT1_SUBMODE,
        },
        comparison_entries=[
            {
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
                "cand8_hex": "5a3e7f46ddd474d0",
                "improvement_gate_passed": True,
            },
            {
                "candidate_hex": "5a3f7f46ddd474d041414141414141",
                "cand8_hex": "5a3f7f46ddd474d0",
                "improvement_gate_passed": False,
            },
        ],
        lineage_entries=[],
        transform_model=SamplereverseTransformModel(),
    )

    assert diagnostic["attempted"] is False
    assert diagnostic["recommended"] is True
    assert diagnostic["base_anchor"] == "78d540b49c590770"
    assert diagnostic["primary_base_anchor"] == "5a3e7f46ddd474d0"
    assert diagnostic["prefix_boundary"]["ci_exact_wchars"] == 2
    assert diagnostic["variable_byte_positions"]


def test_run_compare_aware_smt_records_feedback_value_pools_from_improved_frontier_entries(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    captured_z3: dict[str, object] = {}

    def fake_solve_targeted_prefix8(**kwargs):
        captured_z3.update(kwargs)
        return type(
            "Z3Result",
            (),
            {
                "attempted": True,
                "summary": "ok",
                "evidence": [],
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
            },
        )()

    monkeypatch.setattr(compare_aware_search, "solve_targeted_prefix8", fake_solve_targeted_prefix8)
    monkeypatch.setattr(
        compare_aware_search,
        "validate_compare_aware_results",
        lambda **kwargs: (tmp_path / "smt_validation.json", []),
    )

    result = run_compare_aware_smt(
        target=target,
        artifacts_dir=tmp_path / "smt",
        base_entry={
            "candidate_hex": "5a3e7f46ddd474d041414141414141",
            "cand8_hex": "5a3e7f46ddd474d0",
            "ci_exact_wchars": 1,
            "ci_distance5": 258,
            "source_anchor": "f649b64b5e97dbd0",
            "frontier_role": "exact1_frontier",
            "anchor_lineage": "exact0_frontier(f649b64b5e97dbd0) -> refine(frontier)",
            "pair_gate_kept_escape": [
                {
                    "cand8_hex": "5a447f46ddd474d0",
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x44],
                }
            ],
            "pair_near_local_escape_candidates": [
                {
                    "cand8_hex": "5a667f46ddd474d0",
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x66],
                    "pair_escape_status": "borderline",
                    "pair_escape_quality_band": "near_local_escape",
                }
            ],
            "pair_projected_boundary_entries": [
                {
                    "cand8_hex": "5a427f46ddd474d0",
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x42],
                    "pair_candidate_origin": "exact1_projected_boundary",
                    "pair_projected_boundary_role": "projected_winner_with_base",
                }
            ],
            "pair_projected_winner_available": [
                {"position": 2, "value": 0x43, "base_value": 0x7F}
            ],
            "pair_wide_local_escape_candidates": [
                {
                    "cand8_hex": "5a777f46ddd474d0",
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x77],
                    "pair_escape_status": "borderline",
                    "pair_escape_quality_band": "wide_local_escape",
                }
            ],
            "pair_profile_kept_escape": [
                {
                    "cand8_hex": "5a447f46ddd474d0",
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x44],
                }
            ],
            "pair_profile_kept_preserve": [
                {
                    "cand8_hex": "5a557f46ddd474d0",
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x55],
                }
            ],
            "pair_best_local_escape": {
                "0,1": {
                    "cand8_hex": "5a777f46ddd474d0",
                    "pair_positions": [0, 1],
                    "pair_values": [0x5A, 0x77],
                    "pair_escape_quality_band": "wide_local_escape",
                }
            },
            "pair_projected_competitive_status": {
                "0,1": {
                    "0": "projected_beats_neighbor",
                    "1": "projected_loses_on_raw",
                },
            },
            "pair_projected_competitive_winner": {
                "0,1": {
                    "0": {"family": "projected_soft_family", "value": 0x41},
                    "1": {"family": "escape_neighbor_soft_family", "value": 0x57},
                },
            },
        },
        comparison_entries=[
            {
                "cand8_hex": "5a997f46ddd474d0",
                "pair_positions": [0, 1],
                "pair_values": [0x5A, 0x99],
                "improvement_gate_passed": True,
            },
            {
                "cand8_hex": "5a998846ddd474d0",
                "pair_positions": [0, 1],
                "pair_values": [0x5A, 0x99],
                "triad_positions": [0, 1, 2],
                "triad_value": 0x88,
                "improvement_gate_passed": True,
            },
        ],
        lineage_entries=[
            {
                "candidate_hex": "78997f46ddd474d041414141414141",
                "cand8_hex": "78997f46ddd474d0",
                "ci_exact_wchars": 1,
                "source_anchor": "f649b64b5e97dbd0",
                "frontier_submode": FRONTIER_EXACT1_SUBMODE,
            }
        ],
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    assert result["payload"]["feedback_value_pools"]["0"][0] == 0x5A
    assert 0x44 in result["payload"]["feedback_value_pools"]["1"]
    assert 0x66 in result["payload"]["feedback_value_pools"]["1"]
    assert 0x42 in result["payload"]["feedback_value_pools"]["1"]
    assert 0x77 not in result["payload"]["feedback_value_pools"]["1"]
    assert 0x55 in result["payload"]["feedback_value_pools"]["1"]
    assert 0x99 in result["payload"]["feedback_value_pools"]["1"]
    assert 0x78 in result["payload"]["feedback_value_pools"]["0"]
    assert 0x41 in result["payload"]["feedback_value_pools"]["0"]
    assert 0x43 in result["payload"]["feedback_value_pools"]["2"]
    assert 0x57 not in result["payload"]["feedback_value_pools"]["1"]
    assert result["payload"]["prefix_boundary"]["cand8_hex"] == "5a3e7f46ddd474d0"
    assert result["payload"]["prefix_boundary"]["ci_exact_wchars"] == 1
    assert captured_z3["value_pools"][1][0] == 0x3E
    assert 0x44 in captured_z3["value_pools"][1]


def test_run_compare_aware_smt_records_z3_unknown_diagnostics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")

    def fake_solve_targeted_prefix8(**kwargs):
        return type(
            "Z3Result",
            (),
            {
                "attempted": True,
                "summary": "targeted z3 finished with unknown",
                "evidence": ["runtime_probe:z3_targeted reason_unknown=timeout"],
                "candidate_hex": "",
                "diagnostics": {
                    "z3_reason_unknown": "timeout",
                    "estimated_value_pool_combinations": 18,
                    "value_pool_sizes": {"0": 1, "1": 3},
                    "symbolic_compare_bytes": 10,
                    "solver_type": "Optimize",
                    "timeout_ms": 1500,
                },
            },
        )()

    monkeypatch.setattr(compare_aware_search, "solve_targeted_prefix8", fake_solve_targeted_prefix8)

    result = run_compare_aware_smt(
        target=target,
        artifacts_dir=tmp_path / "smt",
        base_entry={
            "candidate_hex": "78d540b49c59077041414141414141",
            "cand8_hex": "78d540b49c590770",
            "ci_exact_wchars": 2,
            "ci_distance5": 246,
            "anchor_mode": "exact2",
        },
        comparison_entries=[],
        variable_byte_positions_override=[0, 1],
        variable_nibble_positions_override=[0, 1],
        value_pools_override={0: [0x78], 1: [0xD5, 0x3E, 0x3C]},
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    assert result["payload"]["summary"] == "targeted z3 finished with unknown"
    assert result["payload"]["z3_reason_unknown"] == "timeout"
    assert result["payload"]["estimated_value_pool_combinations"] == 18
    assert result["payload"]["value_pool_sizes"] == {"0": 1, "1": 3}
    assert result["payload"]["validation_candidates"] == []


def test_exact2_basin_value_pool_evaluation_enumerates_bounded_pool_and_requires_improvement(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    captured: dict[str, object] = {}

    def fake_validate_compare_aware_results(**kwargs):
        payload = json.loads(Path(kwargs["result_path"]).read_text(encoding="utf-8"))
        candidates = list(payload["validation_candidates"])
        captured["validate_top"] = kwargs["validate_top"]
        captured["candidate_count"] = len(candidates)
        validations = []
        for entry in candidates:
            candidate_hex = str(entry["candidate_hex"])
            is_base = candidate_hex.startswith("78d540b49c590770")
            validations.append(
                {
                    **entry,
                    "candidate_hex": candidate_hex,
                    "cand8_hex": candidate_hex[:16],
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2 if is_base else 1,
                    "runtime_ci_distance5": 246 if is_base else 258,
                    "offline_ci_distance5": int(entry.get("ci_distance5", 1 << 30) or (1 << 30)),
                    "offline_raw_distance10": int(entry.get("raw_distance10", 1 << 30) or (1 << 30)),
                }
            )
        return tmp_path / "value_pool_validation.json", validations

    monkeypatch.setattr(
        compare_aware_search,
        "validate_compare_aware_results",
        fake_validate_compare_aware_results,
    )

    result = run_exact2_basin_value_pool_evaluation(
        target=target,
        artifacts_dir=tmp_path / "exact2_basin_value_pool",
        base_entry={
            "candidate_hex": "78d540b49c59077041414141414141",
            "cand8_hex": "78d540b49c590770",
            "runtime_ci_exact_wchars": 2,
            "runtime_ci_distance5": 246,
            "ci_exact_wchars": 2,
            "ci_distance5": 246,
        },
        exact2_basin_smt={
            "base_anchor": "78d540b49c590770",
            "variable_byte_positions": [1, 2, 3, 0, 4],
            "feedback_value_pools": {
                "1": [0xD5, 0x3E, 0x3C],
                "2": [0x40, 0x7F, 0x80],
                "3": [0xB4, 0x8F],
                "0": [0x78],
                "4": [0x9C],
            },
        },
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["generated_count"] == 18
    assert payload["unique_count"] == 18
    assert payload["validated_count"] == 18
    assert captured["validate_top"] == 18
    assert captured["candidate_count"] == 18
    assert payload["value_pools"]["1"][0] == 0xD5
    assert payload["value_pools"]["0"] == [0x78]
    assert payload["best_runtime_candidate"]["cand8_hex"] == "78d540b49c590770"
    assert payload["improved_over_exact2"] is False
    assert payload["classification"] == "exact2_basin_value_pools_exhausted_no_gain"
    assert result["promotable_validations"] == []


def test_profile_transform_hypothesis_audit_writes_bounded_metadata_only_matrix(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(compare_aware_search, "_negative_exact2_value_pool_recorded", lambda: True)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_artifact_payload",
        lambda kind: (
            {
                "attempted": True,
                "classification": "exact2_basin_value_pools_exhausted_no_gain",
                "generated_count": 18,
                "unique_count": 18,
                "validated_count": 18,
                "best_runtime_candidate": {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                },
                "improved_over_exact2": False,
            },
            "indexed/value_pool.json",
        ),
    )

    result = run_profile_transform_hypothesis_audit(
        artifacts_dir=tmp_path,
        transform_model=SamplereverseTransformModel(),
        runtime_validations=[
            {
                "candidate_hex": "78d540b49c59077041414141414141",
                "cand8_hex": "78d540b49c590770",
                "compare_semantics_agree": True,
                "runtime_lhs_prefix_hex_10": "46006c004464830d311c",
                "runtime_ci_exact_wchars": 2,
                "runtime_ci_distance5": 246,
            },
            {
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
                "cand8_hex": "5a3e7f46ddd474d0",
                "compare_semantics_agree": True,
                "runtime_lhs_prefix_hex_10": "460061357f0b8c688502",
                "runtime_ci_exact_wchars": 1,
                "runtime_ci_distance5": 258,
            },
        ],
        top_entries=[],
        exact2_basin_value_pool_run=None,
        search_budget=200_000_000,
        snapshot_interval=10_000_000,
        validate_top=5,
        per_probe_timeout=2.0,
        log=lambda _: None,
    )

    path = Path(result["result_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == PROFILE_TRANSFORM_HYPOTHESIS_MATRIX_FILE_NAME
    assert payload["audit_only"] is True
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["candidate_count"] <= PROFILE_TRANSFORM_AUDIT_CANDIDATE_LIMIT
    assert {item["id"] for item in payload["hypotheses"]} == {"H1", "H2", "H3", "H4", "H5", "H6"}
    assert payload["exhausted_branch_confirmation"]["generated_count"] == 18
    assert payload["exhausted_branch_confirmation"]["negative_result_recorded"] is True
    assert payload["read_scope"]["uses_latest_indexed_artifacts_only"] is True
    assert payload["read_scope"]["scans_full_solve_reports"] is False
    exact2 = next(item for item in payload["candidates"] if item["label"] == "current_exact2_best")
    assert exact2["offline_runtime_prefix_agree_10"] is True
    assert exact2["trace"]["rc4"]["decrypt_prefix_hex"].startswith("46006c004464830d311c")
    assert any(item["promotion_allowed"] is False for item in payload["candidates"])
    assert payload["next_bounded_validation_target"]["selected_hypotheses"] == ["H1", "H3"]


def test_transform_trace_consistency_confirms_runtime_backed_candidates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_indexed_artifact_payload(kind):
        if kind == "h1_h3_boundary_validation_runtime":
            return (
                {
                    "validations": [
                        {
                            "candidate_hex": "78d540b49c59077040414141414141",
                            "cand8_hex": "78d540b49c590770",
                            "compare_semantics_agree": True,
                            "runtime_lhs_prefix_hex_10": "46006c004464830d311c",
                            "runtime_ci_exact_wchars": 2,
                            "runtime_ci_distance5": 246,
                            "stage": "h1_h3_boundary_validation",
                        },
                        {
                            "candidate_hex": "78d540b49c59077042414141414141",
                            "cand8_hex": "78d540b49c590770",
                            "compare_semantics_agree": True,
                            "runtime_lhs_prefix_hex_10": "46006c004464830d311c",
                            "runtime_ci_exact_wchars": 2,
                            "runtime_ci_distance5": 246,
                            "stage": "h1_h3_boundary_validation",
                        },
                    ]
                },
                "indexed/h1_h3_runtime.json",
            )
        if kind == "exact2_basin_value_pool_validation":
            return (
                {
                    "validations": [
                        {
                            "candidate_hex": "78d540b49c59077041414141414141",
                            "cand8_hex": "78d540b49c590770",
                            "compare_semantics_agree": True,
                            "runtime_lhs_prefix_hex_10": "46006c004464830d311c",
                            "runtime_ci_exact_wchars": 2,
                            "runtime_ci_distance5": 246,
                            "stage": "exact2_basin_value_pool",
                        }
                    ]
                },
                "indexed/value_pool_validation.json",
            )
        return {}, ""

    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)

    result = run_transform_trace_consistency_diagnostic(
        artifacts_dir=tmp_path,
        runtime_validations=[],
        transform_model=SamplereverseTransformModel(),
        log=lambda _: None,
    )

    path = Path(result["result_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == TRANSFORM_TRACE_CONSISTENCY_FILE_NAME
    assert payload["classification"] == "transform_model_confirmed"
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["runtime_backed_count"] == 3
    assert payload["promotable_validations"] == []

    baseline = next(
        item for item in payload["candidates"] if item["candidate_hex"] == "78d540b49c59077041414141414141"
    )
    verdict = baseline["verdict"]
    assert verdict["offline_runtime_prefix_agree_10"] is True
    assert verdict["offline_runtime_metrics_agree"] is True
    assert verdict["compare_semantics_agree"] is True
    assert verdict["first_unsupported_stage"] == ""
    assert verdict["evidence_status"] == "supported_by_runtime"
    assert len(baseline["trace"]["prefix_length_table"]) == 10


def test_transform_trace_consistency_reports_missing_runtime_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", lambda kind: ({}, ""))

    result = run_transform_trace_consistency_diagnostic(
        artifacts_dir=tmp_path,
        runtime_validations=[],
        transform_model=SamplereverseTransformModel(),
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "evidence_insufficient"
    assert payload["runtime_backed_count"] == 0
    assert all(
        item["verdict"]["evidence_status"] == "missing_runtime_artifact"
        for item in payload["candidates"]
    )


def _fake_dynamic_probe_validate(tmp_path: Path, captured: dict[str, object] | None = None):
    def fake_validate_compare_aware_results(**kwargs):
        payload = json.loads(Path(kwargs["result_path"]).read_text(encoding="utf-8"))
        candidates = list(payload["validation_candidates"])
        if captured is not None:
            captured["validate_top"] = kwargs["validate_top"]
            captured["candidate_count"] = len(candidates)
            captured["output_file_name"] = kwargs["output_file_name"]
            captured["capture_prefix_bytes"] = kwargs["capture_prefix_bytes"]
        validations = []
        for entry in candidates:
            candidate_hex = str(entry["candidate_hex"])
            trace = trace_candidate_transform(candidate_hex)
            compare_boundary = trace["compare_boundary"]
            validations.append(
                {
                    **entry,
                    "candidate_hex": candidate_hex,
                    "cand8_hex": candidate_hex[:16],
                    "compare_semantics_agree": True,
                    "runtime_lhs_prefix_hex": compare_boundary["raw_prefix_hex_64"],
                    "runtime_lhs_prefix_hex_10": compare_boundary["raw_prefix_hex_10"],
                    "runtime_lhs_prefix_hex_16": compare_boundary["raw_prefix_hex_64"][:32],
                    "runtime_lhs_prefix_bytes_captured": 64,
                    "runtime_lhs_ptr": "0x1000",
                    "runtime_rhs_ptr": "0x2000",
                    "runtime_compare_count": 5,
                    "runtime_rhs_prefix_hex": "66006c00610067007b00",
                    "runtime_rhs_wide_text": "flag{",
                    "runtime_lhs_wide_text": "",
                    "runtime_ci_exact_wchars": compare_boundary["ci_exact_wchars"],
                    "runtime_ci_distance5": compare_boundary["ci_distance5"],
                    "offline_ci_distance5": compare_boundary["ci_distance5"],
                    "offline_raw_distance10": compare_boundary["raw_distance10"],
                    "prefix_boundary": compare_boundary,
                }
            )
        return tmp_path / "dynamic_probe_validation.json", validations

    return fake_validate_compare_aware_results


def test_dynamic_compare_path_probe_has_bounded_candidate_count(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        compare_aware_search,
        "validate_compare_aware_results",
        _fake_dynamic_probe_validate(tmp_path, captured),
    )

    result = run_dynamic_compare_path_probe(
        target=target,
        artifacts_dir=tmp_path / "dynamic_compare_path_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == DYNAMIC_COMPARE_PATH_PROBE_FILE_NAME
    assert payload["candidate_count"] == 3
    assert captured["validate_top"] == 3
    assert captured["candidate_count"] == 3
    assert captured["output_file_name"] == DYNAMIC_COMPARE_PATH_PROBE_FILE_NAME


def test_dynamic_compare_path_probe_does_not_expand_search_budget(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        compare_aware_search,
        "validate_compare_aware_results",
        _fake_dynamic_probe_validate(tmp_path, captured),
    )

    result = run_dynamic_compare_path_probe(
        target=target,
        artifacts_dir=tmp_path / "dynamic_compare_path_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert captured["capture_prefix_bytes"] == 64


def test_dynamic_compare_path_probe_records_probe_point_availability(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search,
        "validate_compare_aware_results",
        _fake_dynamic_probe_validate(tmp_path),
    )

    result = run_dynamic_compare_path_probe(
        target=target,
        artifacts_dir=tmp_path / "dynamic_compare_path_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "dynamic_probe_complete"
    assert payload["runtime_backed_count"] == 3
    assert payload["probe_points"]["raw_input"] == "available"
    assert payload["probe_points"]["post_rc4_compare_buffer"] == "available"
    assert payload["probe_points"]["compare_target"] == "available"
    assert payload["probe_points"]["compare_length"] == "available"
    assert payload["probe_points"]["compare_unit"] == "available"
    assert payload["probe_points"]["utf16le_payload"] == "inferred"
    assert payload["probe_points"]["base64_material"] == "inferred"
    assert payload["probe_points"]["rc4_key"] == "inferred"
    assert payload["probe_points"]["pre_rc4_runtime_material"] == "unavailable"
    assert payload["candidate_results"][0]["first_failing_wchar"]["index"] == 2


def test_dynamic_compare_path_probe_preserves_existing_selection_behavior(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search,
        "validate_compare_aware_results",
        _fake_dynamic_probe_validate(tmp_path),
    )

    result = run_dynamic_compare_path_probe(
        target=target,
        artifacts_dir=tmp_path / "dynamic_compare_path_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["promotable_validations"] == []
    assert result["promotable_validations"] == []
    assert payload["final_selection_changed"] is False


def _fake_pre_rc4_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    materials_path = Path(command[command.index("--materials") + 1])
    materials = json.loads(materials_path.read_text(encoding="utf-8"))
    material_by_name = {item["name"]: item for item in materials["materials"]}
    available_names = {"utf16le_payload", "base64_ascii", "rc4_output", "compare_buffer"}
    matches = [
        {
            "material": name,
            "status": "available" if name in available_names else "unavailable",
            "match_kind": "prefix" if name in available_names else "",
            "address": "0x1000" if name in available_names else "",
            "protection": "rw-" if name in available_names else "",
            "size": 16 if name in available_names else 0,
            "preview_hex": str(material_by_name[name].get("hex", ""))[:64] if name in available_names else "",
        }
        for name in material_by_name
    ]
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "pre rc4 ok",
                "candidate_hex": command[command.index("--probe-hex") + 1],
                "compare_hit": True,
                "matches": matches,
                "probe_points": {
                    "raw_input": "unavailable",
                    "expanded_bytes": "unavailable",
                    "utf16le_payload": "available",
                    "base64_material": "available",
                    "rc4_ksa_key": "unavailable",
                    "rc4_encrypted_const": "unavailable",
                    "rc4_output": "available",
                    "compare_buffer": "available",
                },
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def test_pre_rc4_material_probe_has_bounded_candidate_count_and_schema(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_pre_rc4_subprocess_run)
    monkeypatch.setattr(compare_aware_search, "_latest_producer_material_previews", lambda: {})

    result = run_pre_rc4_material_probe(
        target=target,
        artifacts_dir=tmp_path / "pre_rc4_material_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == PRE_RC4_MATERIAL_PROBE_FILE_NAME
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["runtime_backed_count"] == 3
    assert payload["classification"] in {"material_chain_agrees", "needs_compare_path_discovery"}
    assert payload["probe_points"]["base64_material"] == "available"
    assert payload["probe_points"]["rc4_output"] == "available"
    assert payload["rc4_key_status"] == "inferred"
    assert payload["rc4_input_status"] == "confirmed"
    assert payload["first_divergence_stage"] == ""
    assert payload["offline_runtime_agreement_table"][0]["utf16_agree"] is True
    assert payload["offline_runtime_agreement_table"][0]["base64_agree"] is True
    assert payload["offline_runtime_agreement_table"][0]["rc4_agree"] is True
    assert payload["producer_material_relation_table"][0]["rc4_to_producer_relation"] in {
        "exact",
        "prefix",
        "slice",
        "no_match",
    }
    assert payload["promotable_validations"] == []


def test_pre_rc4_material_probe_relates_rc4_output_to_latest_producer_buffer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    first_candidate = compare_aware_search.PRE_RC4_MATERIAL_PROBE_CANDIDATES[0]
    expected = compare_aware_search._pre_rc4_expected_materials(first_candidate)
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_pre_rc4_subprocess_run)
    monkeypatch.setattr(
        compare_aware_search,
        "_latest_producer_material_previews",
        lambda: {
            first_candidate: {
                "producer_eax_preview_hex": str(expected["rc4_output_hex"])[:64],
                "producer_lhs_slot_preview_hex": "",
            }
        },
    )

    result = run_pre_rc4_material_probe(
        target=target,
        artifacts_dir=tmp_path / "pre_rc4_material_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "needs_compare_path_discovery"
    first_relation = payload["producer_material_relation_table"][0]
    assert first_relation["rc4_to_producer_eax_relation"] in {"exact", "prefix"}
    assert first_relation["rc4_to_producer_relation"] in {"exact", "prefix"}


def test_pre_rc4_material_probe_does_not_expand_search_or_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_pre_rc4_subprocess_run)
    monkeypatch.setattr(compare_aware_search, "_latest_producer_material_previews", lambda: {})

    result = run_pre_rc4_material_probe(
        target=target,
        artifacts_dir=tmp_path / "pre_rc4_material_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert result["promotable_validations"] == []


def test_pre_rc4_material_probe_exact2_failure_trace_has_offsets_and_dependencies(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_pre_rc4_subprocess_run)
    monkeypatch.setattr(compare_aware_search, "_latest_producer_material_previews", lambda: {})

    result = run_pre_rc4_material_probe(
        target=target,
        artifacts_dir=tmp_path / "pre_rc4_material_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    failure = result["payload"]["exact2_failure_trace"]
    assert failure["wchar_index"] == 2
    assert failure["runtime_word"] == "4464"
    assert failure["target_word"] == "6100"
    assert failure["rc4_output_offsets"] == [4, 5]
    assert failure["encrypted_const_bytes"]
    assert failure["keystream_bytes"]
    assert "candidate_byte_dependencies" in failure["base64_key_dependency"]


def test_material_capture_partial_triggers_base64_rc4_breakpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {
            "latest_pre_rc4_material_probe": {"classification": "material_capture_partial"}
        }
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", lambda kind: ({}, None))

    assert compare_aware_search._prior_pre_rc4_probe_needs_breakpoint() is True


def _fake_base64_rc4_static_points(target: Path) -> dict[str, list[dict[str, object]]]:
    _ = target
    return {
        "utf16le": [
            {
                "kind": "utf16le",
                "name": "utf16le_unresolved",
                "address": "",
                "module_offset": None,
                "confidence": "low",
                "evidence": ["not located"],
                "hook_kind": "memory_access",
                "hookable": False,
                "size": 1,
            }
        ],
        "base64": [
            {
                "kind": "base64",
                "name": "standard_base64_alphabet",
                "address": "module+0x3000",
                "module_offset": 0x3000,
                "confidence": "high",
                "evidence": ["standard alphabet"],
                "hook_kind": "memory_access",
                "hookable": True,
                "size": 64,
            }
        ],
        "rc4_ksa": [],
        "rc4_prga": [],
        "encrypted_const": [
            {
                "kind": "encrypted_const",
                "name": "modeled_rc4_encrypted_const",
                "address": "module+0x4000",
                "module_offset": 0x4000,
                "confidence": "high",
                "evidence": ["const prefix"],
                "hook_kind": "memory_access",
                "hookable": True,
                "size": 64,
            }
        ],
    }


def _fake_base64_rc4_instruction_static_points(target: Path) -> dict[str, list[dict[str, object]]]:
    points = _fake_base64_rc4_static_points(target)
    points["base64_output"] = [
        {
            "kind": "base64_output",
            "name": "base64_output_write",
            "address": "module+0x2345",
            "module_offset": 0x2345,
            "confidence": "high",
            "evidence": ["instruction-confirmed base64 output write"],
            "hook_kind": "interceptor",
            "hookable": True,
            "candidate_dependent": True,
            "connects_to_compare_lhs": True,
            "size": 1,
        }
    ]
    return points


def _fake_base64_rc4_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    utf16_payload_hex = trace_candidate_transform(candidate_hex)["utf16_payload"]["raw_hex"]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert "base64" in points_payload["static_points"]
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "breakpoint ok",
                "candidate_hex": candidate_hex,
                "static_points": points_payload["static_points"],
                "hook_events": [
                    {
                        "point_kind": "base64",
                        "point_name": "standard_base64_alphabet",
                        "hook_kind": "memory_access",
                        "address": "0x403000",
                        "module_offset": "0x3000",
                        "operation": "read",
                        "from": "0x401234",
                        "hit_count": 1,
                        "buffer_preview_hex": "41424344",
                        "buffer_preview_ascii": "ABCD",
                    },
                    {
                        "point_kind": "compare",
                        "point_name": "wide_flag_prefix_compare",
                        "hook_kind": "interceptor",
                        "address": "0x40258c",
                        "module_offset": "0x258c",
                        "hit_count": 1,
                        "lhs_ptr": "0x1000",
                        "rhs_ptr": "0x2000",
                        "compare_count": 5,
                        "registers": {"esp": "0x12fdcb8", "ebp": "0x12fee44"},
                        "stack_preview_hex": "00" * 40 + utf16_payload_hex[:64],
                        "lhs_preview_hex": "46006c004464830d311c",
                        "rhs_preview_hex": "66006c00610067007b00",
                    },
                ],
                "hook_results": {
                    "utf16le_payload": "unavailable",
                    "base64_input": "inferred",
                    "base64_output": "inferred",
                    "rc4_key": "unavailable",
                    "rc4_input": "unavailable",
                    "rc4_output": "unavailable",
                    "compare_buffer": "available",
                },
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_base64_rc4_compare_only_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "compare only",
                "candidate_hex": candidate_hex,
                "static_points": points_payload["static_points"],
                "hook_events": [
                    {
                        "point_kind": "compare",
                        "point_name": "wide_flag_prefix_compare",
                        "hook_kind": "interceptor",
                        "address": "0x40258c",
                        "module_offset": "0x258c",
                        "hit_count": 1,
                        "lhs_preview_hex": "46006c004464830d311c",
                        "rhs_preview_hex": "66006c00610067007b00",
                    }
                ],
                "hook_results": {
                    "utf16le_payload": "unavailable",
                    "base64_input": "unavailable",
                    "base64_output": "unavailable",
                    "rc4_key": "unavailable",
                    "rc4_input": "unavailable",
                    "rc4_output": "unavailable",
                    "compare_buffer": "available",
                },
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_compare_handoff_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} >= {
        "pre_lhs_slot_store",
        "handoff_helper_enter",
        "post_handoff_lhs_reload",
        "wide_flag_prefix_compare",
    }
    lhs_preview = "46006c004464830d311c701038525b85"
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "handoff ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "pre_lhs_slot_store",
                        "address": "0x40253a",
                        "module_offset": "0x253a",
                        "registers": {"eax": "0x419cea8", "esi": "0x0", "esp": "0x12fdc90", "ebp": "0x12fee44"},
                        "stack_preview_hex": "00" * 32,
                        "lhs_slot_ptr": "0x0",
                        "eax_ptr": "0x419cea8",
                        "eax_preview_hex": lhs_preview,
                        "esi_ptr": "0x0",
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                    {
                        "hook_name": "handoff_helper_enter",
                        "address": "0x401b50",
                        "module_offset": "0x1b50",
                        "registers": {"eax": "0x419cea8", "esi": "0x0", "esp": "0x12fdc80", "ebp": "0x12fee44"},
                        "stack_preview_hex": "11" * 32,
                        "lhs_slot_ptr": "0x419cea8",
                        "lhs_slot_preview_hex": lhs_preview,
                        "eax_ptr": "0x419cea8",
                        "eax_preview_hex": lhs_preview,
                        "esi_ptr": "0x0",
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                    {
                        "hook_name": "handoff_helper_return",
                        "address": "0x401b50",
                        "module_offset": "0x1b50",
                        "registers": {"eax": "0x419cea8", "esi": "0x0", "esp": "0x12fdc80", "ebp": "0x12fee44"},
                        "stack_preview_hex": "22" * 32,
                        "lhs_slot_ptr": "0x419cea8",
                        "lhs_slot_preview_hex": lhs_preview,
                        "eax_ptr": "0x419cea8",
                        "eax_preview_hex": lhs_preview,
                        "esi_ptr": "0x0",
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                    {
                        "hook_name": "post_handoff_lhs_reload",
                        "address": "0x402559",
                        "module_offset": "0x2559",
                        "registers": {"eax": "0x419cea8", "esi": "0x0", "esp": "0x12fdc90", "ebp": "0x12fee44"},
                        "stack_preview_hex": "33" * 32,
                        "lhs_slot_ptr": "0x419cea8",
                        "lhs_slot_preview_hex": lhs_preview,
                        "eax_ptr": "0x419cea8",
                        "eax_preview_hex": lhs_preview,
                        "esi_ptr": "0x0",
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                    {
                        "hook_name": "wide_flag_prefix_compare",
                        "address": "0x40258c",
                        "module_offset": "0x258c",
                        "registers": {"eax": "0x0", "esi": "0x419cea8", "esp": "0x12fdc88", "ebp": "0x12fee44"},
                        "stack_preview_hex": "44" * 32,
                        "lhs_slot_ptr": "0x419cea8",
                        "esi_ptr": "0x419cea8",
                        "esi_preview_hex": lhs_preview,
                        "lhs_ptr": "0x419cea8",
                        "rhs_ptr": "0x551c4c",
                        "compare_count": 5,
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                ],
                "hook_results": {
                    "handoff_helper_enter": "available",
                    "handoff_helper_return": "available",
                    "post_handoff_lhs_reload": "available",
                    "compare_lhs_buffer": "available",
                    "lhs_slot": "available",
                },
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_compare_handoff_slice_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} >= {
        "pre_handoff_call",
        "handoff_helper_enter",
        "post_handoff_after_reload",
        "wide_flag_prefix_compare",
    }
    lhs_preview = "46006c004464830d311c701038525b85"
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "slice ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "pre_handoff_call",
                        "address": "0x402554",
                        "module_offset": "0x2554",
                        "registers": {
                            "eax": "0x419cea8",
                            "ecx": "0x12fee00",
                            "edx": "0x12fdc80",
                            "esi": "0x12fdd00",
                            "esp": "0x12fdc80",
                            "ebp": "0x12fee44",
                        },
                        "stack_preview_hex": "11" * 64,
                        "stack_words": [{"index": 0, "value": "0x402559", "module_offset": "0x2559"}],
                        "return_address": "0x402559",
                        "return_address_module_offset": "0x2559",
                        "lhs_slot_ptr": "0x419cea8",
                        "lhs_slot_preview_hex": lhs_preview,
                        "eax_ptr": "0x419cea8",
                        "eax_preview_hex": lhs_preview,
                        "esi_ptr": "0x12fdd00",
                        "esi_preview_hex": "aa" * 16,
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                    {
                        "hook_name": "handoff_helper_enter",
                        "address": "0x401b50",
                        "module_offset": "0x1b50",
                        "registers": {
                            "eax": "0x419cea8",
                            "ecx": "0x12fee00",
                            "edx": "0x12fdc80",
                            "esi": "0x12fdd00",
                            "esp": "0x12fdc7c",
                            "ebp": "0x12fee44",
                        },
                        "stack_preview_hex": "22" * 64,
                        "stack_words": [{"index": 0, "value": "0x402559", "module_offset": "0x2559"}],
                        "return_address": "0x402559",
                        "return_address_module_offset": "0x2559",
                        "lhs_slot_ptr": "0x419cea8",
                        "lhs_slot_preview_hex": lhs_preview,
                        "eax_ptr": "0x419cea8",
                        "eax_preview_hex": lhs_preview,
                        "esi_ptr": "0x12fdd00",
                        "esi_preview_hex": "aa" * 16,
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                    {
                        "hook_name": "handoff_helper_return",
                        "address": "0x401b50",
                        "module_offset": "0x1b50",
                        "registers": {
                            "eax": "0x419cea8",
                            "esi": "0x12fdd00",
                            "esp": "0x12fdc7c",
                            "ebp": "0x12fee44",
                        },
                        "stack_preview_hex": "33" * 64,
                        "stack_words": [{"index": 0, "value": "0x402559", "module_offset": "0x2559"}],
                        "return_address": "0x402559",
                        "return_address_module_offset": "0x2559",
                        "lhs_slot_ptr": "0x419cea8",
                        "lhs_slot_preview_hex": lhs_preview,
                        "eax_ptr": "0x419cea8",
                        "eax_preview_hex": lhs_preview,
                        "esi_ptr": "0x12fdd00",
                        "esi_preview_hex": "aa" * 16,
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                    {
                        "hook_name": "post_handoff_after_reload",
                        "address": "0x40255c",
                        "module_offset": "0x255c",
                        "registers": {"eax": "0x419cea8", "esi": "0x419cea8", "esp": "0x12fdc90", "ebp": "0x12fee44"},
                        "stack_preview_hex": "44" * 64,
                        "lhs_slot_ptr": "0x419cea8",
                        "lhs_slot_preview_hex": lhs_preview,
                        "eax_ptr": "0x419cea8",
                        "eax_preview_hex": lhs_preview,
                        "esi_ptr": "0x419cea8",
                        "esi_preview_hex": lhs_preview,
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                    {
                        "hook_name": "wide_flag_prefix_compare",
                        "address": "0x40258c",
                        "module_offset": "0x258c",
                        "registers": {"eax": "0x0", "esi": "0x419cea8", "esp": "0x12fdc88", "ebp": "0x12fee44"},
                        "stack_preview_hex": "55" * 64,
                        "lhs_slot_ptr": "0x419cea8",
                        "esi_ptr": "0x419cea8",
                        "esi_preview_hex": lhs_preview,
                        "lhs_ptr": "0x419cea8",
                        "rhs_ptr": "0x551c4c",
                        "compare_count": 5,
                        "lhs_buffer_preview_hex": lhs_preview,
                    },
                ],
                "hook_results": {
                    "handoff_helper_enter": "available",
                    "handoff_helper_return": "available",
                    "post_handoff_lhs_reload": "unavailable",
                    "post_handoff_after_reload": "available",
                    "compare_lhs_buffer": "available",
                    "lhs_slot": "available",
                },
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_compare_handoff_return_site_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} >= {
        "handoff_helper_enter",
        "post_handoff_after_reload",
        "wide_flag_prefix_compare",
    }
    candidate_preview = (
        "46006c004464830d311c701038525b85"
        if candidate_hex.startswith("78d540")
        else "460061357f0b8c688502de328c19e029"
    )
    target_preview = "66006c00610067007b00000046006c0061006700"
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "return-site ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "handoff_helper_enter",
                        "address": "0x401b50",
                        "module_offset": "0x1b50",
                        "registers": {"esp": "0x12fdc7c", "ebp": "0x12fee44", "eax": "0x0", "esi": "0x54d73c"},
                        "stack_words": [{"index": 0, "value": "0x40233d", "module_offset": "0x233d"}],
                        "return_address": "0x40233d",
                        "return_address_module_offset": "0x233d",
                        "lhs_slot_ptr": "0x75e1af70",
                        "lhs_slot_preview_hex": "8bf08975e4c745fcfe",
                        "eax_ptr": "0x0",
                        "esi_ptr": "0x54d73c",
                        "lhs_buffer_preview_hex": "8bf08975e4c745fcfe",
                    },
                    {
                        "hook_name": "handoff_helper_return",
                        "address": "0x401b50",
                        "module_offset": "0x1b50",
                        "registers": {"esp": "0x12fdc7c", "ebp": "0x12fee44", "eax": "0x36dce20", "esi": "0x54d73c"},
                        "stack_words": [{"index": 0, "value": "0x40233d", "module_offset": "0x233d"}],
                        "return_address": "0x40233d",
                        "return_address_module_offset": "0x233d",
                        "helper_enter_return_address": "0x40233d",
                        "helper_enter_return_address_module_offset": "0x233d",
                        "lhs_slot_ptr": "0x75e1af70",
                        "lhs_slot_preview_hex": "8bf08975e4c745fcfe",
                        "eax_ptr": "0x36dce20",
                        "eax_preview_hex": candidate_preview,
                        "esi_ptr": "0x54d73c",
                        "esi_preview_hex": "aa" * 16,
                        "lhs_buffer_preview_hex": candidate_preview,
                    },
                    {
                        "hook_name": "helper_return_site_0x233d",
                        "address": "0x40233d",
                        "module_offset": "0x233d",
                        "registers": {"esp": "0x12fdc84", "ebp": "0x12fee44", "eax": "0x36dce20", "esi": "0x54d73c"},
                        "lhs_slot_ptr": "0x75e1af70",
                        "lhs_slot_preview_hex": "8bf08975e4c745fcfe",
                        "eax_ptr": "0x36dce20",
                        "eax_preview_hex": candidate_preview,
                        "esi_ptr": "0x54d73c",
                        "esi_preview_hex": "aa" * 16,
                        "lhs_buffer_preview_hex": "8bf08975e4c745fcfe",
                    },
                    {
                        "hook_name": "wide_flag_prefix_compare",
                        "address": "0x40258c",
                        "module_offset": "0x258c",
                        "registers": {"esp": "0x12fdc88", "ebp": "0x12fee44", "eax": "0x0", "esi": "0x36dce20"},
                        "lhs_ptr": "0x551c4c",
                        "rhs_ptr": "0x36dce20",
                        "compare_count": 5,
                        "compare_args": {
                            "convention": "call-site stack before call: [esp+0]=lhs, [esp+4]=rhs, [esp+8]=count",
                            "args": [
                                {
                                    "index": 0,
                                    "esp_relative": "+0x0",
                                    "value": "0x551c4c",
                                    "preview_hex": target_preview,
                                    "preview_utf16le": "flag{",
                                    "looks_like_flag_target": True,
                                },
                                {
                                    "index": 1,
                                    "esp_relative": "+0x4",
                                    "value": "0x36dce20",
                                    "preview_hex": candidate_preview,
                                    "preview_utf16le": "Fl",
                                    "looks_like_flag_target": False,
                                },
                                {"index": 2, "esp_relative": "+0x8", "value_u32": 5},
                            ],
                        },
                        "lhs_buffer_preview_hex": target_preview,
                        "lhs_buffer_preview_utf16le": "flag{",
                    },
                ],
                "hook_results": {
                    "handoff_helper_enter": "available",
                    "handoff_helper_return": "available",
                    "helper_return_site": "available",
                    "wide_flag_prefix_compare": "available",
                    "compare_call_args": "available",
                    "lhs_slot": "available",
                },
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_compare_producer_trace_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} >= {
        "producer_return_site",
        "compare_helper_entry",
        "pre_compare_push_esi",
    }
    candidate_preview = (
        "46006c004464830d311c701038525b85"
        if candidate_hex.startswith("78d540")
        else "460061357f0b8c688502de328c19e029"
    )
    target_preview = "66006c00610067007b00000046006c0061006700"
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "producer trace ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "producer_return_site",
                        "address": "0x40233d",
                        "module_offset": "0x233d",
                        "registers": {
                            "esp": "0x12fdc84",
                            "ebp": "0x12fee44",
                            "eax": "0x36dce20",
                            "esi": "0x54d73c",
                            "edi": "0x36dce20",
                        },
                        "stack_words": [{"index": 0, "value": "0x403000", "module_offset": "0x3000"}],
                        "frame_slots": [
                            {
                                "name": "[ebp-0x1170]",
                                "value": "0x36dce20",
                                "preview_hex": candidate_preview,
                                "preview_utf16le": "Fl",
                            }
                        ],
                        "lhs_slot_ptr": "0x36dce20",
                        "lhs_slot_preview_hex": candidate_preview,
                        "eax_ptr": "0x36dce20",
                        "eax_preview_hex": candidate_preview,
                        "esi_ptr": "0x54d73c",
                        "esi_preview_hex": "aa" * 16,
                        "edi_ptr": "0x36dce20",
                        "edi_preview_hex": candidate_preview,
                    },
                    {
                        "hook_name": "compare_helper_entry",
                        "address": "0x5028ac",
                        "module_offset": "0x1028ac",
                        "registers": {"esp": "0x12fdc80", "ebp": "0x12fee44", "eax": "0x0", "esi": "0x36dce20"},
                        "compare_entry": {
                            "convention": "callee entry stack",
                            "caller_return_address": "0x402591",
                            "caller_return_module_offset": "0x2591",
                            "slots": [
                                {
                                    "index": 0,
                                    "role": "return_address",
                                    "value": "0x402591",
                                    "module_offset": "0x2591",
                                },
                                {
                                    "index": 1,
                                    "role": "arg0",
                                    "value": "0x36dce20",
                                    "preview_hex": candidate_preview,
                                    "preview_utf16le": "Fl",
                                },
                                {
                                    "index": 2,
                                    "role": "arg1",
                                    "value": "0x551c4c",
                                    "preview_hex": target_preview,
                                    "preview_utf16le": "flag{",
                                    "looks_like_flag_target": True,
                                },
                                {"index": 3, "role": "arg2_count", "value_u32": 5},
                            ],
                        },
                        "lhs_slot_ptr": "0x36dce20",
                        "lhs_slot_preview_hex": candidate_preview,
                        "eax_ptr": "0x0",
                        "esi_ptr": "0x36dce20",
                        "esi_preview_hex": candidate_preview,
                        "edi_ptr": "0x36dce20",
                        "edi_preview_hex": candidate_preview,
                    },
                    {
                        "hook_name": "wide_flag_prefix_compare",
                        "address": "0x40258c",
                        "module_offset": "0x258c",
                        "registers": {"esp": "0x12fdc88", "ebp": "0x12fee44", "eax": "0x0", "esi": "0x36dce20"},
                        "compare_args": {
                            "args": [
                                {"index": 0, "value": "0x36dce20", "preview_hex": candidate_preview},
                                {
                                    "index": 1,
                                    "value": "0x551c4c",
                                    "preview_hex": target_preview,
                                    "preview_utf16le": "flag{",
                                },
                                {"index": 2, "value_u32": 5},
                            ]
                        },
                    },
                ],
                "hook_results": {
                    "producer_return_site": "available",
                    "compare_helper_entry": "available",
                    "compare_entry_args": "available",
                    "wide_flag_prefix_compare": "available",
                    "compare_call_args": "available",
                    "lhs_slot": "available",
                },
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_compare_producer_trace_material_hook_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    proc = _fake_compare_producer_trace_subprocess_run(*args, **kwargs)
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    payload["material_hook_candidates"] = [
        {
            "kind": "base64_output",
            "name": "base64_output_write",
            "module_offset": "0x2345",
            "address": "module+0x2345",
            "instruction": "mov byte ptr [edi], al",
            "hookable": True,
            "instruction_confirmed": True,
            "preview_hex": "516c5a735245526b6844307848413d3d",
            "evidence": ["bounded producer backtrace reached instruction-confirmed material write"],
        }
    ]
    out_path.write_text(json.dumps(payload), encoding="utf-8")
    return proc


def _fake_material_confirmation_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    expected_preview = command[command.index("--expected-eax-preview") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} >= {
        "producer_pre_material_call",
        "producer_return_site",
        "producer_pre_output_call",
    }
    first_preview = expected_preview or (
        "938f65518476c65ba5942f6620003a0020007800d5014000"
        if candidate_hex.startswith("78d540")
        else "938f65518476c65ba5942f6620003a0020005a003e007f01"
    )
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "material confirmation ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "producer_pre_material_call",
                        "module_offset": "0x2338",
                        "instruction": "call 0x401b50",
                        "registers": {"eax": "0x10", "ecx": "0x20", "edx": "0x30"},
                        "eax_ptr": "0x10",
                        "eax_preview_hex": "aa" * 16,
                        "ecx_ptr": "0x20",
                        "ecx_preview_hex": "bb" * 16,
                        "edx_ptr": "0x30",
                        "edx_preview_hex": "cc" * 16,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": False,
                    },
                    {
                        "hook_name": "producer_return_site",
                        "module_offset": "0x233d",
                        "instruction": "mov edx, dword ptr [ebp - 0x116c]",
                        "registers": {"eax": "0x40", "ecx": "0x20", "edx": "0x30"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": first_preview,
                        "ecx_ptr": "0x20",
                        "ecx_preview_hex": "bb" * 16,
                        "edx_ptr": "0x30",
                        "edx_preview_hex": "cc" * 16,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": bool(expected_preview),
                    },
                    {
                        "hook_name": "producer_pre_output_call",
                        "module_offset": "0x234e",
                        "instruction": "call 0x4018cd",
                        "registers": {"eax": "0x40", "ecx": "0x50", "edx": "0x40"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": first_preview,
                        "ecx_ptr": "0x50",
                        "ecx_preview_hex": "dd" * 16,
                        "edx_ptr": "0x40",
                        "edx_preview_hex": first_preview,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": bool(expected_preview),
                    },
                ],
                "confirmed_material_hook_candidates": [],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_material_confirmation_ready_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    proc = _fake_material_confirmation_subprocess_run(*args, **kwargs)
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    payload["confirmed_material_hook_candidates"] = [
        {
            "kind": "base64_output",
            "name": "producer_confirmed_base64_output",
            "module_offset": "0x234e",
            "rva": "0x234e",
            "address": "module+0x234e",
            "instruction": "call 0x4018cd",
            "hook_kind": "interceptor",
            "hookable": True,
            "instruction_confirmed": True,
            "candidate_dependent": True,
            "connects_to_compare_lhs": True,
            "preview_hex": "516c5a735245526b6844307848413d3d",
            "evidence": ["material confirmation linked producer EAX to Base64 output"],
        }
    ]
    out_path.write_text(json.dumps(payload), encoding="utf-8")
    return proc


def _fake_pre_compare_handoff_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    expected_preview = command[command.index("--expected-eax-preview") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} >= {
        "producer_return_site",
        "producer_pre_candidate_push",
        "producer_pre_output_call",
        "producer_pre_second_call",
        "compare_helper_entry",
    }
    first_preview = expected_preview or (
        "938f65518476c65ba5942f6620003a0020007800d5014000"
        if candidate_hex.startswith("78d540")
        else "938f65518476c65ba5942f6620005a003e007f014600"
    )
    compare_arg0 = "66006c00610067007b00"
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "pre-compare handoff ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "producer_return_site",
                        "module_offset": "0x233d",
                        "instruction": "mov edx, dword ptr [ebp - 0x116c]",
                        "registers": {"eax": "0x40", "ecx": "0x20", "edx": "0x30"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": first_preview,
                        "edx_ptr": "0x30",
                        "edx_preview_hex": "cc" * 16,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": bool(expected_preview),
                    },
                    {
                        "hook_name": "producer_pre_candidate_push",
                        "module_offset": "0x2346",
                        "instruction": "push edx",
                        "registers": {"eax": "0x40", "ecx": "0x20", "edx": "0x40"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": first_preview,
                        "edx_ptr": "0x40",
                        "edx_preview_hex": first_preview,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": bool(expected_preview),
                    },
                    {
                        "hook_name": "compare_helper_entry",
                        "module_offset": "0x1028ac",
                        "instruction": "case-insensitive wide compare helper entry",
                        "registers": {"esp": "0x1000"},
                        "stack_words": [
                            {"index": 0, "value": "0x9999", "preview_hex": ""},
                            {"index": 1, "value": "0x40", "preview_hex": first_preview},
                            {"index": 2, "value": "0x50", "preview_hex": compare_arg0},
                            {"index": 3, "value": "0x5", "preview_hex": ""},
                        ],
                        "compare_args": {
                            "args": [
                                {"index": 0, "value": "0x40", "preview_hex": first_preview},
                                {"index": 1, "value": "0x50", "preview_hex": compare_arg0},
                                {"index": 2, "value_u32": 5},
                            ]
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _compare_lhs_candidate_result(
    candidate_hex: str,
    ptr: str,
    preview: str,
    *,
    connect_to_arg0: bool = True,
) -> dict[str, object]:
    arg_ptr = ptr if connect_to_arg0 else "0x9000"
    arg_preview = preview if connect_to_arg0 else "ff" * 32
    slot_preview = preview
    return {
        "label": "test",
        "candidate_hex": candidate_hex,
        "candidate_prefix": candidate_hex[:16],
        "runtime_backed": True,
        "success": True,
        "hook_observations": [
            {
                "candidate_hex": candidate_hex,
                "hook_name": "pre_lhs_slot_store",
                "module_offset": "0x253a",
                "instruction": "mov dword ptr [ebp - 0x1170], eax",
                "registers": {"eax": ptr},
                "eax_ptr": ptr,
                "eax_preview_hex": preview,
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "pre_handoff_call",
                "module_offset": "0x2554",
                "instruction": "call 0x401b50",
                "frame_slots": [
                    {
                        "name": "[ebp-0x1170]",
                        "offset": "-0x1170",
                        "value": ptr,
                        "preview_hex": slot_preview,
                    }
                ],
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "post_handoff_lhs_reload",
                "module_offset": "0x2559",
                "instruction": "mov esi, dword ptr [ebp - 0x1170]",
                "frame_slots": [
                    {
                        "name": "[ebp-0x1170]",
                        "offset": "-0x1170",
                        "value": ptr,
                        "preview_hex": slot_preview,
                    }
                ],
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "pre_compare_lhs_push",
                "module_offset": "0x258b",
                "instruction": "push esi",
                "registers": {"esi": ptr},
                "esi_ptr": ptr,
                "esi_preview_hex": preview,
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "compare_helper_entry",
                "module_offset": "0x1028ac",
                "instruction": "compare helper entry",
                "compare_args": {
                    "args": [
                        {"index": 0, "role": "arg0", "value": arg_ptr, "preview_hex": arg_preview},
                        {"index": 1, "role": "arg1", "value": "0x5000", "preview_hex": "66006c00610067007b00"},
                        {"index": 2, "role": "arg2", "value_u32": 5},
                    ]
                },
            },
        ],
    }


def _fake_compare_lhs_producer_audit_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "pre_lhs_slot_store",
        "pre_handoff_call",
        "post_handoff_lhs_reload",
        "pre_compare_lhs_push",
        "compare_helper_entry",
    }
    previews = {
        "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
        "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
        "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
    }
    ptr, preview = previews[candidate_hex]
    candidate = _compare_lhs_candidate_result(candidate_hex, ptr, preview)
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "compare lhs producer audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": candidate["hook_observations"],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _compare_lhs_upstream_candidate_result(
    candidate_hex: str,
    ptr: str,
    preview: str,
    *,
    connect_to_arg0: bool = True,
) -> dict[str, object]:
    arg_ptr = ptr if connect_to_arg0 else "0x9000"
    arg_preview = preview if connect_to_arg0 else "ff" * 32
    return {
        "label": "test",
        "candidate_hex": candidate_hex,
        "candidate_prefix": candidate_hex[:16],
        "runtime_backed": True,
        "success": True,
        "hook_observations": [
            {
                "candidate_hex": candidate_hex,
                "hook_name": "producer_post_transform_slot_reload",
                "module_offset": "0x2325",
                "instruction": "mov edx, dword ptr [ebp - 0x1168]",
                "edx_ptr": ptr,
                "edx_preview_hex": preview,
                "frame_slots": [
                    {
                        "name": "[ebp-0x1168]",
                        "offset": "-0x1168",
                        "value": ptr,
                        "preview_hex": preview,
                    }
                ],
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "producer_pre_material_call",
                "module_offset": "0x2338",
                "instruction": "call 0x401b50",
                "edx_ptr": ptr,
                "edx_preview_hex": preview,
                "frame_slots": [
                    {
                        "name": "[ebp-0x116c]",
                        "offset": "-0x116c",
                        "value": ptr,
                        "preview_hex": preview,
                    }
                ],
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "downstream_lhs_store_sentinel",
                "module_offset": "0x253a",
                "instruction": "mov dword ptr [ebp - 0x1170], eax",
                "eax_ptr": ptr,
                "eax_preview_hex": preview,
                "frame_slots": [
                    {
                        "name": "[ebp-0x1170]",
                        "offset": "-0x1170",
                        "value": ptr,
                        "preview_hex": preview,
                    }
                ],
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "compare_helper_entry",
                "module_offset": "0x1028ac",
                "instruction": "compare helper entry",
                "compare_args": {
                    "args": [
                        {"index": 0, "role": "arg0", "value": arg_ptr, "preview_hex": arg_preview},
                        {"index": 1, "role": "arg1", "value": "0x5000", "preview_hex": "66006c00610067007b00"},
                        {"index": 2, "role": "arg2", "value_u32": 5},
                    ]
                },
            },
        ],
    }


def _fake_compare_lhs_upstream_writer_audit_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "producer_window_entry",
        "producer_pre_transform_call",
        "producer_post_transform_slot_reload",
        "producer_pre_material_call",
        "downstream_lhs_store_sentinel",
        "compare_helper_entry",
    }
    previews = {
        "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
        "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
        "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
    }
    ptr, preview = previews[candidate_hex]
    candidate = _compare_lhs_upstream_candidate_result(candidate_hex, ptr, preview)
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "compare lhs upstream writer audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": candidate["hook_observations"],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _compare_callsite_reanchor_candidate_result(
    candidate_hex: str,
    ptr: str,
    preview: str,
    *,
    old_frame_matches: bool = False,
    producer_matches: bool = True,
    compare_hook_name: str = "actual_compare_entry",
) -> dict[str, object]:
    old_ptr = ptr if old_frame_matches else "0x8800"
    old_preview = preview if old_frame_matches else "ee" * 32
    producer_ptr = ptr if producer_matches else "0x9900"
    producer_preview = preview if producer_matches else "dd" * 32
    compare_module_offset = "0x258c" if compare_hook_name == "static_compare_callsite" else "0x1028ac"
    compare_args = (
        [
            {"index": 0, "role": "arg0", "value": ptr, "preview_hex": preview},
            {"index": 1, "role": "arg1", "value": "0x5000", "preview_hex": "66006c00610067007b00"},
            {"index": 2, "role": "arg2", "value_u32": 5},
        ]
        if compare_hook_name == "static_compare_callsite"
        else [
            {"index": 0, "role": "arg0", "value": ptr, "preview_hex": preview},
            {"index": 1, "role": "arg1", "value": "0x5000", "preview_hex": "66006c00610067007b00"},
            {"index": 2, "role": "arg2", "value_u32": 5},
        ]
    )
    return {
        "label": "test",
        "candidate_hex": candidate_hex,
        "candidate_prefix": candidate_hex[:16],
        "runtime_backed": True,
        "success": True,
        "hook_observations": [
            {
                "candidate_hex": candidate_hex,
                "hook_name": compare_hook_name,
                "module_offset": compare_module_offset,
                "instruction": "case-insensitive wide compare helper entry",
                "compare_entry": {
                    "slots": [
                        {"index": 0, "role": "return_address", "value": "0x40258c", "module_offset": "0x258c"},
                        *compare_args,
                    ]
                },
                "compare_args": {"args": compare_args},
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "old_lhs_slot_store",
                "module_offset": "0x253a",
                "instruction": "mov dword ptr [ebp - 0x1170], eax",
                "eax_ptr": old_ptr,
                "eax_preview_hex": old_preview,
                "frame_slots": [
                    {"name": "[ebp-0x1170]", "offset": "-0x1170", "value": old_ptr, "preview_hex": old_preview}
                ],
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "upstream_slot_1168_reload",
                "module_offset": "0x2325",
                "instruction": "mov edx, dword ptr [ebp - 0x1168]",
                "edx_ptr": producer_ptr,
                "edx_preview_hex": producer_preview,
                "frame_slots": [
                    {
                        "name": "[ebp-0x1168]",
                        "offset": "-0x1168",
                        "value": producer_ptr,
                        "preview_hex": producer_preview,
                    }
                ],
            },
        ],
    }


def _fake_compare_callsite_reanchor_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "actual_compare_entry",
        "static_compare_callsite",
        "old_lhs_slot_store",
        "old_lhs_reload",
        "upstream_candidate_context",
        "upstream_slot_1168_reload",
        "upstream_material_call",
    }
    previews = {
        "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
        "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
        "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
    }
    ptr, preview = previews[candidate_hex]
    candidate = _compare_callsite_reanchor_candidate_result(candidate_hex, ptr, preview)
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "compare callsite reanchor audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": candidate["hook_observations"],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _compare_real_lhs_candidate_result(
    candidate_hex: str,
    ptr: str,
    preview: str,
    *,
    esi_matches: bool = True,
    old_frame_matches: bool = False,
    write_events: list[dict[str, object]] | None = None,
    write_monitor_health: dict[str, object] | None = None,
) -> dict[str, object]:
    result = _compare_callsite_reanchor_candidate_result(
        candidate_hex,
        ptr,
        preview,
        old_frame_matches=old_frame_matches,
        producer_matches=False,
        compare_hook_name="static_compare_callsite",
    )
    esi_ptr = ptr if esi_matches else "0xa000"
    esi_preview = preview if esi_matches else "ab" * 32
    result["hook_observations"].append(
        {
            "candidate_hex": candidate_hex,
            "hook_name": "pre_compare_lhs_push",
            "module_offset": "0x258b",
            "instruction": "push esi",
            "esi_ptr": esi_ptr,
            "esi_preview_hex": esi_preview,
        }
    )
    if write_events is not None:
        for observation in result["hook_observations"]:
            if observation["hook_name"] == "static_compare_callsite":
                observation["write_ring_buffer"] = write_events
                if write_monitor_health is not None:
                    observation["write_monitor_health"] = dict(write_monitor_health)
                break
    return result


def _with_arg0_pointer_chain(result: dict[str, object], ptr: str, preview: str) -> dict[str, object]:
    observations = result["hook_observations"]
    for observation in observations:
        if observation.get("hook_name") == "old_lhs_slot_store":
            observation["eax_ptr"] = ptr
            observation["eax_preview_hex"] = preview
            observation["frame_slots"] = [
                {"name": "[ebp-0x1170]", "offset": "-0x1170", "value": ptr, "preview_hex": preview}
            ]
    observations.append(
        {
            "candidate_hex": result["candidate_hex"],
            "hook_name": "post_handoff_lhs_reload",
            "module_offset": "0x2559",
            "instruction": "mov esi, dword ptr [ebp - 0x1170]",
            "esi_ptr": ptr,
            "esi_preview_hex": preview,
            "frame_slots": [
                {"name": "[ebp-0x1170]", "offset": "-0x1170", "value": ptr, "preview_hex": preview}
            ],
        }
    )
    return result


def _fake_compare_real_lhs_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "static_compare_callsite",
        "pre_compare_lhs_push",
        "post_handoff_lhs_reload",
        "old_lhs_slot_store",
    }
    static_point = next(point for point in points_payload["hook_points"] if point["name"] == "static_compare_callsite")
    assert static_point["capture_write_ring"] is True
    previews = {
        "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
        "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
        "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
    }
    ptr, preview = previews[candidate_hex]
    candidate = _compare_real_lhs_candidate_result(candidate_hex, ptr, preview)
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "compare real lhs provenance audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": candidate["hook_observations"],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _compare_esi_source_window_candidate_result(
    candidate_hex: str,
    ptr: str,
    preview: str,
    *,
    initial_matches: bool = True,
    final_matches: bool = False,
    repair_observed: bool = False,
    branch_observed: bool = True,
) -> dict[str, object]:
    result = _compare_callsite_reanchor_candidate_result(
        candidate_hex,
        ptr,
        preview,
        old_frame_matches=False,
        producer_matches=False,
        compare_hook_name="static_compare_callsite",
    )
    observations = list(result["hook_observations"])
    initial_ptr = ptr if initial_matches else "0xa000"
    initial_preview = preview if initial_matches else "10" * 32
    final_ptr = ptr if final_matches else initial_ptr
    final_preview = preview if final_matches else initial_preview
    observations.extend(
        [
            {
                "candidate_hex": candidate_hex,
                "hook_name": "initial_lhs_reload",
                "module_offset": "0x2559",
                "instruction": "mov esi, dword ptr [ebp - 0x1170]",
                "esi_ptr": initial_ptr,
                "esi_preview_hex": initial_preview,
            },
            {
                "candidate_hex": candidate_hex,
                "hook_name": "pre_compare_lhs_push",
                "module_offset": "0x258b",
                "instruction": "push esi",
                "esi_ptr": ptr,
                "esi_preview_hex": preview,
            },
        ]
    )
    if branch_observed:
        observations.append(
            {
                "candidate_hex": candidate_hex,
                "hook_name": "pre_compare_branch",
                "module_offset": "0x256f",
                "instruction": "jge 0x2584",
                "esi_ptr": initial_ptr,
                "esi_preview_hex": initial_preview,
            }
        )
    if repair_observed:
        observations.extend(
            [
                {
                    "candidate_hex": candidate_hex,
                    "hook_name": "repair_call_input",
                    "module_offset": "0x2573",
                    "instruction": "lea ecx, [ebp - 0x1170]",
                    "ecx_ptr": "0x7000",
                    "frame_slots": [
                        {
                            "name": "[ebp-0x1170]",
                            "offset": "-0x1170",
                            "value": final_ptr,
                            "preview_hex": final_preview,
                        }
                    ],
                },
                {
                    "candidate_hex": candidate_hex,
                    "hook_name": "repair_call_site",
                    "module_offset": "0x2579",
                    "instruction": "call 0x4019e0",
                    "ecx_ptr": "0x7000",
                    "frame_slots": [
                        {
                            "name": "[ebp-0x1170]",
                            "offset": "-0x1170",
                            "value": final_ptr,
                            "preview_hex": final_preview,
                        }
                    ],
                },
            ]
        )
    observations.append(
        {
            "candidate_hex": candidate_hex,
            "hook_name": "final_lhs_reload",
            "module_offset": "0x257e",
            "instruction": "mov esi, dword ptr [ebp - 0x1170]",
            "esi_ptr": final_ptr,
            "esi_preview_hex": final_preview,
        }
    )
    result["hook_observations"] = observations
    return result


def _compare_esi_source_window_candidates(**kwargs) -> list[dict[str, object]]:
    return [
        _compare_esi_source_window_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
            **kwargs,
        ),
        _compare_esi_source_window_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
            **kwargs,
        ),
        _compare_esi_source_window_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
            **kwargs,
        ),
    ]


def _fake_compare_esi_source_window_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "static_compare_callsite",
        "initial_lhs_reload",
        "esi_length_load",
        "esi_length_sub",
        "pre_compare_branch",
        "repair_call_input",
        "repair_call_site",
        "final_lhs_reload",
        "compare_count_push",
        "compare_flag_push",
        "pre_compare_lhs_push",
    }
    previews = {
        "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
        "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
        "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
    }
    ptr, preview = previews[candidate_hex]
    candidate = _compare_esi_source_window_candidate_result(candidate_hex, ptr, preview)
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "compare ESI source window audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": candidate["hook_observations"],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _compare_lhs_slot_writer_source_candidate_result(
    candidate_hex: str,
    ptr: str,
    preview: str,
    *,
    slot_writer_observed: bool = True,
    slot_writer_matches: bool = True,
    source_matches: bool = False,
) -> dict[str, object]:
    result = _compare_callsite_reanchor_candidate_result(
        candidate_hex,
        ptr,
        preview,
        old_frame_matches=False,
        producer_matches=source_matches,
        compare_hook_name="static_compare_callsite",
    )
    observations = [
        item
        for item in result["hook_observations"]
        if item["hook_name"] in {"static_compare_callsite", "upstream_slot_1168_reload"}
    ]
    if slot_writer_observed:
        writer_ptr = ptr if slot_writer_matches else "0xa000"
        writer_preview = preview if slot_writer_matches else "10" * 32
        observations.append(
            {
                "candidate_hex": candidate_hex,
                "hook_name": "slot_writer",
                "module_offset": "0x253a",
                "instruction": "mov dword ptr [ebp - 0x1170], eax",
                "eax_ptr": writer_ptr,
                "eax_preview_hex": writer_preview,
                "frame_slots": [
                    {
                        "name": "[ebp-0x1170]",
                        "offset": "-0x1170",
                        "value": writer_ptr,
                        "preview_hex": writer_preview,
                    }
                ],
            }
        )
    return {
        **result,
        "hook_observations": observations,
    }


def _compare_lhs_slot_writer_source_candidates(**kwargs) -> list[dict[str, object]]:
    return [
        _compare_lhs_slot_writer_source_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
            **kwargs,
        ),
        _compare_lhs_slot_writer_source_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
            **kwargs,
        ),
        _compare_lhs_slot_writer_source_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
            **kwargs,
        ),
    ]


def _fake_compare_lhs_slot_writer_source_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "static_compare_callsite",
        "slot_writer",
        "upstream_candidate_context",
        "upstream_slot_1168_reload",
        "upstream_material_call",
        "upstream_output_call",
        "upstream_output_return",
        "upstream_second_call",
    }
    previews = {
        "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
        "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
        "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
    }
    ptr, preview = previews[candidate_hex]
    candidate = _compare_lhs_slot_writer_source_candidate_result(candidate_hex, ptr, preview)
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "compare lhs slot writer/source audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": candidate["hook_observations"],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _compare_lhs_slot_writer_predecessor_candidate_result(
    candidate_hex: str,
    ptr: str,
    preview: str,
    *,
    handoff_return_observed: bool = True,
    downstream_output_observed: bool = False,
    source_matches: bool = False,
) -> dict[str, object]:
    result = _compare_lhs_slot_writer_source_candidate_result(
        candidate_hex,
        ptr,
        preview,
        slot_writer_observed=False,
    )
    observations = [
        item
        for item in result["hook_observations"]
        if item["hook_name"] == "static_compare_callsite"
    ]
    observations.append(
        {
            "candidate_hex": candidate_hex,
            "hook_name": "predecessor_handoff_call",
            "module_offset": "0x2338",
            "instruction": "call 0x401b50",
            "edx_ptr": ptr,
            "edx_preview_hex": preview,
        }
    )
    if handoff_return_observed:
        observations.append(
            {
                "candidate_hex": candidate_hex,
                "hook_name": "predecessor_handoff_return",
                "module_offset": "0x233d",
                "instruction": "mov edx, dword ptr [ebp - 0x116c]",
                "edx_ptr": "0xa000",
                "edx_preview_hex": "10" * 32,
            }
        )
        observations.append(
            {
                "candidate_hex": candidate_hex,
                "hook_name": "predecessor_stack_cleanup",
                "module_offset": "0x2343",
                "instruction": "add esp, 0xc",
                "edx_ptr": "0xa000",
                "edx_preview_hex": "10" * 32,
            }
        )
    if downstream_output_observed:
        source_ptr = ptr if source_matches else "0xb000"
        source_preview = preview if source_matches else "20" * 32
        observations.append(
            {
                "candidate_hex": candidate_hex,
                "hook_name": "predecessor_output_call",
                "module_offset": "0x234e",
                "instruction": "call 0x4018cd",
                "eax_ptr": source_ptr,
                "eax_preview_hex": source_preview,
                "frame_slots": [
                    {
                        "name": "[ebp-0x1170]",
                        "offset": "-0x1170",
                        "value": source_ptr,
                        "preview_hex": source_preview,
                    }
                ],
            }
        )
    return {
        **result,
        "hook_observations": observations,
    }


def _compare_lhs_slot_writer_predecessor_candidates(**kwargs) -> list[dict[str, object]]:
    return [
        _compare_lhs_slot_writer_predecessor_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
            **kwargs,
        ),
        _compare_lhs_slot_writer_predecessor_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
            **kwargs,
        ),
        _compare_lhs_slot_writer_predecessor_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
            **kwargs,
        ),
    ]


def _fake_compare_lhs_slot_writer_predecessor_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "static_compare_callsite",
        "predecessor_handoff_call",
        "predecessor_handoff_return",
        "predecessor_stack_cleanup",
        "predecessor_candidate_push",
        "predecessor_output_setup",
        "predecessor_output_call",
        "predecessor_output_return",
        "predecessor_second_call",
        "predecessor_after_second_call",
    }
    previews = {
        "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
        "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
        "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
    }
    ptr, preview = previews[candidate_hex]
    candidate = _compare_lhs_slot_writer_predecessor_candidate_result(
        candidate_hex,
        ptr,
        preview,
        downstream_output_observed=True,
        source_matches=True,
    )
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "compare lhs slot writer predecessor audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": candidate["hook_observations"],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_post_handoff_branch_outcome_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "predecessor_handoff_call",
        "handoff_helper_entry",
        "predecessor_handoff_return",
        "predecessor_stack_cleanup",
        "predecessor_candidate_push",
        "predecessor_output_call",
        "predecessor_second_call",
        "static_compare_callsite",
    }
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "post handoff branch outcome audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "predecessor_handoff_call",
                        "module_offset": "0x2338",
                        "instruction": "call 0x401b50",
                        "event": "enter",
                    },
                    {
                        "hook_name": "handoff_helper_entry",
                        "module_offset": "0x1b50",
                        "instruction": "0x401b50 entry",
                        "event": "enter",
                        "return_address_module_offset": "0x233d",
                    },
                    {
                        "hook_name": "handoff_helper_entry",
                        "module_offset": "0x1b50",
                        "instruction": "0x401b50 entry",
                        "event": "leave",
                        "return_address_module_offset": "0x2400",
                        "current_module_offset": "0x2400",
                    },
                    {
                        "hook_name": "static_compare_callsite",
                        "module_offset": "0x258c",
                        "instruction": "call 0x5028ac",
                        "event": "enter",
                        "compare_args": {
                            "args": [
                                {"index": 0, "role": "arg0", "value": "0x1100", "preview_hex": "aa" * 32},
                                {"index": 1, "role": "arg1", "value": "0x2200", "preview_hex": "66" * 32},
                                {"index": 2, "role": "arg2", "value_u32": 5},
                            ]
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_pre_compare_handoff_ready_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    expected_preview = command[command.index("--expected-eax-preview") + 1]
    first_preview = expected_preview or (
        "938f65518476c65ba5942f6620003a0020007800d5014000"
        if candidate_hex.startswith("78d540")
        else "938f65518476c65ba5942f6620005a003e007f014600"
    )
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "pre-compare handoff material ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "producer_pre_output_call",
                        "module_offset": "0x234e",
                        "instruction": "call 0x4018cd",
                        "registers": {"eax": "0x40", "edx": "0x40"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": first_preview,
                        "edx_ptr": "0x40",
                        "edx_preview_hex": first_preview,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": bool(expected_preview),
                    },
                    {
                        "hook_name": "compare_helper_entry",
                        "module_offset": "0x1028ac",
                        "compare_args": {
                            "args": [
                                {"index": 0, "value": "0x40", "preview_hex": first_preview},
                                {"index": 1, "value": "0x50", "preview_hex": "66006c00610067007b00"},
                                {"index": 2, "value_u32": 5},
                            ]
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_material_hook_runtime_validation_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    expected_preview = command[command.index("--expected-eax-preview") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} == {
        "producer_return_site",
        "producer_pre_candidate_push",
    }
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "material hook runtime validation ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "producer_return_site",
                        "module_offset": "0x233d",
                        "instruction": "mov edx, dword ptr [ebp - 0x116c]",
                        "registers": {"eax": "0x40", "edx": "0x40"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": expected_preview,
                        "edx_ptr": "0x40",
                        "edx_preview_hex": expected_preview,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": bool(expected_preview),
                    },
                    {
                        "hook_name": "producer_pre_candidate_push",
                        "module_offset": "0x2346",
                        "instruction": "push edx",
                        "registers": {"eax": "0x40", "edx": "0x40"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": expected_preview,
                        "edx_ptr": "0x40",
                        "edx_preview_hex": expected_preview,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": bool(expected_preview),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_material_hook_runtime_validation_blocked_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    preview = "aa" * 32 if candidate_hex.startswith("78d540") else "bb" * 32
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "material hook runtime validation blocked",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "producer_return_site",
                        "module_offset": "0x233d",
                        "instruction": "mov edx, dword ptr [ebp - 0x116c]",
                        "registers": {"eax": "0x40"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": preview,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_esi_material_hook_runtime_validation_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    expected_preview = command[command.index("--expected-eax-preview") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert [point["name"] for point in points_payload["hook_points"]] == ["initial_lhs_reload"]
    assert points_payload["hook_points"][0]["kind"] == "rc4_output"
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "ESI material hook runtime validation ok",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "initial_lhs_reload",
                        "module_offset": "0x2559",
                        "instruction": "mov esi, dword ptr [ebp - 0x1170]",
                        "registers": {"eax": "0x40", "esi": "0x44"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": expected_preview,
                        "esi_ptr": "0x44",
                        "esi_preview_hex": "aa" * 32,
                        "expected_eax_preview_hex": expected_preview,
                        "matched_expected_eax": bool(expected_preview),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_esi_material_hook_runtime_validation_blocked_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    preview = "aa" * 32 if candidate_hex.startswith("78d540") else "bb" * 32
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "ESI material hook runtime validation blocked",
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "hook_name": "initial_lhs_reload",
                        "module_offset": "0x2559",
                        "instruction": "mov esi, dword ptr [ebp - 0x1170]",
                        "registers": {"eax": "0x40"},
                        "eax_ptr": "0x40",
                        "eax_preview_hex": preview,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def _fake_material_hook_runtime_validation_timeout_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    raise compare_aware_search.subprocess.TimeoutExpired(command, timeout=kwargs.get("timeout", 1.0))


def test_base64_rc4_static_point_discovery_records_schema_and_blocks_unconfirmed_points(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search, "_base64_rc4_static_points", _fake_base64_rc4_static_points)

    result = run_base64_rc4_static_point_discovery(
        target=target,
        artifacts_dir=tmp_path / "base64_rc4_static_point_discovery",
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == BASE64_RC4_STATIC_POINT_DISCOVERY_FILE_NAME
    assert payload["artifact_kind"] == "base64_rc4_static_point_discovery"
    assert payload["classification"] == "manual_disassembly_required"
    assert payload["hookable_count"] == 2
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["promotable_validations"] == []
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    first = payload["best_points"][0]
    assert {"kind", "module_offset", "rva", "instruction", "hookable", "confidence", "evidence", "classification"}.issubset(first)
    assert payload["by_kind"]["base64"]["hookable_count"] == 1
    assert payload["by_kind"]["base64"]["instruction_confirmed_count"] == 0


def test_base64_rc4_static_point_discovery_allows_breakpoint_only_for_instruction_confirmed_material(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search, "_base64_rc4_static_points", _fake_base64_rc4_instruction_static_points)

    result = run_base64_rc4_static_point_discovery(
        target=target,
        artifacts_dir=tmp_path / "base64_rc4_static_point_discovery",
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "breakpoint_probe_ready"
    assert payload["breakpoint_probe_allowed"] is True
    assert compare_aware_search._base64_rc4_static_discovery_allows_breakpoint(payload) is True
    assert payload["breakpoint_static_points"]["base64_output"][0]["hook_kind"] == "interceptor"


def test_base64_rc4_breakpoint_gate_requires_static_discovery_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {
            "latest_base64_rc4_breakpoint_probe": {
                "classification": "base64_rc4_static_points_unavailable",
                "hook_results": {
                    "base64_input": "unavailable",
                    "base64_output": "unavailable",
                    "rc4_key": "unavailable",
                    "rc4_input": "unavailable",
                    "rc4_output": "unavailable",
                },
            }
        }
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", lambda kind: ({}, None))

    assert compare_aware_search._prior_base64_probe_needs_static_point_discovery() is True
    assert compare_aware_search._prior_base64_rc4_static_discovery_allows_breakpoint() is False


def test_static_discovery_compare_producer_points_trigger_producer_trace(monkeypatch) -> None:
    payload = {
        "classification": "hookable_points_found",
        "breakpoint_probe_allowed": False,
        "by_kind": {
            "compare_producer": {
                "count": 3,
                "hookable_count": 3,
                "instruction_confirmed_count": 3,
            },
            "base64_output": {
                "count": 0,
                "hookable_count": 0,
                "instruction_confirmed_count": 0,
            },
        },
    }
    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {
            "latest_base64_rc4_static_point_discovery": payload,
            "latest_compare_producer_trace_probe": {},
        }
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", lambda kind: ({}, None))

    assert compare_aware_search._base64_rc4_static_discovery_needs_compare_producer_trace(payload) is True
    assert compare_aware_search._prior_base64_rc4_static_discovery_needs_compare_producer_trace() is True
    assert compare_aware_search._base64_rc4_static_discovery_allows_breakpoint(payload) is False


def test_base64_rc4_breakpoint_probe_has_bounded_candidate_count_and_schema(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search, "_base64_rc4_static_points", _fake_base64_rc4_static_points)
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_base64_rc4_subprocess_run)

    result = run_base64_rc4_breakpoint_probe(
        target=target,
        artifacts_dir=tmp_path / "base64_rc4_breakpoint_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == BASE64_RC4_BREAKPOINT_PROBE_FILE_NAME
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["classification"] == "breakpoint_probe_complete"
    assert payload["static_points"]["base64"][0]["name"] == "standard_base64_alphabet"
    assert payload["hook_results"]["base64_input"] == "inferred"
    assert payload["hook_results"]["compare_buffer"] == "available"


def test_base64_rc4_breakpoint_probe_does_not_expand_search_or_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search, "_base64_rc4_static_points", _fake_base64_rc4_static_points)
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_base64_rc4_subprocess_run)

    result = run_base64_rc4_breakpoint_probe(
        target=target,
        artifacts_dir=tmp_path / "base64_rc4_breakpoint_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["promotable_validations"] == []
    assert result["promotable_validations"] == []


def test_base64_rc4_breakpoint_probe_records_exact2_failure_trace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search, "_base64_rc4_static_points", _fake_base64_rc4_static_points)
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_base64_rc4_subprocess_run)

    result = run_base64_rc4_breakpoint_probe(
        target=target,
        artifacts_dir=tmp_path / "base64_rc4_breakpoint_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    failure = result["payload"]["exact2_failure_trace"]
    assert failure["wchar_index"] == 2
    assert failure["runtime_word"] == "4464"
    assert failure["target_word"] == "6100"
    assert failure["encrypted_const_bytes"] == "8f3b"
    assert failure["keystream_bytes"] == "cb5f"
    assert "bounded_constraint" in failure


def test_base64_rc4_breakpoint_probe_classifies_compare_only_capture(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search, "_base64_rc4_static_points", _fake_base64_rc4_static_points)
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_base64_rc4_compare_only_subprocess_run)

    result = run_base64_rc4_breakpoint_probe(
        target=target,
        artifacts_dir=tmp_path / "base64_rc4_breakpoint_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "base64_rc4_compare_only"
    assert payload["hook_results"]["compare_buffer"] == "available"
    assert payload["first_captured_material_kind"] == "compare_buffer"
    assert payload["next_bottleneck"] == "compare-only capture"
    assert payload["hook_event_count"] == 3
    assert payload["promotable_validations"] == []


def test_compare_stack_pivot_probe_extracts_utf16le_payload_from_compare_stack(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search, "_base64_rc4_static_points", _fake_base64_rc4_static_points)
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_base64_rc4_subprocess_run)
    monkeypatch.setattr(
        compare_aware_search,
        "_compare_stack_static_audit",
        lambda target: {
            "classification": "static_anchor_confirmed",
            "compare_site": {
                "expected_call_rva": "0x258c",
                "actual_call_rva": "0x258c",
                "helper_rva": "0x1028ac",
                "helper_classification": "case_insensitive_wchar_compare",
            },
            "next_hook_points": [{"name": "post_handoff_lhs_reload", "module_offset": 0x2559}],
        },
    )
    breakpoint_result = run_base64_rc4_breakpoint_probe(
        target=target,
        artifacts_dir=tmp_path / "base64_rc4_breakpoint_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    result = run_compare_stack_pivot_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_stack_pivot_probe",
        transform_model=SamplereverseTransformModel(),
        breakpoint_probe_payload=breakpoint_result["payload"],
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_STACK_PIVOT_PROBE_FILE_NAME
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["classification"] == "compare_stack_pivot_complete"
    assert payload["hook_results"]["utf16le_payload"] == "available_from_compare_stack"
    assert payload["utf16le_payload_available_count"] == 3
    first = payload["stack_results"][0]["utf16le_payload"]["best_match"]
    assert first["stack_offset"] == 40
    assert first["esp_relative"] == "+0x28"
    assert first["matched_bytes"] >= 16


def test_compare_stack_pivot_probe_does_not_expand_search_or_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search, "_base64_rc4_static_points", _fake_base64_rc4_static_points)
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_base64_rc4_subprocess_run)
    breakpoint_result = run_base64_rc4_breakpoint_probe(
        target=target,
        artifacts_dir=tmp_path / "base64_rc4_breakpoint_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    result = run_compare_stack_pivot_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_stack_pivot_probe",
        transform_model=SamplereverseTransformModel(),
        breakpoint_probe_payload=breakpoint_result["payload"],
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["promotable_validations"] == []
    assert result["promotable_validations"] == []


def test_compare_handoff_probe_schema_and_records_handoff_points(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_handoff_subprocess_run)
    monkeypatch.setattr(
        compare_aware_search,
        "_compare_stack_static_audit",
        lambda target: {
            "classification": "static_anchor_confirmed",
            "errors": [],
            "compare_site": {
                "expected_call_rva": "0x258c",
                "actual_call_rva": "0x258c",
                "helper_rva": "0x1028ac",
                "helper_classification": "case_insensitive_wchar_compare",
            },
        },
    )

    result = run_compare_handoff_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_handoff_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_HANDOFF_PROBE_FILE_NAME
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["classification"] == "handoff_capture_complete"
    assert payload["compare_stack_pivot_audit"] == {
        "compare_call_rva": "0x258c",
        "handoff_helper_rva": "0x1b50",
        "post_handoff_reload_rva": "0x2559",
        "lhs_slot": "[ebp-0x1170]",
        "static_anchor_valid": True,
        "reason": [],
    }
    assert payload["hook_results"]["handoff_helper_enter"] == "available"
    assert payload["hook_results"]["handoff_helper_return"] == "available"
    assert payload["hook_results"]["post_handoff_lhs_reload"] == "available"
    assert payload["hook_results"]["lhs_slot"] == "available"
    assert payload["hook_results"]["compare_lhs_buffer"] == "available"
    assert {item["hook_name"] for item in payload["handoff_observations"]} >= {
        "pre_lhs_slot_store",
        "handoff_helper_enter",
        "handoff_helper_return",
        "post_handoff_lhs_reload",
        "wide_flag_prefix_compare",
    }


def test_compare_handoff_probe_records_lhs_slot_and_post_reload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_handoff_subprocess_run)

    result = run_compare_handoff_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_handoff_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    observations = result["payload"]["handoff_observations"]
    post_reload = next(item for item in observations if item["hook_name"] == "post_handoff_lhs_reload")
    assert post_reload["lhs_slot_ptr"] == "0x419cea8"
    assert post_reload["eax_ptr"] == "0x419cea8"
    assert post_reload["lhs_buffer_preview_hex"].startswith("46006c00")
    assert post_reload["candidate_hex"] == "78d540b49c59077041414141414141"
    assert post_reload["runtime_ci_exact_wchars"] == 2


def test_compare_handoff_probe_does_not_expand_search_or_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_handoff_subprocess_run)

    result = run_compare_handoff_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_handoff_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["promotable_validations"] == []
    assert result["promotable_validations"] == []


def test_compare_handoff_slice_probe_records_helper_argument_map_and_wrong_reload_anchor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_handoff_slice_subprocess_run)
    monkeypatch.setattr(
        compare_aware_search,
        "_compare_stack_static_audit",
        lambda target: {
            "classification": "static_anchor_confirmed",
            "errors": [],
            "compare_site": {
                "expected_call_rva": "0x258c",
                "actual_call_rva": "0x258c",
                "helper_rva": "0x1028ac",
                "helper_classification": "case_insensitive_wchar_compare",
            },
            "backward_slice": [{"rva": "0x2554", "instruction": "call 0x401b50"}],
        },
    )

    result = run_compare_handoff_slice_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_handoff_slice_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_HANDOFF_SLICE_PROBE_FILE_NAME
    assert payload["artifact_kind"] == "compare_handoff_slice_probe"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["classification"] == "wrong_reload_anchor"
    assert payload["hook_results"]["post_handoff_lhs_reload"] == "unavailable"
    assert payload["hook_results"]["post_handoff_after_reload"] == "available"
    first_map = payload["candidate_results"][0]["helper_argument_map"]
    assert first_map["helper_enter"]["return_address_module_offset"] == "0x2559"
    assert first_map["helper_return"]["eax_ptr"] == "0x419cea8"
    assert first_map["compare_lhs"]["lhs_ptr"] == "0x419cea8"
    assert first_map["relations"]["helper_return_eax_preview_matches_compare_lhs"] is True
    assert payload["cross_candidate_summary"]["relation_counts"]["helper_return_eax_matches_compare_lhs_ptr"] == 3


def test_compare_handoff_slice_probe_does_not_expand_search_or_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_handoff_slice_subprocess_run)

    result = run_compare_handoff_slice_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_handoff_slice_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["promotable_validations"] == []
    assert result["promotable_validations"] == []


def test_compare_handoff_return_site_probe_records_return_site_and_compare_args(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_handoff_return_site_subprocess_run)

    result = run_compare_handoff_return_site_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_handoff_return_site_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_HANDOFF_RETURN_SITE_PROBE_FILE_NAME
    assert payload["artifact_kind"] == "compare_handoff_return_site_probe"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["classification"] == "wrong_helper_assumption"
    assert payload["hook_results"]["helper_return_site"] == "available"
    first_map = payload["candidate_results"][0]["return_site_map"]
    assert first_map["helper_enter"]["return_address_module_offset"] == "0x233d"
    assert first_map["helper_enter"]["matches_expected_post_helper"] is False
    assert first_map["return_site"]["observed"] is True
    assert first_map["compare_call"]["args"][0]["preview_utf16le"] == "flag{"
    assert first_map["compare_call"]["args"][2]["value_u32"] == 5
    assert first_map["relations"]["helper_enter_return_is_0x233d"] is True
    assert payload["cross_candidate_summary"]["target_flag_side_counts"]["arg0"] == 3
    assert payload["cross_candidate_summary"]["candidate_dependent_fields"]["compare_call.arg1.preview_hex"] is True
    fallback = next(
        item for item in payload["static_audit"]["hook_point_audit"] if item["name"] == "post_handoff_after_reload"
    )
    assert fallback["boundary_status"] == "inside_instruction"


def test_compare_handoff_return_site_probe_does_not_expand_search_or_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_handoff_return_site_subprocess_run)

    result = run_compare_handoff_return_site_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_handoff_return_site_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["promotable_validations"] == []
    assert result["promotable_validations"] == []


def test_compare_producer_trace_probe_records_compare_entry_and_relations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_producer_trace_subprocess_run)

    result = run_compare_producer_trace_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_producer_trace_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_PRODUCER_TRACE_PROBE_FILE_NAME
    assert payload["artifact_kind"] == "compare_producer_trace_probe"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["classification"] == "compare_producer_trace_captured"
    assert payload["hook_results"]["compare_helper_entry"] == "available"
    assert payload["hook_results"]["compare_entry_args"] == "available"
    assert payload["candidate_material_count"] >= 3
    assert payload["candidate_materials"][0]["kind"] == "compare_buffer"
    assert payload["write_source_trace_count"] >= 1
    assert payload["write_source_trace"][0]["source_module_offset"] == "0x253a"
    assert payload["material_hook_candidate_count"] == 0
    assert payload["material_hook_candidates"] == []
    assert payload["breakpoint_probe_allowed"] is False
    first_map = payload["candidate_results"][0]["producer_trace_map"]
    assert first_map["producer_return_site"]["observed"] is True
    assert first_map["compare_helper_entry"]["caller_return_module_offset"] == "0x2591"
    assert first_map["compare_helper_entry"]["arg1_preview_has_flag_prefix"] is True
    assert first_map["candidate_compare_arg"]["value"] == "0x36dce20"
    assert first_map["relations"]["producer_eax_matches_compare_arg_ptr"] is True
    assert payload["cross_candidate_summary"]["target_flag_side_counts"]["entry_arg1"] == 3
    assert payload["cross_candidate_summary"]["candidate_dependent_fields"]["compare_entry.arg0.preview_hex"] is True
    assert payload["hook_miss_classification"]["missed_hooks"] == "post_handoff_lhs_reload, pre_compare_push_esi"
    assert payload["static_audit"]["producer_window"]["start_rva"] == "0x2310"


def test_compare_producer_trace_probe_does_not_expand_search_or_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_producer_trace_subprocess_run)

    result = run_compare_producer_trace_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_producer_trace_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["promotable_validations"] == []
    assert result["promotable_validations"] == []


def test_compare_producer_trace_probe_promotes_only_instruction_confirmed_material_hooks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_compare_producer_trace_material_hook_subprocess_run,
    )

    result = run_compare_producer_trace_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_producer_trace_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "base64_material_captured"
    assert payload["breakpoint_probe_allowed"] is True
    assert payload["material_hook_candidate_count"] == 3
    assert payload["material_hook_candidates"][0]["kind"] == "base64_output"
    assert payload["promotable_validations"] == []


def _upstream_material_producer_trace_payload() -> dict[str, object]:
    return {
        "artifact_kind": "compare_producer_trace_probe",
        "classification": "upstream_material_candidate_found",
        "candidate_material_count": 3,
        "breakpoint_probe_allowed": False,
        "candidate_results": [
            {
                "candidate_hex": "78d540b49c59077041414141414141",
                "producer_trace_map": {
                    "producer_return_site": {
                        "eax_preview_hex": "938f65518476c65ba5942f6620003a0020007800d5014000"
                    }
                },
            },
            {
                "candidate_hex": "78d540b49c59077040414141414141",
                "producer_trace_map": {
                    "producer_return_site": {
                        "eax_preview_hex": "938f65518476c65ba5942f6620003a0020007800d5014001"
                    }
                },
            },
            {
                "candidate_hex": "5a3e7f46ddd474d041414141414141",
                "producer_trace_map": {
                    "producer_return_site": {
                        "eax_preview_hex": "938f65518476c65ba5942f6620003a0020005a003e007f01"
                    }
                },
            },
        ],
    }


def test_compare_producer_material_confirmation_records_schema_and_blocks_without_confirmed_hook(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_material_confirmation_subprocess_run)

    result = run_compare_producer_material_confirmation_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_producer_material_confirmation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        producer_trace_payload=_upstream_material_producer_trace_payload(),
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_PRODUCER_MATERIAL_CONFIRMATION_FILE_NAME
    assert payload["artifact_kind"] == "compare_producer_material_confirmation"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["classification"] == "material_confirmation_inconclusive"
    assert payload["runtime_backed_count"] == 3
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["confirmed_material_hook_candidates"] == []
    assert payload["instruction_confirmation_table"][0]["instruction_confirmed"] is True
    assert payload["material_source_trace"]
    assert payload["promotable_validations"] == []


def test_compare_producer_material_confirmation_does_not_expand_search_or_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_material_confirmation_subprocess_run)

    result = run_compare_producer_material_confirmation_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_producer_material_confirmation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        producer_trace_payload=_upstream_material_producer_trace_payload(),
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["promotable_validations"] == []
    assert result["promotable_validations"] == []


def test_compare_pre_compare_handoff_target_probe_records_schema_and_relations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_pre_compare_handoff_subprocess_run)

    result = run_compare_pre_compare_handoff_target_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_pre_compare_handoff_target_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        producer_trace_payload=_upstream_material_producer_trace_payload(),
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_PRE_COMPARE_HANDOFF_TARGET_PROBE_FILE_NAME
    assert payload["artifact_kind"] == "compare_pre_compare_handoff_target_probe"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["runtime_backed_count"] == 3
    assert payload["classification"] == "next_handoff_target_identified"
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["promotable_validations"] == []
    assert payload["hit_summary"]["hit_producer_return_site_count"] == 3
    assert payload["hit_summary"]["hit_compare_helper_entry_count"] == 3
    assert payload["candidate_dependent_fields"]["producer_return_site.eax_preview_hex"] is True
    assert payload["relation_counts"]["producer_return_site.eax_to_arg0.ptr_matches"] == 3
    assert payload["relation_table"][0]["compare_observed"] is True


def test_function_semantic_audit_uses_pre_compare_handoff_gate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_pre_compare_handoff_ready_subprocess_run)
    pre_compare = run_compare_pre_compare_handoff_target_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_pre_compare_handoff_target_probe",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        producer_trace_payload=_upstream_material_producer_trace_payload(),
        log=lambda _: None,
    )

    audit = build_function_semantic_audit_payload(
        material_confirmation_payload={
            "instruction_confirmation_table": [],
            "confirmed_material_hook_candidates": [],
        },
        pre_compare_handoff_payload=pre_compare["payload"],
    )

    assert pre_compare["payload"]["breakpoint_probe_allowed"] is True
    assert audit["breakpoint_probe_allowed"] is True
    assert audit["classification"] == "material_hook_ready"
    assert audit["material_hook_candidate_count"] >= 1
    assert any(item["material_hook_candidate_status"] == "ready" for item in audit["functions"])


def test_material_hook_runtime_validation_accepts_only_transform_material(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_material_hook_runtime_validation_subprocess_run,
    )

    result = run_material_hook_runtime_validation(
        target=target,
        artifacts_dir=tmp_path / "material_hook_runtime_validation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        function_semantic_payload={"classification": "material_hook_ready"},
        pre_compare_handoff_payload={"classification": "next_handoff_target_identified"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == MATERIAL_HOOK_RUNTIME_VALIDATION_FILE_NAME
    assert payload["artifact_kind"] == "material_hook_runtime_validation"
    assert payload["candidate_count"] == 4
    assert payload["candidate_limit"] == 4
    assert payload["classification"] == "ACCEPT"
    assert payload["breakpoint_probe_allowed"] is True
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert payload["validated_hooks"][0]["classification"] == "confirmed_utf16le_material"
    assert payload["validated_hooks"][0]["connects_to_transform_chain"] is True
    assert compare_aware_search._material_hook_runtime_validation_allows_breakpoint(payload) is True
    points = compare_aware_search._breakpoint_static_points_from_material_hook_runtime_validation_payload(payload)
    assert points["utf16le_payload"][0]["module_offset"] == 0x233D


def test_material_hook_runtime_validation_blocks_candidate_dependent_non_transform_material(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_material_hook_runtime_validation_blocked_subprocess_run,
    )

    result = run_material_hook_runtime_validation(
        target=target,
        artifacts_dir=tmp_path / "material_hook_runtime_validation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        function_semantic_payload={"classification": "material_hook_ready"},
        pre_compare_handoff_payload={"classification": "next_handoff_target_identified"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "BLOCKED"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["validated_hooks"] == []
    assert payload["blocked_hooks"][0]["classification"] == "candidate_dependent_but_not_transform_material"
    assert compare_aware_search._material_hook_runtime_validation_allows_breakpoint(payload) is False
    assert compare_aware_search._breakpoint_static_points_from_material_hook_runtime_validation_payload(payload) == {}


def test_material_hook_runtime_validation_times_out_without_hanging_strategy(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_material_hook_runtime_validation_timeout_subprocess_run,
    )

    result = run_material_hook_runtime_validation(
        target=target,
        artifacts_dir=tmp_path / "material_hook_runtime_validation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        function_semantic_payload={"classification": "material_hook_ready"},
        pre_compare_handoff_payload={"classification": "next_handoff_target_identified"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "REJECTED"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["candidate_results"][0]["runtime_backed"] is False
    timed_out_candidate = Path(payload["candidate_results"][0]["result_path"])
    timed_out_payload = json.loads(timed_out_candidate.read_text(encoding="utf-8"))
    assert timed_out_payload["error"] == "timeout"


def test_material_hook_runtime_validation_accepts_promoted_esi_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_esi_material_hook_runtime_validation_subprocess_run,
    )

    result = run_material_hook_runtime_validation(
        target=target,
        artifacts_dir=tmp_path / "material_hook_runtime_validation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        compare_esi_source_window_payload={
            "classification": "esi_source_identified",
            "promotable_validations": [
                {
                    "hook_name": "initial_lhs_reload",
                    "module_offset": "0x2559",
                    "instruction": "mov esi, dword ptr [ebp - 0x1170]",
                    "candidate_dependent": True,
                    "connects_to_compare_lhs": True,
                }
            ],
        },
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "ACCEPT"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["source_compare_esi_source_window_classification"] == "esi_source_identified"
    assert payload["material_kind"] == "rc4_output"
    assert payload["hook_points"][0]["module_offset"] == 0x2559
    assert payload["static_audit"]["classification"].startswith("static_compare_esi_source_window")
    assert payload["validated_hooks"][0]["classification"] == "confirmed_rc4_output_material"
    assert payload["validated_hooks"][0]["connects_to_compare_lhs"] is True
    assert payload["breakpoint_probe_allowed"] is True
    points = compare_aware_search._breakpoint_static_points_from_material_hook_runtime_validation_payload(payload)
    assert points["rc4_output"][0]["module_offset"] == 0x2559


def test_material_hook_runtime_validation_blocks_promoted_esi_source_mismatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_esi_material_hook_runtime_validation_blocked_subprocess_run,
    )

    result = run_material_hook_runtime_validation(
        target=target,
        artifacts_dir=tmp_path / "material_hook_runtime_validation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        compare_esi_source_window_payload={
            "classification": "esi_source_identified",
            "promotable_validations": [
                {
                    "hook_name": "initial_lhs_reload",
                    "module_offset": "0x2559",
                    "candidate_dependent": True,
                    "connects_to_compare_lhs": True,
                }
            ],
        },
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "BLOCKED"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["validated_hooks"] == []
    assert payload["blocked_hooks"][0]["classification"] == "candidate_dependent_but_not_transform_material"
    assert "0x2559" in payload["next_bounded_action"]


def test_post_handoff_branch_outcome_audit_rejects_failed_material_window(tmp_path: Path) -> None:
    pre_compare_payload = {
        "classification": "next_handoff_target_identified",
        "hook_miss_classification": "branch_exits_before_output_calls",
        "instruction_confirmation_table": [
            {
                "hook_name": "producer_return_site",
                "module_offset": "0x233d",
                "instruction": "mov edx, dword ptr [ebp - 0x116c]",
                "observed_count": 3,
                "candidate_dependent_eax": True,
                "expected_eax_match_count": 3,
                "instruction_confirmed": True,
                "hookable": True,
            },
            {
                "hook_name": "producer_pre_candidate_push",
                "module_offset": "0x2346",
                "instruction": "push edx",
                "observed_count": 3,
                "candidate_dependent_eax": True,
                "expected_eax_match_count": 3,
                "instruction_confirmed": True,
                "hookable": True,
            },
            {
                "hook_name": "producer_pre_output_call",
                "module_offset": "0x234e",
                "instruction": "call 0x4018cd",
                "observed_count": 0,
                "candidate_dependent_eax": False,
                "expected_eax_match_count": 0,
                "instruction_confirmed": True,
                "hookable": False,
            },
            {
                "hook_name": "producer_pre_second_call",
                "module_offset": "0x2355",
                "instruction": "call 0x401be3",
                "observed_count": 0,
                "candidate_dependent_eax": False,
                "expected_eax_match_count": 0,
                "instruction_confirmed": True,
                "hookable": False,
            },
        ],
    }
    material_payload = {
        "classification": "REJECTED",
        "validated_hooks": [],
        "blocked_hooks": [
            {
                "hook_name": "producer_return_site",
                "module_offset": "0x233d",
                "classification": "not_reached",
                "hit_count": 0,
                "candidate_dependent": False,
                "connects_to_transform_chain": False,
            },
            {
                "hook_name": "producer_pre_candidate_push",
                "module_offset": "0x2346",
                "classification": "not_reached",
                "hit_count": 0,
                "candidate_dependent": False,
                "connects_to_transform_chain": False,
            },
        ],
        "candidate_results": [{"candidate_hex": "78d540b49c59077041414141414141", "error": "timeout"}],
    }

    built = build_post_handoff_branch_outcome_audit_payload(
        pre_compare_handoff_payload=pre_compare_payload,
        material_hook_runtime_payload=material_payload,
        function_semantic_payload={"classification": "material_hook_ready"},
    )
    result = run_post_handoff_branch_outcome_audit(
        artifacts_dir=tmp_path / "post_handoff_branch_outcome_audit",
        pre_compare_handoff_payload=pre_compare_payload,
        material_hook_runtime_payload=material_payload,
        function_semantic_payload={"classification": "material_hook_ready"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert built["classification"] == "post_handoff_window_rejected"
    assert Path(result["result_path"]).name == POST_HANDOFF_BRANCH_OUTCOME_AUDIT_FILE_NAME
    assert payload["artifact_kind"] == "post_handoff_branch_outcome_audit"
    assert payload["classification"] == "post_handoff_window_rejected"
    assert payload["window"]["downstream_transform_calls_reached"] is False
    assert payload["failed_material_hook_hypotheses"][0]["module_offset"] == "0x233d"
    assert payload["timed_out_candidates"][0]["candidate_hex"] == "78d540b49c59077041414141414141"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["candidate_generation_changed"] is False
    assert "0x233d" in payload["blocked_actions"][0]
    assert "0x2346" in payload["blocked_actions"][0]


def _post_handoff_candidate_result(
    candidate_hex: str,
    observations: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "candidate_hex": candidate_hex,
        "candidate_prefix": candidate_hex[:16],
        "runtime_backed": bool(observations),
        "hook_observations": observations,
    }


def _post_handoff_runtime_candidates(kind: str, count: int = 3) -> list[dict[str, object]]:
    candidates = [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
        "78d540b49c59076f41414141414141",
    ][:count]
    rows: list[dict[str, object]] = []
    for candidate_hex in candidates:
        observations: list[dict[str, object]] = [
            {
                "hook_name": "predecessor_handoff_call",
                "module_offset": "0x2338",
                "event": "enter",
            },
            {
                "hook_name": "handoff_helper_entry",
                "module_offset": "0x1b50",
                "event": "enter",
                "return_address_module_offset": "0x233d",
            },
        ]
        if kind in {"alternate", "linear_leave"}:
            observations.append(
                {
                    "hook_name": "handoff_helper_entry",
                    "module_offset": "0x1b50",
                    "event": "leave",
                    "return_address_module_offset": "0x2400" if kind == "alternate" else "0x233d",
                    "current_module_offset": "0x2400" if kind == "alternate" else "0x233d",
                }
            )
        if kind in {"alternate", "tailcall", "exception"}:
            observations.append(
                {
                    "hook_name": "static_compare_callsite",
                    "module_offset": "0x258c",
                    "event": "enter",
                }
            )
        if kind == "exception":
            observations.append(
                {
                    "hook_name": "process_exception",
                    "module_offset": "0x1b60",
                    "event": "exception",
                    "exception": {"type": "access-violation"},
                }
            )
        rows.append(_post_handoff_candidate_result(candidate_hex, observations))
    return rows


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("alternate", "handoff_returns_to_alternate_site"),
        ("tailcall", "handoff_tailcalls_or_jumps"),
        ("exception", "handoff_exception_or_unwind"),
        ("unknown", "callee_observed_but_exit_unknown"),
    ],
)
def test_post_handoff_branch_outcome_runtime_classifications(kind: str, expected: str) -> None:
    payload = build_post_handoff_branch_outcome_audit_payload(
        pre_compare_handoff_payload={},
        material_hook_runtime_payload={},
        predecessor_payload={"classification": "handoff_call_does_not_return_to_linear_path"},
        candidate_results=_post_handoff_runtime_candidates(kind),
    )

    assert payload["classification"] == expected
    assert payload["runtime_backed_count"] == 3
    assert payload["source_predecessor_classification"] == "handoff_call_does_not_return_to_linear_path"
    assert payload["breakpoint_probe_allowed"] is False


def test_post_handoff_branch_outcome_runtime_classification_inconclusive() -> None:
    payload = build_post_handoff_branch_outcome_audit_payload(
        pre_compare_handoff_payload={},
        material_hook_runtime_payload={},
        predecessor_payload={"classification": "handoff_call_does_not_return_to_linear_path"},
        candidate_results=_post_handoff_runtime_candidates("tailcall", count=1),
    )

    assert payload["classification"] == "inconclusive"
    assert payload["runtime_backed_count"] == 1


def test_run_post_handoff_branch_outcome_audit_uses_runtime_sidecar(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_post_handoff_branch_outcome_subprocess_run,
    )

    result = run_post_handoff_branch_outcome_audit(
        target=target,
        artifacts_dir=tmp_path / "post_handoff_branch_outcome_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        pre_compare_handoff_payload={},
        material_hook_runtime_payload={},
        predecessor_payload={"classification": "handoff_call_does_not_return_to_linear_path"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == POST_HANDOFF_BRANCH_OUTCOME_AUDIT_FILE_NAME
    assert payload["classification"] == "handoff_returns_to_alternate_site"
    assert payload["runtime_backed_count"] == 3
    assert payload["exit_summary"]["return_address_module_offsets"]


def _exception_unwind_compare_observation(candidate_hex: str) -> dict[str, object]:
    return {
        "hook_name": "static_compare_callsite",
        "module_offset": "0x258c",
        "event": "enter",
        "compare_args": {
            "args": [
                {"index": 0, "role": "arg0", "value": f"0x{candidate_hex[:4]}", "preview_hex": candidate_hex[:64]},
                {"index": 1, "role": "arg1", "value": "0x711c4c", "preview_hex": "66" * 32},
                {"index": 2, "role": "arg2", "value_u32": 5},
            ]
        },
    }


def _exception_unwind_candidate_results(kind: str) -> list[dict[str, object]]:
    candidates = [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
        "78d540b49c59076f41414141414141",
    ]
    rows: list[dict[str, object]] = []
    for candidate_hex in candidates:
        observations: list[dict[str, object]] = [
            {"hook_name": "predecessor_handoff_call", "module_offset": "0x2338", "event": "enter"},
            {
                "hook_name": "handoff_helper_entry",
                "module_offset": "0x1b50",
                "event": "enter",
                "return_address_module_offset": "0x233d",
            },
        ]
        if kind == "normal":
            observations.append(
                {
                    "hook_name": "handoff_helper_entry",
                    "module_offset": "0x1b50",
                    "event": "leave",
                    "return_address_module_offset": "0x233d",
                    "current_module_offset": "0x233d",
                }
            )
            observations.append(_exception_unwind_compare_observation(candidate_hex))
        elif kind == "alternate":
            observations.append(
                {
                    "hook_name": "handoff_helper_entry",
                    "module_offset": "0x1b50",
                    "event": "leave",
                    "return_address_module_offset": "0x2400",
                    "current_module_offset": "0x2400",
                }
            )
            observations.append(_exception_unwind_compare_observation(candidate_hex))
        elif kind == "exception":
            observations.append(
                {
                    "hook_name": "process_exception",
                    "module_offset": "0x1913",
                    "current_module_offset": "0x1913",
                    "event": "exception",
                    "exception": {"type": "access-violation", "memory": "0x0"},
                }
            )
            observations.append(_exception_unwind_compare_observation(candidate_hex))
        elif kind == "seh":
            observations.append(
                {
                    "hook_name": "process_exception",
                    "module_offset": "0x19bb",
                    "current_module_offset": "0x19bb",
                    "event": "exception",
                    "exception": {"type": "access-violation", "memory": "0x0"},
                }
            )
            observations.append(
                {
                    "hook_name": "tentative_handler_1a30",
                    "module_offset": "0x1a30",
                    "event": "enter",
                }
            )
            observations.append(_exception_unwind_compare_observation(candidate_hex))
        elif kind == "compare_without_args":
            observations.append(
                {
                    "hook_name": "process_exception",
                    "module_offset": "0x1913",
                    "current_module_offset": "0x1913",
                    "event": "exception",
                    "exception": {"type": "access-violation", "memory": "0x0"},
                }
            )
            observations.append({"hook_name": "static_compare_callsite", "module_offset": "0x258c"})
        rows.append(_post_handoff_candidate_result(candidate_hex, observations))
    return rows


@pytest.mark.parametrize(
    ("kind", "expected", "route"),
    [
        ("normal", "normal_return_to_compare_path", "lhs_producer_provenance"),
        ("alternate", "alternate_return_to_compare_path", "alternate_target_slice"),
        ("exception", "exception_dispatch_to_compare_path", "handler_to_lhs_dataflow"),
        ("seh", "seh_unwind_to_compare_path", "handler_to_lhs_dataflow"),
        ("unknown", "instrumentation_missed_return", "hook_reliability_fix"),
    ],
)
def test_post_handoff_exception_unwind_evidence_gated_classifications(
    kind: str,
    expected: str,
    route: str,
) -> None:
    payload = build_post_handoff_exception_unwind_audit_payload(
        post_handoff_payload={"classification": "handoff_exception_or_unwind"},
        candidate_results=_exception_unwind_candidate_results(kind),
    )

    assert payload["classification"] == expected
    assert payload["post_classification_route"] == route
    assert payload["candidate_count"] == 3
    assert payload["runtime_backed_count"] == 3
    assert payload["breakpoint_probe_allowed"] is False


def test_post_handoff_exception_unwind_requires_compare_args_for_compare_path() -> None:
    payload = build_post_handoff_exception_unwind_audit_payload(
        post_handoff_payload={"classification": "handoff_exception_or_unwind"},
        candidate_results=_exception_unwind_candidate_results("compare_without_args"),
    )

    assert payload["evidence_gate"]["compare_entry_observed"] is True
    assert payload["evidence_gate"]["compare_args_captured"] is False
    assert payload["classification"] == "compare_not_reached"
    assert payload["post_classification_route"] == "stop_missing_evidence"


def test_post_handoff_exception_unwind_records_tentative_hook_evidence_refs() -> None:
    results = _exception_unwind_candidate_results("seh")
    for index, result in enumerate(results, 1):
        result["result_path"] = f"artifact/candidate_{index}/post_handoff_exception_unwind_audit.json"
    payload = build_post_handoff_exception_unwind_audit_payload(
        post_handoff_payload={"classification": "handoff_exception_or_unwind"},
        candidate_results=results,
    )

    observed = [
        row for row in payload["tentative_hook_candidates"]
        if row.get("module_offset") == "0x1a30" and row.get("status") == "runtime_observed"
    ]
    assert observed
    assert observed[0]["evidence_ref"]["artifact"].endswith("post_handoff_exception_unwind_audit.json")


def _fake_post_handoff_exception_unwind_subprocess_run(*args, **kwargs):  # noqa: ANN002, ANN003
    command = list(args[0])
    out_path = Path(command[command.index("--out") + 1])
    points_path = Path(command[command.index("--points") + 1])
    candidate_hex = command[command.index("--probe-hex") + 1]
    points_payload = json.loads(points_path.read_text(encoding="utf-8"))
    assert {point["name"] for point in points_payload["hook_points"]} >= {
        "handoff_helper_entry",
        "tentative_exception_site_1913",
        "tentative_exception_site_19bb",
        "tentative_resume_19fe",
        "tentative_handler_1a30",
        "static_compare_callsite",
    }
    out_path.write_text(
        json.dumps(
            {
                "success": True,
                "summary": "post handoff exception/unwind audit ok",
                "candidate_hex": candidate_hex,
                "hook_observations": _exception_unwind_candidate_results("seh")[0]["hook_observations"],
            }
        ),
        encoding="utf-8",
    )

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    return _Proc()


def test_run_post_handoff_exception_unwind_audit_uses_runtime_sidecar(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_post_handoff_exception_unwind_subprocess_run)

    result = run_post_handoff_exception_unwind_audit(
        target=target,
        artifacts_dir=tmp_path / "post_handoff_exception_unwind_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        post_handoff_payload={"classification": "handoff_exception_or_unwind"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == POST_HANDOFF_EXCEPTION_UNWIND_AUDIT_FILE_NAME
    assert payload["artifact_kind"] == "post_handoff_exception_unwind_audit"
    assert payload["classification"] == "seh_unwind_to_compare_path"
    assert payload["candidate_count"] == 3


def test_compare_lhs_producer_audit_identifies_instruction_confirmed_producer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_compare_lhs_producer_audit_subprocess_run,
    )

    result = run_compare_lhs_producer_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_lhs_producer_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        post_handoff_payload={"classification": "post_handoff_window_rejected"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_LHS_PRODUCER_AUDIT_FILE_NAME
    assert payload["artifact_kind"] == "compare_lhs_producer_audit"
    assert payload["classification"] == "producer_identified"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["runtime_backed_count"] == 3
    assert payload["relations"] == {
        "slot_to_compare_arg": "confirmed",
        "eax_to_slot": "confirmed",
        "esi_to_compare_arg": "confirmed",
        "helper_return_to_lhs": "confirmed",
    }
    producer_rows = [row for row in payload["checked_windows"] if row["hook_name"] == "pre_lhs_slot_store"]
    assert producer_rows[0]["candidate_dependent"] is True
    assert producer_rows[0]["connects_to_compare_lhs"] is True
    assert producer_rows[0]["runtime_backed_count"] == 3
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert result["promotable_validations"] == []


def test_compare_lhs_producer_audit_rejects_unconnected_window() -> None:
    candidates = [
        _compare_lhs_candidate_result("78d540b49c59077041414141414141", "0x1100", "aa" * 32, connect_to_arg0=False),
        _compare_lhs_candidate_result("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32, connect_to_arg0=False),
        _compare_lhs_candidate_result("78d540b49c59076f41414141414141", "0x3300", "cc" * 32, connect_to_arg0=False),
    ]

    payload = build_compare_lhs_producer_audit_payload(
        candidate_results=candidates,
        source_post_handoff_payload={"classification": "post_handoff_window_rejected"},
    )

    assert payload["classification"] == "producer_window_rejected"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["relations"]["slot_to_compare_arg"] == "rejected"
    assert payload["relations"]["esi_to_compare_arg"] == "rejected"
    assert payload["identified_producers"] == []


def test_compare_lhs_producer_audit_inconclusive_without_runtime_coverage() -> None:
    payload = build_compare_lhs_producer_audit_payload(
        candidate_results=[
            _compare_lhs_candidate_result("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ],
        source_post_handoff_payload={"classification": "post_handoff_window_rejected"},
    )

    assert payload["classification"] == "inconclusive"
    assert payload["candidate_count"] == 1
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_lhs_upstream_writer_audit_identifies_bounded_writer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_compare_lhs_upstream_writer_audit_subprocess_run,
    )

    result = run_compare_lhs_upstream_writer_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_lhs_upstream_writer_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        compare_lhs_payload={"classification": "producer_window_rejected"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_LHS_UPSTREAM_WRITER_AUDIT_FILE_NAME
    assert payload["artifact_kind"] == "compare_lhs_upstream_writer_audit"
    assert payload["classification"] == "upstream_writer_identified"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["runtime_backed_count"] == 3
    writer_rows = [
        row
        for row in payload["checked_writers"]
        if row["hook_name"] == "producer_post_transform_slot_reload"
    ]
    assert writer_rows[0]["candidate_dependent"] is True
    assert writer_rows[0]["connects_to_compare_lhs"] is True
    assert writer_rows[0]["connects_to_lhs_store"] is True
    assert payload["identified_writers"][0]["hook_name"] == "producer_post_transform_slot_reload"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False
    assert result["promotable_validations"] == []


def test_compare_lhs_upstream_writer_audit_records_candidate_dependent_unconnected_writer() -> None:
    candidates = [
        _compare_lhs_upstream_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
            connect_to_arg0=False,
        ),
        _compare_lhs_upstream_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
            connect_to_arg0=False,
        ),
        _compare_lhs_upstream_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
            connect_to_arg0=False,
        ),
    ]
    for result in candidates:
        observations = result["hook_observations"]
        observations[:] = [
            item
            for item in observations
            if item["hook_name"] not in {"downstream_lhs_store_sentinel", "compare_helper_entry"}
        ]

    payload = build_compare_lhs_upstream_writer_audit_payload(
        candidate_results=candidates,
        source_compare_lhs_payload={"classification": "producer_window_rejected"},
    )

    assert payload["classification"] == "candidate_dependent_upstream_observed"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["identified_writers"] == []
    assert payload["candidate_dependent_writers"][0]["hook_name"] == "producer_post_transform_slot_reload"


def test_compare_lhs_upstream_writer_audit_rejects_non_candidate_dependent_window() -> None:
    candidates = [
        _compare_lhs_upstream_candidate_result("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        _compare_lhs_upstream_candidate_result("5a3e7f46ddd474d041414141414141", "0x1100", "aa" * 32),
        _compare_lhs_upstream_candidate_result("78d540b49c59076f41414141414141", "0x1100", "aa" * 32),
    ]

    payload = build_compare_lhs_upstream_writer_audit_payload(
        candidate_results=candidates,
        source_compare_lhs_payload={"classification": "producer_window_rejected"},
    )

    assert payload["classification"] == "upstream_window_rejected"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["identified_writers"] == []


def test_compare_callsite_reanchor_audit_identifies_lhs_producer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_compare_callsite_reanchor_subprocess_run,
    )

    result = run_compare_callsite_reanchor_and_lhs_provenance_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_callsite_reanchor_and_lhs_provenance_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        upstream_writer_payload={"classification": "candidate_dependent_upstream_observed"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_CALLSITE_REANCHOR_AND_LHS_PROVENANCE_AUDIT_FILE_NAME
    assert payload["artifact_kind"] == "compare_callsite_reanchor_and_lhs_provenance_audit"
    assert payload["classification"] == "lhs_producer_identified"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["runtime_backed_count"] == 3
    assert payload["actual_compare"]["entry_status"] == "confirmed"
    assert payload["actual_compare"]["caller_module_offset"] == "0x258c"
    assert payload["actual_compare"]["lhs_side"] == "arg0"
    assert payload["actual_compare"]["flag_side"] == "arg1"
    assert payload["actual_compare"]["lhs_preview_varies_by_candidate"] is True
    assert payload["frame_anchor"]["old_slot_ebp_minus_1170_valid"] is False
    assert payload["provenance"]["connects_to_compare_lhs"] is True
    assert payload["identified_producers"][0]["hook_name"] == "upstream_slot_1168_reload"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["final_selection_changed"] is False
    assert payload["search_budget_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False


def test_compare_callsite_reanchor_audit_uses_static_callsite_capture() -> None:
    candidates = [
        _compare_callsite_reanchor_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
            producer_matches=False,
            compare_hook_name="static_compare_callsite",
        ),
        _compare_callsite_reanchor_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
            producer_matches=False,
            compare_hook_name="static_compare_callsite",
        ),
        _compare_callsite_reanchor_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
            producer_matches=False,
            compare_hook_name="static_compare_callsite",
        ),
    ]

    payload = build_compare_callsite_reanchor_and_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_upstream_writer_payload={"classification": "candidate_dependent_upstream_observed"},
    )

    assert payload["classification"] == "frame_anchor_rejected"
    assert payload["actual_compare"]["entry"] == "0x258c"
    assert payload["actual_compare"]["entry_status"] == "confirmed"
    assert payload["actual_compare"]["observed_count"] == 3
    assert payload["actual_compare"]["caller_module_offset"] == "0x258c"
    assert payload["actual_compare"]["lhs_side"] == "arg0"
    assert payload["actual_compare"]["flag_side"] == "arg1"


def test_compare_callsite_reanchor_audit_rejects_old_frame_anchor_without_producer() -> None:
    candidates = [
        _compare_callsite_reanchor_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
            producer_matches=False,
        ),
        _compare_callsite_reanchor_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
            producer_matches=False,
        ),
        _compare_callsite_reanchor_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
            producer_matches=False,
        ),
    ]

    payload = build_compare_callsite_reanchor_and_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_upstream_writer_payload={"classification": "candidate_dependent_upstream_observed"},
    )

    assert payload["classification"] == "frame_anchor_rejected"
    assert payload["actual_compare"]["lhs_side"] == "arg0"
    assert payload["frame_anchor"]["old_slot_ebp_minus_1170_status"] == "rejected"
    assert payload["identified_producers"] == []
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_provenance_confirms_esi_source_without_promoting_context_hooks() -> None:
    candidates = [
        _compare_real_lhs_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
        ),
        _compare_real_lhs_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
        ),
        _compare_real_lhs_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
        ),
    ]

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_callsite_reanchor_payload={"classification": "callsite_reanchored_but_producer_unknown"},
    )

    assert payload["classification"] == "lhs_register_source_confirmed"
    assert payload["candidate_count"] == 3
    assert payload["candidate_limit"] == 3
    assert payload["actual_compare"]["entry"] == "0x258c"
    assert payload["actual_compare"]["lhs_side"] == "arg0"
    assert payload["relations"]["esi_to_compare_arg0"] == "confirmed"
    assert payload["frame_anchor"]["old_slot_ebp_minus_1170_status"] == "rejected"
    assert payload["identified_producers"] == []
    assert payload["next_producer_window"]["start_rva"] == "0x2559"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["candidate_generation_changed"] is False
    assert payload["ranking_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False


def test_compare_real_lhs_provenance_confirms_esi_from_static_callsite_snapshot() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        result = _compare_callsite_reanchor_candidate_result(
            candidate_hex,
            ptr,
            preview,
            old_frame_matches=False,
            producer_matches=False,
            compare_hook_name="static_compare_callsite",
        )
        result["hook_observations"] = [
            item for item in result["hook_observations"] if item["hook_name"] == "static_compare_callsite"
        ]
        result["hook_observations"][0]["esi_ptr"] = ptr
        result["hook_observations"][0]["esi_preview_hex"] = preview
        candidates.append(result)

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_callsite_reanchor_payload={"classification": "callsite_reanchored_but_producer_unknown"},
    )

    esi_evidence = next(
        row for row in payload["provenance"]["evidence"] if row["hook_name"] == "pre_compare_lhs_push"
    )
    assert payload["classification"] == "lhs_register_source_confirmed"
    assert payload["relations"]["esi_to_compare_arg0"] == "confirmed"
    assert payload["next_producer_window"]["start_rva"] == "0x2559"
    assert esi_evidence["runtime_backed_count"] == 3
    assert esi_evidence["connects_to_compare_lhs"] is True


def _last_writer_event(
    ptr: str,
    preview: str,
    *,
    sequence: int = 1,
    address: str | None = None,
    after_preview: str | None = None,
    transform_material_backed: bool = False,
) -> dict[str, object]:
    return {
        "sequence": sequence,
        "address": address or ptr,
        "size": 8,
        "instruction_address": "0x402400",
        "module_offset": "0x2400",
        "instruction": "mov dword ptr [edi], eax",
        "before_preview_hex": "00" * 32,
        "after_preview_hex": after_preview if after_preview is not None else preview,
        "arg0_value": ptr,
        "arg0_preview_hex": preview,
        "intersects_arg0": address is None,
        "transform_material_backed": transform_material_backed,
    }


def _write_monitor_health(
    *,
    raw_write_count: int,
    filtered_intersecting_write_count: int = 0,
    followed_thread_count: int = 1,
    activation_status: str = "following_current_thread",
    selected_thread_id: str = "1",
    follow_attempt_stage: str = "upstream_candidate_context",
    runtime_stage: str = "",
) -> dict[str, object]:
    return {
        "observed": True,
        "enabled": True,
        "activation_status": activation_status,
        "selected_thread_id": selected_thread_id,
        "follow_attempt_stage": follow_attempt_stage,
        "runtime_stage": runtime_stage,
        "followed_thread_count": followed_thread_count,
        "raw_write_count": raw_write_count,
        "ring_capacity": 4096,
        "eviction_count": 0,
        "descriptor_decode_failures": 0,
        "last_raw_write_samples": [
            {
                "sequence": max(raw_write_count - 1, 0),
                "address": "0x9000",
                "size": 8,
                "module_offset": "0x2400",
                "instruction": "mov dword ptr [edi], eax",
            }
        ]
        if raw_write_count
        else [],
        "filtered_intersecting_write_count": filtered_intersecting_write_count,
    }


def test_compare_real_lhs_last_writer_followed_thread_with_raw_write_zero_is_writer_missing() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[],
                write_monitor_health=_write_monitor_health(raw_write_count=0),
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "compare_lhs_runtime_backed_writer_missing"
    assert payload["lhs_writer_classification_blocker"] == "no_raw_write_events_observed"
    assert payload["write_monitor_health"]["raw_write_count"] == 0
    assert payload["write_monitor_health"]["followed_thread_count"] == 3
    assert payload["write_monitor_health"]["activation_statuses"] == ["following_current_thread"]
    assert payload["write_monitor_health"]["selected_thread_ids"] == ["1"]
    assert payload["write_monitor_health"]["follow_attempt_stages"] == ["upstream_candidate_context"]
    assert payload["last_writer_summary"]["write_monitor_health"]["enabled"] is True
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_last_writer_unfollowed_thread_is_instrumentation_incomplete() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[],
                write_monitor_health=_write_monitor_health(
                    raw_write_count=0,
                    followed_thread_count=0,
                    activation_status="waiting_for_hook_observation",
                    selected_thread_id="",
                    follow_attempt_stage="",
                ),
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["lhs_writer_classification_blocker"] == "write_monitor_not_following_thread"
    assert payload["write_monitor_health"]["followed_thread_count"] == 0
    assert payload["write_monitor_health"]["raw_write_count"] == 0
    assert payload["write_monitor_health"]["activation_statuses"] == ["waiting_for_hook_observation"]
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_script_delays_stalker_until_hook_thread() -> None:
    script_path = (
        compare_aware_search._compare_real_lhs_provenance_audit_script_path().parent
        / "compare_pre_compare_handoff_target_probe.py"
    )
    script_source = script_path.read_text(encoding="utf-8")

    assert "startWriteRingForThread(currentThreadId" in script_source
    assert "Process.getCurrentThreadId()" in script_source
    assert "waiting_for_hook_observation" in script_source
    assert "Process.enumerateThreads()" not in script_source


def test_compare_real_lhs_last_writer_uses_top_level_write_monitor_health() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidate = _compare_real_lhs_candidate_result(candidate_hex, ptr, preview, write_events=[])
        candidate["write_monitor_health"] = _write_monitor_health(raw_write_count=0)
        candidates.append(candidate)

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "compare_lhs_runtime_backed_writer_missing"
    assert payload["lhs_writer_classification_blocker"] == "no_raw_write_events_observed"
    assert payload["write_monitor_health"]["observed_candidate_count"] == 3
    assert payload["write_monitor_health"]["enabled"] is True
    assert payload["write_monitor_health"]["ring_capacity"] == 4096
    assert payload["write_monitor_health"]["activation_statuses"] == ["following_current_thread"]
    assert payload["last_writer_summary"]["write_monitor_health"]["enabled"] is True


def test_compare_real_lhs_last_writer_missing_write_monitor_health_is_instrumentation_incomplete() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[],
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["lhs_writer_classification_blocker"] == "write_monitor_observation_incomplete"
    assert payload["write_monitor_health"]["observed_candidate_count"] == 0
    assert payload["write_monitor_health"]["raw_write_count"] == 0
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_last_writer_raw_writes_without_intersections_are_writer_missing() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[
                    _last_writer_event(ptr, preview, sequence=1, address="0x9000", after_preview="11" * 32),
                ],
                write_monitor_health=_write_monitor_health(raw_write_count=7),
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "compare_lhs_runtime_backed_writer_missing"
    assert payload["lhs_writer_classification_blocker"] == "arg0_final_writer_trace_schema_gap"
    assert payload["write_monitor_health"]["raw_write_count"] == 21
    assert payload["write_monitor_health"]["filtered_intersecting_write_count"] == 0
    assert payload["write_monitor_health"]["missing_candidate_count"] == 3
    assert payload["raw_write_gap_summary"]["classification"] == "arg0_pointer_origin_untracked"
    assert payload["raw_write_gap_summary"]["arg0_pointer_origin_status"] == "untracked"
    assert payload["raw_write_gap_summary"]["write_monitor_target_source"] == "static_compare_callsite_arg0"
    assert payload["raw_write_gap_summary"]["raw_write_window_summary"][0]["actual_arg0"] == "0x1100"
    assert payload["raw_write_gap_summary"]["raw_write_window_summary"][0]["nearest_write_address"] == "0x9000"
    assert payload["last_writer_summary"]["raw_write_event_count"] == 3
    assert payload["last_writer_summary"]["non_intersecting_write_count"] == 3
    assert payload["last_writer_summary"]["missing_candidate_reasons"][0]["reason"] == (
        "raw_writes_observed_but_none_intersect_actual_arg0"
    )
    assert payload["last_writer_summary"]["missing_candidate_reasons"][0]["nearest_non_intersecting_writes"][0][
        "bounded_failure_reason"
    ] == "write_after_arg0_window"
    assert payload["last_writer_summary"]["retained_write_count"] == 0
    trace = payload["arg0_pointer_origin_trace"]
    assert trace["classification"] == "carrier_identified_writer_missing"
    assert trace["carrier_identified_count"] == 3
    assert trace["final_writer_status"] == "missing"
    assert trace["rows"][0]["pre_compare_esi_equals_arg0"] is True
    assert trace["rows"][0]["carrier_relation"] == "pointer_carrier"
    final_trace = payload["arg0_final_data_writer_trace"]
    assert final_trace["classification"] == "final_writer_trace_schema_gap"
    assert final_trace["rows"][0]["final_writer_gap_reason"] == "bounded_pointer_chain_rows_missing"
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_arg0_final_trace_keeps_pointer_chain_separate_from_writer() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _with_arg0_pointer_chain(
                _compare_real_lhs_candidate_result(
                    candidate_hex,
                    ptr,
                    preview,
                    write_events=[
                        _last_writer_event(ptr, preview, sequence=1, address="0x9000", after_preview="11" * 32),
                    ],
                    write_monitor_health=_write_monitor_health(raw_write_count=7),
                ),
                ptr,
                preview,
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    trace = payload["arg0_final_data_writer_trace"]
    assert trace["classification"] == "writer_not_observed_in_bounded_window"
    assert payload["lhs_writer_classification_blocker"] == "arg0_final_writer_not_observed_in_bounded_window"
    assert payload["last_writer_candidates"] == []
    assert trace["pointer_carrier_is_final_writer"] is False
    assert trace["pointer_write_is_final_data_writer"] is False
    assert trace["rows"][0]["slot_writer_equals_reload_source"] is True
    assert trace["rows"][0]["nearest_write_intersects_arg0"] is False


def test_compare_real_lhs_arg0_final_trace_promotes_only_intersecting_data_writes() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _with_arg0_pointer_chain(
                _compare_real_lhs_candidate_result(
                    candidate_hex,
                    ptr,
                    preview,
                    write_events=[
                        _last_writer_event(ptr, preview, sequence=1, address="0x9000", after_preview="11" * 32),
                        _last_writer_event(ptr, preview, sequence=2),
                    ],
                    write_monitor_health=_write_monitor_health(
                        raw_write_count=7,
                        filtered_intersecting_write_count=1,
                    ),
                ),
                ptr,
                preview,
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    trace = payload["arg0_final_data_writer_trace"]
    assert trace["classification"] == "final_writer_identified"
    assert payload["lhs_writer_classification_blocker"] == "arg0_final_data_writer_identified"
    assert len(payload["last_writer_candidates"]) == 3
    assert trace["rows"][0]["nearest_write_intersects_arg0"] is True
    assert trace["rows"][0]["nearest_write_address"] == "0x1100"


def test_run_compare_real_lhs_no_script_output_marks_fallback_non_provenance(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        command = list(args[0])
        script_name = Path(command[1]).name
        out_path = Path(command[command.index("--out") + 1])
        candidate_hex = command[command.index("--probe-hex") + 1]
        previews = {
            "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
            "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
            "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
        }
        if script_name == "compare_probe.py":
            ptr, preview = previews[candidate_hex]
            out_path.write_text(
                json.dumps(
                    {
                        "success": True,
                        "compare_site": "0x40258c",
                        "lhs_ptr": ptr,
                        "rhs_ptr": "0x5000",
                        "compare_count": 5,
                        "lhs_wide_hex": preview,
                        "rhs_wide_hex": "66006c00610067007b00",
                        "esi_ptr": ptr,
                        "esi_preview_hex": preview,
                    }
                ),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(command, 0, stdout="script stdout", stderr="")

    monkeypatch.setattr(compare_aware_search.subprocess, "run", fake_run)

    result = run_compare_real_lhs_provenance_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_real_lhs_provenance_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    payload = result["payload"]
    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["write_monitor_health"]["observed_candidate_count"] == 0
    assert payload["candidate_execution_health"][0]["scripted_hook_status"] == "scripted_hook_missing"
    assert (
        payload["candidate_execution_health"][0]["compare_probe_fallback_status"]
        == "compare_probe_fallback_captured_compare_args"
    )
    assert payload["candidate_execution_health"][0]["compare_probe_fallback_is_provenance"] is False
    assert payload["last_writer_summary"]["retained_write_count"] == 0
    assert all(
        any(
            observation.get("source") == "compare_probe_fallback"
            for observation in candidate["hook_observations"]
        )
        for candidate in payload["candidate_results"]
    )


def test_run_compare_real_lhs_script_health_survives_compare_probe_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        command = list(args[0])
        script_name = Path(command[1]).name
        out_path = Path(command[command.index("--out") + 1])
        candidate_hex = command[command.index("--probe-hex") + 1]
        previews = {
            "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
            "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
            "78d540b49c59076f41414141414141": ("0x3300", "cc" * 32),
        }
        if script_name == "compare_real_lhs_provenance_audit.py":
            out_path.write_text(
                json.dumps(
                    {
                        "success": False,
                        "hook_observations": [],
                        "write_monitor_health": _write_monitor_health(raw_write_count=0),
                        "write_ring_buffer": [],
                        "hook_install_status": "installed",
                        "hook_count": 4,
                        "requested_hook_count": 4,
                        "script_load_status": "loaded",
                        "python_message_callback_registered_before_load": True,
                        "python_message_count_total": 21,
                        "process_spawned_at_ms": 1000,
                        "frida_attached_at_ms": 1100,
                        "script_load_start_at_ms": 1200,
                        "script_loaded_at_ms": 1300,
                        "message_callback_registered_at_ms": 1190,
                        "hooks_install_begin_at_ms": 1210,
                        "hooks_installed_at_ms": 1250,
                        "ui_trigger_start_at_ms": 1400,
                        "ui_trigger_end_at_ms": 1450,
                        "hooks_ready_barrier_seen": True,
                        "hooks_ready_barrier_wait_ms": 20.0,
                        "hooks_ready_before_ui_trigger": True,
                        "ui_trigger_timing_status": "hooks_ready_before_ui_trigger",
                        "timeout_or_wait_reason": "bounded_wait_ended_without_static_compare_observation",
                        "ui_trigger_status": "button_triggered",
                        "ui_trigger_after_hooks_installed": True,
                    }
                ),
                encoding="utf-8",
            )
        elif script_name == "compare_probe.py":
            ptr, preview = previews[candidate_hex]
            out_path.write_text(
                json.dumps(
                    {
                        "success": True,
                        "compare_site": "0x40258c",
                        "lhs_ptr": ptr,
                        "rhs_ptr": "0x5000",
                        "compare_count": 5,
                        "lhs_wide_hex": preview,
                        "rhs_wide_hex": "66006c00610067007b00",
                        "esi_ptr": ptr,
                        "esi_preview_hex": preview,
                    }
                ),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(compare_aware_search.subprocess, "run", fake_run)

    result = run_compare_real_lhs_provenance_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_real_lhs_provenance_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    payload = result["payload"]
    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["write_monitor_health"]["observed_candidate_count"] == 3
    assert payload["write_monitor_health"]["enabled"] is True
    assert payload["write_monitor_health"]["ring_capacity"] == 4096
    assert payload["candidate_execution_health"][0]["scripted_hook_status"] == "scripted_hook_no_observations"
    assert payload["candidate_execution_health"][0]["compare_probe_fallback_is_provenance"] is False
    assert payload["candidate_execution_health"][0]["hooks_ready_before_ui_trigger"] is True
    assert payload["candidate_execution_health"][0]["ui_trigger_start_at_ms"] == 1400
    assert (
        payload["sidecar_observation_blocker"]
        == "hook_installed_but_compare_call_not_reached_after_ui_trigger"
    )
    assert (
        payload["lhs_writer_classification_blocker"]
        == "hook_installed_but_compare_call_not_reached_after_ui_trigger"
    )
    assert payload["candidate_results"][0]["hooks_installed_at_ms"] == 1250


def test_compare_real_lhs_last_writer_requires_all_three_candidates() -> None:
    candidates = [
        _compare_real_lhs_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
            write_events=[_last_writer_event("0x1100", "aa" * 32)],
            write_monitor_health=_write_monitor_health(raw_write_count=5, filtered_intersecting_write_count=1),
        ),
        _compare_real_lhs_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
            write_events=[_last_writer_event("0x2200", "bb" * 32)],
            write_monitor_health=_write_monitor_health(raw_write_count=5, filtered_intersecting_write_count=1),
        ),
        _compare_real_lhs_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
            write_events=[],
            write_monitor_health=_write_monitor_health(raw_write_count=5),
        ),
    ]

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "writer_path_observed_but_unconnected"
    assert payload["last_writer_summary"]["runtime_backed_count"] == 2
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_last_writer_filters_retained_writes_after_arg0_known() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[
                    _last_writer_event(ptr, preview, sequence=1, address="0x9000", after_preview="11" * 32),
                    _last_writer_event(ptr, preview, sequence=2),
                ],
                write_monitor_health=_write_monitor_health(
                    raw_write_count=7,
                    filtered_intersecting_write_count=1,
                ),
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "last_writer_identified"
    assert payload["last_writer_summary"]["runtime_backed_count"] == 3
    assert all(row["sequence"] == 2 for row in payload["last_writer_candidates"])
    assert payload["last_writer_candidates"][0]["write_address"] == "0x1100"
    assert payload["last_writer_candidates"][0]["arg0_ptr"] == "0x1100"
    assert payload["last_writer_candidates"][0]["compare_arg0_preview_hex"].startswith("aa")
    assert payload["last_writer_candidates"][0]["candidate_dependent"] is True
    assert payload["last_writer_candidates"][0]["hit_count"] == 1
    assert payload["last_writer_summary"]["raw_write_event_count"] == 6
    assert payload["last_writer_summary"]["non_intersecting_write_count"] == 3
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_last_writer_rejects_after_preview_mismatch() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[_last_writer_event(ptr, preview, after_preview="dd" * 32)],
                write_monitor_health=_write_monitor_health(
                    raw_write_count=5,
                    filtered_intersecting_write_count=1,
                ),
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "writer_path_observed_but_unconnected"
    assert payload["write_monitor_health"]["raw_write_count"] == 15
    assert payload["write_monitor_health"]["filtered_intersecting_write_count"] == 3
    assert payload["last_writer_summary"]["match_count"] == 0
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_last_writer_breakpoint_gate_requires_transform_material() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[
                    _last_writer_event(
                        ptr,
                        preview,
                        transform_material_backed=True,
                    )
                ],
                write_monitor_health=_write_monitor_health(
                    raw_write_count=5,
                    filtered_intersecting_write_count=1,
                ),
            )
        )

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_post_handoff_exception_payload={"classification": "compare_reached_but_path_unresolved"},
    )

    assert payload["classification"] == "last_writer_identified"
    assert payload["last_writer_summary"]["transform_material_backed"] is True
    assert payload["breakpoint_probe_allowed"] is True


def test_compare_lhs_last_writer_payload_maps_runtime_writer_schema() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[_last_writer_event(ptr, preview)],
                write_monitor_health=_write_monitor_health(
                    raw_write_count=5,
                    filtered_intersecting_write_count=1,
                ),
            )
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
        run_name="bounded_last_writer_test",
    )

    assert payload["artifact_kind"] == "compare_lhs_last_writer_provenance_audit"
    assert payload["classification"] == "runtime_backed_last_writer_identified"
    assert payload["compare_site"] == "0x258c"
    assert payload["candidate_input_hex"] == "78d540b49c59077041414141414141"
    assert payload["arg0_lhs_ptr"] == "0x1100"
    assert payload["arg0_lhs_preview"].startswith("aa")
    assert payload["last_writer"]["instruction"] == "mov dword ptr [edi], eax"
    assert payload["last_writer"]["module_offset"] == "0x2400"
    assert payload["observations"][0]["arg0_lhs_ptr"] == "0x1100"
    assert payload["bounded_failures"] == []
    assert payload["base64_rc4_breakpoint_probe_run"] is False
    assert payload["project_progress_log_handling"] == "untouched"


def test_compare_lhs_last_writer_payload_reports_compare_reached_but_writer_missing() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[],
                write_monitor_health=_write_monitor_health(raw_write_count=3),
            )
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
    )

    assert payload["classification"] == "compare_reached_but_writer_missing"
    assert payload["last_writer"] == {}
    assert "none intersected actual arg0" in " ".join(payload["bounded_failures"])
    assert payload["next_allowed_probe"] == "narrow bounded write attribution before Base64/RC4 probe"


def test_compare_lhs_last_writer_payload_reports_instrumentation_incomplete() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
    ]:
        candidates.append(
            _compare_real_lhs_candidate_result(
                candidate_hex,
                ptr,
                preview,
                write_events=[],
                write_monitor_health=_write_monitor_health(
                    raw_write_count=0,
                    followed_thread_count=0,
                    activation_status="waiting_for_hook_observation",
                    selected_thread_id="",
                    follow_attempt_stage="",
                ),
            )
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
    )

    assert payload["classification"] == "instrumentation_incomplete"
    assert "did not follow a runtime thread" in " ".join(payload["bounded_failures"])
    assert payload["instrumentation_failure_stage"] == "thread_follow_not_activated"


def test_compare_lhs_last_writer_fallback_cannot_promote_to_provenance() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
    ]:
        candidate = _compare_real_lhs_candidate_result(
            candidate_hex,
            ptr,
            preview,
            write_events=[_last_writer_event(ptr, preview)],
            write_monitor_health=_write_monitor_health(raw_write_count=5, filtered_intersecting_write_count=1),
        )
        candidate["hook_observations"] = [
            {
                **observation,
                "source": "compare_probe_fallback",
            }
            for observation in candidate["hook_observations"]
            if observation["hook_name"] == "static_compare_callsite"
        ]
        candidate["compare_probe_fallback_used"] = True
        candidate["compare_probe_fallback_status"] = "compare_probe_fallback_captured_compare_args"
        candidates.append(candidate)

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
    )

    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["same_process_provenance"] is False
    assert payload["compare_probe_fallback_used"] is True
    assert payload["compare_probe_fallback_is_provenance"] is False
    assert payload["diagnostic_compare_args_captured"] is True
    assert payload["same_process_compare_args_captured"] is False
    assert payload["instrumentation_failure_stage"] == "same_process_compare_args_missing"


def test_compare_lhs_last_writer_timeout_has_precise_failure_stage() -> None:
    candidates = []
    for candidate_hex in [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
    ]:
        candidates.append(
            {
                "candidate_hex": candidate_hex,
                "hook_observations": [],
                "write_monitor_health": {
                    "observed": False,
                    "enabled": True,
                    "activation_status": "script_started",
                    "runtime_stage": "waiting_for_observation",
                    "followed_thread_count": 0,
                    "raw_write_count": 0,
                    "ring_capacity": 4096,
                },
                "scripted_hook_status": "scripted_hook_no_observations",
                "scripted_returncode": 124,
                "scripted_error": "timeout",
                "requested_hook_count": 3,
                "script_load_status": "not_started",
                "frida_message_error_count": 0,
            }
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
    )

    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["instrumentation_failure_stage"] == "timeout_before_script_lifecycle_observation"
    assert payload["root_cause_hypothesis"] == "timeout_before_script_lifecycle_observation"
    assert payload["hook_install_status"] == "not_confirmed_stage_missing"
    assert payload["requested_hook_count"] == 3
    assert payload["script_load_status"] == "not_started"
    assert payload["frida_message_error_count"] == 0
    assert payload["spawn_attach_resume_status"] == ""
    assert payload["ui_trigger_status"] == ""
    assert payload["helper_observation_count"] == 0
    assert payload["static_compare_observation_count"] == 0
    assert "script timed out before any configured hook observation" in " ".join(payload["bounded_failures"])
    assert "script lifecycle fields advanced past not_started" in " ".join(payload["bounded_failures"])


def test_compare_lhs_last_writer_script_load_error_maps_precisely(tmp_path: Path) -> None:
    out_path = tmp_path / "candidate.json"
    out_path.write_text("{}", encoding="utf-8")
    log_path = tmp_path / "candidate.log"
    log_path.write_text("", encoding="utf-8")

    metadata = compare_aware_search._compare_lhs_last_writer_candidate_stage_metadata(
        compare_payload={
            "script_load_status": "failed",
            "script_load_error": "SyntaxError: unexpected token",
            "requested_hook_count": 3,
            "python_exception_count": 1,
            "frida_message_error_count": 0,
        },
        scripted_hook_status="scripted_hook_no_observations",
        scripted_returncode=1,
        helper_observation_count=0,
        static_compare_observation_count=0,
        scripted_write_monitor_health={"runtime_stage": "loading_script"},
        compare_out=out_path,
        compare_log=log_path,
    )

    assert metadata["root_cause_hypothesis"] == "js_compile_error"
    assert metadata["script_load_status"] == "failed"
    assert metadata["script_load_error"] == "SyntaxError: unexpected token"
    assert metadata["python_exception_count"] == 1
    assert metadata["frida_message_error_count"] == 0


def test_compare_lhs_last_writer_frida_message_error_separate_from_python_exception(tmp_path: Path) -> None:
    out_path = tmp_path / "candidate.json"
    out_path.write_text("{}", encoding="utf-8")
    log_path = tmp_path / "candidate.log"
    log_path.write_text("", encoding="utf-8")

    metadata = compare_aware_search._compare_lhs_last_writer_candidate_stage_metadata(
        compare_payload={
            "script_load_status": "loaded",
            "hook_install_status": "installed",
            "hook_count": 3,
            "requested_hook_count": 3,
            "hooks_installed_stage_seen": True,
            "hooks_installed_stage_hook_count": 3,
            "frida_message_error_count": 1,
            "python_exception_count": 0,
            "hook_install_error_count": 0,
        },
        scripted_hook_status="scripted_hook_no_observations",
        scripted_returncode=0,
        helper_observation_count=0,
        static_compare_observation_count=0,
        scripted_write_monitor_health={"runtime_stage": "frida_message_error"},
        compare_out=out_path,
        compare_log=log_path,
    )

    assert metadata["root_cause_hypothesis"] == "frida_message_error"
    assert metadata["frida_message_error_count"] == 1
    assert metadata["python_exception_count"] == 0
    assert metadata["hook_install_error_count"] == 0


def test_compare_lhs_last_writer_hook_install_error_is_surfaced() -> None:
    candidates = []
    for candidate_hex in [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
    ]:
        candidates.append(
            {
                "candidate_hex": candidate_hex,
                "hook_observations": [],
                "write_monitor_health": {
                    "observed": False,
                    "enabled": True,
                    "runtime_stage": "loading_script",
                    "followed_thread_count": 0,
                    "raw_write_count": 0,
                },
                "scripted_hook_status": "scripted_hook_no_observations",
                "scripted_returncode": 0,
                "hook_install_status": "failed_or_not_confirmed",
                "hook_count": 0,
                "requested_hook_count": 3,
                "script_load_status": "loaded",
                "frida_message_error_count": 0,
                "hook_install_error_count": 2,
                "hooks_installed_stage_seen": True,
                "hooks_installed_stage_hook_count": 0,
                "per_hook_install_results": [
                    {
                        "name": "static_compare_callsite",
                        "module_offset": "0x258c",
                        "install_status": "failed",
                        "address": "0x40258c",
                        "error": "access violation",
                    },
                    {
                        "name": "post_handoff_lhs_reload",
                        "module_offset": "0x2559",
                        "install_status": "failed",
                        "address": "0x402559",
                        "error": "access violation",
                    },
                ],
                "root_cause_hypothesis": "hook_install_failed",
                "root_cause_evidence": ["static_compare_callsite: access violation"],
            }
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
    )

    assert payload["instrumentation_failure_stage"] == "hook_install_failed"
    assert payload["hook_install_status"] == "failed_or_not_confirmed"
    assert payload["requested_hook_count"] == 3
    assert payload["script_load_status"] == "loaded"
    assert payload["frida_message_error_count"] == 0
    assert payload["hook_install_error_count"] == 4
    assert payload["hooks_installed_stage_seen"] is True
    assert payload["hooks_installed_stage_hook_count"] == 0
    assert payload["per_hook_install_results"]
    assert "access violation" in " ".join(payload["root_cause_evidence"])


def test_compare_lhs_last_writer_loaded_without_hooks_installed_stage_is_precise(tmp_path: Path) -> None:
    out_path = tmp_path / "candidate.json"
    out_path.write_text("{}", encoding="utf-8")
    log_path = tmp_path / "candidate.log"
    log_path.write_text("", encoding="utf-8")

    metadata = compare_aware_search._compare_lhs_last_writer_candidate_stage_metadata(
        compare_payload={
            "script_load_status": "loaded",
            "hook_install_status": "not_confirmed_stage_missing",
            "hook_count": 0,
            "requested_hook_count": 3,
            "hooks_installed_stage_seen": False,
            "frida_message_error_count": 0,
            "python_exception_count": 0,
            "hook_install_error_count": 0,
        },
        scripted_hook_status="scripted_hook_no_observations",
        scripted_returncode=0,
        helper_observation_count=0,
        static_compare_observation_count=0,
        scripted_write_monitor_health={"runtime_stage": "waiting_for_observation"},
        compare_out=out_path,
        compare_log=log_path,
    )

    assert metadata["root_cause_hypothesis"] == "hooks_installed_stage_missing_after_script_load"
    assert metadata["hook_install_status"] == "not_confirmed_stage_missing"
    assert metadata["hooks_installed_stage_seen"] is False
    assert "hooks_installed_stage_seen=false" in " ".join(metadata["root_cause_evidence"])


def test_compare_lhs_last_writer_message_callback_is_registered_before_load() -> None:
    script_path = Path("reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py")
    source = script_path.read_text(encoding="utf-8")

    assert source.index('script.on("message", on_message)') < source.index("script.load()")
    assert "python_message_callback_registered_before_load = True" in source


def test_compare_lhs_last_writer_loaded_without_js_top_level_is_precise(tmp_path: Path) -> None:
    out_path = tmp_path / "candidate.json"
    out_path.write_text("{}", encoding="utf-8")
    log_path = tmp_path / "candidate.log"
    log_path.write_text("", encoding="utf-8")

    metadata = compare_aware_search._compare_lhs_last_writer_candidate_stage_metadata(
        compare_payload={
            "script_load_status": "loaded",
            "hook_install_status": "not_confirmed_stage_missing",
            "requested_hook_count": 3,
            "python_message_callback_registered_before_load": True,
            "python_message_count_total": 0,
            "js_top_level_seen": False,
            "js_hooks_install_begin_seen": False,
        },
        scripted_hook_status="scripted_hook_no_observations",
        scripted_returncode=0,
        helper_observation_count=0,
        static_compare_observation_count=0,
        scripted_write_monitor_health={"runtime_stage": "waiting_for_observation"},
        compare_out=out_path,
        compare_log=log_path,
    )

    assert metadata["root_cause_hypothesis"] == "js_top_level_not_seen"
    assert metadata["python_message_callback_registered_before_load"] is True
    assert metadata["python_message_count_total"] == 0


def test_compare_lhs_last_writer_js_top_level_without_install_begin_is_bridge_incomplete(tmp_path: Path) -> None:
    out_path = tmp_path / "candidate.json"
    out_path.write_text("{}", encoding="utf-8")
    log_path = tmp_path / "candidate.log"
    log_path.write_text("", encoding="utf-8")

    metadata = compare_aware_search._compare_lhs_last_writer_candidate_stage_metadata(
        compare_payload={
            "script_load_status": "loaded",
            "hook_install_status": "not_confirmed_stage_missing",
            "requested_hook_count": 3,
            "python_message_callback_registered_before_load": True,
            "python_message_count_total": 1,
            "python_message_count_by_type": {"compare_pre_compare_handoff_target_stage": 1},
            "js_top_level_seen": True,
            "js_hooks_install_begin_seen": False,
            "python_message_last_payload": {"runtime_stage": "js_top_level"},
        },
        scripted_hook_status="scripted_hook_no_observations",
        scripted_returncode=0,
        helper_observation_count=0,
        static_compare_observation_count=0,
        scripted_write_monitor_health={"runtime_stage": "waiting_for_observation"},
        compare_out=out_path,
        compare_log=log_path,
    )

    assert metadata["root_cause_hypothesis"] == "message_bridge_incomplete"
    assert metadata["js_top_level_seen"] is True
    assert metadata["js_hooks_install_begin_seen"] is False


def test_compare_lhs_last_writer_hooks_installed_zero_is_not_generic_timeout() -> None:
    candidates = []
    for candidate_hex in [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
    ]:
        candidates.append(
            {
                "candidate_hex": candidate_hex,
                "hook_observations": [],
                "write_monitor_health": {"enabled": True, "runtime_stage": "waiting_for_observation"},
                "scripted_hook_status": "scripted_hook_no_observations",
                "scripted_returncode": 0,
                "hook_install_status": "failed_or_not_confirmed",
                "hook_count": 0,
                "requested_hook_count": 3,
                "hooks_installed_stage_seen": True,
                "hooks_installed_stage_hook_count": 0,
                "script_load_status": "loaded",
                "root_cause_hypothesis": "hook_loop_completed_zero_installed",
                "root_cause_evidence": ["hook loop completed with zero installed"],
                "per_hook_install_results": [
                    {
                        "name": "static_compare_callsite",
                        "module_offset": "0x258c",
                        "install_status": "failed",
                        "address": "0x40258c",
                        "error": "attach failed",
                    },
                    {
                        "name": "post_handoff_lhs_reload",
                        "module_offset": "0x2559",
                        "install_status": "failed",
                        "address": "0x402559",
                        "error": "attach failed",
                    },
                    {
                        "name": "handoff_helper_candidate",
                        "module_offset": "0x1b50",
                        "install_status": "failed",
                        "address": "0x401b50",
                        "error": "attach failed",
                    },
                ],
            }
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
    )

    assert payload["instrumentation_failure_stage"] == "hook_loop_completed_zero_installed"
    assert payload["root_cause_hypothesis"] == "hook_loop_completed_zero_installed"
    assert payload["root_cause_hypothesis"] != "timeout_before_hook_install"
    assert "zero installed" in " ".join(payload["bounded_failures"])
    assert {item["module_offset"] for item in payload["per_hook_install_results"]} == {
        "0x258c",
        "0x2559",
        "0x1b50",
    }


def test_compare_lhs_last_writer_hooks_installed_but_not_hit_is_distinct() -> None:
    candidates = []
    for candidate_hex in [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
    ]:
        candidates.append(
            {
                "candidate_hex": candidate_hex,
                "hook_observations": [],
                "write_monitor_health": {"enabled": True, "runtime_stage": "waiting_for_observation"},
                "scripted_hook_status": "scripted_hook_no_observations",
                "scripted_returncode": 124,
                "hook_install_status": "installed",
                "hook_count": 3,
                "requested_hook_count": 3,
                "hooks_installed_stage_seen": True,
                "hooks_installed_stage_hook_count": 3,
                "script_load_status": "loaded",
                "root_cause_hypothesis": "hook_not_hit",
                "root_cause_evidence": ["hook_install_status=installed"],
                "per_hook_install_results": [
                    {"name": "static_compare_callsite", "module_offset": "0x258c", "install_status": "installed", "address": "0x40258c", "error": ""},
                    {"name": "post_handoff_lhs_reload", "module_offset": "0x2559", "install_status": "installed", "address": "0x402559", "error": ""},
                    {"name": "handoff_helper_candidate", "module_offset": "0x1b50", "install_status": "installed", "address": "0x401b50", "error": ""},
                ],
                "js_top_level_seen": True,
                "js_hooks_install_begin_seen": True,
                "js_hooks_installed_seen": True,
                "python_message_callback_registered_before_load": True,
                "python_message_count_total": 5,
                "module_base_resolution_status": "resolved",
                "ui_trigger_status": "button_triggered",
                "ui_trigger_after_hooks_installed": True,
                "observation_count": 0,
                "post_ui_observation_count": 0,
                "hook_hit_counts_by_name": {},
                "hook_not_hit_vs_hook_not_installed_classification": "hook_not_hit",
            }
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
    )

    assert payload["classification"] == "hook_installed_but_not_hit_after_ui_trigger"
    assert payload["instrumentation_failure_stage"] == "hook_installed_but_not_hit_after_ui_trigger"
    assert payload["root_cause_hypothesis"] == "hook_installed_but_not_hit_after_ui_trigger"
    assert payload["observation_count"] == 0
    assert payload["post_ui_observation_count"] == 0
    assert payload["hook_hit_counts_by_name"] == {}
    assert payload["hook_not_hit_vs_hook_not_installed_classification"] == "hook_not_hit"
    assert payload["compare_probe_fallback_is_provenance"] is False
    assert payload["sidecar_health"]["hook_install"]["hook_install_status"] == "installed"
    assert payload["sidecar_health"]["message_bridge"]["python_message_count_total"] == 10
    assert payload["sidecar_health"]["observations"]["observation_count"] == 0
    assert payload["observations"][0]["sidecar_health"]["hook_install"]["hook_install_status"] == "installed"


def test_compare_lhs_last_writer_helper_only_stage_is_stop_before_compare() -> None:
    candidates = []
    for candidate_hex in [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
    ]:
        candidates.append(
            {
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "candidate_hex": candidate_hex,
                        "hook_name": "handoff_helper_candidate",
                        "module_offset": "0x1b50",
                    }
                ],
                "write_monitor_health": _write_monitor_health(
                    raw_write_count=11,
                    runtime_stage="stop_condition_before_compare",
                    follow_attempt_stage="handoff_helper_candidate",
                ),
                "scripted_hook_status": "scripted_hook_observed",
                "scripted_returncode": 0,
                "same_process_compare_args_captured": False,
                "instrumentation_failure_stage": "stop_condition_before_compare",
            }
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
        project_progress_log_handling="reverted",
    )

    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["same_process_compare_args_captured"] is False
    assert payload["instrumentation_failure_stage"] == "stop_condition_before_compare"
    assert "did not reach 0x258c" in " ".join(payload["bounded_failures"])
    assert payload["project_progress_log_handling"] == "reverted"
    assert payload["helper_observation_count"] == 2
    assert payload["static_compare_observation_count"] == 0


def test_compare_lhs_last_writer_static_compare_without_args_reports_extraction_failure() -> None:
    candidates = []
    for candidate_hex in [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
    ]:
        candidates.append(
            {
                "candidate_hex": candidate_hex,
                "hook_observations": [
                    {
                        "candidate_hex": candidate_hex,
                        "hook_name": "static_compare_callsite",
                        "module_offset": "0x258c",
                        "compare_args": {},
                    }
                ],
                "write_monitor_health": _write_monitor_health(
                    raw_write_count=5,
                    runtime_stage="static_compare_callsite_observed_no_args",
                ),
                "scripted_hook_status": "scripted_hook_observed",
                "scripted_returncode": 0,
                "same_process_compare_args_captured": False,
                "instrumentation_failure_stage": "argument_extraction_failed",
            }
        )

    payload = build_compare_lhs_last_writer_provenance_audit_payload(
        candidate_results=candidates,
        source_real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
    )

    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["instrumentation_failure_stage"] == "argument_extraction_failed"
    assert "arguments were not extracted" in " ".join(payload["bounded_failures"])
    assert payload["static_compare_observation_count"] == 2


def test_run_compare_lhs_last_writer_provenance_audit_uses_bounded_candidates(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    scripted_candidates: list[str] = []

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        command = list(args[0])
        script_name = Path(command[1]).name
        out_path = Path(command[command.index("--out") + 1])
        candidate_hex = command[command.index("--probe-hex") + 1]
        scripted_candidates.append(candidate_hex)
        previews = {
            "78d540b49c59077041414141414141": ("0x1100", "aa" * 32),
            "5a3e7f46ddd474d041414141414141": ("0x2200", "bb" * 32),
        }
        ptr, preview = previews[candidate_hex]
        if script_name == "compare_lhs_last_writer_provenance.py":
            out_path.write_text(
                json.dumps(
                    {
                        "success": True,
                        "hook_observations": [
                            {
                                "candidate_hex": candidate_hex,
                                "hook_name": "static_compare_callsite",
                                "module_offset": "0x258c",
                                "compare_args": {
                                    "args": [
                                        {
                                            "index": 0,
                                            "role": "arg0",
                                            "value": ptr,
                                            "preview_hex": preview,
                                        },
                                        {
                                            "index": 1,
                                            "role": "arg1",
                                            "value": "0x5000",
                                            "preview_hex": "66006c00610067007b00",
                                        },
                                    ]
                                },
                                "write_monitor_health": _write_monitor_health(
                                    raw_write_count=3,
                                    filtered_intersecting_write_count=1,
                                ),
                                "write_ring_buffer": [_last_writer_event(ptr, preview)],
                            }
                        ],
                        "write_monitor_health": _write_monitor_health(
                            raw_write_count=3,
                            filtered_intersecting_write_count=1,
                        ),
                        "write_ring_buffer": [_last_writer_event(ptr, preview)],
                        "hook_install_status": "installed",
                        "hook_count": 3,
                        "requested_hook_count": 3,
                        "script_load_status": "loaded",
                        "script_load_error": "",
                        "python_exception_count": 0,
                        "frida_message_error_count": 0,
                        "hook_install_error_count": 0,
                        "hooks_installed_stage_seen": True,
                        "hooks_installed_stage_hook_count": 3,
                        "js_top_level_seen": True,
                        "js_top_level_timestamp": 123,
                        "js_hooks_install_begin_seen": True,
                        "js_hooks_installed_seen": True,
                        "js_hook_install_exception_count": 0,
                        "js_hook_install_exception_messages": [],
                        "python_message_callback_registered_before_load": True,
                        "python_message_count_total": 6,
                        "python_message_count_by_type": {
                            "compare_pre_compare_handoff_target_stage": 3,
                            "compare_pre_compare_handoff_target_hook_install_result": 3,
                        },
                        "python_message_decode_error_count": 0,
                        "python_message_last_payload": {"runtime_stage": "hooks_installed"},
                        "module_base_resolution_status": "resolved",
                        "hook_address_by_name": {
                            "static_compare_callsite": "0x40258c",
                            "post_handoff_lhs_reload": "0x402559",
                            "handoff_helper_candidate": "0x401b50",
                        },
                        "per_hook_install_results": [
                            {
                                "name": "static_compare_callsite",
                                "module_offset": "0x258c",
                                "install_status": "installed",
                                "address": "0x40258c",
                                "error": "",
                            },
                            {
                                "name": "post_handoff_lhs_reload",
                                "module_offset": "0x2559",
                                "install_status": "installed",
                                "address": "0x402559",
                                "error": "",
                            },
                            {
                                "name": "handoff_helper_candidate",
                                "module_offset": "0x1b50",
                                "install_status": "installed",
                                "address": "0x401b50",
                                "error": "",
                            },
                        ],
                        "spawn_attach_resume_status": "resumed",
                        "ui_trigger_status": "button_triggered",
                        "helper_observation_count": 1,
                        "static_compare_observation_count": 1,
                        "root_cause_hypothesis": "",
                        "root_cause_evidence": [],
                    }
                ),
                encoding="utf-8",
            )
        elif script_name == "compare_probe.py":
            out_path.write_text(
                json.dumps(
                    {
                        "success": True,
                        "compare_site": "0x40258c",
                        "lhs_ptr": ptr,
                        "rhs_ptr": "0x5000",
                        "compare_count": 5,
                        "lhs_wide_hex": preview,
                        "rhs_wide_hex": "66006c00610067007b00",
                        "esi_ptr": ptr,
                        "esi_preview_hex": preview,
                    }
                ),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(compare_aware_search.subprocess, "run", fake_run)

    result = run_compare_lhs_last_writer_provenance_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_lhs_last_writer_provenance_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(str(result["result_path"])).name == COMPARE_LHS_LAST_WRITER_PROVENANCE_AUDIT_FILE_NAME
    assert payload["classification"] == "runtime_backed_last_writer_identified"
    assert payload["candidate_inputs_hex"] == [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
    ]
    assert sorted(set(scripted_candidates)) == sorted(payload["candidate_inputs_hex"])
    assert payload["hook_points"][0]["module_offset"] == 0x258C
    assert payload["hook_points"][1]["module_offset"] == 0x2559
    assert payload["hook_points"][2]["module_offset"] == 0x1B50
    assert payload["hook_install_status"] == "installed"
    assert payload["hook_count"] == 3
    assert payload["requested_hook_count"] == 3
    assert payload["script_load_status"] == "loaded"
    assert payload["python_exception_count"] == 0
    assert payload["frida_message_error_count"] == 0
    assert payload["hook_install_error_count"] == 0
    assert payload["hooks_installed_stage_seen"] is True
    assert payload["hooks_installed_stage_hook_count"] == 3
    assert payload["js_top_level_seen"] is True
    assert payload["js_hooks_install_begin_seen"] is True
    assert payload["js_hooks_installed_seen"] is True
    assert payload["python_message_callback_registered_before_load"] is True
    assert payload["python_message_count_total"] == 12
    assert payload["module_base_resolution_status"] == "resolved"
    assert payload["hook_address_by_name"]["static_compare_callsite"] == "0x40258c"
    assert {item["module_offset"] for item in payload["per_hook_install_results"]} == {
        "0x258c",
        "0x2559",
        "0x1b50",
    }
    assert payload["spawn_attach_resume_status"] == "resumed"
    assert payload["ui_trigger_status"] == "button_triggered"
    assert payload["helper_observation_count"] == 2
    assert payload["static_compare_observation_count"] == 2
    assert payload["candidate_log_paths"]
    assert payload["candidate_invocation_health"]
    first_health = payload["candidate_invocation_health"][payload["candidate_inputs_hex"][0]]
    assert first_health["subprocess_command"][0]
    assert first_health["subprocess_returncode"] == 0
    assert first_health["scripted_output_exists"] is True
    assert first_health["scripted_log_size_bytes"] > 0
    assert first_health["scripted_lifecycle_entered"] is True
    assert payload["compare_probe_sidecar_diff"]["compare_probe_fallback_is_provenance"] is False


def test_run_compare_lhs_last_writer_records_timeout_invocation_health(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        command = list(args[0])
        script_name = Path(command[1]).name
        out_path = Path(command[command.index("--out") + 1])
        candidate_hex = command[command.index("--probe-hex") + 1]
        if script_name == "compare_lhs_last_writer_provenance.py":
            out_path.write_text(
                json.dumps(
                    {
                        "success": False,
                        "candidate_hex": candidate_hex,
                        "hook_observations": [],
                        "evidence": ["compare_pre_compare_handoff_target_probe:script_started"],
                        "requested_hook_count": 3,
                        "script_load_status": "not_started",
                        "spawn_attach_resume_status": "not_started",
                        "ui_trigger_status": "not_started",
                        "runtime_stage": "script_started",
                        "write_monitor_health": {"runtime_stage": "script_started"},
                    }
                ),
                encoding="utf-8",
            )
            raise compare_aware_search.subprocess.TimeoutExpired(
                command,
                timeout=kwargs.get("timeout", 1.0),
                output="sidecar stdout tail",
                stderr="sidecar stderr tail",
            )
        if script_name == "compare_probe.py":
            out_path.write_text(
                json.dumps(
                    {
                        "success": True,
                        "compare_site": "0x40258c",
                        "lhs_ptr": "0x1100",
                        "rhs_ptr": "0x5000",
                        "compare_count": 5,
                        "lhs_wide_hex": "aa" * 32,
                        "rhs_wide_hex": "66006c00610067007b00",
                        "esi_ptr": "0x1100",
                        "esi_preview_hex": "aa" * 32,
                    }
                ),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(command, 0, stdout="probe stdout", stderr="")

    monkeypatch.setattr(compare_aware_search.subprocess, "run", fake_run)

    result = run_compare_lhs_last_writer_provenance_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_lhs_last_writer_provenance_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        real_lhs_payload={"classification": "compare_lhs_runtime_backed_writer_missing"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "instrumentation_incomplete"
    assert payload["root_cause_hypothesis"] == "timeout_after_initial_payload_before_lifecycle"
    assert payload["compare_probe_fallback_is_provenance"] is False
    assert payload["diagnostic_compare_args_captured"] is True
    assert payload["same_process_compare_args_captured"] is False
    for candidate_hex in payload["candidate_inputs_hex"]:
        health = payload["candidate_invocation_health"][candidate_hex]
        assert health["subprocess_returncode"] == 124
        assert health["subprocess_timed_out"] is True
        assert health["subprocess_stdout_tail"] == "sidecar stdout tail"
        assert health["subprocess_stderr_tail"] == "sidecar stderr tail"
        assert health["scripted_output_exists"] is True
        assert health["scripted_output_size_bytes"] > 0
        assert health["scripted_initial_payload_only"] is True
        assert health["scripted_lifecycle_entered"] is False
        assert health["scripted_last_runtime_stage"] == "script_started"
        assert Path(str(health["scripted_log_path"])).exists()
    diff = payload["compare_probe_sidecar_diff"]
    assert diff["compare_probe_fallback_is_provenance"] is False
    assert set(diff["compare_probe_fallback_command_or_path"]) == set(payload["candidate_inputs_hex"])


def test_compare_probe_fallback_observation_carries_esi_snapshot() -> None:
    observation = compare_aware_search._compare_probe_payload_to_static_callsite_observation(
        {
            "success": True,
            "compare_site": "0x40258c",
            "lhs_ptr": "0x1100",
            "rhs_ptr": "0x5000",
            "compare_count": 5,
            "lhs_wide_hex": "aa" * 32,
            "rhs_wide_hex": "66006c00610067007b00",
            "esi_ptr": "0x1100",
            "esi_preview_hex": "aa" * 32,
        },
        "78d540b49c59077041414141414141",
    )

    assert observation["hook_name"] == "static_compare_callsite"
    assert observation["esi_ptr"] == "0x1100"
    assert observation["esi_preview_hex"] == "aa" * 32
    assert observation["registers"]["esi"] == "0x1100"


def test_compare_real_lhs_provenance_rejects_old_frame_without_esi() -> None:
    candidates = [
        _compare_real_lhs_candidate_result(
            "78d540b49c59077041414141414141",
            "0x1100",
            "aa" * 32,
            esi_matches=False,
        ),
        _compare_real_lhs_candidate_result(
            "5a3e7f46ddd474d041414141414141",
            "0x2200",
            "bb" * 32,
            esi_matches=False,
        ),
        _compare_real_lhs_candidate_result(
            "78d540b49c59076f41414141414141",
            "0x3300",
            "cc" * 32,
            esi_matches=False,
        ),
    ]

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_callsite_reanchor_payload={"classification": "callsite_reanchored_but_producer_unknown"},
    )

    assert payload["classification"] == "old_frame_anchor_rejected"
    assert payload["relations"]["esi_to_compare_arg0"] == "inconclusive"
    assert payload["frame_anchor"]["old_slot_ebp_minus_1170_status"] == "rejected"
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_real_lhs_provenance_rejects_unobserved_old_frame_when_compare_arg0_confirmed() -> None:
    candidates = []
    for candidate_hex, ptr, preview in [
        ("78d540b49c59077041414141414141", "0x1100", "aa" * 32),
        ("5a3e7f46ddd474d041414141414141", "0x2200", "bb" * 32),
        ("78d540b49c59076f41414141414141", "0x3300", "cc" * 32),
    ]:
        result = _compare_callsite_reanchor_candidate_result(
            candidate_hex,
            ptr,
            preview,
            old_frame_matches=False,
            producer_matches=False,
            compare_hook_name="static_compare_callsite",
        )
        result["hook_observations"] = [
            item for item in result["hook_observations"] if item["hook_name"] == "static_compare_callsite"
        ]
        candidates.append(result)

    payload = build_compare_real_lhs_provenance_audit_payload(
        candidate_results=candidates,
        source_callsite_reanchor_payload={"classification": "callsite_reanchored_but_producer_unknown"},
    )

    assert payload["classification"] == "old_frame_anchor_rejected"
    assert payload["relations"]["old_frame_anchor_to_compare_arg0"] == "rejected"
    assert payload["frame_anchor"]["old_slot_observed_count"] == 0
    assert "0x258b" in payload["next_bounded_action"]


def test_run_compare_real_lhs_provenance_audit_uses_fixed_candidates(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_real_lhs_subprocess_run)

    result = run_compare_real_lhs_provenance_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_real_lhs_provenance_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        callsite_reanchor_payload={"classification": "callsite_reanchored_but_producer_unknown"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(str(result["result_path"])).name == COMPARE_REAL_LHS_PROVENANCE_AUDIT_FILE_NAME
    assert payload["classification"] == "lhs_register_source_confirmed"
    assert payload["fixed_candidates"] == [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
        "78d540b49c59076f41414141414141",
    ]


def test_compare_esi_source_window_identifies_initial_source() -> None:
    payload = build_compare_esi_source_window_audit_payload(
        candidate_results=_compare_esi_source_window_candidates(initial_matches=True),
        source_real_lhs_payload={"classification": "lhs_register_source_confirmed"},
    )

    assert payload["classification"] == "esi_source_identified"
    assert payload["relations"]["initial_reload_to_arg0"] == "confirmed"
    assert payload["relations"]["pre_compare_esi_to_arg0"] == "confirmed"
    assert payload["breakpoint_probe_allowed"] is True
    assert payload["candidate_generation_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False


def test_compare_esi_source_window_classifies_repair_call_update() -> None:
    payload = build_compare_esi_source_window_audit_payload(
        candidate_results=_compare_esi_source_window_candidates(
            initial_matches=False,
            final_matches=True,
            repair_observed=True,
        ),
        source_real_lhs_payload={"classification": "lhs_register_source_confirmed"},
    )

    assert payload["classification"] == "repair_call_updates_lhs"
    assert payload["relations"]["initial_reload_to_arg0"] == "inconclusive"
    assert payload["relations"]["final_reload_to_arg0"] == "confirmed"
    assert payload["relations"]["repair_path_observed"] == "confirmed"
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_esi_source_window_classifies_branch_bypass() -> None:
    payload = build_compare_esi_source_window_audit_payload(
        candidate_results=_compare_esi_source_window_candidates(
            initial_matches=False,
            final_matches=False,
            repair_observed=False,
        ),
        source_real_lhs_payload={"classification": "lhs_register_source_confirmed"},
    )

    assert payload["classification"] == "pre_compare_branch_bypasses_repair"
    assert payload["relations"]["repair_path_observed"] == "rejected"
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_esi_source_window_classifies_observed_unknown() -> None:
    payload = build_compare_esi_source_window_audit_payload(
        candidate_results=_compare_esi_source_window_candidates(
            initial_matches=False,
            final_matches=False,
            repair_observed=False,
            branch_observed=False,
        ),
        source_real_lhs_payload={"classification": "lhs_register_source_confirmed"},
    )

    assert payload["classification"] == "window_observed_but_source_unknown"
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_esi_source_window_classifies_inconclusive_without_runtime() -> None:
    payload = build_compare_esi_source_window_audit_payload(
        candidate_results=[],
        source_real_lhs_payload={"classification": "lhs_register_source_confirmed"},
    )

    assert payload["classification"] == "inconclusive"
    assert payload["runtime_backed_count"] == 0
    assert payload["breakpoint_probe_allowed"] is False


def test_run_compare_esi_source_window_audit_uses_fixed_candidates(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_esi_source_window_subprocess_run)

    result = run_compare_esi_source_window_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_esi_source_window_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        real_lhs_payload={"classification": "lhs_register_source_confirmed"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(str(result["result_path"])).name == COMPARE_ESI_SOURCE_WINDOW_AUDIT_FILE_NAME
    assert payload["classification"] == "esi_source_identified"
    assert payload["fixed_candidates"] == [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
        "78d540b49c59076f41414141414141",
    ]


def test_compare_lhs_slot_writer_source_confirms_slot_writer() -> None:
    payload = build_compare_lhs_slot_writer_source_audit_payload(
        candidate_results=_compare_lhs_slot_writer_source_candidates(),
        source_material_hook_payload={
            "classification": "REJECTED",
            "source_compare_esi_source_window_classification": "esi_source_identified",
        },
    )

    assert payload["classification"] == "slot_writer_confirmed"
    assert payload["slot_writer"]["hook_name"] == "slot_writer"
    assert payload["slot_writer"]["compare_lhs_match_count"] == 3
    assert payload["relations"]["slot_writer_to_compare_arg0"] == "confirmed"
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["promotable_validations"][0]["hook_name"] == "slot_writer"


def test_compare_lhs_slot_writer_source_classifies_writer_not_reached() -> None:
    payload = build_compare_lhs_slot_writer_source_audit_payload(
        candidate_results=_compare_lhs_slot_writer_source_candidates(slot_writer_observed=False),
        source_material_hook_payload={
            "classification": "REJECTED",
            "source_compare_esi_source_window_classification": "esi_source_identified",
        },
    )

    assert payload["classification"] == "writer_hook_not_reached"
    assert payload["slot_writer"]["observed_count"] == 0
    assert payload["breakpoint_probe_allowed"] is False


def test_run_compare_lhs_slot_writer_source_audit_uses_fixed_candidates(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_compare_lhs_slot_writer_source_subprocess_run)

    result = run_compare_lhs_slot_writer_source_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_lhs_slot_writer_source_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        material_hook_payload={
            "classification": "REJECTED",
            "source_compare_esi_source_window_classification": "esi_source_identified",
        },
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(str(result["result_path"])).name == COMPARE_LHS_SLOT_WRITER_SOURCE_AUDIT_FILE_NAME
    assert payload["classification"] == "slot_writer_confirmed"
    assert payload["fixed_candidates"] == [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
        "78d540b49c59076f41414141414141",
    ]
    assert payload["candidate_generation_changed"] is False
    assert payload["beam_budget_topn_timeout_frontier_limit_expanded"] is False


def test_compare_lhs_slot_writer_predecessor_classifies_handoff_no_return() -> None:
    payload = build_compare_lhs_slot_writer_predecessor_audit_payload(
        candidate_results=_compare_lhs_slot_writer_predecessor_candidates(handoff_return_observed=False),
        source_slot_writer_payload={"classification": "writer_hook_not_reached"},
    )

    assert payload["classification"] == "handoff_call_does_not_return_to_linear_path"
    assert payload["path_observed_counts"]["predecessor_handoff_call"] == 3
    assert payload["path_observed_counts"]["predecessor_handoff_return"] == 0
    assert payload["breakpoint_probe_allowed"] is False


def test_compare_lhs_slot_writer_predecessor_classifies_linear_path_divergence() -> None:
    payload = build_compare_lhs_slot_writer_predecessor_audit_payload(
        candidate_results=_compare_lhs_slot_writer_predecessor_candidates(
            handoff_return_observed=True,
            downstream_output_observed=False,
        ),
        source_slot_writer_payload={"classification": "writer_hook_not_reached"},
    )

    assert payload["classification"] == "linear_path_diverges_before_output_call"
    assert payload["path_observed_counts"]["predecessor_handoff_return"] == 3
    assert payload["path_observed_counts"]["predecessor_output_call"] == 0


def test_compare_lhs_slot_writer_predecessor_identifies_pre_slot_source() -> None:
    payload = build_compare_lhs_slot_writer_predecessor_audit_payload(
        candidate_results=_compare_lhs_slot_writer_predecessor_candidates(
            handoff_return_observed=True,
            downstream_output_observed=True,
            source_matches=True,
        ),
        source_slot_writer_payload={"classification": "writer_hook_not_reached"},
    )

    assert payload["classification"] == "pre_slot_source_identified"
    assert payload["relations"]["pre_slot_source_to_compare_arg0"] == "confirmed"
    assert payload["promotable_validations"][0]["hook_name"] == "predecessor_output_call"


def test_run_compare_lhs_slot_writer_predecessor_audit_uses_fixed_candidates(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(
        compare_aware_search.subprocess,
        "run",
        _fake_compare_lhs_slot_writer_predecessor_subprocess_run,
    )

    result = run_compare_lhs_slot_writer_predecessor_audit(
        target=target,
        artifacts_dir=tmp_path / "compare_lhs_slot_writer_predecessor_audit",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        slot_writer_payload={"classification": "writer_hook_not_reached"},
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(str(result["result_path"])).name == COMPARE_LHS_SLOT_WRITER_PREDECESSOR_AUDIT_FILE_NAME
    assert payload["classification"] == "pre_slot_source_identified"
    assert payload["fixed_candidates"] == [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
        "78d540b49c59076f41414141414141",
    ]


def test_compare_aware_strategy_runs_lhs_producer_sidecar_before_search(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    post_handoff_payload = {
        "classification": "post_handoff_window_rejected",
        "breakpoint_probe_allowed": False,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "post_handoff_branch_outcome_audit": post_handoff_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_compare_lhs_producer_audit(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["post_handoff_classification"] = kwargs["post_handoff_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / COMPARE_LHS_PRODUCER_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "compare_lhs_producer_audit",
            "classification": "producer_window_rejected",
            "candidate_count": 3,
            "checked_windows": [],
            "relations": {
                "slot_to_compare_arg": "rejected",
                "eax_to_slot": "rejected",
                "esi_to_compare_arg": "rejected",
                "helper_return_to_lhs": "rejected",
            },
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "move earlier",
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(compare_aware_search, "_project_state_json", lambda name: {})
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(compare_aware_search, "run_compare_lhs_producer_audit", fake_run_compare_lhs_producer_audit)
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early lhs producer sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "compare_lhs_producer_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "compare_lhs_producer_audit"
    assert captured["post_handoff_classification"] == "post_handoff_window_rejected"
    assert Path(str(result.artifacts[0].output_path)).name == COMPARE_LHS_PRODUCER_AUDIT_FILE_NAME


def test_compare_aware_strategy_runs_upstream_writer_sidecar_after_lhs_rejection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    compare_lhs_payload = {
        "classification": "producer_window_rejected",
        "breakpoint_probe_allowed": False,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "compare_lhs_producer_audit": compare_lhs_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_compare_lhs_upstream_writer_audit(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["source_classification"] = kwargs["compare_lhs_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / COMPARE_LHS_UPSTREAM_WRITER_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "compare_lhs_upstream_writer_audit",
            "classification": "candidate_dependent_upstream_observed",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "checked_writers": [],
            "relations": {"upstream_to_compare_arg": "inconclusive"},
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "connect upstream writer",
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {"latest_compare_lhs_producer_audit": compare_lhs_payload} if name == "current_state.json" else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_lhs_upstream_writer_audit",
        fake_run_compare_lhs_upstream_writer_audit,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early upstream writer sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "compare_lhs_upstream_writer_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "compare_lhs_upstream_writer_audit"
    assert captured["source_classification"] == "producer_window_rejected"
    assert Path(str(result.artifacts[0].output_path)).name == COMPARE_LHS_UPSTREAM_WRITER_AUDIT_FILE_NAME


def test_compare_aware_strategy_runs_callsite_reanchor_sidecar_after_upstream_observation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    upstream_payload = {
        "classification": "candidate_dependent_upstream_observed",
        "breakpoint_probe_allowed": False,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "compare_lhs_upstream_writer_audit": upstream_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_callsite_reanchor_audit(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["source_classification"] = kwargs["upstream_writer_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / COMPARE_CALLSITE_REANCHOR_AND_LHS_PROVENANCE_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "compare_callsite_reanchor_and_lhs_provenance_audit",
            "classification": "frame_anchor_rejected",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {"lhs_side": "arg0", "flag_side": "arg1"},
            "frame_anchor": {"old_slot_ebp_minus_1170_valid": False},
            "provenance": {"evidence": []},
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "narrow real lhs provenance",
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {"latest_compare_lhs_upstream_writer_audit": upstream_payload}
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_callsite_reanchor_and_lhs_provenance_audit",
        fake_run_callsite_reanchor_audit,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early callsite reanchor sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "compare_callsite_reanchor_and_lhs_provenance_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "compare_callsite_reanchor_and_lhs_provenance_audit"
    assert captured["source_classification"] == "candidate_dependent_upstream_observed"
    assert Path(str(result.artifacts[0].output_path)).name == (
        COMPARE_CALLSITE_REANCHOR_AND_LHS_PROVENANCE_AUDIT_FILE_NAME
    )


def test_compare_aware_strategy_runs_real_lhs_sidecar_after_callsite_reanchor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    callsite_payload = {
        "classification": "callsite_reanchored_but_producer_unknown",
        "breakpoint_probe_allowed": False,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "compare_callsite_reanchor_and_lhs_provenance_audit": callsite_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_real_lhs_audit(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["source_classification"] = kwargs["callsite_reanchor_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / COMPARE_REAL_LHS_PROVENANCE_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "lhs_register_source_confirmed",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {"lhs_side": "arg0", "flag_side": "arg1"},
            "frame_anchor": {"old_slot_ebp_minus_1170_valid": False},
            "relations": {"esi_to_compare_arg0": "confirmed"},
            "provenance": {"evidence": []},
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "hook ESI source",
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {"latest_compare_callsite_reanchor_and_lhs_provenance_audit": callsite_payload}
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(compare_aware_search, "run_compare_real_lhs_provenance_audit", fake_run_real_lhs_audit)
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early real-lhs sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "compare_real_lhs_provenance_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "compare_real_lhs_provenance_audit"
    assert captured["source_classification"] == "callsite_reanchored_but_producer_unknown"
    assert Path(str(result.artifacts[0].output_path)).name == COMPARE_REAL_LHS_PROVENANCE_AUDIT_FILE_NAME


@pytest.mark.parametrize(
    "exception_classification",
    ["compare_reached_but_path_unresolved", "seh_unwind_to_compare_path"],
)
def test_compare_aware_strategy_runs_real_lhs_sidecar_after_exception_unwind(
    tmp_path: Path,
    monkeypatch,
    exception_classification: str,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    exception_payload = {
        "classification": exception_classification,
        "breakpoint_probe_allowed": False,
    }
    material_payload = {
        "artifact_kind": "material_hook_runtime_validation",
        "classification": "REJECTED",
        "candidate_count": 3,
        "runtime_backed_count": 0,
        "source_compare_esi_source_window_classification": "esi_source_identified",
        "breakpoint_probe_allowed": False,
    }
    prior_real_lhs_payload = {
        "artifact_kind": "compare_real_lhs_provenance_audit",
        "classification": "instrumentation_incomplete",
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "post_handoff_exception_unwind_audit": exception_payload,
                "material_hook_runtime_validation": material_payload,
                "compare_real_lhs_provenance_audit": prior_real_lhs_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_real_lhs_audit(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["source_classification"] = kwargs["post_handoff_exception_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / COMPARE_REAL_LHS_PROVENANCE_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "compare_real_lhs_provenance_audit",
            "classification": "compare_lhs_runtime_backed_writer_missing",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {"lhs_side": "arg0", "flag_side": "arg1"},
            "last_writer_summary": {"runtime_backed_count": 0},
            "last_writer_candidates": [],
            "breakpoint_probe_allowed": False,
            "next_bounded_action": "improve bounded write ring-buffer coverage before 0x258c",
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {
            "latest_post_handoff_exception_unwind_audit": exception_payload,
            "latest_material_hook_runtime_validation": material_payload,
            "latest_compare_real_lhs_provenance_audit": prior_real_lhs_payload,
        }
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(compare_aware_search, "run_compare_real_lhs_provenance_audit", fake_run_real_lhs_audit)
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_lhs_slot_writer_source_audit",
        lambda **kwargs: pytest.fail("slot writer source audit should not preempt exception-triggered real-lhs audit"),
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for exception-triggered real-lhs sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "compare_real_lhs_provenance_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "compare_real_lhs_provenance_audit"
    assert captured["source_classification"] == exception_classification
    assert Path(str(result.artifacts[0].output_path)).name == COMPARE_REAL_LHS_PROVENANCE_AUDIT_FILE_NAME


def test_compare_aware_strategy_runs_esi_source_window_sidecar_after_real_lhs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    real_lhs_payload = {
        "classification": "lhs_register_source_confirmed",
        "breakpoint_probe_allowed": False,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "compare_real_lhs_provenance_audit": real_lhs_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_esi_source_audit(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["source_classification"] = kwargs["real_lhs_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / COMPARE_ESI_SOURCE_WINDOW_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "compare_esi_source_window_audit",
            "classification": "esi_source_identified",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "actual_compare": {"lhs_side": "arg0", "flag_side": "arg1"},
            "relations": {"initial_reload_to_arg0": "confirmed"},
            "window_rows": [],
            "identified_producers": [],
            "breakpoint_probe_allowed": True,
            "next_bounded_action": "promote source",
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {"latest_compare_real_lhs_provenance_audit": real_lhs_payload}
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(compare_aware_search, "run_compare_esi_source_window_audit", fake_run_esi_source_audit)
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early ESI source sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "compare_esi_source_window_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "compare_esi_source_window_audit"
    assert captured["source_classification"] == "lhs_register_source_confirmed"
    assert Path(str(result.artifacts[0].output_path)).name == COMPARE_ESI_SOURCE_WINDOW_AUDIT_FILE_NAME


def test_compare_aware_strategy_runs_esi_material_hook_sidecar_before_search(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    esi_source_payload = {
        "artifact_kind": "compare_esi_source_window_audit",
        "classification": "esi_source_identified",
        "promotable_validations": [
            {
                "hook_name": "initial_lhs_reload",
                "module_offset": "0x2559",
                "candidate_dependent": True,
                "connects_to_compare_lhs": True,
            }
        ],
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "compare_esi_source_window_audit": esi_source_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_material_hook_runtime_validation(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["source_classification"] = kwargs["compare_esi_source_window_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / MATERIAL_HOOK_RUNTIME_VALIDATION_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "material_hook_runtime_validation",
            "classification": "BLOCKED",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "source_compare_esi_source_window_classification": "esi_source_identified",
            "validated_hooks": [],
            "blocked_hooks": [{"hook_name": "initial_lhs_reload", "module_offset": "0x2559"}],
            "breakpoint_probe_allowed": False,
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {"latest_compare_esi_source_window_audit": esi_source_payload}
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_material_hook_runtime_validation",
        fake_run_material_hook_runtime_validation,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early ESI material-hook sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "material_hook_runtime_validation"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "material_hook_runtime_validation"
    assert captured["source_classification"] == "esi_source_identified"
    assert Path(str(result.artifacts[0].output_path)).name == MATERIAL_HOOK_RUNTIME_VALIDATION_FILE_NAME


def test_compare_aware_strategy_runs_lhs_slot_writer_source_sidecar_before_search(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    material_payload = {
        "artifact_kind": "material_hook_runtime_validation",
        "classification": "REJECTED",
        "candidate_count": 3,
        "runtime_backed_count": 0,
        "source_compare_esi_source_window_classification": "esi_source_identified",
        "validated_hooks": [],
        "blocked_hooks": [{"hook_name": "initial_lhs_reload", "module_offset": "0x2559"}],
        "breakpoint_probe_allowed": False,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "material_hook_runtime_validation": material_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_slot_writer_source_audit(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["source_classification"] = kwargs["material_hook_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / COMPARE_LHS_SLOT_WRITER_SOURCE_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "compare_lhs_slot_writer_source_audit",
            "classification": "slot_writer_confirmed",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "slot_writer": {"hook_name": "slot_writer", "module_offset": "0x253a"},
            "breakpoint_probe_allowed": False,
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {"latest_material_hook_runtime_validation": material_payload}
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_lhs_slot_writer_source_audit",
        fake_run_slot_writer_source_audit,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early slot writer/source sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "compare_lhs_slot_writer_source_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "compare_lhs_slot_writer_source_audit"
    assert captured["source_classification"] == "REJECTED"
    assert Path(str(result.artifacts[0].output_path)).name == COMPARE_LHS_SLOT_WRITER_SOURCE_AUDIT_FILE_NAME


def test_compare_aware_strategy_runs_lhs_slot_writer_predecessor_sidecar_before_search(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    slot_writer_payload = {
        "artifact_kind": "compare_lhs_slot_writer_source_audit",
        "classification": "writer_hook_not_reached",
        "candidate_count": 3,
        "runtime_backed_count": 3,
        "breakpoint_probe_allowed": False,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "compare_lhs_slot_writer_source_audit": slot_writer_payload,
            }.get(kind, {}),
            "",
        )

    def fake_run_predecessor_audit(**kwargs):
        captured["artifacts_dir"] = Path(kwargs["artifacts_dir"]).name
        captured["source_classification"] = kwargs["slot_writer_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / COMPARE_LHS_SLOT_WRITER_PREDECESSOR_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "compare_lhs_slot_writer_predecessor_audit",
            "classification": "handoff_call_does_not_return_to_linear_path",
            "candidate_count": 3,
            "runtime_backed_count": 3,
            "breakpoint_probe_allowed": False,
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {
            "result_path": str(result_path),
            "payload": payload,
            "validations": [],
            "promotable_validations": [],
        }

    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {"latest_compare_lhs_slot_writer_source_audit": slot_writer_payload}
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_lhs_slot_writer_predecessor_audit",
        fake_run_predecessor_audit,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early predecessor sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "compare_lhs_slot_writer_predecessor_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["artifacts_dir"] == "compare_lhs_slot_writer_predecessor_audit"
    assert captured["source_classification"] == "writer_hook_not_reached"
    assert Path(str(result.artifacts[0].output_path)).name == COMPARE_LHS_SLOT_WRITER_PREDECESSOR_AUDIT_FILE_NAME


def test_compare_aware_strategy_runs_post_handoff_sidecar_before_search(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    pre_compare_payload = {
        "classification": "next_handoff_target_identified",
        "hook_miss_classification": "branch_exits_before_output_calls",
        "instruction_confirmation_table": [
            {
                "hook_name": "producer_return_site",
                "module_offset": "0x233d",
                "observed_count": 3,
                "candidate_dependent_eax": True,
                "expected_eax_match_count": 3,
                "hookable": True,
            },
            {
                "hook_name": "producer_pre_output_call",
                "module_offset": "0x234e",
                "observed_count": 0,
                "candidate_dependent_eax": False,
                "expected_eax_match_count": 0,
                "hookable": False,
            },
        ],
    }
    material_payload = {
        "classification": "REJECTED",
        "validated_hooks": [],
        "blocked_hooks": [{"hook_name": "producer_return_site", "module_offset": "0x233d"}],
    }

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "compare_pre_compare_handoff_target_probe": pre_compare_payload,
                "function_semantic_audit": {"classification": "material_hook_ready"},
                "material_hook_runtime_validation": material_payload,
            }.get(kind, {}),
            "",
        )

    monkeypatch.setattr(compare_aware_search, "_project_state_json", lambda name: {})
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for early post-handoff sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "post_handoff_branch_outcome_audit"
    assert result.metadata["early_sidecar"] is True
    assert Path(str(result.artifacts[0].output_path)).name == POST_HANDOFF_BRANCH_OUTCOME_AUDIT_FILE_NAME


def test_compare_aware_strategy_runs_post_handoff_sidecar_from_predecessor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    predecessor_payload = {
        "artifact_kind": "compare_lhs_slot_writer_predecessor_audit",
        "classification": "handoff_call_does_not_return_to_linear_path",
        "runtime_backed_count": 3,
        "candidate_count": 3,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "compare_lhs_slot_writer_predecessor_audit": predecessor_payload,
                "compare_pre_compare_handoff_target_probe": {},
                "function_semantic_audit": {},
                "material_hook_runtime_validation": {},
            }.get(kind, {}),
            "",
        )

    def fake_run_post_handoff(**kwargs):
        captured["target"] = Path(kwargs["target"]).name
        captured["predecessor_classification"] = kwargs["predecessor_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / POST_HANDOFF_BRANCH_OUTCOME_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "post_handoff_branch_outcome_audit",
            "classification": "handoff_tailcalls_or_jumps",
            "runtime_backed_count": 3,
            "breakpoint_probe_allowed": False,
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {"result_path": str(result_path), "payload": payload, "validations": []}

    monkeypatch.setattr(compare_aware_search, "_project_state_json", lambda name: {})
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(compare_aware_search, "run_post_handoff_branch_outcome_audit", fake_run_post_handoff)
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for predecessor post-handoff sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "post_handoff_branch_outcome_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["target"] == "samplereverse.exe"
    assert captured["predecessor_classification"] == "handoff_call_does_not_return_to_linear_path"
    assert Path(str(result.artifacts[0].output_path)).name == POST_HANDOFF_BRANCH_OUTCOME_AUDIT_FILE_NAME


def test_compare_aware_strategy_runs_exception_unwind_sidecar_before_search(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    post_handoff_payload = {
        "artifact_kind": "post_handoff_branch_outcome_audit",
        "classification": "handoff_exception_or_unwind",
        "runtime_backed_count": 3,
        "candidate_count": 3,
    }
    captured: dict[str, object] = {}

    def fake_indexed_artifact_payload(kind):
        return (
            {
                "post_handoff_branch_outcome_audit": post_handoff_payload,
                "compare_pre_compare_handoff_target_probe": {},
                "function_semantic_audit": {},
                "material_hook_runtime_validation": {},
            }.get(kind, {}),
            "",
        )

    def fake_run_exception_unwind(**kwargs):
        captured["source_classification"] = kwargs["post_handoff_payload"]["classification"]
        result_path = Path(kwargs["artifacts_dir"]) / POST_HANDOFF_EXCEPTION_UNWIND_AUDIT_FILE_NAME
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_kind": "post_handoff_exception_unwind_audit",
            "classification": "compare_reached_but_path_unresolved",
            "runtime_backed_count": 3,
            "candidate_count": 3,
            "breakpoint_probe_allowed": False,
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return {"result_path": str(result_path), "payload": payload, "validations": []}

    monkeypatch.setattr(compare_aware_search, "_project_state_json", lambda name: {})
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", fake_indexed_artifact_payload)
    monkeypatch.setattr(
        compare_aware_search,
        "_indexed_or_latest_report_artifact_payload",
        fake_indexed_artifact_payload,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_post_handoff_exception_unwind_audit",
        fake_run_exception_unwind,
    )
    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: pytest.fail("bridge search should not run for exception/unwind sidecar"),
    )

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
        project_state_sidecar_enabled=True,
    )

    assert result.metadata["completed_stage"] == "post_handoff_exception_unwind_audit"
    assert result.metadata["early_sidecar"] is True
    assert captured["source_classification"] == "handoff_exception_or_unwind"
    assert Path(str(result.artifacts[0].output_path)).name == POST_HANDOFF_EXCEPTION_UNWIND_AUDIT_FILE_NAME


def test_compare_hook_path_reachability_payload_classifies_path_gaps() -> None:
    base_result = {
        "candidate_hex": "78d540b49c59077041414141414141",
        "hook_install_status": "installed",
        "ui_trigger_status": "button_triggered",
        "python_message_count_total": 12,
        "hook_address_validation": [
            {
                "name": "static_compare_callsite",
                "install_status": "installed",
                "address_validation": "resolved",
            }
        ],
    }

    no_path = build_compare_hook_path_reachability_audit_payload(candidate_results=[base_result])
    assert no_path["artifact_kind"] == "compare_hook_path_reachability_audit"
    assert no_path["classification"] == "ui_button_triggered_but_decrypt_handler_not_entered"
    assert no_path["breakpoint_probe_allowed"] is False

    handoff_call = {
        **base_result,
        "hook_observations": [{"hook_name": "predecessor_handoff_call", "event": "enter"}],
    }
    payload = build_compare_hook_path_reachability_audit_payload(candidate_results=[handoff_call])
    assert payload["classification"] == "handoff_helper_not_entered_after_ui_trigger"

    helper_entry = {
        **base_result,
        "hook_observations": [{"hook_name": "handoff_helper_entry", "event": "enter"}],
    }
    payload = build_compare_hook_path_reachability_audit_payload(candidate_results=[helper_entry])
    assert payload["classification"] == "handoff_helper_entered_but_return_path_skips_compare_window"

    compare_window = {
        **base_result,
        "hook_observations": [{"hook_name": "static_compare_callsite", "event": "enter"}],
    }
    payload = build_compare_hook_path_reachability_audit_payload(candidate_results=[compare_window])
    assert payload["classification"] == "compare_window_reached_after_ui_trigger"


def test_run_compare_hook_path_reachability_audit_records_fixed_candidates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ" + b"\0" * 4096)

    def fake_run(command, timeout):  # noqa: ANN001
        command = list(command)
        out_path = Path(command[command.index("--out") + 1])
        candidate_hex = command[command.index("--probe-hex") + 1]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(
                {
                    "artifact_kind": "compare_hook_path_reachability_audit",
                    "success": True,
                    "candidate_hex": candidate_hex,
                    "hook_observations": [],
                    "hook_install_status": "installed",
                    "hook_count": 7,
                    "requested_hook_count": 7,
                    "hooks_installed_stage_seen": True,
                    "script_load_status": "loaded",
                    "python_message_callback_registered_before_load": True,
                    "python_message_count_total": 12,
                    "ui_trigger_status": "button_triggered",
                    "observation_count": 0,
                    "hook_address_validation": [
                        {
                            "name": "static_compare_callsite",
                            "install_status": "installed",
                            "address_validation": "resolved",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(compare_aware_search, "_run_material_hook_runtime_command", fake_run)
    result = run_compare_hook_path_reachability_audit(
        target=target,
        artifacts_dir=tmp_path / "artifacts",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.1,
        run_name="unit_path_reachability",
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == COMPARE_HOOK_PATH_REACHABILITY_AUDIT_FILE_NAME
    assert payload["candidate_count"] == 3
    assert payload["fixed_candidates"] == [
        "78d540b49c59077041414141414141",
        "5a3e7f46ddd474d041414141414141",
        "78d540b49c59076f41414141414141",
    ]
    assert payload["classification"] == "ui_button_triggered_but_decrypt_handler_not_entered"
    assert payload["breakpoint_probe_allowed"] is False


def test_function_semantic_audit_blocks_without_candidate_dependent_material_hook(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_material_confirmation_subprocess_run)
    material_result = run_compare_producer_material_confirmation_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_producer_material_confirmation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        producer_trace_payload=_upstream_material_producer_trace_payload(),
        log=lambda _: None,
    )

    result = run_function_semantic_audit(
        artifacts_dir=tmp_path / "function_semantic_audit",
        material_confirmation_payload=material_result["payload"],
        log=lambda _: None,
    )

    payload = result["payload"]
    assert Path(result["result_path"]).name == FUNCTION_SEMANTIC_AUDIT_FILE_NAME
    assert payload["artifact_kind"] == "function_semantic_audit"
    assert payload["classification"] == "runtime_instrumentation_required"
    assert payload["function_count"] == 4
    assert payload["material_hook_candidate_count"] == 0
    assert payload["breakpoint_probe_allowed"] is False
    assert payload["functions"][1]["function"] == "0x401b50"
    assert payload["functions"][1]["material_hook_candidate_status"] == "blocked_missing_candidate_dependent_output"


def test_function_semantic_audit_allows_breakpoint_only_after_semantic_gate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    monkeypatch.setattr(compare_aware_search.subprocess, "run", _fake_material_confirmation_ready_subprocess_run)

    result = run_compare_producer_material_confirmation_probe(
        target=target,
        artifacts_dir=tmp_path / "compare_producer_material_confirmation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        producer_trace_payload=_upstream_material_producer_trace_payload(),
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "base64_material_captured"
    assert payload["breakpoint_probe_allowed"] is True
    assert compare_aware_search._producer_material_confirmation_allows_breakpoint(payload) is True
    points = compare_aware_search._breakpoint_static_points_from_material_confirmation_payload(payload)
    assert points["base64_output"][0]["module_offset"] == 0x234E

    audit = build_function_semantic_audit_payload(material_confirmation_payload=payload)
    assert audit["breakpoint_probe_allowed"] is True
    assert audit["material_hook_candidate_count"] == 1


def test_upstream_producer_trace_triggers_material_confirmation_not_pre_rc4(monkeypatch) -> None:
    payload = _upstream_material_producer_trace_payload()
    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {
            "latest_compare_producer_trace_probe": payload,
            "latest_compare_producer_material_confirmation": {},
            "latest_pre_rc4_material_probe": {},
        }
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", lambda kind: ({}, None))

    assert compare_aware_search._prior_compare_producer_trace_needs_material_confirmation() is True
    assert compare_aware_search._prior_compare_producer_trace_needs_pre_rc4_fallback() is False


def test_wrong_helper_assumption_triggers_pre_compare_handoff_target_probe(monkeypatch) -> None:
    monkeypatch.setattr(
        compare_aware_search,
        "_project_state_json",
        lambda name: {
            "latest_compare_pre_compare_handoff_target_probe": {},
            "latest_compare_producer_material_confirmation": {},
            "latest_compare_handoff_return_site_probe": {
                "classification": "wrong_helper_assumption",
                "next_bounded_action": "move to the next bounded pre-compare handoff target",
            },
            "latest_function_semantic_audit": {},
        }
        if name == "current_state.json"
        else {},
    )
    monkeypatch.setattr(compare_aware_search, "_indexed_artifact_payload", lambda kind: ({}, None))

    assert compare_aware_search._prior_needs_pre_compare_handoff_target_probe() is True


def test_h1_h3_boundary_validation_runtime_validates_fixed_contrast_set(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    captured: dict[str, object] = {}

    def fake_validate_compare_aware_results(**kwargs):
        payload = json.loads(Path(kwargs["result_path"]).read_text(encoding="utf-8"))
        candidates = list(payload["validation_candidates"])
        captured["validate_top"] = kwargs["validate_top"]
        captured["candidate_count"] = len(candidates)
        captured["output_file_name"] = kwargs["output_file_name"]
        captured["artifacts_dir_name"] = Path(kwargs["artifacts_dir"]).name
        validations = []
        for entry in candidates:
            candidate_hex = str(entry["candidate_hex"])
            validations.append(
                {
                    **entry,
                    "candidate_hex": candidate_hex,
                    "cand8_hex": candidate_hex[:16],
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "offline_ci_distance5": int(entry.get("ci_distance5", 1 << 30) or (1 << 30)),
                    "offline_raw_distance10": int(entry.get("raw_distance10", 1 << 30) or (1 << 30)),
                }
            )
        return tmp_path / "h1_h3_validation.json", validations

    monkeypatch.setattr(
        compare_aware_search,
        "validate_compare_aware_results",
        fake_validate_compare_aware_results,
    )

    result = run_h1_h3_boundary_validation(
        target=target,
        artifacts_dir=tmp_path / "h1_h3_boundary_validation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    candidates = payload["validation_candidates"]
    assert Path(result["result_path"]).name == H1_H3_BOUNDARY_VALIDATION_FILE_NAME
    assert captured["validate_top"] == H1_H3_BOUNDARY_CANDIDATE_LIMIT
    assert captured["candidate_count"] == H1_H3_BOUNDARY_CANDIDATE_LIMIT
    assert captured["output_file_name"] == H1_H3_BOUNDARY_VALIDATION_FILE_NAME
    assert captured["artifacts_dir_name"] == "validation"
    assert payload["candidate_count"] == H1_H3_BOUNDARY_CANDIDATE_LIMIT
    assert candidates[0]["candidate_hex"] == "78d540b49c59077041414141414141"
    assert {item["candidate_hex"] for item in candidates} == {
        "78d540b49c59077041414141414141",
        "78d540b49c59076f41414141414141",
        "78d540b49c59077141414141414141",
        "78d540b49c5907b041414141414141",
        "78d540b49c5907d041414141414141",
        "78d540b49c59077040414141414141",
        "78d540b49c59077042414141414141",
        "78d540b49c59076f42414141414141",
    }
    first = candidates[0]
    assert first["trace_prefix7"]["base64_boundary"]["prefix_last_chunk_raw_remainder"] == 1
    assert first["trace_prefix8"]["base64_boundary"]["prefix_last_chunk_raw_remainder"] == 2
    assert first["trace_prefix9"]["base64_boundary"]["prefix_last_chunk_raw_remainder"] == 0
    assert payload["improved_over_exact2"] is False
    assert payload["classification"] == "h1_h3_boundary_contrast_exhausted_no_gain"
    assert result["promotable_validations"] == []


def test_h1_h3_boundary_validation_promotes_runtime_improvement_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")

    def fake_validate_compare_aware_results(**kwargs):
        payload = json.loads(Path(kwargs["result_path"]).read_text(encoding="utf-8"))
        validations = []
        for entry in payload["validation_candidates"]:
            candidate_hex = str(entry["candidate_hex"])
            improved = candidate_hex == "78d540b49c59077042414141414141"
            validations.append(
                {
                    **entry,
                    "candidate_hex": candidate_hex,
                    "cand8_hex": candidate_hex[:16],
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 3 if improved else 2,
                    "runtime_ci_distance5": 200 if improved else 246,
                    "offline_ci_distance5": int(entry.get("ci_distance5", 1 << 30) or (1 << 30)),
                    "offline_raw_distance10": int(entry.get("raw_distance10", 1 << 30) or (1 << 30)),
                }
            )
        return tmp_path / "h1_h3_validation.json", validations

    monkeypatch.setattr(
        compare_aware_search,
        "validate_compare_aware_results",
        fake_validate_compare_aware_results,
    )

    result = run_h1_h3_boundary_validation(
        target=target,
        artifacts_dir=tmp_path / "h1_h3_boundary_validation",
        transform_model=SamplereverseTransformModel(),
        per_probe_timeout=0.5,
        log=lambda _: None,
    )

    payload = result["payload"]
    assert payload["classification"] == "h1_h3_boundary_contrast_improved"
    assert payload["improved_over_exact2"] is True
    assert [item["candidate_hex"] for item in result["promotable_validations"]] == [
        "78d540b49c59077042414141414141"
    ]


def test_compare_aware_strategy_runs_second_frontier_guided_round_on_improved_frontier(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    guided_calls: list[str] = []
    refine_calls: list[str] = []

    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: {
            "pairscan_path": str(tmp_path / "pairscan_summary.json"),
            "bridge_result_path": str(tmp_path / BRIDGE_RESULT_FILE_NAME),
            "bridge_validation_path": str(tmp_path / "bridge_validation.json"),
            "bridge_entries": [],
            "bridge_validations": [],
            "hot_positions": [0, 1, 2],
            "hot_nibbles": [0, 1, 2, 3, 4],
        },
    )

    def fake_guided_pool(**kwargs):
        base_anchor = kwargs["base_anchor"]
        guided_calls.append(base_anchor)
        entry = {
            "stage": "guided_pool",
            "base_anchor": base_anchor,
            "positions_or_nibbles": [0, 1, 2, 3, 4],
            "candidate_hex": f"{base_anchor}41414141414141",
            "cand8_hex": base_anchor,
            "raw_prefix_hex": "46006c004464830d311c",
            "raw_prefix_hex_64": "46006c004464830d311c",
            "ci_exact_wchars": 2 if base_anchor == "78d540b49c590770" else 0,
            "ci_distance5": 246 if base_anchor == "78d540b49c590770" else 220,
            "raw_distance10": 304 if base_anchor == "78d540b49c590770" else 266,
            "source_anchor": kwargs.get("source_anchor", base_anchor),
            "frontier_role": kwargs.get("frontier_role", ""),
            "anchor_mode": "exact2" if base_anchor == "78d540b49c590770" else "frontier",
            "anchor_lineage": kwargs.get("anchor_lineage", ""),
        }
        return {
            "guided_pool_result_path": str(tmp_path / f"{base_anchor}_guided_pool_result.json"),
            "guided_pool_validation_path": str(tmp_path / f"{base_anchor}_guided_pool_validation.json"),
            "guided_entries": [entry],
            "guided_validations": [],
            "positions": [0, 1, 2, 3, 4],
            "value_pools": {"0": [0x41]},
            "beam_limit": 16,
            "anchor_mode": entry["anchor_mode"],
            "source_anchor": entry["source_anchor"],
            "frontier_role": entry["frontier_role"],
            "anchor_lineage": entry["anchor_lineage"],
            "pair_frontier_pool": [],
            "triad_frontier_pool": [],
            "pair_stage_stats": {},
            "stage_stats": [],
        }

    def fake_run_compare_aware_refine(
        *,
        artifacts_dir: Path,
        search_budget: int,
        seed: int,
        anchors: list[str],
        snapshot_interval: int,
        log,
    ) -> Path:
        _ = search_budget, seed, snapshot_interval, log, anchors
        refine_calls.append(artifacts_dir.name)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / RESULT_FILE_NAME
        candidate_hex = (
            "78d540b49c59077041414141414141"
            if artifacts_dir.name == "artifacts"
            else "f649b64b5e97dbd041414141414141"
            if artifacts_dir.name == "frontier_refine_1"
            else "a47a0a74bd35355041414141414141"
        )
        out.write_text(
            json.dumps(
                {
                    "best": {
                        "candidate_hex": candidate_hex,
                        "cand8_hex": candidate_hex[:16],
                        "raw_prefix_hex": "46006c004464830d311c",
                        "ci_exact_wchars": 2 if candidate_hex.startswith("78d540") else 0,
                        "ci_distance5": 246 if candidate_hex.startswith("78d540") else 218 if candidate_hex.startswith("f649") else 208,
                        "raw_distance10": 304 if candidate_hex.startswith("78d540") else 266,
                    },
                    "top_entries": [
                        {
                            "candidate_hex": candidate_hex,
                            "cand8_hex": candidate_hex[:16],
                            "raw_prefix_hex": "46006c004464830d311c",
                            "ci_exact_wchars": 2 if candidate_hex.startswith("78d540") else 0,
                            "ci_distance5": 246 if candidate_hex.startswith("78d540") else 218 if candidate_hex.startswith("f649") else 208,
                            "raw_distance10": 304 if candidate_hex.startswith("78d540") else 266,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return out

    def fake_validate_compare_aware_results(
        *,
        target: Path,
        artifacts_dir: Path,
        result_path: Path,
        transform_model: SamplereverseTransformModel,
        validate_top: int,
        per_probe_timeout: float,
        log,
        output_file_name: str = VALIDATION_FILE_NAME,
        compare_output_prefix: str = "samplereverse_compare_aware_compare",
    ) -> tuple[Path, list[dict[str, object]]]:
        _ = target, result_path, transform_model, validate_top, per_probe_timeout, log, compare_output_prefix
        out = artifacts_dir / output_file_name
        out.parent.mkdir(parents=True, exist_ok=True)
        if artifacts_dir == tmp_path / "artifacts":
            validations = [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "frontier_role": "exact2_seed",
                },
                {
                    "candidate_hex": "f649b64b5e97dbd041414141414141",
                    "cand8_hex": "f649b64b5e97dbd0",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 0,
                    "runtime_ci_distance5": 218,
                    "frontier_role": "exact0_frontier",
                },
            ]
        elif artifacts_dir == tmp_path / "artifacts" / "frontier_refine_1":
            validations = [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "frontier_role": "exact2_seed",
                },
                {
                    "candidate_hex": "a47a0a74bd35355041414141414141",
                    "cand8_hex": "a47a0a74bd353550",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 0,
                    "runtime_ci_distance5": 208,
                    "frontier_role": "exact0_frontier",
                    "source_anchor": "f649b64b5e97dbd0",
                    "anchor_lineage": "exact0_frontier(f649b64b5e97dbd0) -> refine(frontier)",
                },
            ]
        else:
            validations = [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "frontier_role": "exact2_seed",
                },
                {
                    "candidate_hex": "a47a0a74bd35355041414141414141",
                    "cand8_hex": "a47a0a74bd353550",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 0,
                    "runtime_ci_distance5": 208,
                    "frontier_role": "exact0_frontier",
                    "source_anchor": "a47a0a74bd353550",
                    "anchor_lineage": "exact0_frontier(a47a0a74bd353550) -> refine(frontier)",
                },
            ]
        out.write_text(json.dumps({"validations": validations}, ensure_ascii=False), encoding="utf-8")
        return out, validations

    monkeypatch.setattr(compare_aware_search, "run_compare_aware_guided_pool", fake_guided_pool)
    monkeypatch.setattr(compare_aware_search, "run_compare_aware_refine", fake_run_compare_aware_refine)
    monkeypatch.setattr(compare_aware_search, "validate_compare_aware_results", fake_validate_compare_aware_results)
    smt_calls: list[dict[str, object]] = []

    def fake_run_compare_aware_smt(**kwargs):
        smt_calls.append(kwargs)
        result_path = tmp_path / f"smt_result_{len(smt_calls)}.json"
        return {
            "result_path": str(result_path),
            "validation_path": "",
            "entry": None,
            "validations": [],
            "payload": {"summary": "smt attempted"},
        }

    monkeypatch.setattr(compare_aware_search, "run_compare_aware_smt", fake_run_compare_aware_smt)

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
    )

    assert guided_calls == [
        "78d540b49c590770",
        "f649b64b5e97dbd0",
        "a47a0a74bd353550",
    ]
    assert refine_calls == ["artifacts", "frontier_refine_1", "frontier_refine_2"]
    assert len(result.metadata["frontier_iterations"]) == 2
    assert result.metadata["frontier_converged_reason"] == "iteration_limit"


def test_compare_aware_strategy_runs_second_frontier_guided_round_on_second_hop_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "samplereverse.exe"
    target.write_bytes(b"MZ")
    guided_calls: list[str] = []
    refine_calls: list[str] = []

    monkeypatch.setattr(
        compare_aware_search,
        "run_compare_aware_bridge",
        lambda **kwargs: {
            "pairscan_path": str(tmp_path / "pairscan_summary.json"),
            "bridge_result_path": str(tmp_path / BRIDGE_RESULT_FILE_NAME),
            "bridge_validation_path": str(tmp_path / "bridge_validation.json"),
            "bridge_entries": [],
            "bridge_validations": [],
            "hot_positions": [0, 1, 2],
            "hot_nibbles": [0, 1, 2, 3, 4],
        },
    )

    def fake_guided_pool(**kwargs):
        base_anchor = kwargs["base_anchor"]
        guided_calls.append(base_anchor)
        entry = {
            "stage": "guided_pool",
            "base_anchor": base_anchor,
            "positions_or_nibbles": [1, 2, 3],
            "candidate_hex": f"{base_anchor}41414141414141",
            "cand8_hex": base_anchor,
            "raw_prefix_hex": "460061357f0b8c688502",
            "raw_prefix_hex_64": "460061357f0b8c688502",
            "ci_exact_wchars": 1 if base_anchor == "5a3e7f46ddd474d0" else 0,
            "ci_distance5": 258 if base_anchor == "5a3e7f46ddd474d0" else 740,
            "raw_distance10": 290 if base_anchor == "5a3e7f46ddd474d0" else 772,
            "source_anchor": kwargs.get("source_anchor", base_anchor),
            "frontier_role": kwargs.get("frontier_role", ""),
            "anchor_mode": "frontier",
            "anchor_lineage": kwargs.get("anchor_lineage", ""),
        }
        guided_entries = [entry]
        if base_anchor == "5a3e7f46ddd474d0":
            guided_entries.append(
                {
                    "stage": "guided_pool",
                    "base_anchor": base_anchor,
                    "positions_or_nibbles": [1, 2, 3],
                    "candidate_hex": "5a3f7f46ddd474d041414141414141",
                    "cand8_hex": "5a3f7f46ddd474d0",
                    "raw_prefix_hex": "74934b156ba69ef3370f",
                    "raw_prefix_hex_64": "74934b156ba69ef3370f",
                    "ci_exact_wchars": 0,
                    "ci_distance5": 740,
                    "raw_distance10": 772,
                    "source_anchor": kwargs.get("source_anchor", base_anchor),
                    "frontier_role": "projected_preserve_handoff",
                    "anchor_mode": "frontier",
                    "anchor_lineage": "exact2_seed(78d540b49c590770) -> guided(frontier)",
                    "pair_candidate_origin": "exact1_projected_preserve_lane",
                    "pair_projected_boundary_role": "projected_winner_with_base",
                    "pair_projected_winner_gate_status": "projected_winner_promoted_to_near_local",
                }
            )
        return {
            "guided_pool_result_path": str(tmp_path / f"{base_anchor}_guided_pool_result.json"),
            "guided_pool_validation_path": str(tmp_path / f"{base_anchor}_guided_pool_validation.json"),
            "guided_entries": guided_entries,
            "guided_validations": [],
            "positions": [1, 2, 3],
            "value_pools": {"1": [0x3E, 0x3F]},
            "beam_limit": 16,
            "anchor_mode": entry["anchor_mode"],
            "source_anchor": entry["source_anchor"],
            "frontier_role": entry["frontier_role"],
            "anchor_lineage": entry["anchor_lineage"],
            "pair_frontier_pool": [],
            "triad_frontier_pool": [],
            "pair_stage_stats": {},
            "stage_stats": [],
        }

    def fake_run_compare_aware_refine(
        *,
        artifacts_dir: Path,
        search_budget: int,
        seed: int,
        anchors: list[str],
        snapshot_interval: int,
        log,
    ) -> Path:
        _ = search_budget, seed, snapshot_interval, log, anchors
        refine_calls.append(artifacts_dir.name)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / RESULT_FILE_NAME
        candidate_hex = (
            "78d540b49c59077041414141414141"
            if artifacts_dir.name == "artifacts"
            else "5a3e7f46ddd474d041414141414141"
            if artifacts_dir.name == "frontier_refine_1"
            else "5a3f7f46ddd474d041414141414141"
        )
        out.write_text(
            json.dumps(
                {
                    "best": {
                        "candidate_hex": candidate_hex,
                        "cand8_hex": candidate_hex[:16],
                        "raw_prefix_hex": "460061357f0b8c688502",
                        "ci_exact_wchars": 2 if candidate_hex.startswith("78d540") else 1 if candidate_hex.startswith("5a3e") else 0,
                        "ci_distance5": 246 if candidate_hex.startswith("78d540") else 258 if candidate_hex.startswith("5a3e") else 740,
                        "raw_distance10": 304 if candidate_hex.startswith("78d540") else 290 if candidate_hex.startswith("5a3e") else 772,
                    },
                    "top_entries": [
                        {
                            "candidate_hex": candidate_hex,
                            "cand8_hex": candidate_hex[:16],
                            "raw_prefix_hex": "460061357f0b8c688502",
                            "ci_exact_wchars": 2 if candidate_hex.startswith("78d540") else 1 if candidate_hex.startswith("5a3e") else 0,
                            "ci_distance5": 246 if candidate_hex.startswith("78d540") else 258 if candidate_hex.startswith("5a3e") else 740,
                            "raw_distance10": 304 if candidate_hex.startswith("78d540") else 290 if candidate_hex.startswith("5a3e") else 772,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return out

    def fake_validate_compare_aware_results(
        *,
        target: Path,
        artifacts_dir: Path,
        result_path: Path,
        transform_model: SamplereverseTransformModel,
        validate_top: int,
        per_probe_timeout: float,
        log,
        output_file_name: str = VALIDATION_FILE_NAME,
        compare_output_prefix: str = "samplereverse_compare_aware_compare",
    ) -> tuple[Path, list[dict[str, object]]]:
        _ = target, result_path, transform_model, validate_top, per_probe_timeout, log, compare_output_prefix
        out = artifacts_dir / output_file_name
        out.parent.mkdir(parents=True, exist_ok=True)
        if artifacts_dir == tmp_path / "artifacts":
            validations = [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "frontier_role": "exact2_seed",
                },
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 1,
                    "runtime_ci_distance5": 258,
                    "frontier_role": "exact1_frontier",
                    "source_anchor": "78d540b49c590770",
                    "anchor_lineage": "exact2_seed(78d540b49c590770) -> guided(frontier)",
                },
            ]
        elif artifacts_dir == tmp_path / "artifacts" / "frontier_refine_1":
            validations = [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "frontier_role": "exact2_seed",
                },
                {
                    "candidate_hex": "5a3e7f46ddd474d041414141414141",
                    "cand8_hex": "5a3e7f46ddd474d0",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 1,
                    "runtime_ci_distance5": 258,
                    "frontier_role": "exact1_frontier",
                    "source_anchor": "78d540b49c590770",
                },
                {
                    "candidate_hex": "5a3f7f46ddd474d041414141414141",
                    "cand8_hex": "5a3f7f46ddd474d0",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 0,
                    "runtime_ci_distance5": 740,
                    "frontier_role": "projected_preserve_handoff",
                    "source_anchor": "78d540b49c590770",
                },
            ]
        else:
            validations = [
                {
                    "candidate_hex": "78d540b49c59077041414141414141",
                    "cand8_hex": "78d540b49c590770",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 2,
                    "runtime_ci_distance5": 246,
                    "frontier_role": "exact2_seed",
                },
                {
                    "candidate_hex": "5a3f7f46ddd474d041414141414141",
                    "cand8_hex": "5a3f7f46ddd474d0",
                    "compare_semantics_agree": True,
                    "runtime_ci_exact_wchars": 0,
                    "runtime_ci_distance5": 740,
                    "frontier_role": PROJECTED_PRESERVE_SECOND_HOP_ROLE,
                    "source_anchor": "78d540b49c590770",
                },
            ]
        out.write_text(json.dumps({"validations": validations}, ensure_ascii=False), encoding="utf-8")
        return out, validations

    monkeypatch.setattr(compare_aware_search, "run_compare_aware_guided_pool", fake_guided_pool)
    monkeypatch.setattr(compare_aware_search, "run_compare_aware_refine", fake_run_compare_aware_refine)
    monkeypatch.setattr(compare_aware_search, "validate_compare_aware_results", fake_validate_compare_aware_results)
    smt_calls: list[dict[str, object]] = []

    def fake_run_compare_aware_smt(**kwargs):
        smt_calls.append(kwargs)
        result_path = tmp_path / f"smt_second_hop_result_{len(smt_calls)}.json"
        return {
            "result_path": str(result_path),
            "validation_path": "",
            "entry": None,
            "validations": [],
            "payload": {"summary": "smt attempted"},
        }

    monkeypatch.setattr(compare_aware_search, "run_compare_aware_smt", fake_run_compare_aware_smt)

    result = CompareAwareSearchStrategy().run(
        file_path=target,
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        transform_model=SamplereverseTransformModel(),
    )

    assert guided_calls == [
        "78d540b49c590770",
        "5a3e7f46ddd474d0",
        "5a3f7f46ddd474d0",
    ]
    assert refine_calls == ["artifacts", "frontier_refine_1", "frontier_refine_2"]
    assert len(result.metadata["frontier_iterations"]) == 2
    assert result.metadata["frontier_iterations"][0]["used_second_hop_frontier_candidates"] is True
    assert result.metadata["frontier_iterations"][0]["frontier_converged_reason"] == "continue"
    assert result.metadata["frontier_guided_runs"][1]["frontier_role"] == PROJECTED_PRESERVE_SECOND_HOP_ROLE
    assert result.metadata["frontier_guided_runs"][1]["anchor"] == "5a3f7f46ddd474d0"
    assert [Path(call["artifacts_dir"]).name for call in smt_calls] == ["smt", "smt_exact2_basin"]
    assert smt_calls[1]["base_entry"]["cand8_hex"] == "78d540b49c590770"
    assert set(smt_calls[1]["variable_byte_positions_override"]) == {0, 1, 2, 3, 4}
    assert smt_calls[1]["value_pools_override"]["1"][0] == 0xD5
    assert result.metadata["exact2_basin_smt"]["payload"]["exact2_basin_smt"]["attempted"] is True


def test_samplereverse_profile_runs_compare_aware_strategy_when_only_compare_truth_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sample = tmp_path / "samplereverse.exe"
    sample.write_bytes(b"MZ")
    profile = SamplereverseProfile()
    compare_artifact = ToolRunArtifact(
        tool_name="CompareProbe",
        enabled=True,
        attempted=True,
        success=True,
        structured_evidence=[
            StructuredEvidence(kind="RuntimeCompareEvidence", source_tool="CompareProbe"),
        ],
    )
    strategy_artifact = ToolRunArtifact(
        tool_name="CompareAwareBridge",
        enabled=True,
        attempted=True,
        success=True,
        summary="compare-aware ok",
    )
    called: dict[str, bool] = {"strategy": False}

    def fake_strategy_run(self, **kwargs) -> StrategyResult:
        _ = kwargs
        called["strategy"] = True
        return StrategyResult(
            strategy_name="CompareAwareSearchStrategy",
            summary="compare-aware ok",
            candidates=[bytes.fromhex("4a78f0eaeb4f13b041414141414141").decode("latin1")],
            artifacts=[strategy_artifact],
        )

    monkeypatch.setattr(CompareAwareSearchStrategy, "run", fake_strategy_run)

    result = profile.run_specialized_solver(
        file_path=sample,
        strings=["输入的密钥是", "密钥不正确"],
        seed_candidates=[],
        artifacts_dir=tmp_path / "artifacts",
        log=lambda _: None,
        prior_artifacts=[compare_artifact],
    )

    assert result is not None
    assert result.enabled is True
    assert called["strategy"] is True
    assert result.strategies == ["CompareAwareSearchStrategy"]
    assert result.candidates[0].encode("latin1").hex() == "4a78f0eaeb4f13b041414141414141"
