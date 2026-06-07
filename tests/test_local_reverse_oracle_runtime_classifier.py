"""Tests for local_reverse_oracle_runtime_classifier."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from reverse_agent.local_reverse_oracle_runtime_classifier import (
    classify_run,
    extract_oracle_signals,
    strip_ansi,
)


class TestStripAnsi:
    def test_no_ansi(self) -> None:
        assert strip_ansi("hello world") == "hello world"

    def test_simple_ansi(self) -> None:
        assert strip_ansi("\x1b[31mred\x1b[0m") == "red"

    def test_cursor_positioning(self) -> None:
        raw = "\x1b[2;1H10013\x1b[2;6H"
        assert strip_ansi(raw) == "10013"

    def test_mixed_terminal_codes(self) -> None:
        raw = "\x1b[1t\x1b[c\x1b[?1004h\x1b[?9001hPlease input"
        assert strip_ansi(raw) == "Please input"


class TestExtractOracleSignals:
    def test_extract_signals(self) -> None:
        oracle = {
            "success_path": {
                "observable_signals": [
                    {"type": "stdout_string", "value": "Ok, you know it. Just hang on."}
                ]
            },
            "failure_path": {
                "observable_signals": [
                    {"type": "stdout_string", "value": "Sorry! Hang on!"}
                ]
            },
        }
        success, failure = extract_oracle_signals(oracle)
        assert success == ["Ok, you know it. Just hang on."]
        assert failure == ["Sorry! Hang on!"]

    def test_empty_oracle(self) -> None:
        success, failure = extract_oracle_signals({})
        assert success == []
        assert failure == []


class TestClassifyRun:
    def test_success_match(self) -> None:
        stdout = "Please input a string : \n10013\nOk, you know it. Just hang on.\n"
        result = classify_run(
            stdout,
            ["Ok, you know it. Just hang on."],
            ["Sorry! Hang on!"],
        )
        assert result["classification"] == "SUCCESS"
        assert result["success_matched"] is True
        assert result["failure_matched"] is False

    def test_failure_match(self) -> None:
        stdout = "Please input a string : \n20013\nSorry! Hang on!\n"
        result = classify_run(
            stdout,
            ["Ok, you know it. Just hang on."],
            ["Sorry! Hang on!"],
        )
        assert result["classification"] == "FAILURE"
        assert result["success_matched"] is False
        assert result["failure_matched"] is True

    def test_ansi_stripped_before_match(self) -> None:
        stdout = "\x1b[31m\x1b[1tPlease input\x1b[0m\n10013\n\x1b[32mOk, you know it. Just hang on.\x1b[0m\n"
        result = classify_run(
            stdout,
            ["Ok, you know it. Just hang on."],
            ["Sorry! Hang on!"],
        )
        assert result["classification"] == "SUCCESS"

    def test_no_signal(self) -> None:
        stdout = "Some random output without oracle strings"
        result = classify_run(
            stdout,
            ["Ok, you know it. Just hang on."],
            ["Sorry! Hang on!"],
        )
        assert result["classification"] == "NO_SIGNAL"

    def test_ambiguous_both(self) -> None:
        stdout = "Ok, you know it. Just hang on. Sorry! Hang on!"
        result = classify_run(
            stdout,
            ["Ok, you know it. Just hang on."],
            ["Sorry! Hang on!"],
        )
        assert result["classification"] == "AMBIGUOUS_BOTH"
