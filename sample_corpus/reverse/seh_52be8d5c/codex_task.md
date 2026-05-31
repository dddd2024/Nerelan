# Local Reverse Sample Task: seh_52be8d5c

## Sample

- case_id: `seh_52be8d5c`
- sample path: `local_reverse_samples/seh_52be8d5c/sample.exe`
- sha256: `52be8d5c485f7c7c3340d42791505b9f55cf4ff63191768c0cc62f30cde4ae07`
- size_bytes: `196685`
- case.json: `local_reverse_samples/seh_52be8d5c/case.json`
- expected solver output: `local_reverse_samples/seh_52be8d5c/solver.py`

## Harness

```powershell
python -m reverse_agent.harness --dataset local_reverse_samples\seh_52be8d5c\case.json --run-name local_seh_52be8d5c_static --analysis-mode "Static Analysis" --case-id seh_52be8d5c
```

## First Pass

1. Inspect printable strings, imports, constants, compare points, hash clues, and encoding indicators.
2. Keep the first pass static and auditable.
3. Write any one-off solution code to `local_reverse_samples/seh_52be8d5c/solver.py`.
4. Do not run IDA, OllyDbg, Frida, or other runtime probes unless the user explicitly authorizes it.
5. Do not commit `local_reverse_samples/` contents or the local `solver.py`.
6. If a reusable pattern appears, propose a future project strategy instead of modifying the current samplereverse strategy immediately.

## Case Payload

```json
{
  "cases": [
    {
      "case_id": "seh_52be8d5c",
      "input_value": "local_reverse_samples/seh_52be8d5c/sample.exe",
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
