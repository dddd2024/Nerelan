import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { TaskCard } from "@/components/task-card";
import { TaskInbox } from "@/components/task-inbox";
import { ActivityStream } from "@/components/activity-stream";
import { ChangesPanel } from "@/components/changes-panel";
import { EvidencePanel } from "@/components/evidence-panel";
import type { Task } from "@/types";

const FIXTURE_TASK: Task = {
  id: "task-1723000000000-abcdef123456",
  title: "Provider-free fixture task",
  issueNumber: 128,
  state: "READY_FOR_HUMAN",
  riskTier: "R1",
  updatedAt: "2026-08-07T00:00:00Z",
  permissionProfile: "ASK_FOR_APPROVAL",
  branch: "task-1723000000000-abcdef123456",
  repository: "dddd2024/reverse-agent",
  executionId: "exec-task-1723000000000-abcdef123456",
  executor: "fixture/provider-free",
  validationCommandId: "git_diff_check",
  validationExitCode: 0,
  activity: [
    {
      id: "e-discovered",
      type: "DISCOVERED",
      timestamp: "2026-08-07T00:00:00Z",
      title: "Task queued",
      description: "Task created for dddd2024/reverse-agent",
      expanded: false,
    },
    {
      id: "e-workspace",
      type: "WORKSPACE_READY",
      timestamp: "2026-08-07T00:00:01Z",
      title: "Workspace ready",
      description: "Disposable worktree created",
      expanded: false,
    },
    {
      id: "e-executor",
      type: "EXECUTOR_RUNNING",
      timestamp: "2026-08-07T00:00:02Z",
      title: "Executor running",
      description: "Executor deterministic_fixture started",
      expanded: false,
    },
    {
      id: "e-validated",
      type: "VALIDATED",
      timestamp: "2026-08-07T00:00:03Z",
      title: "Validation passed",
      description: "git_diff_check passed",
      expanded: false,
    },
  ],
  changes: [
    {
      path: "fixture.txt",
      status: "modified",
      additions: 1,
      deletions: 0,
      diff: "+deterministic mutation applied",
    },
  ],
  evidence: [
    {
      id: "ev-1",
      category: "Validation",
      label: "git_diff_check",
      value: "0",
      status: "pass",
      detail: "deterministic fixture validation passed",
      rawJson: "deadbeef",
    },
    {
      id: "ev-2",
      category: "Executor",
      label: "executor_kind",
      value: "deterministic_fixture",
      status: "pass",
      detail: "fixture/provider-free executor",
      rawJson: "",
    },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PASS",
  workflowStatus: "PENDING",
};

const BLOCKED_TASK: Task = {
  ...FIXTURE_TASK,
  id: "task-blocked-001",
  title: "Blocked fixture task",
  state: "BLOCKED_EXTERNAL",
  blocker: "workspace_root_required",
  failureClassification: "blocked",
  testStatus: "FAIL",
  workflowStatus: "FAILURE",
  activity: [
    ...FIXTURE_TASK.activity,
    {
      id: "e-failed",
      type: "EXECUTOR_FINISHED",
      timestamp: "2026-08-07T00:00:04Z",
      title: "Executor failed",
      description: "failure_classification=blocked",
      expanded: false,
    },
  ],
  evidence: [
    ...FIXTURE_TASK.evidence,
    {
      id: "ev-3",
      category: "Failure",
      label: "failure_classification",
      value: "blocked",
      status: "fail",
      detail: "workspace_root_required",
    },
  ],
};

describe("provider-free task plane integration", () => {
  it("task-card shows fixture/provider-free executor badge", () => {
    renderWithProviders(
      <TaskCard task={FIXTURE_TASK} />,
    );
    expect(screen.getByTestId("task-executor-badge")).toBeInTheDocument();
    expect(
      screen.getByText((content) =>
        content.includes("fixture / provider-free") ||
        content.includes("deterministic_fixture"),
      ),
    ).toBeInTheDocument();
  });

  it("task-inbox places ready-for-human tasks in needs-attention", () => {
    renderWithProviders(
      <TaskInbox tasks={[FIXTURE_TASK, BLOCKED_TASK]} isLoading={false} isError={false} />,
    );
    expect(screen.getByTestId("section-needs-attention")).toBeInTheDocument();
    expect(
      screen.getByTestId(`task-card-${FIXTURE_TASK.id}`),
    ).toBeInTheDocument();
  });

  it("activity-stream renders provider-free lifecycle events", () => {
    renderWithProviders(<ActivityStream events={FIXTURE_TASK.activity} />);
    expect(screen.getByText("Task queued")).toBeInTheDocument();
    expect(screen.getByText("Workspace ready")).toBeInTheDocument();
    expect(screen.getByText("Validation passed")).toBeInTheDocument();
  });

  it("changes-panel shows fixture changed file", () => {
    renderWithProviders(<ChangesPanel changes={FIXTURE_TASK.changes} />);
    expect(screen.getByText("fixture.txt")).toBeInTheDocument();
  });

  it("evidence-panel shows validation + executor categories", () => {
    renderWithProviders(<EvidencePanel evidence={FIXTURE_TASK.evidence} />);
    expect(screen.getByTestId("evidence-panel")).toBeInTheDocument();
    expect(screen.getByText("Validation")).toBeInTheDocument();
    expect(screen.getByText("Executor")).toBeInTheDocument();
  });

  it("blocked task shows blocker and failure evidence", () => {
    renderWithProviders(
      <TaskInbox tasks={[BLOCKED_TASK]} isLoading={false} isError={false} />,
    );
    expect(
      screen.getByText((content) => content.includes("workspace_root_required")),
    ).toBeInTheDocument();
  });

  it("adapter maps provider-free task fields", () => {
    renderWithProviders(
      <TaskCard
        task={{
          id: "task-adapter",
          title: "Adapter task",
          issueNumber: 0,
          state: "WAITING_FOR_OWNER",
          riskTier: "R1",
          updatedAt: "2026-08-07T00:00:00Z",
          permissionProfile: "ASK_FOR_APPROVAL",
          branch: "task-adapter",
          activity: [],
          changes: [],
          evidence: [],
          authorityStatus: "APPROVED",
          testStatus: "PENDING",
          workflowStatus: "PENDING",
          executor: "fixture/provider-free",
          repository: "dddd2024/reverse-agent",
          executionId: "exec-task-adapter",
        }}
      />,
    );
    expect(
      screen.getByTestId("task-card-task-adapter"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("task-executor-badge")).toBeInTheDocument();
  });
});
