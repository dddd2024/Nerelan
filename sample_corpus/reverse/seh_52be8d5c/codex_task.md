# Curated Corpus Sample Task: seh_52be8d5c

## Sample

- case_id: `seh_52be8d5c`
- sample path: `sample_corpus/reverse/seh_52be8d5c/sample.exe`
- sha256: `52be8d5c485f7c7c3340d42791505b9f55cf4ff63191768c0cc62f30cde4ae07`
- size_bytes: `196685`
- case.json: `sample_corpus/reverse/seh_52be8d5c/case.json`

## Harness

```powershell
python -m reverse_agent.harness --dataset sample_corpus\reverse\seh_52be8d5c\case.json --run-name corpus_seh_52be8d5c_static --analysis-mode "Static Analysis" --case-id seh_52be8d5c
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
      "case_id": "seh_52be8d5c",
      "input_value": "sample_corpus/reverse/seh_52be8d5c/sample.exe",
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
