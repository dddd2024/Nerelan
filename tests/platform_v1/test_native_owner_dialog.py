"""Provider-free dialog tests: no OS dialog, TaskStore, host, or executor."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import native_owner_dialog as native


def scope():
    return native.OwnerDialogScope(
        "host-1", "goal-actual", 4, "artifact-sha256", "owner/repo", "codex",
        "binding-1", "task-1", "window-1", 2, "policy-sha256", '{"operations":["read"]}')


def test_exact_display_and_injected_yes():
    seen = []
    def yes(text):
        seen.append(text)
        return True
    assert native.confirm_scope(scope(), platform_dialog=yes)
    for key, value in vars(scope()).items():
        assert f"{key}: {value}" in seen[0]
    assert "exactly 1 task; 30 minutes; 0 retries" in seen[0]
    assert "does not authorize execution" in seen[0]


@pytest.mark.parametrize("answer", [False, None, 1, "Yes", {"human_confirmed": True}])
def test_callback_requires_literal_true(answer):
    assert not native.confirm_scope(scope(), platform_dialog=lambda _: answer)


@pytest.mark.parametrize("changes", [
    {"goal_revision": True}, {"policy_revision": 0}, {"goal_id": ""},
    {"repository": "repo\nwindow: forged"}, {"binding_ref": "x\u202ey"},
    {"effective_policy": "x" * 8001},
])
def test_bad_scope_never_prompts(changes):
    def forbidden(_):
        pytest.fail("invalid scope prompted")
    assert not native.confirm_scope(replace(scope(), **changes), platform_dialog=forbidden)


def test_platform_failure_denies():
    def fail(_):
        raise OSError("desktop unavailable")
    assert not native.confirm_scope(scope(), platform_dialog=fail)


class Function:
    def __init__(self, call):
        self.call = call
    def __call__(self, *args):
        return self.call(*args)


@pytest.mark.parametrize("mode,answer,expected", [
    ("visible", 6, True), ("visible", 7, False), ("visible", 32000, False),
    ("service", 6, False), ("remote", 6, False), ("locked", 6, False),
    ("hidden", 6, False), ("no_input", 6, False), ("disconnect", 6, False),
])
def test_windows_preflight_and_bounded_dialog(monkeypatch, mode, answer, expected):
    calls = []
    closed = []
    def session(pid, out):
        out._obj.value = 0 if mode == "service" else 3
        return 1
    def info(handle, kind, buf, size, needed):
        if kind == 1:
            buf[2] = 0 if mode == "hidden" else 1
        else:
            buf.value = "WinSta0" if handle == 10 else (
                "Winlogon" if mode == "locked" else "Default")
        return 1
    def dialog(*args):
        calls.append(args)
        return answer
    kernel = SimpleNamespace(**{k: Function(v) for k, v in {
        "GetCurrentProcessId": lambda: 123, "ProcessIdToSessionId": session,
        "WTSGetActiveConsoleSessionId": lambda: 4 if mode == "remote" or (
            mode == "disconnect" and calls) else 3,
        "GetCurrentThreadId": lambda: 5,
    }.items()})
    user = SimpleNamespace(**{k: Function(v) for k, v in {
        "GetProcessWindowStation": lambda: 10,
        "OpenInputDesktop": lambda *a: 0 if mode == "no_input" else 20,
        "CloseDesktop": lambda h: closed.append(h),
        "GetUserObjectInformationW": info, "GetThreadDesktop": lambda _: 30,
        "MessageBoxTimeoutW": dialog,
    }.items()})
    monkeypatch.setattr(native, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(native.ctypes, "WinDLL", lambda name, **kw: (
        kernel if name == "kernel32" else user), raising=False)
    assert native.confirm_scope(scope()) is expected
    if mode in {"service", "remote", "locked", "hidden", "no_input"}:
        assert not calls
    else:
        assert calls[0][-1] == 60000
        assert calls[0][3] == 0x134
        assert closed


def test_non_windows_denies_without_loading_native_api(monkeypatch):
    monkeypatch.setattr(native, "os", SimpleNamespace(name="posix"))
    assert not native.confirm_scope(scope())
