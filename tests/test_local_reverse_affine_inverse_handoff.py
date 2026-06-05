"""Tests for affine inverse handoff generator."""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pytest

from reverse_agent.local_reverse_affine_inverse_handoff import (
    TRUSTED_CIPHERTEXT_SOURCES,
    _build_per_char_mapping,
    _check_ciphertext_provenance,
    _decrypt_affine,
    _extended_gcd,
    _mod_inverse,
    run_affine_inverse_handoff,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_affine_artifact(
    *,
    a: int = 5,
    b: int = 5,
    modulus: int = 26,
    min_char: int = 97,
    max_char: int = 122,
    expected_ciphertext: str | None = None,
    ciphertext_source: str | None = None,
    ciphertext_provenance: str | None = None,
    ciphertext_origin: str | None = None,
) -> dict:
    """Build a minimal affine artifact dict for testing."""
    artifact: dict = {
        "sample_id": "test_sample",
        "post_scanf_flow_evidence": {
            "transform_loop": {
                "affine_parameters": {"a": a, "b": b, "modulus": modulus},
            },
            "input_validation_loop": {
                "range_check": {"min_char": min_char, "max_char": max_char},
            },
        },
    }
    if expected_ciphertext is not None:
        artifact["expected_ciphertext"] = expected_ciphertext
    if ciphertext_source is not None:
        artifact["expected_ciphertext_source"] = ciphertext_source
    if ciphertext_provenance is not None:
        artifact["expected_ciphertext_provenance"] = ciphertext_provenance
    if ciphertext_origin is not None:
        artifact["expected_ciphertext_origin"] = ciphertext_origin
    return artifact


def _write_and_run(artifact: dict) -> dict:
    """Write artifact to temp file, run handoff, return result."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as inf:
        json.dump(artifact, inf)
        in_path = Path(inf.name)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as outf:
        out_path = Path(outf.name)

    try:
        result = run_affine_inverse_handoff(in_path, out_path)
    finally:
        in_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)

    return result


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

class TestExtendedGcd:
    def test_gcd_5_26(self):
        g, x, y = _extended_gcd(5, 26)
        assert g == 1
        assert 5 * x + 26 * y == 1

    def test_gcd_4_26(self):
        g, _, _ = _extended_gcd(4, 26)
        assert g == 2  # not coprime


class TestModInverse:
    def test_inverse_5_mod_26(self):
        assert _mod_inverse(5, 26) == 21

    def test_inverse_non_coprime(self):
        assert _mod_inverse(4, 26) is None

    def test_inverse_verify(self):
        inv = _mod_inverse(5, 26)
        assert inv is not None
        assert (5 * inv) % 26 == 1


# ---------------------------------------------------------------------------
# Per-char mapping
# ---------------------------------------------------------------------------

class TestPerCharMapping:
    def test_mapping_length(self):
        mapping = _build_per_char_mapping(5, 5, 21, 26)
        assert len(mapping) == 26

    def test_mapping_roundtrip(self):
        mapping = _build_per_char_mapping(5, 5, 21, 26)
        for entry in mapping:
            plain = entry["plain"]
            cipher = entry["cipher"]
            # Verify forward: c = (5*p + 5) % 26
            p = ord(plain) - 97
            expected_c = (5 * p + 5) % 26
            assert cipher == chr(expected_c + 97)

    def test_a_is_5(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["forward_transform"]["a"] == 5

    def test_b_is_5(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["forward_transform"]["b"] == 5

    def test_modulus_is_26(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["domain"]["modulus"] == 26


# ---------------------------------------------------------------------------
# Inverse computation
# ---------------------------------------------------------------------------

class TestInverseA:
    def test_inverse_a_21(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["inverse_transform"]["inverse_a"] == 21

    def test_gcd_is_1(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["inverse_transform"]["gcd_a_modulus"] == 1


# ---------------------------------------------------------------------------
# Decrypt
# ---------------------------------------------------------------------------

class TestDecryptAffine:
    def test_known_pair(self):
        # a=5, b=5: 'a'(0) -> (5*0+5)%26=5 -> 'f'
        # inverse: 'f'(5) -> 21*(5-5)%26=0 -> 'a'
        assert _decrypt_affine("f", 21, 5, 26) == "a"

    def test_word(self):
        # Encrypt 'hello': h(7)->(35+5)%26=14->'o', e(4)->(20+5)%26=25->'z',
        # l(11)->(55+5)%26=8->'i', l->'i', o(14)->(70+5)%26=23->'x'
        # So 'hello' -> 'oziix'
        cipher = _decrypt_affine("oziix", 21, 5, 26)
        assert cipher == "hello"


# ---------------------------------------------------------------------------
# Provenance gate
# ---------------------------------------------------------------------------

class TestProvenanceGate:
    def test_no_ciphertext_blocked(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["status"] == "BLOCKED"
        assert result["blocked_reason"] == "MISSING_EXPECTED_CIPHERTEXT"
        assert result["candidate"] is None
        assert result["ciphertext_provenance"] is None

    def test_ciphertext_no_source_blocked(self):
        result = _write_and_run(_make_affine_artifact(expected_ciphertext="oziiix"))
        assert result["status"] == "BLOCKED"
        assert result["blocked_reason"] == "UNTRUSTED_EXPECTED_CIPHERTEXT_SOURCE"
        assert result["candidate"] is None
        assert result["ciphertext_provenance"] is None

    def test_ciphertext_untrusted_source_blocked(self):
        result = _write_and_run(
            _make_affine_artifact(
                expected_ciphertext="oziiix",
                ciphertext_source="random_internet_source",
            )
        )
        assert result["status"] == "BLOCKED"
        assert result["blocked_reason"] == "UNTRUSTED_EXPECTED_CIPHERTEXT_SOURCE"
        assert result["candidate"] is None

    def test_ciphertext_challenge_statement_ready(self):
        result = _write_and_run(
            _make_affine_artifact(
                expected_ciphertext="oziix",
                ciphertext_source="challenge_statement",
            )
        )
        assert result["status"] == "READY"
        assert result["candidate"] == "hello"
        assert result["ciphertext_provenance"] == "challenge_statement"

    def test_ciphertext_user_provided_ready(self):
        result = _write_and_run(
            _make_affine_artifact(
                expected_ciphertext="oziix",
                ciphertext_provenance="user_provided",
            )
        )
        assert result["status"] == "READY"
        assert result["candidate"] == "hello"
        assert result["ciphertext_provenance"] == "user_provided"

    def test_ciphertext_allowed_static_ready(self):
        result = _write_and_run(
            _make_affine_artifact(
                expected_ciphertext="oziix",
                ciphertext_origin="allowed_static_evidence",
            )
        )
        assert result["status"] == "READY"
        assert result["candidate"] == "hello"
        assert result["ciphertext_provenance"] == "allowed_static_evidence"


class TestCheckCiphertextProvenance:
    def test_no_field(self):
        assert _check_ciphertext_provenance({}) is None

    def test_empty_string(self):
        assert _check_ciphertext_provenance({"expected_ciphertext_source": ""}) is None

    def test_untrusted(self):
        assert _check_ciphertext_provenance({"expected_ciphertext_source": "untrusted"}) is None

    def test_challenge_statement(self):
        assert _check_ciphertext_provenance({"expected_ciphertext_source": "challenge_statement"}) == "challenge_statement"

    def test_provenance_key(self):
        assert _check_ciphertext_provenance({"expected_ciphertext_provenance": "user_provided"}) == "user_provided"

    def test_origin_key(self):
        assert _check_ciphertext_provenance({"expected_ciphertext_origin": "allowed_static_evidence"}) == "allowed_static_evidence"

    def test_whitespace_trimmed(self):
        assert _check_ciphertext_provenance({"expected_ciphertext_source": "  challenge_statement  "}) == "challenge_statement"


# ---------------------------------------------------------------------------
# Domain validation
# ---------------------------------------------------------------------------

class TestDomainValidation:
    def test_unsupported_domain_uppercase(self):
        result = _write_and_run(_make_affine_artifact(min_char=65, max_char=90))
        assert result["status"] == "BLOCKED"
        assert result["blocked_reason"] == "UNSUPPORTED_DOMAIN"

    def test_unsupported_domain_mixed(self):
        result = _write_and_run(_make_affine_artifact(min_char=32, max_char=126))
        assert result["status"] == "BLOCKED"
        assert result["blocked_reason"] == "UNSUPPORTED_DOMAIN"


# ---------------------------------------------------------------------------
# Non-invertible multiplier
# ---------------------------------------------------------------------------

class TestNonInvertible:
    def test_a_4_mod_26(self):
        result = _write_and_run(_make_affine_artifact(a=4, b=5, modulus=26))
        assert result["status"] == "BLOCKED"
        assert result["blocked_reason"] == "NON_INVERTIBLE_AFFINE_MULTIPLIER"
        assert result["candidate"] is None

    def test_a_2_mod_26(self):
        result = _write_and_run(_make_affine_artifact(a=2, b=3, modulus=26))
        assert result["status"] == "BLOCKED"
        assert result["blocked_reason"] == "NON_INVERTIBLE_AFFINE_MULTIPLIER"


# ---------------------------------------------------------------------------
# Static-only flags
# ---------------------------------------------------------------------------

class TestStaticOnlyFlags:
    def test_executed_sample_false(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["executed_sample"] is False

    def test_static_only_true(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["static_only"] is True

    def test_runtime_validated_false(self):
        result = _write_and_run(_make_affine_artifact())
        assert result["runtime_validated"] is False


# ---------------------------------------------------------------------------
# Missing affine parameters
# ---------------------------------------------------------------------------

class TestMissingParameters:
    def test_no_affine_params(self):
        artifact = {
            "sample_id": "test_sample",
            "post_scanf_flow_evidence": {
                "transform_loop": {},
                "input_validation_loop": {"range_check": {"min_char": 97, "max_char": 122}},
            },
        }
        result = _write_and_run(artifact)
        assert result["status"] == "BLOCKED"
        assert result["blocked_reason"] == "MISSING_AFFINE_PARAMETERS"
