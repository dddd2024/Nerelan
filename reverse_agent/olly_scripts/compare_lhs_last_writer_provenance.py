from __future__ import annotations

try:
    from .compare_pre_compare_handoff_target_probe import main as _pre_compare_main
except ImportError:  # pragma: no cover - direct script execution
    from compare_pre_compare_handoff_target_probe import main as _pre_compare_main


def main() -> int:
    """Run the bounded same-process compare-LHS last-writer provenance sidecar."""
    return _pre_compare_main()


if __name__ == "__main__":
    raise SystemExit(main())
