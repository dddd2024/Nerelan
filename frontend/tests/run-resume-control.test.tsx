import { afterEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { RunsPage } from "@/routes/runs";

function resumeRunFixture(taskId: string) {
  return {
    task_id: taskId,
    title: `可恢复运行 ${taskId}`,
    repository: "dddd2024/reverse-agent",
    status: "RUNNING",
    state: "RUNNING",
    executor_kind: "opencode",
    orchestration_mode: "single",
    created_at: "2026-09-02T03:00:00.000Z",
    updated_at: "2026-09-02T03:01:00.000Z",
    failure_classification: "",
    goal_id: "goal-resume",
    goal_title: "Resume goal",
    window_id: "window-resume",
    stage: "RECOVERY",
    liveness: "STALE",
    current_activity: null,
    current_agent: null,
    agents: [],
    events: [],
    activity: [],
    activity_total: 0,
    changed_files: [],
    change_summary: null,
    validation: null,
    usage: {
      status: "OBSERVED",
      input_units: 0,
      output_units: 0,
      reasoning_units: 0,
      cache_read_units: 0,
      cache_write_units: 0,
      cost_micro_units: 0,
      total_token_units: 0,
      observation_count: 0,
      unknown_observation_count: 0,
      provenance_ids: [],
      per_role: [],
    },
    budget: null,
    publication: null,
    controls: {
      cancel: {
        action: "CANCEL",
        scope: "QUEUE_ONLY",
        availability: "UNAVAILABLE",
        reason_code: "STATUS_NOT_CANCELLABLE",
      },
      resume: {
        action: "RESUME",
        scope: "DURABLE_RECOVERY",
        availability: "AVAILABLE",
        reason_code: "INTERRUPTED_DURABLE_READY",
      },
    },
  };
}

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("Agent Runs durable Resume control", () => {
  it("trusts only the server descriptor, requires confirmation, and never posts early", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const run = resumeRunFixture("task-resume-descriptor");
    const calls: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push(`${init?.method ?? "GET"} ${url}`);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [run] });
      if (url.endsWith("/api/runs/task-resume-descriptor")) return jsonResponse(run);
      if (url.endsWith("/api/tasks/task-resume-descriptor/resume")) return jsonResponse({ status: "RUNNING" });
      return jsonResponse({ error: "not found" }, 404);
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    await user.click(await screen.findByTestId("run-toggle-task-resume-descriptor"));

    const resume = await screen.findByTestId("run-resume-task-resume-descriptor");
    expect(resume).toBeEnabled();
    expect(screen.getByTestId("run-resume-help-task-resume-descriptor")).toHaveTextContent(
      "服务端会重新校验恢复条件",
    );
    expect(calls.some((call) => call.includes("/api/tasks/task-resume-descriptor/resume"))).toBe(false);

    resume.focus();
    await user.keyboard("{Enter}");
    const confirm = await screen.findByRole("button", { name: "确认恢复" });
    expect(document.activeElement).toBe(confirm);
    expect(screen.getByTestId("run-resume-confirm-task-resume-descriptor")).toHaveTextContent(
      "当前提示不代表恢复一定成功",
    );
    expect(calls.some((call) => call.includes("/api/tasks/task-resume-descriptor/resume"))).toBe(false);

    await user.keyboard("{Enter}");
    await waitFor(() => {
      expect(calls.filter((call) => call === "POST http://127.0.0.1:8766/api/tasks/task-resume-descriptor/resume")).toHaveLength(1);
    });
    await waitFor(() => {
      expect(calls.filter((call) => call === "GET http://127.0.0.1:8766/api/runs").length).toBeGreaterThan(1);
      expect(calls.filter((call) => call === "GET http://127.0.0.1:8766/api/runs/task-resume-descriptor").length).toBeGreaterThan(1);
    });
  });

  it("refetches authoritative detail and list before surfacing a bounded 409 alert, then retries with a real POST", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const run = resumeRunFixture("task-resume-409");
    const calls: string[] = [];
    let resumeCalls = 0;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push(`${init?.method ?? "GET"} ${url}`);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [run] });
      if (url.endsWith("/api/runs/task-resume-409")) return jsonResponse(run);
      if (url.endsWith("/api/tasks/task-resume-409/resume")) {
        resumeCalls += 1;
        return resumeCalls === 1
          ? jsonResponse({ error: "no_active_durable_run_to_resume" }, 409)
          : jsonResponse({ status: "RUNNING" });
      }
      return jsonResponse({ error: "not found" }, 404);
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    await user.click(await screen.findByTestId("run-toggle-task-resume-409"));
    await user.click(await screen.findByTestId("run-resume-task-resume-409"));
    await user.click(await screen.findByRole("button", { name: "确认恢复" }));

    const alert = await screen.findByTestId("run-resume-error-task-resume-409");
    expect(alert).toHaveAttribute("role", "alert");
    expect(alert).toHaveTextContent("已重新读取服务器状态");
    const firstPost = calls.findIndex((call) => call.includes("/api/tasks/task-resume-409/resume"));
    expect(firstPost).toBeGreaterThanOrEqual(0);
    expect(calls.slice(firstPost + 1).some((call) => call === "GET http://127.0.0.1:8766/api/runs/task-resume-409")).toBe(true);
    expect(calls.slice(firstPost + 1).some((call) => call === "GET http://127.0.0.1:8766/api/runs")).toBe(true);

    await user.click(within(alert).getByRole("button", { name: "重试" }));
    await waitFor(() => expect(resumeCalls).toBe(2));
    await waitFor(() => expect(screen.queryByTestId("run-resume-error-task-resume-409")).not.toBeInTheDocument());
  });

  it("scopes pending state to one card, suppresses duplicate posts, and ignores a late error after collapse", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const run = resumeRunFixture("task-resume-pending");
    let resumeCalls = 0;
    let rejectResume!: (error: Error) => void;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return Promise.resolve(jsonResponse({ runs: [run] }));
      if (url.endsWith("/api/runs/task-resume-pending")) return Promise.resolve(jsonResponse(run));
      if (url.endsWith("/api/tasks/task-resume-pending/resume")) {
        resumeCalls += 1;
        return new Promise<Response>((_resolve, reject) => { rejectResume = reject; });
      }
      return Promise.resolve(jsonResponse({ error: "not found" }, 404));
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    const toggle = await screen.findByTestId("run-toggle-task-resume-pending");
    await user.click(toggle);
    await user.click(await screen.findByTestId("run-resume-task-resume-pending"));
    await user.click(await screen.findByRole("button", { name: "确认恢复" }));

    const resume = await screen.findByTestId("run-resume-task-resume-pending");
    expect(resume).toBeDisabled();
    expect(resume).toHaveTextContent("正在提交恢复请求");
    expect(resumeCalls).toBe(1);
    await user.click(resume);
    expect(resumeCalls).toBe(1);

    await user.click(toggle);
    rejectResume(new Error("late resume failure"));
    await waitFor(() => expect(screen.queryByTestId("run-resume-error-task-resume-pending")).not.toBeInTheDocument());
    await user.click(toggle);
    expect(screen.queryByTestId("run-resume-error-task-resume-pending")).not.toBeInTheDocument();
  });
});
