# ChatGPT Sites handoff — reverse-agent Frontend V1

## Purpose

This file defines the publication boundary for a **fixture-only interactive demo** of the reverse-agent Frontend V1.

The Sites version is a product demonstration, not a production control plane. It may display deterministic task, activity, evidence, diff and permission-policy fixtures, but it must not receive credentials or invoke Git, GitHub mutations, shells, model APIs, OpenHands runtime, deployment systems or reverse-engineering tools.

## Source of truth

- Repository: `dddd2024/reverse-agent`
- Work Item: Issue #117
- Draft PR: #119
- Source directory: `frontend/**`
- OpenHands reference: tag `1.8.0`, commit `c7a765d900df294cbbf0f405ae26c9cbbd0fcc29`
- Data mode: deterministic local fixtures only

## Required screens

1. Task inbox
   - Needs Owner Attention
   - Running
   - Recent Tasks
2. Task workspace
   - chronological Activity
   - Changed Files and diff
   - Evidence
   - Authority
3. New Task composer
   - `ASK_FOR_APPROVAL`
   - `CONTROLLER_REVIEW`
   - `OWNER_CONTROL`
   - `CUSTOM`
4. CUSTOM policy editor
   - repository and branch scope
   - merge and push-main kept independent
   - release, publication and deployment controls
   - expiry, budgets, retries and stop conditions
5. Responsive shell
   - 60px / 300px desktop sidebar
   - mobile hamburger, backdrop and fixed left drawer
   - reversible one-pane mobile task workspace

## Public-data restrictions

Before publishing, verify that the generated Site contains none of the following:

- tokens, API keys, cookies or credentials;
- private repository URLs or private issue content;
- absolute local paths such as `F:\reverse-agent`;
- raw personal information;
- executable GitHub write controls;
- live shell, Git, model or deployment calls;
- production logs or unredacted stack traces.

The existing fixture names and synthetic SHAs may be retained only when clearly labelled as demonstration data.

## Interaction boundary

Allowed in the public demo:

- local UI state changes;
- opening and closing panels;
- selecting permission profiles;
- editing an in-memory CUSTOM policy;
- expanding deterministic evidence and diffs;
- responsive navigation.

Forbidden in the public demo:

- real task submission;
- network mutation;
- repository mutation;
- authentication or secret collection;
- file upload containing private data;
- production analytics containing user identifiers.

## Local verification before import

Run from the repository root:

```bash
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend run build:mock
git diff --check 1142dd324fdd4c4bf2a1353d9d5e93bc04b33507..HEAD
```

All commands must exit `0`. A failed or skipped frontend test is not acceptable publication evidence.

## Sites creation brief

Use the contents of `frontend/**` as the product and visual source. Preserve the OpenHands-style shell and reverse-agent terminology. Recreate the interactions with client-side state and deterministic fixtures only.

Suggested Sites instruction:

```text
Create a responsive interactive demonstration of reverse-agent Frontend V1 from the supplied frontend source. Preserve the dark OpenHands-style application shell, 60px/300px desktop sidebar, mobile drawer, task inbox, chronological Activity workspace, Changed Files/Diff, Evidence, Authority and New Task permission selector. Use deterministic fixture data only. CUSTOM policy edits must remain in local page state. Do not add authentication, network calls, GitHub writes, shell execution, model calls, uploads, deployment actions or credential fields. Clearly label the product as an interactive prototype.
```

## Publication sequence

1. Complete exact-head frontend verification.
2. Perform Owner desktop and mobile visual review.
3. Import the source and this handoff into ChatGPT Sites.
4. Review every page and interaction in Preview.
5. Confirm the public-data restrictions above.
6. Publish through the Owner's ChatGPT Sites UI.
7. Record the resulting public URL in Issue #117 or a separately authorized deployment Work Item.

The final Sites `Publish` action is an account-level Owner operation. It is not authorized by Decision v4 and is not performed by repository code.
