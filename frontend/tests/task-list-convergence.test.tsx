import { act, cleanup, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Task } from "@/types";
import {
  TASK_LIST_REFRESH_INTERVAL_MS,
  TasksPage,
} from "@/routes/tasks";
import { renderWithProviders } from "./test-utils";

const taskQuery = vi.hoisted(() => ({
  data: [] as unknown[],
  refetch: vi.fn(() => Promise.resolve({})),
}));

vi.mock("@/hooks/use-tasks", () => ({
  useTasks: () => ({
    data: taskQuery.data,
    isLoading: false,
    isError: false,
    error: null,
    refetch: taskQuery.refetch,
  }),
}));

function makeTask(state: Task["state"]): Task {
  return {
    id: "task-281",
    title: "Converge visible runtime state",
    issueNumber: 281,
    state,
    riskTier: "R1",
    updatedAt: "2026-09-02T10:00:00Z",
    permissionProfile: "ASK_FOR_APPROVAL",
    branch: "owner/issue281-task-list-convergence-r1-v1",
    activity: [],
    changes: [],
    evidence: [],
    authorityStatus: "APPROVED",
    testStatus: "PENDING",
    workflowStatus: "PENDING",
    repository: "dddd2024/Nerelan",
  };
}

function expectSectionCount(testId: string, count: number) {
  expect(
    within(screen.getByTestId(testId)).getByText(`(${count})`),
  ).toBeInTheDocument();
}

describe("TasksPage authoritative task-state convergence", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    taskQuery.refetch.mockClear();
    taskQuery.data = [];
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("polls while a visible task is running, then stops after Owner-attention truth arrives", () => {
    taskQuery.data = [makeTask("RUNNING")];
    const view = renderWithProviders(<TasksPage />, { initialEntries: ["/tasks"] });

    expectSectionCount("section-running", 1);
    expectSectionCount("section-needs-attention", 0);

    act(() => {
      vi.advanceTimersByTime(TASK_LIST_REFRESH_INTERVAL_MS);
    });
    expect(taskQuery.refetch).toHaveBeenCalledTimes(1);

    taskQuery.data = [makeTask("READY_FOR_HUMAN")];
    view.rerender(<TasksPage />);

    expectSectionCount("section-running", 0);
    expectSectionCount("section-needs-attention", 1);

    taskQuery.refetch.mockClear();
    act(() => {
      vi.advanceTimersByTime(TASK_LIST_REFRESH_INTERVAL_MS * 2);
    });
    expect(taskQuery.refetch).not.toHaveBeenCalled();
  });

  it("moves a failed terminal task out of Running and leaves high-frequency polling stopped", () => {
    taskQuery.data = [makeTask("RUNNING")];
    const view = renderWithProviders(<TasksPage />, { initialEntries: ["/tasks"] });

    taskQuery.data = [makeTask("FAILED_TERMINAL")];
    view.rerender(<TasksPage />);

    expectSectionCount("section-running", 0);
    expectSectionCount("section-recent", 1);

    taskQuery.refetch.mockClear();
    act(() => {
      vi.advanceTimersByTime(TASK_LIST_REFRESH_INTERVAL_MS * 2);
    });
    expect(taskQuery.refetch).not.toHaveBeenCalled();
  });

  it("reconciles authoritative task truth on focus, reconnect, and visibility changes", () => {
    taskQuery.data = [makeTask("READY_FOR_HUMAN")];
    renderWithProviders(<TasksPage />, { initialEntries: ["/tasks"] });

    taskQuery.refetch.mockClear();
    act(() => window.dispatchEvent(new Event("focus")));
    act(() => window.dispatchEvent(new Event("online")));
    act(() => document.dispatchEvent(new Event("visibilitychange")));

    expect(taskQuery.refetch).toHaveBeenCalledTimes(3);

    taskQuery.refetch.mockClear();
    act(() => {
      vi.advanceTimersByTime(TASK_LIST_REFRESH_INTERVAL_MS * 2);
    });
    expect(taskQuery.refetch).not.toHaveBeenCalled();
  });

  it("keeps the last authoritative state when a background reconciliation fails", async () => {
    taskQuery.data = [makeTask("RUNNING")];
    taskQuery.refetch.mockRejectedValueOnce(new Error("transient refresh failure"));
    renderWithProviders(<TasksPage />, { initialEntries: ["/tasks"] });

    await act(async () => {
      vi.advanceTimersByTime(TASK_LIST_REFRESH_INTERVAL_MS);
      await Promise.resolve();
    });

    expectSectionCount("section-running", 1);
    expectSectionCount("section-needs-attention", 0);
  });
});
