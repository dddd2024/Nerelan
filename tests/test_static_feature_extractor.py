"""Tests for static_feature_extractor module."""

import tempfile
from pathlib import Path

import pytest

from reverse_agent.static_feature_extractor import (
    CRYPTO_KEYWORDS,
    COMPARE_KEYWORDS,
    StaticFeatures,
    compute_entropy,
    detect_pe_format,
    extract_ascii_strings,
    extract_static_features,
    extract_utf16le_strings,
    features_to_dict,
    find_base64_like_strings,
    find_hex_like_constants,
    find_keyword_hits,
    get_entropy_hint,
)


class TestComputeEntropy:
    """Tests for compute_entropy function."""

    def test_entropy_empty(self):
        """Test entropy of empty data."""
        assert compute_entropy(b"") == 0.0

    def test_entropy_uniform(self):
        """Test entropy of uniform data (should be high)."""
        # All bytes 0-255 repeated
        data = bytes(range(256)) * 10
        entropy = compute_entropy(data)
        assert entropy > 7.0  # Should be close to 8

    def test_entropy_constant(self):
        """Test entropy of constant data (should be 0)."""
        data = b"\x00" * 1000
        assert compute_entropy(data) == 0.0

    def test_entropy_hello(self):
        """Test entropy of simple string."""
        data = b"hello world"
        entropy = compute_entropy(data)
        assert 2.0 < entropy < 4.0  # Moderate entropy


class TestGetEntropyHint:
    """Tests for get_entropy_hint function."""

    def test_low_entropy(self):
        """Test low entropy classification."""
        assert get_entropy_hint(3.0) == "low"
        assert get_entropy_hint(4.9) == "low"

    def test_medium_entropy(self):
        """Test medium entropy classification."""
        assert get_entropy_hint(5.0) == "medium"
        assert get_entropy_hint(6.5) == "medium"
        assert get_entropy_hint(6.9) == "medium"

    def test_high_entropy(self):
        """Test high entropy classification."""
        assert get_entropy_hint(7.0) == "high"
        assert get_entropy_hint(8.0) == "high"


class TestDetectPeFormat:
    """Tests for detect_pe_format function."""

    def test_empty_data(self):
        """Test detection on empty data."""
        assert detect_pe_format(b"") == "unknown"

    def test_mz_header_only(self):
        """Test detection of MZ header without PE."""
        data = b"MZ" + b"\x00" * 62
        assert detect_pe_format(data) == "mz"

    def test_pe_header(self):
        """Test detection of PE executable."""
        # Create minimal PE header structure
        # MZ header: first 2 bytes are "MZ", then padding
        # At offset 60-63 (0x3C-0x3F) is the PE header offset
        mz_header = b"MZ" + b"\x00" * 58  # 60 bytes total
        pe_offset = 64
        mz_header += pe_offset.to_bytes(4, "little")  # Now 64 bytes
        pe_header = b"PE\x00\x00"
        data = mz_header + pe_header
        # Ensure data is long enough
        assert len(data) >= 68  # 64 + 4 for PE header
        result = detect_pe_format(data)
        assert result == "pe", f"Expected 'pe' but got '{result}' for data length {len(data)}"

    def test_not_executable(self):
        """Test detection of non-executable data."""
        data = b"This is just some text data"
        assert detect_pe_format(data) == "unknown"


class TestExtractAsciiStrings:
    """Tests for extract_ascii_strings function."""

    def test_empty_data(self):
        """Test extraction from empty data."""
        assert extract_ascii_strings(b"") == []

    def test_simple_strings(self):
        """Test extraction of simple strings."""
        data = b"Hello\x00World\x00Test123"
        strings = extract_ascii_strings(data, min_length=4)
        assert "Hello" in strings
        assert "World" in strings
        assert "Test123" in strings

    def test_min_length_filter(self):
        """Test minimum length filtering."""
        data = b"Hi\x00Hello\x00A\x00World"
        strings = extract_ascii_strings(data, min_length=4)
        assert "Hello" in strings
        assert "World" in strings
        assert "Hi" not in strings  # Too short
        assert "A" not in strings  # Too short

    def test_max_count_limit(self):
        """Test maximum count limiting."""
        data = b"String1\x00String2\x00String3\x00String4\x00"
        strings = extract_ascii_strings(data, min_length=4, max_count=2)
        assert len(strings) <= 2


class TestExtractUtf16leStrings:
    """Tests for extract_utf16le_strings function."""

    def test_empty_data(self):
        """Test extraction from empty data."""
        assert extract_utf16le_strings(b"") == []

    def test_simple_utf16le(self):
        """Test extraction of UTF-16LE strings."""
        # "Hello" in UTF-16LE
        data = b"H\x00e\x00l\x00l\x00o\x00\x00\x00"
        strings = extract_utf16le_strings(data, min_length=4)
        assert "Hello" in strings

    def test_min_length_filter(self):
        """Test minimum length filtering."""
        # "Hi" and "Hello" in UTF-16LE
        data = b"H\x00i\x00\x00\x00H\x00e\x00l\x00l\x00o\x00"
        strings = extract_utf16le_strings(data, min_length=4)
        assert "Hello" in strings
        assert "Hi" not in strings  # Too short


class TestFindKeywordHits:
    """Tests for find_keyword_hits function."""

    def test_no_hits(self):
        """Test with no matching keywords."""
        strings = ["hello world", "test string"]
        hits = find_keyword_hits(strings, ["crypto", "encrypt"])
        assert hits == []

    def test_single_hit(self):
        """Test with one matching keyword."""
        strings = ["hello world", "this uses crypto library"]
        hits = find_keyword_hits(strings, ["crypto", "encrypt"])
        assert len(hits) == 1
        assert hits[0]["keyword"] == "crypto"

    def test_multiple_hits(self):
        """Test with multiple matching keywords."""
        strings = ["using crypto", "encrypt data", "normal string"]
        hits = find_keyword_hits(strings, ["crypto", "encrypt"])
        assert len(hits) == 2

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        strings = ["Using CRYPTO library"]
        hits = find_keyword_hits(strings, ["crypto"])
        assert len(hits) == 1


class TestFindHexLikeConstants:
    """Tests for find_hex_like_constants function."""

    def test_no_hex(self):
        """Test with no hex sequences."""
        data = b"hello world normal text"
        constants = find_hex_like_constants(data)
        assert constants == []

    def test_md5_like(self):
        """Test detection of MD5-like hex string."""
        # 32 hex chars = MD5 length
        data = b"d41d8cd98f00b204e9800998ecf8427e"
        constants = find_hex_like_constants(data)
        assert len(constants) == 1
        assert constants[0]["kind"] == "md5_like"

    def test_sha1_like(self):
        """Test detection of SHA1-like hex string."""
        # 40 hex chars = SHA1 length
        data = b"da39a3ee5e6b4b0d3255bfef95601890afd80709"
        constants = find_hex_like_constants(data)
        assert len(constants) == 1
        assert constants[0]["kind"] == "sha1_like"

    def test_sha256_like(self):
        """Test detection of SHA256-like hex string."""
        # 64 hex chars = SHA256 length
        data = b"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        constants = find_hex_like_constants(data)
        assert len(constants) == 1
        assert constants[0]["kind"] == "sha256_like"


class TestFindBase64LikeStrings:
    """Tests for find_base64_like_strings function."""

    def test_no_base64(self):
        """Test with no base64-like strings."""
        strings = ["hello world", "test@#$%"]
        candidates = find_base64_like_strings(strings)
        assert candidates == []

    def test_valid_base64(self):
        """Test detection of valid base64."""
        strings = ["SGVsbG8gV29ybGQh", "aGVsbG8gd29ybGQ="]
        candidates = find_base64_like_strings(strings, min_length=8)
        # Both should be valid base64 (length multiple of 4, valid chars)
        assert len(candidates) == 2, f"Expected 2 candidates, got {len(candidates)}: {candidates}"

    def test_invalid_length(self):
        """Test that invalid length strings are rejected."""
        # Length not multiple of 4
        strings = ["SGVsbG8gV29ybGQ"]
        candidates = find_base64_like_strings(strings)
        assert candidates == []


class TestExtractStaticFeatures:
    """Tests for extract_static_features function."""

    def test_nonexistent_file(self):
        """Test extraction from non-existent file."""
        features = extract_static_features(Path("/nonexistent/file.exe"))
        assert features.format == "unknown"
        assert features.file_size == 0

    def test_empty_file(self):
        """Test extraction from empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"")
            temp_path = Path(f.name)

        try:
            features = extract_static_features(temp_path)
            assert features.format == "unknown"
            assert features.file_size == 0
        finally:
            temp_path.unlink()

    def test_text_file(self):
        """Test extraction from text file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Hello World\nThis is a test\n")
            temp_path = Path(f.name)

        try:
            features = extract_static_features(temp_path)
            assert features.format == "unknown"
            assert features.file_size > 0
            assert "Hello World" in features.ascii_strings_sample
        finally:
            temp_path.unlink()

    def test_crypto_keywords_detection(self):
        """Test detection of crypto keywords."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            # Write text with crypto keywords that will be detected
            f.write("This file uses RC4 encryption and MD5 hashing\n")
            temp_path = Path(f.name)

        try:
            features = extract_static_features(temp_path)
            crypto_keywords = [h["keyword"] for h in features.crypto_hints]
            # Check that at least one crypto keyword is detected
            expected_keywords = {"rc4", "encrypt", "md5", "hash"}
            found = set(crypto_keywords) & expected_keywords
            assert len(found) > 0, f"Expected to find crypto keywords in {crypto_keywords}"
        finally:
            temp_path.unlink()

    def test_compare_keywords_detection(self):
        """Test detection of compare keywords."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("strcmp comparison password input flag\n")
            temp_path = Path(f.name)

        try:
            features = extract_static_features(temp_path)
            compare_keywords = [h["keyword"] for h in features.compare_hints]
            assert len(compare_keywords) > 0
        finally:
            temp_path.unlink()


class TestFeaturesToDict:
    """Tests for features_to_dict function."""

    def test_basic_conversion(self):
        """Test basic conversion to dictionary."""
        features = StaticFeatures(
            format="pe",
            file_size=1000,
            entropy_hint="medium",
        )
        d = features_to_dict(features)
        assert d["format"] == "pe"
        assert d["file_size"] == 1000
        assert d["entropy_hint"] == "medium"

    def test_list_truncation(self):
        """Test that lists are truncated in output."""
        features = StaticFeatures(
            ascii_strings_sample=["string"] * 100,
            keyword_hits=[{"keyword": "test"}] * 50,
        )
        d = features_to_dict(features)
        assert len(d["ascii_strings_sample"]) <= 20
        assert len(d["keyword_hits"]) <= 20


class TestRealSamples:
    """Tests against real corpus samples (if available)."""

    def test_extract_from_real_samples(self):
        """Test extraction from real corpus samples."""
        corpus_dir = Path("sample_corpus/reverse")
        if not corpus_dir.exists():
            pytest.skip("Real corpus not found")

        sample_dirs = [d for d in corpus_dir.iterdir() if d.is_dir()]
        if not sample_dirs:
            pytest.skip("No samples found in corpus")

        for sample_dir in sample_dirs[:2]:  # Test first 2 samples
            sample_path = sample_dir / "sample.exe"
            if not sample_path.exists():
                continue

            features = extract_static_features(sample_path)

            # Basic checks
            assert features.file_size > 0
            assert features.format in ["pe", "mz", "unknown"]

            # PE files should have strings
            if features.format == "pe":
                assert len(features.ascii_strings_sample) > 0
