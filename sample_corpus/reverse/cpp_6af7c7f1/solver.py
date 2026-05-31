from __future__ import annotations


TARGET = "qvldxt"
MULTIPLIER = 5
OFFSET = 7
ALPHABET_SIZE = 26


def modular_inverse(value: int, modulus: int) -> int:
    for candidate in range(modulus):
        if (value * candidate) % modulus == 1:
            return candidate
    raise ValueError(f"{value} has no inverse modulo {modulus}")


def encode(candidate: str) -> str:
    chars: list[str] = []
    for char in candidate:
        if not "a" <= char <= "z":
            raise ValueError("candidate must contain only lowercase a-z")
        x = ord(char) - ord("a")
        y = (x * MULTIPLIER + OFFSET) % ALPHABET_SIZE
        chars.append(chr(y + ord("a")))
    return "".join(chars)


def solve() -> str:
    inverse = modular_inverse(MULTIPLIER, ALPHABET_SIZE)
    chars: list[str] = []
    for char in TARGET:
        y = ord(char) - ord("a")
        x = ((y - OFFSET) * inverse) % ALPHABET_SIZE
        chars.append(chr(x + ord("a")))
    result = "".join(chars)
    if encode(result) != TARGET:
        raise RuntimeError("internal verification failed")
    return result


def main() -> None:
    print(solve())


if __name__ == "__main__":
    main()
