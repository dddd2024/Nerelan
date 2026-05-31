# Reverse Engineering Sample Corpus

This directory contains a curated collection of reverse engineering training samples for static analysis practice.

## Overview

- **Purpose**: Provide reproducible, auditable reverse engineering challenges
- **Analysis Mode**: Static analysis first (strings, imports, constants, disassembly)
- **Execution Policy**: `safe_to_run=false` - Do not execute samples directly on host
- **Upload Status**: `upload_allowed=true` - Samples are explicitly allowed for upload

## Directory Structure

Each sample is organized in its own case directory:

```
sample_corpus/reverse/
  <case_id>/
    sample.exe          # The binary sample
    metadata.json       # Sample metadata (sha256, size, tags, etc.)
    case.json           # Case configuration for harness
    notes.md            # General notes about the sample
    codex_task.md       # Task description for Codex analysis
    analysis_notes.md   # (Optional) Detailed static analysis results
    solve_result.json   # (Optional) Solver results if available
```

## Required Files per Sample

Every sample must have:
- `sample.exe` - The binary file
- `metadata.json` - Must contain: sha256, size_bytes, upload_allowed=true, safe_to_run=false
- `case.json` - Case configuration with input_value pointing to sample.exe
- `notes.md` - Brief description
- `codex_task.md` - Analysis task description

## Sample List

| Case ID | SHA256 (first 8 chars) | Size | Notes |
|---------|------------------------|------|-------|
| cpp_6af7c7f1 | 6af7c7f1... | 196,690 bytes | Affine cipher lowercase transform |
| desenc_40cba418 | 40cba418... | 200,784 bytes | DES-ECB encryption challenge |
| rc4enc_3480917d | 3480917d... | 196,693 bytes | Modified RC4 encryption challenge |
| seh_52be8d5c | 52be8d5c... | 196,685 bytes | SEH exception handling obfuscation |

## Safety Notice

⚠️ **WARNING**: These samples are provided for educational static analysis only.

- `safe_to_run=false` for all samples
- Do not execute these binaries directly on your host system
- Use isolated environments (VMs, containers) if dynamic analysis is required
- Static analysis (strings, disassembly) is the recommended first approach

## Temporary Local Import Directory

The `.gitignore` still includes `local_reverse_samples/` for future temporary local sample intake. This directory should remain empty or be used only for transient imports before samples are curated and moved to `sample_corpus/reverse/`.

## Contributing

When adding new samples:
1. Ensure `upload_allowed=true` and `safe_to_run=false` in metadata.json
2. Include all required files (metadata.json, case.json, notes.md, codex_task.md)
3. Do not include local absolute paths in metadata
4. Run `pytest tests/test_sample_corpus.py` to validate corpus structure
