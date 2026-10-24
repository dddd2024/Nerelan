"""Owner-configured, durable remote experiment broker (no provider calls).

Only the trusted host loads profiles. Requests are data, not host commands.
The remote Python helper requires Python 3, bash, setsid and nohup on the server.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass, replace
import hashlib
import json
import logging
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shlex
import subprocess
import threading
import time
import uuid
from typing import Callable, Protocol


ENV_PROFILE = "REVERSE_AGENT_REMOTE_JOB_PROFILE"
LOG = logging.getLogger(__name__)
JOB_ID = re.compile(r"[a-z0-9][a-z0-9._-]{2,63}\Z")
REQUEST_FIELDS = ("job_id", "command", "files", "outputs", "max_wall_seconds", "gpu", "purpose")
TERMINAL = {"SUCCEEDED", "FAILED", "TIMED_OUT", "LOST"}
LOG_LIMIT = 1024 * 1024


def _relative(value: str) -> str:
    if (not isinstance(value, str) or not value or "\\" in value
            or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value)
            or PurePosixPath(value).is_absolute()
            or PureWindowsPath(value).drive
            or any(p in {"", ".", ".."} for p in value.split("/"))):
        raise ValueError("expected relative path without '..': %r" % (value,))
    return value


def _positive(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(name + " must be a positive integer")
    return value


@dataclass(frozen=True)
class RemoteJobProfile:
    ssh_alias: str
    remote_root: str
    local_root: Path
    scan_roots: tuple[Path, ...]
    max_concurrent: int = 1
    max_wall_seconds: int = 21600
    gpu_devices: tuple[str, ...] = ("0",)
    max_upload_bytes: int = 52428800
    max_download_bytes: int = 524288000
    poll_seconds: int = 30
    termination_grace_seconds: int = 30

    def __post_init__(self):
        _relative(self.remote_root)
        if self.remote_root != "wjc" and not self.remote_root.startswith("wjc/"):
            raise ValueError("remote_root must be wjc or beneath wjc/")
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", self.ssh_alias):
            raise ValueError("invalid ssh_alias")
        for name in ("max_concurrent", "max_wall_seconds", "max_upload_bytes",
                     "max_download_bytes", "poll_seconds", "termination_grace_seconds"):
            _positive(getattr(self, name), name)
        if not isinstance(self.gpu_devices, (list, tuple)) or any(
                not isinstance(d, str) or not re.fullmatch(r"[0-9]+", d)
                for d in self.gpu_devices):
            raise ValueError("gpu_devices must contain device numbers")
        if not isinstance(self.scan_roots, (list, tuple)) or not self.scan_roots:
            raise ValueError("scan_roots must be a nonempty list")
        object.__setattr__(self, "local_root", Path(self.local_root).absolute())
        object.__setattr__(self, "scan_roots", tuple(Path(p).absolute() for p in self.scan_roots))

    @classmethod
    def load(cls, path):
        return cls(**json.loads(Path(path).read_text(encoding="utf-8")))


class Transport(Protocol):
    def run(self, argv: list[str], timeout: int,
            stdin_text: str | None = None) -> tuple[int, str, str]: ...
    def upload(self, local_dir: Path, remote_dir: str) -> None: ...
    def download(self, remote_path: str, local_path: Path) -> None: ...


class SSHTransport:
    def __init__(self, profile: RemoteJobProfile):
        self.alias = profile.ssh_alias

    def run(self, argv, timeout, stdin_text=None):
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                                encoding="utf-8", errors="replace", check=False,
                                input=stdin_text)
        return result.returncode, result.stdout, result.stderr

    def _scp(self, args):
        code, _, err = self.run(["scp", "-O", "-o", "BatchMode=yes", "-o",
                                 "ConnectTimeout=20", *args], 120)
        if code:
            raise OSError("scp failed: " + err[-2000:])

    def upload(self, local_dir, remote_dir):
        # scp derives the remote filename from the *local argument*.  On Windows that
        # argument is an absolute path with backslashes, which POSIX scp keeps
        # verbatim: a job uploaded from F://...//request//run.py lands as a single file
        # literally named "F://...//request//run.py", the launch then cannot find
        # run.py, and the receipt records a failed job.  Name every remote file
        # explicitly instead of relying on basename rules of the local platform.
        for entry in sorted(local_dir.iterdir()):
            target = self.alias + ":" + shlex.quote(remote_dir + "/" + entry.name)
            self._scp((["-r"] if entry.is_dir() else []) + [str(entry), target])

    def download(self, remote_path, local_path):
        self._scp([self.alias + ":" + shlex.quote(remote_path), str(local_path)])


# One fixed helper, passed as a quoted Python argument. No model text is ever
# interpolated into this program or evaluated by a local shell.
REMOTE_HELPER = r'''
import base64, glob, hashlib, json, os, pathlib, signal, subprocess, sys, time
p = json.loads(sys.argv[1])
root = pathlib.Path.home() / p['root']
job = root / p['job_id']
home_wjc = pathlib.Path.home() / 'wjc'
def safe(path):
    # Reject symlinks in every existing component, including the configured root.
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise ValueError('remote symlink refused')
    path.resolve().relative_to(home_wjc.resolve())
    return path
safe(job)
job.mkdir(parents=True, exist_ok=True)
os.chdir(job)
marker = job / 'launch.json'
for name in ('launch.json', 'pid', 'exit_code', 'stdout.log', 'stderr.log', 'launch.tmp'):
    safe(job / name)
def save_marker(info):
    temporary = safe(job / 'launch.tmp')
    with temporary.open('w') as f:
        json.dump(info, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, marker)

def stat(pid):
    # comm may contain spaces and parentheses. Fields after its last ')' start at 3.
    fields = pathlib.Path('/proc/%s/stat' % pid).read_text().rsplit(')', 1)[1].split()
    return fields[0], int(fields[2]), int(fields[3]), int(fields[19])

def group_alive(pid, info):
    if (type(info.get('start_time')) is not int or info['start_time'] < 0
            or not isinstance(info.get('boot_id'), str) or not info['boot_id']):
        raise ValueError('missing process identity')
    if pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip() != info['boot_id']:
        raise ValueError('boot identity mismatch')
    try:
        leader = stat(pid)
    except (FileNotFoundError, ProcessLookupError):
        leader = None
    if leader is not None and leader[3] != info['start_time']:
        raise ValueError('process identity mismatch')
    # A dead leader does not imply a dead group. Include surviving descendants,
    # but never a group/session whose members predate the recorded leader.
    alive = False
    for entry in pathlib.Path('/proc').iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            state, group, session, start = stat(int(entry.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
        if group == pid:
            if session != pid or start < info['start_time']:
                raise ValueError('process group identity mismatch')
            alive |= state != 'Z'
    if alive:
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            return False
    return alive

op = p['op']
answer = {}
if op == 'probe':
    answer = {'marker': marker.exists()}
elif op == 'launch':
    try:
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        answer = {'marker': True}
    else:
        # Reserve before spawn: even a crash between these operations never
        # permits a second invocation. An incomplete reservation becomes LOST.
        with os.fdopen(fd, 'w') as f:
            json.dump({'job_id': p['job_id'], 'request_digest': p['digest'],
                       'launched_at': p['now']}, f)
            f.flush()
            os.fsync(f.fileno())
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=p['devices'])
        # The command runs in a child bash so `exit` cannot skip exit_code.
        import shlex
        wrapper = 'bash -c ' + shlex.quote(p['command']) + '; rc=$?; printf "%s\\n" "$rc" > exit_code'
        with open('stdout.log', 'ab') as out, open('stderr.log', 'ab') as err:
            proc = subprocess.Popen(['setsid', 'nohup', 'bash', '-c', wrapper],
                                    stdin=subprocess.DEVNULL, stdout=out, stderr=err, env=env)
        pathlib.Path('pid').write_text(str(proc.pid))
        info = json.loads(marker.read_text())
        info.update(pid=proc.pid, start_time=stat(proc.pid)[3],
                    boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                    termination_grace_seconds=p['grace'])
        save_marker(info)
        answer = {'marker': True}
elif op == 'poll':
    try:
        info = json.loads(marker.read_text())
        if not isinstance(info, dict):
            info = {}
    except (FileNotFoundError, ValueError):
        info = {}
    answer['launched_at'] = info.get('launched_at', p['fallback_launched_at'])
    answer['request_digest'] = info.get('request_digest')
    try:
        pid = info['pid']
        if type(pid) is not int or pid <= 1:
            raise ValueError('invalid pid')
        alive = group_alive(pid, info)
        timed_out = 'term_sent_at' in info
        if timed_out or (alive and p['now'] - answer['launched_at'] > p['wall']):
            if alive:
                if not timed_out:
                    info['term_sent_at'] = p['now']
                    save_marker(info)
                    try:
                        os.killpg(pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                elif p['now'] - info['term_sent_at'] >= info['termination_grace_seconds']:
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                alive = group_alive(pid, info)
            answer['state'] = 'TIMED_OUT_KILL_PENDING' if alive else 'TIMED_OUT'
        elif pathlib.Path('exit_code').exists():
            answer['state'] = 'SUCCEEDED' if int(pathlib.Path('exit_code').read_text()) == 0 else 'FAILED'
        else:
            answer['state'] = 'RUNNING' if alive else 'LOST'
    except (FileNotFoundError, ProcessLookupError, PermissionError, KeyError, TypeError, ValueError):
        answer['state'] = 'LOST'
elif op == 'collect':
    snapshot = safe(job / '.nerelan-results' / p['digest'])
    snapshot.mkdir(parents=True, exist_ok=True)
    completed = safe(snapshot / 'collection.json')
    if completed.exists():
        print(completed.read_text())
        sys.exit(0)
    files, total = [], 0
    for pattern in p['outputs']:
        for name in sorted(glob.glob(pattern, recursive=True)):
            path = safe(job / name)
            name = path.relative_to(job).as_posix()
            if name.split('/')[0] == '.nerelan-results':
                continue
            if not path.is_file() or name in {x['path'] for x in files}:
                continue
            if path.stat().st_size + total > p['cap']:
                raise ValueError('max_download_bytes exceeded')
            # Freeze a bounded snapshot before scp. A still-writing descendant
            # cannot turn a small stat result into an unbounded download.
            target = safe(snapshot / (str(len(files)) + '.bin'))
            size, digest = 0, hashlib.sha256()
            with path.open('rb') as source, target.open('wb') as dest:
                while True:
                    chunk = source.read(min(65536, p['cap'] - total + 1))
                    if not chunk:
                        break
                    total += len(chunk)
                    size += len(chunk)
                    if total > p['cap']:
                        raise ValueError('max_download_bytes exceeded')
                    digest.update(chunk)
                    dest.write(chunk)
            files.append({'path': name, 'size': size, 'sha256': digest.hexdigest(),
                          'remote_path': target.relative_to(job).as_posix()})
    answer = {'files': files, 'logs': {}}
    for name in ('stdout.log', 'stderr.log'):
        path = safe(job / name)
        if path.exists():
            with path.open('rb') as f:
                f.seek(max(0, path.stat().st_size - 1048576))
                data = f.read(1048576)
        else:
            data = b''
        answer['logs'][name] = base64.b64encode(data).decode('ascii')
    temporary = safe(snapshot / 'collection.tmp')
    with temporary.open('w') as f:
        json.dump(answer, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, completed)
print(json.dumps(answer))
'''

# The remote interpreter reads its program from stdin. Passing the quoted
# helper and the JSON request on the ssh command line instead does not fit in
# the Windows process command line (8191 characters): the helper alone expands
# from 8067 to ~8.8k characters once shlex.quote escapes its 236 single quotes,
# and the tail is silently truncated, leaving the remote shell with an
# unterminated quote ("unexpected EOF while looking for matching '"). Keeping
# the command line at "python3 -" also means no shell metacharacter is ever
# interpreted on the way out.
REMOTE_COMMAND = ("python3", "-")
REMOTE_COMMAND_LINE_LIMIT = 8191


def _remote_program(data: dict) -> str:
    """Return the program text the remote interpreter executes from stdin.

    The request JSON is handed to the unchanged helper through ``sys.argv`` so
    the helper keeps its single documented input contract, and none of the
    payload touches the command line.
    """
    request = json.dumps(data, sort_keys=True)
    return "import sys as _sys\n_sys.argv = ['-', " + json.dumps(request) + "]\n" + REMOTE_HELPER


def _atomic_json(path: Path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _hash(path, max_bytes=None):
    with path.open("rb") as stream:
        if max_bytes is None:
            return hashlib.file_digest(stream, "sha256").hexdigest()
        digest, size = hashlib.sha256(), 0
        while chunk := stream.read(min(65536, max_bytes - size + 1)):
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("max_upload_bytes exceeded")
            digest.update(chunk)
        return digest.hexdigest()


def _copy_limited(source, dest, limit):
    if any(p.is_symlink() for p in (source, *source.parents)):
        raise ValueError("symlinks are forbidden")
    size = 0
    with source.open("rb") as inp, dest.open("wb") as out:
        while chunk := inp.read(min(65536, limit - size + 1)):
            size += len(chunk)
            if size > limit:
                raise ValueError("upload changed size while freezing")
            out.write(chunk)
    return size


def _fingerprint(path):
    try:
        with path.open("rb") as stream:
            return hashlib.sha256(stream.read(65537)).hexdigest()
    except OSError as exc:
        return "unreadable:" + str(exc)


class _BrokerStopped(Exception):
    pass


class RemoteJobBroker:
    def __init__(self, profile: RemoteJobProfile, transport: Transport | None = None,
                 clock: Callable[[], float] = time.time):
        self.profile = profile
        self.transport = transport or SSHTransport(profile)
        self.clock = clock
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        profile.local_root.mkdir(parents=True, exist_ok=True)

    def receipts(self):
        return [json.loads(p.read_text(encoding="utf-8")) for p in
                sorted(self.profile.local_root.glob("*/receipt.json"))]

    def _save(self, receipt):
        _atomic_json(self.profile.local_root / receipt["job_id"] / "receipt.json", receipt)

    def _event(self, receipt, state, detail=""):
        receipt["state"] = state
        receipt["history"].append({"state": state, "at": self.clock(), "detail": detail})
        self._save(receipt)

    def _request(self, path):
        with path.open("rb") as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError("job.json exceeds 64 KiB")
        request = json.loads(raw)
        if not isinstance(request, dict) or set(request) != set(REQUEST_FIELDS):
            raise ValueError("unknown or missing request fields")
        if not isinstance(request["job_id"], str) or not JOB_ID.fullmatch(request["job_id"]):
            raise ValueError("invalid job_id")
        if request["job_id"] != path.parent.name:
            raise ValueError("job_id must match outbox directory")
        if (not isinstance(request["command"], str) or not 1 <= len(request["command"]) <= 4000
                or "\x00" in request["command"]):
            raise ValueError("command must contain 1..4000 characters without NUL")
        if not isinstance(request["purpose"], str) or type(request["gpu"]) is not bool:
            raise ValueError("invalid purpose or gpu")
        if _positive(request["max_wall_seconds"], "max_wall_seconds") > self.profile.max_wall_seconds:
            raise ValueError("max_wall_seconds exceeds profile limit")
        for name in ("files", "outputs"):
            if not isinstance(request[name], list) or len(set(request[name])) != len(request[name]):
                raise ValueError(name + " must be a list of unique paths")
            for value in request[name]:
                _relative(value)
        hashes, total = {}, 0
        for name in request["files"]:
            if name.split("/")[0] in {"job.json", "launch.json", "pid", "exit_code", "stdout.log", "stderr.log", "launch.tmp", ".nerelan-results"}:
                raise ValueError("broker control paths are reserved")
            file = path.parent / name
            if any(p.is_symlink() for p in (file, *file.parents)):
                raise ValueError("symlinks are forbidden")
            file.resolve().relative_to(path.parent.resolve())
            if not file.is_file():
                raise ValueError("upload is not a regular file: " + name)
            size = file.stat().st_size
            remaining = self.profile.max_upload_bytes - total
            if size > remaining:
                raise ValueError("max_upload_bytes exceeded")
            hashes[name] = _hash(file, remaining)
            total += size
        digest = hashlib.sha256(raw + json.dumps(hashes, sort_keys=True).encode()).hexdigest()
        return request, digest

    def _discover(self):
        for root in self.profile.scan_roots:
            for path in sorted(root.glob("*/.nerelan-remote/outbox/*/job.json")):
                # Never follow worktree/outbox symlinks supplied by a request.
                if any(p.is_symlink() for p in (path, *path.parents)):
                    continue
                job_id = path.parent.name
                # Invalid IDs still get a safe, deterministic receipt directory.
                safe_id = job_id if JOB_ID.fullmatch(job_id) else "rejected-" + hashlib.sha256(str(path).encode()).hexdigest()[:24]
                directory = self.profile.local_root / safe_id
                existing = directory / "receipt.json"
                try:
                    request, digest = self._request(path)
                    error = None
                except (ValueError, OSError, TypeError) as exc:
                    request, digest, error = None, None, str(exc)
                if existing.exists():
                    receipt = json.loads(existing.read_text(encoding="utf-8"))
                    fingerprint = digest or _fingerprint(path)
                    seen = receipt.setdefault("seen_request_digests", [receipt.get("observed_digest")])
                    if fingerprint not in seen:
                        seen.append(fingerprint)
                        receipt["observed_digest"] = fingerprint
                        self._event(receipt, receipt["state"], "DUPLICATE_ID_CHANGED_REQUEST")
                    continue
                directory.mkdir(parents=True, exist_ok=True)
                receipt = {"job_id": safe_id, "source": str(path), "history": [],
                           "discovered_at": self.clock(), "request_digest": digest,
                           "observed_digest": digest or _fingerprint(path)}
                if error:
                    self._event(receipt, "REJECTED", error)
                    continue
                frozen = directory / "request"
                if frozen.exists():
                    self._event(receipt, "REJECTED", "incomplete local preparation; use a new job_id")
                    continue
                try:
                    frozen.mkdir()
                    _copy_limited(path, frozen / "job.json", 65536)
                    size = 0
                    for name in request["files"]:
                        dest = frozen / name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        size += _copy_limited(path.parent / name, dest, self.profile.max_upload_bytes - size)
                except (OSError, ValueError) as exc:
                    self._event(receipt, "REJECTED", "cannot freeze request: " + str(exc))
                    continue
                receipt["request"] = request
                snapshot_hashes = {name: _hash(frozen / name) for name in request["files"]}
                snapshot_digest = hashlib.sha256((frozen / "job.json").read_bytes() +
                    json.dumps(snapshot_hashes, sort_keys=True).encode()).hexdigest()
                if snapshot_digest != digest:
                    self._event(receipt, "REJECTED", "request changed while freezing")
                    continue
                self._event(receipt, "PREPARED")

    def _remote(self, receipt, op):
        request = receipt["request"]
        data = {"op": op, "root": self.profile.remote_root, "job_id": receipt["job_id"],
                "digest": receipt["request_digest"], "now": self.clock(),
                "command": request["command"], "outputs": request["outputs"],
                "wall": request["max_wall_seconds"], "cap": self.profile.max_download_bytes,
                "fallback_launched_at": receipt.get("launch_attempted_at", receipt["discovered_at"]),
                "grace": self.profile.termination_grace_seconds,
                "devices": ",".join(self.profile.gpu_devices) if request["gpu"] else ""}
        argv = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
                self.profile.ssh_alias, *REMOTE_COMMAND]
        command_length = sum(len(part) + 1 for part in argv)
        if command_length > REMOTE_COMMAND_LINE_LIMIT:
            raise OSError("ssh command line exceeds the platform limit")
        code, out, err = self.transport.run(argv, 120, stdin_text=_remote_program(data))
        if self._stop.is_set():
            raise _BrokerStopped()
        if code:
            raise OSError("ssh failed: " + err[-2000:])
        result = json.loads(out)
        self._validate_reply(op, result)
        return result

    def _validate_reply(self, op, result):
        if not isinstance(result, dict):
            raise ValueError("remote reply must be an object")
        if op in {"probe", "launch"}:
            if type(result.get("marker")) is not bool:
                raise ValueError("remote reply requires boolean marker")
        elif op == "poll":
            if (type(result.get("launched_at")) not in {int, float}
                    or "request_digest" not in result
                    or (result["request_digest"] is not None and not isinstance(result["request_digest"], str))):
                raise ValueError("invalid remote poll metadata")
            if not isinstance(result.get("state"), str) or result["state"] not in TERMINAL | {"RUNNING", "TIMED_OUT_KILL_PENDING"}:
                raise ValueError("invalid remote state")
        elif op == "collect":
            if not isinstance(result.get("files"), list) or not isinstance(result.get("logs"), dict):
                raise ValueError("remote collection requires files and logs")
            for item in result["files"]:
                if not isinstance(item, dict):
                    raise ValueError("invalid collection file")
                _relative(item.get("path"))
                _relative(item.get("remote_path"))
                if (type(item.get("size")) is not int or item["size"] < 0
                        or not isinstance(item.get("sha256"), str)
                        or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])):
                    raise ValueError("invalid collection metadata")
            for name in ("stdout.log", "stderr.log"):
                data = result["logs"].get(name)
                if not isinstance(data, str) or len(base64.b64decode(data, validate=True)) > LOG_LIMIT:
                    raise ValueError("invalid log tail")

    def _collect(self, receipt):
        listing = self._remote(receipt, "collect")
        directory = self.profile.local_root / receipt["job_id"]
        manifest, total = [], 0
        for item in listing["files"]:
            if self._stop.is_set():
                raise _BrokerStopped()
            name = _relative(item["path"])
            total += item["size"]
            if total > self.profile.max_download_bytes:
                raise ValueError("max_download_bytes exceeded")
            dest = directory / "outputs" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            remote_path = _relative(item["remote_path"])
            self.transport.download(self.profile.remote_root + "/" + receipt["job_id"] + "/" + remote_path, dest)
            if self._stop.is_set():
                raise _BrokerStopped()
            if dest.is_symlink() or dest.stat().st_size != item["size"]:
                raise ValueError("download changed size or is symlink")
            digest = _hash(dest)
            if digest != item["sha256"]:
                raise ValueError("download hash mismatch")
            manifest.append({"path": "outputs/" + name, "size": dest.stat().st_size, "sha256": digest})
        (directory / "outputs").mkdir(exist_ok=True)
        for name in ("stdout.log", "stderr.log"):
            data = base64.b64decode(listing["logs"][name], validate=True)
            if len(data) > LOG_LIMIT:
                raise ValueError("log tail exceeds limit")
            (directory / name).write_bytes(data)
            manifest.append({"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        _atomic_json(directory / "manifest.json", {"request_digest": receipt["request_digest"],
                     "remote_request_digest": receipt.get("remote_request_digest"), "files": manifest})
        self._event(receipt, "RESULT_COLLECTED", receipt["outcome"])

    def tick(self):
        # File locking also excludes a manual CLI tick from the host daemon.
        with self._lock, _BrokerLock(self.profile.local_root / ".broker.lock"):
            self._discover()
            receipts = sorted(self.receipts(), key=lambda r: (r["discovered_at"], r["job_id"]))
            # Reconcile pre-existing remote markers even when all local slots
            # are occupied. Recovery is observation, not a new submission.
            for receipt in receipts:
                if self._stop.is_set():
                    return
                if receipt["state"] != "PREPARED" or receipt.get("retry_at", 0) > self.clock():
                    continue
                try:
                    if self._remote(receipt, "probe")["marker"]:
                        self._event(receipt, "LAUNCHED", "recovered remote launch marker")
                except _BrokerStopped:
                    return
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    self._error(receipt, exc)
            active = sum(r["state"] in {"LAUNCHED", "RUNNING", "UPLOADED", "TIMED_OUT_KILL_PENDING"} for r in receipts)
            for receipt in receipts:
                if self._stop.is_set():
                    return
                if receipt["state"] in {"REJECTED", "RESULT_COLLECTED"} or receipt.get("retry_at", 0) > self.clock():
                    continue
                try:
                    state = receipt["state"]
                    if state == "PREPARED":
                        if active >= self.profile.max_concurrent:
                            continue
                        self.transport.upload(self.profile.local_root / receipt["job_id"] / "request",
                            self.profile.remote_root + "/" + receipt["job_id"])
                        if self._stop.is_set():
                            return
                        self._event(receipt, "UPLOADED")
                        active += 1
                    if self._stop.is_set():
                        return
                    if receipt["state"] == "UPLOADED":
                        if "launch_attempted_at" not in receipt:
                            receipt["launch_attempted_at"] = self.clock()
                            self._save(receipt)
                        self._remote(receipt, "launch")
                        self._event(receipt, "LAUNCHED")
                    if receipt["state"] in {"LAUNCHED", "RUNNING", "TIMED_OUT_KILL_PENDING"}:
                        result = self._remote(receipt, "poll")
                        remote_digest = result.get("request_digest")
                        if remote_digest and remote_digest != receipt.get("remote_request_digest"):
                            receipt["remote_request_digest"] = remote_digest
                            if remote_digest != receipt["request_digest"]:
                                self._event(receipt, receipt["state"], "remote launch marker has a different request digest")
                        state = result["state"]
                        if state not in TERMINAL | {"RUNNING", "TIMED_OUT_KILL_PENDING"}:
                            raise ValueError("invalid remote state")
                        if state in TERMINAL:
                            receipt["outcome"] = state
                            active -= 1
                        if state != receipt["state"]:
                            self._event(receipt, state)
                    if receipt["state"] in TERMINAL:
                        self._collect(receipt)
                    receipt["errors"] = 0
                    receipt["retry_at"] = 0
                    self._save(receipt)
                except _BrokerStopped:
                    return
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    self._error(receipt, exc)

    def _error(self, receipt, exc):
        receipt["errors"] = receipt.get("errors", 0) + 1
        receipt["retry_at"] = self.clock() + min(600, self.profile.poll_seconds * 2 ** min(receipt["errors"], 10))
        self._event(receipt, receipt["state"], "transport/collection error: " + str(exc)[:2000])

    def start(self):
        if self._thread and self._thread.is_alive():
            raise RuntimeError("remote broker already started")
        self._stop.clear()
        def loop():
            while not self._stop.is_set():
                try:
                    self.tick()
                except Exception:
                    LOG.exception("remote job broker tick failed")
                self._stop.wait(self.profile.poll_seconds)
        self._thread = threading.Thread(target=loop, name="remote-jobs", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)


class _BrokerLock:
    """OS-released advisory lock; a crashed host cannot strand a lock file."""
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.stream = self.path.open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                if self.stream.tell() == 0:
                    self.stream.write(b"0")
                    self.stream.flush()
                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.stream.close()
            raise
        return self

    def __exit__(self, *args):
        self.stream.close()


def configured_broker():
    path = os.environ.get(ENV_PROFILE)
    if not path:
        return None
    try:
        return RemoteJobBroker(RemoteJobProfile.load(path))
    except (OSError, TypeError, ValueError):
        LOG.exception("invalid remote job profile; broker disabled")
        return None


def smoke(profile: RemoteJobProfile):
    """Opt-in real-server check. Never invoked by startup, CI or unit tests.

    Retain requests, receipts and the displaced receipt directory as evidence.
    The GPU case checks device visibility; it does not benchmark GPU hardware.
    """
    if profile.max_wall_seconds < 10 or not profile.gpu_devices:
        raise ValueError("smoke needs max_wall_seconds >= 10 and configured GPU devices")
    prefix = "smoke-" + uuid.uuid4().hex[:16]
    evidence = profile.local_root / prefix
    workspace = evidence / "workspaces"
    isolated = replace(profile, local_root=evidence / "receipts", scan_roots=(workspace,),
                       poll_seconds=1)
    broker = RemoteJobBroker(isolated)
    report = {"smoke_id": prefix, "status": "RUNNING", "cases": []}
    evidence.mkdir(parents=True, exist_ok=True)
    report_path = evidence / "smoke-report.json"
    _atomic_json(report_path, report)
    print("Smoke evidence:", evidence, flush=True)

    def submit(label, command, gpu=False, wall=10):
        job_id = prefix + "-" + label
        directory = workspace / "task" / ".nerelan-remote" / "outbox" / job_id
        directory.mkdir(parents=True)
        _atomic_json(directory / "job.json", {
            "job_id": job_id, "command": command, "files": [],
            "outputs": ["result.json"], "max_wall_seconds": wall,
            "gpu": gpu, "purpose": "Owner-run remote broker smoke: " + label})
        return job_id

    def wait(job_id, wanted):
        deadline = time.monotonic() + 300 + profile.termination_grace_seconds
        while time.monotonic() < deadline:
            broker.tick()
            current = next(r for r in broker.receipts() if r["job_id"] == job_id)
            if current["state"] in wanted:
                return current
            if current["state"] in TERMINAL | {"REJECTED", "RESULT_COLLECTED"}:
                raise RuntimeError("unexpected smoke state: " + json.dumps(current))
            time.sleep(1)
        raise TimeoutError("smoke observation deadline exceeded for " + job_id)

    def check_result(current, expected_devices):
        if current.get("outcome") != "SUCCEEDED":
            raise RuntimeError("smoke job did not succeed: " + json.dumps(current))
        result = json.loads((isolated.local_root / current["job_id"] / "outputs/result.json").read_text())
        if result != {"devices": expected_devices}:
            raise RuntimeError("unexpected device visibility: " + repr(result))

    program = "import json,os; open('result.json','w').write(json.dumps({'devices':os.environ.get('CUDA_VISIBLE_DEVICES')}))"
    normal_command = "python3 -c " + shlex.quote(program)
    try:
        for label, gpu in (("normal", False), ("gpu", True)):
            job_id = submit(label, normal_command, gpu=gpu)
            current = wait(job_id, {"RESULT_COLLECTED"})
            check_result(current, ",".join(profile.gpu_devices) if gpu else "")
            report["cases"].append({"case": label, "receipt": current})
            _atomic_json(report_path, report)

        stubborn = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(600)"
        job_id = submit("timeout", "python3 -c " + shlex.quote(stubborn), wall=2)
        current = wait(job_id, {"RESULT_COLLECTED"})
        if (current.get("outcome") != "TIMED_OUT" or not any(
                event["state"] == "TIMED_OUT_KILL_PENDING" for event in current["history"])):
            raise RuntimeError("timeout escalation was not observed: " + json.dumps(current))
        report["cases"].append({"case": "timeout-ignoring-term", "receipt": current})
        _atomic_json(report_path, report)

        job_id = submit("recovery", "sleep 5; " + normal_command)
        before = wait(job_id, {"RUNNING"})
        original = broker._remote(before, "poll")
        # Simulate receipt loss by moving, never deleting, all local job evidence.
        archive = evidence / "displaced-receipts"
        archive.mkdir()
        (isolated.local_root / job_id).rename(archive / job_id)
        current = wait(job_id, {"RESULT_COLLECTED"})
        check_result(current, "")
        recovered = broker._remote(current, "poll")
        if (original["launched_at"] != recovered["launched_at"]
                or original["request_digest"] != recovered["request_digest"]
                or not any(event["detail"] == "recovered remote launch marker" for event in current["history"])):
            raise RuntimeError("recovery did not preserve the original launch")
        report["cases"].append({"case": "receipt-loss-recovery", "receipt": current})
        report["status"] = "PASSED"
    except Exception as exc:
        report["status"] = "FAILED"
        report["error"] = str(exc)
        raise
    finally:
        _atomic_json(report_path, report)
    print("Smoke checks passed; supervisor must inspect", report_path)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["status", "tick", "smoke"])
    parser.add_argument("--profile", type=Path, help="Owner-written remote job profile")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "smoke":
        if args.profile is None:
            parser.error("smoke requires an explicit --profile")
        smoke(RemoteJobProfile.load(args.profile))
        return
    broker = RemoteJobBroker(RemoteJobProfile.load(args.profile)) if args.profile else configured_broker()
    if broker is None:
        parser.error("a valid " + ENV_PROFILE + " is required")
    if args.action == "tick":
        broker.tick()
    receipts = broker.receipts()
    if args.json:
        print(json.dumps(receipts, indent=2))
    else:
        for receipt in receipts:
            print(receipt["job_id"], receipt["state"])


if __name__ == "__main__":
    main()
