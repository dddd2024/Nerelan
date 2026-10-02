# Approved functional checks

## Fixed combinations and exact-candidate checks

Two additional host-owned profiles run from repository root only. They accept
no caller-supplied targets, argv, environment, timeout, or alternate directory:

| Profile | Fixed pytest targets |
| --- | --- |
| `python_pytest_report_consistency` | `tests/platform_v1/test_functional_report_consistency.py` |
| `python_pytest_functional_artifact` | `tests/platform_v1/test_functional_execution.py` and `tests/platform_v1/test_artifact_handoff.py` |

Both use the existing trusted Python runtime, pytest quiet mode, disabled cache
provider, a 600-second deadline, and a host-created JUnit report. Each check has
new owned temporary storage. Adding these profiles changes the catalog digest;
previously frozen contracts fail stale-catalog admission. The contract format
version remains 1. Valid mixed pass/skip results retain their existing meaning.

For provider-free commit validation, create a Goal with
`executor_kind: candidate_validation`, `orchestration_mode: single`, and no
Binding. Every planned task must select `capability: validate_task`, at least
one of the fixed combinations above, and `expected_candidate_sha` containing
the full approved 40-character lowercase Git commit SHA. The exact SHA is shown
in the generated plan and included in its revision/digest before owner approval.
Candidate tasks cannot request artifact inputs, dependencies, or producer exports.

The existing Goal approval and ACTIVE window are required. The window must
include the repository and both `execute_task` and `validate_task`. Execution
rechecks the current Goal revision/digest, selected checks, Task link, window
status/time and repository identity; it freezes these into the existing
FunctionalContract evidence. A direct unapproved Task cannot invent this authority.
The native router prepares a new isolated checkout of the exact SHA without
model/provider calls, credentials or network fetches. The commit must already be
available in the configured trusted source repository.

Host validation requires the exact expected HEAD and committed tree before
running checks, then unchanged HEAD/tree afterward. Another stable descendant
of the approved base fails. Missing, contradictory, failed, zero-test or
all-skipped reports cannot pass. Results retain the truthful
`candidate_validation` executor identity in the existing Task/Run/SQLite views;
durable execution uses the existing fenced lease/evidence/checkpoint writes.
No producer AcceptedArtifact is generated and this route grants no publication,
Ready, merge, deployment, or independent acceptance.

“Read-only” describes intended validation behavior. Repository tests execute
code; this route is not an OS sandbox or proof of authentic test provenance or
complete task-obligation coverage. Its scoped result is author/runtime evidence
until a different auditor reviews the final exact head and required CI.

Goal tasks can select host-owned checks before owner review:

```json
{
  "id": "T001",
  "title": "Implement the requested behavior",
  "instruction": "Implement and verify the acceptance criteria",
  "validation_checks": [
    {"profile_id": "python_pytest", "working_directory": "."},
    {"profile_id": "npm_test", "working_directory": "frontend"}
  ]
}
```

The persisted plan lists these checks. Editing a planned task changes the Goal's
artifact digest and revision. An approved plan is immutable; amend and review the
Goal again before changing its checks. Launch atomically freezes the checks,
catalog digest/version, Goal/revision/artifact identity, repository and admitted
source HEAD with Task creation in the existing SQLite evidence table. A repeated
launch returns the same Tasks and contracts. No additional execution store or
database migration is used.

The catalog has four profiles. Its two general profiles are:

| Profile | Installed runtime | Accepted test evidence |
| --- | --- | --- |
| `python_pytest` | Host Python running `-m pytest -q -p no:cacheprovider` | Host-selected temporary JUnit report |
| `npm_test` | Installed Node and npm CLI, running `npm test` | `node --test` with TAP, or `vitest run` with a temporary JUnit report |

The server adds fixed reporting arguments. Other npm test scripts, lifecycle
`pretest`/`posttest` hooks and project `.npmrc` files are explicitly unsupported.
There is no installation fallback. npm runs offline with isolated empty user and
global configuration, an isolated cache, disabled audits/funding/update notices,
and closed stdin. Provider credentials and parent Python/Node injection flags
are not copied into the child environment. This is process and command policy,
not an operating-system sandbox for repository test code.

Up to eight distinct profile/directory pairs may be selected. Directories must
resolve inside the actual prepared repository; traversal, absolute paths and
escaping directory links fail. The caller cannot supply argv, executable paths,
shell commands, environment overrides or timeout overrides. Each check has a
600-second deadline. The runner drains and hashes output while retaining at most
4096 bytes for report parsing; raw output is not stored as functional evidence.
JUnit files are temporary and limited to 8 MiB. Windows jobs contain the child
before it resumes and terminate descendants on close. Other hosts use an owned
process group. A timed-out check or dangling output stream fails.

Verification requires an actual implementation delta for an implementation task,
all selected checks to succeed, at least one executed passing test per check, no
failed tests, supplementary Git whitespace hygiene, and unchanged exact Git HEAD
and private-index tree identities across the checks. Zero collected tests,
entirely skipped suites, syntax errors, failed assertions, changed base/contract
or modification during validation cannot produce verified evidence. The existing
private-index snapshot preserves the real Git index. Test coverage and the quality
of assertions remain part of owner review; passing a selected suite does not prove
every product requirement.

Ordinary and durable single/sequential execution use the same oracle after the
executor finishes. Sequential handoff files are removed before taking the tested
artifact snapshot. Durable evidence uses the existing lease-fenced TaskStore
writes. Accepted executor roles are not replayed after restart. Recovery from an
accepted validation checkpoint rechecks the persisted result binding and current
artifact; it cannot turn a failed or stale result into success.

`approved_functional_checks` identifies this validation surface. Task frontend
projections expose `functionalValidation`, and Run validation exposes
`functional`. These projections require the frozen contract, matching result
digest, current execution identity and successful per-check evidence. An exit
code of zero by itself is insufficient. A deterministic fixture may have
`FIXTURE_VERIFIED` evidence but never `verified: true`. Legacy Tasks without a
selected contract continue to expose hygiene results without functional proof.
GitHub workflow-name `required_checks` remains a separate publication contract.

Goal list, detail and history-page responses include the same safe proof in each
`task_links[].functional_validation`, alongside the Task's `executor_kind` and
the existing `publication` projection. The host reads the current Goal revision,
links, Task proof and publication records in one SQLite transaction. It also
checks the functional contract's Goal, revision, plan-task and artifact digest
against that response. Missing or mismatched evidence remains unverified, and
unchanged reads preserve business timestamps. Event history is not loaded for
this projection.

Goal responses explicitly report `completion_scope: "EXECUTION_ONLY"` and
`remote_acceptance: "NOT_OBSERVED"`. The existing `COMPLETED` lifecycle means all
Tasks reached review-ready, including fixture Tasks. It does not establish
functional verification, review acceptance, merge or delivery. Publication
`COMPLETE` records that the controller created a Draft PR; the stored PR reference
does not establish its current remote Draft/Ready, review or merge state. Goal
GET requests make no GitHub or model calls. Consumers display these stages
separately and use the recorded PR link for remote review.

Goal progress displays execution/review state and a visible functional status for
each materialized Task. **查看功能检查** opens the shared check report; its evidence
disclosure contains the exact artifact identities. **查看运行** opens the existing
Run route using the encoded runtime Task ID, including Tasks outside the current
history page. Unlaunched plan rows have no synthetic Run link. Missing executor
provenance cannot borrow the Goal's executor to produce a positive badge, and a
fixture lifecycle cannot present real implementation acceptance.

Home, review and Roadmap completion labels describe execution ended and pending
review. Goal rows show recorded publication progress independently: a recorded
Draft is not an observation of the PR's current remote state. Even a valid
functional check and a Draft record leave remote review, merge and delivery
unconfirmed. A newer unverified response replaces the earlier positive badge.

In the Goal review page, choose **编辑当前计划**, then **添加功能检查** for
each planned Task. Select Python/pytest or JavaScript/npm test and its repository
relative directory (`.` for the root). The editor rejects duplicate pairs,
invalid directories and more than eight checks per Task. Saving preserves the
Task identities and dependencies and requires another explicit review and
approval; it does not launch execution. Removing the last check submits an empty
selection. Existing selections survive instruction edits. If another update
makes the editor stale, local input remains visible and saving is disabled until
the user explicitly discards it and reloads. Approved/launched plans retain the
existing immutability policy.

Task and Run details share a bounded functional-evidence view. It shows the
host-reported verification state, profile and directory, exit code, actual
passed/failed/skipped counts, and expandable exact base/HEAD/tree and contract
and result digests. Missing, stale, incomplete and fixture evidence cannot turn
a zero exit code into functional success. This is a projection of host evidence,
not browser-side artifact verification or a second authority store. Raw command
output and environment fields are not displayed by this view. Patch hygiene,
functional verification, review readiness and Draft publication remain distinct.

Component tests cover selection/revision handling and the real adapter-to-hook
path into Task details, plus Run evidence rendering. The Playwright selection
scenario uses the explicitly mocked UI: it proves visible review controls,
not actual provider execution. Separate local acceptance uses the changed
TypeScript clients, real loopback Task API, disk SQLite, local Git and installed
pytest; only model execution and binding metadata are test doubles. No local
browser, provider call or snapshot update was part of that earlier R2 slice.
The visible Goal integration additionally requires isolated real Edge acceptance
through the actual frontend and Task API, with disk SQLite/Git/pytest and
disclosed execution/binding doubles. That acceptance is distinct from provider
dogfood and actual desktop lifecycle acceptance. Windows Edge screenshots do
not replace the natural Ubuntu Chromium golden checks. Functional evidence
grants no publication or merge authority; full F03 acceptance remains tracked
under #653.
# Explicit dependency inputs

See [Accepted artifact inputs](artifact-handoff.md) for selecting one checked
dependency as a task's exact code input. Validation-only consumers run host checks
without model edits; functional evidence retains both the original approved base
and the consumed producer commit/tree identity.

## Test-report consistency at admission and readback

The existing parser and functional-evidence projection share a strict report
predicate. `accepted: true` alone is not proof: `tests`, `passed`, `failed` and
`skipped` must be nonnegative integers (not booleans, strings or floats), their
sum must agree, at least one test must pass, and no test may fail. The stored
acceptance flag must still be exactly `true`; recomputation cannot promote a
missing or false flag. Valid reports with some skipped tests remain admissible;
entirely skipped or zero-test reports do not.

The report format must match the selected profile: Python/pytest requires JUnit;
the supported npm scripts use JUnit or TAP. Unknown report kinds and repeated,
contradictory or malformed TAP summary keys are rejected instead of taking the
last reported value. The same checks run when reading persisted evidence, so a
report with matching ordinary digests but contradictory counts cannot produce a
positive Task/Run functional-verification projection. Historical evidence is not
silently rewritten and validation is not rerun by the read path.

This consistency check is not an authenticity signature, a protected-verifier
execution environment or proof that every requested obligation was tested.
Correct-looking fabricated records still require provenance protection at the
existing trusted-host boundary. The change neither adds an evidence store nor
authorizes publication, merge, deployment or modifications to the verifier's
own authority. These remaining requirements stay under #653 and #379.

The report-consistency regression suite includes malformed persisted records,
positive controls, actual fixed pytest/JUnit subprocesses and disk-SQLite
readback through the real Task/Run projections. Model execution and binding use
the existing disclosed local test doubles. Persistence corruption is injected
only by tests, with ordinary digests updated deliberately to exercise count
validation rather than a pre-existing digest mismatch; this does not demonstrate
an untrusted production write path. A generated all-skipped test suite is a
negative input, not a skipped regression test.


Native candidate recovery freezes the approved repository base before accepting
PRE_PLANNER. Recovery rechecks live Goal/window admission, prepares only the
owned disposable checkout, and verifies or initializes that same base under the
new lease. An existing nonrepository workspace container may be reconstructed;
a contradictory Git checkout remains rejected. Historical empty-base runs are
bound to the unchanged approved contract before validation.

Reading an accepted POST_VALIDATION result checks the frozen Goal/task/plan
snapshot and the run's candidate/base plus existing digest, lease, repository,
head and tree proof. Normal Goal completion or window expiry/stop does not
require a new execution and does not invalidate that unchanged historical
result. New executor work still requires a RUNNING Goal and ACTIVE window.
