"""Tests for local_reverse_cpp1_7b504c54_xor_handoff."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from reverse_agent.local_reverse_cpp1_7b504c54_xor_handoff import (
    _extract_arrays,
    _find_sample_root,
    _resolve_binary_path,
    _va_to_file_offset,
    run_xor_handoff,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_triage_artifact(tmp_path: Path, relative_path: str = "逆向课程2023春补考01/Cpp1.exe") -> Path:
    triage = {
        "sample_id": "cpp1_7b504c54",
        "sha256": "abc123",
        "relative_path": relative_path,
        "tool_status": "success",
    }
    p = tmp_path / "triage.json"
    p.write_text(json.dumps(triage), encoding="utf-8")
    return p


def _make_pe_with_arrays(tmp_path: Path) -> Path:
    """Create a minimal PE with byte arrays at 0x427A30, 0x427A3C, 0x427A48."""
    # Build a minimal PE: DOS header + PE header + optional header + section table + .data section
    dos_header = bytearray(0x40)
    dos_header[0:2] = b"MZ"
    dos_header[0x3C:0x40] = struct.pack("<I", 0x40)  # PE offset

    pe_sig = b"PE\x00\x00"
    coff_header = bytearray(20)
    coff_header[0:2] = struct.pack("<H", 0x14C)   # Machine i386
    coff_header[2:4] = struct.pack("<H", 1)       # NumberOfSections
    coff_header[16:18] = struct.pack("<H", 0xE0)  # SizeOfOptionalHeader (PE32)

    # Optional header (PE32, 224 bytes)
    opt_header = bytearray(0xE0)
    opt_header[0:2] = struct.pack("<H", 0x10B)    # Magic PE32
    opt_header[28:32] = struct.pack("<I", 0x00400000)  # ImageBase

    # Section table (40 bytes per section)
    section_table = bytearray(40)
    section_table[0:8] = b".data\x00\x00\x00"
    # VirtualAddress = 0x27000, VirtualSize = 0x1000
    # RawAddress = 0x160 (actual file offset where section data starts)
    # RawSize = 0x1000
    section_table[8:12] = struct.pack("<I", 0x1000)    # VirtualSize
    section_table[12:16] = struct.pack("<I", 0x27000)  # VirtualAddress
    section_table[16:20] = struct.pack("<I", 0x1000)   # SizeOfRawData
    section_table[20:24] = struct.pack("<I", 0x160)    # PointerToRawData = actual offset in file

    # .data section content starts at file offset 0x160
    # Target VA 0x427A30 -> RVA 0x27A30
    # -> file offset = 0x160 + (0x27A30 - 0x27000) = 0x160 + 0xA30 = 0xB90
    data_section = bytearray(0x1000)
    offset_in_data = 0xA30
    # byte_427A30: 10 bytes
    data_section[offset_in_data:offset_in_data + 10] = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A])
    # byte_427A3C: 10 bytes
    data_section[offset_in_data + 12:offset_in_data + 22] = bytes([0x00, 0x00, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18])
    # byte_427A48: 10 bytes
    data_section[offset_in_data + 24:offset_in_data + 34] = bytes([0x19, 0x1A, 0x00, 0x00, 0x4C, 0x7E, 0x50, 0x7D, 0x7C, 0x64])

    # Build the full PE file using explicit concatenation to ensure correct byte layout
    pe_parts = [bytes(dos_header), pe_sig, bytes(coff_header), bytes(opt_header), bytes(section_table), bytes(data_section)]
    pe_data = b"".join(pe_parts)
    p = tmp_path / "Cpp1.exe"
    p.write_bytes(pe_data)
    return p


import struct


# ── Tests ────────────────────────────────────────────────────────────────────


class TestVaToFileOffset:
    def test_maps_correctly(self, tmp_path: Path) -> None:
        pe = _make_pe_with_arrays(tmp_path)
        data = bytearray(pe.read_bytes())
        image_base = 0x00400000
        offset = _va_to_file_offset(data, image_base, 0x427A30)
        assert offset is not None
        assert data[offset:offset + 10] == bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A])

    def test_missing_va_returns_none(self, tmp_path: Path) -> None:
        pe = _make_pe_with_arrays(tmp_path)
        data = bytearray(pe.read_bytes())
        image_base = 0x00400000
        offset = _va_to_file_offset(data, image_base, 0x99999999)
        assert offset is None


class TestExtractArrays:
    def test_extracts_all_three(self, tmp_path: Path) -> None:
        pe = _make_pe_with_arrays(tmp_path)
        result = _extract_arrays(pe)
        assert result["status"] == "READY_FOR_STATIC_REVIEW"
        assert "byte_427A30" in result["arrays"]
        assert "byte_427A3C" in result["arrays"]
        assert "byte_427A48" in result["arrays"]
        assert result["arrays"]["byte_427A30"]["bytes_hex"] == "0102030405060708090a"
        assert result["forward_transform_verified"] is True

    def test_computes_correct_candidate(self, tmp_path: Path) -> None:
        pe = _make_pe_with_arrays(tmp_path)
        result = _extract_arrays(pe)
        # candidate[i] = byte_427A30[9-i] ^ byte_427A3C[i] ^ byte_427A48[i]
        expected = bytearray(10)
        arr1 = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A])
        arr2 = bytes([0x00, 0x00, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18])
        arr3 = bytes([0x19, 0x1A, 0x00, 0x00, 0x4C, 0x7E, 0x50, 0x7D, 0x7C, 0x64])
        for i in range(10):
            expected[i] = arr1[9 - i] ^ arr2[i] ^ arr3[i]
        assert result["candidate_hex"] == expected.hex()


class TestResolveBinaryPath:
    def test_finds_binary(self, tmp_path: Path) -> None:
        with patch.dict(os.environ, {"LOCAL_REVERSE_ROOT": str(tmp_path)}):
            (tmp_path / "逆向课程2023春补考01").mkdir(parents=True)
            (tmp_path / "逆向课程2023春补考01" / "Cpp1.exe").write_text("fake")
            result = _resolve_binary_path("逆向课程2023春补考01/Cpp1.exe")
            assert result is not None
            assert result.name == "Cpp1.exe"

    def test_missing_returns_none(self, tmp_path: Path) -> None:
        with patch.dict(os.environ, {"LOCAL_REVERSE_ROOT": str(tmp_path)}):
            result = _resolve_binary_path("nonexistent/Cpp1.exe")
            assert result is None


class TestRunXorHandoff:
    def test_generates_artifact(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        out = tmp_path / "handoff.json"
        with patch("reverse_agent.local_reverse_cpp1_7b504c54_xor_handoff._find_sample_root", return_value=tmp_path):
            pe = _make_pe_with_arrays(tmp_path)
            # Create the expected directory structure
            (tmp_path / "逆向课程2023春补考01").mkdir(parents=True, exist_ok=True)
            pe.rename(tmp_path / "逆向课程2023春补考01" / "Cpp1.exe")
            result = run_xor_handoff(static_triage_path=triage, out_path=out)

        assert result["status"] == "READY_FOR_STATIC_REVIEW"
        assert result["sample_id"] == "cpp1_7b504c54"
        assert result["executed_sample"] is False
        assert result["static_only"] is True
        assert result["runtime_validated"] is False
        assert result["solved"] is False
        assert result["candidate"] is None
        assert result["known_candidate"] == ""
        assert "arrays" in result
        assert "static_candidate_hex" in result
        assert result["forward_transform_verified"] is True

        # Verify file was written
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["sample_id"] == "cpp1_7b504c54"

    def test_wrong_sample_id_raises(self, tmp_path: Path) -> None:
        triage = tmp_path / "triage.json"
        triage.write_text(json.dumps({"sample_id": "wrong_id"}), encoding="utf-8")
        out = tmp_path / "handoff.json"
        with pytest.raises(ValueError, match="Expected sample_id=cpp1_7b504c54"):
            run_xor_handoff(static_triage_path=triage, out_path=out)

    def test_blocked_on_missing_binary(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path, relative_path="nonexistent/Cpp1.exe")
        out = tmp_path / "handoff.json"
        with patch("reverse_agent.local_reverse_cpp1_7b504c54_xor_handoff._find_sample_root", return_value=tmp_path):
            result = run_xor_handoff(static_triage_path=triage, out_path=out)
        assert result["status"] == "BLOCKED"
        assert "BINARY_NOT_FOUND" in result["blocked_reason"]
