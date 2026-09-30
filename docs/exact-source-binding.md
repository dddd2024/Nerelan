# Exact remote source binding

Work item #1043; priority #1010 A2b-2a; parents #379 and #653.

## Implemented boundary

The existing `GitHubRemoteAcceptanceVerifier.load_ref_file_bytes` and
`verify_ref_file_sha256` now share one pinned Git-object reader. Existing
mainline callers use it without adopting a second authority store or verifier.

A successful read establishes a regular file at a particular path in an exact
commit, under the existing authenticated GitHub API trust assumption. It does
not authorize the commit, execute its contents, certify functional acceptance,
or prove a workflow used those bytes.

## Algorithm

1. Validate a full lowercase SHA-1 commit identity, safe repository and exact
   path before sending any request. Mutable branches, tags, short references,
   revision expressions and malformed paths are rejected.
2. Read the Git commit object. The returned commit identity must match; its
   observed root tree is the only traversal starting point.
3. Read nonrecursive Git trees. Require complete, well-shaped unique entries
   and recompute each tree's Git object hash using canonical mode/name/object
   encoding and Git directory sorting. Never infer identity from a filename.
4. Traverse only actual tree entries. The final object must be a regular blob
   with mode `100644` or `100755`. Selected symbolic links and submodules are
   rejected rather than dereferenced. Unselected valid link/gitlink entries
   can coexist in the containing tree.
5. Read the selected blob, strictly decode base64, verify actual size against
   tree metadata, and recompute its Git blob hash. The digest-verification
   method additionally compares SHA-256 with the independently supplied value.
6. Return the existing `verified`/`bytes` or `verified`/`sha256` result with
   observed `source_identity` (commit, root/tree chain, path, blob, mode, size).
   Failure returns no file bytes and never falls back to Contents or main.

Only validated repository and object IDs are interpolated into API URLs. Path
components are matched as data in returned trees, not interpreted as URL syntax.

## Limits and assumptions

The reader supports at most 32 path components, 255 UTF-8 bytes per component,
4096 path characters, 10000 entries per nonrecursive tree, 1 MiB decoded file
content and 2 MiB encoded content text. It rejects `.`, `..`, `.git`, separators,
colon, control characters and unrepresentable UTF-8 names. This is a deliberate
bounded source-reader subset, not a complete arbitrary-Git-filename interface.

These are traversal/processing bounds **after** the existing transport decodes
JSON. This change does not add a streaming HTTP response-body limit, request-wide
deadline, redirect policy, commit-signature verification or a new credential
source. The SHA-1 Git object model and the authenticated API's exact
commit-to-root-tree association remain trusted; no stronger cryptographic or
cross-object atomicity claim is made.

The caller must obtain the pinned commit and expected digest through an
independently authorized policy. Passing candidate-selected values proves
self-consistency, not approved provenance. A later protected executor must bind
workflow invocation and dependency closure to trusted versions and isolate
execution, review and promotion identities. App identity alone is insufficient.
No Ruleset, workflow, source-selection policy or automatic-merge switch changes
in this slice. #1042's check-producer patch affects other methods in the same
module and must be preserved during separately reviewed integration.

## Tests

`tests/platform_v1/test_exact_source_binding.py` covers pinned positive cases,
empty/binary/Unicode and executable files, immutable-reference input checks,
wrong object and tree hashes, truncation, duplicate entries, unsupported modes,
symlink/submodule traversal, invalid sizes/base64 and failures at each API stage.
A disposable real Git repository supplies real commit/tree/blob objects,
including Unicode names, Git directory sorting, symlink and gitlink index modes.
HTTP responses are explicitly simulated; these tests do not perform online
GitHub authentication or run candidate programs.

The existing `_verify_contents_payload` helper in `tests/test_mainline_landing.py`
is adapted only to the commit/tree/blob HTTP protocol. All original test
functions and assertions remain. Its Git hashes are constructed independently
from the production helpers, preserving the original strict base64 and digest
positive/negative cases.

Required validation:

```text
python -m pytest tests/platform_v1/test_exact_source_binding.py -q
python -m pytest tests/test_mainline_landing.py -q
python -m pytest tests/platform_v1 -q
git diff --check
```

Partial-source local checks do not replace full-checkout exact-head CI or
independent acceptance. Source-stage publication remains Draft/unmerged.
