# Curated Corpus Sample Task: rc4enc_3480917d

## Sample

- case_id: `rc4enc_3480917d`
- sample path: `sample_corpus/reverse/rc4enc_3480917d/sample.exe`
- sha256: `3480917ddedce512f76e97c26df3b3ad12b71b34db472fa8836ba67528bcb09f`
- size_bytes: `196693`
- case.json: `sample_corpus/reverse/rc4enc_3480917d/case.json`

## Harness

```powershell
python -m reverse_agent.harness --dataset sample_corpus\reverse\rc4enc_3480917d\case.json --run-name corpus_rc4enc_3480917d_static --analysis-mode "Static Analysis" --case-id rc4enc_3480917d
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
      "case_id": "rc4enc_3480917d",
      "input_value": "sample_corpus/reverse/rc4enc_3480917d/sample.exe",
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
