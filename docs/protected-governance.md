# Protected governance execution (shadow)

Work Item #1045; priority #1010 A2b-2b; parent #379 / #653.
This is an execution adapter for existing governance lint, not a new authority
engine. No source change in this document or its diagnostic grants permission.

## What is implemented

`tools/protected_governance.py` reads a fixed standard-library-only source closure
from an independently selected trusted Git commit, exports those exact bytes
into a fresh private directory, and starts a real `python -I -S -B` subprocess.
The subprocess invokes the existing `load_transition_decision`,
`build_transition_command_plan` and `validate_command_plan` functions.

Only `project_state/decision_packet.md` is read from the candidate commit. It is
passed as bounded UTF-8 data, never imported or installed. Its submitted command
strings are never executed. Candidate packages, setup hooks, local actions,
customization files, source modules and bytecode cannot supply this process's
project imports. An invalid plan is still invalid when the candidate replaces
its own validator with an always-successful implementation.

This is a concrete protected execution route for **R2 Decision/plan lint**. It is
not full Path-A/Path-B authorization, functional acceptance or a merge controller.

## Invocation and trust roots

Run an independently trusted copy, not a candidate-provided launcher:

```text
/usr/bin/python3 -I -S -B /trusted/tools/protected_governance.py \
  --repository-dir /trusted \
  --git-executable /usr/bin/git \
  --trusted-ref TRUSTED_FULL_COMMIT_SHA \
  --candidate-ref CANDIDATE_FULL_COMMIT_SHA
```

Both refs must be full lowercase 40-character Git commit identifiers. `/trusted`
is an operator-controlled Git object repository and configuration, not a
candidate checkout or candidate-controlled `.git` directory. The operator also
trusts the Git/Python executables, standard library, dynamic loader, operating
system and the initial launcher. A launcher cannot establish its own trust after
malicious code has already started running.

The checked launcher must equal its committed trusted blob. All project imports
come from a fixed exported closure. Git reads use raw objects rather than
checkout filters, textconv, symlink following or submodule checkout. Each file's
mode, size and recomputed Git blob identity are checked. Git replacement refs,
lazy fetching, global/system configuration and inherited environment overrides
are disabled. Repository-local configuration remains part of the trusted host
contract; this is not a parser for hostile `.git` configurations.

A clean child environment contains no inherited GitHub/provider credentials,
Python search-path variables, proxies or dynamic-loader overrides. The tool
requires isolated/no-site/no-bytecode startup. No installed project package or
third-party dependency is required by the exported source closure. A missing or
new out-of-closure project import fails rather than using installed fallback code.

## Shadow workflow

`.github/workflows/protected-governance.yml` proposes a separate
`pull_request_target` shadow job. Its source revision is `github.workflow_sha`
from the protected base repository event context, never a SHA from candidate
files or PR prose. The single checkout action is pinned by full commit SHA.
Only trusted source is checked out; candidate Git objects are fetched from the
canonical public repository without a candidate worktree checkout.

The initial workflow handles same-repository PRs into `main` only. It has
`contents: read`, no secret inputs, dependency installs, caches, persistent
checkout credentials, manual dispatch or merge operation. Unsupported/fork PRs
are not claimed evaluated. This shadow job name must not be added to required
merge contexts as a shortcut to full live authorization.

The default branch is the deployment trust root. Promoting a new validator to
that branch requires the existing independent acceptance and separately scoped
landing authority. A candidate cannot select its own evaluator pin merely by
editing this workflow in its PR.

**An unmerged workflow is not a deployed workflow.** Full CI exercises the real
Git/process composition using synthetic histories, but actual protected event
invocation and policy rollout still require post-landing observation.

## Output and bounds

Exit 0 / `VALID` means only that the pinned existing compiler/plan checks found
no lint defect. Exit 1 / `INVALID` is a completed negative lint result; exit 2 /
`ERROR` is a missing/invalid input or execution-boundary failure. Argument usage
errors use argparse's usual exit 2. Invalid/unsupported Decision formats do not
produce an approval. The older parser's semantics remain unchanged.

Every result is `SHADOW_ONLY`. Approval, implementation, Ready, merge, product
acceptance, implementation completion and candidate/Issue-command execution
flags are false. A Decision that says `APPROVED` is still only input data here;
this route does not authenticate who approved it or whether approval was revoked.

The successful process observation records trusted and candidate commit IDs,
Decision digest, exported source blobs/digests, actual loaded project-module
digests, Python version and child environment key names. This unsigned JSON is
not an independently authenticated execution receipt. It cannot replace GitHub
run identity, exact-head acceptance or a protected promotion decision.

Limits: 1 MiB per fixed source file, 256 KiB candidate Decision, 64 KiB worker
output/stderr, a 30-second overall subprocess budget and a 10-second worker
budget. Outputs are captured to temporary files and memory reads are bounded;
disk usage is checked after child completion, not an OS filesystem quota. These
limits do not establish an OS sandbox, CPU/memory quota, atomic observation or
protection against a compromised same-user host. The design does not execute
hostile candidate code; actual product tests need their own suitable sandbox.

## Verification and remaining work

The added blocking Platform V1 tests use the real existing repository validators,
real temporary Git commits and real Python subprocesses. They test valid and
invalid plans, candidate always-PASS validator replacements, package/setup/site
payloads with harmless observable marker attempts, dirty worktree modules and
bytecode, environment/credential exclusion, nonregular Git objects, missing and
oversize inputs, unsafe startup, timeout and excessive output. Source tests and
author checks are not independent acceptance.

Remaining work: integrate full live authority/functional obligations through a
protected path; authenticate actual workflow invocation/source version; separate
execution/review/promotion identities and credentials; enforce native source
restrictions; validate revocation and fresh pre-action state; then stage a bounded
real canary under its own authority. This shadow route does not finish overall A2
or enable general automatic merge. Earlier #1042/#1044 source patches are not
imported and must be preserved in future reviewed integration.

## Primary references

- Python command-line isolation and site controls:
  https://docs.python.org/3/using/cmdline.html
- GitHub Actions secure use (untrusted data and privileged triggers):
  https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- Workflow source identity context:
  https://docs.github.com/en/actions/learn-github-actions/contexts#github-context

The version-pinned project source is the definition of the implemented lint;
these references describe reused execution mechanisms, not new project authority.
