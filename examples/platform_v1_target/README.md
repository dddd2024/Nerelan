# Platform V1 target example

This directory holds an example target Work Item payload that demonstrates
the thin adapter's input contract. It is consumed by the provider-free CI
tests to verify contract, policy, idempotency, and acceptance behavior
without any real provider credentials.

## Usage

```bash
# Validate the example Work Item against the platform policy
python -m reverse_agent.platform_v1.cli validate-work-item < examples/platform_v1_target/work_item.json

# Generate the bounded task prompt
python -m reverse_agent.platform_v1.cli generate-prompt < examples/platform_v1_target/work_item.json

# Evaluate acceptance from a synthetic evidence payload
python -m reverse_agent.platform_v1.cli evaluate-acceptance < examples/platform_v1_target/acceptance_input.json
```

All three commands are machine-readable (JSON on stdout) and return stable
exit codes (0 = success, 10 = schema error, 20 = policy violation,
40 = REWORK_REQUIRED, 50 = BLOCKED_APPROVAL / FAILED_TERMINAL).
