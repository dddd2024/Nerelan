"""Outbound alert toasts. No process is started: Popen is faked."""
from __future__ import annotations

from reverse_agent.platform_v1.multi_account import notify
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig


def capture():
    calls = []

    def popen(args, **kwargs):
        calls.append((args, kwargs))
    return calls, popen


def raised(severity="warning", detail="workbuddy-ai quarantined"):
    return {"event": "raised", "severity": severity, "code": "account_quarantined", "subject": "x", "detail": detail}


def test_a_raised_warning_shows_one_toast_with_its_text_in_the_environment():
    calls, popen = capture()
    notify.toast_sink(popen=popen, platform="win32")(raised())
    (args, kwargs), = calls
    assert args[0] == "powershell.exe" and "workbuddy" not in " ".join(args)  # text never on the command line
    assert kwargs["env"]["NERELAN_TOAST_TITLE"] == "Nerelan warning: account_quarantined"
    assert kwargs["env"]["NERELAN_TOAST_BODY"] == "workbuddy-ai quarantined"


def test_info_alerts_resolutions_and_other_platforms_show_nothing():
    calls, popen = capture()
    notify.toast_sink(popen=popen, platform="win32")(raised(severity="info"))
    notify.toast_sink(popen=popen, platform="win32")({**raised(), "event": "resolved"})
    notify.toast_sink(popen=popen, platform="linux")(raised())
    assert calls == []


def test_text_is_flattened_and_bounded():
    calls, popen = capture()
    notify.toast_sink(popen=popen, platform="win32")(raised(detail="a\nb\r\n" + "x" * 500))
    body = calls[0][1]["env"]["NERELAN_TOAST_BODY"]
    assert "\n" not in body and len(body) <= notify.MAX_TEXT


def test_a_failing_sink_does_not_stop_the_log():
    written = []

    def broken(event):
        raise RuntimeError("no toast")
    sink = notify.chain(broken, written.append)
    sink(raised())
    assert written == [raised()]
    assert notify.chain(None, None) is None


def test_toasts_are_off_unless_configured(monkeypatch):
    assert MultiAccountConfig().alert_notify == ""
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ALERT_NOTIFY", "toast")
    assert MultiAccountConfig.from_env().alert_notify == "toast"
