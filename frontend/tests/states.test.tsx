import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { TaskInbox } from "@/components/task-inbox";
import type { Task } from "@/types";

describe("state components", () => {
  it("shows a loading state", () => {
    renderWithProviders(
      <TaskInbox tasks={undefined} isLoading={true} isError={false} />,
    );
    expect(screen.getByTestId("loading-state")).toBeInTheDocument();
  });

  it("shows an empty state when there are no tasks", () => {
    renderWithProviders(
      <TaskInbox tasks={[]} isLoading={false} isError={false} />,
    );
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByText("No tasks")).toBeInTheDocument();
  });

  it("shows an error state", () => {
    renderWithProviders(
      <TaskInbox
        tasks={undefined}
        isLoading={false}
        isError={true}
        error={new Error("boom")}
      />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
  });

  it("renders sections for real tasks", () => {
    const tasks: Task[] = [
      {
        id: "t1",
        title: "T1",
        issueNumber: 1,
        state: "READY_FOR_HUMAN",
        riskTier: "R1",
        updatedAt: "2026-08-05T00:00:00Z",
        permissionProfile: "OWNER_CONTROL",
        branch: "b1",
        activity: [],
        changes: [],
        evidence: [],
        authorityStatus: "APPROVED",
        testStatus: "PASS",
        workflowStatus: "SUCCESS",
      },
    ];
    renderWithProviders(
      <TaskInbox tasks={tasks} isLoading={false} isError={false} />,
    );
    expect(screen.getByTestId("section-needs-attention")).toBeInTheDocument();
  });

  it("LoadingState, EmptyState, ErrorState render standalone", () => {
    renderWithProviders(<LoadingState label="x" />);
    expect(screen.getByTestId("loading-state")).toBeInTheDocument();
    renderWithProviders(<EmptyState title="Nothing" />);
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    renderWithProviders(<ErrorState error="oops" />);
    expect(screen.getByTestId("error-state")).toBeInTheDocument();
  });
});
