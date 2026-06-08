from __future__ import annotations

from pathlib import Path

from reverse_agent.local_reverse_solver_profiles import (
    BLOCKED,
    PARTIAL,
    SOLVED,
    SolverProfileResult,
    invert_bytewise_transform_table,
    invert_digit_mod_affine_table,
    invert_xor_array_table,
)


def test_xor_array_table_compare_synthetic_reverse_index() -> None:
    candidate = b"PlainText!"
    array_a = bytes([0x10, 0x21, 0x32, 0x43, 0x54, 0x65, 0x76, 0x87, 0x98, 0xA9])
    array_b = bytes([0x01, 0x12, 0x23, 0x34, 0x45, 0x56, 0x67, 0x78, 0x89, 0x9A])
    target = bytes(
        candidate[index] ^ array_a[len(candidate) - 1 - index] ^ array_b[index]
        for index in range(len(candidate))
    )

    result = invert_xor_array_table(array_a, array_b, target)

    assert isinstance(result, SolverProfileResult)
    assert result.status == SOLVED
    assert result.candidate == candidate.decode("ascii")
    assert result.candidate_generated is True
    assert "reverse_a=True" in result.proof_chain_summary


def test_bytewise_reversible_transform_table_synthetic_bit_swap() -> None:
    def swap_low_bits(value: int) -> int:
        return (
            (value & ~0x06)
            | ((value & 0x02) << 1)
            | ((value & 0x04) >> 1)
        )

    candidate = b"BitSwap9"
    target = bytes(swap_low_bits(value) for value in candidate)

    result = invert_bytewise_transform_table(target, swap_low_bits, domain=range(256))

    assert result.status == SOLVED
    assert result.candidate == candidate.decode("ascii")
    assert result.candidate_generated is True


def test_digit_mod_affine_transform_compare_synthetic_digits() -> None:
    digits = "0123456789"
    target = [((3 + 7 * int(ch)) % 10) + ord("0") for ch in digits]

    result = invert_digit_mod_affine_table(
        target,
        a=3,
        b=7,
        modulus=10,
        offset=ord("0"),
        domain=range(10),
    )

    assert result.status == SOLVED
    assert result.candidate == digits
    assert result.candidate_generated is True


def test_bytewise_non_invertible_case_returns_partial_without_guess() -> None:
    result = invert_bytewise_transform_table([0], lambda value: value % 2, domain=range(4))

    assert result.status == PARTIAL
    assert result.candidate == ""
    assert result.candidate_generated is False
    assert result.unsupported_reason == "AMBIGUOUS_INVERSE"


def test_digit_no_inverse_case_returns_blocked_without_guess() -> None:
    result = invert_digit_mod_affine_table([11], a=1, b=2, modulus=10, domain=range(10))

    assert result.status == BLOCKED
    assert result.candidate == ""
    assert result.candidate_generated is False
    assert result.unsupported_reason == "NO_DIGIT_INVERSE_FOR_TARGET"


def test_production_module_has_no_real_solved_candidates_hardcoded() -> None:
    module_text = Path("reverse_agent/local_reverse_solver_profiles.py").read_text(encoding="utf-8")

    for forbidden in ("KEEP_DREAM", "WeKnowItOk", "10013", "hookapi"):
        assert forbidden not in module_text
