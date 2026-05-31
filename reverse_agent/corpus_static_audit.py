"""Corpus static audit CLI.

This module provides a command-line interface for performing static audits
of the reverse engineering sample corpus.

Usage:
    python -m reverse_agent.corpus_static_audit \
        --corpus-dir sample_corpus/reverse \
        --out project_state/corpus_static_audit.json \
        --gap-report project_state/corpus_solver_gap_report.md
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from reverse_agent.corpus_classifier import (
    CATEGORIES,
    classify_sample,
    classification_to_dict,
)
from reverse_agent.corpus_loader import load_corpus_cases
from reverse_agent.static_feature_extractor import extract_static_features, features_to_dict


def run_audit(corpus_dir: Path) -> dict[str, Any]:
    """Run static audit on corpus.

    Args:
        corpus_dir: Path to corpus directory

    Returns:
        Audit result dictionary
    """
    cases = load_corpus_cases(corpus_dir)

    audit_cases = []
    category_counts: dict[str, int] = {cat: 0 for cat in CATEGORIES}
    unknown_count = 0

    for case in cases:
        # Extract static features (does not execute sample)
        features = extract_static_features(case.sample_path)

        # Read codex_task if available
        codex_task = ""
        if case.codex_task_path.exists():
            codex_task = case.codex_task_path.read_text(encoding="utf-8")

        # Classify sample
        classification = classify_sample(
            case_id=case.case_id,
            features=features,
            notes=case.notes,
            codex_task=codex_task,
        )

        audit_case = {
            "case_id": case.case_id,
            "sha256": case.sha256,
            "size_bytes": case.size_bytes,
            "static_features": features_to_dict(features),
            "classification": classification_to_dict(classification),
            "status": "static_profiled",
        }
        audit_cases.append(audit_case)

        # Update counts
        category_counts[classification.predicted_category] += 1
        if classification.predicted_category == "unknown":
            unknown_count += 1

    # Build summary
    summary = {
        "total_cases": len(cases),
        "classified_cases": len(cases) - unknown_count,
        "unknown_cases": unknown_count,
        "category_counts": {k: v for k, v in category_counts.items() if v > 0},
    }

    # Build audit result
    audit_result = {
        "schema_version": 1,
        "generated_at": datetime.now().isoformat(),
        "corpus_dir": str(corpus_dir),
        "execution_policy": {
            "executed_samples": False,
            "runtime_probe_used": False,
            "static_only": True,
        },
        "cases": audit_cases,
        "summary": summary,
    }

    return audit_result


def generate_gap_report(audit_result: dict[str, Any]) -> str:
    """Generate solver gap report from audit results.

    Args:
        audit_result: The audit result dictionary

    Returns:
        Markdown formatted report
    """
    lines = []

    # Header
    lines.append("# Corpus Solver Gap Report")
    lines.append("")
    lines.append(f"Generated: {audit_result['generated_at']}")
    lines.append(f"Corpus: {audit_result['corpus_dir']}")
    lines.append("")

    # Execution policy
    lines.append("## Execution Policy")
    lines.append("")
    policy = audit_result["execution_policy"]
    lines.append(f"- Static Analysis Only: {policy['static_only']}")
    lines.append(f"- Samples Executed: {policy['executed_samples']}")
    lines.append(f"- Runtime Probes Used: {policy['runtime_probe_used']}")
    lines.append("")

    # Summary
    summary = audit_result["summary"]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total Samples: {summary['total_cases']}")
    lines.append(f"- Classified: {summary['classified_cases']}")
    lines.append(f"- Unknown: {summary['unknown_cases']}")
    lines.append("")

    # Category distribution
    lines.append("### Category Distribution")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for category, count in sorted(summary["category_counts"].items()):
        lines.append(f"| {category} | {count} |")
    lines.append("")

    # Per-sample details
    lines.append("## Sample Details")
    lines.append("")

    for case in audit_result["cases"]:
        case_id = case["case_id"]
        classification = case["classification"]
        features = case["static_features"]

        lines.append(f"### {case_id}")
        lines.append("")
        lines.append(f"- **SHA256**: `{case['sha256'][:16]}...`")
        lines.append(f"- **Size**: {case['size_bytes']:,} bytes")
        lines.append(f"- **Format**: {features['format']}")
        lines.append(f"- **Entropy**: {features['entropy_hint']}")
        lines.append("")

        lines.append("**Classification**:")
        lines.append(f"- Category: `{classification['predicted_category']}`")
        lines.append(f"- Confidence: `{classification['confidence']}`")
        lines.append("")

        if classification["evidence"]:
            lines.append("**Evidence**:")
            for ev in classification["evidence"]:
                lines.append(f"- ({ev.get('strength', 'unknown')}) {ev.get('detail', '')}")
            lines.append("")

        lines.append(f"**Recommended Next Step**: {classification['recommended_next_step']}")
        lines.append("")

        # Feature summary
        lines.append("**Feature Summary**:")
        lines.append(f"- ASCII strings found: {len(features['ascii_strings_sample'])}")
        lines.append(f"- UTF-16LE strings found: {len(features['utf16_strings_sample'])}")
        lines.append(f"- Crypto hints: {len(features['crypto_hints'])}")
        lines.append(f"- Compare hints: {len(features['compare_hints'])}")
        lines.append(f"- Interesting constants: {len(features['interesting_constants'])}")
        lines.append("")

    # Capability coverage
    lines.append("## Current Capability Coverage")
    lines.append("")

    covered = [
        ("affine_lowercase", "Fully covered by simple_static_patterns.py"),
        ("caesar_or_shift", "Fully covered by simple_static_patterns.py"),
        ("xor_or_bytewise", "Helper functions available in simple_static_patterns.py"),
        ("hash_check", "Hex digest detection available in simple_static_patterns.py"),
    ]

    lines.append("### Covered Capabilities")
    lines.append("")
    for category, description in covered:
        count = summary["category_counts"].get(category, 0)
        lines.append(f"- **{category}** ({count} samples): {description}")
    lines.append("")

    # Capability gaps
    lines.append("### Capability Gaps")
    lines.append("")

    gaps = [
        ("rc4_like", [
            "No static RC4 KSA/PRGA identification",
            "No automatic key extraction from binary",
            "No RC4 keystream analysis",
        ]),
        ("des_like", [
            "No static DES key schedule analysis",
            "No DES S-box or permutation table identification",
            "No automatic key/ciphertext extraction",
        ]),
        ("aes_like", [
            "No static AES key schedule analysis",
            "No AES S-box identification",
            "No automatic key extraction",
        ]),
        ("seh_or_exception", [
            "No SEH handler chain analysis",
            "No exception-based control flow reconstruction",
            "No anti-debugging detection via SEH",
        ]),
        ("base64_or_encoding", [
            "Basic detection available but no automatic decoding",
        ]),
        ("string_compare", [
            "Basic detection available but no automatic string extraction",
        ]),
    ]

    for category, gap_list in gaps:
        count = summary["category_counts"].get(category, 0)
        if count > 0:
            lines.append(f"**{category}** ({count} samples):")
            for gap in gap_list:
                lines.append(f"- {gap}")
            lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    lines.append("### Next Steps")
    lines.append("")
    lines.append("1. **Start with one capability at a time** - Do not attempt to implement")
    lines.append("   DES, RC4, and SEH solvers simultaneously.")
    lines.append("")
    lines.append("2. **Prioritize by sample availability** - Focus on categories with")
    lines.append("   the most samples first.")
    lines.append("")
    lines.append("3. **Maintain static-first approach** - Continue using static analysis")
    lines.append("   before considering dynamic execution.")
    lines.append("")
    lines.append("4. **Evidence-based implementation** - Build solvers based on actual")
    lines.append("   patterns found in the corpus samples.")
    lines.append("")

    # Specific recommendations based on current corpus
    lines.append("### Suggested Priority Order")
    lines.append("")

    # Sort categories by count
    sorted_categories = sorted(
        summary["category_counts"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    priority = 1
    for category, count in sorted_categories:
        if category == "unknown":
            continue
        if category in ["affine_lowercase", "caesar_or_shift", "xor_or_bytewise", "hash_check"]:
            continue  # Already covered

        lines.append(f"{priority}. **{category}** ({count} samples)")
        priority += 1

    if summary["unknown_cases"] > 0:
        lines.append(f"{priority}. **unknown** ({summary['unknown_cases']} samples) - Needs deeper analysis")

    lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Static audit for reverse engineering sample corpus"
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=Path("sample_corpus/reverse"),
        help="Path to corpus directory",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("project_state/corpus_static_audit.json"),
        help="Output path for JSON audit results",
    )
    parser.add_argument(
        "--gap-report",
        type=Path,
        default=Path("project_state/corpus_solver_gap_report.md"),
        help="Output path for gap report markdown",
    )

    args = parser.parse_args()

    # Run audit
    print(f"Running static audit on {args.corpus_dir}...")
    audit_result = run_audit(args.corpus_dir)
    print(f"Audited {audit_result['summary']['total_cases']} samples")

    # Write JSON output
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(audit_result, f, indent=2)
    print(f"Wrote audit results to {args.out}")

    # Generate and write gap report
    gap_report = generate_gap_report(audit_result)
    args.gap_report.parent.mkdir(parents=True, exist_ok=True)
    with open(args.gap_report, "w", encoding="utf-8") as f:
        f.write(gap_report)
    print(f"Wrote gap report to {args.gap_report}")

    # Print summary
    print("\nSummary:")
    summary = audit_result["summary"]
    print(f"  Total samples: {summary['total_cases']}")
    print(f"  Classified: {summary['classified_cases']}")
    print(f"  Unknown: {summary['unknown_cases']}")
    print("\nCategory distribution:")
    for category, count in sorted(summary["category_counts"].items()):
        if count > 0:
            print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
