# Frontend e2e

`npm run e2e` runs the whole Playwright suite; `npm run e2e:visual` runs only the
`@visual` screenshot tests whose baselines live in `snapshots/`.

## Updating visual baselines after an intentional UI change

Baselines must be captured in the CI runner image, so do not regenerate them
locally. Instead, from the PR branch:

1. Push a commit whose message contains `[update-visual-baselines]` (or run the
   *Frontend Visual Baselines* workflow with `workflow_dispatch` on the branch).
2. The workflow regenerates the PNGs, re-runs `@visual` against them, and
   creates the staging branch `ci-visual-baselines/<your-head-sha>` with one
   commit on top of that head. It never writes to your PR branch and never
   rewrites a staging branch; a head that was already staged is skipped.
3. Adopt the result with your own commit, which re-runs the normal checks:

   ```bash
   git fetch origin ci-visual-baselines/<your-head-sha>
   git checkout FETCH_HEAD -- frontend/e2e/snapshots
   git commit -m "Update visual baselines" && git push
   ```

Look at the PNG diff before committing: the independent review still has to
accept the new baselines like any other change.
