"""Affine cipher inverse handoff generator.

Reads a structured affine static artifact (e.g. from targeted IDA decompile)
and produces an inverse handoff artifact with transform parameters, modular
inverse, and per-character mapping rules.

Does NOT run the target binary. Does NOT generate a candidate unless an
expected ciphertext is explicitly provided in the input artifact AND
accompanied by an auditable provenance/source field.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Return (g, x, y) such that a*x + b*y = g = gcd(a, b)."""
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = _extended_gcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def _mod_inverse(a: int, modulus: int) -> int | None:
    """Return modular inverse of a modulo modulus, or None if not invertible."""
    g, x, _ = _extended_gcd(a % modulus, modulus)
    if g != 1:
        return None
    return x % modulus


def _build_per_char_mapping(a: int, b: int, inverse_a: int, modulus: int) -> list[dict[str, Any]]:
    """Build per-character forward and inverse mapping table."""
    mapping = []
    for p in range(modulus):
        c = (a * p + b) % modulus
        p_check = (inverse_a * (c - b)) % modulus
        mapping.append({
            "plain": chr(p + 97),
            "cipher": chr(c + 97),
            "forward": f"c = ({a} * {p} + {b}) % {modulus} = {c} -> '{chr(c + 97)}'",
            "inverse": f"p = {inverse_a} * ({c} - {b}) % {modulus} = {p_check} -> '{chr(p_check + 97)}'",
        })
    return mapping


# Auditable provenance source whitelist.
TRUSTED_CIPHERTEXT_SOURCES = frozenset({
    "challenge_statement",
    "allowed_static_evidence",
    "user_provided",
})


def _check_ciphertext_provenance(artifact: dict[str, Any]) -> str | None:
    """Return the provenance source if auditable, or None."""
    for key in ("expected_ciphertext_source", "expected_ciphertext_provenance", "expected_ciphertext_origin"):
        value = artifact.get(key)
        if isinstance(value, str) and value.strip() in TRUSTED_CIPHERTEXT_SOURCES:
            return value.strip()
    return None


def run_affine_inverse_handoff(
    input_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Main logic: parse affine artifact, compute inverse, emit handoff."""
    artifact = _load_json(input_path)

    sample_id = str(artifact.get("sample_id", ""))
    if not sample_id:
        raise ValueError("Input artifact missing sample_id")

    # Extract affine parameters from transform_loop
    post_scanf = artifact.get("post_scanf_flow_evidence", {})
    transform_loop = post_scanf.get("transform_loop", {})
    affine_params = transform_loop.get("affine_parameters", {})

    a = affine_params.get("a")
    b = affine_params.get("b")
    modulus = affine_params.get("modulus")

    if a is None or b is None or modulus is None:
        # Try alternative paths
        candidate_sites = artifact.get("candidate_transform_sites", [])
        if candidate_sites:
            site = candidate_sites[0]
            formula = site.get("formula", "")
            # Parse "Str[j] = (5 + 5 * (Str[j] - 97)) % 26 + 97"
            if "(5 + 5 *" in formula and "% 26" in formula:
                a, b, modulus = 5, 5, 26

    if a is None or b is None or modulus is None:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="MISSING_AFFINE_PARAMETERS",
            detail="Input artifact does not contain affine_parameters (a, b, modulus) in expected fields.",
        )
        _save_json(out_path, result)
        return result

    # Validate domain
    range_check = post_scanf.get("input_validation_loop", {}).get("range_check", {})
    min_char = range_check.get("min_char")
    max_char = range_check.get("max_char")

    domain_ok = (
        min_char == 97 and max_char == 122
    ) or (
        # Fallback: check notes
        any("a-z" in str(note) for note in artifact.get("notes", []))
    )

    if not domain_ok:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="UNSUPPORTED_DOMAIN",
            detail=f"Input domain min_char={min_char}, max_char={max_char}; only lowercase a-z (97..122) is supported.",
        )
        _save_json(out_path, result)
        return result

    # Check invertibility
    gcd_a_mod = math.gcd(a, modulus)
    inverse_a = _mod_inverse(a, modulus) if gcd_a_mod == 1 else None

    if inverse_a is None:
        result = _blocked_result(
            sample_id=sample_id,
            source_artifact=str(input_path),
            blocked_reason="NON_INVERTIBLE_AFFINE_MULTIPLIER",
            detail=f"gcd(a={a}, modulus={modulus}) = {gcd_a_mod} != 1; no modular inverse exists.",
            forward_transform={"a": a, "b": b, "formula": f"c = ({a} * p + {b}) % {modulus}"},
        )
        _save_json(out_path, result)
        return result

    # Build mapping
    per_char_mapping = _build_per_char_mapping(a, b, inverse_a, modulus)

    # Check for expected ciphertext
    expected_ciphertext = artifact.get("expected_ciphertext")
    ciphertext_provenance = None

    # Determine status
    if expected_ciphertext is None:
        status = "BLOCKED"
        blocked_reason = "MISSING_EXPECTED_CIPHERTEXT"
        candidate = None
        next_action = (
            "Provide expected ciphertext from challenge statement or another "
            "allowed evidence source before candidate generation."
        )
    else:
        # Provenance gate: require auditable source
        ciphertext_provenance = _check_ciphertext_provenance(artifact)
        if ciphertext_provenance is None:
            status = "BLOCKED"
            blocked_reason = "UNTRUSTED_EXPECTED_CIPHERTEXT_SOURCE"
            candidate = None
            next_action = (
                "expected_ciphertext is present but has no auditable provenance/source "
                "field. Add expected_ciphertext_source, expected_ciphertext_provenance, or "
                "expected_ciphertext_origin with a trusted value "
                "(challenge_statement, allowed_static_evidence, user_provided)."
            )
        else:
            status = "READY"
            blocked_reason = ""
            candidate = _decrypt_affine(expected_ciphertext, inverse_a, b, modulus)
            next_action = "Validate candidate against challenge requirements."

    result: dict[str, Any] = {
        "schema_version": 1,
        "sample_id": sample_id,
        "source_artifact": str(input_path).replace("\\", "/"),
        "analysis_mode": "affine_inverse_handoff_static_only",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "cipher_type": "affine_cipher",
        "domain": {
            "alphabet": "lowercase_ascii",
            "min_char": "a",
            "max_char": "z",
            "min_char_code": 97,
            "max_char_code": 122,
            "modulus": modulus,
        },
        "forward_transform": {
            "a": a,
            "b": b,
            "formula": f"c = ({a} * p + {b}) % {modulus}",
            "description": "Affine cipher: multiply by a, add b, mod 26",
        },
        "inverse_transform": {
            "gcd_a_modulus": gcd_a_mod,
            "inverse_a": inverse_a,
            "formula": f"p = {inverse_a} * (c - {b}) % {modulus}",
            "description": f"Modular inverse of {a} mod {modulus} is {inverse_a} (since {a}*{inverse_a} = {a * inverse_a} = 1 mod {modulus})",
        },
        "per_char_mapping": per_char_mapping,
        "expected_ciphertext": expected_ciphertext,
        "ciphertext_provenance": ciphertext_provenance,
        "candidate": candidate,
        "status": status,
        "blocked_reason": blocked_reason,
        "recommended_next_action": next_action,
    }

    _save_json(out_path, result)

    print(f"affine inverse handoff: status={status} sample_id={sample_id}")
    print(f"  forward: a={a} b={b} modulus={modulus}")
    print(f"  inverse_a={inverse_a} gcd={gcd_a_mod}")
    if blocked_reason:
        print(f"  blocked_reason={blocked_reason}")
    if candidate:
        print(f"  candidate={candidate}")

    return result


def _blocked_result(
    sample_id: str,
    source_artifact: str,
    blocked_reason: str,
    detail: str,
    forward_transform: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sample_id": sample_id,
        "source_artifact": source_artifact.replace("\\", "/"),
        "analysis_mode": "affine_inverse_handoff_static_only",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "generated_at": _now_iso(),
        "cipher_type": "affine_cipher",
        "domain": {},
        "forward_transform": forward_transform or {},
        "inverse_transform": {},
        "per_char_mapping": [],
        "expected_ciphertext": None,
        "candidate": None,
        "status": "BLOCKED",
        "blocked_reason": blocked_reason,
        "blocked_detail": detail,
        "recommended_next_action": "Review input artifact and provide missing affine parameters or expected ciphertext.",
    }


def _decrypt_affine(ciphertext: str, inverse_a: int, b: int, modulus: int) -> str:
    """Decrypt affine ciphertext to plaintext."""
    plaintext = []
    for ch in ciphertext:
        if not ch.islower():
            plaintext.append(ch)
            continue
        c = ord(ch) - 97
        p = (inverse_a * (c - b)) % modulus
        plaintext.append(chr(p + 97))
    return "".join(plaintext)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate affine cipher inverse handoff from static IDA artifact.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("project_state/local_reverse_affine_main0_targeted_ida_decompile.json"),
        help="Path to targeted IDA decompile artifact with affine parameters",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("project_state/local_reverse_affine_inverse_handoff.json"),
        help="Output path for inverse handoff JSON",
    )
    args = parser.parse_args()

    try:
        run_affine_inverse_handoff(args.input, args.out)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
