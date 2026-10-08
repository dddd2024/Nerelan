# Durable autonomous-window lifecycle

Issue #118 is the architecture target for bounded unattended operation. This
Phase-E prerequisite strengthens the existing window lifecycle; it does not
complete canonical policy activation or the privileged publication adapters.

An autonomous window remains in the existing TaskStore SQLite database.
Activation takes one `BEGIN IMMEDIATE` transaction that retires expired active
rows, checks immutable revision replay and digest conflicts, checks for another
active window, and inserts the new window. Independent host connections cannot
both admit windows after stale preflight observations. A future-start window
reserves the single active slot but cannot dispatch work before its start time.

Store replay of the same policy identity, revision and digest returns the existing
record, including its terminal state and spent counters. It does not reactivate
a stopped, expired, completed or blocked revision. Changing that revision's
content fails with `policy_revision_conflict`; a changed policy needs a new
revision. Restarting the host does not reset task, retry or observed usage counts.
Activation storage failure rolls back its transaction.
The service still validates the requested time bounds: an already expired
activation request cannot create a fresh window. Historical records remain
readable without granting execution.

Policy evaluation observes the current active window and requires its identity
to equal the requested window's identity. The presence of an unrelated window
cannot authorize an expired or stale request. Allowed and denied evaluations
continue through existing append-only receipts. Existing task claims and budget
reservations remain responsible for the atomic execution admission fence; a
policy evaluation alone is not a durable privileged-operation claim.

The legacy `ACTIVATE` field and declared owner name are not authenticated Owner
identity. This change does not promote them to verified authority. The remaining
#118 chain still requires canonical policy persistence, trusted Owner activation
and upper-authority compilation, complete per-operation context, durable
idempotency and external-truth recovery, and separately governed GitHub,
release and deployment adapters. Existing capability restrictions, secret
isolation, provider-free startup, independent acceptance and landing controls
remain in force.
# Delegated Goal admission

The trusted host may include `goal_admissions` in its existing immutable
PolicyAuthority binding: at most 100 exact `{goal_id, revision, artifact_digest,
idempotency_key}` snapshots. Such a binding explicitly grants `approve_goal` and
`validate_task`, and `max_tasks` equals snapshot cardinality. Each admitted Goal
contains one exact fixed `git_diff_check` task. The original single-checker
binding remains supported. This does not enable arbitrary coding, models,
GitHub writes, merge or deployment; those capabilities remain separate work.

The coordinator reads preauthorized planned Goals and admits them without
another interactive confirmation. Goal approval, task materialization and its
delegated-identity receipt commit in one existing TaskStore SQLite transaction.
Restart and concurrent connection replay use the original task/receipt; they
do not reset admission or execution allowances. Revision/digest drift, expiry,
revocation, missing authority and exhausted budgets reject. An isolated Goal
denial does not stall another eligible Goal. Receipt persistence failure rolls
back admission and persists a window hard stop.

The browser cannot submit an authoritative snapshot list. A trusted loader
must verify the activated Decision and complete binding. Capability metadata,
executor prose, test doubles and self-issued reports are not grants. Unit
composition uses actual temporary Git, disk SQLite and fixed host checks with
an explicitly synthetic authority loader; it is not live policy activation or
whole unattended-platform acceptance. Long-duration project selection, real
coding and separately governed delivery remain unimplemented by this slice.
