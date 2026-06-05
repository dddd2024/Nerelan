import json
from pathlib import Path

import pytest

from reverse_agent.local_reverse_training_status import (
    TRAINING_STATUS_BLOCKED,
    TRAINING_STATUS_INVENTORY_ONLY,
    TRAINING_STATUS_SOLVED,
    _build_blocked_map,
    _build_evaluation_queue,
    _build_sample_entry,
    _build_solved_map,
    _build_static_handoff_overlay,
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
                "freshness": freshness,
                "path": str(art_file),
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
