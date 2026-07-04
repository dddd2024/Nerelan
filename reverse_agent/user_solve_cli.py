from __future__ import annotations

import argparse
import json
from typing import Sequence

from .user_solve_controller import UserSolveController
from .user_solve_fixtures import FIXTURE_NAMES
from .user_solve_request import demo_request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fixture-only user solve preview.")
    parser.add_argument("--demo", choices=FIXTURE_NAMES, required=True)
    parser.add_argument("--developer", action="store_true", help="Include developer audit fields.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    envelope = UserSolveController().solve(demo_request(args.demo))
    payload = envelope.to_developer_dict() if args.developer else envelope.to_user_dict()
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
