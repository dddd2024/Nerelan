"""Simple static analysis patterns for local reverse samples.

This module provides pure functions for solving simple reverse engineering patterns
without requiring runtime execution or complex analysis frameworks.

Patterns supported:
- Affine lowercase alphabet transform (ax + b mod 26)
- Caesar/ROT cipher
- XOR with single-byte or repeating key
- Hex digest detection (MD5/SHA1/SHA256)
"""

from __future__ import annotations

import re
from typing import Literal


def modular_inverse(value: int, modulus: int) -> int:
    """Compute modular multiplicative inverse using extended Euclidean algorithm.

    Args:
        value: The value to find inverse for
        modulus: The modulus

    Returns:
        The modular inverse such that (value * inverse) % modulus == 1

    Raises:
        ValueError: If inverse does not exist (value and modulus not coprime)
    """
    for candidate in range(modulus):
        if (value * candidate) % modulus == 1:
            return candidate
    raise ValueError(f"{value} has no inverse modulo {modulus}")


def solve_affine_lowercase(
    target: str,
    a: int,
    b: int,
    alphabet_size: int = 26,
) -> str | None:
    """Solve affine cipher for lowercase alphabet: y = (ax + b) mod 26.

    Given target string and transform parameters (a, b), recover the original
    input that would produce the target after affine transformation.

    Args:
        target: The transformed string (must be lowercase a-z)
        a: Multiplier in affine transform (must be coprime with alphabet_size)
        b: Offset in affine transform
        alphabet_size: Size of alphabet (default 26 for English)

    Returns:
        The recovered original string, or None if target contains non-lowercase chars

    Raises:
        ValueError: If 'a' has no modular inverse (not coprime with alphabet_size)

    Example:
        >>> solve_affine_lowercase("qvldxt", a=5, b=7)
        'higuys'
    """
    # Validate target contains only lowercase a-z
    if not target or not all("a" <= c <= "z" for c in target):
        return None

    # Compute modular inverse of 'a'
    try:
        a_inv = modular_inverse(a, alphabet_size)
    except ValueError:
        raise ValueError(f"Multiplier {a} has no inverse modulo {alphabet_size}")

    result_chars: list[str] = []
    for char in target:
        y = ord(char) - ord("a")
        # Inverse: x = a_inv * (y - b) mod alphabet_size
        x = (a_inv * (y - b)) % alphabet_size
        result_chars.append(chr(x + ord("a")))

    return "".join(result_chars)


def encode_affine_lowercase(
    plaintext: str,
    a: int,
    b: int,
    alphabet_size: int = 26,
) -> str | None:
    """Encode string using affine cipher: y = (ax + b) mod 26.

    Args:
        plaintext: Input string (must be lowercase a-z)
        a: Multiplier in affine transform
        b: Offset in affine transform
        alphabet_size: Size of alphabet (default 26)

    Returns:
        Encoded string, or None if plaintext contains non-lowercase chars

    Example:
        >>> encode_affine_lowercase("higuys", a=5, b=7)
        'qvldxt'
    """
    if not plaintext or not all("a" <= c <= "z" for c in plaintext):
        return None

    result_chars: list[str] = []
    for char in plaintext:
        x = ord(char) - ord("a")
        y = (a * x + b) % alphabet_size
        result_chars.append(chr(y + ord("a")))

    return "".join(result_chars)


def solve_caesar_lowercase(target: str, shift: int) -> str | None:
    """Solve Caesar cipher for lowercase alphabet.

    Args:
        target: The shifted string (must be lowercase a-z)
        shift: The shift amount (positive = right shift in encoding)

    Returns:
        The recovered original string, or None if target invalid

    Example:
        >>> solve_caesar_lowercase("bcd", shift=1)
        'abc'
    """
    if not target or not all("a" <= c <= "z" for c in target):
        return None

    # Caesar is affine with a=1, so inverse is just negative shift
    return solve_affine_lowercase(target, a=1, b=shift)


def encode_caesar_lowercase(plaintext: str, shift: int) -> str | None:
    """Encode string using Caesar cipher.

    Args:
        plaintext: Input string (must be lowercase a-z)
        shift: The shift amount

    Returns:
        Encoded string, or None if plaintext invalid
    """
    return encode_affine_lowercase(plaintext, a=1, b=shift)


def xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR data with a repeating key.

    Args:
        data: Input bytes to XOR
        key: Key bytes (will be repeated if shorter than data)

    Returns:
        XOR result bytes

    Example:
        >>> xor_bytes(b"hello", b"k")
        b'\\x15\\x0c\\x07\\x07\\x04'
    """
    if not key:
        return data

    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    return bytes(result)


def xor_hex_string(hex_str: str, key: bytes) -> bytes | None:
    """XOR hex-encoded string with a key.

    Args:
        hex_str: Hexadecimal string (e.g., "48656c6c6f")
        key: XOR key bytes

    Returns:
        XOR result bytes, or None if hex_str is invalid
    """
    try:
        data = bytes.fromhex(hex_str)
        return xor_bytes(data, key)
    except ValueError:
        return None


def detect_hex_digest_kind(s: str) -> Literal["md5", "sha1", "sha256"] | None:
    """Detect if string is a hex-encoded cryptographic hash digest.

    Args:
        s: String to check (should be hex digits only)

    Returns:
        Hash type if recognized, None otherwise

    Example:
        >>> detect_hex_digest_kind("d41d8cd98f00b204e9800998ecf8427e")
        'md5'
    """
    # Remove common prefixes/suffixes and whitespace
    cleaned = s.lower().strip()
    if cleaned.startswith("0x"):
        cleaned = cleaned[2:]

    # Check if it's valid hex
    if not re.match(r"^[0-9a-f]+$", cleaned):
        return None

    # Check length
    length = len(cleaned)
    if length == 32:
        return "md5"
    elif length == 40:
        return "sha1"
    elif length == 64:
        return "sha256"

    return None


def is_valid_lowercase_only(s: str) -> bool:
    """Check if string contains only lowercase English letters.

    Args:
        s: String to validate

    Returns:
        True if all chars are in [a-z], False otherwise
    """
    return bool(s) and all("a" <= c <= "z" for c in s)


def find_affine_candidates(
    target: str,
    alphabet_size: int = 26,
) -> list[tuple[int, int, str]]:
    """Find all valid affine parameters that produce readable output.

    This is a brute-force helper for when transform parameters are unknown.
    Tries all valid (a, b) combinations and returns those that produce
    plausible plaintext (all lowercase).

    Args:
        target: The transformed string
        alphabet_size: Size of alphabet (default 26)

    Returns:
        List of (a, b, plaintext) tuples for valid transforms
    """
    candidates: list[tuple[int, int, str]] = []

    # Valid 'a' values are those coprime with alphabet_size
    valid_a_values = [
        a for a in range(1, alphabet_size) if __import__("math").gcd(a, alphabet_size) == 1
    ]

    for a in valid_a_values:
        for b in range(alphabet_size):
            try:
                plaintext = solve_affine_lowercase(target, a, b, alphabet_size)
                if plaintext:
                    candidates.append((a, b, plaintext))
            except ValueError:
                continue

    return candidates
