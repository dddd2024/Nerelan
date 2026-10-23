# CI receipt-cap test clock repair

Base: `616a4bfd6839a886c56c9b1c2b05960edadc956e`

## Changes

- `tests/platform_v1/test_claude_reset_signals.py`
  - `test_64_receipt_cap_preserves_revision_of_oldest` now injects
    `clock=lambda: NOW`, matching the fixed parse clock. The Oct 22 offer no
    longer expires against the real Oct 23 wall clock, so the no-duplicate
    assertion remains valid.
  - Added
    `test_expiry_crossing_invalidates_once_and_stale_observation_cannot_reactivate`:
    a mutable injected clock crosses 2026-10-22 -> 2026-10-23. It verifies the
    banked offer invalidates exactly once, a repeated same-revision FRESH
    observation cannot reactivate or re-notify it, and a restart snapshot keeps
    the receipt invalid.
- Product behavior is unchanged; the existing watcher already implements the
  expiry contract.

## Verification

- `python -m py_compile tests/platform_v1/test_claude_reset_signals.py`: ok.
- `git diff --check`: clean.
- Pytest was not run in this bounded CLI session, per task constraints. Host is
  expected to run the whole `tests/platform_v1/test_claude_reset_signals.py`.
- Host verification pending.
