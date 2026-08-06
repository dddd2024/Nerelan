import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { ActivityStream } from "@/components/activity-stream";
import type { ActivityEvent } from "@/types";

const events: ActivityEvent[] = [
  {
    id: "e1",
    type: "EXECUTOR_RUNNING",
    timestamp: "2026-08-05T03:00:00Z",
    title: "执行器运行中",
    description: "已启动。",
    rawLog: "executor: started\nexecutor: step 1",
    expanded: false,
  },
  {
    id: "e2",
    type: "READY_FOR_HUMAN",
    timestamp: "2026-08-05T04:00:00Z",
    title: "等待人工处理",
    description: "等待审查。",
    expanded: false,
  },
];

describe("activity stream", () => {
  it("renders all events", () => {
    renderWithProviders(<ActivityStream events={events} />);
    expect(screen.getByText("执行器运行中")).toBeInTheDocument();
    expect(screen.getByText("等待人工处理")).toBeInTheDocument();
  });

  it("raw logs are collapsed by default and expandable", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ActivityStream events={events} />);
    // Raw log not present initially.
    expect(screen.queryByTestId("raw-log-e1")).not.toBeInTheDocument();
    const toggle = screen.getByTestId("raw-toggle-e1");
    await user.click(toggle);
    expect(screen.getByTestId("raw-log-e1")).toBeInTheDocument();
    expect(screen.getByTestId("raw-log-e1").textContent).toContain("executor: started");
  });

  it("events without raw logs do not show a toggle", () => {
    renderWithProviders(<ActivityStream events={events} />);
    expect(screen.queryByTestId("raw-toggle-e2")).not.toBeInTheDocument();
  });
});
