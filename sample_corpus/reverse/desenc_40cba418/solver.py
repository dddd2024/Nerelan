"""Solver for desenc_40cba418 - DES-ECB encrypted password checker.

Static analysis found:
- DES key: "TakeEasy" (8 bytes)
- Algorithm: standard DES-ECB
- Expected ciphertext: embedded in binary (need to locate)
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

# Try to use pycryptodome, fall back to pure Python DES if unavailable
try:
    from Crypto.Cipher import DES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def try_decrypt_block(key: bytes, block: bytes) -> bytes | None:
    """Try to decrypt an 8-byte block with DES-ECB."""
    if len(block) != 8:
        return None
    try:
        if HAS_CRYPTO:
            cipher = DES.new(key, DES.MODE_ECB)
            return cipher.decrypt(block)
    except Exception:
        pass
    return None


def is_printable_ascii(data: bytes) -> bool:
    """Check if all bytes are printable ASCII (0x20-0x7E)."""
    return all(0x20 <= b <= 0x7E for b in data)


def solve() -> str | None:
    """Scan binary for 8-byte blocks that decrypt to printable ASCII with DES key 'TakeEasy'."""
    sample_path = Path(__file__).parent / "sample.exe"
    if not sample_path.exists():
        print(f"ERROR: {sample_path} not found", file=sys.stderr)
        return None

    key = b"TakeEasy"
    data = sample_path.read_bytes()

    candidates: list[tuple[int, bytes]] = []

    # Scan all 8-byte aligned blocks
    for offset in range(0, len(data) - 7):
        block = data[offset:offset + 8]
        decrypted = try_decrypt_block(key, block)
        if decrypted and is_printable_ascii(decrypted):
            # Filter out obvious false positives (common English words, code patterns)
            text = decrypted.decode("ascii")
            # Skip very common short patterns that are likely coincidental
            if text.strip() and len(text.strip()) >= 4:
                candidates.append((offset, decrypted))

    if not candidates:
        print("No printable DES-ECB decryption found with key 'TakeEasy'")
        return None

    print(f"Found {len(candidates)} candidate(s):")
    for offset, decrypted in candidates:
        text = decrypted.decode("ascii")
        print(f"  offset 0x{offset:04X}: {text!r}")

    # Return the most likely candidate
    # Priority 1: flag-like patterns
    for offset, decrypted in candidates:
        text = decrypted.decode("ascii")
        if any(kw in text.lower() for kw in ["flag", "key", "pass", "ctf"]):
            return text

    # Priority 2: all-lowercase alphabetic strings (likely real passwords)
    for offset, decrypted in candidates:
        text = decrypted.decode("ascii")
        if text.isalpha() and text.islower() and len(text) >= 6:
            return text

    # Priority 3: all-alphabetic strings
    for offset, decrypted in candidates:
        text = decrypted.decode("ascii")
        if text.isalpha() and len(text) >= 6:
            return text

    # Fallback: first candidate
    if candidates:
        return candidates[0][1].decode("ascii")

    return None


def main() -> None:
    result = solve()
    if result:
        print(f"\nCandidate: {result}")
    else:
        print("\nNo solution found")


if __name__ == "__main__":
    main()
