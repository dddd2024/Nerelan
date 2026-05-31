"""Solver for rc4enc_3480917d - RC4 encrypted password checker.

Static analysis found:
- RC4 key: "WORKER" (6 bytes)
- Non-standard S-box init: fill 0xCC, first 6 bytes +2, then KSA
- Target ciphertext: d5 23 a5 22 75 d8 b7 80 (8 bytes)

NOTE: Multiple RC4 init variants tested, none produced printable ASCII.
The exact S-box preprocessing requires disassembly to determine.
"""

from __future__ import annotations


def rc4_init_modified(key: bytes) -> list[int]:
    """Initialize RC4 S-box with non-standard preprocessing."""
    S = [0xCC] * 256
    for i in range(len(key)):
        S[i] = (S[i] + 2) & 0xFF
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    return S


def rc4_crypt(S: list[int], data: bytes) -> bytes:
    """RC4 PRGA stream cipher."""
    S = S.copy()
    i = j = 0
    result = bytearray()
    for byte in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) & 0xFF]
        result.append(byte ^ k)
    return bytes(result)


def solve() -> str | None:
    """Try to decrypt the target ciphertext using the modified RC4."""
    key = b"WORKER"
    target_ct = bytes([0xD5, 0x23, 0xA5, 0x22, 0x75, 0xD8, 0xB7, 0x80])

    # Try multiple init variants
    variants = {
        "0xCC fill +2 first 6 + KSA": lambda k: rc4_init_modified(k),
        "standard RC4": lambda k: _std_init(k),
        "0xCC fill + KSA": lambda k: _cc_ksa(k),
        "std KSA +2 first 6 after": lambda k: _std_then_add2(k),
    }

    for label, init_fn in variants.items():
        S = init_fn(key)
        pt = rc4_crypt(S, target_ct)
        printable = all(0x20 <= b <= 0x7E for b in pt)
        print(f"Variant '{label}': {pt.hex()} printable={printable}")
        if printable:
            return pt.decode("ascii")

    print("No variant produced printable ASCII.")
    return None


def _std_init(key: bytes) -> list[int]:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    return S


def _cc_ksa(key: bytes) -> list[int]:
    S = [0xCC] * 256
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    return S


def _std_then_add2(key: bytes) -> list[int]:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    for i in range(len(key)):
        S[i] = (S[i] + 2) & 0xFF
    return S


def main() -> None:
    result = solve()
    if result:
        print(f"Candidate: {result}")
    else:
        print("No solution found - static analysis insufficient")


if __name__ == "__main__":
    main()
