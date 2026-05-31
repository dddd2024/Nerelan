# Local Reverse Sample Task: rc4enc_3480917d

## Sample

- case_id: `rc4enc_3480917d`
- sample path: `local_reverse_samples/rc4enc_3480917d/sample.exe`
- sha256: `3480917ddedce512f76e97c26df3b3ad12b71b34db472fa8836ba67528bcb09f`
- size_bytes: `196693`
- case.json: `local_reverse_samples/rc4enc_3480917d/case.json`
- expected solver output: `local_reverse_samples/rc4enc_3480917d/solver.py`

## Harness

```powershell
python -m reverse_agent.harness --dataset local_reverse_samples\rc4enc_3480917d\case.json --run-name local_rc4enc_3480917d_static --analysis-mode "Static Analysis" --case-id rc4enc_3480917d
```

## First Pass

1. Inspect printable strings, imports, constants, compare points, hash clues, and encoding indicators.
2. Keep the first pass static and auditable.
3. Write any one-off solution code to `local_reverse_samples/rc4enc_3480917d/solver.py`.
4. Do not run IDA, OllyDbg, Frida, or other runtime probes unless the user explicitly authorizes it.
5. Do not commit `local_reverse_samples/` contents or the local `solver.py`.
6. If a reusable pattern appears, propose a future project strategy instead of modifying the current samplereverse strategy immediately.

## Case Payload

```json
{
  "cases": [
    {
      "case_id": "rc4enc_3480917d",
      "input_value": "local_reverse_samples/rc4enc_3480917d/sample.exe",
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
