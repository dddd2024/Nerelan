"""Tests for simple_static_patterns module."""

import pytest

from reverse_agent.simple_static_patterns import (
    detect_hex_digest_kind,
    encode_affine_lowercase,
    encode_caesar_lowercase,
    find_affine_candidates,
    is_valid_lowercase_only,
    modular_inverse,
    solve_affine_lowercase,
    solve_caesar_lowercase,
    xor_bytes,
    xor_hex_string,
)


class TestModularInverse:
    """Tests for modular_inverse function."""

    def test_inverse_mod_26_valid(self):
        """Test valid inverses modulo 26."""
        # 5 * 21 = 105 = 1 mod 26
        assert modular_inverse(5, 26) == 21
        # 3 * 9 = 27 = 1 mod 26
        assert modular_inverse(3, 26) == 9
        # 1 * 1 = 1 mod 26
        assert modular_inverse(1, 26) == 1

    def test_inverse_mod_26_invalid(self):
        """Test that invalid values raise ValueError."""
        # 2 has no inverse mod 26 (gcd(2, 26) = 2)
        with pytest.raises(ValueError):
            modular_inverse(2, 26)
        # 13 has no inverse mod 26 (gcd(13, 26) = 13)
        with pytest.raises(ValueError):
            modular_inverse(13, 26)


class TestAffineLowercase:
    """Tests for affine cipher functions with lowercase alphabet."""

    def test_solve_affine_known_case(self):
        """Test solving affine cipher with known case from cpp_6af7c7f1.

        From sample cpp_6af7c7f1:
        - Target: "qvldxt"
        - Transform: y = (5x + 7) mod 26
        - Expected: "higuys"
        """
        result = solve_affine_lowercase("qvldxt", a=5, b=7)
        assert result == "higuys"

    def test_encode_affine_round_trip(self):
        """Test that encode and solve are inverses."""
        plaintext = "higuys"
        encoded = encode_affine_lowercase(plaintext, a=5, b=7)
        assert encoded == "qvldxt"

        # Solve should recover original
        recovered = solve_affine_lowercase(encoded, a=5, b=7)
        assert recovered == plaintext

    def test_solve_affine_invalid_target(self):
        """Test that non-lowercase targets return None."""
        # Uppercase should return None
        assert solve_affine_lowercase("QVLDXT", a=5, b=7) is None
        # Mixed case should return None
        assert solve_affine_lowercase("Qvldxt", a=5, b=7) is None
        # Digits should return None
        assert solve_affine_lowercase("qvld1t", a=5, b=7) is None
        # Empty string should return None
        assert solve_affine_lowercase("", a=5, b=7) is None

    def test_solve_affine_invalid_multiplier(self):
        """Test that non-coprime multiplier raises ValueError."""
        # 2 and 26 are not coprime
        with pytest.raises(ValueError):
            solve_affine_lowercase("abc", a=2, b=1)

    def test_encode_affine_invalid_input(self):
        """Test that non-lowercase input returns None."""
        assert encode_affine_lowercase("Hello", a=5, b=7) is None
        assert encode_affine_lowercase("higuys1", a=5, b=7) is None
        assert encode_affine_lowercase("", a=5, b=7) is None


class TestCaesarCipher:
    """Tests for Caesar/ROT cipher functions."""

    def test_solve_caesar_basic(self):
        """Test basic Caesar decryption."""
        # "bcd" with shift 1 -> "abc"
        assert solve_caesar_lowercase("bcd", shift=1) == "abc"
        # "abc" with shift 3 -> "xyz"
        assert solve_caesar_lowercase("abc", shift=3) == "xyz"

    def test_encode_caesar_basic(self):
        """Test basic Caesar encryption."""
        assert encode_caesar_lowercase("abc", shift=1) == "bcd"
        assert encode_caesar_lowercase("xyz", shift=3) == "abc"

    def test_caesar_round_trip(self):
        """Test that encode and solve are inverses for Caesar."""
        plaintext = "helloworld"
        shift = 13  # ROT13
        encoded = encode_caesar_lowercase(plaintext, shift)
        recovered = solve_caesar_lowercase(encoded, shift)
        assert recovered == plaintext

    def test_caesar_rot13(self):
        """Test ROT13 (shift 13) is self-inverse."""
        plaintext = "uryyb"
        # ROT13 applied twice returns original
        encoded = encode_caesar_lowercase(plaintext, 13)
        recovered = encode_caesar_lowercase(encoded, 13)
        assert recovered == plaintext


class TestXorOperations:
    """Tests for XOR operations."""

    def test_xor_bytes_single_key(self):
        """Test XOR with single-byte key."""
        data = b"hello"
        key = b"k"
        result = xor_bytes(data, key)
        # XOR is self-inverse: result XOR key = original
        recovered = xor_bytes(result, key)
        assert recovered == data

    def test_xor_bytes_repeating_key(self):
        """Test XOR with repeating multi-byte key."""
        data = b"hello world"
        key = b"key"
        result = xor_bytes(data, key)
        recovered = xor_bytes(result, key)
        assert recovered == data

    def test_xor_bytes_empty_key(self):
        """Test XOR with empty key returns original data."""
        data = b"hello"
        result = xor_bytes(data, b"")
        assert result == data

    def test_xor_hex_string_valid(self):
        """Test XOR with valid hex string."""
        # "hello" hex encoded
        hex_str = "68656c6c6f"
        key = b"k"
        result = xor_hex_string(hex_str, key)
        assert result is not None
        # Verify round-trip
        recovered = xor_bytes(result, key)
        assert recovered.hex() == hex_str

    def test_xor_hex_string_invalid(self):
        """Test XOR with invalid hex string returns None."""
        assert xor_hex_string("nothex", b"k") is None
        assert xor_hex_string("xyz", b"k") is None


class TestHexDigestDetection:
    """Tests for hex digest detection."""

    def test_detect_md5(self):
        """Test MD5 digest detection (32 hex chars)."""
        # MD5 of empty string
        md5_hash = "d41d8cd98f00b204e9800998ecf8427e"
        assert detect_hex_digest_kind(md5_hash) == "md5"
        # With 0x prefix
        assert detect_hex_digest_kind("0x" + md5_hash) == "md5"

    def test_detect_sha1(self):
        """Test SHA1 digest detection (40 hex chars)."""
        # SHA1 of empty string
        sha1_hash = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        assert detect_hex_digest_kind(sha1_hash) == "sha1"

    def test_detect_sha256(self):
        """Test SHA256 digest detection (64 hex chars)."""
        # SHA256 of empty string
        sha256_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert detect_hex_digest_kind(sha256_hash) == "sha256"

    def test_detect_invalid_length(self):
        """Test that non-standard lengths return None."""
        assert detect_hex_digest_kind("abcd") is None
        assert detect_hex_digest_kind("a" * 31) is None
        assert detect_hex_digest_kind("a" * 33) is None

    def test_detect_invalid_chars(self):
        """Test that non-hex chars return None."""
        assert detect_hex_digest_kind("ghijklmnopqrstuvwxyz1234567890ab") is None
        assert detect_hex_digest_kind("d41d8cd98f00b204e9800998ecf8427g") is None


class TestValidationHelpers:
    """Tests for validation helper functions."""

    def test_is_valid_lowercase_only_valid(self):
        """Test validation of lowercase strings."""
        assert is_valid_lowercase_only("abc") is True
        assert is_valid_lowercase_only("higuys") is True
        assert is_valid_lowercase_only("qvldxt") is True

    def test_is_valid_lowercase_only_invalid(self):
        """Test rejection of non-lowercase strings."""
        assert is_valid_lowercase_only("ABC") is False
        assert is_valid_lowercase_only("Abc") is False
        assert is_valid_lowercase_only("abc1") is False
        assert is_valid_lowercase_only("abc def") is False
        assert is_valid_lowercase_only("") is False


class TestAffineCandidates:
    """Tests for affine candidate finder."""

    def test_find_affine_candidates_known_case(self):
        """Test finding candidates for known case."""
        # "qvldxt" from cpp_6af7c7f1 with a=5, b=7
        candidates = find_affine_candidates("qvldxt")
        # Should find (5, 7, "higuys")
        assert (5, 7, "higuys") in candidates

    def test_find_affine_candidates_returns_valid_only(self):
        """Test that all returned candidates are valid."""
        candidates = find_affine_candidates("abc")
        for a, b, plaintext in candidates:
            # Verify round-trip
            encoded = encode_affine_lowercase(plaintext, a, b)
            assert encoded == "abc"


class TestCpp6af7c7f1Evidence:
    """Tests verifying the evidence from sample cpp_6af7c7f1."""

    def test_cpp_6af7c7f1_affine_pattern(self):
        """Verify the affine pattern from cpp_6af7c7f1 sample.

        This test documents the evidence from the sample:
        - Target string: "qvldxt"
        - Transform: y = (5x + 7) mod 26
        - Inverse: x = 21 * (y - 7) mod 26
        - Result: "higuys"
        """
        target = "qvldxt"
        a, b = 5, 7

        # Verify inverse calculation
        a_inv = modular_inverse(a, 26)
        assert a_inv == 21  # 5 * 21 = 105 = 1 mod 26

        # Solve
        result = solve_affine_lowercase(target, a, b)
        assert result == "higuys"

        # Verify by re-encoding
        encoded = encode_affine_lowercase(result, a, b)
        assert encoded == target

    def test_cpp_6af7c7f1_rejects_non_lowercase(self):
        """Verify that non-lowercase input would be rejected."""
        # The sample only accepts lowercase a-z input
        assert is_valid_lowercase_only("higuys") is True
        assert is_valid_lowercase_only("HiGuys") is False
        assert is_valid_lowercase_only("HIGUYS") is False
