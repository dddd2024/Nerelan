"""Read-only positive evidence contract. No default provider or trust anchor.

Trusted host composition must inject BOTH dependencies; neither may come from
request JSON. An anchor authenticates canonical bytes under a pinned provider
key and checks key revocation/algorithm policy. Returning a caller boolean is
not an implementation of that contract. No production adapter exists here.
"""

from dataclasses import asdict, dataclass, fields
import json
import secrets
from typing import Literal, Protocol


@dataclass(frozen=True)
class OriginalBinding:
    task_id: str
    run_id: str
    claim_owner: str
    claim_epoch: int
    claim_expires_ms: int
    window_id: str
    window_expires_ms: int
    policy_id: str
    policy_revision: int
    policy_digest: str
    executor_kind: str
    execution_id: str
    binding_ref: str
    lease_owner: str
    lease_epoch: int
    lease_expires_ms: int
    reservation_task_id: str
    reservation_claim_epoch: int
    reservation_window_id: str
    reserved_token_units: int
    reserved_cost_micro_units: int
    provider_operation_id: str


@dataclass(frozen=True)
class TerminalReceipt:
    binding: OriginalBinding
    provider: str
    key_id: str
    receipt_id: str
    challenge: str
    issued_ms: int
    expires_ms: int
    # Means all effects of the ORIGINAL remote execution have ceased.
    outcome: Literal["SUCCEEDED", "FAILED", "CANCELLED"]
    signature: bytes

    def signing_bytes(self) -> bytes:
        payload = asdict(self)
        del payload["signature"]
        return b"nerelan-terminal-receipt-v1\x00" + json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")


class ReceiptSource(Protocol):
    def resolve(self, binding: OriginalBinding, challenge: str) -> TerminalReceipt | None:
        """Query original provider; never synthesize from local bookkeeping."""
        ...


class TrustAnchor(Protocol):
    def verify(self, provider: str, key_id: str, payload: bytes, signature: bytes) -> bool:
        """Cryptographically authenticate using independently configured keys."""
        ...


@dataclass(frozen=True)
class ReceiptEvidence:
    classification: Literal["UNKNOWN", "TERMINAL_VERIFIED"]
    reason: str
    receipt: TerminalReceipt | None = None
    budget_state: Literal["UNKNOWN"] = "UNKNOWN"
    release_allowed: Literal[False] = False


def _complete(binding: OriginalBinding) -> bool:
    if type(binding) is not OriginalBinding:
        return False
    for field in fields(binding):
        value = getattr(binding, field.name)
        if field.type is int:
            minimum = 0 if field.name.startswith("reserved_") else 1
            if type(value) is not int or value < minimum:
                return False
        elif type(value) is not str or not value.strip():
            return False
    return (binding.reservation_task_id == binding.task_id
            and binding.reservation_claim_epoch == binding.claim_epoch
            and binding.reservation_window_id == binding.window_id)


def verify_terminal_receipt(
    binding: OriginalBinding, *, source: ReceiptSource | None = None,
    anchor: TrustAnchor | None = None, now_ms: int,
) -> ReceiptEvidence:
    """Classify only; never a release capability or spend measurement.

    Expected bindings must come from an independently read original snapshot.
    Fresh random challenges reject replay across calls without a receipt store.
    Later CAS must re-read every fence; this result cannot authorize that write.
    """
    unknown = lambda reason: ReceiptEvidence("UNKNOWN", reason)
    if not _complete(binding) or type(now_ms) is not int or now_ms < 0:
        return unknown("original_binding_incomplete")
    if source is None or anchor is None:
        return unknown("trusted_provider_or_anchor_missing")
    challenge = secrets.token_hex(32)
    try:
        receipt = source.resolve(binding, challenge)
        if type(receipt) is not TerminalReceipt:
            return unknown("provider_receipt_missing")
        if not _complete(receipt.binding) or receipt.binding != binding:
            return unknown("original_binding_mismatch")
        if receipt.challenge != challenge:
            return unknown("replayed_or_unbound_receipt")
        if (type(receipt.issued_ms) is not int or type(receipt.expires_ms) is not int
                or not 0 <= receipt.issued_ms <= now_ms < receipt.expires_ms
                or receipt.expires_ms - receipt.issued_ms > 60_000):
            return unknown("receipt_stale_or_invalid_interval")
        if receipt.outcome not in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            return unknown("remote_effects_not_terminal")
        if (any(type(v) is not str or not v.strip() for v in
                (receipt.provider, receipt.key_id, receipt.receipt_id))
                or type(receipt.signature) is not bytes or not receipt.signature):
            return unknown("attestation_missing")
        if anchor.verify(receipt.provider, receipt.key_id,
                         receipt.signing_bytes(), receipt.signature) is not True:
            return unknown("attestation_invalid")
    except Exception:
        # Provider failures must not disclose response bodies or become evidence.
        return unknown("provider_or_attestation_unavailable")
    return ReceiptEvidence("TERMINAL_VERIFIED", "independently_attested", receipt)
