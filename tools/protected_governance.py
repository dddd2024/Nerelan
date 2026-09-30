"""Run existing governance lint from pinned source; candidate commits are data.

Start from an independently trusted copy with python -I -S -B. This read-only
shadow diagnostic is neither live authorization nor a hostile-code sandbox.
The caller owns the trusted Git repository/configuration, executable and pin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ENTRY = "tools/protected_governance.py"
DECISION = "project_state/decision_packet.md"
SOURCES = (
    "reverse_agent/__init__.py",
    "reverse_agent/control_plane/__init__.py",
    "reverse_agent/control_plane/evidence_source.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/transition.py",
)
MAX_FILE = 1024 * 1024
MAX_DECISION = 256 * 1024
MAX_OUTPUT = 64 * 1024
SHA = re.compile(r"[0-9a-f]{40}\Z")
DENIED = (
    "approval_granted", "implementation_authority", "ready_authority",
    "merge_authority", "product_accepted", "implementation_complete",
    "candidate_code_executed", "issue_commands_executed",
)


class BoundaryError(ValueError):
    """A bounded, non-secret diagnostic code."""


def _result(status: str, **observations: object) -> dict:
    return {"status": status, "claim_scope": "SHADOW_ONLY",
            **dict.fromkeys(DENIED, False), **observations}


def _isolated() -> None:
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise BoundaryError("isolated_startup_required")


def _sha(value: str) -> str:
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise BoundaryError("immutable_commit_required")
    return value


def _environment(home: Path) -> dict[str, str]:
    # No token, proxy, Python startup, loader or caller Git override is inherited.
    return {
        "HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0",
    }


def _process(argv: list[str], *, cwd: Path, env: dict[str, str],
             deadline: float, limit: int, data: bytes | None = None) -> tuple[int, bytes]:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise BoundaryError("execution_timeout")
    # Bound memory, not just the JSON parser; never echo child stderr/commands.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            process = subprocess.run(argv, input=data, stdout=out, stderr=err,
                                     cwd=cwd, env=env, timeout=remaining, check=False)
        except subprocess.TimeoutExpired as exc:
            raise BoundaryError("execution_timeout") from exc
        if out.tell() > limit or err.tell() > MAX_OUTPUT:
            raise BoundaryError("execution_output_too_large")
        out.seek(0)
        return process.returncode, out.read(limit + 1)


class Objects:
    def __init__(self, repository: Path, git: Path, home: Path, deadline: float):
        self.repository, self.git = repository, git
        self.env, self.deadline = _environment(home), deadline

    def read(self, *args: str, limit: int = MAX_FILE) -> bytes:
        argv = [str(self.git), "--no-pager", "--literal-pathspecs",
                "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}",
                "-c", "credential.helper=", "-c", "protocol.allow=never", *args]
        code, data = _process(argv, cwd=self.repository, env=self.env,
                              deadline=self.deadline, limit=limit)
        if code:
            raise BoundaryError("git_object_read_failed")
        return data

    def commit(self, ref: str) -> str:
        ref = _sha(ref)
        if self.read("cat-file", "-t", ref, limit=64) != b"commit\n":
            raise BoundaryError("object_is_not_commit")
        return ref

    def file(self, ref: str, path: str, limit: int = MAX_FILE) -> tuple[bytes, dict]:
        # Only repository-owned constants call this method. ls-tree does not
        # dereference filesystem symlinks, checkout filters or submodules.
        raw = self.read("ls-tree", "-z", ref, "--", path, limit=4096)
        records = raw.split(b"\0")
        if len(records) != 2 or records[1] != b"":
            raise BoundaryError("source_missing_or_ambiguous")
        try:
            metadata, name = records[0].split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split(" ")
        except (UnicodeError, ValueError) as exc:
            raise BoundaryError("source_metadata_invalid") from exc
        if name != path.encode("utf-8") or kind != "blob" or mode not in {"100644", "100755"}:
            raise BoundaryError("source_not_regular_file")
        _sha(oid)
        size_raw = self.read("cat-file", "-s", oid, limit=64).strip()
        if not size_raw.isdigit() or len(size_raw) > 10:
            raise BoundaryError("source_size_invalid")
        size = int(size_raw)
        if size > limit:
            raise BoundaryError("source_too_large")
        data = self.read("cat-file", "blob", oid, limit=limit)
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if len(data) != size or actual != oid:
            raise BoundaryError("source_object_mismatch")
        return data, {"blob": oid, "sha256": hashlib.sha256(data).hexdigest(),
                      "mode": mode, "size": size}


def _worker() -> int:
    """Internal isolated process: no Git access, network or command execution."""
    _isolated()
    root = Path(__file__).resolve().parents[1]
    data = sys.stdin.buffer.read(MAX_DECISION + 1)
    if len(data) > MAX_DECISION:
        raise BoundaryError("decision_too_large")
    text = data.decode("utf-8", errors="strict")
    for name in ("decision_meta", "decision_contract"):
        if len(re.findall(r"```json\s+" + name + r"\s*\n", text)) != 1:
            raise BoundaryError("decision_blocks_ambiguous")
    # Only exported .py files exist here; no candidate path or site-packages.
    sys.path.insert(0, str(root))
    from reverse_agent.control_plane.legacy_adapter import (
        load_transition_decision, build_transition_command_plan,
    )
    from reverse_agent.control_plane.command_authority import validate_command_plan

    decision_file = root / "candidate_decision.md"
    decision_file.write_bytes(data)
    decision, contract = load_transition_decision(decision_file)
    plan = build_transition_command_plan(decision, contract)
    errors = validate_command_plan(plan)
    valid = (not errors and decision.status == "APPROVED"
             and bool(decision.skill_profiles)
             and contract.get("transition_kernel_required") is True)
    # Bind actually imported project modules to the exported closure.
    loaded = {}
    for name, module in tuple(sys.modules.items()):
        if name != "reverse_agent" and not name.startswith("reverse_agent."):
            continue
        origin = Path(module.__file__).resolve()
        relative = origin.relative_to(root).as_posix()
        if relative not in SOURCES:
            raise BoundaryError("unlisted_project_import")
        loaded[relative] = hashlib.sha256(origin.read_bytes()).hexdigest()
    output = _result("VALID" if valid else "INVALID", loaded_sources=loaded,
                     command_count=len(plan.commands), error_count=len(errors),
                     error_codes=sorted({error.split(":", 1)[0] for error in errors})[:64],
                     interpreter=sys.version, interpreter_executable=sys.executable,
                     isolated=bool(sys.flags.isolated), no_site=bool(sys.flags.no_site),
                     environment_keys=sorted(os.environ))
    print(json.dumps(output, sort_keys=True))
    return 0 if valid else 1


def run(repository: Path, git: Path, trusted_ref: str, candidate_ref: str) -> dict:
    _isolated()
    _sha(trusted_ref)
    _sha(candidate_ref)
    if os.name != "posix":
        raise BoundaryError("posix_host_required")
    if not repository.is_absolute() or not repository.is_dir():
        raise BoundaryError("trusted_repository_required")
    if not git.is_absolute() or not git.is_file() or not os.access(git, os.X_OK):
        raise BoundaryError("absolute_trusted_git_required")
    deadline = time.monotonic() + 30
    with tempfile.TemporaryDirectory(prefix="nerelan-protected-") as temporary:
        root = Path(temporary)
        home = root / "home"
        home.mkdir(mode=0o700)
        objects = Objects(repository.resolve(), git.resolve(), home, deadline)
        trusted_ref, candidate_ref = objects.commit(trusted_ref), objects.commit(candidate_ref)
        source_records = {}
        for path in (ENTRY, *SOURCES):
            data, record = objects.file(trusted_ref, path)
            if path == ENTRY and data != Path(__file__).read_bytes():
                raise BoundaryError("launcher_does_not_match_trusted_pin")
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            destination.chmod(0o600)
            source_records[path] = record
        candidate, candidate_record = objects.file(candidate_ref, DECISION, MAX_DECISION)
        code, raw = _process(
            [sys.executable, "-I", "-S", "-B", str(root / ENTRY), "--worker"],
            cwd=home, env=_environment(home), deadline=min(deadline, time.monotonic() + 10),
            limit=MAX_OUTPUT, data=candidate,
        )
        try:
            observed = json.loads(raw)
            if not isinstance(observed, dict):
                raise ValueError()
            valid = observed["status"] == "VALID"
            if observed["status"] not in {"VALID", "INVALID"} or code != (0 if valid else 1):
                raise ValueError()
            if any(observed.get(key) is not False for key in DENIED):
                raise ValueError()
            loaded = observed["loaded_sources"]
            if not isinstance(loaded, dict) or set(loaded) != set(SOURCES):
                raise ValueError()
            if any(digest != source_records[path]["sha256"] for path, digest in loaded.items()):
                raise ValueError()
            if observed.get("claim_scope") != "SHADOW_ONLY" or observed.get("isolated") is not True or observed.get("no_site") is not True:
                raise ValueError()
            if set(observed["environment_keys"]) - set(_environment(home)):
                raise ValueError()
        except (ValueError, TypeError, KeyError) as exc:
            raise BoundaryError("worker_failed_or_invalid_output") from exc
        return _result(
            "VALID" if valid else "INVALID", trusted_ref=trusted_ref,
            candidate_ref=candidate_ref, candidate_decision=candidate_record,
            source_closure=source_records, worker=observed,
        )


def main(argv: list[str] | None = None) -> int:
    try:
        if (sys.argv[1:] if argv is None else argv) == ["--worker"]:
            return _worker()
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--repository-dir", type=Path, required=True)
        parser.add_argument("--git-executable", type=Path, required=True)
        parser.add_argument("--trusted-ref", required=True)
        parser.add_argument("--candidate-ref", required=True)
        args = parser.parse_args(argv)
        result = run(args.repository_dir, args.git_executable, args.trusted_ref, args.candidate_ref)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "VALID" else 1
    except BoundaryError as exc:
        print(json.dumps(_result("ERROR", diagnostic=str(exc)), sort_keys=True))
        return 2
    except (OSError, ValueError, TypeError, KeyError, ImportError, RecursionError):
        # Avoid printing candidate data, secret paths or arbitrary exception text.
        print(json.dumps(_result("ERROR", diagnostic="protected_execution_failed"), sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
