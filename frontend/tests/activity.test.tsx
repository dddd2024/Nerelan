import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
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
  it("renders all events from semantic fields", () => {
    renderWithProviders(<ActivityStream events={events} />);
    expect(screen.getByText("执行器运行中")).toBeInTheDocument();
    expect(screen.getByText("等待人工处理")).toBeInTheDocument();
    expect(screen.getByText("已启动。")).toBeInTheDocument();
    expect(screen.getByText("等待审查。")).toBeInTheDocument();
  });

  it("never renders a raw executor log or expand toggle", () => {
    renderWithProviders(<ActivityStream events={events} />);
    expect(screen.queryByTestId("raw-log-e1")).not.toBeInTheDocument();
    expect(screen.queryByTestId("raw-toggle-e1")).not.toBeInTheDocument();
    expect(screen.queryByTestId("raw-log-e2")).not.toBeInTheDocument();
    expect(screen.queryByTestId("raw-toggle-e2")).not.toBeInTheDocument();
  });
});
