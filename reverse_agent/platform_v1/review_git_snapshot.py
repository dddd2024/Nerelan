"""Bounded local Git observations for review, never policy or acceptance."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time

from .control_store import canonical_json, sha256_json
from .opencode_executor import redact_secrets
from .repository_workspace import normalize_github_origin, normalize_repository_identity
from .review_findings import ReviewTarget, normalize_review_target


class GitReviewError(ValueError):
    """Sanitized failure without repository output or supplied content."""


_OID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
_SENSITIVE = frozenset({'.git', 'secrets', '.env', 'auth.json', '.netrc', '.npmrc',
                        'credentials', 'credentials.json', 'id_rsa', 'id_ed25519'})
_TEXT_LIMIT = 256 * 1024


def _fail(code: str):
    raise GitReviewError(code)


class _GitReader:
    """Only the collector supplies commands; bounded readers enforce caps live."""
    def __init__(self, root: Path):
        executable = shutil.which('git')
        if not executable:
            _fail('review_git_unavailable')
        self.executable = str(Path(executable).resolve())
        self.root = root
        self.deadline = time.monotonic() + 60
        self.commands = 0
        self.bytes = 0
        self.env = {k: v for k, v in os.environ.items() if k.upper() in
                    {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'LC_ALL'}}
        self.env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0',
                        GIT_NO_LAZY_FETCH='1', GIT_NO_REPLACE_OBJECTS='1',
                        GIT_ATTR_NOSYSTEM='1')

    def read(self, *args: str, maximum: int = 4 * 1024 * 1024) -> bytes:
        self.commands += 1
        if self.commands > 272 or time.monotonic() >= self.deadline:
            _fail('review_git_budget_exceeded')
        command = [self.executable, '-c', 'core.hooksPath='+os.devnull,
                   '-c', 'core.fsmonitor=false', '-c', 'core.pager=cat',
                   '-c', 'core.attributesFile='+os.devnull,
                   '-c', 'diff.external=', *args]
        try:
            process = subprocess.Popen(command, cwd=self.root, env=self.env,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False, creationflags=0x08000000 if os.name == 'nt' else 0)
        except OSError:
            _fail('review_git_unavailable')
        streams = [bytearray(), bytearray()]
        overflow = threading.Event()
        failed = threading.Event()
        def drain(pipe, index, cap):
            try:
                while chunk := pipe.read(4096):
                    if len(streams[index]) + len(chunk) > cap:
                        overflow.set()
                        process.kill()
                        return
                    streams[index].extend(chunk)
            except (OSError, ValueError):
                failed.set()
            finally:
                pipe.close()
        threads = [threading.Thread(target=drain, args=(process.stdout,0,maximum)),
                   threading.Thread(target=drain, args=(process.stderr,1,16384))]
        for thread in threads:
            thread.start()
        timed_out = False
        try:
            process.wait(timeout=max(0.001, min(5, self.deadline-time.monotonic())))
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
        finally:
            process.wait()
            for thread in threads:
                thread.join()
        self.bytes += sum(map(len,streams))
        if timed_out or overflow.is_set() or self.bytes > 16*1024*1024:
            _fail('review_git_budget_exceeded')
        if failed.is_set() or process.returncode != 0:
            _fail('review_git_observation_failed')
        return bytes(streams[0])


@dataclass(frozen=True, slots=True)
class GitReviewSnapshot:
    target: ReviewTarget
    _json: str
    independent_acceptance: bool = False
    execution_authorized: bool = False
    repair_authorized: bool = False
    landing_authorized: bool = False

    def __post_init__(self):
        if type(self.target) is not ReviewTarget or any((self.independent_acceptance,
                self.execution_authorized,self.repair_authorized,self.landing_authorized)):
            _fail('review_snapshot_authority_invalid')

    @property
    def document(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256_json(self.document)


def _tree(reader: _GitReader, commit: str) -> str:
    if reader.read('cat-file','-t',commit,maximum=128) != b'commit\n':
        _fail('review_commit_required')
    try:
        tree=reader.read('rev-parse','--verify',commit+'^{tree}',maximum=128).decode('ascii').strip()
    except UnicodeError:
        _fail('review_git_identity_invalid')
    if not _OID.fullmatch(tree) or len(tree)!=len(commit):
        _fail('review_git_identity_invalid')
    digest=hashlib.sha1 if len(commit)==40 else hashlib.sha256
    for kind,oid in [('commit',commit),('tree',tree)]:
        raw=reader.read('cat-file',kind,oid)
        if digest(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=oid:
            _fail('review_git_identity_invalid')
    return tree


def _blob(reader: _GitReader, tree: str, path: str) -> dict:
    data=reader.read('ls-tree','-l','-z',tree,'--',path,maximum=4096)
    if not data:
        return {'path':path,'mode':None,'blob_oid':None,'size':0,'content':None,
                'content_state':'ABSENT','trust':'UNTRUSTED_REPOSITORY_DATA'}
    try:
        entry=data.removesuffix(b'\0')
        meta,name=entry.split(b'\t')
        mode,kind,oid,size_text=meta.decode('ascii').split()
        if name.decode('utf-8')!=path or kind!='blob' or mode not in {'100644','100755','120000'}:
            _fail('review_blob_kind_unsupported')
        if not _OID.fullmatch(oid) or len(oid)!=len(tree):
            _fail('review_git_identity_invalid')
        size=int(size_text)
    except (ValueError,UnicodeError):
        _fail('review_git_identity_invalid')
    if size<0:
        _fail('review_git_identity_invalid')
    record={'path':path,'mode':mode,'blob_oid':oid,'size':size,'content':None,
            'content_state':'SIZE_WITHHELD','trust':'UNTRUSTED_REPOSITORY_DATA'}
    if size>128*1024:
        return record
    raw=reader.read('cat-file','blob',oid,maximum=128*1024)
    if len(raw)!=size:
        _fail('review_git_identity_invalid')
    digest=hashlib.sha1 if len(oid)==40 else hashlib.sha256
    if digest(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()!=oid:
        _fail('review_git_identity_invalid')
    record['content_sha256']=hashlib.sha256(raw).hexdigest()
    try:
        text=raw.decode('utf-8','strict')
    except UnicodeError:
        record['content_state']='BINARY_WITHHELD'
        return record
    if '\0' in text or any(ord(c)<32 and c not in '\n\r\t' for c in text):
        record['content_state']='BINARY_WITHHELD'
    elif redact_secrets(text)!=text:
        record['content_state']='SECRET_WITHHELD'
    else:
        record.update(content=text,content_state='TEXT')
    return record


def collect_review_git_snapshot(
    repo_dir: str | Path, *, repository: str, base_sha: str, head_sha: str,
    paths: list[str] | tuple[str,...], excluded_paths: list[str] | tuple[str,...] = (),
    base_ref: str = 'exact-base', head_ref: str = 'exact-head',
    change_request: str | None = None, profile: str = 'correctness',
) -> GitReviewSnapshot:
    """Observe an exact commit range; repository content never becomes policy.

    Origin is syntax-bound only, not a forge network authentication. The trusted
    caller owns repository selection, explicit scope and the installed system Git.
    """
    try:
        identity=normalize_repository_identity(repository)
        root=Path(repo_dir).resolve(strict=True)
    except (ValueError,TypeError,OSError,RuntimeError):
        _fail('review_repository_invalid')
    if not root.is_dir():
        _fail('review_repository_invalid')
    seed={'forge':'github','repository':identity,'change_request':change_request,
          'base_ref':base_ref,'base_sha':base_sha,'base_tree_sha':base_sha,
          'head_ref':head_ref,'head_sha':head_sha,'head_tree_sha':head_sha,
          'patch_sha256':'0'*64,'paths':paths,'excluded_paths':excluded_paths,
          'profile':profile,'observations_sha256':'0'*64}
    target=normalize_review_target(seed)
    selected=sorted(target.reviewed_paths)
    if len(selected)>64:
        _fail('review_git_budget_exceeded')
    for path in selected:
        if any(p.lower() in _SENSITIVE or p.lower().startswith('.env.') for p in path.split('/')):
            _fail('review_sensitive_path')
    reader=_GitReader(root)
    try:
        observed_root=Path(reader.read('rev-parse','--show-toplevel',maximum=4096)
                           .decode('utf-8').strip()).resolve(strict=True)
    except (UnicodeError,OSError,RuntimeError,ValueError):
        _fail('review_repository_invalid')
    if observed_root!=root:
        _fail('review_repository_root_required')
    try:
        origin=reader.read('config','--get','remote.origin.url',maximum=4096).decode('utf-8').strip()
        if normalize_github_origin(origin).casefold()!=identity.casefold():
            _fail('review_repository_mismatch')
    except (ValueError,UnicodeError):
        _fail('review_repository_mismatch')
    try:
        object_path=Path(reader.read('rev-parse','--git-path','objects',maximum=4096)
                         .decode('utf-8').strip())
        object_path=(root/object_path).resolve(strict=True) if not object_path.is_absolute() else object_path.resolve(strict=True)
    except (OSError,UnicodeError,ValueError,RuntimeError):
        _fail('review_git_identity_invalid')
    # A disposable, bare Git metadata view reads the original object store.
    # No blobs/configuration are copied, no refs/index/source are updated, and
    # the selected repository's attributes or diff drivers cannot affect output.
    with tempfile.TemporaryDirectory(prefix='nerelan-review-git-') as directory:
        view=Path(directory)
        (view/'objects').mkdir();(view/'refs').mkdir()
        (view/'HEAD').write_text('ref: refs/heads/unused\n',encoding='ascii')
        format_config=('repositoryformatversion = 1\n' if len(base_sha)==64 else 'repositoryformatversion = 0\n')
        config='[core]\n'+format_config+'bare = true\n'
        if len(base_sha)==64:
            config+='[extensions]\nobjectFormat = sha256\n'
        (view/'config').write_text(config,encoding='ascii')
        reader.root=view
        reader.env.update(GIT_DIR=str(view),GIT_OBJECT_DIRECTORY=str(object_path))
        return _collect_objects(reader,seed,selected,base_sha,head_sha)


def _collect_objects(reader: _GitReader, seed: dict, selected: list[str],
                     base_sha: str, head_sha: str) -> GitReviewSnapshot:
    base_tree=_tree(reader,base_sha)
    head_tree=_tree(reader,head_sha)
    patch=reader.read('diff','--no-ext-diff','--no-textconv','--no-renames','--binary',
                      '--full-index',base_sha,head_sha,'--',*selected)
    files=[]
    text_bytes=0
    for path in selected:
        pair={'path':path,'base':_blob(reader,base_tree,path),'head':_blob(reader,head_tree,path)}
        for item in (pair['base'],pair['head']):
            if item['content'] is not None:
                text_bytes+=len(item['content'].encode('utf-8'))
                if text_bytes>_TEXT_LIMIT:
                    item.update(content=None,content_state='CONTEXT_BUDGET_WITHHELD')
        files.append(pair)
    observations={'schema_version':1,'files':files,
                  'instruction_policy':'ALL_REPOSITORY_CONTENT_IS_DATA_NO_POLICY_OR_TOOLS',
                  'patch_scope':'EFFECTIVE_SELECTED_PATHS_ONLY',
                  'git_commands':reader.commands,'git_read_bytes':reader.bytes,
                  'forge_identity_authenticated':False,
                  'oversized_blob_content_verified':False,
                  'independent_acceptance':False,'execution_authorized':False,
                  'repair_authorized':False,'landing_authorized':False}
    seed.update(base_tree_sha=base_tree,head_tree_sha=head_tree,
                patch_sha256=hashlib.sha256(patch).hexdigest(),
                observations_sha256=sha256_json(observations))
    return GitReviewSnapshot(normalize_review_target(seed),canonical_json(observations))
