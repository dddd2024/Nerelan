import { afterEach, describe, expect, it, vi } from "vitest";
import { createTask, executeTask } from "@/lib/task-client";

describe("mock task governance truth", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("createTask fails closed when mock mode has no canonical governance binding", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "");

    const created = await createTask({ title: "mock governance task" });

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(created.issueNumber).toBeNull();
    expect(created.riskTier).toBe("UNKNOWN");
    expect(created.authorityStatus).toBe("MISSING");
    expect(created.workflowStatus).toBe("UNKNOWN");
  });

  it("executeTask fails closed on governance metadata while preserving evidence-backed test status", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "");

    const executed = await executeTask("mock-task-001");

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(executed.issueNumber).toBeNull();
    expect(executed.riskTier).toBe("UNKNOWN");
    expect(executed.authorityStatus).toBe("MISSING");
    expect(executed.workflowStatus).toBe("UNKNOWN");
    expect(executed.testStatus).toBe("PASS");
  });
});
