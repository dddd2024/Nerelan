import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { ActivityStream } from "@/components/activity-stream";
import type { ActivityEvent } from "@/types";

const source: ActivityEvent[] = [
  { id: "step-1", type: "WORKSPACE_READY", timestamp: "2026-10-18T08:00:00Z",
    title: "工作区就绪", description: "", expanded: false },
  { id: "step-2", type: "EXECUTOR_RUNNING", timestamp: "2026-10-18T08:01:00Z",
    title: "Agent 正在执行", description: "", expanded: false },
  { id: "step-3", type: "EXECUTOR_PROGRESS", timestamp: "2026-10-18T08:02:00Z",
    title: "Codex activity", description: "Read actual project files",
    rawLog: "tool command completed", expanded: false },
  { id: "step-4", type: "EXECUTOR_COMPLETED", timestamp: "2026-10-18T08:03:00Z",
    title: "Agent response", description: "Cannot access workspace; task blocked",
    expanded: false },
];

beforeEach(() => localStorage.clear());

describe("three levels of truthful task activity", () => {
  it("defaults to standard and shows source-backed Agent messages in original language", () => {
    renderWithProviders(<ActivityStream events={source} />);
    expect(screen.getByTestId("activity-density-standard")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Read actual project files")).toBeInTheDocument();
    expect(screen.getByText("Cannot access workspace; task blocked")).toBeInTheDocument();
    expect(screen.getByText("工作区就绪")).toBeInTheDocument();
  });

  it("brief mode shows only the last three actual events without fabricating a summary", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ActivityStream events={source} />);
    await user.click(screen.getByTestId("activity-density-brief"));
    expect(screen.queryByText("工作区就绪")).not.toBeInTheDocument();
    expect(screen.getByText("Read actual project files")).toBeInTheDocument();
    expect(screen.getByText("最近 2 / 4 条")).toBeInTheDocument();
  });

  it("brief mode keeps an earlier failure that recent chatter would otherwise hide", async () => {
    const user = userEvent.setup();
    const activity: ActivityEvent[] = [
      { ...source[0], id: "early-failure", title: "工具调用失败", description: "Workspace unavailable" },
      ...source.slice(0, 3).map((event, i) => ({
        ...event, id: `later-${i}`, type: "EXECUTOR_PROGRESS" as const,
        title: "Codex activity", description: `Reading file ${i}`,
      })),
    ];
    renderWithProviders(<ActivityStream events={activity} />);
    await user.click(screen.getByTestId("activity-density-brief"));
    expect(screen.getByText("工具调用失败")).toBeInTheDocument();
    expect(screen.getByText("Reading file 2")).toBeInTheDocument();
    expect(screen.getByText("最近 3 / 4 条")).toBeInTheDocument();
  });

  it("detail mode exposes observed event provenance, without changing underlying event data", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ActivityStream events={source} />);
    await user.click(screen.getByTestId("activity-density-detail"));
    expect(screen.getByTestId("event-source-step-3")).toHaveTextContent("EXECUTOR_PROGRESS · step-3");
    expect(screen.queryByTestId("raw-log-step-3")).not.toBeInTheDocument();
    await user.click(screen.getByTestId("raw-toggle-step-3"));
    expect(screen.getByTestId("raw-log-step-3")).toHaveTextContent("tool command completed");
    expect(screen.getByText("完整事件日志")).toBeInTheDocument();
  });

  it("keeps the preference when the activity view remounts for a different task", async () => {
    const user = userEvent.setup();
    const first = renderWithProviders(<ActivityStream events={source} />);
    await user.click(screen.getByTestId("activity-density-brief"));
    first.unmount();
    renderWithProviders(<ActivityStream events={source.slice(-1)} />);
    expect(screen.getByTestId("activity-density-brief")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("最近 1 / 1 条")).toBeInTheDocument();
  });
});
