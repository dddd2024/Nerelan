# Transform Material Provenance Report

## Sample: affine_8cfebe03

**Round:** round_20260619_affine_static_material_artifact_enrichment_v1
**Generated:** 2026-06-19T09:30:00Z

## 1. Summary

The transform material gap for `affine_8cfebe03` has been **resolved**. The targeted IDA decompile of `_main_0` revealed a complete affine cipher implementation with concrete constants.

## 2. Transform Material

- **Cipher type:** affine_cipher
- **Formula:** `c = (a * p + b) mod m`
- **Parameters:**
  - `a = 5` (multiplicative key, variable `v11`)
  - `b = 5` (additive key, variable `v10`)
  - `modulus = 26`
- **Modular inverse:** `a_inverse = 21` (since `5 * 21 = 105 = 1 mod 26`)
- **Inverse formula:** `p = 21 * (c - 5) mod 26`
- **Input domain:** lowercase ASCII 'a'-'z' (97-122), enforced with hard exit
- **Normalization:** `p = input_char - 97` (maps 'a'-'z' to 0..25)
- **Denormalization:** `output_char = c + 97` (maps 0..25 back to 'a'-'z')

## 3. Program Type

This is a **pure affine cipher encoder**. The program:
1. Reads input string via `scanf("%s", Str)`
2. Validates all characters are in 'a'-'z' range (returns -1 if not)
3. Applies affine cipher transform in-place: `Str[j] = (5 + 5 * (Str[j] - 97)) % 26 + 97`
4. Prints transformed string via `printf("%s", Str)`
5. Calls `system("pause")`

No compare site or password validation branch exists in `_main_0`.

## 4. Evidence Gap Resolution

- **Previous gap:** `transform_constant_evidence` (listed as missing in current dispatch plan)
- **Resolution:** resolved
- **Reason:** Targeted IDA decompile of `_main_0` revealed affine cipher constants `a=5`, `b=5`, `modulus=26`
- **Confidence:** high

## 5. Source Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Transform material static extract | `project_state/local_reverse_affine_8cfebe03_transform_material_static_extract.json` | success |
| Transform material evidence | `project_state/local_reverse_affine_8cfebe03_transform_material_evidence.json` | success |
| Transform material dispatch plan | `project_state/local_reverse_affine_8cfebe03_transform_material_dispatch_plan.json` | success |
| Source targeted decompile | `project_state/local_reverse_affine_main0_targeted_ida_decompile.json` | success |

## 6. Provenance Notes

- Source artifact: `local_reverse_affine_8cfebe03_transform_material_static_extract`
- Source targeted decompile: `local_reverse_affine_main0_targeted_ida_decompile`
- Transform constant evidence resolved via targeted IDA decompile of `_main_0`
- Runtime validated: false (static-only artifact)
- No external analysis tools or local binaries were run in this round

## 7. Next Recommended Mainline

`reverse_solving` — Transform material is resolved. The next step is to obtain the expected ciphertext output (from problem statement or external source) and compute the inverse affine transform to recover the plaintext.
