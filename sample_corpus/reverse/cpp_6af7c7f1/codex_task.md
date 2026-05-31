# Local Reverse Sample Task: cpp_6af7c7f1

## Sample

- case_id: `cpp_6af7c7f1`
- sample path: `local_reverse_samples/cpp_6af7c7f1/sample.exe`
- sha256: `6af7c7f131eb4991b04f1dc04fd2341113da1aaa318018c14b9e9b81a37186c3`
- size_bytes: `196690`
- case.json: `local_reverse_samples/cpp_6af7c7f1/case.json`
- expected solver output: `local_reverse_samples/cpp_6af7c7f1/solver.py`

## Harness

```powershell
python -m reverse_agent.harness --dataset local_reverse_samples\cpp_6af7c7f1\case.json --run-name local_cpp_6af7c7f1_static --analysis-mode "Static Analysis" --case-id cpp_6af7c7f1
```

## First Pass

1. Inspect printable strings, imports, constants, compare points, hash clues, and encoding indicators.
2. Keep the first pass static and auditable.
3. Write any one-off solution code to `local_reverse_samples/cpp_6af7c7f1/solver.py`.
4. Do not run IDA, OllyDbg, Frida, or other runtime probes unless the user explicitly authorizes it.
5. Do not commit `local_reverse_samples/` contents or the local `solver.py`.
6. If a reusable pattern appears, propose a future project strategy instead of modifying the current samplereverse strategy immediately.

## Case Payload

```json
{
  "cases": [
    {
      "case_id": "cpp_6af7c7f1",
      "input_value": "local_reverse_samples/cpp_6af7c7f1/sample.exe",
      "expected_flag": "",
      "category": "unknown",
      "tags": [
        "local",
        "reverse",
        "auto_imported"
      ],
      "notes": "Auto-generated from local sample intake."
    }
  ]
}
```
