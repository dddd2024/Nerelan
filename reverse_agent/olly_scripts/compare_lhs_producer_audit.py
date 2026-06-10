from __future__ import annotations

try:
    from .compare_pre_compare_handoff_target_probe import main
except ImportError:  # pragma: no cover - direct script execution
    from compare_pre_compare_handoff_target_probe import main


if __name__ == "__main__":
    raise SystemExit(main())
