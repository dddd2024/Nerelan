# Design QA

Status: PASSED

## Reference and capture contract

- Selected directional reference: C:/Users/wjc27/.codex/generated_images/01a03111-d2a3-78a2-a23b-aabff89f5ffa/exec-b89c9079-4691-4fbb-b700-2149d5311309.png
- Reference SHA256: f205bb1ec30da46c99c4bdc087ba99547f2515d7aca039b2e2a24dc45554fc86
- Native reference size: 1487x1058
- The reference is directional design-language evidence only, not a pixel baseline.
- All pass/fail comparisons use the same app viewports: desktop 1440x900, mobile 390x844.
- Runtime lock for Issue #492: Ubuntu 24.04, Node 22.23.1, @playwright/test 1.62.1, Chromium revision 1234 / Chrome for Testing 151.0.7922.34.
- Runtime network surface: loopback mock application only; no provider/model/credential access.

## Historical baseline

The earlier bounded visual recovery established the first eight Home/Settings goldens. Those snapshots intentionally remained stale throughout the #448 R1 convergence sequence so intermediate layouts would not be canonized.

## Issue #492 final visual acceptance candidate

Source branch: `owner/issue492-final-visual-golden-r3-v1`

Locked integration base: `main@f1f366a9f5a3663430cd1eddb559ea07de434738`

Candidate head inspected: `b8bc057a58258a84b8f7d8bcd03f178a29c624bf`

Frontend Playwright run: `33475992766` / run #56. Artifact: `frontend-playwright-results`, artifact id `9788256355`, artifact ZIP SHA256 `d1cdc719574547854887953978f0973f2987c5bd2ed8e5f59286c2d15f2638a7`.

Observed suite result before golden materialization: 48 tests total; 16 functional tests passed, 8 viewport/state-specific tests skipped by contract, and 24 visual assertions failed only because the accepted candidate PNGs are either new lifecycle snapshots or intentionally stale Home/Settings baselines. No functional journey failure was observed.

Same-viewport visual inspection disposition: ACCEPTED. The candidate preserves the #448 task-first two-pane contract: warm paper shell, expanded quiet Nerelan sidebar, one neutral rounded workspace, compact composer, active Goal-first hierarchy, continuous semantic execution stream, restrained metadata, quiet normal states, prominent exception states, and no permanent right rail. The inspected running, validating, failed, Owner-action, large-change and multi-Agent desktop states remain legible without card-wall regression; mobile candidate states preserve the compact single-workspace presentation.

Lifecycle/stress coverage now represented by deterministic test-side state only: empty, running, waiting, validating, completed, failed, blocked, Owner action, large changes, long stream and multi-Agent. Production runtime truth is unchanged.

## Accepted candidate snapshot manifest

The following SHA256 values are computed from the exact `*-actual.png` files emitted by Frontend Playwright run #56 and are the only accepted PNG bytes for the one permitted Issue #492 snapshot materialization.

- frontend/e2e/snapshots/desktop-chromium/home-blocked-light.png — 2a33a5c3945842a5f92fc0b155077facf4bc0f27077fe2f5fe0b4ffac8ab8bec
- frontend/e2e/snapshots/desktop-chromium/home-completed-light.png — 5b93d55121cb15d88e2833fc51f27ac0c8e312b9bbcd30c6ec6231adc3609fb7
- frontend/e2e/snapshots/desktop-chromium/home-dark.png — 9c38986ec8423413fa1a97e959fe48cadb7dd9a1e0fc551cfcc8fb90216cf00d
- frontend/e2e/snapshots/desktop-chromium/home-empty-light.png — cb73d9b149dbe8eacce12e041112de21a6ab4f38ba99004deeae3b12f21a543b
- frontend/e2e/snapshots/desktop-chromium/home-failed-light.png — 385bf2e729e18743208adb85f2f7faeaef1c78891e02bf8e7b86af8913207081
- frontend/e2e/snapshots/desktop-chromium/home-large-changes-light.png — 55837f7c401bf0736a29898a7a78630015523384b3ae42d8e8a2367a2d627f46
- frontend/e2e/snapshots/desktop-chromium/home-light.png — 500a0a3918c94d027bf4dbe83a491edc9dc245a58e352dc075bad7a9ea5fd869
- frontend/e2e/snapshots/desktop-chromium/home-long-stream-light.png — c2952a2ff204a2051ceecff7bc5f4f0e735ae09e4dbf2715b6f6b52272b6e84a
- frontend/e2e/snapshots/desktop-chromium/home-multi-agent-light.png — b2e34f20741fb933a8509b316cdf42b46bf880eaaba1b8b1b8aa71237474a4f9
- frontend/e2e/snapshots/desktop-chromium/home-owner-action-light.png — 1a820bf70cd3de819eab01a5b8b76d41667decf4c632fdbdb0969232d4f29ce7
- frontend/e2e/snapshots/desktop-chromium/home-running-light.png — 750ae4b5b5e9b73614448a3991e36751691baace8c875bfdbb03c1b4382dce75
- frontend/e2e/snapshots/desktop-chromium/home-validating-light.png — ec2ec278c8c40061d6159dd977c74e69d27049382e505cd7652b78c645161f31
- frontend/e2e/snapshots/desktop-chromium/home-waiting-light.png — 26bb45ba3e738c1d433c7f6ed198fdad7fa795d05570bb99926504026cdab6c6
- frontend/e2e/snapshots/desktop-chromium/settings-dark.png — c49bb2ea49192021a7283eecf054174ab88714e615879887f638667403e4e85a
- frontend/e2e/snapshots/desktop-chromium/settings-light.png — c7f236675d70c88c8978fc9240d4b48645c6b55a3e18be3ee63eb19aabf5edcb
- frontend/e2e/snapshots/mobile-chromium/home-blocked-light.png — 3f7750a63f735db6b7139386cd299a878e23e144f9f208173e1e095bf68aaae9
- frontend/e2e/snapshots/mobile-chromium/home-dark.png — ab0225302346ffaef3fbe992d4ea6c238247a7056b961409233ed6916a86e56e
- frontend/e2e/snapshots/mobile-chromium/home-empty-light.png — bdfc6f2dc94853c4dd6d721db2484690de04bf16ff11f04d5ab4599bea26c29b
- frontend/e2e/snapshots/mobile-chromium/home-light.png — 8821da7ffaec59891997cc02498c7b3f8a1b70ecf830be1bfc674c892d6de099
- frontend/e2e/snapshots/mobile-chromium/home-long-stream-light.png — 7936b7930a8ff0dc9bc0e914b38cc9b6340619190de013e414dc17da94fbaee5
- frontend/e2e/snapshots/mobile-chromium/home-owner-action-light.png — 8ecfe17694b638dc7b57e325fbeda15da3cc3e7b3cf93ea4da7b398b1cbc833d
- frontend/e2e/snapshots/mobile-chromium/home-running-light.png — 17ab49ee1dbac0991d51762ec19c9f1fb5f41ed1ba1d5ecbc1bdf9697ab4daca
- frontend/e2e/snapshots/mobile-chromium/settings-dark.png — 56848abfc843b93261d104caecf5f7c3dbfe52a31e3d048e8e283806b230a122
- frontend/e2e/snapshots/mobile-chromium/settings-light.png — 3e58ee1126fb7e51849299bb58416b0b93c3c87c47b04c4e0dffd64195e87877

## Issue #492 R3 v14 final re-anchor

- Branch: `owner/issue492-final-visual-golden-r3-v14`

- Draft PR: `#555`

- Locked integration base: `main@0da78df5d2c5337ffeab17e3a00651df507637f0`

- Accepted visual-source replay commit: `1cb438b3`

- Accepted golden materialization commit: `97d1a203`

- Bound first-acceptance head: `39ece65b56266e464ff73121dc33a442f44d1300`

- Mainline intent: schema v3 / `workflow_profile=browser_r3`

- Required workflows exactly:
  `CI`
  `Decision Preflight`
  `State Gate (pull_request)`
  `Frontend Playwright`
  `Model Access`

- First exact-head workflow evidence:
  CI `33586127647` — SUCCESS
  Decision Preflight `33586127603` — SUCCESS
  State Gate `33586127592` — SUCCESS
  Model Access `33586127608` — SUCCESS
  Frontend Playwright `33586127616` — SUCCESS

- Frontend Playwright:
  `40 passed / 8 skipped / 0 failed`
  `48 total`

- Runtime:
  Ubuntu 24.04.4
  Node 22.23.1
  @playwright/test 1.62.1
  Chrome for Testing 151.0.7922.34
  Chromium revision 1234
  workers 1

- No production `frontend/src/**` mutation
- No snapshot recapture
- No local browser execution
- 3/3 accepted visual text source blob replay verified
- 24/24 PNG source blob replay verified
- 24/24 accepted SHA256 manifest verified
- connection-degraded Goal/Run state remains
  `NOT_APPLICABLE_TO_GOAL_RUN_VISUAL_MATRIX`
  unless the existing document already expresses this in equivalent
  accepted wording; do not invent runtime truth.

`FIRST_EXACT_HEAD_BROWSER_ACCEPTANCE = PASSED`

## Governance disposition

`PRODUCT_DESIGN_CANDIDATE = ACCEPTED`

`FUNCTIONAL_BROWSER_JOURNEYS = PASS`

`SNAPSHOT_CANDIDATE_SET = LOCKED_BY_SHA256`

`SNAPSHOT_MATERIALIZATION = COMPLETE`

`FIRST_EXACT_HEAD_BROWSER_ACCEPTANCE = PASSED`

`DESIGN_QA = PASSED`

The accepted PNG set has been materialized exactly once; first exact-head browser acceptance succeeded. This documentation-only finalization is the final semantic mutation authorized by v14. A fresh exact-head five-workflow set is required on the new head. PR remains Draft; Ready/Merge remain unauthorized.