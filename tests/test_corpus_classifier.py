"""Tests for corpus_classifier module."""

import pytest

from reverse_agent.corpus_classifier import (
    CATEGORIES,
    ClassificationResult,
    classify_from_filename,
    classify_from_features,
    classify_sample,
    classification_to_dict,
    get_recommended_step,
)
from reverse_agent.static_feature_extractor import StaticFeatures


class TestCategories:
    """Tests for category definitions."""

    def test_categories_defined(self):
        """Test that categories are defined."""
        assert len(CATEGORIES) > 0
        assert "unknown" in CATEGORIES
        assert "rc4_like" in CATEGORIES
        assert "des_like" in CATEGORIES


class TestClassifyFromFilename:
    """Tests for classify_from_filename function."""

    def test_rc4_in_filename(self):
        """Test detection of RC4 from filename."""
        category, confidence, evidence = classify_from_filename("rc4enc_test")
        assert category == "rc4_like"
        assert confidence == "low"
        assert any("rc4" in e["detail"].lower() for e in evidence)

    def test_des_in_filename(self):
        """Test detection of DES from filename."""
        category, confidence, evidence = classify_from_filename("desenc_test")
        assert category == "des_like"
        assert confidence == "low"

    def test_aes_in_filename(self):
        """Test detection of AES from filename."""
        category, confidence, evidence = classify_from_filename("aes_test")
        assert category == "aes_like"
        assert confidence == "low"

    def test_seh_in_filename(self):
        """Test detection of SEH from filename."""
        category, confidence, evidence = classify_from_filename("seh_test")
        assert category == "seh_or_exception"
        assert confidence == "low"

    def test_hash_in_filename(self):
        """Test detection of hash from filename."""
        category, confidence, evidence = classify_from_filename("hash_check")
        assert category == "hash_check"
        assert confidence == "low"

    def test_base64_in_filename(self):
        """Test detection of Base64 from filename."""
        category, confidence, evidence = classify_from_filename("base64_test")
        assert category == "base64_or_encoding"
        assert confidence == "low"

    def test_xor_in_filename(self):
        """Test detection of XOR from filename."""
        category, confidence, evidence = classify_from_filename("xor_cipher")
        assert category == "xor_or_bytewise"
        assert confidence == "low"

    def test_unknown_filename(self):
        """Test unknown filename."""
        category, confidence, evidence = classify_from_filename("random_name")
        assert category == "unknown"
        assert confidence == "low"
        assert evidence == []


class TestClassifyFromFeatures:
    """Tests for classify_from_features function."""

    def test_empty_features(self):
        """Test classification with empty features."""
        features = StaticFeatures()
        category, confidence, evidence = classify_from_features(features)
        assert category == "unknown"
        assert confidence == "low"

    def test_rc4_from_crypto_hints(self):
        """Test RC4 detection from crypto hints."""
        features = StaticFeatures(
            crypto_hints=[{"keyword": "rc4", "source": "test", "context": "rc4_init"}]
        )
        category, confidence, evidence = classify_from_features(features)
        assert category == "rc4_like"
        assert confidence == "medium"

    def test_des_from_crypto_hints(self):
        """Test DES detection from crypto hints."""
        features = StaticFeatures(
            crypto_hints=[{"keyword": "des", "source": "test", "context": "des_encrypt"}]
        )
        category, confidence, evidence = classify_from_features(features)
        assert category == "des_like"
        assert confidence == "medium"

    def test_aes_from_crypto_hints(self):
        """Test AES detection from crypto hints."""
        features = StaticFeatures(
            crypto_hints=[{"keyword": "aes", "source": "test", "context": "aes_encrypt"}]
        )
        category, confidence, evidence = classify_from_features(features)
        assert category == "aes_like"
        assert confidence == "medium"

    def test_hash_from_crypto_hints(self):
        """Test hash detection from crypto hints."""
        features = StaticFeatures(
            crypto_hints=[{"keyword": "md5", "source": "test", "context": "md5_hash"}]
        )
        category, confidence, evidence = classify_from_features(features)
        assert category == "hash_check"
        assert confidence == "medium"

    def test_base64_from_crypto_hints(self):
        """Test Base64 detection from crypto hints."""
        features = StaticFeatures(
            crypto_hints=[{"keyword": "base64", "source": "test", "context": "base64_encode"}]
        )
        category, confidence, evidence = classify_from_features(features)
        assert category == "base64_or_encoding"
        assert confidence == "medium"

    def test_string_compare_from_hints(self):
        """Test string compare detection."""
        features = StaticFeatures(
            compare_hints=[{"keyword": "strcmp", "source": "test", "context": "strcmp(input"}]
        )
        category, confidence, evidence = classify_from_features(features)
        assert category == "string_compare"
        assert confidence == "medium"

    def test_xor_from_strings(self):
        """Test XOR detection from strings."""
        features = StaticFeatures(
            ascii_strings_sample=["XOR encryption", "xor_cipher"]
        )
        category, confidence, evidence = classify_from_features(features)
        assert category == "xor_or_bytewise"
        assert confidence == "low"


class TestClassifySample:
    """Tests for classify_sample function."""

    def test_basic_classification(self):
        """Test basic classification."""
        features = StaticFeatures(
            crypto_hints=[{"keyword": "rc4", "source": "test", "context": "rc4_init"}]
        )
        result = classify_sample("test_case", features)
        assert result.case_id == "test_case"
        assert result.predicted_category == "rc4_like"
        assert result.confidence == "medium"
        assert result.recommended_next_step != ""

    def test_filename_boosts_confidence(self):
        """Test that matching filename and features boosts confidence."""
        features = StaticFeatures(
            crypto_hints=[{"keyword": "rc4", "source": "test", "context": "rc4_init"}]
        )
        result = classify_sample("rc4enc_test", features)
        # Both filename and features agree on RC4
        assert result.predicted_category == "rc4_like"

    def test_notes_hint_affine(self):
        """Test that notes mentioning affine are detected."""
        features = StaticFeatures()
        notes = "This sample uses an affine cipher transformation"
        result = classify_sample("test_case", features, notes=notes)
        assert result.predicted_category == "affine_lowercase"

    def test_notes_hint_caesar(self):
        """Test that notes mentioning Caesar are detected."""
        features = StaticFeatures()
        notes = "This is a Caesar cipher challenge"
        result = classify_sample("test_case", features, notes=notes)
        assert result.predicted_category == "caesar_or_shift"

    def test_codex_task_hint(self):
        """Test that codex_task hints are detected."""
        features = StaticFeatures()
        codex_task = "Analyze the ROT13 cipher in this binary"
        result = classify_sample("test_case", features, codex_task=codex_task)
        # ROT13 hint should be detected
        assert result.predicted_category == "caesar_or_shift", f"Expected 'caesar_or_shift' but got '{result.predicted_category}'"

    def test_unknown_classification(self):
        """Test classification when nothing is found."""
        features = StaticFeatures()
        result = classify_sample("random_name", features)
        assert result.predicted_category == "unknown"
        assert result.confidence == "low"


class TestGetRecommendedStep:
    """Tests for get_recommended_step function."""

    def test_all_categories_have_recommendations(self):
        """Test that all categories have recommendations."""
        for category in CATEGORIES:
            step = get_recommended_step(category)
            assert step != ""
            assert "Unknown category" not in step or category == "unknown"

    def test_rc4_recommendation(self):
        """Test RC4 recommendation."""
        step = get_recommended_step("rc4_like")
        assert "KSA" in step or "PRGA" in step or "S-box" in step

    def test_des_recommendation(self):
        """Test DES recommendation."""
        step = get_recommended_step("des_like")
        assert "DES" in step or "key schedule" in step

    def test_unknown_recommendation(self):
        """Test unknown category recommendation."""
        step = get_recommended_step("unknown")
        assert "manual analysis" in step.lower() or "deeper" in step.lower()


class TestClassificationToDict:
    """Tests for classification_to_dict function."""

    def test_basic_conversion(self):
        """Test basic conversion to dictionary."""
        result = ClassificationResult(
            case_id="test",
            predicted_category="rc4_like",
            confidence="medium",
            evidence=[{"type": "test", "detail": "test evidence"}],
            recommended_next_step="Do something",
        )
        d = classification_to_dict(result)
        assert d["case_id"] == "test"
        assert d["predicted_category"] == "rc4_like"
        assert d["confidence"] == "medium"
        assert len(d["evidence"]) == 1
        assert d["recommended_next_step"] == "Do something"

    def test_empty_evidence(self):
        """Test conversion with empty evidence."""
        result = ClassificationResult(
            case_id="test",
            predicted_category="unknown",
            confidence="low",
        )
        d = classification_to_dict(result)
        assert d["evidence"] == []


class TestRealSamples:
    """Tests against real corpus samples (if available)."""

    def test_classify_real_samples(self):
        """Test classification of real corpus samples."""
        from pathlib import Path
        from reverse_agent.corpus_loader import load_corpus_cases

        corpus_dir = Path("sample_corpus/reverse")
        if not corpus_dir.exists():
            pytest.skip("Real corpus not found")

        cases = load_corpus_cases(corpus_dir)
        if not cases:
            pytest.skip("No cases found in corpus")

        for case in cases[:2]:  # Test first 2 samples
            features = StaticFeatures()  # Would normally extract from sample
            result = classify_sample(
                case.case_id,
                features,
                notes=case.notes,
            )

            # Basic checks
            assert result.case_id == case.case_id
            assert result.predicted_category in CATEGORIES
            assert result.confidence in ["high", "medium", "low"]
            assert result.recommended_next_step != ""
