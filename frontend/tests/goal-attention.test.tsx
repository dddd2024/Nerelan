import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { GoalAttention, failureText, modelName } from "@/components/goal-attention";
import { collapseRepeats } from "@/components/goal-current-activity";
import type { PlatformGoal, PlatformGoalTaskLink, PlatformRunActivityEvent } from "@/lib/platform-client";

function goal(links: PlatformGoalTaskLink[]): PlatformGoal {
  return { id: "goal-1", task_links: links } as unknown as PlatformGoal;
}

const base: PlatformGoalTaskLink = {
  task_id: "task-2", plan_task_id: "T001", status: "RUNNING", title: "在 README 末尾加一行",
  executor_kind: "opencode", binding_ref: "magpie-opencode-zen-free-deepseek-v4.1-flash-free",
};

describe("GoalAttention", () => {
  it("says what the agent is doing now", () => {
    render(<MemoryRouter><GoalAttention goal={goal([{ ...base, activity: {
      type: "EXECUTOR_PROGRESS", title: "OpenCode", description: "read README.md", timestamp: new Date().toISOString(),
    } }])} /></MemoryRouter>);
    expect(screen.getByTestId("goal-now-task-2")).toHaveTextContent("正在做：read README.md");
    expect(screen.getByTestId("goal-now-task-2")).toHaveTextContent("deepseek-v4.1-flash-free");
  });

  it("explains a stall in plain language with the host's own words and earlier attempts", () => {
    render(<MemoryRouter><GoalAttention goal={goal([{ ...base, status: "FAILED",
      failure: { classification: "executor_stalled", detail: "durable sequential team failed:planner_failed:opencode_stalled:900",
        message: "OpenCode stalled: OpenCode CLI wrote nothing for too long (often a provider 429 it waits out)" },
      attempts: [{ task_id: "task-1", status: "FAILED", executor_kind: "opencode", binding_ref: "magpie-codex-gpt-6.1-sol",
        failure: { classification: "deterministic_validation_failure", detail: "functional_check_failed", message: "" } }],
    }])} /></MemoryRouter>);
    const card = screen.getByTestId("goal-stopped-task-2");
    expect(card).toHaveTextContent("为什么停下：Agent 长时间没有任何输出，已被停止");
    expect(card).toHaveTextContent("下一步：最常见的原因是模型被限流（429）");
    expect(screen.getByTestId("goal-stopped-detail-task-2")).toHaveTextContent("often a provider 429");
    const attempts = screen.getByTestId("goal-attempts-task-2");
    expect(attempts).toHaveTextContent("第 1 次：OpenCode · codex-gpt-6.1-sol — 功能检查没有通过");
    expect(attempts).toHaveTextContent("第 2 次（本次）");
    expect(card).not.toHaveTextContent("task_unsuccessful");
  });

  it("renders nothing for queued or finished-for-review work", () => {
    const { container } = render(<MemoryRouter><GoalAttention goal={goal([{ ...base, status: "READY_FOR_REVIEW" }])} /></MemoryRouter>);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("failure wording", () => {
  it("prefers a specific code found in the detail and never shows a bare class as the label", () => {
    expect(failureText({ classification: "executor_nonzero", detail: "x", message: "" }).label).toBe("执行器异常退出");
    expect(failureText({ classification: "something_new", detail: "", message: "m" }).label).toBe("已停止");
    expect(modelName("magpie-codex-gpt-6.1-sol")).toBe("codex-gpt-6.1-sol");
  });
});

describe("collapseRepeats", () => {
  it("merges adjacent rows that say the same thing", () => {
    const row = (id: string, title: string, description = "") => ({
      key: id, event: { id, title, category: "AGENT_STARTED", description } as PlatformRunActivityEvent,
    });
    const rows = collapseRepeats([row("1", "Agent started"), row("2", "Agent started"), row("3", "Agent started", "read a.py"), row("4", "Agent started")]);
    expect(rows.map((r) => r.repeats)).toEqual([2, 1, 1]);
  });
});
