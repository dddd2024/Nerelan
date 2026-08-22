import { afterEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { RunsPage } from "@/routes/runs";

function httpRun(taskId: string) {
  return {
    task_id: taskId,
    title: `队列任务 ${taskId}`,
    repository: "dddd2024/reverse-agent",
    status: "QUEUED",
    state: "QUEUED",
    executor_kind: "deterministic_fixture",
    orchestration_mode: "single",
    created_at: "2026-08-22T06:00:00.000Z",
    updated_at: "2026-08-22T06:01:00.000Z",
    failure_classification: "",
    goal_id: "goal-http",
    goal_title: "HTTP queue goal",
    window_id: "window-http",
    stage: "PLAN",
    liveness: "WAITING",
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
        availability: "AVAILABLE",
        reason_code: "QUEUED_UNCLAIMED",
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


describe("Agent Runs page", () => {
  it("renders the derived run timeline with state badges", async () => {
    renderWithProviders(<RunsPage />);
    expect(screen.getByRole("heading", { name: /Agent 运行/ })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByTestId("run-task-demo-1")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("run-state-task-demo-1").textContent).toBe(
      "等待人工审查",
    );
    expect(screen.getByTestId("run-state-task-demo-2").textContent).toBe("运行中");
  });

  it("shows the goal link and publication PR link per run", async () => {
    renderWithProviders(<RunsPage />);
    await waitFor(() =>
      expect(screen.getByTestId("run-goal-task-demo-1")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("run-goal-task-demo-1").textContent).toContain(
      "完善无人值守多 Agent 平台",
    );

    const pr = screen.getByTestId("run-pr-task-demo-1");
    expect(pr).toHaveAttribute(
      "href",
      "https://github.com/dddd2024/reverse-agent/pull/97",
    );
    expect(pr.textContent).toContain("#97");

    expect(screen.queryByTestId("run-pr-task-demo-2")).not.toBeInTheDocument();
  });

  it("states the read-model contract in the page copy", () => {
    renderWithProviders(<RunsPage />);
    expect(
      screen.getByText(/由任务库、目标链接与发布记录派生的只读时间线/),
    ).toBeInTheDocument();
  });

  it("shows numeric usage and only draws a bar for hard admission", async () => {
    renderWithProviders(<RunsPage />);
    const observed = await screen.findByTestId("run-usage-task-demo-1");
    expect(observed.textContent).toContain("Tokens 68,420");
    expect(observed.textContent).toContain("Cost $0.8123");
    expect(screen.getByTestId("run-enforcement-task-demo-1").textContent).toBe(
      "派发前硬预算",
    );
    expect(within(observed).getByRole("progressbar")).toHaveAttribute(
      "aria-valuemax",
      "240000",
    );
    expect(screen.getByTestId("run-usage-overrun-task-demo-1").textContent).toContain(
      "仅在完成后发现",
    );

    const unknown = screen.getByTestId("run-usage-task-demo-2");
    expect(screen.getByTestId("run-enforcement-task-demo-2").textContent).toBe(
      "用量未知，已停派发",
    );
    expect(within(unknown).queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByTestId("run-usage-unknown-task-demo-2").textContent).toContain(
      "UNKNOWN 不是 0",
    );
  });

  it("shows semantic activity, stage, liveness and change summary on each card", async () => {
    renderWithProviders(<RunsPage />);
    await waitFor(() => expect(screen.getByTestId("run-task-demo-2")).toBeInTheDocument());

    expect(screen.getByTestId("run-liveness-task-demo-2").textContent).toContain("活跃");
    expect(screen.getByTestId("run-agent-task-demo-2").textContent).toContain("Coder");
    expect(screen.getByTestId("run-current-activity-task-demo-2").textContent).toContain("运行集成测试");
    expect(screen.getByTestId("run-change-summary-task-demo-2").textContent).toContain("1 个文件");
  });

  it("opens the detail region by keyboard and renders overview, activity and files", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    const toggle = await screen.findByTestId("run-toggle-task-demo-2");

    toggle.focus();
    await user.keyboard("{Enter}");

    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const region = await screen.findByTestId("run-detail-task-demo-2");
    expect(region).toHaveAttribute("role", "region");
    expect(region).toHaveAttribute("id", "run-detail-task-demo-2");
    const overview = within(region).getByTestId("run-overview-task-demo-2");
    expect(overview).toBeInTheDocument();
    expect(within(overview).getByText("执行")).toBeInTheDocument();
    expect(within(overview).getByText("Coder")).toBeInTheDocument();
    expect(within(region).getByText("Activity")).toBeInTheDocument();
    expect(within(region).getByText("Files")).toBeInTheDocument();
    expect(within(region).getByText("活动")).toBeInTheDocument();
    expect(within(region).getByText("最近 3 / 共 8 条")).toBeInTheDocument();
    expect(within(region).getByText(/仅显示最近 3 条结构化活动/)).toBeInTheDocument();
    const commandActivity = within(region).getByTestId("run-activity-activity-demo-5");
    expect(within(commandActivity).getByText(/git_diff_check/)).toBeInTheDocument();
    expect(within(commandActivity).getByText(/RUNNING/)).toBeInTheDocument();
    expect(within(region).getByTestId("run-files-task-demo-2")).toContainElement(
      within(region).getByText("reverse_agent/platform_v1/task_service.py"),
    );

    await user.keyboard("{Enter}");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByTestId("run-detail-task-demo-2")).not.toBeInTheDocument();
  });

  it("renders the finite cancel contract and keeps unsupported controls disabled", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);

    const runningToggle = await screen.findByTestId("run-toggle-task-demo-2");
    await user.click(runningToggle);
    const runningCancel = await screen.findByTestId("run-cancel-task-demo-2");
    expect(runningCancel).toBeDisabled();
    expect(screen.getByTestId("run-cancel-help-task-demo-2").textContent).toContain(
      "当前状态不支持取消",
    );
  });

  it("requires inline confirmation and refetches the mock run after queue cancellation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);

    await user.click(await screen.findByTestId("run-toggle-task-demo-queued"));
    const cancel = await screen.findByTestId("run-cancel-task-demo-queued");
    expect(cancel).toBeEnabled();
    await user.click(cancel);
    expect(screen.getByTestId("run-cancel-confirm-task-demo-queued")).toBeInTheDocument();
    expect(screen.getByText(/不会停止正在运行的 Agent/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "确认取消" }));
    await waitFor(() => expect(screen.getByTestId("run-cancel-task-demo-queued")).toBeDisabled());
    expect(screen.getByTestId("run-cancel-help-task-demo-queued").textContent).toContain("任务已取消");
    expect(screen.getByTestId("run-state-task-demo-queued").textContent).toBe("CANCELLED");
  });

  it("uses the real 409 error path, refetches run and list, then shows the fixed conflict", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const run = httpRun("task-http-409");
    const calls: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push(`${init?.method ?? "GET"} ${url}`);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [run] });
      if (url.endsWith("/api/runs/task-http-409/cancel")) {
        return jsonResponse({ error: "queue_cancel_unavailable", reason_code: "STATUS_NOT_CANCELLABLE" }, 409);
      }
      if (url.endsWith("/api/runs/task-http-409")) return jsonResponse(run);
      return jsonResponse({ error: "not found" }, 404);
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    await user.click(await screen.findByTestId("run-toggle-task-http-409"));
    await user.click(await screen.findByTestId("run-cancel-task-http-409"));
    await user.click(await screen.findByRole("button", { name: "确认取消" }));

    const alert = await screen.findByTestId("run-cancel-error-task-http-409");
    expect(alert).toHaveTextContent("取消请求与最新运行状态冲突，请刷新后重试。");
    const cancelIndex = calls.findIndex((call) => call.includes("/cancel"));
    expect(cancelIndex).toBeGreaterThanOrEqual(0);
    expect(calls.slice(cancelIndex + 1).filter((call) => call.includes("task-http-409"))).toHaveLength(1);
    expect(calls.slice(cancelIndex + 1).some((call) => call.endsWith("GET http://127.0.0.1:8766/api/runs"))).toBe(true);
  });

  it("keeps one card pending and suppresses duplicate cancel submissions", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const run = httpRun("task-http-pending");
    let cancelCalls = 0;
    let resolveCancel!: (response: Response) => void;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return Promise.resolve(jsonResponse({ runs: [run] }));
      if (url.endsWith("/api/runs/task-http-pending")) return Promise.resolve(jsonResponse(run));
      if (url.endsWith("/api/runs/task-http-pending/cancel")) {
        cancelCalls += 1;
        return new Promise<Response>((resolve) => { resolveCancel = resolve; });
      }
      return Promise.resolve(jsonResponse({ error: "not found" }, 404));
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    await user.click(await screen.findByTestId("run-toggle-task-http-pending"));
    await user.click(await screen.findByTestId("run-cancel-task-http-pending"));
    await user.click(await screen.findByRole("button", { name: "确认取消" }));
    const cancel = await screen.findByTestId("run-cancel-task-http-pending");
    expect(cancel).toBeDisabled();
    expect(cancel).toHaveTextContent("正在取消排队任务");
    expect(cancelCalls).toBe(1);
    await user.click(cancel);
    expect(cancelCalls).toBe(1);
    resolveCancel(jsonResponse({ status: "APPLIED" }));
    await waitFor(() => expect(screen.queryByTestId("run-cancel-error-task-http-pending")).not.toBeInTheDocument());
  });

  it("retries a non-409 cancel error through the mutation and clears the alert on success", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const run = httpRun("task-http-retry");
    let cancelCalls = 0;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [run] });
      if (url.endsWith("/api/runs/task-http-retry")) return jsonResponse(run);
      if (url.endsWith("/api/runs/task-http-retry/cancel")) {
        cancelCalls += 1;
        return cancelCalls === 1
          ? jsonResponse({ error: "queue_cancel_failed" }, 500)
          : jsonResponse({ status: "ALREADY_APPLIED" });
      }
      return jsonResponse({ error: "not found" }, 404);
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    await user.click(await screen.findByTestId("run-toggle-task-http-retry"));
    await user.click(await screen.findByTestId("run-cancel-task-http-retry"));
    await user.click(await screen.findByRole("button", { name: "确认取消" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("取消请求未完成，请稍后重试。");
    await user.click(within(alert).getByRole("button", { name: "重试" }));
    await waitFor(() => expect(cancelCalls).toBe(2));
    await waitFor(() => expect(screen.queryByTestId("run-cancel-error-task-http-retry")).not.toBeInTheDocument());
  });

  it("does not write a late error after collapse and restores clean state on reopen", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const run = httpRun("task-http-collapse");
    let rejectCancel!: (error: Error) => void;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return Promise.resolve(jsonResponse({ runs: [run] }));
      if (url.endsWith("/api/runs/task-http-collapse")) return Promise.resolve(jsonResponse(run));
      if (url.endsWith("/api/runs/task-http-collapse/cancel")) return new Promise<Response>((_resolve, reject) => { rejectCancel = reject; });
      return Promise.resolve(jsonResponse({ error: "not found" }, 404));
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    const toggle = await screen.findByTestId("run-toggle-task-http-collapse");
    await user.click(toggle);
    await user.click(await screen.findByTestId("run-cancel-task-http-collapse"));
    await user.click(await screen.findByRole("button", { name: "确认取消" }));
    await user.click(toggle);
    rejectCancel(new Error("late failure"));
    await waitFor(() => expect(screen.queryByTestId("run-cancel-error-task-http-collapse")).not.toBeInTheDocument());
    await user.click(toggle);
    expect(screen.queryByTestId("run-cancel-error-task-http-collapse")).not.toBeInTheDocument();
  });

  it("guards a delayed 409 refetch when the detail collapses before reconciliation completes", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const run = httpRun("task-http-delayed-409");
    let detailReads = 0;
    let resolveDetail!: (response: Response) => void;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return Promise.resolve(jsonResponse({ runs: [run] }));
      if (url.endsWith("/api/runs/task-http-delayed-409")) {
        detailReads += 1;
        if (detailReads > 1) return new Promise<Response>((resolve) => { resolveDetail = resolve; });
        return Promise.resolve(jsonResponse(run));
      }
      if (url.endsWith("/api/runs/task-http-delayed-409/cancel")) {
        return Promise.resolve(jsonResponse({ error: "queue_cancel_unavailable", reason_code: "STATUS_NOT_CANCELLABLE" }, 409));
      }
      return Promise.resolve(jsonResponse({ error: "not found" }, 404));
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    const toggle = await screen.findByTestId("run-toggle-task-http-delayed-409");
    await user.click(toggle);
    await user.click(await screen.findByTestId("run-cancel-task-http-delayed-409"));
    await user.click(await screen.findByRole("button", { name: "确认取消" }));
    await waitFor(() => expect(detailReads).toBe(2));
    await user.click(toggle);
    resolveDetail(jsonResponse(run));
    await waitFor(() => expect(screen.queryByTestId("run-cancel-error-task-http-delayed-409")).not.toBeInTheDocument());
    await user.click(toggle);
    expect(screen.queryByTestId("run-cancel-error-task-http-delayed-409")).not.toBeInTheDocument();
  });

  it("keeps cancellation errors isolated to one card and supports keyboard confirmation focus", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const first = httpRun("task-http-isolated");
    const second = httpRun("task-http-other");
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [first, second] });
      if (url.endsWith("/api/runs/task-http-isolated")) return jsonResponse(first);
      if (url.endsWith("/api/runs/task-http-other")) return jsonResponse(second);
      if (url.endsWith("/api/runs/task-http-isolated/cancel")) return jsonResponse({ error: "queue_cancel_failed" }, 500);
      return jsonResponse({ error: "not found" }, 404);
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    const toggle = await screen.findByTestId("run-toggle-task-http-isolated");
    toggle.focus();
    await user.keyboard("{Enter}");
    const cancel = await screen.findByTestId("run-cancel-task-http-isolated");
    cancel.focus();
    await user.keyboard("{Enter}");
    const confirm = await screen.findByRole("button", { name: "确认取消" });
    expect(document.activeElement).toBe(confirm);
    await user.keyboard("{Enter}");
    const alert = await screen.findByTestId("run-cancel-error-task-http-isolated");
    expect(alert).toHaveAttribute("role", "alert");
    expect(screen.queryByTestId("run-cancel-error-task-http-other")).not.toBeInTheDocument();
  });
});
