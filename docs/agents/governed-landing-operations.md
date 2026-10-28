# Governed unattended landing

This R2 implementation implements Owner decision **2026-10-20: approved** for
issue #1266, T003. It retains the review and landing rules in AGENTS.md and
[the governance reference](governance-reference.md#landing). An independent
reviewer must confirm that this change does not weaken gates beyond that decision.
No live acceptance is claimed by the offline tests.

The trusted host connects retained-artifact publication and independent review
to UnattendedCoordinator, followed by LandingLoopController ticks. Startup alone
does not grant authority: autonomy must be enabled and an owner-activated,
current, repository-scoped window must include the relevant publication, review
and landing capabilities. Existing delegated/trusted-policy publication adapter
restrictions still fail closed.

The host's optional `landing_owner_decisions` callable is a trusted integration
boundary, never a browser field, model claim or PR-body authority source. It must
return only verified Owner-decision citations for the supplied goal/repository.
Its default is empty. R2 publication parks without such evidence; the generated
PR body names supplied decisions. Landing independently reads actual GitHub
changed paths and requires a trusted citation in the body. Sensitive credential
paths park; no R3 operation is admitted by this adapter. Fresh action-specific
Owner authorization must be handled through separately admitted host operations.

Each tick takes a persisted five-minute lease. Writes additionally have durable
operation claims and reconciled receipts. Normal waits retry after 30 seconds;
API failures retry after 60 seconds, persisted across restart. There is no inner
polling loop. Unknown write outcomes are queried again, never blindly replayed.
An unresolved operation may require operator investigation rather than a retry.
The run detail `landing` projection exposes phase, review round, PR/head,
next retry timestamp and parking reason; it does not mirror GitHub state.

Before writes, the loop rereads authority, repository/base, PR, head and main.
It requires the latest successful GitHub Actions baseline and state-gate check
runs on the current head, updates behind branches only through GitHub's
merge-main update endpoint with expected-head protection, and reassesses the
new head. A new review round waits for a fresh independent ACCEPT or the existing
checker's verified carry-over result. Ancestry alone never supplies acceptance.
The checker itself is unchanged. Ready requires accepted review; landing then
requires the fresh current-head landing-state-gate. Immediately before the
head-matched merge-commit command, the adapter runs the mandatory verdict CLI.
A newer trusted REJECT blocks. Receipt reconciliation checks the PR's recorded
merge commit against main before terminal success, including after restart.

## Supervised harmless-change acceptance (not executed)

1. In a separately authorized live session, select a harmless ordinary product
   documentation change in an isolated branch and configure a bounded window
   for just its repository and goal. Preserve existing work. Do not use secrets,
   releases, deployment, destructive operations or untrusted binaries.
2. Submit a planned retained-artifact producer and independent validate-only
   reviewer through the normal goal/task entry. Observe unattended publication
   to Draft; record the PR, exact head, review evidence and run-detail state.
3. Verify baseline and state-gate independently on that head. Verify the fresh
   reviewer context read the complete diff and posted the trusted ACCEPT marker.
   Observe Ready, the current-head landing-state-gate, mandatory verdict recheck
   and head-matched merge command through host evidence.
4. Confirm GitHub main equals the PR's recorded merge commit. Record this remote
   evidence as functional acceptance; a successful CLI or fake fixture is not it.
5. In separately scoped scenarios, revoke the window, introduce a head movement,
   fail CI, post a newer trusted REJECT and interrupt the host after a remote
   write. Verify parking/reconciliation without duplicate writes or gate bypass.
   R2 acceptance additionally needs a trusted decision citation in the body and
   the accepting independent reviewer's explicit confirmation of the decision's
   bounds, recorded as `Nerelan-R2: CONFIRM <40-hex head> <exact decision citation>`
   on its own unfenced line in a trusted comment/review. The adapter requires
   this confirmation before Ready; the ordinary verdict checker remains unchanged.

Do not run this procedure from provider-free startup or CI. Local validation is
`python -m pytest tests/platform_v1/test_landing_loop.py tests/platform_v1/test_run_read_model.py`
and `git diff --check`. These tests use fake GitHub/provider boundaries and
imported-module subprocess patches; they do not establish live acceptance.
