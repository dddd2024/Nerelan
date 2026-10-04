# Read-only Git review snapshots

`collect_review_git_snapshot` observes an explicitly selected commit range in an
existing local GitHub repository. It builds the existing `ReviewTarget` from
actual commit/tree objects and a binary full-index patch of effective selected
paths. It reads bounded blob objects and checks their object hashes before
exposing their text. SHA1 and SHA256 repositories are supported. Ref names are
metadata; they never resolve or select executable Git arguments.

The selected repository and installed system Git belong to the trusted caller.
Matching origin syntax does not authenticate remote ownership. The collector
does not fetch, check out a branch, update the index, run hooks/filters/textconv,
use replacement objects, lazy-fetch or execute repository configuration. Working
tree dirt and moving branch refs do not change a snapshot of explicit commits.
An automatically removed bare metadata view contains only host-authored Git
configuration and points read-only at the selected repository's object store.
No source blob or raw repository configuration is copied into that view. This
also prevents local attributes/diff drivers from changing patch identity.

Only literal, explicitly selected files are read. Excluded files are absent from
the patch and context. Sensitive-named selected files are refused before reads.
Symlinks are stored link-text data, never followed. Deleted files are explicitly
absent. Binary, oversized or secret-pattern-matching text is withheld; oversized
blob contents are not verified or represented as having been read. File limits,
stream-time byte limits, a command ceiling and a whole-run deadline fail closed.

All repository text from both base and head, including AGENTS, skills and proposed
configuration, is marked **untrusted data**. The snapshot grants no policy or
tools and performs no trusted instruction resolution. A future reviewer runtime
must separately enforce its trusted policy and prevent automatic candidate
configuration loading; this collector alone does not implement that isolation.

The normalized target keeps its claims-only flags false. Local Git observation
does not verify a defect, scanner provenance, independent acceptance, functional
correctness or permission to execute, repair or land. No TaskStore, API, model
call, scanner, forge write or second verifier is introduced. Runtime orchestration,
trusted policy resolution, analyzer composition, incremental impact review and
governed repair remain separate unfinished #811 requirements.
