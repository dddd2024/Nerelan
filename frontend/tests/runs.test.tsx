import { afterEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { RunsPage } from "@/routes/runs";
import type { PlatformRunCurrentActivity } from "@/lib/platform-client";

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
      status: "USAGE_UNKNOWN",
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
    // Run state labels come from the same mapping as the task list, so the
    // same authoritative state cannot read differently on two surfaces. This
    // is the wording the Runs page already shipped with; the shared mapping
    // was aligned onto it rather than the other way round.
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

  it("collapses a server activity title that only restates the category", async () => {
    // The live read-model derives `current_activity.title` from the category
    // alone (`run_read_model.py::_activity_title`), so it is a static English
    // humanisation rather than authored content. The row used to print that one
    // fact twice, in two languages, with the readable half demoted:
    // `当前活动：Agent completed · Agent 完成`.
    const currentActivity: PlatformRunCurrentActivity = {
      category: "AGENT_COMPLETED",
      title: "Agent completed",
      description: "",
    };
    const run = { ...httpRun("task-http-generic-activity"), current_activity: currentActivity };
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) =>
        jsonResponse(String(input).endsWith("/api/runs") ? { runs: [run] } : run),
      ),
    );

    renderWithProviders(<RunsPage />);

    const activity = await screen.findByTestId("run-current-activity-task-http-generic-activity");
    expect(activity.textContent).toContain("当前活动：Agent 完成");
    expect(activity.textContent).not.toContain("Agent completed");
  });

  it("keeps an authored server activity title beside its category label", async () => {
    // A title the server did not derive from the category names the specific
    // activity, so it must stay visible in full; the label becomes the hint.
    const currentActivity: PlatformRunCurrentActivity = {
      category: "COMMAND",
      title: "运行集成测试",
      description: "正在执行确定性测试。",
    };
    const run = {
      ...httpRun("task-http-authored-activity"),
      state: "RUNNING",
      current_activity: currentActivity,
    };
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) =>
        jsonResponse(String(input).endsWith("/api/runs") ? { runs: [run] } : run),
      ),
    );

    renderWithProviders(<RunsPage />);

    const activity = await screen.findByTestId("run-current-activity-task-http-authored-activity");
    expect(activity.textContent).toContain("当前活动：运行集成测试");
    expect(activity.textContent).toContain("命令");
    expect(activity.textContent).toContain("正在执行确定性测试。");
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
    expect(within(region).getByText("执行活动")).toBeInTheDocument();
    expect(within(region).getByText("变更文件")).toBeInTheDocument();
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

  it("renders truthful usage for observed-zero, no-observations, all-unknown and partial runs", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const zeroTotals = { input_units: 0, output_units: 0, reasoning_units: 0, cache_read_units: 0, cache_write_units: 0, cost_micro_units: 0, total_token_units: 0 };
    const observedZero = { ...httpRun("task-usage-observed-zero"),
      usage: { status: "OBSERVED", ...zeroTotals, observation_count: 2, unknown_observation_count: 0, provenance_ids: ["a", "b"], per_role: [] } };
    const noObs = { ...httpRun("task-usage-no-obs"),
      usage: { status: "USAGE_UNKNOWN", ...zeroTotals, observation_count: 0, unknown_observation_count: 0, provenance_ids: [], per_role: [] } };
    const allUnknown = { ...httpRun("task-usage-all-unknown"),
      usage: { status: "USAGE_UNKNOWN", ...zeroTotals, observation_count: 1, unknown_observation_count: 1, provenance_ids: ["u"], per_role: [] } };
    const partial = { ...httpRun("task-usage-partial"),
      usage: { status: "USAGE_UNKNOWN", input_units: 1000, output_units: 200, reasoning_units: 0, cache_read_units: 300, cache_write_units: 0, cost_micro_units: 5000, total_token_units: 1500, observation_count: 3, unknown_observation_count: 1, provenance_ids: ["o1", "o2", "u"], per_role: [] } };
    const partialZero = { ...httpRun("task-usage-partial-zero"),
      usage: { status: "USAGE_UNKNOWN", ...zeroTotals, observation_count: 2, unknown_observation_count: 1, provenance_ids: ["z", "u"], per_role: [] } };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [observedZero, noObs, allUnknown, partial, partialZero] });
      return jsonResponse({ error: "not found" }, 404);
    }));

    renderWithProviders(<RunsPage />);

    const observedZeroUsage = await screen.findByTestId("run-usage-task-usage-observed-zero");
    expect(observedZeroUsage.textContent).toContain("Tokens 0");
    expect(observedZeroUsage.textContent).toContain("Cost $0.0000");
    expect(observedZeroUsage.textContent).toContain("已观测为 0");
    expect(observedZeroUsage.textContent).not.toContain("用量未知");

    const noObservations = await screen.findByTestId("run-usage-task-usage-no-obs");
    expect(noObservations.textContent).toContain("尚无用量观测记录");
    expect(noObservations.textContent).not.toContain("Tokens");

    const allUnknownUsage = await screen.findByTestId("run-usage-task-usage-all-unknown");
    expect(allUnknownUsage.textContent).toContain("用量未知：1 条观测均未提供数值");
    expect(allUnknownUsage.textContent).not.toContain("Tokens");

    const partialUsage = await screen.findByTestId("run-usage-task-usage-partial");
    expect(partialUsage.textContent).toContain("Tokens 1,500（部分）");
    expect(partialUsage.textContent).toContain("Cost $0.0050（部分）");
    expect(partialUsage.textContent).toContain("1 条未知");
    expect(partialUsage.textContent).not.toContain("尚无可信数值观测");

    // A mixed summary with a genuinely observed-zero subtotal must still show
    // the zero truthfully and mark it partial, never hiding behind
    // no-trustworthy-observation copy.
    const partialZeroUsage = await screen.findByTestId("run-usage-task-usage-partial-zero");
    expect(partialZeroUsage.textContent).toContain("Tokens 0（部分）");
    expect(partialZeroUsage.textContent).toContain("Cost $0.0000（部分）");
    expect(partialZeroUsage.textContent).toContain("1 条未知");
    expect(partialZeroUsage.textContent).not.toContain("尚无可信数值观测");
    expect(partialZeroUsage.textContent).not.toContain("已观测为 0");

    // The provider-reported cost disclaimer lives once at the page level instead
    // of repeating in every observed row.
    expect(screen.getByTestId("runs-cost-context").textContent).toContain("成本为 Provider");
    expect(screen.getByTestId("runs-cost-context").textContent).toContain("不代表免费");
  });

  it("identifies each run by task title in the toggle accessible name", async () => {
    renderWithProviders(<RunsPage />);
    const toggle = await screen.findByTestId("run-toggle-task-demo-1");
    const label = toggle.getAttribute("aria-label") ?? "";
    expect(label).toMatch(/运行：.*T001 分析目标与代码库/);
    expect(label).toContain("等待人工审查");
    expect(screen.getByText(/T001 分析目标与代码库/)).toBeInTheDocument();
  });

  it("progressively discloses unavailable controls while keeping applicable ones prominent", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const unavailableRun = {
      ...httpRun("task-disc-unavailable"),
      controls: {
        cancel: { action: "CANCEL", scope: "QUEUE_ONLY", availability: "UNAVAILABLE", reason_code: "STATUS_NOT_CANCELLABLE" },
      },
    };
    const availableRun = { ...httpRun("task-disc-available") };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [unavailableRun, availableRun] });
      if (url.endsWith("/api/runs/task-disc-unavailable")) return jsonResponse(unavailableRun);
      if (url.endsWith("/api/runs/task-disc-available")) return jsonResponse(availableRun);
      return jsonResponse({ error: "not found" }, 404);
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);

    // An unavailable control collapses into a native details so the expanded
    // card no longer leads with two large unavailable panels; the disabled
    // button and server-authoritative reason remain reachable.
    await user.click(await screen.findByTestId("run-toggle-task-disc-unavailable"));
    await waitFor(() => expect(screen.getByTestId("run-cancel-help-task-disc-unavailable").textContent).toContain("当前状态不支持取消"));
    const cancelDetails = screen.getByTestId("run-control-task-disc-unavailable");
    expect(cancelDetails.tagName).toBe("DETAILS");
    expect(cancelDetails).not.toHaveAttribute("open");
    expect(screen.getByTestId("run-cancel-task-disc-unavailable")).toBeDisabled();

    // Resume is unavailable here too: same compact disclosure, truthful reason.
    const resumeDetails = screen.getByTestId("run-resume-control-task-disc-unavailable");
    expect(resumeDetails.tagName).toBe("DETAILS");
    expect(resumeDetails).not.toHaveAttribute("open");
    expect(screen.getByTestId("run-resume-task-disc-unavailable")).toBeDisabled();
    expect(screen.getByTestId("run-resume-help-task-disc-unavailable").textContent).toContain("服务器未提供");

    // An applicable control stays a prominent section, not a collapsed disclosure.
    await user.click(await screen.findByTestId("run-toggle-task-disc-available"));
    const availableCancel = await screen.findByTestId("run-cancel-task-disc-available");
    await waitFor(() => expect(availableCancel).toBeEnabled());
    expect(screen.getByTestId("run-control-task-disc-available").tagName).toBe("SECTION");
  });

  it("renders a truthful task-id heading and accessible name when the public title is empty or whitespace", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const emptyTitleRun = { ...httpRun("task-empty-title"), title: "", goal_id: "goal-redacted", goal_title: "被脱敏的目标标题" };
    const whitespaceRun = { ...httpRun("task-whitespace-title"), title: "   \t  ", goal_id: "goal-redacted", goal_title: "被脱敏的目标标题" };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [emptyTitleRun, whitespaceRun] });
      return jsonResponse({ error: "not found" }, 404);
    }));

    renderWithProviders(<RunsPage />);

    const emptyHeading = await screen.findByTestId("run-heading-task-empty-title");
    expect(emptyHeading.textContent).toBe("任务 task-empty-title · 标题暂不可用");
    expect(emptyHeading.textContent).not.toContain("被脱敏的目标标题");
    const emptyToggle = screen.getByTestId("run-toggle-task-empty-title");
    expect(emptyToggle.getAttribute("aria-label") ?? "").toMatch(/运行：.*任务 task-empty-title/);
    expect(emptyToggle.getAttribute("aria-label") ?? "").toContain("标题暂不可用");

    const wsHeading = screen.getByTestId("run-heading-task-whitespace-title");
    expect(wsHeading.textContent).toBe("任务 task-whitespace-title · 标题暂不可用");
    expect(wsHeading.textContent).not.toContain("被脱敏的目标标题");
    expect((screen.getByTestId("run-toggle-task-whitespace-title").getAttribute("aria-label") ?? "")).toContain("任务 task-whitespace-title");

    // The goal remains truthful secondary metadata, never promoted to the heading.
    expect(screen.getByTestId("run-goal-task-empty-title").textContent).toContain("被脱敏的目标标题");
  });

  it("keeps same-goal runs with empty titles distinguishable by task id", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const runA = { ...httpRun("task-samegoal-a"), title: "", goal_id: "goal-same", goal_title: "同一目标" };
    const runB = { ...httpRun("task-samegoal-b"), title: "", goal_id: "goal-same", goal_title: "同一目标" };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [runA, runB] });
      return jsonResponse({ error: "not found" }, 404);
    }));

    renderWithProviders(<RunsPage />);

    const headingA = await screen.findByTestId("run-heading-task-samegoal-a");
    const headingB = screen.getByTestId("run-heading-task-samegoal-b");
    expect(headingA.textContent).toContain("task-samegoal-a");
    expect(headingB.textContent).toContain("task-samegoal-b");
    expect(headingA.textContent).not.toStrictEqual(headingB.textContent);

    const labelA = screen.getByTestId("run-toggle-task-samegoal-a").getAttribute("aria-label") ?? "";
    const labelB = screen.getByTestId("run-toggle-task-samegoal-b").getAttribute("aria-label") ?? "";
    expect(labelA).not.toStrictEqual(labelB);
    expect(labelA).toContain("task-samegoal-a");
    expect(labelB).toContain("task-samegoal-b");
  });

  it("falls back to the task id for runs with no goal and an empty title", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const noGoalRun = { ...httpRun("task-nogoal"), title: "  ", goal_id: "", goal_title: "" };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [noGoalRun] });
      return jsonResponse({ error: "not found" }, 404);
    }));

    renderWithProviders(<RunsPage />);

    const heading = await screen.findByTestId("run-heading-task-nogoal");
    expect(heading.textContent).toBe("任务 task-nogoal · 标题暂不可用");
    expect(screen.getByText("未关联目标")).toBeInTheDocument();
    const toggle = screen.getByTestId("run-toggle-task-nogoal");
    expect(toggle.getAttribute("aria-label") ?? "").toMatch(/运行：.*任务 task-nogoal/);
  });

  it("keeps keyboard focus on the run disclosure when a 409 makes cancel unavailable", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const queuedRun = httpRun("task-focus-409");
    const cancelledRun = {
      ...queuedRun,
      status: "CANCELLED",
      state: "CANCELLED",
      controls: { cancel: { action: "CANCEL", scope: "QUEUE_ONLY", availability: "UNAVAILABLE", reason_code: "ALREADY_CANCELLED" } },
    };
    let cancelCalls = 0;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      const afterAttempt = cancelCalls > 0;
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [afterAttempt ? cancelledRun : queuedRun] });
      if (url.endsWith("/api/runs/task-focus-409")) return jsonResponse(afterAttempt ? cancelledRun : queuedRun);
      if (url.endsWith("/api/runs/task-focus-409/cancel")) {
        cancelCalls += 1;
        return cancelCalls === 1
          ? jsonResponse({ error: "queue_cancel_unavailable", reason_code: "STATUS_NOT_CANCELLABLE" }, 409)
          : jsonResponse({ status: "APPLIED" });
      }
      return jsonResponse({ error: "not found" }, 404);
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);
    const toggle = await screen.findByTestId("run-toggle-task-focus-409");
    await user.click(toggle);
    await user.click(await screen.findByTestId("run-cancel-task-focus-409"));
    await user.click(await screen.findByRole("button", { name: "确认取消" }));

    const alert = await screen.findByTestId("run-cancel-error-task-focus-409");
    expect(alert).toHaveTextContent("取消请求与最新运行状态冲突");
    const retryButton = within(alert).getByRole("button", { name: "重试" });
    await waitFor(() => expect(document.activeElement).toBe(retryButton));

    await user.click(retryButton);
    await waitFor(() => expect(screen.queryByTestId("run-cancel-error-task-focus-409")).not.toBeInTheDocument());
    // The retry removed the error button; the control is unavailable, so focus
    // must land on the stable run disclosure, not a disabled control or body.
    expect(document.activeElement).toBe(toggle);
    expect(screen.getByTestId("run-control-task-focus-409").tagName).toBe("DETAILS");
    expect(screen.getByTestId("run-cancel-help-task-focus-409").textContent).toContain("任务已取消");
  });

  it("distinguishes same nonempty title and state runs by public task id in name and visible id", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const sharedTitle = "同名运行任务 · 共享标题";
    const runA = { ...httpRun("task-collision-a"), title: sharedTitle, state: "QUEUED", status: "QUEUED" };
    const runB = { ...httpRun("task-collision-b"), title: sharedTitle, state: "QUEUED", status: "QUEUED" };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [runA, runB] });
      if (url.endsWith("/api/runs/task-collision-a")) return jsonResponse(runA);
      if (url.endsWith("/api/runs/task-collision-b")) return jsonResponse(runB);
      return jsonResponse({ error: "not found" }, 404);
    }));

    renderWithProviders(<RunsPage />);

    const headingA = await screen.findByTestId("run-heading-task-collision-a");
    const headingB = screen.getByTestId("run-heading-task-collision-b");
    // The meaningful public title stays primary and identical for both rows.
    expect(headingA.textContent).toBe(sharedTitle);
    expect(headingB.textContent).toBe(sharedTitle);

    // A readable secondary visible identifier exposes each distinct public id.
    const idA = screen.getByTestId("run-task-id-task-collision-a");
    const idB = screen.getByTestId("run-task-id-task-collision-b");
    expect(idA.textContent).toContain("task-collision-a");
    expect(idB.textContent).toContain("task-collision-b");
    expect(idA.textContent).not.toStrictEqual(idB.textContent);

    // Accessible toggle names retain state and are distinguished by the full id.
    const labelA = screen.getByTestId("run-toggle-task-collision-a").getAttribute("aria-label") ?? "";
    const labelB = screen.getByTestId("run-toggle-task-collision-b").getAttribute("aria-label") ?? "";
    expect(labelA).not.toStrictEqual(labelB);
    expect(labelA).toContain("task-collision-a");
    expect(labelB).toContain("task-collision-b");
    expect(labelA).toContain("QUEUED");
    expect(labelB).toContain("QUEUED");
  });

  it("renders a long public task id verbatim and expands the run by keyboard", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const longId = "task-1790522355226-9393a716c142-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const run = { ...httpRun(longId), title: "长 ID 运行任务" };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [run] });
      if (url.endsWith(`/api/runs/${longId}`)) return jsonResponse(run);
      return jsonResponse({ error: "not found" }, 404);
    }));

    const user = userEvent.setup();
    renderWithProviders(<RunsPage />);

    const idElement = await screen.findByTestId(`run-task-id-${longId}`);
    // The full public id is present as text (not truncated to empty); actual
    // wrapping/overflow is supervisor-verified in a real browser viewport.
    expect(idElement.textContent).toContain(longId);

    const toggle = screen.getByTestId(`run-toggle-${longId}`);
    expect(toggle.getAttribute("aria-label") ?? "").toContain(longId);

    toggle.focus();
    expect(document.activeElement).toBe(toggle);
    await user.keyboard("{Enter}");
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const region = await screen.findByTestId(`run-detail-${longId}`);
    expect(region).toHaveAttribute("role", "region");
    await user.keyboard("{Enter}");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByTestId(`run-detail-${longId}`)).not.toBeInTheDocument();
  });

  it("does not render a separate visible id when the empty-title fallback already shows it", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    const emptyRun = { ...httpRun("task-no-redundant-id"), title: "" };
    const whitespaceRun = { ...httpRun("task-no-redundant-id-ws"), title: "   \t  " };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/runs")) return jsonResponse({ runs: [emptyRun, whitespaceRun] });
      return jsonResponse({ error: "not found" }, 404);
    }));

    renderWithProviders(<RunsPage />);

    const emptyHeading = await screen.findByTestId("run-heading-task-no-redundant-id");
    expect(emptyHeading.textContent).toBe("任务 task-no-redundant-id · 标题暂不可用");
    // No redundant separate visible id: the fallback heading already carries it.
    expect(screen.queryByTestId("run-task-id-task-no-redundant-id")).not.toBeInTheDocument();

    const wsHeading = screen.getByTestId("run-heading-task-no-redundant-id-ws");
    expect(wsHeading.textContent).toBe("任务 task-no-redundant-id-ws · 标题暂不可用");
    expect(screen.queryByTestId("run-task-id-task-no-redundant-id-ws")).not.toBeInTheDocument();
  });
});

it.each([
  ["UNVERIFIED", false, "功能尚未验证"], ["FIXTURE_VERIFIED", false, "仅测试夹具通过"], ["FAILED", false, "功能检查未通过"],
])("renders Run %s functional evidence without promoting legacy zero-exit SUCCESS", async (status, verified, label) => {
  vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
  const run = { ...httpRun("functional-run"), status: "READY_FOR_REVIEW", state: "READY_FOR_REVIEW", executor_kind: "opencode",
    validation: { command_id: "approved_functional_checks", status: "SUCCESS", exit_code: 0,
      functional: { status, verified, contract_digest: "a".repeat(64) } } };
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => jsonResponse(String(input).endsWith("/api/runs") ? { runs: [run] } : run)));
  renderWithProviders(<RunsPage />);
  await userEvent.setup().click(await screen.findByTestId("run-toggle-functional-run"));
  expect(await screen.findByText(label)).toBeInTheDocument();
  expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
  expect(screen.queryByTestId("run-validation-functional-run")).not.toBeInTheDocument();
});
