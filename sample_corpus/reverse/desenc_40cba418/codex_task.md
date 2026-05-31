# Local Reverse Sample Task: desenc_40cba418

## Sample

- case_id: `desenc_40cba418`
- sample path: `local_reverse_samples/desenc_40cba418/sample.exe`
- sha256: `40cba4189a9639da601b9d9b74fd9937c3d03fc93c90f5df12840e8b7763700f`
- size_bytes: `200784`
- case.json: `local_reverse_samples/desenc_40cba418/case.json`
- expected solver output: `local_reverse_samples/desenc_40cba418/solver.py`

## Harness

```powershell
python -m reverse_agent.harness --dataset local_reverse_samples\desenc_40cba418\case.json --run-name local_desenc_40cba418_static --analysis-mode "Static Analysis" --case-id desenc_40cba418
```

## First Pass

1. Inspect printable strings, imports, constants, compare points, hash clues, and encoding indicators.
2. Keep the first pass static and auditable.
3. Write any one-off solution code to `local_reverse_samples/desenc_40cba418/solver.py`.
4. Do not run IDA, OllyDbg, Frida, or other runtime probes unless the user explicitly authorizes it.
5. Do not commit `local_reverse_samples/` contents or the local `solver.py`.
6. If a reusable pattern appears, propose a future project strategy instead of modifying the current samplereverse strategy immediately.

## Case Payload

```json
{
  "cases": [
    {
      "case_id": "desenc_40cba418",
      "input_value": "local_reverse_samples/desenc_40cba418/sample.exe",
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
