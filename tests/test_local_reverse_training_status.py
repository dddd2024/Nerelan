import json
from pathlib import Path

import pytest

from reverse_agent.local_reverse_training_status import (
    TRAINING_STATUS_BLOCKED,
    TRAINING_STATUS_INVENTORY_ONLY,
    TRAINING_STATUS_NEEDS_TRIAGE,
    TRAINING_STATUS_SOLVED,
    _build_blocked_map,
    _build_evaluation_queue,
    _build_mature_backend_blocked_overlay,
    _build_runtime_blocked_overlay,
    _build_runtime_validation_overlay,
    _build_sample_entry,
    _build_solved_map,
    _build_static_handoff_overlay,
    _build_static_triage_success_overlay,
    _build_static_tool_blocked_overlay,
    build_training_status,
    main,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_solved_map_from_validated() -> None:
    validated = {
        "validated_candidates": [
            {
                "sample_id": "abc123",
                "candidate": "hookapi",
                "validation_status": "validated",
                "source_relation": "xor_constants_against_literal",
            },
            {
                "sample_id": "def456",
                "candidate": "bad",
                "validation_status": "rejected",
                "source_relation": "test",
            },
        ]
    }
    result = _build_solved_map(validated)
    assert "abc123" in result
    assert result["abc123"]["known_candidate"] == "hookapi"
    assert "def456" not in result


def test_build_blocked_map_from_constraints() -> None:
    constraint = {
        "targets": [
            {
                "sample_id": "hash001",
                "constraint_status": "blocked",
                "blocked_reason": "NO_BOUNDED_HASH_PREIMAGE_DOMAIN",
                "next_action": "request hint",
            },
            {
                "sample_id": "good001",
                "constraint_status": "recovered",
                "blocked_reason": "",
            },
        ]
    }
    result = _build_blocked_map(constraint)
    assert "hash001" in result
    assert result["hash001"]["blocked_reason"] == "NO_BOUNDED_HASH_PREIMAGE_DOMAIN"
    assert "good001" not in result


def test_build_sample_entry_solved() -> None:
    entry = {
        "sample_id": "cpp1_abc123",
        "relative_path": "Cpp1.exe",
        "sha256": "abc123def456",
        "size_bytes": 200782,
        "extension": ".exe",
        "guessed_file_type": "pe",
        "category": "cpp",
        "tags": ["local", "reverse", "cpp", "pe"],
    }
    info = {"known_candidate": "hookapi", "validation_status": "validated"}
    result = _build_sample_entry(entry, TRAINING_STATUS_SOLVED, info, {})
    assert result["training_status"] == TRAINING_STATUS_SOLVED
    assert result["known_candidate"] == "hookapi"
    assert result["blocked_reason"] == ""
    assert result["size_bytes"] == 200782
    assert result["extension"] == ".exe"
    assert result["guessed_file_type"] == "pe"


def test_build_sample_entry_blocked() -> None:
    entry = {
        "sample_id": "sha_256_def789",
        "relative_path": "sha_256.exe",
        "sha256": "def789abc012",
        "category": "crypto/hash",
        "tags": ["local", "reverse", "crypto_hash", "pe"],
    }
    info = {"blocked_reason": "NO_BOUNDED_HASH_PREIMAGE_DOMAIN", "next_action": "request hint"}
    result = _build_sample_entry(entry, TRAINING_STATUS_BLOCKED, info, {})
    assert result["training_status"] == TRAINING_STATUS_BLOCKED
    assert result["blocked_reason"] == "NO_BOUNDED_HASH_PREIMAGE_DOMAIN"
    assert result["known_candidate"] == ""


def test_build_evaluation_queue_excludes_solved_and_blocked() -> None:
    samples = [
        {
            "sample_id": "solved1",
            "relative_path": "solved.exe",
            "training_status": TRAINING_STATUS_SOLVED,
            "tags": ["local", "reverse", "pe"],
            "size_bytes": 1000,
        },
        {
            "sample_id": "blocked1",
            "relative_path": "blocked.exe",
            "training_status": TRAINING_STATUS_BLOCKED,
            "tags": ["local", "reverse", "pe"],
            "size_bytes": 1000,
        },
        {
            "sample_id": "todo1",
            "relative_path": "todo.exe",
            "training_status": TRAINING_STATUS_INVENTORY_ONLY,
            "tags": ["local", "reverse", "pe"],
            "size_bytes": 1000,
        },
    ]
    queue = _build_evaluation_queue(samples)
    assert len(queue["items"]) == 1
    assert queue["items"][0]["sample_id"] == "todo1"


def test_build_evaluation_queue_excludes_solver_scripts() -> None:
    samples = [
        {
            "sample_id": "des_interactive_solver",
            "relative_path": "DES/des_interactive_solver.py",
            "training_status": TRAINING_STATUS_INVENTORY_ONLY,
            "tags": ["local", "reverse", "crypto_cipher", "python"],
            "size_bytes": 1000,
        },
        {
            "sample_id": "rc4enc",
            "relative_path": "rc4enc.exe",
            "training_status": TRAINING_STATUS_INVENTORY_ONLY,
            "tags": ["local", "reverse", "crypto_cipher", "pe"],
            "size_bytes": 1000,
        },
    ]
    queue = _build_evaluation_queue(samples)
    ids = {item["sample_id"] for item in queue["items"]}
    assert "des_interactive_solver" not in ids
    assert "rc4enc" in ids


def test_build_evaluation_queue_excludes_needs_triage_and_support_docs() -> None:
    samples = [
        {
            "sample_id": "affineenc_333f8ca9",
            "relative_path": "affineenc.exe",
            "training_status": TRAINING_STATUS_NEEDS_TRIAGE,
            "tags": ["local", "reverse", "pe"],
            "size_bytes": 196691,
            "extension": ".exe",
            "guessed_file_type": "pe",
        },
        {
            "sample_id": "ascii_table_chinese_46efc7ea",
            "relative_path": "ascii_table_chinese.pdf",
            "training_status": TRAINING_STATUS_INVENTORY_ONLY,
            "tags": ["local", "reverse"],
            "size_bytes": 13485,
            "extension": ".pdf",
            "guessed_file_type": "unknown",
        },
        {
            "sample_id": "cpp1_2f6fcb63",
            "relative_path": "CPP1.exe",
            "training_status": TRAINING_STATUS_INVENTORY_ONLY,
            "tags": ["local", "reverse", "cpp", "pe"],
            "size_bytes": 196700,
            "extension": ".exe",
            "guessed_file_type": "pe",
        },
    ]

    queue = _build_evaluation_queue(samples)

    assert [item["sample_id"] for item in queue["items"]] == ["cpp1_2f6fcb63"]


def test_build_static_triage_success_overlay_marks_needs_triage(tmp_path: Path) -> None:
    artifact_file = tmp_path / "local_reverse_affineenc_333f8ca9_static_triage.json"
    _write_json(artifact_file, {
        "sample_id": "affineenc_333f8ca9",
        "static_only": True,
        "executed_sample": False,
        "runtime_validated": False,
        "tool_status": "success",
        "source_tool": "IDA",
        "candidate": None,
        "analysis_mode": "single_sample_static_triage",
        "triage": {
            "solver_profile_hypotheses": [
                "string_compare_password_checker",
                "standard_input_based",
                "strcmp_direct_compare",
            ],
        },
    })
    index_path = tmp_path / "artifact_index.json"
    _write_json(index_path, {
        "latest_artifacts_v2": {
            "local_reverse_affineenc_333f8ca9_static_triage": {
                "kind": "local_reverse_single_sample_static_triage",
                "freshness": "current",
                "path": str(artifact_file),
                "sample_id": "affineenc_333f8ca9",
            }
        }
    })

    result = _build_static_triage_success_overlay(index_path)

    entry = result["affineenc_333f8ca9"]
    assert entry["training_status"] == TRAINING_STATUS_NEEDS_TRIAGE
    assert entry["blocked_reason"] == ""
    assert "static_triage_completed" in entry["evidence_sources"]
    assert "tool_status:success" in entry["evidence_sources"]
    assert "source_tool:IDA" in entry["evidence_sources"]
    assert "string_compare_password_checker" in entry["classification"]


def test_build_training_status_static_triage_success_exits_queue(tmp_path: Path) -> None:
    inventory = {
        "schema_version": 1,
        "entries": [
            {
                "sample_id": "affineenc_333f8ca9",
                "display_name": "affineenc.exe",
                "relative_path": "affineenc.exe",
                "sha256": "333f8ca9f47e5e705b6dcdbcfbb6b24898dba01f6c518f51515d36618e7add9f",
                "size_bytes": 196691,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "unknown",
                "tags": ["local", "reverse", "pe"],
            },
            {
                "sample_id": "ascii_table_chinese_46efc7ea",
                "display_name": "ascii_table_chinese.pdf",
                "relative_path": "ascii_table_chinese.pdf",
                "sha256": "46efc7ea2cd29d8c364198c53a6f146aed679d3e6977753a6984a9771748543a",
                "size_bytes": 13485,
                "extension": ".pdf",
                "guessed_file_type": "unknown",
                "category": "unknown",
                "tags": ["local", "reverse"],
            },
            {
                "sample_id": "cpp1_2f6fcb63",
                "display_name": "CPP1.exe",
                "relative_path": "CPP1.exe",
                "sha256": "2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede",
                "size_bytes": 196700,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "cpp",
                "tags": ["local", "reverse", "cpp", "pe"],
            },
        ],
    }
    artifact_file = tmp_path / "local_reverse_affineenc_333f8ca9_static_triage.json"
    _write_json(artifact_file, {
        "sample_id": "affineenc_333f8ca9",
        "static_only": True,
        "executed_sample": False,
        "runtime_validated": False,
        "tool_status": "success",
        "source_tool": "IDA",
        "candidate": None,
        "analysis_mode": "single_sample_static_triage",
        "triage": {"solver_profile_hypotheses": ["string_compare_password_checker"]},
    })
    artifact_index = {
        "latest_artifacts_v2": {
            "local_reverse_affineenc_333f8ca9_static_triage": {
                "kind": "local_reverse_single_sample_static_triage",
                "freshness": "current",
                "path": str(artifact_file),
                "sample_id": "affineenc_333f8ca9",
            }
        }
    }

    inv_path = tmp_path / "inventory.json"
    artifact_index_path = tmp_path / "artifact_index.json"
    out_path = tmp_path / "status.json"
    queue_path = tmp_path / "queue.json"
    _write_json(inv_path, inventory)
    _write_json(artifact_index_path, artifact_index)

    result = build_training_status(
        inventory_path=inv_path,
        validated_path=tmp_path / "missing_validated.json",
        constraint_path=tmp_path / "missing_constraint.json",
        solver_result_path=tmp_path / "missing_solver.json",
        artifact_index_path=artifact_index_path,
        out_path=out_path,
        queue_out_path=queue_path,
    )

    assert result["status_summary"]["needs_triage"] == 1
    assert result["status_summary"]["inventory_only"] == 2

    status_data = json.loads(out_path.read_text(encoding="utf-8"))
    samples_by_id = {item["sample_id"]: item for item in status_data["samples"]}
    affineenc = samples_by_id["affineenc_333f8ca9"]
    assert affineenc["training_status"] == TRAINING_STATUS_NEEDS_TRIAGE
    assert affineenc["known_candidate"] == ""
    assert affineenc["blocked_reason"] == ""

    queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
    assert [item["sample_id"] for item in queue_data["items"]] == ["cpp1_2f6fcb63"]


def test_build_training_status_end_to_end(tmp_path: Path) -> None:
    # Create mock inventory
    inventory = {
        "schema_version": 1,
        "entries": [
            {
                "sample_id": "cpp1_bcbd9979",
                "display_name": "Cpp1.exe",
                "relative_path": "Cpp1.exe",
                "sha256": "bcbd9979db015bfd12d7c0c270df46918713433636123c545315a9d527b22a5a",
                "size_bytes": 200782,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "cpp",
                "tags": ["local", "reverse", "cpp", "pe"],
            },
            {
                "sample_id": "sha_256_18019fca",
                "display_name": "sha_256.exe",
                "relative_path": "sha_256.exe",
                "sha256": "18019fca52b389feeb2f690d096d5848ff7ba686eac9173bb17a6fabb819a8ff",
                "size_bytes": 200788,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "crypto/hash",
                "tags": ["local", "reverse", "crypto_hash", "pe"],
            },
            {
                "sample_id": "cpp2_4c69f173",
                "display_name": "CPP2.exe",
                "relative_path": "CPP2.exe",
                "sha256": "4c69f173f2bd0211fe472e12b3ecc4dcfbae6a20735a750b8f8c0ea5c566223a",
                "size_bytes": 200785,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "cpp",
                "tags": ["local", "reverse", "cpp", "pe"],
            },
            {
                "sample_id": "rc4enc_3480917d",
                "display_name": "rc4enc.exe",
                "relative_path": "rc4enc.exe",
                "sha256": "3480917ddedce512f76e97c26df3b3ad12b71b34db472fa8836ba67528bcb09f",
                "size_bytes": 196693,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "crypto/cipher",
                "tags": ["local", "reverse", "crypto_cipher", "pe"],
            },
        ],
    }

    # Create mock validated handoff (Cpp1 solved)
    validated = {
        "validated_candidates": [
            {
                "sample_id": "bcbd9979db015bfd",
                "candidate": "hookapi",
                "validation_status": "validated",
            }
        ],
        "unresolved_targets": [],
    }

    # Create mock constraint recovery (sha_256 blocked, CPP2 blocked)
    constraint = {
        "targets": [
            {
                "sample_id": "18019fca52b389fe",
                "constraint_status": "blocked",
                "blocked_reason": "NO_BOUNDED_HASH_PREIMAGE_DOMAIN",
                "next_action": "request hint",
            },
            {
                "sample_id": "4c69f173f2bd0211",
                "constraint_status": "blocked",
                "blocked_reason": "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005",
                "next_action": "recover transform",
            },
        ],
    }

    # Create mock solver result
    solver = {
        "targets": [
            {
                "sample_id": "18019fca52b389fe",
                "classification": "sha256_hex_compare",
            },
            {
                "sample_id": "4c69f173f2bd0211",
                "classification": "bounded_input_range_hash",
            },
            {
                "sample_id": "bcbd9979db015bfd",
                "classification": "api_assisted_password",
            },
        ],
    }

    inv_path = tmp_path / "inventory.json"
    val_path = tmp_path / "validated.json"
    con_path = tmp_path / "constraint.json"
    sol_path = tmp_path / "solver.json"
    out_path = tmp_path / "status.json"
    queue_path = tmp_path / "queue.json"
    gh_path = tmp_path / "github_status.json"

    _write_json(inv_path, inventory)
    _write_json(val_path, validated)
    _write_json(con_path, constraint)
    _write_json(sol_path, solver)

    result = build_training_status(
        inventory_path=inv_path,
        validated_path=val_path,
        constraint_path=con_path,
        solver_result_path=sol_path,
        out_path=out_path,
        queue_out_path=queue_path,
        github_status_path=gh_path,
    )

    assert result["sample_count"] == 4
    status = result["status_summary"]
    assert status["solved"] == 1
    assert status["blocked"] == 2
    assert status["inventory_only"] == 1

    # Verify output files
    assert out_path.exists()
    assert queue_path.exists()
    assert gh_path.exists()

    status_data = json.loads(out_path.read_text(encoding="utf-8"))
    samples_by_id = {s["sample_id"]: s for s in status_data["samples"]}

    # Cpp1 solved
    cpp1 = samples_by_id["cpp1_bcbd9979"]
    assert cpp1["training_status"] == TRAINING_STATUS_SOLVED
    assert cpp1["known_candidate"] == "hookapi"

    # sha_256 blocked
    sha = samples_by_id["sha_256_18019fca"]
    assert sha["training_status"] == TRAINING_STATUS_BLOCKED
    assert sha["blocked_reason"] == "NO_BOUNDED_HASH_PREIMAGE_DOMAIN"

    # CPP2 blocked
    cpp2 = samples_by_id["cpp2_4c69f173"]
    assert cpp2["training_status"] == TRAINING_STATUS_BLOCKED
    assert cpp2["blocked_reason"] == "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005"

    # rc4enc inventory_only
    rc4 = samples_by_id["rc4enc_3480917d"]
    assert rc4["training_status"] == TRAINING_STATUS_INVENTORY_ONLY

    # Queue should have rc4enc only (unsolved)
    queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
    assert len(queue_data["items"]) == 1
    assert queue_data["items"][0]["sample_id"] == "rc4enc_3480917d"

    # GitHub status should not contain real paths
    gh_data = json.loads(gh_path.read_text(encoding="utf-8"))
    assert "source_inventory_hint" in gh_data
    assert gh_data["source_inventory_hint"] == "LOCAL_REVERSE_ROOT"


def test_training_status_no_real_local_path(tmp_path: Path) -> None:
    """Verify output JSON does not contain E:\reverse or similar real paths."""
    inventory = {
        "entries": [
            {
                "sample_id": "test_12345678",
                "relative_path": "test.exe",
                "sha256": "1234567890abcdef",
                "category": "cpp",
                "tags": ["local", "reverse", "cpp", "pe"],
            }
        ]
    }
    inv_path = tmp_path / "inventory.json"
    out_path = tmp_path / "status.json"
    queue_path = tmp_path / "queue.json"
    _write_json(inv_path, inventory)

    build_training_status(
        inventory_path=inv_path,
        validated_path=tmp_path / "missing.json",
        constraint_path=tmp_path / "missing2.json",
        solver_result_path=tmp_path / "missing3.json",
        out_path=out_path,
        queue_out_path=queue_path,
    )

    text = out_path.read_text(encoding="utf-8")
    assert "E:\\reverse" not in text
    assert "E:/reverse" not in text
    assert "LOCAL_REVERSE_ROOT" in text or "source_inventory" in text


def test_main_cli_build(tmp_path: Path) -> None:
    inventory = {
        "entries": [
            {
                "sample_id": "todo1",
                "relative_path": "todo.exe",
                "sha256": "deadbeef",
                "category": "cpp",
                "tags": ["local", "reverse", "cpp", "pe"],
            }
        ]
    }
    inv_path = tmp_path / "inventory.json"
    out_path = tmp_path / "status.json"
    queue_path = tmp_path / "queue.json"
    gh_path = tmp_path / "github_status.json"
    _write_json(inv_path, inventory)

    assert main([
        "--inventory", str(inv_path),
        "--out", str(out_path),
        "--queue-out", str(queue_path),
        "--github-status-out", str(gh_path),
    ]) == 0

    assert out_path.exists()
    assert queue_path.exists()
    assert gh_path.exists()


def test_cpp1_not_mislabeled_as_solved_without_validation() -> None:
    """Cpp1 should only be solved if validation_status is 'validated'."""
    validated = {
        "validated_candidates": [
            {
                "sample_id": "cpp1_abc",
                "candidate": "hookapi",
                "validation_status": "rejected",  # Not validated
            }
        ]
    }
    result = _build_solved_map(validated)
    assert "cpp1_abc" not in result


def test_evaluation_queue_prioritizes_simple_tags() -> None:
    """Queue should prioritize samples with simple static tags."""
    samples = [
        {
            "sample_id": "hash_hard",
            "relative_path": "hash.exe",
            "training_status": TRAINING_STATUS_INVENTORY_ONLY,
            "tags": ["local", "reverse", "hash", "pe"],
            "size_bytes": 200000,
        },
        {
            "sample_id": "xor_easy",
            "relative_path": "xor.exe",
            "training_status": TRAINING_STATUS_INVENTORY_ONLY,
            "tags": ["local", "reverse", "xor", "pe"],
            "size_bytes": 100000,
        },
        {
            "sample_id": "rc4_mid",
            "relative_path": "rc4.exe",
            "training_status": TRAINING_STATUS_INVENTORY_ONLY,
            "tags": ["local", "reverse", "rc4", "pe"],
            "size_bytes": 150000,
        },
    ]
    queue = _build_evaluation_queue(samples)
    ids = [item["sample_id"] for item in queue["items"]]
    # xor should be first (simple), rc4 second, hash last
    assert ids.index("xor_easy") < ids.index("rc4_mid")
    assert ids.index("rc4_mid") < ids.index("hash_hard")


# ---------------------------------------------------------------------------
# Tests for _build_runtime_validation_overlay
# ---------------------------------------------------------------------------


class TestBuildRuntimeValidationOverlay:
    def _make_artifact_index(
        self,
        tmp_path: Path,
        artifacts: list[dict],
    ) -> Path:
        v2: dict[str, dict] = {}
        for i, art_meta in enumerate(artifacts):
            artifact_payload = art_meta["artifact"]
            art_file = tmp_path / f"runtime_artifact_{i}.json"
            _write_json(art_file, artifact_payload)

            v2_key = art_meta.get("key", f"local_reverse_runtime_validation_{i}")
            v2[v2_key] = {
                "kind": art_meta.get("kind", "local_reverse_console_runtime_validation"),
                "freshness": art_meta.get("freshness", "current"),
                "path": str(art_file),
                "sample_id": art_meta.get("sample_id"),
            }

        index_path = tmp_path / "artifact_index.json"
        _write_json(index_path, {"latest_artifacts_v2": v2})
        return index_path

    def _make_success_artifact(self, **overrides) -> dict:
        base = {
            "sample_id": "cpp1_7b504c54",
            "analysis_mode": "console_runtime_validation",
            "validation_status": "VALIDATED_SUCCESS",
            "runtime_validated": True,
            "solved": True,
            "known_candidate": "WeKnowItOk",
        }
        base.update(overrides)
        return base

    def test_validated_success_artifact_marks_sample_solved(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {"artifact": self._make_success_artifact()},
        ])

        result = _build_runtime_validation_overlay(index_path)

        entry = result["cpp1_7b504c54"]
        assert entry["known_candidate"] == "WeKnowItOk"
        assert entry["validation_status"] == "VALIDATED_SUCCESS"
        assert "console_runtime_validation" in entry["evidence_sources"]
        assert "runtime_validated_success" in entry["evidence_sources"]

    @pytest.mark.parametrize(
        "overrides",
        [
            {"validation_status": "BLOCKED"},
            {"validation_status": "VALIDATED_FAILURE"},
            {"validation_status": "AMBIGUOUS_OUTPUT"},
            {"runtime_validated": False},
            {"solved": False},
            {"known_candidate": ""},
        ],
    )
    def test_non_success_runtime_artifacts_do_not_mark_solved(
        self,
        tmp_path: Path,
        overrides: dict,
    ) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {"artifact": self._make_success_artifact(**overrides)},
        ])

        assert _build_runtime_validation_overlay(index_path) == {}

    def test_stale_or_wrong_kind_runtime_artifact_skipped(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "freshness": "stale",
                "artifact": self._make_success_artifact(sample_id="stale_success"),
            },
            {
                "kind": "local_reverse_static_handoff",
                "artifact": self._make_success_artifact(sample_id="wrong_kind"),
            },
        ])

        assert _build_runtime_validation_overlay(index_path) == {}

    # -- Tests for _build_runtime_blocked_overlay --

    def test_ambiguous_output_runtime_artifact_marks_blocked_not_solved(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "artifact": {
                    "sample_id": "cpp2_ambiguous",
                    "analysis_mode": "console_runtime_pair_validation",
                    "validation_status": "AMBIGUOUS_OUTPUT",
                    "runtime_validated": False,
                    "solved": False,
                    "blocked_reason": "AMBIGUOUS_OUTPUT",
                    "failure_reason": "Candidate and negative control produced identical stdout, stderr, and return code.",
                    "known_candidate": "",
                },
                "kind": "local_reverse_console_pair_runtime_validation",
            },
        ])

        result = _build_runtime_blocked_overlay(index_path)
        entry = result["cpp2_ambiguous"]
        assert entry["training_status"] == TRAINING_STATUS_BLOCKED
        assert entry["blocked_reason"] == "AMBIGUOUS_OUTPUT"
        assert "known_candidate" not in entry
        assert "runtime_validation_status:AMBIGUOUS_OUTPUT" in entry["evidence_sources"]

    def test_validated_failure_runtime_artifact_marks_blocked(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "artifact": {
                    "sample_id": "cpp2_failure",
                    "analysis_mode": "console_runtime_validation",
                    "validation_status": "VALIDATED_FAILURE",
                    "runtime_validated": False,
                    "solved": False,
                    "blocked_reason": "VALIDATED_FAILURE",
                    "failure_reason": "Candidate produced wrong output.",
                    "known_candidate": "",
                },
                "kind": "local_reverse_console_runtime_validation",
            },
        ])

        result = _build_runtime_blocked_overlay(index_path)
        entry = result["cpp2_failure"]
        assert entry["training_status"] == TRAINING_STATUS_BLOCKED
        assert entry["blocked_reason"] == "VALIDATED_FAILURE"

    def test_validated_success_not_in_runtime_blocked_overlay(self, tmp_path: Path) -> None:
        """VALIDATED_SUCCESS should NOT appear in runtime_blocked overlay."""
        index_path = self._make_artifact_index(tmp_path, [
            {"artifact": self._make_success_artifact(sample_id="cpp1_success")},
        ])

        assert _build_runtime_blocked_overlay(index_path) == {}

    def test_runtime_blocked_uses_failure_reason_fallback(self, tmp_path: Path) -> None:
        """When blocked_reason is empty but failure_reason exists, use failure_reason."""
        index_path = self._make_artifact_index(tmp_path, [
            {
                "artifact": {
                    "sample_id": "cpp2_fallback",
                    "analysis_mode": "console_runtime_validation",
                    "validation_status": "BLOCKED",
                    "runtime_validated": False,
                    "solved": False,
                    "blocked_reason": "",
                    "failure_reason": "Some failure reason",
                    "known_candidate": "",
                },
                "kind": "local_reverse_console_runtime_validation",
            },
        ])

        result = _build_runtime_blocked_overlay(index_path)
        assert result["cpp2_fallback"]["blocked_reason"] == "Some failure reason"

    # -- Tests for _build_mature_backend_blocked_overlay --

    def test_mature_backend_missing_marks_blocked(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "artifact": {
                    "sample_id": "cpp2_backend",
                    "analysis_mode": "console_mature_backend_availability_probe",
                    "probe_status": "BLOCKED_MATURE_BACKEND_MISSING",
                    "can_attempt_interactive_console_validation_next": False,
                    "solved": False,
                    "blocked_reason": "Windows platform but no mature backend available",
                    "known_candidate": "",
                },
                "kind": "local_reverse_console_mature_backend_availability_probe",
            },
        ])

        result = _build_mature_backend_blocked_overlay(index_path)
        entry = result["cpp2_backend"]
        assert entry["training_status"] == TRAINING_STATUS_BLOCKED
        assert entry["blocked_reason"] == "Windows platform but no mature backend available"
        assert "known_candidate" not in entry
        assert "console_mature_backend_probe" in entry["evidence_sources"]
        assert "mature_backend_missing" in entry["evidence_sources"]

    def test_mature_backend_can_attempt_true_skipped(self, tmp_path: Path) -> None:
        """If can_attempt_interactive_console_validation_next is True, skip."""
        index_path = self._make_artifact_index(tmp_path, [
            {
                "artifact": {
                    "sample_id": "cpp2_can_attempt",
                    "analysis_mode": "console_mature_backend_availability_probe",
                    "probe_status": "BLOCKED_MATURE_BACKEND_MISSING",
                    "can_attempt_interactive_console_validation_next": True,
                    "solved": False,
                    "blocked_reason": "Windows platform but no mature backend available",
                },
                "kind": "local_reverse_console_mature_backend_availability_probe",
            },
        ])

        assert _build_mature_backend_blocked_overlay(index_path) == {}

    def test_mature_backend_solved_true_skipped(self, tmp_path: Path) -> None:
        """If solved=True, skip."""
        index_path = self._make_artifact_index(tmp_path, [
            {
                "artifact": {
                    "sample_id": "cpp2_solved",
                    "analysis_mode": "console_mature_backend_availability_probe",
                    "probe_status": "BLOCKED_MATURE_BACKEND_MISSING",
                    "can_attempt_interactive_console_validation_next": False,
                    "solved": True,
                    "blocked_reason": "Windows platform but no mature backend available",
                },
                "kind": "local_reverse_console_mature_backend_availability_probe",
            },
        ])

        assert _build_mature_backend_blocked_overlay(index_path) == {}

    # -- Priority test: mature_backend_blocked overrides runtime_blocked --

    def test_mature_backend_priority_overrides_ambiguous_runtime(self, tmp_path: Path) -> None:
        """For same sample, mature_backend_blocked should take priority over runtime_blocked."""
        # Build artifact index with both artifacts for same sample
        v2: dict[str, dict] = {}

        runtime_artifact = {
            "sample_id": "cpp2_both",
            "analysis_mode": "console_runtime_pair_validation",
            "validation_status": "AMBIGUOUS_OUTPUT",
            "runtime_validated": False,
            "solved": False,
            "blocked_reason": "AMBIGUOUS_OUTPUT",
            "failure_reason": "Candidate and negative control produced identical output.",
            "known_candidate": "",
        }
        runtime_file = tmp_path / "runtime_blocked.json"
        _write_json(runtime_file, runtime_artifact)
        v2["local_reverse_cpp2_runtime_pair_validation"] = {
            "kind": "local_reverse_console_pair_runtime_validation",
            "freshness": "current",
            "path": str(runtime_file),
            "sample_id": "cpp2_both",
        }

        probe_artifact = {
            "sample_id": "cpp2_both",
            "analysis_mode": "console_mature_backend_availability_probe",
            "probe_status": "BLOCKED_MATURE_BACKEND_MISSING",
            "can_attempt_interactive_console_validation_next": False,
            "solved": False,
            "blocked_reason": "Windows platform but no mature backend available (pywinpty/winpty/wexpect/ConPTY API)",
            "known_candidate": "",
        }
        probe_file = tmp_path / "probe_blocked.json"
        _write_json(probe_file, probe_artifact)
        v2["local_reverse_cpp2_console_mature_backend_probe"] = {
            "kind": "local_reverse_console_mature_backend_availability_probe",
            "freshness": "current",
            "path": str(probe_file),
            "sample_id": "cpp2_both",
        }

        index_path = tmp_path / "artifact_index.json"
        _write_json(index_path, {"latest_artifacts_v2": v2})

        runtime_blocked = _build_runtime_blocked_overlay(index_path)
        mature_backend_blocked = _build_mature_backend_blocked_overlay(index_path)

        assert "cpp2_both" in runtime_blocked
        assert "cpp2_both" in mature_backend_blocked

        # Simulate the priority logic from build_training_status
        # mature_backend_blocked should win
        info = mature_backend_blocked["cpp2_both"]
        assert info["blocked_reason"] == "Windows platform but no mature backend available (pywinpty/winpty/wexpect/ConPTY API)"
        assert "mature_backend_missing" in info["evidence_sources"]


# ---------------------------------------------------------------------------
# Tests for _build_static_handoff_overlay
# ---------------------------------------------------------------------------


class TestBuildStaticHandoffOverlay:
    """Tests for the static handoff overlay builder that scans artifact_index.json.

    After rework: static handoff overlay ONLY accepts artifacts that satisfy ALL of:
      - static_only is True
      - executed_sample is False
      - runtime_validated is False
      - status == "BLOCKED"
      - candidate is None
      - blocked_reason is non-empty

    It can NEVER produce solved/known_candidate.
    """

    def _make_artifact_index(
        self,
        tmp_path,
        artifacts: list[dict],
    ) -> Path:
        """Helper: create an artifact_index.json with given artifact entries."""
        v2: dict[str, dict] = {}
        for i, art_meta in enumerate(artifacts):
            key_prefix = art_meta["key_prefix"]
            freshness = art_meta.get("freshness", "current")
            artifact_payload = art_meta["artifact"]

            art_file = tmp_path / f"artifact_{i}.json"
            _write_json(art_file, artifact_payload)

            v2_key = f"{key_prefix}_sample_{i}"
            v2[v2_key] = {
                "kind": art_meta.get("kind", key_prefix),
                "freshness": freshness,
                "path": str(art_file),
                "sample_id": art_meta.get("sample_id"),
            }

        index_path = tmp_path / "artifact_index.json"
        _write_json(index_path, {"latest_artifacts_v2": v2})
        return index_path

    def _make_blocked_artifact(self, **overrides) -> dict:
        """Helper: build a minimal valid blocked artifact for overlay."""
        base = {
            "sample_id": "test_blocked",
            "static_only": True,
            "executed_sample": False,
            "runtime_validated": False,
            "status": "BLOCKED",
            "blocked_reason": "MISSING_EXPECTED_CIPHERTEXT",
            "candidate": None,
            "cipher_type": "affine_cipher",
            "analysis_mode": "affine inverse handoff static only",
        }
        base.update(overrides)
        return base

    # -- 1. No artifact_index file -> returns empty dict --

    def test_missing_index_returns_empty(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "does_not_exist.json"
        result = _build_static_handoff_overlay(nonexistent)
        assert result == {}

    # -- 2. Artifact with freshness != current -> skipped --

    def test_stale_artifact_skipped(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_affine_inverse_handoff",
                "freshness": "stale",
                "artifact": self._make_blocked_artifact(),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        assert result == {}

    def test_current_target_provenance_recheck_artifact_accepted(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_sample_target_provenance_recheck",
                "kind": "local_reverse_sample_target_provenance_recheck",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="cpp1_target",
                    blocked_reason="CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE",
                    provenance_verdict="CONFIRMED_NO_PRINTABLE_PREIMAGE",
                    cipher_type="",
                    analysis_mode="target_byte_provenance_recheck",
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        entry = result["cpp1_target"]
        assert entry["training_status"] == TRAINING_STATUS_BLOCKED
        assert entry["blocked_reason"] == "CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE"
        assert "known_candidate" not in entry
        assert "static_blocked_artifact" in entry["evidence_sources"]
        assert "provenance:CONFIRMED_NO_PRINTABLE_PREIMAGE" in entry["evidence_sources"]

    # -- 3. Valid blocked artifact -> training_status=blocked --

    def test_valid_blocked_artifact_accepted(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_targeted_static_reextraction_result",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="blocked_sample_01",
                    cipher_type="xor_fixed_key",
                    analysis_mode="targeted_static",
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        assert "blocked_sample_01" in result
        entry = result["blocked_sample_01"]
        assert entry["training_status"] == TRAINING_STATUS_BLOCKED
        assert entry["blocked_reason"] == "MISSING_EXPECTED_CIPHERTEXT"
        assert "known_candidate" not in entry

    # -- 4. READY + candidate -> NOT solved, skipped entirely --

    def test_ready_with_candidate_skipped(self, tmp_path: Path) -> None:
        """READY + candidate static handoff must NOT produce solved/known_candidate."""
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_affine_inverse_handoff",
                "freshness": "current",
                "artifact": {
                    "sample_id": "ready_sample",
                    "static_only": True,
                    "executed_sample": False,
                    "runtime_validated": False,
                    "status": "READY",
                    "candidate": "affine_key_ab",
                    "cipher_type": "affine",
                    "analysis_mode": "targeted_inverse",
                },
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        # Must NOT appear in overlay at all
        assert "ready_sample" not in result

    # -- 5. Missing static_only field -> skipped --

    def test_missing_static_only_skipped(self, tmp_path: Path) -> None:
        artifact = self._make_blocked_artifact(sample_id="no_static")
        del artifact["static_only"]
        index_path = self._make_artifact_index(tmp_path, [
            {"key_prefix": "local_reverse_affine_inverse_handoff", "freshness": "current", "artifact": artifact},
        ])
        result = _build_static_handoff_overlay(index_path)
        assert "no_static" not in result

    def test_static_tool_no_output_triage_artifact_skipped(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_affine_8cfebe03_static_triage",
                "kind": "local_reverse_single_sample_static_triage",
                "freshness": "current",
                "artifact": {
                    "sample_id": "affine_8cfebe03",
                    "static_only": True,
                    "executed_sample": False,
                    "runtime_validated": False,
                    "tool_status": "blocked",
                    "blocked_reason": "STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON",
                    "candidate": None,
                    "analysis_mode": "single_sample_static_triage",
                },
            },
        ])

        result = _build_static_handoff_overlay(index_path)

        assert "affine_8cfebe03" not in result

    # -- 6. executed_sample=true -> skipped --

    def test_executed_sample_true_skipped(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_affine_inverse_handoff",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="executed_sample",
                    executed_sample=True,
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        assert "executed_sample" not in result

    # -- 7. runtime_validated=true -> skipped --

    def test_runtime_validated_true_skipped(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_affine_inverse_handoff",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="runtime_validated",
                    runtime_validated=True,
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        assert "runtime_validated" not in result

    # -- 8. candidate present -> skipped --

    def test_candidate_present_skipped(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_affine_inverse_handoff",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="has_candidate",
                    candidate="some_answer",
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        assert "has_candidate" not in result

    def test_target_provenance_priority_over_transform_and_handoff(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_sample_inverse_handoff",
                "kind": "local_reverse_sample_inverse_handoff",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="priority_target",
                    analysis_mode="inverse_handoff",
                    blocked_reason="INVERSE_HANDOFF_BLOCKED",
                ),
            },
            {
                "key_prefix": "local_reverse_sample_transform_recheck",
                "kind": "local_reverse_sample_transform_recheck",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="priority_target",
                    analysis_mode="transform_recheck",
                    blocked_reason="TRANSFORM_RECHECK_BLOCKED",
                ),
            },
            {
                "key_prefix": "local_reverse_sample_target_provenance_recheck",
                "kind": "local_reverse_sample_target_provenance_recheck",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="priority_target",
                    analysis_mode="target_provenance_recheck",
                    blocked_reason="TARGET_PROVENANCE_BLOCKED",
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        assert result["priority_target"]["blocked_reason"] == "TARGET_PROVENANCE_BLOCKED"

    # -- 9. Evidence sources include static_handoff tag --

    def test_evidence_sources_include_static_handoff(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_targeted_static_reextraction_result",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="evidence_sample",
                    cipher_type="xor_fixed_key",
                    confidence="high",
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        entry = result["evidence_sample"]
        sources = entry["evidence_sources"]
        assert "static_handoff" in sources
        assert "static_cipher_analysis" in sources
        assert "confidence:high" in sources

    # -- 10. Classification includes cipher_type, analysis_mode, and blocked_reason --

    def test_classification_includes_cipher_mode_and_reason(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_affine_inverse_handoff",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="class_sample",
                    cipher_type="affine_cipher",
                    analysis_mode="affine inverse handoff static only",
                    blocked_reason="MISSING_EXPECTED_CIPHERTEXT",
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        entry = result["class_sample"]
        classification = entry["classification"]
        assert "affine_cipher" in classification
        assert "inverse" in classification
        assert "missing_expected_ciphertext" in classification

    # -- 11. Handoff takes priority over analysis for same sample_id --

    def test_handoff_priority_over_analysis(self, tmp_path: Path) -> None:
        index_path = self._make_artifact_index(tmp_path, [
            {
                "key_prefix": "local_reverse_affine_main0_targeted_ida_decompile",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="priority_sample",
                    cipher_type="xor_fixed_key",
                    analysis_mode="targeted_decompile",
                    blocked_reason="NEEDS_MORE_EVIDENCE",
                ),
            },
            {
                "key_prefix": "local_reverse_affine_inverse_handoff",
                "freshness": "current",
                "artifact": self._make_blocked_artifact(
                    sample_id="priority_sample",
                    cipher_type="affine_cipher",
                    analysis_mode="affine inverse handoff static only",
                    blocked_reason="MISSING_EXPECTED_CIPHERTEXT",
                ),
            },
        ])
        result = _build_static_handoff_overlay(index_path)
        entry = result["priority_sample"]
        # Handoff should win (affine_cipher, not xor_fixed_key)
        assert "affine_cipher" in entry["classification"]
        assert entry["blocked_reason"] == "MISSING_EXPECTED_CIPHERTEXT"


class TestBuildStaticToolBlockedOverlay:
    def test_static_tool_no_output_marks_needs_triage(self, tmp_path: Path) -> None:
        artifact_file = tmp_path / "static_triage.json"
        _write_json(artifact_file, {
            "sample_id": "affine_8cfebe03",
            "static_only": True,
            "executed_sample": False,
            "runtime_validated": False,
            "tool_status": "blocked",
            "blocked_reason": "STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON",
            "source_tool": "IDA",
            "candidate": None,
            "analysis_mode": "single_sample_static_triage",
        })
        index_path = tmp_path / "artifact_index.json"
        _write_json(index_path, {
            "latest_artifacts_v2": {
                "local_reverse_affine_8cfebe03_static_triage": {
                    "kind": "local_reverse_single_sample_static_triage",
                    "freshness": "current",
                    "path": str(artifact_file),
                    "sample_id": "affine_8cfebe03",
                }
            }
        })

        result = _build_static_tool_blocked_overlay(index_path)

        entry = result["affine_8cfebe03"]
        assert entry["training_status"] == "needs_triage"
        assert entry["blocked_reason"] == "STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON"
        assert "static_tool_blocked" in entry["evidence_sources"]
        assert "source_tool:IDA" in entry["evidence_sources"]

    def test_static_tool_success_or_stale_artifact_skipped(self, tmp_path: Path) -> None:
        artifact_file = tmp_path / "static_triage.json"
        _write_json(artifact_file, {
            "sample_id": "affine_8cfebe03",
            "static_only": True,
            "executed_sample": False,
            "runtime_validated": False,
            "tool_status": "success",
            "blocked_reason": "",
            "candidate": None,
        })
        index_path = tmp_path / "artifact_index.json"
        _write_json(index_path, {
            "latest_artifacts_v2": {
                "local_reverse_affine_8cfebe03_static_triage": {
                    "kind": "local_reverse_single_sample_static_triage",
                    "freshness": "current",
                    "path": str(artifact_file),
                    "sample_id": "affine_8cfebe03",
                },
                "local_reverse_affine_8cfebe03_stale_static_triage": {
                    "kind": "local_reverse_single_sample_static_triage",
                    "freshness": "stale",
                    "path": str(artifact_file),
                    "sample_id": "affine_8cfebe03",
                },
            }
        })

        assert _build_static_tool_blocked_overlay(index_path) == {}


def test_build_training_status_marks_static_tool_blocked_sample_needs_triage(tmp_path: Path) -> None:
    inventory = {
        "schema_version": 1,
        "entries": [
            {
                "sample_id": "affine_8cfebe03",
                "display_name": "affine.exe",
                "relative_path": "affine.exe",
                "sha256": "8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659",
                "size_bytes": 196688,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "unknown",
                "tags": ["local", "reverse", "pe"],
            }
        ],
    }
    artifact_file = tmp_path / "local_reverse_affine_8cfebe03_static_triage.json"
    _write_json(artifact_file, {
        "sample_id": "affine_8cfebe03",
        "static_only": True,
        "executed_sample": False,
        "runtime_validated": False,
        "tool_status": "blocked",
        "blocked_reason": "STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON",
        "source_tool": "IDA",
        "candidate": None,
        "analysis_mode": "single_sample_static_triage",
    })
    artifact_index = {
        "latest_artifacts_v2": {
            "local_reverse_affine_8cfebe03_static_triage": {
                "kind": "local_reverse_single_sample_static_triage",
                "freshness": "current",
                "path": str(artifact_file),
                "sample_id": "affine_8cfebe03",
            }
        }
    }

    inv_path = tmp_path / "inventory.json"
    artifact_index_path = tmp_path / "artifact_index.json"
    out_path = tmp_path / "status.json"
    queue_path = tmp_path / "queue.json"
    _write_json(inv_path, inventory)
    _write_json(artifact_index_path, artifact_index)

    result = build_training_status(
        inventory_path=inv_path,
        validated_path=tmp_path / "missing_validated.json",
        constraint_path=tmp_path / "missing_constraint.json",
        solver_result_path=tmp_path / "missing_solver.json",
        artifact_index_path=artifact_index_path,
        out_path=out_path,
        queue_out_path=queue_path,
    )

    assert result["status_summary"]["needs_triage"] == 1
    assert result["status_summary"]["inventory_only"] == 0

    status_data = json.loads(out_path.read_text(encoding="utf-8"))
    sample = status_data["samples"][0]
    assert sample["sample_id"] == "affine_8cfebe03"
    assert sample["training_status"] == "needs_triage"
    assert sample["known_candidate"] == ""
    assert sample["blocked_reason"] == "STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON"
    assert "static_tool_blocked" in sample["evidence_sources"]

    queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
    assert queue_data["items"] == []


def test_training_status_end_to_end_with_artifact_index_overlays(tmp_path: Path) -> None:
    """End-to-end test using deterministic tmp_path fixtures instead of live artifact_index.

    Verifies that build_training_status correctly merges:
    - inventory entries
    - validated candidate handoff (solved)
    - constraint recovery (blocked)
    - runtime validation overlay (solved via current artifact)
    - runtime blocked overlay (blocked via current artifact)
    - mature backend blocked overlay (blocked via current artifact)
    - static handoff overlay (blocked via current artifact)

    All artifacts are created in tmp_path; no dependency on live project_state/artifact_index.json.
    """
    # --- 1. Build deterministic inventory ---
    inventory = {
        "schema_version": 1,
        "entries": [
            {
                "sample_id": "cpp1_2f6fcb63",
                "display_name": "CPP1.exe",
                "relative_path": "Cpp1.exe",
                "sha256": "2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede",
                "size_bytes": 196700,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "cpp",
                "tags": ["local", "reverse", "cpp", "pe"],
            },
            {
                "sample_id": "cpp1_7b504c54",
                "display_name": "Cpp1.exe",
                "relative_path": "Cpp1.exe",
                "sha256": "7b504c54c165100549a0eacb7eb7cad26bc235ec0c4bed5c38c95a827ff81a3c",
                "size_bytes": 184398,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "cpp",
                "tags": ["local", "reverse", "cpp", "pe"],
            },
            {
                "sample_id": "cpp2_2f64e68d",
                "display_name": "CPP2.exe",
                "relative_path": "CPP2.exe",
                "sha256": "2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1",
                "size_bytes": 196689,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "cpp",
                "tags": ["local", "reverse", "cpp", "pe"],
            },
            {
                "sample_id": "rc4enc_3480917d",
                "display_name": "rc4enc.exe",
                "relative_path": "rc4enc.exe",
                "sha256": "3480917ddedce512f76e97c26df3b3ad12b71b34db472fa8836ba67528bcb09f",
                "size_bytes": 196693,
                "extension": ".exe",
                "guessed_file_type": "pe",
                "category": "crypto/cipher",
                "tags": ["local", "reverse", "crypto_cipher", "pe"],
            },
        ],
    }

    # --- 2. Validated handoff: cpp1_7b504c54 solved ---
    validated = {
        "validated_candidates": [
            {
                "sample_id": "7b504c54c1651005",
                "candidate": "WeKnowItOk",
                "validation_status": "validated",
            }
        ],
        "unresolved_targets": [],
    }

    # --- 3. Constraint recovery: rc4enc blocked ---
    constraint = {
        "targets": [
            {
                "sample_id": "3480917ddedce512",
                "constraint_status": "blocked",
                "blocked_reason": "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005",
                "next_action": "recover transform",
            },
        ],
    }

    # --- 4. Solver result ---
    solver = {
        "targets": [
            {
                "sample_id": "2f6fcb637151a413",
                "classification": "cpp_static_triage",
            },
            {
                "sample_id": "7b504c54c1651005",
                "classification": "api_assisted_password",
            },
            {
                "sample_id": "2f64e68d4f8c20b1",
                "classification": "bounded_input_range_hash",
            },
        ],
    }

    # --- 5. Build deterministic artifact_index in tmp_path ---
    # 5a. Static handoff overlay artifact for cpp1_2f6fcb63 -> BLOCKED
    static_artifact_file = tmp_path / "static_handoff.json"
    _write_json(static_artifact_file, {
        "sample_id": "cpp1_2f6fcb63",
        "static_only": True,
        "executed_sample": False,
        "runtime_validated": False,
        "status": "BLOCKED",
        "blocked_reason": "CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE",
        "candidate": None,
        "cipher_type": "",
        "analysis_mode": "target_byte_provenance_recheck",
        "provenance_verdict": "CONFIRMED_NO_PRINTABLE_PREIMAGE",
    })

    # 5b. Runtime validation artifact for cpp1_7b504c54 -> SOLVED
    runtime_val_file = tmp_path / "runtime_validation.json"
    _write_json(runtime_val_file, {
        "sample_id": "cpp1_7b504c54",
        "analysis_mode": "console_runtime_validation",
        "validation_status": "VALIDATED_SUCCESS",
        "runtime_validated": True,
        "solved": True,
        "known_candidate": "WeKnowItOk",
    })

    # 5c. Runtime blocked artifact for cpp2_2f64e68d -> BLOCKED
    runtime_blocked_file = tmp_path / "runtime_blocked.json"
    _write_json(runtime_blocked_file, {
        "sample_id": "cpp2_2f64e68d",
        "analysis_mode": "console_runtime_pair_validation",
        "validation_status": "AMBIGUOUS_OUTPUT",
        "runtime_validated": False,
        "solved": False,
        "blocked_reason": "AMBIGUOUS_OUTPUT",
        "failure_reason": "Candidate and negative control produced identical output.",
        "known_candidate": "",
    })

    # 5d. Mature backend blocked artifact for cpp2_2f64e68d -> BLOCKED (higher priority)
    mature_backend_file = tmp_path / "mature_backend_blocked.json"
    _write_json(mature_backend_file, {
        "sample_id": "cpp2_2f64e68d",
        "analysis_mode": "console_mature_backend_availability_probe",
        "probe_status": "BLOCKED_MATURE_BACKEND_MISSING",
        "can_attempt_interactive_console_validation_next": False,
        "solved": False,
        "blocked_reason": "Windows platform but no mature backend available",
        "known_candidate": "",
    })

    # 5e. Assemble artifact_index
    artifact_index = {
        "latest_artifacts_v2": {
            "local_reverse_cpp1_2f6fcb63_target_provenance_recheck": {
                "kind": "local_reverse_sample_target_provenance_recheck",
                "freshness": "current",
                "path": str(static_artifact_file),
                "sample_id": "cpp1_2f6fcb63",
            },
            "local_reverse_cpp1_7b504c54_runtime_validation": {
                "kind": "local_reverse_console_runtime_validation",
                "freshness": "current",
                "path": str(runtime_val_file),
                "sample_id": "cpp1_7b504c54",
            },
            "local_reverse_cpp2_2f64e68d_runtime_blocked": {
                "kind": "local_reverse_console_pair_runtime_validation",
                "freshness": "current",
                "path": str(runtime_blocked_file),
                "sample_id": "cpp2_2f64e68d",
            },
            "local_reverse_cpp2_2f64e68d_mature_backend": {
                "kind": "local_reverse_console_mature_backend_availability_probe",
                "freshness": "current",
                "path": str(mature_backend_file),
                "sample_id": "cpp2_2f64e68d",
            },
        }
    }
    artifact_index_path = tmp_path / "artifact_index.json"
    _write_json(artifact_index_path, artifact_index)

    # --- 6. Run build_training_status ---
    inv_path = tmp_path / "inventory.json"
    val_path = tmp_path / "validated.json"
    con_path = tmp_path / "constraint.json"
    sol_path = tmp_path / "solver.json"
    out_path = tmp_path / "status.json"
    queue_path = tmp_path / "queue.json"
    gh_path = tmp_path / "github_status.json"

    _write_json(inv_path, inventory)
    _write_json(val_path, validated)
    _write_json(con_path, constraint)
    _write_json(sol_path, solver)

    result = build_training_status(
        inventory_path=inv_path,
        validated_path=val_path,
        constraint_path=con_path,
        solver_result_path=sol_path,
        artifact_index_path=artifact_index_path,
        out_path=out_path,
        queue_out_path=queue_path,
        github_status_path=gh_path,
    )

    # --- 7. Assertions ---
    # blocked: cpp1_2f6fcb63 (static), cpp2_2f64e68d (mature_backend priority over runtime_blocked), rc4enc_3480917d (constraint)
    assert result["status_summary"]["blocked"] == 3
    # solved: cpp1_7b504c54 (runtime validation)
    assert result["status_summary"]["solved"] == 1
    # inventory_only: none (all 4 samples have some status)
    assert result["status_summary"]["inventory_only"] == 0

    status_data = json.loads(out_path.read_text(encoding="utf-8"))
    samples_by_id = {s["sample_id"]: s for s in status_data["samples"]}

    # cpp1_2f6fcb63 blocked via static handoff overlay
    cpp1 = samples_by_id["cpp1_2f6fcb63"]
    assert cpp1["training_status"] == TRAINING_STATUS_BLOCKED
    assert cpp1["known_candidate"] == ""
    assert cpp1["blocked_reason"] == "CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE"
    assert "static_blocked_artifact" in cpp1["evidence_sources"]

    # cpp1_7b504c54 solved via runtime validation overlay
    runtime_cpp1 = samples_by_id["cpp1_7b504c54"]
    assert runtime_cpp1["training_status"] == TRAINING_STATUS_SOLVED
    assert runtime_cpp1["known_candidate"] == "WeKnowItOk"
    assert runtime_cpp1["blocked_reason"] == ""
    assert "console_runtime_validation" in runtime_cpp1["evidence_sources"]
    assert "runtime_validated_success" in runtime_cpp1["evidence_sources"]

    # cpp2_2f64e68d blocked via mature_backend overlay (priority over runtime_blocked)
    cpp2 = samples_by_id["cpp2_2f64e68d"]
    assert cpp2["training_status"] == TRAINING_STATUS_BLOCKED
    assert cpp2["known_candidate"] == ""
    assert cpp2["blocked_reason"] == "Windows platform but no mature backend available"
    assert "console_mature_backend_probe" in cpp2["evidence_sources"]
    assert "mature_backend_missing" in cpp2["evidence_sources"]

    # Queue excludes solved and blocked
    queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
    queue_ids = {item["sample_id"] for item in queue_data["items"]}
    assert "cpp1_2f6fcb63" not in queue_ids
    assert "cpp1_7b504c54" not in queue_ids
    assert "cpp2_2f64e68d" not in queue_ids

    # GitHub-safe output has no absolute local paths
    github_text = gh_path.read_text(encoding="utf-8")
    assert "E:\\reverse" not in github_text
    assert "D:\\reverse" not in github_text
    assert "C:\\reverse" not in github_text
