"""Host-only Windows dialog gate.

This is an input primitive, not an authorization issuer. Admission requires
the host's transactional snapshot comparison and single-use admission gate.
No HTTP routes import it; standalone preview callers obtain no authority.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import os
from collections.abc import Callable


@dataclass(frozen=True)
class OwnerDialogScope:
    """Display-only frozen scope. Admission caller must load persisted truth."""

    host_instance_id: str
    goal_id: str
    goal_revision: int
    artifact_digest: str
    repository: str
    executor_kind: str
    binding_ref: str
    task_id: str
    window_id: str
    policy_revision: int
    policy_digest: str
    effective_policy: str

    def text(self, *, admission: bool = False) -> str:
        rows = vars(self)
        if any(type(value) is not str or not value.strip() or len(value) > 8000
               or any(ord(c) < 32 or ord(c) > 126 for c in value)
               for key, value in rows.items()
               if key not in {"goal_revision", "policy_revision"}):
            raise ValueError("scope_text_invalid")
        if any(type(value) is not int or value < 1
               for value in (self.goal_revision, self.policy_revision)):
            raise ValueError("scope_revision_invalid")
        text = "\n".join(f"{key}: {value}" for key, value in rows.items())
        if len(text) > 12000:
            raise ValueError("scope_too_large")
        if admission:
            return ("Nerelan native Owner consent: approve and enqueue this exact Goal\n\n"
                    + text + "\n\nMaximum: exactly 1 task; 30 minutes; 0 retries.\n"
                    "This admits execution under the existing coordinator and sandbox.\n"
                    "No API authentication bypass or account switching. Confirm?")
        return ("Nerelan host consent preview (does not authorize execution)\n\n"
                + text + "\n\nMaximum: exactly 1 task; 30 minutes; 0 retries.\n"
                "No activation or dispatch is implemented by this dialog.\n"
                "Confirm this displayed selection?")


def confirm_admission(scope: OwnerDialogScope) -> bool:
    """Native host only. A Yes still requires atomic scope validation/admission."""
    try:
        return _windows_confirm(scope.text(admission=True)) is True
    except Exception:
        return False


def confirm_scope(scope: OwnerDialogScope, *,
                  platform_dialog: Callable[[str], bool] | None = None) -> bool:
    """Injection is for host-side tests only; never expose through HTTP.

    No grant, nonce, receipt, TaskStore write, or dispatch is produced.
    Exceptions and non-boolean callback answers fail closed.
    """
    try:
        text = scope.text()
        return (platform_dialog or _windows_confirm)(text) is True
    except Exception:
        return False


def _windows_confirm(text: str) -> bool:
    if os.name != "nt":
        return False
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel.GetCurrentProcessId.restype = wintypes.DWORD
    kernel.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.ProcessIdToSessionId.restype = wintypes.BOOL
    kernel.WTSGetActiveConsoleSessionId.restype = wintypes.DWORD
    user.GetProcessWindowStation.restype = wintypes.HANDLE
    user.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    user.OpenInputDesktop.restype = wintypes.HANDLE
    user.CloseDesktop.argtypes = [wintypes.HANDLE]
    user.GetUserObjectInformationW.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                              wintypes.LPVOID, wintypes.DWORD,
                                              ctypes.POINTER(wintypes.DWORD)]
    user.GetUserObjectInformationW.restype = wintypes.BOOL
    user.GetThreadDesktop.argtypes = [wintypes.DWORD]
    user.GetThreadDesktop.restype = wintypes.HANDLE
    kernel.GetCurrentThreadId.restype = wintypes.DWORD

    def name(handle: int) -> str:
        buf = ctypes.create_unicode_buffer(256)
        needed = wintypes.DWORD()
        if not user.GetUserObjectInformationW(handle, 2, buf, ctypes.sizeof(buf), ctypes.byref(needed)):
            return ""
        return buf.value

    def visible() -> bool:
        session = wintypes.DWORD()
        if not kernel.ProcessIdToSessionId(kernel.GetCurrentProcessId(), ctypes.byref(session)):
            return False
        if session.value == 0 or session.value != kernel.WTSGetActiveConsoleSessionId():
            return False
        station = user.GetProcessWindowStation()
        # USEROBJECTFLAGS: BOOL inherit, BOOL reserved, DWORD flags.
        flags = (wintypes.DWORD * 3)()
        needed = wintypes.DWORD()
        if (name(station) != "WinSta0" or not user.GetUserObjectInformationW(
                station, 1, flags, ctypes.sizeof(flags), ctypes.byref(needed))
                or not flags[2] & 1):
            return False
        desktop = user.OpenInputDesktop(0, False, 1)  # DESKTOP_READOBJECTS
        if not desktop:
            return False
        try:
            return (name(desktop) == "Default" and name(user.GetThreadDesktop(
                kernel.GetCurrentThreadId())) == "Default")
        finally:
            user.CloseDesktop(desktop)

    if not visible():
        return False
    # No service-notification/default-desktop flags. Default button is No.
    # Timeout also bounds a desktop disconnect/lock race after the preflight.
    dialog = user.MessageBoxTimeoutW
    dialog.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR,
                       wintypes.UINT, wintypes.WORD, wintypes.DWORD]
    dialog.restype = ctypes.c_int
    result = dialog(None, text, "Nerelan TrustedHost selection", 0x4 | 0x30 | 0x100, 0, 60000)
    return result == 6 and visible()  # IDYES only; recheck session after input.
