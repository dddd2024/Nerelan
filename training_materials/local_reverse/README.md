# Local Reverse Training Materials

This directory contains **metadata-only** training material indexes for the local reverse engineering sample collection.

## Policy

- **Original sample binaries are NOT stored in this repository.**
- The actual samples live on the local machine under `E:\reverse` (or another path pointed to by the `LOCAL_REVERSE_ROOT` environment variable).
- Only **metadata** (hashes, relative paths, categories, tags, etc.) is committed to GitHub.
- If you need to run analysis on a sample, resolve the real file locally via `LOCAL_REVERSE_ROOT`.

## Filtering Rules

The inventory scanner applies the following filters to avoid polluting the training dataset with IDE configs, build artifacts, and cache files:

### Excluded Directories

The scanner skips any file located under these directories:

- `.idea`, `.vscode`, `.git`
- `__pycache__`, `.pytest_cache`
- `.venv`, `venv`, `env`
- `node_modules`

### Excluded Extensions

The following extensions are excluded by default:

- IDE / project: `.iml`, `.xml`
- Cache / temp: `.tmp`, `.cache`, `.pyc`, `.pyo`, `.pyd`, `.class`
- Build artifacts: `.o`, `.obj`, `.ilk`, `.pdb`, `.idb`, `.tlog`, `.manifest`, `.res`, `.rc`
- Logs: `.log`

### Included Extensions

Only files with the following extensions are registered as potential samples/attachments:

- Executables / libraries: `.exe`, `.dll`, `.sys`, `.com`, `.ocx`, `.drv`, `.vxd`, `.386`
- Raw / data: `.bin`, `.dat`, `.elf`, `.so`
- Archives: `.zip`, `.7z`, `.rar`, `.tar`, `.gz`, `.bz2`, `.xz`, `.jar`, `.apk`
- Documents / text: `.txt`, `.md`, `.json`, `.pdf`, `.doc`, `.docx`, `.csv`, `.xls`, `.xlsx`
- Source code: `.py`, `.c`, `.cpp`, `.h`, `.hpp`, `.cs`, `.vb`, `.java`, `.js`, `.html`, `.php`, `.asp`, `.sql`
- Media / other: `.bmp`, `.jpg`, `.png`, `.gif`, `.ico`, `.wav`, `.mp3`, `.mp4`, `.ttf`, `.cur`, `.lnk`, `.reg`, `.ini`, `.yaml`, `.toml`

Files without an extension are also included (they may be raw binaries or Unix executables).

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

## Case `input_value` Format

Each case file uses the placeholder format:

```json
{
  "cases": [
    {
      "case_id": "...",
      "input_value": "${LOCAL_REVERSE_ROOT}/relative/path/to/sample.exe",
      ...
    }
  ]
}
```

When loading cases for local harness runs, replace `${LOCAL_REVERSE_ROOT}` with the actual path (or set the environment variable and let the harness resolve it).
