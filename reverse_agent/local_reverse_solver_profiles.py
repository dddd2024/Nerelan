from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence


SOLVED = "SOLVED"
PARTIAL = "PARTIAL"
BLOCKED = "BLOCKED"

XOR_ARRAY_TABLE_COMPARE = "xor_array_table_compare"
BYTEWISE_REVERSIBLE_TRANSFORM_TABLE_COMPARE = "bytewise_reversible_transform_table_compare"
DIGIT_MOD_AFFINE_TRANSFORM_COMPARE = "digit_mod_affine_transform_compare"
SWAP_LOW_BITS_1_2 = "swap_low_bits_1_2"
SUPPORTED_NORMALIZED_PROFILES = {
    XOR_ARRAY_TABLE_COMPARE,
    BYTEWISE_REVERSIBLE_TRANSFORM_TABLE_COMPARE,
    DIGIT_MOD_AFFINE_TRANSFORM_COMPARE,
}


@dataclass(frozen=True)
class SolverProfileResult:
    status: str
    candidate: str
    candidate_generated: bool
    confidence: str
    proof_chain_summary: tuple[str, ...]
    unsupported_reason: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "candidate": self.candidate,
            "candidate_generated": self.candidate_generated,
            "confidence": self.confidence,
            "proof_chain_summary": list(self.proof_chain_summary),
            "unsupported_reason": self.unsupported_reason,
        }


@dataclass(frozen=True)
class ProfileNormalizedEvidence:
    profile: str
    profile_evidence: Mapping[str, Any]
    source_artifact: str = ""
    source_run: str = ""
    freshness: str = "unknown"
    provenance_notes: tuple[str, ...] = ()

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        default_profile: str = "",
    ) -> "ProfileNormalizedEvidence | None":
        evidence = payload.get("profile_evidence")
        if not isinstance(evidence, Mapping):
            return None
        notes = payload.get("provenance_notes", ())
        if isinstance(notes, str):
            provenance_notes = (notes,)
        else:
            provenance_notes = tuple(str(item) for item in notes or ())
        return cls(
            profile=str(payload.get("profile") or default_profile),
            profile_evidence=evidence,
            source_artifact=str(payload.get("source_artifact") or ""),
            source_run=str(payload.get("source_run") or ""),
            freshness=str(payload.get("freshness") or "unknown"),
            provenance_notes=provenance_notes,
        )


def solve_normalized_profile(payload: Mapping[str, Any], *, default_profile: str = "") -> SolverProfileResult:
    normalized = ProfileNormalizedEvidence.from_mapping(payload, default_profile=default_profile)
    if normalized is None:
        return _blocked(
            "MISSING_PROFILE_NORMALIZED_EVIDENCE",
            "profile-normalized evidence must include a profile_evidence mapping",
        )
    if normalized.profile not in SUPPORTED_NORMALIZED_PROFILES:
        return _blocked("UNSUPPORTED_PROFILE", f"unsupported normalized profile: {normalized.profile}")
    evidence = normalized.profile_evidence
    if normalized.profile == XOR_ARRAY_TABLE_COMPARE:
        return invert_xor_array_table(
            _required_sequence(evidence, "array_a"),
            _required_sequence(evidence, "array_b"),
            _required_sequence(evidence, "target"),
            reverse_a=bool(evidence.get("reverse_a", True)),
            encoding=str(evidence.get("encoding") or "latin-1"),
        )
    if normalized.profile == DIGIT_MOD_AFFINE_TRANSFORM_COMPARE:
        return invert_digit_mod_affine_table(
            _required_sequence(evidence, "target"),
            a=int(evidence.get("a", 0)),
            b=int(evidence.get("b", 0)),
            modulus=int(evidence.get("modulus", 0)),
            offset=int(evidence.get("offset", 0)),
            domain=_domain_values(evidence.get("domain"), default=range(10)),
        )
    transform_kind = str(evidence.get("transform_kind") or "")
    transform = _bytewise_transform(transform_kind, evidence.get("transform_params"))
    if transform is None:
        return _blocked("UNSUPPORTED_TRANSFORM_KIND", f"unsupported transform_kind: {transform_kind}")
    return invert_bytewise_transform_table(
        _required_sequence(evidence, "target"),
        transform,
        domain=_domain_values(evidence.get("domain"), default=range(256)),
        encoding=str(evidence.get("encoding") or "latin-1"),
    )


def invert_xor_array_table(
    array_a: Sequence[int],
    array_b: Sequence[int],
    target: Sequence[int],
    *,
    reverse_a: bool = True,
    encoding: str = "latin-1",
) -> SolverProfileResult:
    """Invert candidate[i] = A[index] XOR B[i] XOR target[i]."""
    length = len(target)
    if not length:
        return _blocked("EMPTY_TARGET_TABLE", "xor target table is empty")
    if len(array_a) < length or len(array_b) < length:
        return _blocked(
            "INSUFFICIENT_TABLE_LENGTH",
            "xor source tables must cover the target table length",
        )

    candidate_bytes = bytearray()
    for index, target_value in enumerate(target):
        a_index = length - 1 - index if reverse_a else index
        candidate_bytes.append(_byte(array_a[a_index]) ^ _byte(array_b[index]) ^ _byte(target_value))

    candidate = _decode_candidate(candidate_bytes, encoding)
    if candidate is None:
        return _blocked("NON_TEXT_CANDIDATE", "xor inversion produced non-text bytes")
    return SolverProfileResult(
        status=SOLVED,
        candidate=candidate,
        candidate_generated=True,
        confidence="high",
        proof_chain_summary=(
            "applied bounded xor array/table inverse",
            f"target_length={length}",
            f"reverse_a={reverse_a}",
        ),
    )


def invert_bytewise_transform_table(
    target: Sequence[int],
    transform: Callable[[int], int],
    *,
    domain: Iterable[int] = range(256),
    encoding: str = "latin-1",
) -> SolverProfileResult:
    domain_values = tuple(_byte(value) for value in domain)
    if not domain_values:
        return _blocked("EMPTY_DOMAIN", "bytewise inverse domain is empty")
    if not target:
        return _blocked("EMPTY_TARGET_TABLE", "bytewise target table is empty")

    candidate_bytes = bytearray()
    ambiguous_positions: list[int] = []
    missing_positions: list[int] = []
    for index, target_value in enumerate(target):
        matches = [
            value
            for value in domain_values
            if _byte(transform(value)) == _byte(target_value)
        ]
        if len(matches) == 1:
            candidate_bytes.append(matches[0])
        elif matches:
            ambiguous_positions.append(index)
        else:
            missing_positions.append(index)

    if missing_positions:
        return _blocked(
            "NO_INVERSE_FOR_TARGET_BYTE",
            f"no byte inverse at positions {missing_positions}",
        )
    if ambiguous_positions:
        return SolverProfileResult(
            status=PARTIAL,
            candidate="",
            candidate_generated=False,
            confidence="low",
            proof_chain_summary=(
                "bounded bytewise inverse map was ambiguous",
                f"ambiguous_positions={ambiguous_positions}",
            ),
            unsupported_reason="AMBIGUOUS_INVERSE",
        )

    candidate = _decode_candidate(candidate_bytes, encoding)
    if candidate is None:
        return _blocked("NON_TEXT_CANDIDATE", "bytewise inversion produced non-text bytes")
    return SolverProfileResult(
        status=SOLVED,
        candidate=candidate,
        candidate_generated=True,
        confidence="high",
        proof_chain_summary=(
            "applied bounded bytewise inverse map",
            f"target_length={len(target)}",
            f"domain_size={len(domain_values)}",
        ),
    )


def invert_digit_mod_affine_table(
    target: Sequence[int | str],
    *,
    a: int,
    b: int,
    modulus: int,
    offset: int = 0,
    domain: Iterable[int] = range(10),
) -> SolverProfileResult:
    domain_values = tuple(int(value) for value in domain)
    if not domain_values:
        return _blocked("EMPTY_DOMAIN", "digit inverse domain is empty")
    if modulus <= 0:
        return _blocked("INVALID_MODULUS", "modulus must be positive")
    if not target:
        return _blocked("EMPTY_TARGET_TABLE", "digit affine target table is empty")

    candidate_digits: list[str] = []
    ambiguous_positions: list[int] = []
    missing_positions: list[int] = []
    for index, target_value in enumerate(target):
        expected = _target_number(target_value)
        matches = [
            value
            for value in domain_values
            if ((a + b * value) % modulus) + offset == expected
        ]
        if len(matches) == 1:
            candidate_digits.append(str(matches[0]))
        elif matches:
            ambiguous_positions.append(index)
        else:
            missing_positions.append(index)

    if missing_positions:
        return _blocked(
            "NO_DIGIT_INVERSE_FOR_TARGET",
            f"no digit inverse at positions {missing_positions}",
        )
    if ambiguous_positions:
        return SolverProfileResult(
            status=PARTIAL,
            candidate="",
            candidate_generated=False,
            confidence="low",
            proof_chain_summary=(
                "bounded digit affine inverse was ambiguous",
                f"ambiguous_positions={ambiguous_positions}",
            ),
            unsupported_reason="AMBIGUOUS_INVERSE",
        )

    return SolverProfileResult(
        status=SOLVED,
        candidate="".join(candidate_digits),
        candidate_generated=True,
        confidence="high",
        proof_chain_summary=(
            "applied bounded digit modular affine inverse",
            f"target_length={len(target)}",
            f"modulus={modulus}",
            f"domain_size={len(domain_values)}",
        ),
    )


def _blocked(reason: str, summary: str) -> SolverProfileResult:
    return SolverProfileResult(
        status=BLOCKED,
        candidate="",
        candidate_generated=False,
        confidence="none",
        proof_chain_summary=(summary,),
        unsupported_reason=reason,
    )


def _required_sequence(evidence: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = evidence.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"profile_evidence.{key} must be a sequence")
    return value


def _domain_values(value: Any, *, default: Iterable[int]) -> Iterable[int]:
    if value in (None, ""):
        return default
    if value == "byte":
        return range(256)
    if value == "digit":
        return range(10)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [int(item) for item in value]
    raise ValueError(f"unsupported domain value: {value!r}")


def _bytewise_transform(
    transform_kind: str,
    transform_params: Any,
) -> Callable[[int], int] | None:
    if transform_kind != SWAP_LOW_BITS_1_2:
        return None
    params = transform_params if isinstance(transform_params, Mapping) else {}
    bit_a = int(params.get("bit_a", 1))
    bit_b = int(params.get("bit_b", 2))
    if bit_a < 0 or bit_b < 0 or bit_a > 7 or bit_b > 7:
        raise ValueError("bit swap positions must be in 0..7")
    mask_a = 1 << bit_a
    mask_b = 1 << bit_b
    keep_mask = 0xFF ^ mask_a ^ mask_b

    def swap_bits(value: int) -> int:
        byte = _byte(value)
        bit_a_value = (byte & mask_a) >> bit_a
        bit_b_value = (byte & mask_b) >> bit_b
        return (byte & keep_mask) | (bit_a_value << bit_b) | (bit_b_value << bit_a)

    return swap_bits


def _byte(value: int) -> int:
    integer = int(value)
    if integer < 0 or integer > 255:
        raise ValueError(f"byte value out of range: {value}")
    return integer


def _target_number(value: int | str) -> int:
    if isinstance(value, str):
        if len(value) != 1:
            raise ValueError(f"target string item must be one character: {value!r}")
        return ord(value)
    return int(value)


def _decode_candidate(candidate_bytes: bytearray, encoding: str) -> str | None:
    try:
        candidate = bytes(candidate_bytes).decode(encoding)
    except UnicodeDecodeError:
        return None
    if any(ord(ch) < 32 or ord(ch) > 126 for ch in candidate):
        return None
    return candidate
