"""Synthetic/static contract tests for local_reverse_static_type_tag_contract.

These tests verify the contract schema and key tag rules.
They do NOT validate sample results, run samples, or execute tools.
All fixtures are synthetic/static contract data.
"""

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Contract loading
# ---------------------------------------------------------------------------

CONTRACT_PATH = Path(__file__).resolve().parent.parent / "project_state" / "local_reverse_static_type_tag_contract.json"

REQUIRED_TAG_IDS = [
    "string_comparison",
    "xor",
    "shift_affine",
    "bit_operations",
    "lookup_table",
    "rc4",
    "des",
    "tea_xtea",
    "base64",
    "hash_md5_sha",
    "gui_validation",
    "simple_antidebug",
    "mixed_unknown",
]

REQUIRED_FIELDS_PER_TAG = [
    "evidence_requirements",
    "allowed_evidence_sources",
    "confidence_rules",
    "solver_or_tool_route",
    "not_sufficient_conditions",
    "next_minimal_task",
    "metadata_only_allowed",
    "static_verified_requires",
]


def _load_contract() -> dict:
    """Load the static type tag contract from project_state."""
    with open(CONTRACT_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def contract() -> dict:
    """Module-scoped fixture that loads the contract once."""
    return _load_contract()


# ---------------------------------------------------------------------------
# 1. Contract covers all required tag ids
# ---------------------------------------------------------------------------


class TestContractCoversRequiredTagIds:
    """Verify the contract covers all 13 required tag ids."""

    def test_contract_file_exists(self) -> None:
        assert CONTRACT_PATH.exists(), f"Contract file not found at {CONTRACT_PATH}"

    def test_contract_has_tags_section(self, contract: dict) -> None:
        assert "tags" in contract, "Contract missing 'tags' section"
        assert isinstance(contract["tags"], dict), "'tags' must be a dict"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_tag_id_present(self, contract: dict, tag_id: str) -> None:
        assert tag_id in contract["tags"], f"Required tag '{tag_id}' not in contract tags"

    def test_required_tag_ids_list_matches(self, contract: dict) -> None:
        contract_required = set(contract.get("required_tag_ids", []))
        expected = set(REQUIRED_TAG_IDS)
        assert contract_required == expected, (
            f"Contract required_tag_ids mismatch: "
            f"missing={expected - contract_required}, "
            f"extra={contract_required - expected}"
        )

    def test_no_extra_tags_beyond_required(self, contract: dict) -> None:
        tag_keys = set(contract["tags"].keys())
        expected = set(REQUIRED_TAG_IDS)
        extra = tag_keys - expected
        assert not extra, f"Unexpected extra tags in contract: {extra}"


# ---------------------------------------------------------------------------
# 2. Each tag has required fields
# ---------------------------------------------------------------------------


class TestTagHasRequiredFields:
    """Verify each tag has all 8 required fields with correct types."""

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_tag_has_all_required_fields(self, contract: dict, tag_id: str) -> None:
        tag = contract["tags"][tag_id]
        for field in REQUIRED_FIELDS_PER_TAG:
            assert field in tag, f"Tag '{tag_id}' missing required field '{field}'"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_evidence_requirements_is_nonempty_list(self, contract: dict, tag_id: str) -> None:
        val = contract["tags"][tag_id]["evidence_requirements"]
        assert isinstance(val, list), f"Tag '{tag_id}' evidence_requirements must be a list"
        assert len(val) > 0, f"Tag '{tag_id}' evidence_requirements must not be empty"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_allowed_evidence_sources_is_nonempty_list(self, contract: dict, tag_id: str) -> None:
        val = contract["tags"][tag_id]["allowed_evidence_sources"]
        assert isinstance(val, list), f"Tag '{tag_id}' allowed_evidence_sources must be a list"
        assert len(val) > 0, f"Tag '{tag_id}' allowed_evidence_sources must not be empty"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_confidence_rules_is_dict(self, contract: dict, tag_id: str) -> None:
        val = contract["tags"][tag_id]["confidence_rules"]
        assert isinstance(val, dict), f"Tag '{tag_id}' confidence_rules must be a dict"
        assert "metadata_only" in val, f"Tag '{tag_id}' confidence_rules must have 'metadata_only' key"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_solver_or_tool_route_is_string(self, contract: dict, tag_id: str) -> None:
        val = contract["tags"][tag_id]["solver_or_tool_route"]
        assert isinstance(val, str), f"Tag '{tag_id}' solver_or_tool_route must be a string"
        assert len(val) > 0, f"Tag '{tag_id}' solver_or_tool_route must not be empty"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_not_sufficient_conditions_is_nonempty_list(self, contract: dict, tag_id: str) -> None:
        val = contract["tags"][tag_id]["not_sufficient_conditions"]
        assert isinstance(val, list), f"Tag '{tag_id}' not_sufficient_conditions must be a list"
        assert len(val) > 0, f"Tag '{tag_id}' not_sufficient_conditions must not be empty"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_next_minimal_task_is_string(self, contract: dict, tag_id: str) -> None:
        val = contract["tags"][tag_id]["next_minimal_task"]
        assert isinstance(val, str), f"Tag '{tag_id}' next_minimal_task must be a string"
        assert len(val) > 0, f"Tag '{tag_id}' next_minimal_task must not be empty"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_metadata_only_allowed_is_bool(self, contract: dict, tag_id: str) -> None:
        val = contract["tags"][tag_id]["metadata_only_allowed"]
        assert isinstance(val, bool), f"Tag '{tag_id}' metadata_only_allowed must be a bool"

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_static_verified_requires_is_nonempty_list(self, contract: dict, tag_id: str) -> None:
        val = contract["tags"][tag_id]["static_verified_requires"]
        assert isinstance(val, list), f"Tag '{tag_id}' static_verified_requires must be a list"
        assert len(val) > 0, f"Tag '{tag_id}' static_verified_requires must not be empty"


# ---------------------------------------------------------------------------
# 3. Filename/metadata hints are not sufficient for static_verified
# ---------------------------------------------------------------------------


class TestFilenameMetadataHintsNotSufficient:
    """Verify filename/metadata hints alone are never sufficient for static_verified."""

    def test_global_rules_exist(self, contract: dict) -> None:
        assert "global_rules" in contract, "Contract missing 'global_rules' section"

    def test_filename_hint_never_static_verified(self, contract: dict) -> None:
        rules = contract["global_rules"]
        assert rules.get("filename_hint_alone_never_static_verified") is True

    def test_solver_module_name_never_static_verified(self, contract: dict) -> None:
        rules = contract["global_rules"]
        assert rules.get("solver_module_name_alone_never_static_verified") is True

    def test_metadata_only_not_static_evidence(self, contract: dict) -> None:
        rules = contract["global_rules"]
        assert rules.get("metadata_only_is_not_static_evidence") is True

    def test_sample_name_pattern_never_upgrades_confidence(self, contract: dict) -> None:
        rules = contract["global_rules"]
        assert rules.get("sample_name_pattern_alone_never_upgrades_confidence") is True

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_not_sufficient_conditions_include_filename_hint(self, contract: dict, tag_id: str) -> None:
        """Each tag must list at least one filename/name-based condition as not sufficient."""
        not_sufficient = contract["tags"][tag_id]["not_sufficient_conditions"]
        has_filename_condition = any(
            "filename" in cond.lower() or "name" in cond.lower()
            for cond in not_sufficient
        )
        assert has_filename_condition, (
            f"Tag '{tag_id}' not_sufficient_conditions must include at least one "
            f"filename or name-based condition"
        )

    @pytest.mark.parametrize("tag_id", REQUIRED_TAG_IDS)
    def test_static_verified_requires_more_than_metadata(self, contract: dict, tag_id: str) -> None:
        """static_verified_requires must include more than just metadata."""
        requirements = contract["tags"][tag_id]["static_verified_requires"]
        # Must require at least static_triage and runtime validation
        req_text = " ".join(requirements).lower()
        assert "static_triage" in req_text or "static" in req_text, (
            f"Tag '{tag_id}' static_verified_requires must mention static triage"
        )
        assert "runtime_validation" in req_text or "runtime" in req_text, (
            f"Tag '{tag_id}' static_verified_requires must mention runtime validation"
        )


# ---------------------------------------------------------------------------
# 4. Specific types have clear evidence requirements
# ---------------------------------------------------------------------------


class TestSpecificTypeEvidenceRequirements:
    """Verify string_comparison, xor, shift_affine, lookup_table, rc4, des,
    hash_md5_sha, simple_antidebug have clear evidence requirements."""

    @pytest.mark.parametrize("tag_id", [
        "string_comparison", "xor", "shift_affine", "lookup_table",
        "rc4", "des", "hash_md5_sha", "simple_antidebug",
    ])
    def test_evidence_requirements_mention_static_analysis(self, contract: dict, tag_id: str) -> None:
        reqs = contract["tags"][tag_id]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "static" in req_text, (
            f"Tag '{tag_id}' evidence_requirements must mention static analysis"
        )

    def test_string_comparison_requires_compare_callsite(self, contract: dict) -> None:
        reqs = contract["tags"]["string_comparison"]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "compare" in req_text or "strcmp" in req_text or "memcmp" in req_text, (
            "string_comparison must require compare callsite identification"
        )

    def test_xor_requires_xor_instruction(self, contract: dict) -> None:
        reqs = contract["tags"]["xor"]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "xor" in req_text, (
            "xor must require XOR instruction/loop identification"
        )

    def test_shift_affine_requires_transform_constants(self, contract: dict) -> None:
        reqs = contract["tags"]["shift_affine"]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "shift" in req_text or "affine" in req_text, (
            "shift_affine must require shift/affine transform identification"
        )
        assert "constant" in req_text, (
            "shift_affine must require transform constants extraction"
        )

    def test_lookup_table_requires_table_access(self, contract: dict) -> None:
        reqs = contract["tags"]["lookup_table"]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "table" in req_text or "array" in req_text, (
            "lookup_table must require table/array access identification"
        )

    def test_rc4_requires_ksa_or_prga(self, contract: dict) -> None:
        reqs = contract["tags"]["rc4"]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "rc4" in req_text or "ksa" in req_text or "prga" in req_text, (
            "rc4 must require RC4 KSA/PRGA identification"
        )

    def test_des_requires_round_or_sbox(self, contract: dict) -> None:
        reqs = contract["tags"]["des"]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "des" in req_text, (
            "des must require DES round/S-box identification"
        )

    def test_hash_md5_sha_requires_input_domain(self, contract: dict) -> None:
        reqs = contract["tags"]["hash_md5_sha"]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "domain" in req_text or "input" in req_text, (
            "hash_md5_sha must require input domain identification"
        )

    def test_simple_antidebug_requires_technique_identification(self, contract: dict) -> None:
        reqs = contract["tags"]["simple_antidebug"]["evidence_requirements"]
        req_text = " ".join(reqs).lower()
        assert "anti" in req_text or "debug" in req_text, (
            "simple_antidebug must require anti-debug technique identification"
        )


# ---------------------------------------------------------------------------
# 5. Cipher/hash/anti-debug types don't upgrade based on name alone
# ---------------------------------------------------------------------------


class TestCipherHashAntidebugNoNameOnlyUpgrade:
    """Verify cipher, hash, and anti-debug types are not upgraded to
    static_verified based on sample name or solver module name alone."""

    @pytest.mark.parametrize("tag_id", ["rc4", "des", "tea_xtea", "base64", "hash_md5_sha", "simple_antidebug"])
    def test_not_sufficient_includes_filename_hint(self, contract: dict, tag_id: str) -> None:
        """Each cipher/hash/anti-debug tag must list filename-based hints as not sufficient."""
        not_sufficient = contract["tags"][tag_id]["not_sufficient_conditions"]
        not_sufficient_text = " ".join(not_sufficient).lower()
        assert "filename" in not_sufficient_text, (
            f"Tag '{tag_id}' must list filename-based condition as not sufficient"
        )

    @pytest.mark.parametrize("tag_id", ["rc4", "des", "tea_xtea", "base64", "hash_md5_sha", "simple_antidebug"])
    def test_not_sufficient_includes_solver_module_name(self, contract: dict, tag_id: str) -> None:
        """Each cipher/hash/anti-debug tag must list solver module name as not sufficient."""
        not_sufficient = contract["tags"][tag_id]["not_sufficient_conditions"]
        not_sufficient_text = " ".join(not_sufficient).lower()
        assert "solver" in not_sufficient_text or "module" in not_sufficient_text, (
            f"Tag '{tag_id}' must list solver module name as not sufficient"
        )

    @pytest.mark.parametrize("tag_id", ["rc4", "des", "tea_xtea", "base64", "hash_md5_sha", "simple_antidebug"])
    def test_confidence_metadata_only_is_low(self, contract: dict, tag_id: str) -> None:
        """Metadata-only confidence must be 'low' for cipher/hash/anti-debug types."""
        confidence = contract["tags"][tag_id]["confidence_rules"]
        assert confidence.get("metadata_only") == "low", (
            f"Tag '{tag_id}' metadata_only confidence must be 'low', got '{confidence.get('metadata_only')}'"
        )

    @pytest.mark.parametrize("tag_id", ["rc4", "des", "tea_xtea", "base64", "hash_md5_sha", "simple_antidebug"])
    def test_static_verified_requires_more_than_name(self, contract: dict, tag_id: str) -> None:
        """static_verified_requires must include at least 3 concrete evidence items."""
        requirements = contract["tags"][tag_id]["static_verified_requires"]
        assert len(requirements) >= 3, (
            f"Tag '{tag_id}' static_verified_requires must have at least 3 items, "
            f"got {len(requirements)}"
        )

    def test_rc4_not_sufficient_mentions_rc4_in_filename(self, contract: dict) -> None:
        not_sufficient = contract["tags"]["rc4"]["not_sufficient_conditions"]
        not_sufficient_text = " ".join(not_sufficient).lower()
        assert "rc4" in not_sufficient_text, (
            "rc4 not_sufficient_conditions must mention rc4 in filename"
        )

    def test_des_not_sufficient_mentions_des_in_filename(self, contract: dict) -> None:
        not_sufficient = contract["tags"]["des"]["not_sufficient_conditions"]
        not_sufficient_text = " ".join(not_sufficient).lower()
        assert "des" in not_sufficient_text, (
            "des not_sufficient_conditions must mention des in filename"
        )

    def test_hash_not_sufficient_mentions_hash_in_filename(self, contract: dict) -> None:
        not_sufficient = contract["tags"]["hash_md5_sha"]["not_sufficient_conditions"]
        not_sufficient_text = " ".join(not_sufficient).lower()
        assert "sha" in not_sufficient_text or "md5" in not_sufficient_text or "hash" in not_sufficient_text, (
            "hash_md5_sha not_sufficient_conditions must mention hash-related filename"
        )

    def test_antidebug_not_sufficient_mentions_seh_or_debug(self, contract: dict) -> None:
        not_sufficient = contract["tags"]["simple_antidebug"]["not_sufficient_conditions"]
        not_sufficient_text = " ".join(not_sufficient).lower()
        assert "seh" in not_sufficient_text or "debug" in not_sufficient_text or "anti" in not_sufficient_text, (
            "simple_antidebug not_sufficient_conditions must mention seh/debug/anti filename"
        )


# ---------------------------------------------------------------------------
# 6. Contract schema integrity
# ---------------------------------------------------------------------------


class TestContractSchemaIntegrity:
    """Verify contract schema-level integrity."""

    def test_schema_version_is_1(self, contract: dict) -> None:
        assert contract.get("schema_version") == 1

    def test_contract_name_present(self, contract: dict) -> None:
        assert "contract_name" in contract
        assert isinstance(contract["contract_name"], str)

    def test_decision_id_present(self, contract: dict) -> None:
        assert "decision_id" in contract
        assert contract["decision_id"].startswith("decision_")

    def test_round_id_present(self, contract: dict) -> None:
        assert "round_id" in contract
        assert contract["round_id"].startswith("round_")

    def test_based_on_artifacts_listed(self, contract: dict) -> None:
        artifacts = contract.get("based_on_artifacts", [])
        assert isinstance(artifacts, list)
        assert len(artifacts) > 0, "Contract must list at least one source artifact"

    def test_required_fields_per_tag_matches(self, contract: dict) -> None:
        contract_fields = set(contract.get("required_fields_per_tag", []))
        expected = set(REQUIRED_FIELDS_PER_TAG)
        assert contract_fields == expected, (
            f"required_fields_per_tag mismatch: "
            f"missing={expected - contract_fields}, "
            f"extra={contract_fields - expected}"
        )

    def test_all_tags_have_metadata_only_allowed_true(self, contract: dict) -> None:
        """All tags must allow metadata_only since no sample has been static-verified yet."""
        for tag_id, tag in contract["tags"].items():
            assert tag["metadata_only_allowed"] is True, (
                f"Tag '{tag_id}' metadata_only_allowed must be True "
                f"(no samples are static-verified yet)"
            )

    def test_all_tags_confidence_metadata_only_is_low(self, contract: dict) -> None:
        """All tags must have metadata_only confidence = 'low'."""
        for tag_id, tag in contract["tags"].items():
            assert tag["confidence_rules"]["metadata_only"] == "low", (
                f"Tag '{tag_id}' metadata_only confidence must be 'low'"
            )
