import { describe, expect, it } from "vitest";
import { fetchRuns, startGoal } from "@/lib/platform-client";

describe("provider-free mock Goal-to-Run continuity", () => {
  it("materializes runs for the task links returned by startGoal", async () => {
    const goal = await startGoal({
      objective: "Verify provider-free Goal-to-Run continuity",
      repository: "dddd2024/Nerelan",
      executorKind: "deterministic_fixture",
      bindingRef: "",
      autonomyHours: 2,
    });

    const links = goal.task_links ?? [];
    expect(links.length).toBeGreaterThanOrEqual(2);

    const runs = await fetchRuns();
    const linkedRuns = links.map((link) => runs.find((run) => run.task_id === link.task_id));
    expect(linkedRuns).not.toContain(undefined);

    const primary = linkedRuns[0];
    if (!primary) throw new Error("mock primary run was not materialized");

    expect(primary.goal_id).toBe(goal.id);
    expect(primary.goal_title).toBe(goal.title);
    expect(primary.repository).toBe(goal.repository);
    expect(primary.executor_kind).toBe("deterministic_fixture");
    expect(primary.orchestration_mode).toBe("single");
    expect(primary.agents?.length ?? 0).toBeGreaterThan(0);
    expect(primary.events?.length ?? 0).toBeGreaterThan(0);
    expect(primary.events?.every((event) => event.task_id === primary.task_id)).toBe(true);
    expect(primary.changed_files?.length ?? 0).toBeGreaterThan(0);
    expect(primary.validation).toBeTruthy();
    expect(primary.usage.total_token_units).toBe(0);

    const queued = linkedRuns.find(
      (run) => run?.controls?.cancel.availability === "AVAILABLE",
    );
    expect(queued).toBeDefined();
    expect(queued?.state).toBe("QUEUED");
    expect(queued?.controls?.cancel.scope).toBe("QUEUE_ONLY");
    expect(queued?.controls?.cancel.reason_code).toBe("QUEUED_UNCLAIMED");

    expect(runs.some((run) => run.task_id === "task-demo-1")).toBe(true);
    expect(runs.some((run) => run.task_id === "task-demo-queued")).toBe(true);
  });
});
