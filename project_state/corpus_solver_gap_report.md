# Corpus Solver Gap Report

Generated: 2026-05-31T18:21:31.086638
Corpus: sample_corpus\reverse

## Execution Policy

- Static Analysis Only: True
- Samples Executed: False
- Runtime Probes Used: False

## Summary

- Total Samples: 4
- Classified: 4
- Unknown: 0

### Category Distribution

| Category | Count |
|----------|-------|
| des_like | 1 |
| rc4_like | 1 |
| seh_or_exception | 1 |
| string_compare | 1 |

## Sample Details

### cpp_6af7c7f1

- **SHA256**: `6af7c7f131eb4991...`
- **Size**: 196,690 bytes
- **Format**: pe
- **Entropy**: low

**Classification**:
- Category: `string_compare`
- Confidence: `medium`

**Evidence**:
- (medium) Found comparison keywords: ['flag']

**Recommended Next Step**: Look for strcmp/memcmp calls; expected string may be nearby in binary

**Feature Summary**:
- ASCII strings found: 20
- UTF-16LE strings found: 10
- Crypto hints: 0
- Compare hints: 8
- Interesting constants: 1

### desenc_40cba418

- **SHA256**: `40cba4189a9639da...`
- **Size**: 200,784 bytes
- **Format**: pe
- **Entropy**: low

**Classification**:
- Category: `des_like`
- Confidence: `low`

**Evidence**:
- (weak) Case ID 'desenc_40cba418' contains 'des'
- (medium) Found comparison keywords: ['flag']

**Recommended Next Step**: Static analysis: look for DES key schedule, S-boxes, or permutation tables. Key and ciphertext may be in binary. DO NOT assume key is known.

**Feature Summary**:
- ASCII strings found: 20
- UTF-16LE strings found: 10
- Crypto hints: 1
- Compare hints: 8
- Interesting constants: 0

### rc4enc_3480917d

- **SHA256**: `3480917ddedce512...`
- **Size**: 196,693 bytes
- **Format**: pe
- **Entropy**: low

**Classification**:
- Category: `rc4_like`
- Confidence: `low`

**Evidence**:
- (weak) Case ID 'rc4enc_3480917d' contains 'rc4'
- (medium) Found comparison keywords: ['flag']

**Recommended Next Step**: Static analysis: look for S-box initialization (KSA) and keystream generation (PRGA). Key may be in strings or hardcoded. DO NOT assume key is known.

**Feature Summary**:
- ASCII strings found: 20
- UTF-16LE strings found: 10
- Crypto hints: 1
- Compare hints: 9
- Interesting constants: 0

### seh_52be8d5c

- **SHA256**: `52be8d5c485f7c7c...`
- **Size**: 196,685 bytes
- **Format**: pe
- **Entropy**: low

**Classification**:
- Category: `seh_or_exception`
- Confidence: `low`

**Evidence**:
- (weak) Case ID 'seh_52be8d5c' contains 'seh'
- (medium) Found comparison keywords: ['flag']

**Recommended Next Step**: Analyze exception handler structure; control flow may be obfuscated via SEH

**Feature Summary**:
- ASCII strings found: 20
- UTF-16LE strings found: 10
- Crypto hints: 0
- Compare hints: 10
- Interesting constants: 0

## Current Capability Coverage

### Covered Capabilities

- **affine_lowercase** (0 samples): Fully covered by simple_static_patterns.py
- **caesar_or_shift** (0 samples): Fully covered by simple_static_patterns.py
- **xor_or_bytewise** (0 samples): Helper functions available in simple_static_patterns.py
- **hash_check** (0 samples): Hex digest detection available in simple_static_patterns.py

### Capability Gaps

**rc4_like** (1 samples):
- No static RC4 KSA/PRGA identification
- No automatic key extraction from binary
- No RC4 keystream analysis

**des_like** (1 samples):
- No static DES key schedule analysis
- No DES S-box or permutation table identification
- No automatic key/ciphertext extraction

**seh_or_exception** (1 samples):
- No SEH handler chain analysis
- No exception-based control flow reconstruction
- No anti-debugging detection via SEH

**string_compare** (1 samples):
- Basic detection available but no automatic string extraction

## Recommendations

### Next Steps

1. **Start with one capability at a time** - Do not attempt to implement
   DES, RC4, and SEH solvers simultaneously.

2. **Prioritize by sample availability** - Focus on categories with
   the most samples first.

3. **Maintain static-first approach** - Continue using static analysis
   before considering dynamic execution.

4. **Evidence-based implementation** - Build solvers based on actual
   patterns found in the corpus samples.

### Suggested Priority Order

1. **rc4_like** (1 samples)
2. **des_like** (1 samples)
3. **seh_or_exception** (1 samples)
4. **string_compare** (1 samples)
