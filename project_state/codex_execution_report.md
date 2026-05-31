```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260531_rename_local_samples_to_uploadable_corpus",
  "round_id": "round_20260531_rename_local_samples_to_uploadable_corpus",
  "based_on_decision_id": "decision_20260531_rename_local_samples_to_uploadable_corpus",
  "based_on_state_build_id": "state_20260527_153028_1d6dd81ecbd6",
  "based_on_state_digest": "1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "sample_corpus/reverse/manifest.json",
    "sample_corpus/reverse/README.md",
    "sample_corpus/reverse/cpp_6af7c7f1/metadata.json",
    "sample_corpus/reverse/desenc_40cba418/metadata.json",
    "sample_corpus/reverse/rc4enc_3480917d/metadata.json",
    "sample_corpus/reverse/seh_52be8d5c/metadata.json",
    "tests/test_sample_corpus.py",
    "README.txt"
  ],
  "tests_ran": [
    "python -m pytest tests/test_sample_corpus.py -v",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "sample_corpus/reverse/manifest.json",
    "sample_corpus/reverse/README.md",
    "tests/test_sample_corpus.py"
  ]
}
```

# Codex Execution Report

**Report ID:** report_20260531_rename_local_samples_to_uploadable_corpus
**Decision ID:** decision_20260531_rename_local_samples_to_uploadable_corpus
**Round ID:** round_20260531_rename_local_samples_to_uploadable_corpus
**Status:** SUCCESS
**Date:** 2026-05-31

---

## 1. Directory Rename/Move

### 1.1 Source Directory

- **Original path:** `local_reverse_samples/`
- **Original status:** Ignored by Git (`.gitignore` line 8)
- **Contents:** 4 case directories + 4 loose .exe files

### 1.2 Destination Directory

- **New path:** `sample_corpus/reverse/`
- **New status:** Tracked by Git (not in `.gitignore`)
- **Move method:** `robocopy /E /MOVE` (atomic rename, no duplicate copies)

### 1.3 Move Result

- ✅ `local_reverse_samples/` emptied and removed
- ✅ `sample_corpus/reverse/` created with all contents
- ✅ Only one copy exists (no duplicate)

---

## 2. Root Directory Normalization

### 2.1 Discovered Loose .exe Files

| File | SHA256 | Status |
|------|--------|--------|
| cpp.exe | 6af7c7f1... | duplicate of cpp_6af7c7f1/sample.exe |
| SEH.exe | 52be8d5c... | duplicate of seh_52be8d5c/sample.exe |
| desenc.exe | 40cba418... | duplicate of desenc_40cba418/sample.exe |
| rc4enc.exe | 3480917d... | duplicate of rc4enc_3480917d/sample.exe |

### 2.2 Normalization Action

All 4 loose .exe files were **removed** (they were duplicates of existing case samples).

### 2.3 Final Directory Structure

```
sample_corpus/reverse/
├── manifest.json
├── README.md
├── cpp_6af7c7f1/
│   ├── sample.exe
│   ├── metadata.json
│   ├── case.json
│   ├── notes.md
│   ├── codex_task.md
│   ├── analysis_notes.md
│   ├── solver.py
│   └── solve_result.json
├── desenc_40cba418/
│   ├── sample.exe
│   ├── metadata.json
│   ├── case.json
│   ├── notes.md
│   ├── codex_task.md
│   ├── analysis_notes.md
│   ├── solver.py
│   └── solve_result.json
├── rc4enc_3480917d/
│   ├── sample.exe
│   ├── metadata.json
│   ├── case.json
│   ├── notes.md
│   ├── codex_task.md
│   ├── analysis_notes.md
│   ├── solver.py
│   └── solve_result.json
└── seh_52be8d5c/
    ├── sample.exe
    ├── metadata.json
    ├── case.json
    ├── notes.md
    ├── codex_task.md
    ├── analysis_notes.md
    └── solve_result.json
```

---

## 3. Metadata Updates

### 3.1 Updated Fields

All 4 `metadata.json` files updated with:

| Field | Old Value | New Value |
|-------|-----------|-----------|
| `sample_path` | `local_reverse_samples/...` | `sample_corpus/reverse/...` |
| `upload_allowed` | (not set) | `true` |
| `safe_to_run` | (not set) | `false` |
| `source` | (various) | `renamed_from_local_reverse_samples` |

### 3.2 Metadata Validation

- ✅ All 4 metadata files have required fields
- ✅ All have `upload_allowed=true`
- ✅ All have `safe_to_run=false`
- ✅ All use relative paths without absolute Windows paths

---

## 4. Generated Artifacts

### 4.1 manifest.json

- **Location:** `sample_corpus/reverse/manifest.json`
- **Content:** Catalog of all 4 samples with case_id, path, sha256, size, category, safe_to_run, upload_allowed
- **Validation:** Matches actual case directories and metadata sha256 values

### 4.2 README.md

- **Location:** `sample_corpus/reverse/README.md`
- **Content:**
  - Corpus overview and purpose
  - Directory structure documentation
  - Required files per sample
  - Sample list with descriptions
  - Safety notice (safe_to_run=false)
  - Contributing guidelines

### 4.3 tests/test_sample_corpus.py

- **Location:** `tests/test_sample_corpus.py`
- **Purpose:** Validate corpus structure and metadata
- **Test Classes:**
  - `TestCorpusStructure` - Directory, manifest, README existence
  - `TestSampleStructure` - Required files per case, no loose .exe
  - `TestMetadata` - Required fields, upload_allowed, safe_to_run, path format
  - `TestManifestConsistency` - Manifest matches actual samples and metadata

---

## 5. Test Results

### 5.1 pytest test_sample_corpus.py

```
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.0.3, pluggy-1.6.0
collected 15 items

tests/test_sample_corpus.py::TestCorpusStructure::test_corpus_directory_exists PASSED
tests/test_sample_corpus.py::TestCorpusStructure::test_manifest_exists PASSED
tests/test_sample_corpus.py::TestCorpusStructure::test_readme_exists PASSED
tests/test_sample_corpus.py::TestSampleStructure::test_no_root_exe_files PASSED
tests/test_sample_corpus.py::TestSampleStructure::test_each_case_has_required_files[sample.exe] PASSED
tests/test_sample_corpus.py::TestSampleStructure::test_each_case_has_required_files[metadata.json] PASSED
tests/test_sample_corpus.py::TestSampleStructure::test_each_case_has_required_files[case.json] PASSED
tests/test_sample_corpus.py::TestSampleStructure::test_each_case_has_required_files[notes.md] PASSED
tests/test_sample_corpus.py::TestSampleStructure::test_each_case_has_required_files[codex_task.md] PASSED
tests/test_sample_corpus.py::TestMetadata::test_metadata_has_required_fields PASSED
tests/test_sample_corpus.py::TestMetadata::test_upload_allowed_is_true PASSED
tests/test_sample_corpus.py::TestMetadata::test_safe_to_run_is_false PASSED
tests/test_sample_corpus.py::TestMetadata::test_sample_path_format PASSED
tests/test_sample_corpus.py::TestManifestConsistency::test_manifest_matches_actual_samples PASSED
tests/test_sample_corpus.py::TestManifestConsistency::test_manifest_sha256_matches_metadata PASSED

============================= 15 passed in 0.05s =============================
```

### 5.2 lint-decision

```
lint-decision: OK
decision_id: decision_20260531_rename_local_samples_to_uploadable_corpus
decision_status: APPROVED
```

### 5.3 git diff --check

```
passed (only CRLF line-ending warnings)
```

---

## 6. Compliance Verification

### 6.1 Required Audit Checklist

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | local_reverse_samples/ 是否已改名/移动 | done | renamed to sample_corpus/reverse/ |
| 2 | 是否没有保留两份副本 | done | robocopy /MOVE used, source directory removed |
| 3 | 根目录下裸 .exe 是否已处理 | done | 4 duplicates removed |
| 4 | 每个样本是否都有独立 case 目录 | done | 4 case directories verified |
| 5 | 每个 case 是否有 metadata.json | done | all 4 have metadata.json |
| 6 | 每个 metadata 是否有 upload_allowed=true | done | all 4 have upload_allowed=true |
| 7 | 每个 metadata 是否有 safe_to_run=false | done | all 4 have safe_to_run=false |
| 8 | 是否生成了 manifest.json | done | sample_corpus/reverse/manifest.json |
| 9 | 是否生成了 README.md | done | sample_corpus/reverse/README.md |
| 10 | 是否新增了 corpus 结构测试 | done | tests/test_sample_corpus.py |
| 11 | 所有测试是否通过 | done | 15 passed |
| 12 | .gitignore 是否正确 | done | local_reverse_samples/ ignored, sample_corpus/ not ignored |
| 13 | 是否没有执行任何 sample.exe | done | no execution |
| 14 | 是否没有修改 .codex-skills/ | done | no changes |
| 15 | 是否没有修改 samplereverse 主线 | done | no changes |

---

## 7. Summary

| # | Requirement | Status |
|---|-------------|--------|
| 1 | 改名/移动原目录，不保留两份副本 | done |
| 2 | 规范化内部结构（独立 case 目录） | done |
| 3 | 补齐 metadata（upload_allowed, safe_to_run） | done |
| 4 | 生成 manifest.json | done |
| 5 | 生成 README.md | done |
| 6 | 新增 corpus 结构测试 | done |
| 7 | 所有测试通过 | done (15 passed) |
| 8 | 未执行任何 sample.exe | done |
| 9 | 未修改 .codex-skills/ | done |
| 10 | 未修改 samplereverse 主线 | done |

---

*Report generated by Codex Execution Agent*
*Following decision_packet: decision_20260531_rename_local_samples_to_uploadable_corpus*
