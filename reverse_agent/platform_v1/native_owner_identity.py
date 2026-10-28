"""Read-only Windows proof of the host user's active console identity.

The native bootstrap runs as the Owner. Pin this proof at host construction;
neither account names, SIDs nor session IDs are accepted from a client.
Remote sessions, impersonation, locked/noninteractive desktops and unavailable
native APIs fail closed. This does not log in or switch any account.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class InteractiveOwner:
    sid: str
    session_id: int


def interactive_owner() -> InteractiveOwner | None:
    if os.name != "nt":
        return None
    try:
        return _windows_interactive_owner()
    except Exception:
        return None


def _windows_interactive_owner() -> InteractiveOwner:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    wts = ctypes.WinDLL("wtsapi32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    def api(lib, name, args, result):
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, result
        return fn

    process = api(kernel, "GetCurrentProcess", [], w.HANDLE)
    thread = api(kernel, "GetCurrentThread", [], w.HANDLE)
    close = api(kernel, "CloseHandle", [w.HANDLE], w.BOOL)
    console = api(kernel, "WTSGetActiveConsoleSessionId", [], w.DWORD)
    open_process = api(advapi, "OpenProcessToken", [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)], w.BOOL)
    open_thread = api(advapi, "OpenThreadToken", [w.HANDLE, w.DWORD, w.BOOL, ctypes.POINTER(w.HANDLE)], w.BOOL)
    info = api(advapi, "GetTokenInformation", [w.HANDLE, ctypes.c_int, w.LPVOID, w.DWORD,
                                               ctypes.POINTER(w.DWORD)], w.BOOL)
    query = api(wts, "WTSQuerySessionInformationW", [w.HANDLE, w.DWORD, ctypes.c_int,
                                                    ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.DWORD)], w.BOOL)
    free_wts = api(wts, "WTSFreeMemory", [w.LPVOID], None)
    lookup = api(advapi, "LookupAccountNameW", [w.LPCWSTR, w.LPCWSTR, w.LPVOID,
                 ctypes.POINTER(w.DWORD), w.LPWSTR, ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD)], w.BOOL)
    stringify = api(advapi, "ConvertSidToStringSidW", [w.LPVOID, ctypes.POINTER(w.LPWSTR)], w.BOOL)
    free = api(kernel, "LocalFree", [w.LPVOID], w.LPVOID)
    station = api(user32, "GetProcessWindowStation", [], w.HANDLE)
    desktop = api(user32, "OpenInputDesktop", [w.DWORD, w.BOOL, w.DWORD], w.HANDLE)
    close_desktop = api(user32, "CloseDesktop", [w.HANDLE], w.BOOL)
    user_info = api(user32, "GetUserObjectInformationW", [w.HANDLE, ctypes.c_int, w.LPVOID,
                       w.DWORD, ctypes.POINTER(w.DWORD)], w.BOOL)
    thread_id = api(kernel, "GetCurrentThreadId", [], w.DWORD)
    thread_desktop = api(user32, "GetThreadDesktop", [w.DWORD], w.HANDLE)

    def require(ok):
        if not ok:
            raise OSError("native_owner_identity_unavailable")

    def sid_string(sid):
        value = w.LPWSTR()
        require(stringify(sid, ctypes.byref(value)))
        try:
            return value.value
        finally:
            free(ctypes.cast(value, w.LPVOID))

    def object_name(handle):
        name, needed = ctypes.create_unicode_buffer(256), w.DWORD()
        require(user_info(handle, 2, name, ctypes.sizeof(name), ctypes.byref(needed)))
        return name.value

    require(object_name(station()) == "WinSta0")
    flags, needed = (w.DWORD * 3)(), w.DWORD()
    require(user_info(station(), 1, flags, ctypes.sizeof(flags), ctypes.byref(needed)) and flags[2] & 1)
    input_desktop = desktop(0, False, 1)  # DESKTOP_READOBJECTS, never switch desktops
    require(input_desktop)
    try:
        require(object_name(input_desktop) == "Default"
                and object_name(thread_desktop(thread_id())) == "Default")
    finally:
        close_desktop(input_desktop)

    impersonation = w.HANDLE()
    if open_thread(thread(), 8, True, ctypes.byref(impersonation)):
        close(impersonation)
        raise OSError("native_owner_impersonation")
    require(ctypes.get_last_error() == 1008)  # ERROR_NO_TOKEN, no impersonation
    token = w.HANDLE()
    require(open_process(process(), 8, ctypes.byref(token)))  # TOKEN_QUERY only
    try:
        needed = w.DWORD()
        session = w.DWORD()
        require(info(token, 12, ctypes.byref(session), ctypes.sizeof(session), ctypes.byref(needed)))
        require(session.value not in {0, 0xFFFFFFFF} and session.value == console())
        # TOKEN_USER begins with SID_AND_ATTRIBUTES (pointer + DWORD).
        info(token, 1, None, 0, ctypes.byref(needed))
        require(0 < needed.value <= 65536)
        user = ctypes.create_string_buffer(needed.value)
        require(info(token, 1, user, len(user), ctypes.byref(needed)))
        host_sid = sid_string(ctypes.cast(user, ctypes.POINTER(w.LPVOID))[0])

        def session_info(kind, is_string=True):
            value, length = w.LPVOID(), w.DWORD()
            require(query(None, session.value, kind, ctypes.byref(value), ctypes.byref(length)))
            try:
                require(value and length.value >= (2 if is_string else 4))
                return ctypes.wstring_at(value) if is_string else ctypes.cast(value, ctypes.POINTER(w.DWORD))[0]
            finally:
                free_wts(value)

        require(session_info(8, False) == 0)  # WTSActive
        username, domain = session_info(5), session_info(7)
        require(username and domain)
        size, domain_size, kind = w.DWORD(), w.DWORD(), w.DWORD()
        account = domain + "\\" + username
        lookup(None, account, None, ctypes.byref(size), None, ctypes.byref(domain_size), ctypes.byref(kind))
        require(0 < size.value <= 65536 and 0 < domain_size.value <= 32768)
        sid = ctypes.create_string_buffer(size.value)
        domain_buf = ctypes.create_unicode_buffer(domain_size.value)
        require(lookup(None, account, sid, ctypes.byref(size), domain_buf, ctypes.byref(domain_size), ctypes.byref(kind)))
        require(kind.value == 1 and sid_string(sid) == host_sid and console() == session.value)
        return InteractiveOwner(host_sid, session.value)
    finally:
        close(token)
