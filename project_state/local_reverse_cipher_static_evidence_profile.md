# Cipher Static Evidence Profile

**Decision**: `decision_20260617_training_dataset_cipher_static_evidence_profile_v1`
**Round**: `round_20260617_training_dataset_cipher_static_evidence_profile_v1`
**Mainline**: `training_dataset`
**Generated**: 2026-06-17

## Scope

PE cipher samples only — DES and RC4 families. This profile defines the evidence contract that future static-triage rounds must satisfy before any cipher sample can move from `inventory_only` to active triage.

## Target Samples

### DES Family (4 PE samples)

| Sample ID | Status | First Triage Target |
|-----------|--------|-------------------|
| desenc_0e0b5203 | inventory_only | **Yes** |
| desenc_14c58fcd | inventory_only | No |
| desenc_40cba418 | inventory_only | No |
| desenc_fd9d0af6 | inventory_only | No |

### RC4 Family (2 PE samples)

| Sample ID | Status | First Triage Target |
|-----------|--------|-------------------|
| rc4enc_3480917d | inventory_only | **Yes** |
| rc4enc_f93c785f | inventory_only | No |

### Reference Material (Python)

| Sample ID | Family | Role |
|-----------|--------|------|
| des_interactive_solver_256e1726 | DES | Reference solver implementation |
| rc4_add1978d | RC4 | Reference implementation |
| rc4_interactive_solver_773052ac | RC4 | Reference solver implementation |

## Evidence Contract

### 1. Algorithm Marker Evidence

**Purpose**: Identify the cipher algorithm from static artifacts.

**DES Markers**:
- DES initial permutation table (IP table, 64 bytes)
- DES S-box tables (8 S-boxes, 64 entries each)
- DES permutation tables (P-box, expansion E, PC-1, PC-2)
- DES Feistel round structure (16 rounds)
- Constant: 0x0E329B23 or equivalent S1 checksum

**RC4 Markers**:
- RC4 KSA: swap loop with 256-iteration initialization
- RC4 S-box: identity permutation 0x00..0xFF
- RC4 PRGA: two-index swap-and-output loop
- Constant: 256 (S-box size) in loop bound
- Pattern: XOR with S-box indexed value in tight loop

**Extraction**: IDA constant array search; `strings` command; import table analysis.

**Confidence**: HIGH (2+ markers), MEDIUM (1 marker), LOW (no markers).

### 2. String Evidence

**Fields**: algorithm name, mode (ECB/CBC/CFB/OFB), padding (PKCS5/PKCS7), key derivation strings, error diagnostics.

**Extraction**: Existing `static_feature_extractor.py`; IDA strings window; `strings` command.

### 3. Constant Table Evidence

**DES Tables**: IP (64B), FP (64B), E (48B), P (32B), S1-S8 (512B total), PC1 (56B), PC2 (48B), shift schedule (16 entries).

**RC4 Tables**: S-box (256-byte permutation, identity at KSA start). No other fixed constants.

**Extraction**: IDA constant array identification in .rdata; cross-reference with Feistel round function.

### 4. Import API Evidence

**APIs to Check**: CryptAcquireContext, CryptCreateHash, CryptDeriveKey, CryptEncrypt, CryptDecrypt, CryptDestroyKey, CryptReleaseContext, BCryptGenerateSymmetricKey, BCryptEncrypt, BCryptDecrypt.

**Algorithm Hints**: CALG_DES → DES; CALG_RC4 → RC4; BCRYPT_DES_ALGORITHM → DES; BCRYPT_RC4_ALGORITHM → RC4.

### 5. Input Source Evidence

**Fields**: input buffer address, input read function, input length field, input encoding.

**Extraction**: IDA data flow tracing from input API to cipher function entry.

### 6. Key Source Evidence

**DES**: 8-byte key (56 effective bits); may be derived from password; Triple-DES uses 16/24 byte keys.

**RC4**: Variable-length key (1-256 bytes); fed directly into KSA.

**Fields**: key buffer address, key derivation function, key length, hardcoded key indicator.

### 7. IV / Mode / Padding Evidence

**DES**: Modes ECB/CBC/CFB/OFB; IV required for CBC/CFB/OFB (8 bytes); padding PKCS5/PKCS7 or zero.

**RC4**: Stream cipher — no block mode, no IV, no padding.

### 8. Ciphertext Source Evidence

**Fields**: ciphertext buffer address, write function, length, encoding (raw/Base64/hex).

### 9. Comparison Output Sink Evidence

**Fields**: comparison function address, comparison type (memcmp/string/byte-by-byte), expected ciphertext location, branch direction.

### 10. Candidate Input Domain Evidence

**DES**: 2^56 key space (infeasible without constraints); feasibility depends on key source.

**RC4**: Key space depends on key length; keystream recovery possible with known plaintext.

## Validation Preconditions

Before attempting sample solution:

1. Algorithm marker confidence >= MEDIUM
2. Key source identified (hardcoded, password-derived, or confirmed unknown)
3. Comparison output sink located
4. Candidate input domain bounded or confirmed unbounded

**Blocker conditions**:
- LOW algorithm confidence → cannot confirm cipher
- Unknown key source with no hardcoded key → key recovery may be infeasible
- Missing comparison sink → cannot determine success criteria

## Structured Evidence Mapping Plan

| Step | Tool | Output | Target |
|------|------|--------|--------|
| 1 | IDA static triage | Algorithm markers, constant tables, function boundaries | StructuredEvidence.algorithm_identification |
| 2 | static_feature_extractor.py | String indicators, import table, section layout | StructuredEvidence.string_indicators + api_imports |
| 3 | IDA data flow analysis | Input, key, IV, ciphertext, comparison points | StructuredEvidence.data_flow_contract |
| 4 | Derived analysis | Domain bounds, validation preconditions | StructuredEvidence.solution_feasibility |

## Future Static Triage Sequence

1. **desenc_0e0b5203** — First DES target. Confirm DES algorithm, locate S-box tables, identify key source.
2. **rc4enc_3480917d** — First RC4 target. Confirm RC4 algorithm, locate KSA loop, identify key source.
3. Data flow analysis on confirmed samples — locate input, key, ciphertext, comparison points.
4. Candidate domain analysis — determine bounded solution feasibility.
5. Apply patterns to remaining DES/RC4 samples.

## Non-Goals

- No samples solved in this round
- No IDA/Ghidra/debugger/emulator execution
- No source/test code modification
- No solver/harness/sample binary modification
- No new IDA/Ghidra interface implementation
- No existing training status artifact overwrites
