import { describe, expect, it } from "vitest";
import { displayTitle } from "@/lib/display-title";
import { cleanIssueTitle, goalState, goalTitle, humanActivity, humanCommand, issueRef, objectiveText, stepTitle } from "@/lib/goal-view";
import { tidyDetail } from "@/lib/run-explain";
import type { PlatformGoal, PlatformGoalTaskLink } from "@/lib/platform-client";

const ISSUE_OBJECTIVE = "Resolve https://github.com/dddd2024/Nerelan/issues/1488 # [Runtime] Detect provider 429 in OpenCode output ## Problem When a provider answers with `HTTP 429`, OpenCode keeps waiting. ## Change - Recognise **rate-limit** signals - Stop after a grace period";

function goal(overrides: Partial<PlatformGoal> = {}): PlatformGoal {
  return {
    id: "goal-1", title: "#1488 [Runtime] Detect provider 429 in OpenCode output", objective: ISSUE_OBJECTIVE,
    repository: "dddd2024/Nerelan", status: "RUNNING", revision: 1, spec_markdown: "", plan_markdown: "", tasks: [],
    acceptance_criteria: [], artifact_digest: "", executor_kind: "opencode", orchestration_mode: "agent_team",
    binding_ref: "", window_id: "", created_at: "2026-11-13T00:00:00Z", updated_at: "2026-11-13T00:00:00Z",
    ...overrides,
  } as PlatformGoal;
}

function link(status: string, extra: Partial<PlatformGoalTaskLink> = {}): PlatformGoalTaskLink {
  return { task_id: `t-${status}`, plan_task_id: "implement", status, title: "x", ...extra };
}

describe("titles", () => {
  it("keeps a nested bracket goal title whole", () => {
    expect(displayTitle("[#1488 [Runtime] Detect provider 429] implement Implement #1488\n\nFollow the Goal objective."))
      .toBe("#1488 [Runtime] Detect provider 429");
  });

  it("drops the issue number and tracker tags", () => {
    expect(cleanIssueTitle("#1492 [Owner window D06] Terminal start: retry a mistyped code")).toBe("Terminal start: retry a mistyped code");
    expect(goalTitle(goal())).toBe("Detect provider 429 in OpenCode output");
    expect(cleanIssueTitle("[Runtime]")).toBe("[Runtime]");
    expect(goalTitle(goal({ title: "完善无人值守多 Agent 平台" }))).toBe("完善无人值守多 Agent 平台");
  });

  it("finds the issue from the objective or the title", () => {
    expect(issueRef(goal())).toEqual({ number: 1488, url: "https://github.com/dddd2024/Nerelan/issues/1488" });
    expect(issueRef(goal({ objective: "free text" }))?.number).toBe(1488);
    expect(issueRef(goal({ title: "plain", objective: "free text" }))).toBeNull();
  });

  it("turns an issue objective into prose", () => {
    const text = objectiveText(goal());
    expect(text.startsWith("Problem When a provider answers with HTTP 429")).toBe(true);
    expect(text).not.toContain("https://");
    expect(text).not.toContain("##");
    expect(text).toContain("· Recognise rate-limit signals");
  });

  it("names plan steps by role", () => {
    expect(stepTitle("[#1488 [Runtime] Detect] implement Implement #1488\n\nFollow")).toBe("实现");
    expect(stepTitle("[#1488 [Runtime] Detect] review Review #1488")).toBe("审查");
    expect(stepTitle("实现上传逻辑修复", "coder")).toBe("实现上传逻辑修复");
    expect(stepTitle("Implement #1336", "coder")).toBe("实现");
    expect(stepTitle("", "reviewer")).toBe("审查");
    expect(stepTitle("整理发布说明")).toBe("整理发布说明");
  });
});

describe("goal state", () => {
  it("has one state per goal", () => {
    expect(goalState(goal({ status: "PLANNED" }))).toMatchObject({ key: "needs_you", label: "待审阅" });
    expect(goalState(goal({ task_links: [link("RUNNING", { activity: { type: "x", title: "OpenCode", description: "bash python -m pytest -q tests/a.py", timestamp: "" } })] })))
      .toMatchObject({ key: "running", group: "active", detail: "正在跑测试" });
    expect(goalState(goal({ task_links: [link("QUEUED"), link("QUEUED")] }))).toMatchObject({ key: "queued", detail: "已完成 0/2 步，等待执行" });
    expect(goalState(goal({ task_links: [link("FAILED", { failure: { classification: "MODEL_REFUSED", detail: "", message: "" } })] })))
      .toMatchObject({ key: "stopped", group: "stopped" });
    // A BLOCKED goal with a stale RUNNING link still reads as stopped.
    expect(goalState(goal({ status: "BLOCKED", task_links: [link("FAILED"), link("RUNNING")] }))).toMatchObject({ key: "stopped" });
    expect(goalState(goal({ status: "BLOCKED", task_links: [link("CANCELLED"), link("CANCELLED")] })))
      .toMatchObject({ key: "cancelled", group: "ended", label: "已取消" });
    expect(goalState(goal({ status: "COMPLETED", task_links: [link("READY_FOR_REVIEW"), link("READY_FOR_REVIEW")] })))
      .toMatchObject({ key: "needs_you", label: "待审查" });
  });
});

describe("review findings on #1493", () => {
  it("calls a PR opened only when one was", () => {
    const ready = (publication?: unknown) => goalState(goal({ status: "COMPLETED", task_links: [link("READY_FOR_REVIEW", { publication } as Partial<PlatformGoalTaskLink>)] }));
    expect(ready({ status: "PUSHED", pr_number: 0 }).detail).toBe("执行完成，等你审查结果");
    expect(ready({ status: "COMPLETE", pr_number: 77 }).detail).toBe("已开 Draft PR，等你审查");
  });

  it("keeps dashes inside prose and reads ordinary words", () => {
    expect(objectiveText(goal({ objective: "Use range 1 - 5 here" }))).toBe("Use range 1 - 5 here");
    expect(stepTitle("Add review endpoint")).toBe("Add review endpoint");
    expect(humanActivity({ type: "x", title: "", description: "Read the docs first" })).toBe("Read the docs first");
    expect(humanActivity({ type: "x", title: "", description: "read src/lib/a.ts" })).toBe("正在读 a.ts");
    expect(tidyDetail("printf 'a\\nb'")).toBe("printf 'a\\nb'");
    expect(tidyDetail("type src\\lib\\a.ts")).toBe("type src/lib/a.ts");
  });

  it("puts a blocked goal without steps with the stopped ones", () => {
    expect(goalState(goal({ status: "BLOCKED", task_links: [] }))).toMatchObject({ group: "stopped" });
  });
});

describe("activity in plain words", () => {
  it("reads commands", () => {
    expect(humanCommand("bash python -m pytest -q tests/platform_v1/test_x.py")).toBe("正在跑测试");
    expect(humanCommand("bash Get-Content reverse_agent/platform_v1/opencode_executor.py | Select-Object -First 90")).toBe("正在读 opencode_executor.py");
    expect(humanCommand("bash rg -n stall reverse_agent")).toBe("正在搜索代码");
    expect(humanCommand("bash git status --short")).toBe("正在查看 Git 记录");
    expect(humanCommand("bash npx vitest run")).toBe("正在跑前端测试");
    expect(humanCommand("bash make something")).toBe("正在执行命令");
    expect(humanActivity({ type: "x", title: "OpenCode", description: "Now run the focused tests:" })).toBe("Now run the focused tests:");
  });

  it("shows workspace paths as repository paths", () => {
    expect(tidyDetail("edit F:\\nerelan-run-data\\task_workspaces\\task-1794-d25\\reverse_agent\\platform_v1\\x.py"))
      .toBe("edit reverse_agent/platform_v1/x.py");
    expect(tidyDetail("bash python -m pytest -q tests/x.py")).toBe("python -m pytest -q tests/x.py");
    expect(tidyDetail("cat /tmp/data/task_workspaces/task-abc/src/a.ts")).toBe("cat src/a.ts");
  });
});
