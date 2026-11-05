"""Workspace lease token: make a stale executor's artifacts unusable.

The durable lease already carries a monotonic fencing token, but it only guards
**database rows**: `_fenced_add_evidence`, `_accept_checkpoint` and friends
compare `(owner, epoch)` before writing. The worktree on disk has no such guard,
so an executor that lost its lease can still edit files and hand a diff back.

This module supplies the missing half — a token written into the worktree that
records which `(run_id, owner, epoch)` produced its current contents.

What it does and does not guarantee:

* **does** let any later stage refuse work whose token no longer matches the
  current lease, so a superseded run cannot publish or be accepted;
* **does not** stop an arbitrary process from writing files. It is a fencing
  token, not a sandbox; enforcement happens where the token is *checked*.

The checking step is deliberately **not wired** yet: it belongs in
`durable_execution` before product-diff collection and before publication, and
that path needs its own review (see `C3_WORKSPACE_FENCE_DESIGN.md`). Until then
the module is available and tested, and the wiring gap stays a red test.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

TOKEN_NAME = ".nerelan-lease.json"
ENABLE_ENV = "REVERSE_AGENT_WORKSPACE_FENCE"
TOKEN_VERSION = 1


class WorkspaceFenced(RuntimeError):
    """The worktree's token does not belong to the caller's lease."""


def workspace_fence_enabled(env: Optional[Mapping[str, str]] = None) -> bool:
    """Off by default: this changes behaviour only when explicitly enabled."""
    return (env if env is not None else os.environ).get(ENABLE_ENV) == "1"


@dataclass(frozen=True)
class LeaseToken:
    run_id: str
    owner: str
    epoch: int
    version: int = TOKEN_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {"version": self.version, "run_id": self.run_id,
                "owner": self.owner, "epoch": self.epoch}

    @classmethod
    def parse(cls, raw: Any) -> Optional["LeaseToken"]:
        if not isinstance(raw, Mapping):
            return None
        run_id, owner, epoch = raw.get("run_id"), raw.get("owner"), raw.get("epoch")
        if not isinstance(run_id, str) or not run_id:
            return None
        if not isinstance(owner, str) or not owner:
            return None
        if not isinstance(epoch, int) or epoch < 0:
            return None
        version = raw.get("version")
        return cls(run_id=run_id, owner=owner, epoch=epoch,
                   version=version if isinstance(version, int) else TOKEN_VERSION)

    def matches(self, other: "LeaseToken") -> bool:
        return (self.run_id, self.owner, self.epoch) == (other.run_id, other.owner, other.epoch)


def token_path(worktree: Path) -> Path:
    return Path(worktree) / TOKEN_NAME


def read_token(worktree: Path) -> Optional[LeaseToken]:
    """The token currently in this worktree, or ``None`` when absent/unreadable."""
    try:
        raw = json.loads(token_path(worktree).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return LeaseToken.parse(raw)


def publish_token(worktree: Path, token: LeaseToken) -> None:
    """Atomically write the token that owns this worktree from now on.

    Atomic because a crash mid-write must not leave a truncated token: a reader
    that cannot parse the file treats the worktree as unowned and refuses, which
    is the safe direction.
    """
    target = token_path(worktree)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(token.to_payload(), stream, ensure_ascii=False, sort_keys=True)
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def verify_token(worktree: Path, token: LeaseToken, *, adopt_missing: bool = True,
                 allow_takeover: bool = True) -> LeaseToken:
    """Raise unless this worktree belongs to ``token``; return the effective token.

    Three cases, and only three:

    * **missing** — adopted when ``adopt_missing`` (worktrees created before the
      feature, or prepared but never published); refused otherwise, because on a
      verification pass a missing token means someone took it away.
    * **same token** — accepted.
    * **different token** — accepted *only* as a legitimate takeover: the caller
      must hold a strictly greater epoch (which only a database-fenced recovery
      can produce). Anything else is a stale writer and is refused.

    The epoch comparison is why this is safe to call on both the publish path and
    the verify path: a recovering owner takes over, an old owner cannot.
    """
    current = read_token(worktree)
    if current is None:
        if not adopt_missing:
            raise WorkspaceFenced(f"workspace_token_missing:{worktree}")
        publish_token(worktree, token)
        return token
    if current.matches(token):
        return current
    if allow_takeover and token.epoch > current.epoch:
        publish_token(worktree, token)
        return token
    raise WorkspaceFenced(
        f"workspace_fenced:{current.run_id}:owner={current.owner}:epoch={current.epoch} "
        f"caller_owner={token.owner}:caller_epoch={token.epoch}")


def fence_workspace(worktree: Path, *, run_id: str, owner: str, epoch: int,
                    verify_only: bool = False,
                    env: Optional[Mapping[str, str]] = None) -> Optional[LeaseToken]:
    """Publish (or verify) this worktree's token, when the feature is enabled.

    A single entry point so the execution path has one thing to call and one
    thing to test. Returns ``None`` when disabled — the caller then behaves
    exactly as before.
    """
    if not workspace_fence_enabled(env):
        return None
    token = LeaseToken(run_id=run_id, owner=owner, epoch=epoch)
    return verify_token(Path(worktree), token, adopt_missing=not verify_only)
