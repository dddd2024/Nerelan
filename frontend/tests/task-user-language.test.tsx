import { afterEach, describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { FunctionalValidationView } from "@/components/functional-validation";
import { TaskCard } from "@/components/task-card";
import { functionalStatusLabel } from "@/lib/functional-validation";
import { permissionModeLabel } from "@/lib/format";
import { taskActionCopy, taskBlockerCopy, taskReviewNotice } from "@/lib/task-status-copy";
import { taskCopy, uiLocale, UI_LOCALE_STORAGE_KEY, UI_LOCALES } from "@/lib/ui-locale";
import type { Task } from "@/types";

afterEach(() => {
  window.localStorage.removeItem(UI_LOCALE_STORAGE_KEY);
  document.documentElement.lang = "zh-CN";
});

const HAN = /[一-鿿]/;

function strings(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (typeof value === "function") return [String((value as (...args: unknown[]) => unknown)("X", 1, 1, 0, 0))];
  if (value && typeof value === "object") return Object.values(value).flatMap(strings);
  return [];
}

describe("task copy follows one locale switch (#1200)", () => {
  it("defaults to the document language and honours an explicit stored preference", () => {
    document.documentElement.lang = "zh-CN";
    expect(uiLocale()).toBe("zh-CN");
    document.documentElement.lang = "en-US";
    expect(uiLocale()).toBe("en");
    window.localStorage.setItem(UI_LOCALE_STORAGE_KEY, "zh-CN");
    expect(uiLocale()).toBe("zh-CN");
    window.localStorage.setItem(UI_LOCALE_STORAGE_KEY, "fr");
    expect(uiLocale()).toBe("en");
  });

  it("keeps the two catalogues complete and free of mixed fixed strings", () => {
    const zh = strings(taskCopy("zh-CN"));
    const en = strings(taskCopy("en"));
    expect(zh.length).toBe(en.length);
    for (const text of en) expect(text).not.toMatch(HAN);
    for (const locale of UI_LOCALES) {
      expect(strings(taskCopy(locale)).every((text) => text.trim().length > 0)).toBe(true);
    }
  });

  it("renders status, action and blocker copy in English without changing raw codes", () => {
    expect(taskActionCopy("Investigate failure classification", "en")).toBe("Review why the task failed and its run history");
    expect(taskBlockerCopy("planner_failed:opencode_timeout:840", "en")).toContain("timed out while planning");
    expect(taskBlockerCopy("upstream_unknown_reason", "en")).toBe("upstream_unknown_reason");
    expect(taskReviewNotice("en")).not.toMatch(HAN);
    expect(functionalStatusLabel("UNVERIFIED", "en")).toBe("Testing not finished");
  });

  it("uses the owner-specified timeout sentence in Chinese", () => {
    expect(taskBlockerCopy("planner_failed:opencode_timeout:840", "zh-CN"))
      .toBe("Agent 在规划阶段超时；可以查看执行记录和阻塞原因");
  });
});

describe("missing functional evidence is an honest, short non-success", () => {
  it("shows the user-facing heading and keeps the proof policy inside 验证详情", () => {
    render(<FunctionalValidationView evidence={undefined} executor="codex" locale="zh-CN" />);
    const section = screen.getByRole("region", { name: "功能验证" });
    expect(within(section).getByText("尚未完成测试")).toBeVisible();
    expect(within(section).getByText("尚无足够的功能测试结果证明修改有效。")).toBeVisible();
    expect(screen.getByTestId("functional-next-action")).toHaveTextContent("在目标计划中选择功能检查");
    const details = screen.getByTestId("functional-validation-details");
    expect(details).not.toHaveAttribute("open");
    expect(within(details).getByText(/退出码 0 不能单独证明功能通过/)).toBeInTheDocument();
    expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
  });

  it("does not offer a fake action once checks were contracted but results are missing", () => {
    render(<FunctionalValidationView evidence={{ status: "UNVERIFIED", contract_digest: "a".repeat(64), reason: "stale" }} executor="codex" locale="en" />);
    expect(screen.getByText("Testing not finished")).toBeInTheDocument();
    expect(screen.getByTestId("functional-next-action")).toHaveTextContent("Waiting for usable verification results");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText("stale")).toBeInTheDocument();
  });

  it("never promotes git diff --check style exit 0 without a bound report", () => {
    render(<FunctionalValidationView evidence={{ status: "VERIFIED", verified: true, checks: [{ profile_id: "python_pytest", working_directory: ".", exit_code: 0, timed_out: false }] }} executor="codex" locale="zh-CN" />);
    expect(screen.getByText("尚未完成测试")).toBeInTheDocument();
    expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
  });
});

it("keeps per-check exit codes and counts inside the collapsed details", () => {
  render(<FunctionalValidationView evidence={{ status: "FAILED", checks: [{ profile_id: "npm_test", working_directory: "frontend", exit_code: 1, timed_out: false,
    test_report: { format: "tap", tests: 2, passed: 1, failed: 1, skipped: 0 } }] }} executor="codex" locale="zh-CN" />);
  const details = screen.getByTestId("functional-validation-details");
  expect(within(details).getByText("退出码：1")).toBeInTheDocument();
  expect(within(details).getByText("共 2 项 · 通过 1 · 失败 1 · 跳过 0")).toBeInTheDocument();
  expect(screen.getByText("测试未通过")).toBeInTheDocument();
});

describe("task list rows", () => {
  const task: Task = {
    id: "t-1", title: "Fix login", state: "FAILED_TERMINAL", riskTier: "UNKNOWN", permissionProfile: "ASK_FOR_APPROVAL",
    branch: "fix/login", repository: "dddd2024/Nerelan", updatedAt: "2026-10-20T00:00:00Z",
    blocker: "planner_failed:opencode_timeout:840", nextAction: "Investigate failure classification",
  } as Task;

  it("does not label the permission mode as a pending approval request", () => {
    expect(permissionModeLabel("ASK_FOR_APPROVAL")).toBe("操作前询问");
    render(<MemoryRouter><TaskCard task={task} /></MemoryRouter>);
    expect(screen.queryByText("请求批准")).not.toBeInTheDocument();
    expect(screen.getByText("操作前询问")).toBeInTheDocument();
  });

  it("shows product copy for the blocker and keeps the exact raw code in the tooltip", () => {
    render(<MemoryRouter><TaskCard task={task} /></MemoryRouter>);
    const note = screen.getByText("Agent 在规划阶段超时；可以查看执行记录和阻塞原因");
    expect(note).toHaveAttribute("title", "planner_failed:opencode_timeout:840");
    expect(screen.queryByText("Investigate failure classification")).not.toBeInTheDocument();
  });
});
