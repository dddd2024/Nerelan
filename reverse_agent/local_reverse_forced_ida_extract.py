"""Forced IDA decompilation for specific functions in unresolved samples.

Runs IDA in batch mode with forced_function_extract.py script to decompile
sub_401005 (and optionally sub_40100A) for sha_256.exe and CPP2.exe.

Decision: decision_20260603_local_reverse_forced_ida_extraction_v1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .tool_runners import (
    ToolAutomationConfig,
    ToolRunArtifact,
    _resolve_ida_executable,
    _populate_artifact_from_json_output,
)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _run_forced_ida_extraction(
    binary_path: Path,
    script_path: Path,
    output_path: Path,
    function_names: list[str],
    timeout_seconds: int = 180,
) -> ToolRunArtifact:
    """Run IDA with forced_function_extract.py for specific functions."""
    import subprocess
    import shlex

    artifact = ToolRunArtifact(
        tool_name="IDA_ForcedExtract",
        enabled=True,
        attempted=False,
        success=False,
    )

    ida_executable = _resolve_ida_executable("")
    if not ida_executable:
        artifact.error = "IDA executable not found"
        artifact.summary = "IDA forced extraction not executed"
        return artifact

    if not script_path.exists():
        artifact.error = f"IDA script not found: {script_path}"
        artifact.summary = "IDA forced extraction not executed"
        return artifact

    if not binary_path.exists():
        artifact.error = f"Binary not found: {binary_path}"
        artifact.summary = "IDA forced extraction not executed"
        return artifact

    # Use idat64 for batch mode (headless) if available
    idat_executable = ida_executable.replace("ida64.exe", "idat64.exe").replace("ida.exe", "idat.exe")
    if not Path(idat_executable).exists():
        idat_executable = ida_executable

    log_path = output_path.with_suffix(".log")
    db_path = output_path.with_suffix(".i64")
    for suffix in (".i64", ".id0", ".id1", ".nam", ".til"):
        sidecar = db_path.with_suffix(suffix)
        try:
            sidecar.unlink(missing_ok=True)
        except OSError:
            pass

    command_args = [
        idat_executable,
        "-A",
        f"-L{log_path}",
        f"-o{db_path}",
        f"-S{script_path}",
        str(binary_path),
    ]
    artifact.command = " ".join(shlex.quote(a) for a in command_args)
    artifact.output_path = str(output_path)
    artifact.attempted = True

    env = dict(os.environ)
    env["REVERSE_AGENT_IDA_OUT"] = str(output_path)
    env["REVERSE_AGENT_FORCED_FUNCTIONS"] = ",".join(function_names)

    try:
        proc = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired:
        artifact.error = f"IDA forced extraction timeout (>{timeout_seconds}s)"
        artifact.summary = "IDA forced extraction timed out"
        return artifact
    except Exception as exc:
        artifact.error = f"IDA forced extraction failed: {exc}"
        artifact.summary = "IDA forced extraction error"
        return artifact

    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "").strip()
        if not details and log_path.exists():
            details = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
        artifact.error = details[:2000] if details else "IDA forced extraction failed"
        artifact.summary = f"IDA forced extraction failed (exit code {proc.returncode})"
        return artifact

    if not output_path.exists():
        artifact.error = "IDA forced extraction completed but no output file"
        artifact.summary = "IDA forced extraction output missing"
        return artifact

    # Parse output
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        artifact.error = f"Failed to parse forced extraction output: {exc}"
        artifact.summary = "IDA forced extraction output unparseable"
        return artifact

    extracted_count = data.get("extracted_count", 0)
    function_count = data.get("function_count", 0)
    hexrays_available = data.get("hexrays_available", False)

    artifact.success = True
    artifact.summary = (
        f"IDA forced extraction: {extracted_count}/{function_count} functions "
        f"decompiled (Hex-Rays={'yes' if hexrays_available else 'no'})"
    )

    # Add evidence
    for func in data.get("functions", []):
        if isinstance(func, dict):
            name = func.get("function_name", "")
            resolved = func.get("resolved", False)
            pseudocode = func.get("pseudocode", "")
            pseudocode_preview = pseudocode[:200] if pseudocode else ""
            artifact.evidence.append(
                f"ForcedExtract:{name} resolved={resolved} "
                f"pseudocode_len={len(pseudocode)}"
            )
            if pseudocode_preview:
                artifact.evidence.append(
                    f"ForcedExtract:{name}_preview: {pseudocode_preview}"
                )

    return artifact


def run_forced_extraction(
    artifact_index_path: Path,
    handoff_path: Path,
    out_path: Path,
    policy_path: Path | None = None,
    ida_timeout_seconds: int = 180,
) -> dict[str, Any]:
    """Main extraction logic for unresolved targets."""
    artifact_index = _load_json(artifact_index_path)
    handoff = _load_json(handoff_path)

    # Load policy for root path
    root_path = Path("E:\\reverse")
    if policy_path and policy_path.exists():
        policy = _load_json(policy_path)
        policy_root = policy.get("root", "")
        if policy_root:
            root_path = Path(policy_root)

    # Validate handoff
    validated = handoff.get("validated_candidates", [])
    hookapi_ok = any(
        c.get("candidate") == "hookapi" and c.get("validation_status") == "validated"
        for c in validated
    )
    if not hookapi_ok:
        print("ERROR: handoff does not contain validated hookapi candidate", file=sys.stderr)
        sys.exit(1)

    # Get unresolved targets
    unresolved = handoff.get("unresolved_targets", [])
    expected_ids = {"18019fca52b389fe", "4c69f173f2bd0211"}
    actual_ids = {t["sample_id"] for t in unresolved}
    if not actual_ids.issubset(expected_ids):
        print(f"ERROR: unexpected targets {actual_ids - expected_ids}", file=sys.stderr)
        sys.exit(1)

    # Get evidence paths from artifact_index
    v2 = artifact_index.get("latest_artifacts_v2", {})
    targets: list[dict[str, Any]] = []

    script_path = Path(__file__).parent / "ida_scripts" / "forced_function_extract.py"

    for target in unresolved:
        sid = target["sample_id"]
        rel_path = target.get("relative_path", "")

        # Find binary path from root + relative_path
        binary_path = root_path / rel_path if rel_path else None
        if binary_path is None or not binary_path.exists():
            # Fallback: try to find from evidence directory
            evidence_key = f"local_reverse_ida_evidence_{sid}"
            evidence_meta = v2.get(evidence_key, {})
            evidence_path = evidence_meta.get("path", "")
            if evidence_path:
                evidence_dir = Path(evidence_path).parent
                binary_candidates = list(evidence_dir.glob("*.exe"))
                if binary_candidates:
                    binary_path = binary_candidates[0]

        if binary_path is None or not binary_path.exists():
            targets.append({
                "sample_id": sid,
                "relative_path": rel_path,
                "previous_blocker": target.get("blocked_reason", ""),
                "extraction_status": "blocked",
                "forced_ida_ran": False,
                "sub_401005_pseudocode": "",
                "sub_401005_disassembly": [],
                "sub_401005_constants": [],
                "sub_401005_callgraph": [],
                "sub_401005_string_refs": [],
                "transform_inferred": "",
                "blocker_resolved": False,
                "next_action": f"binary not found for {sid} (tried {root_path / rel_path if rel_path else 'N/A'})",
            })
            continue

        # Output path in evidence directory
        evidence_key = f"local_reverse_ida_evidence_{sid}"
        evidence_meta = v2.get(evidence_key, {})
        evidence_path_str = evidence_meta.get("path", "")
        if evidence_path_str:
            output_dir = Path(evidence_path_str).parent
        else:
            output_dir = Path("project_state")
        output_path = output_dir / f"{binary_path.stem}_forced_extract.json"

        # Run forced IDA extraction for sub_401005 first
        artifact = _run_forced_ida_extraction(
            binary_path=binary_path,
            script_path=script_path,
            output_path=output_path,
            function_names=["sub_401005"],
            timeout_seconds=ida_timeout_seconds,
        )

        if not artifact.success:
            targets.append({
                "sample_id": sid,
                "relative_path": rel_path,
                "previous_blocker": target.get("blocked_reason", ""),
                "extraction_status": "blocked",
                "forced_ida_ran": True,
                "forced_ida_error": artifact.error,
                "sub_401005_pseudocode": "",
                "sub_401005_disassembly": [],
                "sub_401005_constants": [],
                "sub_401005_callgraph": [],
                "sub_401005_string_refs": [],
                "transform_inferred": "",
                "blocker_resolved": False,
                "next_action": f"IDA forced extraction failed: {artifact.error}",
            })
            continue

        # Parse extraction result
        try:
            extraction_data = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            targets.append({
                "sample_id": sid,
                "relative_path": rel_path,
                "previous_blocker": target.get("blocked_reason", ""),
                "extraction_status": "blocked",
                "forced_ida_ran": True,
                "sub_401005_pseudocode": "",
                "sub_401005_disassembly": [],
                "sub_401005_constants": [],
                "sub_401005_callgraph": [],
                "sub_401005_string_refs": [],
                "transform_inferred": "",
                "blocker_resolved": False,
                "next_action": "failed to parse forced extraction output",
            })
            continue

        functions = extraction_data.get("functions", [])
        sub_401005_data = next(
            (f for f in functions if f.get("function_name") == "sub_401005"), {}
        )

        pseudocode = sub_401005_data.get("pseudocode", "")
        disassembly = sub_401005_data.get("disassembly", [])
        constants = sub_401005_data.get("constants", [])
        callgraph = sub_401005_data.get("callgraph", [])
        string_refs = sub_401005_data.get("string_refs", [])

        # Check if sub_401005 is a thunk (jmp to another function)
        thunk_target = ""
        if disassembly and len(disassembly) == 1 and "jmp" in disassembly[0].lower():
            # Extract callee from callgraph
            if callgraph:
                thunk_target = callgraph[0].get("callee_name", "")

        # If thunk, also extract the real function
        real_pseudocode = pseudocode
        real_disassembly = disassembly
        real_constants = constants
        real_callgraph = callgraph
        real_string_refs = string_refs

        if thunk_target:
            # Run second extraction for the thunk target
            thunk_output_path = output_path.with_suffix(".thunk.json")
            thunk_artifact = _run_forced_ida_extraction(
                binary_path=binary_path,
                script_path=script_path,
                output_path=thunk_output_path,
                function_names=[thunk_target],
                timeout_seconds=ida_timeout_seconds,
            )
            if thunk_artifact.success:
                try:
                    thunk_data = json.loads(thunk_output_path.read_text(encoding="utf-8"))
                    thunk_functions = thunk_data.get("functions", [])
                    real_func_data = next(
                        (f for f in thunk_functions if f.get("function_name") == thunk_target), {}
                    )
                    if real_func_data.get("pseudocode"):
                        real_pseudocode = real_func_data["pseudocode"]
                        real_disassembly = real_func_data.get("disassembly", [])
                        real_constants = real_func_data.get("constants", [])
                        real_callgraph = real_func_data.get("callgraph", [])
                        real_string_refs = real_func_data.get("string_refs", [])
                except Exception:
                    pass

        # Infer transform from real pseudocode
        transform_inferred = ""
        if real_pseudocode:
            lower = real_pseudocode.lower()
            # Check for SHA-256 signature: 8x %08x format = 8 words = 256 bits
            has_8x_hex = "%08x%08x%08x%08x%08x%08x%08x%08x" in lower.replace(" ", "")
            has_64_byte_loop = "v6 >> 6" in real_pseudocode or "i < v6 >> 6" in real_pseudocode
            if has_8x_hex or (has_64_byte_loop and "sprintf" in lower):
                transform_inferred = "SHA-256 hash + hex encoding"
            elif "sha256" in lower or "sha-256" in lower:
                transform_inferred = "SHA-256 hash + hex encoding"
            elif "sha" in lower:
                transform_inferred = "SHA-family hash + hex encoding"
            elif "md5" in lower:
                transform_inferred = "MD5 hash + hex encoding"
            elif "crypt" in lower or "hash" in lower:
                transform_inferred = "cryptographic hash + hex encoding"
            elif any(kw in lower for kw in ("xor", "add", "sub", "shift", "rotate")):
                transform_inferred = "reversible bitwise/arithmetic transform"
            else:
                transform_inferred = "unknown transform (needs manual analysis)"
        else:
            transform_inferred = "pseudocode not available (Hex-Rays may have failed)"

        # Determine blocker resolution
        blocker_resolved = bool(real_pseudocode) and "thunk" not in real_pseudocode.lower()
        extraction_status = "recovered" if blocker_resolved else "partial"

        targets.append({
            "sample_id": sid,
            "relative_path": rel_path,
            "previous_blocker": target.get("blocked_reason", ""),
            "extraction_status": extraction_status,
            "forced_ida_ran": True,
            "forced_ida_success": artifact.success,
            "forced_ida_summary": artifact.summary,
            "sub_401005_is_thunk": bool(thunk_target),
            "sub_401005_thunk_target": thunk_target,
            "sub_401005_pseudocode": pseudocode,
            "sub_401005_disassembly": disassembly,
            "sub_401005_constants": constants,
            "sub_401005_callgraph": callgraph,
            "sub_401005_string_refs": string_refs,
            "real_transform_pseudocode": real_pseudocode,
            "real_transform_disassembly": real_disassembly,
            "real_transform_constants": real_constants,
            "real_transform_callgraph": real_callgraph,
            "real_transform_string_refs": real_string_refs,
            "transform_inferred": transform_inferred,
            "blocker_resolved": blocker_resolved,
            "next_action": (
                f"sub_401005 is thunk to {thunk_target}; real transform recovered; "
                f"proceed to constraint recovery"
                if thunk_target and blocker_resolved
                else "sub_401005 transform recovered; proceed to constraint recovery"
                if blocker_resolved
                else "sub_401005 is thunk but real transform unclear; "
                     "needs manual analysis or alternative approach"
                if thunk_target
                else "sub_401005 pseudocode missing or transform unclear; "
                     "needs manual analysis or alternative approach"
            ),
        })

    result: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stage": "local_reverse_forced_ida_extraction_v1",
        "status": "PARTIAL" if any(not t["blocker_resolved"] for t in targets) else "SUCCESS",
        "target_count": len(targets),
        "source_handoff": str(handoff_path),
        "targets": targets,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    print(
        f"forced IDA extraction: status={result['status']} "
        f"targets={result['target_count']}"
    )
    for t in targets:
        print(
            f"  {t['sample_id']}: extraction_status={t['extraction_status']} "
            f"forced_ida_ran={t.get('forced_ida_ran', False)} "
            f"blocker_resolved={t['blocker_resolved']}"
        )

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Forced IDA decompilation for unresolved local reverse samples.",
    )
    parser.add_argument(
        "--artifact-index",
        type=Path,
        default=Path("project_state/artifact_index.json"),
        help="Path to artifact_index.json",
    )
    parser.add_argument(
        "--handoff",
        type=Path,
        default=Path("project_state/local_reverse_validated_candidate_handoff.json"),
        help="Path to validated candidate handoff JSON",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("project_state/local_reverse_forced_ida_extraction_result.json"),
        help="Output path for forced extraction result JSON",
    )
    parser.add_argument(
        "--ida-timeout",
        type=int,
        default=180,
        help="IDA execution timeout in seconds (default: 180)",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("project_state/local_reverse_runtime_policy.json"),
        help="Path to runtime policy JSON for root directory",
    )
    args = parser.parse_args()
    run_forced_extraction(
        artifact_index_path=args.artifact_index,
        handoff_path=args.handoff,
        out_path=args.out,
        policy_path=args.policy,
        ida_timeout_seconds=args.ida_timeout,
    )


if __name__ == "__main__":
    main()
