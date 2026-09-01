"""Thin OS-backed durable credential vault adapter (trusted host only).

This module implements the durable OS-credential-store boundary described by
the product requirement for durable API-key persistence:

- a typed adapter contract (store / resolve / delete / probe) with fail-closed
  errors and no plaintext fallback;
- a deterministic in-memory fake adapter for provider-free tests;
- a Windows Credential Manager implementation reached only through the Python
  standard library (``ctypes``), never instantiated on other platforms;
- a stable non-secret vault item reference derived from and bound to the
  Connection authority, so one Connection can never resolve another
  Connection's stored item.

Raw secret material handled here never reaches persisted state files, public
JSON, logs, evidence or the frontend. Only the trusted host imports this
module.
"""

from __future__ import annotations

import hashlib
import sys
import threading
from typing import Any, Callable, Protocol

__all__ = [
    "VaultAdapter",
    "VaultError",
    "VaultUnavailableError",
    "VaultItemMissingError",
    "VaultSizeError",
    "FakeVault",
    "WindowsVaultAdapter",
    "connection_vault_ref",
    "default_vault_adapter",
]

_VAULT_REF_NAMESPACE = "nerelan:conn:v1"

# Windows Credential Manager accepts at most 5*512 bytes for a generic
# credential blob. Secrets are stored as UTF-8 bytes, so the byte length of
# the encoded secret is the binding constraint.
_MAX_SECRET_BYTES = 2560


class VaultError(ValueError):
    """Base fail-closed vault error mapped to an explicit client error."""


class VaultUnavailableError(VaultError):
    """The OS credential store is locked or otherwise unavailable."""


class VaultItemMissingError(VaultError):
    """The referenced vault item does not exist (removed or invalidated)."""


class VaultSizeError(VaultError):
    """The secret exceeds the OS credential store item size limit."""


def connection_vault_ref(
    connection_id: str,
    provider: str,
    base_url: str,
    auth_method: str,
) -> str:
    """Return the stable non-secret vault item reference for a Connection.

    The reference embeds a digest of the Connection authority (provider, base
    URL, auth method). Changing any authority-bearing field changes the
    reference, so a stored item can never be silently reused across a
    different authority boundary, and one Connection can never resolve
    another Connection's item.
    """

    authority = hashlib.sha256(
        f"{provider}\n{base_url}\n{auth_method}".encode("utf-8")
    ).hexdigest()[:16]
    return f"{_VAULT_REF_NAMESPACE}:{connection_id}:{authority}"


class VaultAdapter(Protocol):
    """Trusted-host-only contract for OS-backed durable secret storage."""

    def store(self, ref: str, secret: str) -> None:
        """Durably store ``secret`` under ``ref``, replacing any prior item."""

    def resolve(self, ref: str) -> str:
        """Resolve ``ref`` to its stored secret.

        Raises ``VaultUnavailableError`` when the store is locked or
        unavailable and ``VaultItemMissingError`` when the item is absent.
        """

    def delete(self, ref: str) -> None:
        """Delete the item under ``ref``; a missing item is not an error."""

    def probe(self, ref: str) -> str:
        """Return ``"available"``, ``"locked"`` or ``"missing"`` for ``ref``.

        Probing must never return the secret itself.
        """


def _encode_secret(secret: str) -> bytes:
    encoded = secret.encode("utf-8")
    if len(encoded) > _MAX_SECRET_BYTES:
        raise VaultSizeError(
            "secret exceeds the OS credential store item size limit"
        )
    return encoded


def _decode_secret_blob(
    ctypes_api: Any,
    blob_pointer: Any,
    size: int,
    ref: str,
) -> str:
    """Copy and decode one bounded native credential blob fail closed."""

    if size == 0:
        raise VaultItemMissingError(f"vault item is empty: {ref}")
    if size > _MAX_SECRET_BYTES:
        raise VaultSizeError(
            "OS credential store returned an oversized secret item"
        )
    if not blob_pointer:
        raise VaultItemMissingError(f"vault item is invalid: {ref}")
    blob = ctypes_api.string_at(blob_pointer, size)
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VaultItemMissingError(f"vault item is invalid: {ref}") from exc


class FakeVault:
    """Deterministic in-memory vault adapter for provider-free tests.

    The optional ``store_hook``/``resolve_hook``/``delete_hook`` callables let
    tests inject bounded failures without touching a real OS credential store.
    """

    def __init__(
        self,
        *,
        store_hook: Callable[[str], None] | None = None,
        resolve_hook: Callable[[str], None] | None = None,
        delete_hook: Callable[[str], None] | None = None,
    ) -> None:
        self._items: dict[str, str] = {}
        self._lock = threading.Lock()
        self.locked = False
        self.store_calls: list[str] = []
        self.resolve_calls: list[str] = []
        self.delete_calls: list[str] = []
        self.probe_calls: list[str] = []
        self._store_hook = store_hook
        self._resolve_hook = resolve_hook
        self._delete_hook = delete_hook

    def store(self, ref: str, secret: str) -> None:
        with self._lock:
            self.store_calls.append(ref)
            if self._store_hook is not None:
                self._store_hook(ref)
            if self.locked:
                raise VaultUnavailableError("credential store is locked")
            # Faithful to the adapter contract: oversized secrets fail closed.
            _encode_secret(secret)
            self._items[ref] = secret

    def resolve(self, ref: str) -> str:
        with self._lock:
            self.resolve_calls.append(ref)
            if self._resolve_hook is not None:
                self._resolve_hook(ref)
            if self.locked:
                raise VaultUnavailableError("credential store is locked")
            if ref not in self._items:
                raise VaultItemMissingError(f"vault item not found: {ref}")
            return self._items[ref]

    def delete(self, ref: str) -> None:
        with self._lock:
            self.delete_calls.append(ref)
            if self._delete_hook is not None:
                self._delete_hook(ref)
            if self.locked:
                raise VaultUnavailableError("credential store is locked")
            self._items.pop(ref, None)

    def probe(self, ref: str) -> str:
        with self._lock:
            self.probe_calls.append(ref)
            if self.locked:
                return "locked"
            return "available" if ref in self._items else "missing"

    def item_refs(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._items.keys()))


class WindowsVaultAdapter:
    """Windows Credential Manager adapter via the Python standard library.

    Generic credentials are written with a namespaced target name so only
    Nerelan-owned items are ever touched. Secrets are stored as UTF-8 bytes
    and never appear in logs, exceptions or public JSON.
    """

    _CRED_TYPE_GENERIC = 1
    _CRED_PERSIST_LOCAL_MACHINE = 2
    _ERROR_NOT_FOUND = 1168

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise VaultError("Windows vault adapter requires win32")
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        self._wintypes = wintypes

        class _CREDENTIALW(ctypes.Structure):
            _fields_ = [
                ("Flags", wintypes.DWORD),
                ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME),
                ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
                ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD),
                ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR),
                ("UserName", wintypes.LPWSTR),
            ]

        self._credential_type = _CREDENTIALW
        self._advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        credential_pointer = ctypes.POINTER(_CREDENTIALW)
        self._cred_write = self._advapi32.CredWriteW
        self._cred_write.argtypes = [credential_pointer, wintypes.DWORD]
        self._cred_write.restype = wintypes.BOOL
        self._cred_read = self._advapi32.CredReadW
        self._cred_read.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(credential_pointer),
        ]
        self._cred_read.restype = wintypes.BOOL
        self._cred_delete = self._advapi32.CredDeleteW
        self._cred_delete.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        self._cred_delete.restype = wintypes.BOOL
        self._cred_free = self._advapi32.CredFree
        self._cred_free.argtypes = [ctypes.c_void_p]
        self._cred_free.restype = None

    def store(self, ref: str, secret: str) -> None:
        ctypes = self._ctypes
        blob = _encode_secret(secret)
        blob_buffer = ctypes.create_string_buffer(blob, len(blob))
        credential = self._credential_type()
        credential.Flags = 0
        credential.Type = self._CRED_TYPE_GENERIC
        credential.TargetName = ref
        credential.Comment = None
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = ctypes.cast(
            blob_buffer, ctypes.POINTER(ctypes.c_char)
        )
        credential.Persist = self._CRED_PERSIST_LOCAL_MACHINE
        credential.AttributeCount = 0
        credential.Attributes = None
        credential.TargetAlias = None
        credential.UserName = "nerelan"
        ctypes.set_last_error(0)
        if not self._cred_write(ctypes.byref(credential), 0):
            code = ctypes.get_last_error()
            raise VaultUnavailableError(
                f"Windows credential store write failed (error {code})"
            )

    def resolve(self, ref: str) -> str:
        ctypes = self._ctypes
        pointer = ctypes.POINTER(self._credential_type)()
        ctypes.set_last_error(0)
        if not self._cred_read(
            ref, self._CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)
        ):
            code = ctypes.get_last_error()
            if code == self._ERROR_NOT_FOUND:
                raise VaultItemMissingError(f"vault item not found: {ref}")
            raise VaultUnavailableError(
                f"Windows credential store read failed (error {code})"
            )
        try:
            credential = pointer.contents
            size = credential.CredentialBlobSize
            secret = _decode_secret_blob(
                ctypes,
                credential.CredentialBlob,
                size,
                ref,
            )
        finally:
            self._cred_free(pointer)
        return secret

    def delete(self, ref: str) -> None:
        ctypes = self._ctypes
        ctypes.set_last_error(0)
        if not self._cred_delete(
            ref, self._CRED_TYPE_GENERIC, 0
        ):
            code = ctypes.get_last_error()
            if code == self._ERROR_NOT_FOUND:
                return
            raise VaultUnavailableError(
                f"Windows credential store delete failed (error {code})"
            )

    def probe(self, ref: str) -> str:
        ctypes = self._ctypes
        pointer = ctypes.POINTER(self._credential_type)()
        ctypes.set_last_error(0)
        if not self._cred_read(
            ref, self._CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)
        ):
            code = ctypes.get_last_error()
            return "missing" if code == self._ERROR_NOT_FOUND else "locked"
        self._cred_free(pointer)
        return "available"


def default_vault_adapter() -> Any:
    """Return the platform vault adapter, or None when unsupported.

    Returning ``None`` keeps the exact legacy process-local behavior; there
    is never a plaintext fallback for durable storage.
    """

    if sys.platform == "win32":
        return WindowsVaultAdapter()
    return None
