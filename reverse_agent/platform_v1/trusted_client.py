"""Private native bootstrap for the host's owned browser client.

The client identity travels through anonymous stdin, never argv, environment,
metadata, renderer state or a public HTTP bootstrap endpoint.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from urllib.parse import urlsplit


def _loopback_base(value: str) -> str:
    try:
        url = urlsplit(value)
        valid = (
            url.scheme == "http"
            and url.hostname in {"127.0.0.1", "localhost"}
            and not url.username and not url.password
            and url.path in {"", "/"} and not url.query and not url.fragment
            and url.port is not None and 1 <= url.port <= 65535
        )
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError("trusted_client_configuration_invalid")
    return value.rstrip("/")


def client_environment() -> dict[str, str]:
    # No debug hooks, model credentials, proxy credentials, session capability
    # or arbitrary Node loader options are inherited by this owned process.
    allowed = (
        "PATH", "SystemRoot", "SYSTEMROOT", "WINDIR", "SystemDrive",
        "ProgramFiles", "ProgramFiles(x86)", "CommonProgramFiles",
        "USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "HOME",
        "LANG", "LC_ALL",
    )
    return {name: os.environ[name] for name in allowed if name in os.environ}


def _start_filetime(process) -> str | None:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes
        class FileTime(ctypes.Structure):
            _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]
        creation, exit_time, kernel, user = (FileTime() for _ in range(4))
        function = ctypes.windll.kernel32.GetProcessTimes
        function.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(FileTime)] * 4)]
        function.restype = wintypes.BOOL
        if function(wintypes.HANDLE(int(process._handle)), ctypes.byref(creation),
                    ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)):
            return str((creation.high << 32) | creation.low)
    except Exception:
        pass
    return None


class TrustedClient:
    def __init__(self, *, node_executable: str, frontend_url: str, task_api_url: str) -> None:
        self._frontend = _loopback_base(frontend_url)
        self._api = _loopback_base(task_api_url)
        if self._frontend == self._api:
            raise ValueError("trusted_client_configuration_invalid")
        self._node = node_executable or shutil.which("node") or ""
        self._script = Path(__file__).resolve().parents[2] / "frontend" / "trusted-client.mjs"
        self._process = None
        self._ready = threading.Event()
        self._status_listener = None
        self.start_filetime = None

    @property
    def pid(self) -> int | None:
        return self._process.pid if self._process is not None and self._process.poll() is None else None

    @property
    def ready(self) -> bool:
        return self._ready.is_set() and self.pid is not None

    @property
    def executable(self) -> str:
        return self._node

    def observe_status(self, listener) -> None:
        self._status_listener = listener
        listener()

    def _read_status(self, process) -> None:
        try:
            raw = process.stdout.readline(1025)
            status = json.loads(raw) if len(raw) <= 1024 else None
            if status == {"state": "ready", "pid": process.pid} and process.poll() is None:
                self._ready.set()
        except Exception:
            pass
        if self._status_listener is not None:
            self._status_listener()
        try:
            process.wait()
        except OSError:
            pass
        self._ready.clear()
        if self._status_listener is not None:
            self._status_listener()

    def __repr__(self) -> str:
        return "TrustedClient(<owned-native-process>)"

    def start(self, capability: str) -> None:
        if self._process is not None:
            raise RuntimeError("trusted_client_already_started")
        if not self._node or not self._script.is_file():
            raise RuntimeError("trusted_client_runtime_unavailable")
        if not isinstance(capability, str) or len(capability) != 64 or any(c not in "0123456789abcdef" for c in capability):
            raise ValueError("trusted_client_configuration_invalid")
        try:
            self._process = subprocess.Popen(
                [self._node, str(self._script)],
                cwd=str(self._script.parent),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env=client_environment(), close_fds=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            packet = json.dumps({
                "frontend_url": self._frontend, "task_api_url": self._api,
                "capability": capability,
            }, separators=(",", ":")).encode("utf-8") + b"\n"
            self._process.stdin.write(packet)
            self._process.stdin.flush()
            self.start_filetime = _start_filetime(self._process)
            threading.Thread(target=self._read_status, args=(self._process,), daemon=True).start()
            failed = False
        except Exception:
            failed = True
        if failed:
            self.stop()
            raise RuntimeError("trusted_client_bootstrap_failed")

    def stop(self) -> None:
        process = self._process
        self._process = None
        self._ready.clear()
        if process is None:
            return
        try:
            if process.stdin is not None:
                process.stdin.close()
        except Exception:
            pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                process.terminate()
                process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                # This Popen handle identifies only our exact child, never a
                # name-wide/PID-reopened process. Its owner job fences the tree.
                try:
                    process.kill()
                    process.wait(timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    pass
        except OSError:
            pass
