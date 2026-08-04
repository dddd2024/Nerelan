"""In-process attestation state established only by the isolated launcher."""

from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ActiveTrustedLauncher:
    trusted_verifier_root: str
    candidate_repository_root: str
    trusted_revision: str


_ACTIVE: ActiveTrustedLauncher | None = None


def activate_from_isolated_launcher(
    *, trusted_verifier_root: str, candidate_repository_root: str, trusted_revision: str,
) -> ActiveTrustedLauncher:
    """Activate only when called by the validated trusted launcher itself."""

    global _ACTIVE
    caller = Path(inspect.stack()[1].filename).resolve()
    expected = Path(__file__).resolve().with_name("trusted_live_launcher.py")
    if caller != expected or not sys.flags.isolated or not sys.flags.safe_path:
        raise RuntimeError("TRUSTED_LAUNCHER_REQUIRED")
    binding = ActiveTrustedLauncher(
        str(Path(trusted_verifier_root).resolve()),
        str(Path(candidate_repository_root).resolve()),
        trusted_revision,
    )
    _ACTIVE = binding
    return binding


def get_active_launcher() -> ActiveTrustedLauncher | None:
    return _ACTIVE
