# Local Reverse Training Materials

This directory contains **metadata-only** training material indexes for the local reverse engineering sample collection.

## Policy

- **Original sample binaries are NOT stored in this repository.**
- The actual samples live on the local machine under `E:\reverse` (or another path pointed to by the `LOCAL_REVERSE_ROOT` environment variable).
- Only **metadata** (hashes, relative paths, categories, tags, etc.) is committed to GitHub.
- If you need to run analysis on a sample, resolve the real file locally via `LOCAL_REVERSE_ROOT`.

## Files

| File | Purpose |
|------|---------|
| `inventory.json` | GitHub-safe metadata inventory. Contains no absolute local paths. |
| `cases/*.json` | Harness-compatible case files, one per sample. Can be loaded by `reverse_agent.harness.load_harness_cases`. |

## Generating / Updating

```powershell
python -m reverse_agent.local_reverse_inventory scan `
  --samples-root E:\reverse `
  --out project_state\local_reverse_inventory.json `
  --github-out training_materials\local_reverse\inventory.json `
  --cases-dir training_materials\local_reverse\cases
```

## Metadata Fields

Each entry in `inventory.json` contains:

- `sample_id` — stable identifier derived from filename + sha256 prefix.
- `display_name` — original filename.
- `relative_path` — path relative to `LOCAL_REVERSE_ROOT`.
- `sha256` — SHA-256 hash of the file.
- `size_bytes` — file size.
- `extension` — file extension.
- `guessed_file_type` — heuristic file type (`pe`, `raw`, `python`, etc.).
- `category` — heuristic category (`crypto/hash`, `cpp`, `encoding`, etc.).
- `tags` — list of tags for harness filtering.
- `status` — indexing status.
- `github_upload_policy` — always `metadata_only`.

## Environment Variable

```powershell
$env:LOCAL_REVERSE_ROOT = "E:\reverse"
```

The harness and inventory tools use this variable (or the default `E:\reverse`) to resolve `relative_path` to an absolute file path when running locally.
