"""TEST ONLY provider/key: synthetic HMAC proof is not production attestation."""

from dataclasses import FrozenInstanceError, fields, replace
import hashlib
import hmac

import pytest

from reverse_agent.platform_v1.terminal_receipt import (
    OriginalBinding, TerminalReceipt, verify_terminal_receipt,
)


BINDING = OriginalBinding(
    "task", "run", "coordinator", 7, 100, "window", 100, "policy", 2,
    "digest", "executor", "execution", "binding", "worker", 3, 100,
    "task", 7, "window", 50, 60, "remote-operation",
)
TEST_KEY = b"fixture-only-not-a-provider-key"


class TestOnlyAnchor:
    def verify(self, provider, key_id, payload, signature):
        return (provider == "test-only" and key_id == "fixture"
                and hmac.compare_digest(signature, hmac.digest(TEST_KEY, payload, hashlib.sha256)))


class TestOnlySource:
    __test__ = False

    def __init__(self, change=lambda r: r, *, sign=True):
        self.change = change
        self.sign = sign

    def resolve(self, binding, challenge):
        receipt = self.change(TerminalReceipt(
            binding, "test-only", "fixture", "receipt", challenge, 1000, 2000,
            "SUCCEEDED", b"",
        ))
        if self.sign:
            receipt = replace(receipt, signature=hmac.digest(
                TEST_KEY, receipt.signing_bytes(), hashlib.sha256,
            ))
        return receipt


def classify(source=None, anchor=None, binding=BINDING):
    return verify_terminal_receipt(binding, source=source, anchor=anchor, now_ms=1500)


def assert_unknown(result):
    assert result.classification == "UNKNOWN"
    assert result.receipt is None
    assert result.budget_state == "UNKNOWN"
    assert result.release_allowed is False


@pytest.mark.parametrize("outcome", ["SUCCEEDED", "FAILED", "CANCELLED"])
def test_positive_requires_test_only_cryptographic_proof(outcome):
    result = classify(TestOnlySource(lambda r: replace(r, outcome=outcome)), TestOnlyAnchor())
    assert result.classification == "TERMINAL_VERIFIED"
    assert result.receipt.binding == BINDING
    assert result.budget_state == "UNKNOWN"
    assert result.release_allowed is False
    with pytest.raises(FrozenInstanceError):
        result.receipt.binding.claim_epoch = 8


@pytest.mark.parametrize("field", fields(BINDING), ids=lambda f: f.name)
def test_every_original_binding_mismatch_rejected_even_with_valid_signature(field):
    value = getattr(BINDING, field.name)
    changed = replace(BINDING, **{field.name: value + 1 if type(value) is int else value + "-other"})
    assert_unknown(classify(TestOnlySource(lambda r: replace(r, binding=changed)), TestOnlyAnchor()))


@pytest.mark.parametrize("field", fields(BINDING), ids=lambda f: f.name)
def test_every_missing_original_binding_rejected(field):
    assert_unknown(classify(TestOnlySource(), TestOnlyAnchor(), replace(BINDING, **{field.name: None})))


@pytest.mark.parametrize("changes", [
    {"challenge": "old"}, {"issued_ms": 1501}, {"expires_ms": 1500},
    {"issued_ms": -1}, {"expires_ms": 100000}, {"issued_ms": True},
    {"outcome": "RUNNING"}, {"provider": "other"}, {"key_id": "other"},
    {"receipt_id": ""}, {"provider": ""}, {"key_id": ""},
])
def test_replay_stale_nonterminal_and_untrusted_key(changes):
    assert_unknown(classify(TestOnlySource(lambda r: replace(r, **changes)), TestOnlyAnchor()))


def test_unsigned_and_forged_proof():
    assert_unknown(classify(TestOnlySource(sign=False), TestOnlyAnchor()))
    assert_unknown(classify(TestOnlySource(lambda r: replace(r, signature=b"fake"), sign=False), TestOnlyAnchor()))


def test_signature_covers_all_payload_fields():
    original = TestOnlySource().resolve(BINDING, "challenge")
    anchor = TestOnlyAnchor()
    for field in fields(original):
        if field.name == "signature":
            continue
        value = getattr(original, field.name)
        changed = replace(original, **{field.name:
            replace(BINDING, execution_id="other") if field.name == "binding"
            else value + 1 if type(value) is int else value + "other"})
        assert not anchor.verify(changed.provider, changed.key_id, changed.signing_bytes(), changed.signature)


def test_cached_signed_receipt_cannot_be_replayed():
    class CachedSource:
        receipt = None

        def resolve(self, binding, challenge):
            if self.receipt is None:
                self.receipt = TestOnlySource().resolve(binding, challenge)
            return self.receipt

    source = CachedSource()
    assert classify(source, TestOnlyAnchor()).classification == "TERMINAL_VERIFIED"
    assert_unknown(classify(source, TestOnlyAnchor()))


@pytest.mark.parametrize("value", [None, {"verified": True, "result_state": "SUCCESS"}, True])
def test_caller_json_and_local_success_are_not_receipts(value):
    class Source:
        def resolve(self, binding, challenge):
            return value

    assert_unknown(classify(Source(), TestOnlyAnchor()))


def test_missing_dependencies_and_unavailable_provider_or_anchor():
    class Unavailable:
        def resolve(self, *args):
            raise RuntimeError("private provider body")

        verify = resolve

    assert_unknown(classify())
    assert_unknown(classify(TestOnlySource()))
    assert_unknown(classify(anchor=TestOnlyAnchor()))
    assert_unknown(classify(Unavailable(), TestOnlyAnchor()))
    assert_unknown(classify(TestOnlySource(), Unavailable()))


@pytest.mark.parametrize("field,value", [("claim_epoch", True), ("reserved_token_units", -1),
                                        ("binding_ref", " "), ("reservation_claim_epoch", 8)])
def test_malformed_expected_binding(field, value):
    assert_unknown(classify(TestOnlySource(), TestOnlyAnchor(), replace(BINDING, **{field: value})))
