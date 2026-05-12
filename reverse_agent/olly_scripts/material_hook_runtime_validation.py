from __future__ import annotations

try:  # Reuse the bounded Frida/UIA hook collector with a narrower point set.
    from .compare_pre_compare_handoff_target_probe import main
except ImportError:  # pragma: no cover - exercised by subprocess execution
    from compare_pre_compare_handoff_target_probe import main


if __name__ == "__main__":
    raise SystemExit(main())
