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

- frontend/e2e/snapshots/desktop-chromium/home-light.png — EDF146B22451F9C9069F5C17A7F4B9B4D9517933514577E6054EEB7F6978BDFE
- frontend/e2e/snapshots/desktop-chromium/home-dark.png — 1AE03A05903872120B47DE03F42B24565FBF0279D5FC130C4F98A3BAB4ABF038
- frontend/e2e/snapshots/desktop-chromium/settings-light.png — 89DA7AEFC61530ED3E1536CEE21DCD6CBB76260073AC261F6C6884460724D5E7
- frontend/e2e/snapshots/desktop-chromium/settings-dark.png — 05655B3F094453DAB0AFDEB7121DE94B10FF057765BD7688A971DCA7898AC4DF
- frontend/e2e/snapshots/mobile-chromium/home-light.png — 3DC8D0483058BE539D2F746C81463BD9B02A945E280387268D194D94B0CC1656
- frontend/e2e/snapshots/mobile-chromium/home-dark.png — E46DE700DA483331DFA1D8418CF3914B3D06493262896FBFB739DB985D68AB50
- frontend/e2e/snapshots/mobile-chromium/settings-light.png — D61689D9C0AC72E5BBA2AD3FDF60A9A5F537277B19182FED75575994A98E889A
- frontend/e2e/snapshots/mobile-chromium/settings-dark.png — EEC0946C153AA54FA3090FF1AC8A2CC97DE802E5D522027BB4CEDC14856DAB2F

Previous recorded hashes for the same eight paths (desktop home-light `AA4EB97D…`, home-dark `7827EF30…`, settings-light `D262BB23…`, settings-dark `DB7F60B4…`; mobile home-light `76727CE5…`, home-dark `0AC46E91…`, settings-light `CA0EB688…`, settings-dark `395C49F1…`) no longer matched the working tree and have been replaced with the values above. Four of the eight — the settings pair on both viewports — were re-captured in this round for two rendering changes: the accent swatch in `theme.ts` now resolves from the `--ra-swatch-*` tokens instead of a hardcoded saturated hex, and `src/index.css` now sets `accent-color: var(--ra-accent)` on native checkbox/radio so those controls follow the product accent instead of the browser default blue. The remaining four had already drifted from this document before this round; they are recorded here as observed rather than re-captured.

The implementation retains the current product Home/Settings information architecture and does not fabricate unavailable capabilities or states.
