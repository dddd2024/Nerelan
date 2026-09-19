"""Render native pytest JUnit statistics without changing the test exit status."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET


def render_summary(report: Path, exit_code: str) -> str:
    lines = [
        "## Selected repository diagnostic (nonblocking)",
        "",
        f"pytest exit code: <code>{escape(exit_code or 'unavailable')}</code>",
        "",
        "Scope: default provider-free selection. Four installed_opencode integrations "
        "are excluded and were not executed; this is not an all-tests-pass claim.",
    ]
    try:
        root = ET.parse(report).getroot()
        suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
        if not suites:
            raise ValueError("missing test suites")
        counts = {}
        for field in ("tests", "failures", "errors", "skipped"):
            values = [int(suite.attrib[field]) for suite in suites]
            if any(value < 0 for value in values):
                raise ValueError("negative count")
            counts[field] = sum(values)
    except (OSError, ET.ParseError, KeyError, ValueError):
        lines += ["", "**JUnit statistics unavailable; test success is unproven.**"]
        return "\n".join(lines) + "\n"

    lines += ["", "| Raw JUnit field | Count |", "| --- | ---: |"]
    lines += [f"| {field} | {value} |" for field, value in counts.items()]
    success = exit_code == "0" and counts["tests"] > counts["skipped"] and counts["failures"] == counts["errors"] == 0
    lines += ["", "**Selected tests passed.**" if success else "**Selected test success is not established.**"]
    failures = [case for case in root.iter("testcase") if case.find("failure") is not None or case.find("error") is not None]
    if failures:
        lines += ["", "Failing JUnit cases (up to 20; see the diagnostic artifact for details):", ""]
        for case in failures[:20]:
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            lines.append(f"- <code>{escape(name)}</code>")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--exit-code", default="")
    args = parser.parse_args()
    print(render_summary(args.report, args.exit_code), end="")
