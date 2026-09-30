"""Exact source integrity; Git objects are real or explicitly synthetic HTTP data."""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import subprocess
from pathlib import Path

import pytest

from reverse_agent.github_remote_verifier import GitHubEvidenceError, GitHubRemoteAcceptanceVerifier

REPO = 'dddd2024/Nerelan'
REF = 'a' * 40
PATH = 'policy/validator.py'
RAW = b'protected source\n'


def oid(kind: str, raw: bytes) -> str:
    return hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def tree(entries: list[dict]) -> dict:
    raw = b''
    for e in sorted(entries, key=lambda x: x['path'].encode() + (b'/' if x['type'] == 'tree' else b'')):
        raw += e['mode'].lstrip('0').encode() + b' ' + e['path'].encode() + b'\0' + bytes.fromhex(e['sha'])
    return {'sha': oid('tree', raw), 'truncated': False, 'tree': entries}


def fixture(raw: bytes = RAW, mode: str = '100644') -> tuple[dict, dict, dict, dict]:
    blob = {'sha': oid('blob', raw), 'size': len(raw), 'encoding': 'base64', 'content': base64.b64encode(raw).decode()}
    leaf = tree([{'path': 'validator.py', 'mode': mode, 'type': 'commit' if mode == '160000' else 'blob', 'sha': blob['sha'], 'size': len(raw)}])
    root = tree([{'path': 'policy', 'mode': '040000', 'type': 'tree', 'sha': leaf['sha']}])
    commit = {'sha': REF, 'tree': {'sha': root['sha']}}
    return commit, root, leaf, blob


def verifier(objects: tuple | None = None) -> tuple[GitHubRemoteAcceptanceVerifier, list[str]]:
    c, r, t, b = objects or fixture()
    responses = {
        f'/repos/{REPO}/git/commits/{REF}': c,
        f'/repos/{REPO}/git/trees/{c["tree"]["sha"]}': r,
        f'/repos/{REPO}/git/trees/{r["tree"][0]["sha"]}': t,
        f'/repos/{REPO}/git/blobs/{t["tree"][0]["sha"]}': b,
    }
    calls: list[str] = []
    v = GitHubRemoteAcceptanceVerifier(repository=REPO, token='test-only-not-a-credential')
    def read(path: str) -> dict:
        calls.append(path)
        assert path in responses, path
        return copy.deepcopy(responses[path])
    v._request_json = read
    return v, calls


def check(v: GitHubRemoteAcceptanceVerifier, *, ref: str = REF, path: str = PATH) -> dict:
    return v.load_ref_file_bytes(ref=ref, path=path)


@pytest.mark.parametrize('raw', [RAW, b'', b'\x00\xff\xfe', '文本é'.encode(), b'x' * (1024 * 1024)])
@pytest.mark.parametrize('mode', ['100644', '100755'])
def test_regular_files_identity_and_digest(raw: bytes, mode: str) -> None:
    v, calls = verifier(fixture(raw, mode))
    out = check(v)
    assert out['verified'] is True, out
    assert out['bytes'] == raw
    assert out['source_identity']['blob_sha'] == oid('blob', raw)
    assert out['source_identity']['mode'] == mode
    assert out['source_identity']['commit_sha'] == REF
    assert out['source_identity']['path'] == PATH
    assert len(calls) == 4
    hashed = v.verify_ref_file_sha256(ref=REF, path=PATH, expected_sha256=hashlib.sha256(raw).hexdigest())
    assert hashed['verified'] is True
    assert 'bytes' not in hashed
    bad = v.verify_ref_file_sha256(ref=REF, path=PATH, expected_sha256='0' * 64)
    assert bad['verified'] is False


@pytest.mark.parametrize('ref', ['main', 'HEAD', 'v1', 'A'*40, 'a'*39, 'a'*41, None, True, REF+'?x=1', REF+'\n'])
def test_mutable_or_invalid_ref_rejected_before_io(ref: object) -> None:
    v, calls = verifier()
    assert check(v, ref=ref)['verified'] is False
    assert calls == []


@pytest.mark.parametrize('path', ['', '/a', '../a', 'a/../b', 'a//b', './a', 'a/', 'C:/a', 'a\\b', 'a\x00b', 'a\nb', '.git/config', 'a/./b', '/'.join(['a'] * 33), 'x'*256, None, 3, '\ud800'])
def test_invalid_paths_reject_without_io(path: object) -> None:
    v, calls = verifier()
    assert check(v, path=path)['verified'] is False
    assert calls == []


@pytest.mark.parametrize('digest', [None, True, '', 'a'*63, 'A'*64, 'z'*64])
def test_invalid_expected_digest_reject_without_io(digest: object) -> None:
    v, calls = verifier()
    out = v.verify_ref_file_sha256(ref=REF, path=PATH, expected_sha256=digest)
    assert out == {'verified': False, 'reason': 'invalid_expected_sha256'}
    assert not calls


@pytest.mark.parametrize('mode', ['120000', '160000', '040000'])
def test_selected_nonregular_file_rejects(mode: str) -> None:
    c, r, t, b = fixture(mode=mode)
    if mode == '040000':
        t['tree'][0]['type'] = 'tree'
        t = tree(t['tree'])
        r = tree([{**r['tree'][0], 'sha': t['sha']}])
        c['tree']['sha'] = r['sha']
    v, _ = verifier((c, r, t, b))
    assert check(v)['verified'] is False


@pytest.mark.parametrize('mode,kind', [('120000','blob'), ('160000','commit'), ('100644','blob')])
def test_selected_parent_must_be_directory(mode: str, kind: str) -> None:
    c,r,t,b = fixture()
    r = tree([{**r['tree'][0], 'mode':mode, 'type':kind}])
    c['tree']['sha'] = r['sha']
    v,_ = verifier((c,r,t,b))
    assert check(v)['reason'] == 'source_component_not_tree'


@pytest.mark.parametrize('mutation,reason', [
    ('tree_sha','tree_identity_mismatch'), ('truncated','source_tree_incomplete'),
    ('missing_truncated','source_tree_incomplete'), ('entries_type','invalid_source_tree_entries'),
    ('duplicates','duplicate_source_tree_entry'), ('tree_digest','source_tree_digest_mismatch'),
    ('bad_mode','invalid_source_tree_entry'), ('mode_type','invalid_source_tree_entry'),
    ('bad_oid','invalid_source_tree_entry'), ('bad_path','invalid_source_tree_entry'),
    ('too_many','invalid_source_tree_entries'),
    ('bad_blob_sha','blob_identity_mismatch'), ('blob_shape','blob_identity_mismatch'),
    ('encoding','unexpected_content_encoding'), ('content_type','invalid_content_type'),
    ('bad_base64','invalid_base64_content'), ('blob_size','source_size_mismatch'),
    ('blob_boolsize','source_size_mismatch'), ('wrong_content','source_blob_digest_mismatch'),
    ('big_encoding','source_encoding_too_large'),
])
def test_malformed_and_mismatched_objects_reject(mutation: str, reason: str) -> None:
    c,r,t,b=fixture()
    if mutation == 'tree_sha': t['sha']='c'*40
    elif mutation == 'truncated': t['truncated']=True
    elif mutation == 'missing_truncated': del t['truncated']
    elif mutation == 'entries_type': t['tree']={}
    elif mutation == 'duplicates': t['tree']*=2
    elif mutation == 'tree_digest': t['tree'][0]['path']='other.py'
    elif mutation == 'bad_mode': t['tree'][0]['mode']='100600'
    elif mutation == 'mode_type': t['tree'][0]['type']='tree'
    elif mutation == 'bad_oid': t['tree'][0]['sha']='bad'
    elif mutation == 'bad_path': t['tree'][0]['path']='a/b'
    elif mutation == 'too_many': t['tree']*=10001
    elif mutation == 'bad_blob_sha': b['sha']='c'*40
    elif mutation == 'blob_shape': b=[]
    elif mutation == 'encoding': b['encoding']='utf-8'
    elif mutation == 'content_type': b['content']=42
    elif mutation == 'bad_base64': b['content']='YWJj*'
    elif mutation == 'blob_size': b['size']+=1
    elif mutation == 'blob_boolsize': b['size']=True
    elif mutation == 'wrong_content': b['content']=base64.b64encode(b'x'*len(RAW)).decode()
    elif mutation == 'big_encoding': b['content']=' '* (2*1024*1024+1)
    # Build the route map before malformed observation data is returned.
    v,_ = verifier()
    responses = iter([c,r,t,b])
    v._request_json=lambda _: next(responses)
    result=check(v)
    assert result == {'verified':False,'reason':reason}


@pytest.mark.parametrize('size', [-1, True, 1.0, '1', None, 1024*1024+1])
def test_leaf_size_bounded_before_blob_request(size: object) -> None:
    objects=fixture()
    objects[2]['tree'][0]['size']=size  # Size is metadata, not part of tree hash.
    v,calls=verifier(objects)
    assert check(v)['reason']=='invalid_source_size'
    assert len(calls)==3


@pytest.mark.parametrize('payload', [None, [], {}, {'sha':'b'*40}, {'sha':REF,'tree':None}, {'sha':REF,'tree':{'sha':4}}])
def test_bad_commit_is_not_accepted(payload: object) -> None:
    v,_=verifier()
    v._request_json=lambda _:payload
    assert check(v)['verified'] is False


@pytest.mark.parametrize('stage', [0,1,2,3])
def test_transport_failure_no_fallback(stage: int) -> None:
    v,calls=verifier()
    original=v._request_json
    def read(path):
        if len(calls)==stage:
            raise GitHubEvidenceError('github_api_failure:TimeoutError')
        return original(path)
    v._request_json=read
    assert check(v)=={'verified':False,'reason':'github_api_failure:TimeoutError'}


@pytest.mark.parametrize('separator', [' ', '\t', '\r\n', '\n'])
def test_base64_ascii_whitespace(separator: str) -> None:
    objects=fixture()
    objects[3]['content']=separator.join(objects[3]['content'][i:i+4] for i in range(0,len(objects[3]['content']),4))
    v,_=verifier(objects)
    assert check(v)['verified'] is True


@pytest.mark.parametrize('value', ['YWJj*','YWJj=','YWJj===','YWJ','YW\vJj','YW\fJj','YW\u00a0Jj'])
def test_strict_base64_rejects_noncanonical_values(value: str) -> None:
    objects=fixture()
    objects[3]['content']=value
    v,_=verifier(objects)
    assert check(v)=={'verified':False,'reason':'invalid_base64_content'}


def test_original_transport_request_json_composition(monkeypatch: pytest.MonkeyPatch) -> None:
    v,_=verifier()
    read=v._request_json
    del v._request_json
    seen=[]
    class Response(io.BytesIO):
        status=200
    def urlopen(request, timeout):
        assert request.get_method()=='GET'
        assert timeout==30
        assert request.full_url.startswith('https://api.github.com/repos/'+REPO+'/git/')
        seen.append(request.full_url)
        return Response(json.dumps(read(request.full_url.removeprefix('https://api.github.com'))).encode())
    monkeypatch.setattr('urllib.request.urlopen',urlopen)
    assert check(v)['verified'] is True
    assert len(seen)==4


def test_real_git_objects_unicode_sort_and_nonregular_modes(tmp_path: Path) -> None:
    def git(*args: str, data: bytes | None = None) -> bytes:
        return subprocess.run(['git',*args],cwd=tmp_path,input=data,capture_output=True,check=True,timeout=10).stdout
    git('init','--object-format=sha1')
    git('config','user.email','test@example.invalid')
    git('config','user.name','Test')
    (tmp_path/'a.dir').mkdir()
    (tmp_path/'a.dir'/'验证.py').write_bytes(RAW)
    (tmp_path/'a.dir.c').write_bytes(b'file sibling changes sort')
    git('add','a.dir','a.dir.c')
    # Add modes to the INDEX; no platform symlink privilege or unknown code.
    target=git('hash-object','-w','--stdin',data='a.dir/验证.py'.encode()).decode().strip()
    git('update-index','--add','--cacheinfo',f'120000,{target},link')
    git('commit','-m','fixture')
    first=git('rev-parse','HEAD').decode().strip()
    git('update-index','--add','--cacheinfo',f'160000,{first},submodule')
    git('commit','-m','gitlink fixture')
    head=git('rev-parse','HEAD').decode().strip()
    v=GitHubRemoteAcceptanceVerifier(repository=REPO,token='fixture')
    calls=[]
    def request(path: str) -> dict:
        calls.append(path)
        group,sha=path.rsplit('/',2)[-2:]
        if group=='commits':
            raw=git('cat-file','commit',sha)
            root=raw.splitlines()[0].split()[1].decode()
            return {'sha':sha,'tree':{'sha':root}}
        if group=='trees':
            entries=[]
            for row in git('ls-tree','-z',sha).split(b'\0'):
                if not row:continue
                meta,name=row.split(b'\t',1)
                mode,kind,child=meta.decode().split()
                entry={'path':name.decode(),'mode':mode,'type':kind,'sha':child}
                if kind=='blob':entry['size']=int(git('cat-file','-s',child))
                entries.append(entry)
            return {'sha':sha,'truncated':False,'tree':entries}
        assert group=='blobs'
        raw=git('cat-file','blob',sha)
        return {'sha':sha,'size':len(raw),'encoding':'base64','content':base64.b64encode(raw).decode()}
    v._request_json=request
    result=check(v,ref=head,path='a.dir/验证.py')
    assert result['verified'] is True, result
    assert result['bytes']==RAW
    for path in ('link','link/x','submodule','submodule/x'):
        assert check(v,ref=head,path=path)['verified'] is False
    assert not any('/contents/' in path for path in calls)
    assert check(v,ref=head,path='absent')['reason']=='source_path_missing'
