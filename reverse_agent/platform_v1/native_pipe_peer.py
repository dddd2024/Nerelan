"""Windows kernel-backed named-pipe peer PID check for the CLI-2 test fixture.

This checks a process identifier obtained from the SERVER-SIDE pipe HANDLE,
not from JSON, a client claim, or a caller-supplied name. Exact PID equality
is only a test of intended-process correlation; it is NOT Owner identity,
an access-control list, a signed-binary attestation or an authorization grant.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os


def get_named_pipe_client_pid(pipe_handle: object) -> int | None:
    """Fail closed on non-Windows, malformed handles or Win32 API failure."""
    if os.name != "nt" or type(pipe_handle) is not int or pipe_handle <= 0:
        return None
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        fn = kernel32.GetNamedPipeClientProcessId
        fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        fn.restype = wintypes.BOOL
        pid = wintypes.DWORD(0)
        success = fn(wintypes.HANDLE(pipe_handle), ctypes.byref(pid))
        if not success or not pid.value:
            return None
        return int(pid.value)
    except (OSError, AttributeError, ValueError, TypeError, OverflowError):
        return None


def matches_expected_client_pid(pipe_handle: object, expected_pid: object) -> bool:
    """Compare actual kernel peer to a PID obtained from trusted host launch."""
    if type(expected_pid) is not int or not (1 <= expected_pid <= 0xFFFFFFFF):
        return False
    return get_named_pipe_client_pid(pipe_handle) == expected_pid
