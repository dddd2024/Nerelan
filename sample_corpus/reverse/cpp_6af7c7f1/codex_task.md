# Curated Corpus Sample Task: cpp_6af7c7f1

## Sample

- case_id: `cpp_6af7c7f1`
- sample path: `sample_corpus/reverse/cpp_6af7c7f1/sample.exe`
- sha256: `6af7c7f131eb4991b04f1dc04fd2341113da1aaa318018c14b9e9b81a37186c3`
- size_bytes: `196690`
- case.json: `sample_corpus/reverse/cpp_6af7c7f1/case.json`

## Harness

```powershell
python -m reverse_agent.harness --dataset sample_corpus\reverse\cpp_6af7c7f1\case.json --run-name corpus_cpp_6af7c7f1_static --analysis-mode "Static Analysis" --case-id cpp_6af7c7f1
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
      "case_id": "cpp_6af7c7f1",
      "input_value": "sample_corpus/reverse/cpp_6af7c7f1/sample.exe",
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
