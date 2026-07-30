from __future__ import annotations

import base64

import pytest

from reverse_agent.unattended.probe import _history_secret_scan


def test_history_secret_scan_rejects_names_raw_and_encoded_values() -> None:
    secret = "sk-synthetic-executor-value"
    assert _history_secret_scan("bounded-history", sensitive_values=(secret,))
    assert not _history_secret_scan(
        f"history:{secret}",
        sensitive_values=(secret,),
    )
    assert not _history_secret_scan(
        "history:" + base64.b64encode(secret.encode()).decode(),
        sensitive_values=(secret,),
    )
    assert not _history_secret_scan(
        "history:SESSION_API_KEY",
        sensitive_values=(secret,),
    )


@pytest.mark.parametrize("value", ("",))
def test_history_secret_scan_rejects_invalid_sensitive_value(value: str) -> None:
    assert not _history_secret_scan("bounded-history", sensitive_values=(value,))
