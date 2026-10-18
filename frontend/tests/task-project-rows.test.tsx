import { expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { TaskCard } from "@/components/task-card";
import type { Task } from "@/types";

it("shows project membership directly on a task card", () => {
  const task: Task = {
    id: "task-example", title: "Check project navigation", issueNumber: null,
    state: "RUNNING", riskTier: "R1", updatedAt: "2026-10-18T10:00:00Z",
    permissionProfile: "ASK_FOR_APPROVAL", branch: "example",
    activity: [], changes: [], evidence: [], authorityStatus: "MISSING",
    testStatus: "PENDING", workflowStatus: "UNKNOWN", repository: "team/project-a",
  };
  renderWithProviders(<TaskCard task={task} />);
  expect(screen.getByTestId("task-project-task-example")).toHaveTextContent("team/project-a");
  expect(screen.getByRole("link")).toHaveAttribute("href", "/tasks/task-example");
});
