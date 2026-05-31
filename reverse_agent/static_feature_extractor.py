"""Static feature extractor for binary samples.

This module provides pure Python static analysis capabilities for extracting
features from binary files without executing them.
"""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Keywords for crypto/encoding detection
CRYPTO_KEYWORDS = [
    "md5", "sha", "sha1", "sha256", "sha512",
    "rc4", "des", "aes", "blowfish", "chacha",
    "base64", "base32", "base16", "hex", "encode", "decode",
    "encrypt", "decrypt", "cipher",
]

# Keywords for comparison detection
COMPARE_KEYWORDS = [
    "strcmp", "strncmp", "memcmp", "compare",
    "input", "password", "key", "flag", "correct",
    "wrong", "invalid", "success", "fail",
]

# Input/output keywords
IO_KEYWORDS = [
    "scanf", "printf", "gets", "fgets", "getchar",
    "stdin", "stdout", "stderr", "read", "write",
]


@dataclass
class StaticFeatures:
    """Static features extracted from a binary sample."""

    format: str = "unknown"  # pe, mz, unknown
    file_size: int = 0
    ascii_strings_sample: list[str] = field(default_factory=list)
    utf16_strings_sample: list[str] = field(default_factory=list)
    keyword_hits: list[dict[str, Any]] = field(default_factory=list)
    crypto_hints: list[dict[str, Any]] = field(default_factory=list)
    compare_hints: list[dict[str, Any]] = field(default_factory=list)
    interesting_constants: list[dict[str, Any]] = field(default_factory=list)
    entropy_hint: str = "unknown"  # low, medium, high, unknown


def compute_entropy(data: bytes) -> float:
    """Compute Shannon entropy of byte data.

    Args:
        data: Byte data to analyze

    Returns:
        Entropy value between 0 and 8 (bits per byte)
    """
    if not data:
        return 0.0

    entropy = 0.0
    length = len(data)

    for byte in range(256):
        count = data.count(byte)
        if count > 0:
            freq = count / length
            entropy -= freq * math.log2(freq)

    return entropy


def get_entropy_hint(entropy: float) -> str:
    """Convert entropy value to qualitative hint.

    Args:
        entropy: Entropy value (0-8)

    Returns:
        Qualitative hint: low, medium, high
    """
    if entropy < 5.0:
        return "low"
    elif entropy < 7.0:
        return "medium"
    else:
        return "high"


def detect_pe_format(data: bytes) -> str:
    """Detect if data is a PE/MZ executable.

    Args:
        data: Binary data to analyze

    Returns:
        Format string: pe, mz, or unknown
    """
    if len(data) < 2:
        return "unknown"

    # Check for MZ header
    if data[:2] == b"MZ":
        if len(data) < 64:
            return "mz"

        # Check for PE header at offset pointed by MZ header
        try:
            pe_offset = struct.unpack("<I", data[60:64])[0]
            if pe_offset <= len(data) - 4:
                if data[pe_offset:pe_offset+4] == b"PE\x00\x00":
                    return "pe"
        except (struct.error, IndexError):
            pass

        return "mz"

    return "unknown"


def extract_ascii_strings(data: bytes, min_length: int = 4, max_count: int = 100) -> list[str]:
    """Extract ASCII strings from binary data.

    Args:
        data: Binary data to analyze
        min_length: Minimum string length to include
        max_count: Maximum number of strings to return

    Returns:
        List of ASCII strings
    """
    # Match printable ASCII characters (32-126)
    pattern = rb"[\x20-\x7E]{%d,}" % min_length
    matches = re.findall(pattern, data)

    # Decode and limit
    strings = []
    for match in matches[:max_count]:
        try:
            decoded = match.decode("ascii")
            strings.append(decoded)
        except UnicodeDecodeError:
            continue

    return strings


def extract_utf16le_strings(data: bytes, min_length: int = 4, max_count: int = 100) -> list[str]:
    """Extract UTF-16LE strings from binary data.

    Args:
        data: Binary data to analyze
        min_length: Minimum string length to include
        max_count: Maximum number of strings to return

    Returns:
        List of UTF-16LE decoded strings
    """
    strings = []

    # Look for patterns of ASCII chars in UTF-16LE (e.g., 'h\x00e\x00l\x00l\x00')
    # Match: (ASCII char followed by \x00) repeated min_length times
    pattern = rb"(?:[\x20-\x7E]\x00){%d,}" % min_length
    matches = re.findall(pattern, data)

    for match in matches[:max_count]:
        try:
            decoded = match.decode("utf-16le")
            strings.append(decoded)
        except UnicodeDecodeError:
            continue

    return strings


def find_keyword_hits(
    strings: list[str],
    keywords: list[str],
    context_chars: int = 20,
) -> list[dict[str, Any]]:
    """Find keyword occurrences in strings with context.

    Args:
        strings: List of strings to search
        keywords: List of keywords to find
        context_chars: Number of context characters to include

    Returns:
        List of hit dictionaries with keyword, source, and context
    """
    hits = []
    keyword_set = set(k.lower() for k in keywords)

    for string in strings:
        string_lower = string.lower()
        for keyword in keyword_set:
            if keyword in string_lower:
                # Find position and extract context
                pos = string_lower.find(keyword)
                start = max(0, pos - context_chars)
                end = min(len(string), pos + len(keyword) + context_chars)
                context = string[start:end]

                hits.append({
                    "keyword": keyword,
                    "source": string[:50] + "..." if len(string) > 50 else string,
                    "context": context,
                })
                break  # Only record once per string

    return hits


def find_hex_like_constants(data: bytes, min_length: int = 8) -> list[dict[str, Any]]:
    """Find hex-like constants in binary data.

    Args:
        data: Binary data to analyze
        min_length: Minimum length of hex sequence

    Returns:
        List of hex constant dictionaries
    """
    constants = []

    # Pattern for hex sequences (at least min_length hex chars)
    pattern = rb"[0-9a-fA-F]{%d,}" % min_length

    for match in re.finditer(pattern, data):
        hex_str = match.group().decode("ascii")
        start = match.start()

        # Classify by length
        kind = None
        if len(hex_str) == 32:
            kind = "md5_like"
        elif len(hex_str) == 40:
            kind = "sha1_like"
        elif len(hex_str) == 64:
            kind = "sha256_like"

        constants.append({
            "hex": hex_str[:64],  # Limit length
            "offset": start,
            "length": len(hex_str),
            "kind": kind or "unknown",
        })

    # Limit results
    return constants[:50]


def find_base64_like_strings(strings: list[str], min_length: int = 20) -> list[dict[str, Any]]:
    """Find base64-like strings.

    Args:
        strings: List of strings to check
        min_length: Minimum length to consider

    Returns:
        List of base64 candidate dictionaries
    """
    candidates = []
    # Base64 alphabet pattern
    b64_pattern = re.compile(r"^[A-Za-z0-9+/]{%d,}={0,2}$" % min_length)

    for string in strings:
        if b64_pattern.match(string) and len(string) % 4 == 0:
            candidates.append({
                "string": string[:100],  # Limit length
                "length": len(string),
            })

    return candidates[:20]


def extract_static_features(
    sample_path: Path,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB limit
) -> StaticFeatures:
    """Extract static features from a binary sample.

    This function only reads file bytes and does not execute the sample.

    Args:
        sample_path: Path to the binary sample
        max_file_size: Maximum file size to process

    Returns:
        StaticFeatures object with extracted features
    """
    features = StaticFeatures()

    if not sample_path.exists():
        return features

    file_size = sample_path.stat().st_size
    features.file_size = file_size

    # Skip files that are too large
    if file_size > max_file_size:
        features.entropy_hint = "unknown"
        return features

    # Read file data
    with open(sample_path, "rb") as f:
        data = f.read()

    if not data:
        return features

    # Detect format
    features.format = detect_pe_format(data)

    # Compute entropy
    entropy = compute_entropy(data)
    features.entropy_hint = get_entropy_hint(entropy)

    # Extract strings
    ascii_strings = extract_ascii_strings(data, min_length=4, max_count=200)
    utf16_strings = extract_utf16le_strings(data, min_length=4, max_count=100)

    # Sample strings for output (limit to avoid bloating reports)
    features.ascii_strings_sample = ascii_strings[:50]
    features.utf16_strings_sample = utf16_strings[:30]

    # Find keyword hits
    all_strings = ascii_strings + utf16_strings
    features.keyword_hits = find_keyword_hits(all_strings, CRYPTO_KEYWORDS + COMPARE_KEYWORDS + IO_KEYWORDS)

    # Find crypto hints
    features.crypto_hints = find_keyword_hits(all_strings, CRYPTO_KEYWORDS)

    # Find compare hints
    features.compare_hints = find_keyword_hits(all_strings, COMPARE_KEYWORDS)

    # Find interesting constants
    features.interesting_constants = find_hex_like_constants(data)

    # Add base64 candidates to interesting constants
    b64_candidates = find_base64_like_strings(ascii_strings)
    for candidate in b64_candidates:
        features.interesting_constants.append({
            "hex": candidate["string"],
            "offset": -1,
            "length": candidate["length"],
            "kind": "base64_candidate",
        })

    return features


def features_to_dict(features: StaticFeatures) -> dict[str, Any]:
    """Convert StaticFeatures to dictionary for JSON serialization.

    Args:
        features: StaticFeatures object

    Returns:
        Dictionary representation
    """
    return {
        "format": features.format,
        "file_size": features.file_size,
        "ascii_strings_sample": features.ascii_strings_sample[:20],  # Limit for JSON
        "utf16_strings_sample": features.utf16_strings_sample[:10],
        "keyword_hits": features.keyword_hits[:20],
        "crypto_hints": features.crypto_hints[:10],
        "compare_hints": features.compare_hints[:10],
        "interesting_constants": features.interesting_constants[:20],
        "entropy_hint": features.entropy_hint,
    }
