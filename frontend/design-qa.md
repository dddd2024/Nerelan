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

Snapshot paths and SHA256 (bounded re-capture on locked main):

- frontend/e2e/snapshots/desktop-chromium/home-light.png — AA4EB97D531B1720A58C06BC5DD273E8CAFFFA6A78871B5ABAB53B9B26D8528E
- frontend/e2e/snapshots/desktop-chromium/home-dark.png — 7827EF305C15F21067AF8CAEADC17F69A3F5263E9BF61036D2816570285DBA5D
- frontend/e2e/snapshots/desktop-chromium/settings-light.png — D262BB23EBFDD39480F9EB55E6A474D0DBADAB47F737A81539DA3CAEA977D139
- frontend/e2e/snapshots/desktop-chromium/settings-dark.png — DB7F60B4407B603DAE78F90A10BBE793F1E0C87923F8316A6558C7A0A220B7E8
- frontend/e2e/snapshots/mobile-chromium/home-light.png — 76727CE5B96020D354E523135B801102FCCFC0978B5719CB80375C8E1F7BD7B6
- frontend/e2e/snapshots/mobile-chromium/home-dark.png — 0AC46E9176E0018CC5D121AC093FC87FA358C6801518B2569603C4BDA6D04200
- frontend/e2e/snapshots/mobile-chromium/settings-light.png — CA0EB68807BC184CB6471B0F7A6E289A70910E0155D73AFD506A4A15D8C8FF42
- frontend/e2e/snapshots/mobile-chromium/settings-dark.png — 395C49F15DAAB3DD192D7CBEE2924504CDAEC016FBDBB07D3F051EE73A52FC1B

The implementation retains the current product Home/Settings information architecture and does not fabricate unavailable capabilities or states.
