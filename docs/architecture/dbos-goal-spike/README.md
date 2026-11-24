# DBOS goal recovery experiment

The [#1546 adoption gate](https://github.com/dddd2024/Nerelan/issues/1546) requires Windows SQLite compatibility, recovery without duplicate review calls, a safe alternate-account retry, and roughly 3,000 lines of replaceable code. **Do not replace the Goal engine at this stage.** The duplicate-review counterexample fails a required gate. Durable timers are a candidate for a smaller experiment.

## Results

Windows CPython 3.13.12 ran DBOS `3.7.0a0+g2cf279c` from [the pinned upstream revision](https://github.com/dbos-inc/dbos-transact-py/tree/2cf279cf380152b426ecd451d573ccc41f5715a6) against Nerelan main at `0ddd4ef5`. DBOS and TaskStore used separate SQLite files under a fresh temporary directory. Restart recovered the original workflow ID without a second submission.

| Scenario | Observed result |
| --- | --- |
| A refused attempt and its 429 are recorded, then the worker exits before DBOS records the implement step | The existing GoalService replaces the synthetic `bind-a` attempt with `bind-b` exactly once. The workflow runs a fixture implementation, a fixture rejection, one repair and a refreshed fixture review. The four executor receipts are `SUCCESS`. |
| The real deterministic executor writes its fixture change, then the worker exits before the durable service settles its receipt | The next worker finds the original `PENDING` operation and returns an explicit hold. It leaves one task and one operation. Restarting again preserves the result. |
| A simulated review receiver commits before DBOS records the step result, with no TaskStore intent | The recovered workflow calls the receiver again. Both calls commit. |

The first row uses the [#1696 test bed](https://github.com/dddd2024/Nerelan/issues/1696) for fault injection and named bindings. It exercises actual escalation and the existing deterministic executor. Real account handoff, model review independence and live publication remain outside this replay. The hold in the second row needs a verified receipt or an authorized resolution. A completed DBOS method returning a hold leaves the Nerelan operation pending.

Earlier isolated runs of the same upstream revision also completed 100 TaskStore writes from two concurrent workflows. An experiment with a persisted 12-second timer killed the worker, waited for the deadline and retrieved the recovered result in 2.67 seconds. With a receiver capable of lookup by stable operation ID, a separate review experiment reconciled the original TaskStore intent without a second call. A stale lease epoch could not settle the receipt.

## Replacement boundary

The directly targeted entry points in `control_store.py`, `goal_service.py` and `unattended_coordinator.py` span 744 gross lines on the evaluated main commit. This covers status projection, runnable selection, retries, review repair, and coordinator sweeps. That footprint includes policy and evidence code that a workflow still needs.

TaskStore remains authoritative for claims and budgets, external intent and receipts, workspaces, and execution fencing. Model-review evidence must still identify the exact artifact and an independent author. Publication and landing keep their matched-head gates and separate durable operation receipts. No net replacement above the issue's threshold was established.

## Reproduce

From a checkout with Git and Python 3.13, use an isolated virtual environment. The script starts only its own fixture workers and never starts a Nerelan server or model executor.

```powershell
python -m venv .venv-spike
.\.venv-spike\Scripts\python.exe -m pip install -e ".[test]" "dbos @ git+https://github.com/dbos-inc/dbos-transact-py.git@2cf279cf380152b426ecd451d573ccc41f5715a6"
.\.venv-spike\Scripts\python.exe docs/architecture/dbos-goal-spike/replay.py
```

The runner prints its fixture directory and verifies the result twice after each forced process exit. Workers require a directory and marker created by the runner. The runner removes inherited Git and DBOS settings before starting a worker. The three scenarios stay outside standard CI and project dependencies.
