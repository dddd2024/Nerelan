import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { AppShell } from "@/components/app-shell";
import { Sidebar } from "@/components/sidebar";
import { ConversationPanel } from "@/components/conversation-panel";
import { NewTaskComposer } from "@/components/new-task-composer";
import { TaskInbox } from "@/components/task-inbox";
import { TaskDetail } from "@/components/task-detail";
import { Task } from "@/types";

const FIXTURE_TASK: Task = {
  id: "t1",
  title: "PR #114 provider-free closure",
  issueNumber: 114,
  state: "READY_FOR_HUMAN",
  riskTier: "R1",
  updatedAt: "2026-08-05T00:00:00Z",
  permissionProfile: "CONTROLLER_REVIEW",
  branch: "agent/platform-v1-codex-e2e-v1",
  activity: [
    {
      id: "e1",
      timestamp: "2026-08-05T10:00:00Z",
      type: "EXECUTOR_RUNNING",
      title: "Task execution started",
      description: "Starting task execution",
      expanded: false,
    },
  ],
  changes: [
    {
      path: "src/main.py",
      status: "modified",
      additions: 10,
      deletions: 3,
      diff: "@@ -1,3 +1,4 @@\n line\n-removed\n+added\n+added2\n",
    },
  ],
  evidence: [
    {
      id: "ev1",
      category: "tests",
      label: "pytest",
      value: "212 passed",
      status: "pass",
    },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PASS",
  workflowStatus: "SUCCESS",
};

describe("OpenHands-style workspace shell", () => {
  it("app shell has sidebar + workspace + composer dock pattern", () => {
    renderWithProviders(
      <AppShell>
        <div data-testid="workspace-content">content</div>
      </AppShell>,
    );
    expect(screen.getByTestId("app-shell")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-outlet")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-content")).toBeInTheDocument();
  });

  it("sidebar is an icon rail with Nerelan identity and new task entry", () => {
    renderWithProviders(
      <Sidebar
        onNewTask={() => {}}
        onOpenConversationPanel={() => {}}
        onConversationPanelClose={() => {}}
        conversationPanelOpen={false}
      />,
    );
    expect(screen.getByTestId("sidebar")).toHaveAttribute(
      "data-agent-canvas-source",
      "v1.6.1",
    );
    expect(screen.getByTestId("sidebar")).toHaveAttribute(
      "data-presentation-boundary",
      "slot-adapter",
    );
    expect(screen.getByTestId("sidebar-logo")).toBeInTheDocument();
    expect(screen.getByLabelText("Nerelan")).toBeInTheDocument();
    expect(screen.getByTestId("new-task-button")).toBeInTheDocument();
    expect(screen.getByLabelText("新建任务")).toBeInTheDocument();
    expect(screen.getByTestId("toggle-conversation-panel")).toBeInTheDocument();
    expect(screen.getByLabelText("打开任务列表")).toBeInTheDocument();
  });

  it("sidebar has nav links for home and tasks", () => {
    renderWithProviders(
      <Sidebar
        onNewTask={() => {}}
        onOpenConversationPanel={() => {}}
        onConversationPanelClose={() => {}}
        conversationPanelOpen={false}
      />,
    );
    const homeLink = screen.getByTestId("sidebar-nav-首页");
    expect(homeLink).toHaveAttribute("href", "/");
    const tasksLink = screen.getByTestId("sidebar-nav-任务");
    expect(tasksLink).toHaveAttribute("href", "/tasks");
  });
});

describe("New Task composer with permission selector", () => {
  it("renders task input with permission selector adjacent", () => {
    renderWithProviders(<NewTaskComposer open={true} onClose={() => {}} />);
    expect(screen.getByTestId("new-task-composer")).toBeInTheDocument();
    expect(screen.getByLabelText("权限配置")).toBeInTheDocument();
  });

  it("permission selector shows 4 profiles", async () => {
    const user = userEvent.setup();
    renderWithProviders(<NewTaskComposer open={true} onClose={() => {}} />);
    const trigger = screen.getByLabelText("权限配置");
    expect(trigger).toHaveAttribute("aria-haspopup", "listbox");
    await user.click(trigger);
    expect(screen.getByTestId("permission-option-ASK_FOR_APPROVAL")).toBeInTheDocument();
    expect(screen.getByTestId("permission-option-CONTROLLER_REVIEW")).toBeInTheDocument();
    expect(screen.getByTestId("permission-option-OWNER_CONTROL")).toBeInTheDocument();
    expect(screen.getByTestId("permission-option-CUSTOM")).toBeInTheDocument();
  });

  it("permission selector triggers are keyboard accessible", async () => {
    const user = userEvent.setup();
    renderWithProviders(<NewTaskComposer open={true} onClose={() => {}} />);
    const trigger = screen.getByLabelText("权限配置");
    trigger.focus();
    expect(trigger).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(trigger).toHaveAttribute("aria-expanded", "true");
  });
});

describe("Task inbox (OpenHands HomeScreen adaptation)", () => {
  it("renders loading state", () => {
    renderWithProviders(
      <TaskInbox tasks={undefined} isLoading={true} isError={false} />,
    );
    expect(screen.getByTestId("loading-state")).toBeInTheDocument();
  });

  it("renders empty state with no tasks", () => {
    renderWithProviders(
      <TaskInbox tasks={[]} isLoading={false} isError={false} />,
    );
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });

  it("renders error state", () => {
    renderWithProviders(
      <TaskInbox
        tasks={undefined}
        isLoading={false}
        isError={true}
        error={new Error("fail")}
      />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

describe("Task detail (OpenHands ConversationMain adaptation)", () => {
  it("renders header with title, status dot, and badges", () => {
    renderWithProviders(<TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />);
    expect(screen.getByTestId("task-detail")).toBeInTheDocument();
    expect(screen.getByTestId("resize-handle")).toBeInTheDocument();
  });

  it("renders resizable workspace with activity stream and tab panel", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />);
    expect(screen.getByTestId("desktop-split-container")).toHaveAttribute(
      "data-agent-canvas-source",
      "v1.6.1",
    );
    expect(screen.getByTestId("resize-handle-container")).toHaveAttribute(
      "data-agent-canvas-source",
      "v1.6.1",
    );
    expect(screen.getByTestId("activity-stream")).toBeInTheDocument();
    expect(screen.getByTestId("right-panel-content")).toBeInTheDocument();
    const changesTab = screen.getByTestId("right-tab-changes");
    await user.click(changesTab);
    expect(screen.getByTestId("changes-panel")).toBeInTheDocument();
  });

  it("renders evidence tab with collapsible items", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />);
    const evidenceTab = screen.getByTestId("right-tab-evidence");
    await user.click(evidenceTab);
    expect(screen.getByTestId("evidence-panel")).toBeInTheDocument();
  });

  it("resize handle is keyboard accessible", () => {
    renderWithProviders(<TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />);
    const handle = screen.getByTestId("resize-handle");
    expect(handle).toBeInTheDocument();
    expect(handle.tagName).toBe("DIV");
  });
});

describe("Conversation panel (OpenHands task list overlay)", () => {
  it("renders as overlay panel", () => {
    renderWithProviders(<ConversationPanel open={true} onClose={() => {}} />);
    expect(screen.getByTestId("conversation-panel")).toBeInTheDocument();
  });
});
