"""Native streaming quota boundary and host salvage, without provider I/O."""
from __future__ import annotations

import hashlib
import json
import os
import signal
import stat
import subprocess
import time
from pathlib import Path

from .quota_inflight import CooperativeQuotaCheckpoint
from .task_runtime import ExecutorRuntimeError, QuotaPauseOutcome


class QuotaBoundary(Exception):
    """A durable request exists; do not consume another protocol frame."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def workspace_manifest(root):
    """Read regular product bytes only; fail closed on links or substitutions."""
    root = Path(root)
    for component in (*reversed(root.parents), root):
        info = component.lstat()
        if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise OSError("quota_workspace_link")
    identity = root.stat()
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = sorted(d for d in dirs if d != ".git" and not d.startswith(".nt-") and d != ".nt")
        for name in dirs + sorted(files):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if relative == ".git" or relative.split("/")[0].startswith(".nt-"):
                continue
            before = path.lstat()
            if stat.S_ISLNK(before.st_mode) or getattr(before, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise OSError("quota_workspace_link")
            if stat.S_ISDIR(before.st_mode):
                continue
            if not stat.S_ISREG(before.st_mode):
                raise OSError("quota_workspace_special_file")
            content = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    content.update(chunk)
                after = os.fstat(stream.fileno())
            current = path.lstat()
            signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_mode)
            if signature(before) != signature(after) or signature(after) != signature(current):
                raise OSError("quota_workspace_changed")
            result[relative] = {"sha256": content.hexdigest(), "size": after.st_size, "mode": after.st_mode}
    after = root.stat()
    if (identity.st_dev, identity.st_ino) != (after.st_dev, after.st_ino):
        raise OSError("quota_workspace_replaced")
    return result


def stop_and_confirm(proc, job):
    """Confirm the owned process group/job is empty before reading saved bytes."""
    if job is not None:
        import ctypes
        from ctypes import wintypes
        # Terminate and query while retaining the job handle. Closing a job alone
        # requests asynchronous termination and does not prove descendants exited.
        kernel = job.kernel
        kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.TerminateJobObject.restype = wintypes.BOOL
        kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                                    wintypes.DWORD, ctypes.c_void_p]
        kernel.QueryInformationJobObject.restype = wintypes.BOOL
        class Accounting(ctypes.Structure):
            _fields_ = [("times", ctypes.c_longlong * 4), ("faults", wintypes.DWORD),
                        ("total", wintypes.DWORD), ("active", wintypes.DWORD), ("terminated", wintypes.DWORD)]
        if not kernel.TerminateJobObject(job.handle, 1):
            return False
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            info = Accounting()
            if not kernel.QueryInformationJobObject(job.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None):
                return False
            if info.active == 0:
                proc.wait(timeout=10)
                return proc.poll() is not None
            time.sleep(.01)
        return False
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait(timeout=10)
    try:
        os.killpg(proc.pid, 0)
    except ProcessLookupError:
        return proc.poll() is not None
    return False  # A surviving descendant (including an unreaped zombie) is ambiguous.


class NativeQuota:
    def __init__(self, store, run_id, owner, epoch, prepared, snapshot):
        self.store, self.run_id, self.owner, self.epoch = store, run_id, owner, epoch
        self.prepared, self.snapshot = prepared, snapshot
        self.sequence = 0
        self.checkpoint_id = "native-quota-" + digest([run_id, epoch, snapshot["attempt"], prepared.execution_id])
        self.control = CooperativeQuotaCheckpoint(checkpoint_id=self.checkpoint_id,
            journal=self.journal, request=lambda cp: None, verify=self.verify,
            stop=lambda cp: False, clock=time.time, signals=self.signals)

    def journal(self, state, payload):
        return self.store.quota_checkpoint(self.run_id, self.checkpoint_id, self.owner, self.epoch,
                                           state=state, payload=payload)

    def signals(self, **kwargs):
        return self.store.quota_live_signal(self.run_id, self.owner, self.epoch,
            self.snapshot["attempt"], self.snapshot["account_ref"], estimate=self.snapshot["need"], **kwargs)

    def observe(self, item):
        if item.get("type") != "quota.signal":
            return
        self.control.observe_signal(self.prepared.executor_kind, self.sequence,
                                    {k: item[k] for k in ("tokens", "rate_limit") if k in item})
        self.sequence += 1
        s = self.snapshot
        if self.control.tick(s["evidence"], s["need"], s["outstanding"],
                             reservation_id=s["reservation_id"], headroom=s["headroom"]) != "RUNNING":
            raise QuotaBoundary()

    def wait_verdict(self):
        wait = dict(self.control.wait_verdict or {})
        wait["confirmed_exhaustion"] = any(
            source.get("signal", {}).get("rate_limit", {}).get("status") == "rejected"
            for source in self.signals().get("sources", {}).values())
        if wait["confirmed_exhaustion"]:
            wait["reason"] = "provider_exhaustion"
        return wait

    def payload(self, summary, remaining_work, provenance):
        root = self.prepared.worktree
        identity = root.stat()
        value = {"workspace": str(root), "workspace_identity": [identity.st_dev, identity.st_ino],
                 "manifest": workspace_manifest(root),
                 "summary": summary or "Host preserved interrupted native work; completion unverified.",
                 "remaining_work": remaining_work,
                 "provenance": provenance, "agent_acknowledged": provenance == "cooperative_agent",
                 "quota_wait": self.wait_verdict(),
                 "reservation_claim": self.snapshot.get("reservation_claim"),
                 "usage_before": self.snapshot.get("usage_before", []),
                 "resume_state": {"run_id": self.run_id, "execution_id": self.prepared.execution_id,
                                  "epoch": self.epoch, "attempt": self.snapshot["attempt"],
                                  "account_ref": self.snapshot["account_ref"], "base_sha": self.prepared.base_sha,
                                  "executor_kind": self.prepared.executor_kind, "checkpoint_id": self.checkpoint_id}}
        value["artifact_digest"] = digest(value)
        return value

    def verify(self, value):
        try:
            raw = dict(value)
            proof = raw.pop("artifact_digest")
            identity = self.prepared.worktree.stat()
            return (proof == digest(raw) and value["workspace"] == str(self.prepared.worktree)
                    and value["workspace_identity"] == [identity.st_dev, identity.st_ino]
                    and value["resume_state"]["checkpoint_id"] == self.checkpoint_id
                    and value["resume_state"]["execution_id"] == self.prepared.execution_id
                    and value["resume_state"]["base_sha"] == self.prepared.base_sha
                    and value["resume_state"]["run_id"] == self.run_id
                    and value["resume_state"]["epoch"] == self.epoch
                    and value["resume_state"]["attempt"] == self.snapshot["attempt"]
                    and value["resume_state"]["account_ref"] == self.snapshot["account_ref"]
                    and value["resume_state"]["executor_kind"] == self.prepared.executor_kind
                    and value.get("quota_wait") == self.wait_verdict()
                    and value.get("reservation_claim") == self.snapshot.get("reservation_claim")
                    and value.get("usage_before") == self.snapshot.get("usage_before", [])
                    and value["manifest"] == workspace_manifest(self.prepared.worktree))
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def finish(self, proc, job, parser, prompt) -> QuotaPauseOutcome:
        state = "FAILED"
        provenance = "host_salvaged"
        try:
            cooperative = getattr(proc, "supports_quota_checkpoint", False) is True
            if cooperative:
                # Only an explicitly selected bidirectional transport may opt in.
                value = proc.request_quota_checkpoint(self.checkpoint_id)
                if (not isinstance(value, dict) or value.get("agent_acknowledged") is not True
                        or value.get("provenance") != "cooperative_agent" or not self.verify(value)):
                    raise ValueError("quota_save_unacknowledged")
                if proc.stop_quota_checkpoint(self.checkpoint_id) is not True:
                    raise ValueError("quota_stop_unacknowledged")
                provenance = "cooperative_agent"
            else:
                value = None
            if stop_and_confirm(proc, job) is not True:
                raise ValueError("quota_tree_stop_unconfirmed")
            if value is None:
                value = self.payload(parser.turn.final_text, prompt, provenance)
            if not self.verify(value):
                raise ValueError("quota_save_verification_failed")
            # Reuse interrupted-coder evidence without accepting a role milestone.
            from .opencode_executor import _collect_product_diff
            partial = _collect_product_diff(self.prepared.worktree)
            partial_digest = hashlib.sha256(json.dumps(list(partial), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            self.store._set_partial_coder_diff_digest(self.run_id, partial_digest, self.owner, self.epoch)
            self.journal("SAVED", value)
            self.journal("PAUSED", None)
            state = "PAUSED"
        except (OSError, ValueError, TypeError, AttributeError, ExecutorRuntimeError, subprocess.SubprocessError):
            self.journal("FAILED", None)
        return {"state": state, "checkpoint_id": self.checkpoint_id, "provenance": provenance,
                "agent_acknowledged": state == "PAUSED" and provenance == "cooperative_agent"}
