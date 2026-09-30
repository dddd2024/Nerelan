# Required-check producer and commit binding

Scope: #1041 / priority #1010 A2b / parents #379 and #653.
This is a repair of `GitHubRemoteAcceptanceVerifier.verify_check_run_contexts`,
not a new verifier, authority source, automatic-merge service or ruleset change.

## Evidence admitted by this method

The existing method reads GitHub REST check-run objects, not an agent's claim
that a similarly named command passed. Its first-party GitHub.com policy now
requires the observed App integer ID `15368` and slug `github-actions`. Those
expected values are repository-owned policy, not inferred from returned data,
a display name or a request's asserted producer.

Each record must carry the requested exact commit SHA, a positive integer ID,
and its exact repository-scoped API URL. Required context names must be bounded,
nonempty and unique. Names are compared exactly, including case. Missing or
malformed identity cannot be replaced with the expected value. An unknown API
host cannot borrow GitHub.com's App identity; separately governed host policy is
needed for an enterprise/custom-host integration.

An unrelated App never satisfies a first-party required context. A valid
foreign-App failure also cannot override the expected App's legitimate result.
Malformed records are not silently discarded as if the observation were whole.

## Complete, bounded observation

The existing read-only transport reads `filter=latest`, 100 records per page,
up to 1,000 records. The API's `total_count`, page lengths and record IDs must be
consistent. A missing/truncated page, duplicate ID, changed total, malformed
payload or unavailable later page rejects the observation even if page one has
a green result. The collector does not follow URLs supplied inside records.

These checks detect observable inconsistency; multiple requests are not an
atomic snapshot. Stable counts alone do not prove absence of concurrent or ABA
changes. Later privileged actions still require their own immediate identity,
authority and freshness checks.

## Outcome rules

Only `status=completed` plus `conclusion=success` from the expected producer
satisfies a context. A same-name expected-producer failure, pending result or
unknown state blocks a green record from hiding the conflict. The method does
not guess authority from the greatest numeric ID or newest timestamp.

A skipped record never satisfies a requirement. Existing PR/push/conditional
workflows can emit a separate skipped job with the same name as a real successful
job. This case retains the actual success without describing the skipped job as
passed. If all applicable records are skipped, the context remains unsatisfied.
Neutral, cancelled and timed-out are not successful outcomes.

The returned `context_check_ids` identifies real successful observations;
`blocking_check_ids`, `skipped_check_ids` and `ignored_foreign_check_ids` explain
the disposition. Callers must honor `verified` and `contexts`: a successful ID
can coexist with a blocking ID, in which case the context is not verified.
No merge, implementation-completion or independent-acceptance authority is added.

## Integration and remaining trust boundaries

The existing `mainline_landing` false/none post-merge validation path calls this
method. Its signature and other methods remain unchanged. This patch does not
install a universal pre-merge guard, enable an automatic merge, or replace the
other landing predicates. A5 remains responsible for composing the pre-action
promotion controller.

App identity is necessary but **not protected workflow-source provenance**.
GitHub Actions can run a candidate-controlled workflow. This method does not
prove its workflow revision, referenced action/dependency closure, protected
execution environment, reviewer independence or all functional obligations.
Those remain explicitly unresolved under A2b/#379/#653.

A read of repository ruleset `21023698` on 2026-09-30 showed required names
`baseline`, `state-gate` and `landing-state-gate` without `integration_id` pins.
This task did not change those settings. Native expected-source enforcement and
its corresponding verification require a separately authorized configuration
slice; a code predicate alone is not proof that server-side rules are enforced.

## Verification

The dedicated provider-free regression suite imports the actual verifier and
simulates only the HTTP boundary. It covers producer identity, wrong artifacts,
empty requirements, conflicting outcomes, complete and invalid pagination,
observation bounds, and the existing Request/JSON parser composition. It makes
no model/provider call, reads no credential and does not mutate GitHub.

```text
python -m pytest tests/platform_v1/test_check_producer_binding.py -q
python -m pytest tests/test_mainline_landing.py -q
```

The first command can run on an exact partial-source checkout. Full-package
compatibility and the original tests are separately exercised by natural CI's
existing mainline and blocking Platform V1 suites. Simulated HTTP and replay of
observed response fields are not a live end-to-end authorization proof. Author
verification is not independent acceptance.

## Native references

- GitHub REST checks, list check runs for a Git reference:
  https://docs.github.com/en/rest/checks/runs#list-check-runs-for-a-git-reference
- GitHub required-status troubleshooting and expected App source:
  https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks

These native identity/observation primitives are reused instead of adding a
second evidence store, generic model judge or general policy language.
