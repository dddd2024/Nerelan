# Existing change-set review tasks

`TaskExecutionService.execute_review` and loopback
`POST /api/tasks/{task_id}/review` run a read-only review of an existing exact
commit range. They reuse the existing TaskStore, Task API, executor router,
model binding/lease path, events and evidence. They add no task database,
executor kind, verifier, analyzer, index or merge authority.

Create an ordinary single-mode OpenCode task using the existing API. The review
request has required `base_sha`, `head_sha`, `paths` and optional `excluded_paths`,
`base_ref`, `head_ref`, `change_request`, `profile`. Commits are exact object IDs;
at most 64 effective paths are collected. Repository selection comes from the
task and trusted host registry. The request cannot supply a repository directory,
workspace directory, model, tools, configuration, policy or credentials.

The existing Git collector authenticates selected commit/tree/blob bytes and
binds the patch/context digests. It never changes the target checkout, refs,
index or configuration. Forge identity remains unauthenticated by a local
origin string; oversized/binary/sensitive content retains its withheld state.

The executor runs in a newly owned disposable projection repository outside
the target. A readable JSON index references every collected nonwithheld
base/head text through host-authored ordinal `.txt` files. Their UTF-8 bytes and
source line boundaries are preserved; withheld content stays explicitly withheld.
The target digest binds the original collected observations, while the index
describes their presentation. It does not replace the collector's identity.
Head instructions, plugins, skills and MCP configuration remain quoted data;
none becomes executable project configuration. The dedicated `review_only`
role denies all shell, network, task and external-directory tools and permits
only `.reverse-agent-handoff/review.md` as an edit. Its prompt does not promote
the original team task title to reviewer instructions. Standard Git
`--separate-git-dir` places disposable runtime metadata outside the model's
context directory. Runtime cache/index activity therefore does not rewrite
model inputs. The context, all data files, plan, `.git` pointer and private Git
configuration/HEAD/initial branch reference remain protected. Reviewer tools
cannot edit the private metadata through external-directory or edit permissions.
The entire newly owned container is then removed.

Integrity rejection events retain bounded known host-path labels and the count
of unexpected files. Unknown filenames and file contents are not exported in
diagnostics, because they could contain sensitive data. This is the existing
task failure path, not a new verifier or acceptance receipt.

The handoff is JSON with exactly `target_digest` and `findings`. It is limited
to 64 KiB and 64 findings. Findings use the existing normalizer's exact field
contract and must have `source: model`; deterministic provenance cannot be
asserted by the model. Unknown/private fields, duplicate JSON keys, wrong target
generation and known secret patterns in any persisted field fail closed.
Each finding cites at least one digest from the supplied context; invented
evidence references fail closed. This authenticates the cited context identity,
never the model's defect claim. Explicit rule/location duplicates use the existing
deduplicator and retain every distinct contribution.
Summary redaction alone is not used as a persistence boundary.

The existing lifecycle is QUEUED → PREPARING_WORKSPACE → RUNNING → VALIDATING
→ READY_FOR_REVIEW, or an explicit failure. Claims are atomic across the manual
single, sequential and review paths; an existing active durable run is not
stolen. Validation here checks the advisory handoff contract, not functionality.
The evidence category is `Review`, status `advisory`, bound to the exact target
and findings. Functional validation results remain unset, and all acceptance,
execution, repair and landing flags remain false. An empty report is advice,
never a verified clean bill of health or permission to merge.

Provider-free tests use real temporary Git repositories and HTTP services with
an injected role. They do not establish native model confinement, defect
detection, false-positive rate, billing or independent reviewer qualification.
Live execution requires the separately authorized existing model/credential
path and independent acceptance. This feature does not activate an autonomy
window or register an unattended review workflow.

The original native trial of #1074 failed with `review_projection_mutated`;
the target and setup stayed unchanged. Its temporary projection was removed
before changed-path diagnostics were retained, so its exact mutation cause
remains unresolved. The separate metadata layout and text presentation are a
new candidate requiring fresh native evaluation; provider-free fixtures alone
do not establish that the real-model lifecycle now succeeds.

Remaining Issue #811 work includes mature analyzer composition, contextual
impact retrieval, prior forge feedback linking, real model/evaluation evidence,
incremental reconciliation, advisory forge projection and governed remediation.
