# Design QA

Status: PASSED

## Reference and capture contract

- Selected directional reference: C:/Users/wjc27/.codex/generated_images/01a03111-d2a3-78a2-a23b-aabff89f5ffa/exec-b89c9079-4691-4fbb-b700-2149d5311309.png
- Reference SHA256: f205bb1ec30da46c99c4bdc087ba99547f2515d7aca039b2e2a24dc45554fc86
- Native reference size: 1487x1058
- The reference is directional design-language evidence only, not a pixel baseline.
- All pass/fail comparisons use the same app viewports: desktop 1440x900, mobile 390x844.
- Official image: mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e
- Runtime: Ubuntu 24.04, Node 22.23.1, @playwright/test 1.62.1, Chromium revision 1234 / Chrome for Testing 151.0.7922.34.

## Visual evidence

The unlayered global margin: 0/padding: 0 reset overrode Tailwind utility classes. Removing those declarations and retaining only box-sizing: border-box restored the intended hierarchy, spacing, rounded corners, borders, light/dark themes, cyan accent, and mobile layout without obvious breakage.

Linux snapshot update: 8 passed. Full Playwright: 24 passed, 2 viewport-specific skipped.

Issue #343 bounded re-capture (single permitted snapshot update): the replayed PR #341 snapshots were captured against the index.css without the unlayered global margin/padding reset, while locked current main `af0bfdb62d96e00b5f89660390950f3b7f096026` still carries that reset. Because this round freezes `frontend/src/**`, the eight baselines were re-captured exactly once in the same official container image against locked main rendering; no CI snapshot update occurred. Container re-capture: 8 regenerated, full Playwright 24 passed, 2 viewport-specific skipped.

Snapshot paths and SHA256 (current working tree, verified by `sha256sum`):

- frontend/e2e/snapshots/desktop-chromium/home-light.png — 9B8DACE44378B9CB034DB1A27E7FFF5EC1AF0DCE41BD3352966D53C10284FAEC
- frontend/e2e/snapshots/desktop-chromium/home-dark.png — 4911DE16438FDAEE2414C4FB677A647FBC68E18D1885EC86E4BC74F18FC72BE7
- frontend/e2e/snapshots/desktop-chromium/settings-light.png — 420FCA597ADC0C8D2CC82B1F92D96C5576807E0FB60027A4D8CE26836D016E01
- frontend/e2e/snapshots/desktop-chromium/settings-dark.png — 622CBC4D7676BAEAC3ADCEAB6AA3B77E5413421D74509804C43FF20BCE2F26D7
- frontend/e2e/snapshots/mobile-chromium/home-light.png — A663EE23819C0552195BD55184D89480C5FB7311EA73DD2A281728EE0D46C860
- frontend/e2e/snapshots/mobile-chromium/home-dark.png — 40C522028B8D6E741400C7FBC5A724D87ABC8BE20C1F262BAD8E291B386E323C
- frontend/e2e/snapshots/mobile-chromium/settings-light.png — 97A34B2177F69F13BF4B88C1C75A9CCE6E057B1EEDA478DC797F7707457C7F91
- frontend/e2e/snapshots/mobile-chromium/settings-dark.png — 9DE1B453F113631907E5B8283537F636E7DCD98FD8C8D47F46F46D82C7F823F7

Provenance of the eight values above. The previously recorded hashes for the same paths (desktop home-light `AA4EB97D…`, home-dark `7827EF30…`, settings-light `D262BB23…`, settings-dark `DB7F60B4…`; mobile home-light `76727CE5…`, home-dark `0AC46E91…`, settings-light `CA0EB688…`, settings-dark `395C49F1…`) were captured before this round re-anchored the frontend onto current main, and no longer matched the rendering produced by this branch. All eight were therefore re-captured, and they are recorded here as the observed render of this branch rather than inherited from the earlier round.

Capture source. The eight baselines were taken from the canonical CI container, not from a local run: GitHub Actions workflow `.github/workflows/frontend-playwright.yml`, job `e2e`, run `36562645075`, artifact `frontend-playwright-results`. Each `*-actual.png` produced by that job was written to its corresponding path above, so the baselines are the exact bytes the workflow itself renders. That workflow runs in the same official image and runtime recorded under "Reference and capture contract" above (`mcr.microsoft.com/playwright:v1.62.1-noble`, Chromium revision 1234), which is what makes them valid as the pixel contract for the required `e2e` check.

Why CI rather than local. A local `--update-snapshots` run did not complete — one test in 29 minutes — while the identical suite finished on CI in 1.9 minutes, so the local capture path is unreliable in this environment and was not used. Because `frontend-playwright.yml` triggers on `frontend/**` changes and runs the full suite including the `@visual` projects, these baselines are a hard required check rather than an optional record, which is why the refresh is in scope for this round.

Rendering changes behind the refresh. Four of the eight — the settings pair on both viewports — additionally reflect two changes in this round: the accent swatch in `theme.ts` now resolves from the `--ra-swatch-*` tokens instead of a hardcoded saturated hex, and `src/index.css` now sets `accent-color: var(--ra-accent)` on native checkbox/radio so those controls follow the product accent instead of the browser default blue. The remaining four reflect the broader re-anchor of the frontend onto current main.

Agent workbench refresh (PR #1397). The shell, the home route and the palette changed, so the six baselines above that changed were re-captured the same way: `*-actual.png` from the `frontend-playwright-results` artifact of workflow run `42352221184`, not a local run. The home baselines now show the composer-first page, because Home no longer selects a goal by itself. The previous values are in git history.

The implementation retains the current product Home/Settings information architecture and does not fabricate unavailable capabilities or states.
