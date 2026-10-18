"""Native API contract tests; no real token/account/session is read."""
import ctypes
from ctypes import wintypes as w
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import native_owner_identity as native


class Function:
    def __init__(self, call):
        self.call = call

    def __call__(self, *args):
        return self.call(*args)


@pytest.mark.parametrize("mode", ["success", "different_sid", "different_session", "service",
                                 "impersonation", "token_denied", "wts_denied", "disconnected",
                                 "locked", "hidden", "missing_desktop", "missing_api"])
def test_native_identity_fail_closed(monkeypatch, mode):
    retained, freed, closed = [], [], []
    def open_token(_process, access, out):
        assert access == 8  # QUERY only
        out._obj.value = 77
        return mode != "token_denied"
    def open_thread(_thread, access, _as_self, out):
        out._obj.value = 78
        return mode == "impersonation"
    def info(token, kind, buf, size, needed):
        if kind == 12:
            buf._obj.value = 0 if mode == "service" else 3
            return 1
        needed._obj.value = 32
        if buf is None:
            return 0
        ctypes.cast(buf, ctypes.POINTER(w.LPVOID))[0] = 123
        return 1
    def query(_server, session, kind, out, length):
        if mode == "wts_denied":
            return 0
        if kind == 8:
            value = w.DWORD(4 if mode == "disconnected" else 0)
        else:
            value = ctypes.create_unicode_buffer("Owner" if kind == 5 else "HOST")
        retained.append(value)
        out._obj.value = ctypes.addressof(value)
        length._obj.value = ctypes.sizeof(value)
        return 1
    def lookup(_server, name, sid, size, domain, domain_size, kind):
        assert name == "HOST\\Owner"
        size._obj.value, domain_size._obj.value, kind._obj.value = 32, 20, 1
        return sid is not None
    def stringify(sid, out):
        value = ctypes.create_unicode_buffer("S-1-5-21-other" if (
            mode == "different_sid" and not isinstance(sid, int)) else "S-1-5-21-owner")
        retained.append(value)
        ctypes.cast(out, ctypes.POINTER(w.LPWSTR))[0] = ctypes.cast(value, w.LPWSTR)
        return 1
    def user_info(handle, kind, buf, size, needed):
        if kind == 1:
            buf[2] = 0 if mode == "hidden" else 1
        else:
            buf.value = "WinSta0" if handle == 10 else "Winlogon" if mode == "locked" else "Default"
        return 1
    def library(mapping):
        return SimpleNamespace(**{key: Function(value) for key, value in mapping.items()})
    libraries = {
        "kernel32": library({"GetCurrentProcess": lambda: 1, "GetCurrentThread": lambda: 2,
            "CloseHandle": lambda handle: closed.append(handle.value),
            "WTSGetActiveConsoleSessionId": lambda: 4 if mode == "different_session" else 3,
            "LocalFree": lambda ptr: freed.append(ptr), "GetCurrentThreadId": lambda: 5}),
        "advapi32": library({"OpenProcessToken": open_token, "OpenThreadToken": open_thread,
            "GetTokenInformation": info, "LookupAccountNameW": lookup, "ConvertSidToStringSidW": stringify}),
        "wtsapi32": library({"WTSQuerySessionInformationW": query, "WTSFreeMemory": lambda p: freed.append(p)}),
        "user32": library({"GetProcessWindowStation": lambda: 10,
            "OpenInputDesktop": lambda *args: 0 if mode == "missing_desktop" else 20,
            "CloseDesktop": lambda handle: closed.append(handle),
            "GetUserObjectInformationW": user_info, "GetThreadDesktop": lambda _: 30}),
    }
    def load(name, **kwargs):
        if mode == "missing_api":
            raise OSError("native helper missing")
        return libraries[name]
    monkeypatch.setattr(native, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(native.ctypes, "WinDLL", load, raising=False)
    monkeypatch.setattr(native.ctypes, "get_last_error", lambda: 1008, raising=False)
    result = native.interactive_owner()
    if mode == "success":
        assert result == native.InteractiveOwner("S-1-5-21-owner", 3)
        assert 77 in closed and 20 in closed and len(freed) == 5
    else:
        assert result is None


def test_unsupported_os_never_loads_native_code(monkeypatch):
    monkeypatch.setattr(native, "os", SimpleNamespace(name="posix"))
    monkeypatch.setattr(native.ctypes, "WinDLL", lambda *args, **kwargs: pytest.fail("loaded"), raising=False)
    assert native.interactive_owner() is None
