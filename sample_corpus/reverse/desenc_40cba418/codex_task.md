# Curated Corpus Sample Task: desenc_40cba418

## Sample

- case_id: `desenc_40cba418`
- sample path: `sample_corpus/reverse/desenc_40cba418/sample.exe`
- sha256: `40cba4189a9639da601b9d9b74fd9937c3d03fc93c90f5df12840e8b7763700f`
- size_bytes: `200784`
- case.json: `sample_corpus/reverse/desenc_40cba418/case.json`

## Harness

```powershell
python -m reverse_agent.harness --dataset sample_corpus\reverse\desenc_40cba418\case.json --run-name corpus_desenc_40cba418_static --analysis-mode "Static Analysis" --case-id desenc_40cba418
```

## First Pass

1. Inspect printable strings, imports, constants, compare points, hash clues, and encoding indicators.
2. Keep the first pass static and auditable.
3. This case now belongs to sample_corpus/reverse/ as a curated, upload-approved corpus case.
4. local_reverse_samples/ is only for future temporary intake and must not contain a duplicate copy of this case.
5. Keep analysis static-first. Do not execute sample.exe by default.
6. Do not run IDA / OllyDbg / Frida / runtime probes unless a future decision explicitly authorizes it.

## Case Payload

```json
{
  "cases": [
    {
      "case_id": "desenc_40cba418",
      "input_value": "sample_corpus/reverse/desenc_40cba418/sample.exe",
      "expected_flag": "",
      "category": "unknown",
      "tags": [
        "reverse",
        "local-sample",
        "curated"
      ],
      "notes": "Curated reverse training sample. Static analysis first. Do not execute by default."
    }
  ]
}
```
