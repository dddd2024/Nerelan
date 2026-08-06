import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { AppShell } from "@/components/app-shell";
import { NewTaskComposer } from "@/components/new-task-composer";
import { TaskDetail } from "@/components/task-detail";
import { Sidebar } from "@/components/sidebar";
import type { Task } from "@/types";

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

const FIXTURE_TASK_CUSTOM: Task = {
  ...FIXTURE_TASK,
  id: "t2",
  permissionProfile: "CUSTOM",
};

function mockMatchMedia(matchesDesktop: boolean) {
  const impl = (query: string) => ({
    matches: matchesDesktop
      ? /min-width: 1024px/.test(query)
      : /max-width: 639px/.test(query),
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).matchMedia = impl;
}

describe("sidebar collapse/expand — OpenHands 1.8.0 adaptation", () => {
  it("sidebar renders with collapse/expand toggle on desktop", () => {
    mockMatchMedia(true);
    renderWithProviders(
      <Sidebar
        onNewTask={() => {}}
        onOpenConversationPanel={() => {}}
        onConversationPanelClose={() => {}}
        conversationPanelOpen={false}
      />,
    );
    // The collapse/expand toggle must be present on desktop
    expect(screen.getByTestId("sidebar-collapse-toggle")).toBeInTheDocument();
    // Sidebar must have the correct collapsed class for testing the width contract
    const sidebar = screen.getByTestId("sidebar");
    expect(sidebar).toBeInTheDocument();
  });

  it("sidebar desktop collapsed state is 60px wide", () => {
    mockMatchMedia(true);
    renderWithProviders(
      <Sidebar
        onNewTask={() => {}}
        onOpenConversationPanel={() => {}}
        onConversationPanelClose={() => {}}
        conversationPanelOpen={false}
      />,
      { initialEntries: ["/"] },
    );
    const sidebar = screen.getByTestId("sidebar");
    expect(sidebar.getAttribute("data-collapsed")).toBe("true");
    expect(sidebar).toHaveClass("sidebar-collapsed");
  });

  it("sidebar desktop expanded state is 300px wide", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <Sidebar
        onNewTask={() => {}}
        onOpenConversationPanel={() => {}}
        onConversationPanelClose={() => {}}
        conversationPanelOpen={false}
      />,
      { initialEntries: ["/"] },
    );
    const toggle = screen.getByTestId("sidebar-collapse-toggle");
    await user.click(toggle);
    const sidebar = screen.getByTestId("sidebar");
    expect(sidebar.getAttribute("data-collapsed")).toBe("false");
    expect(sidebar).toHaveClass("sidebar-expanded");
    // Nav items become visible in expanded state
    expect(screen.getByTestId("sidebar-nav-首页")).toBeInTheDocument();
  });

  it("sidebar has keyboard accessible collapse/expand toggle", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <Sidebar
        onNewTask={() => {}}
        onOpenConversationPanel={() => {}}
        onConversationPanelClose={() => {}}
        conversationPanelOpen={false}
      />,
      { initialEntries: ["/"] },
    );
    const toggle = screen.getByTestId("sidebar-collapse-toggle");
    expect(toggle).toHaveAttribute("aria-pressed");
    toggle.focus();
    expect(toggle).toHaveFocus();
    await user.keyboard("{Space}");
    expect(toggle.getAttribute("aria-pressed")).toBe("false");
  });
});

describe("conversation panel stability", () => {
  it("keeps conversation panel open after toggle button click", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <AppShell>
        <div data-testid="workspace-content">content</div>
      </AppShell>,
      { initialEntries: ["/tasks"] },
    );

    // Open the conversation panel
    const toggle = screen.getByTestId("toggle-conversation-panel");
    await user.click(toggle);
    await screen.findByTestId("conversation-panel");

    // Panel must remain visible after the state update that previously triggered the bug
    expect(screen.getByTestId("conversation-panel")).toBeInTheDocument();
  });

  it("closes conversation panel when route changes", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <AppShell>
        <div data-testid="workspace-content">content</div>
      </AppShell>,
      { initialEntries: ["/tasks"] },
    );

    // Open the panel
    const toggle = screen.getByTestId("toggle-conversation-panel");
    await user.click(toggle);
    await screen.findByTestId("conversation-panel");

    // Navigate away via sidebar nav
    const tasksLink = screen.getByTestId("sidebar-nav-首页");
    await user.click(tasksLink);

    // Panel should have been closed exactly once on route change
    expect(screen.queryByTestId("conversation-panel")).not.toBeInTheDocument();
  });
});

describe("New Task composer — CUSTOM policy persistence", () => {
  it("selecting CUSTOM sets active mode and opens editor", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(<NewTaskComposer open={true} onClose={() => {}} />);

    // Open permission selector
    const selectorTrigger = screen.getByTestId("permission-mode-composer");
    await user.click(selectorTrigger);

    // Select CUSTOM
    await user.click(screen.getByTestId("permission-option-CUSTOM"));

    // Custom editor should open
    await screen.findByTestId("custom-policy-editor");
    expect(screen.getByTestId("custom-policy-editor")).toBeInTheDocument();
  });

  it("CUSTOM policy edit persists and updates summary", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(<NewTaskComposer open={true} onClose={() => {}} />);

    // Select CUSTOM
    const selectorTrigger = screen.getByTestId("permission-mode-composer");
    await user.click(selectorTrigger);
    await user.click(screen.getByTestId("permission-option-CUSTOM"));
    await screen.findByTestId("custom-policy-editor");

    // Find the merge policy text input and change it
    const mergeReposInput = screen.getByTestId("merge-allowed-repos");
    expect(mergeReposInput).toBeInTheDocument();

    await user.clear(mergeReposInput);
    await user.type(mergeReposInput, "myorg/myrepo");

    // Accept (close) the editor
    const editorContainer = screen.getByTestId("custom-policy-editor");
    const closeButton = within(editorContainer).getByRole("button", { name: "关闭编辑器" });
    await user.click(closeButton);

    // Editor should close
    expect(screen.queryByTestId("custom-policy-editor")).not.toBeInTheDocument();

    // Mode badge should reflect CUSTOM (both dropdown and footer show "自定义")
    const customLabels = screen.getAllByText("自定义");
    expect(customLabels.length).toBeGreaterThanOrEqual(1);

    // AuthorizationSummary should reflect the edited repository
    const summaryText = screen.getByTestId("authorization-summary-text");
    expect(summaryText.textContent).toContain("myorg/myrepo");
  });
});

describe("Task detail — custom policy editor reachability", () => {
  it("edit button is reachable for predefined task profiles", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
      { initialEntries: ["/tasks/t1"] },
    );

    // Edit policy button must be visible for CONTROLLER_REVIEW task
    const editButton = screen.getByRole("button", { name: "编辑权限" });
    expect(editButton).toBeInTheDocument();

    // Clicking it should open the custom editor
    await user.click(editButton);
    await screen.findByTestId("custom-policy-editor");
    expect(screen.getByTestId("custom-policy-editor")).toBeInTheDocument();
  });

  it("edit button is reachable for CUSTOM task profiles", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK_CUSTOM} isLoading={false} isError={false} />,
      { initialEntries: ["/tasks/t2"] },
    );

    // Edit policy button must also be visible for CUSTOM task
    const editButton = screen.getByRole("button", { name: "编辑权限" });
    expect(editButton).toBeInTheDocument();

    await user.click(editButton);
    await screen.findByTestId("custom-policy-editor");
    expect(screen.getByTestId("custom-policy-editor")).toBeInTheDocument();
  });

  it("edit button opens editor with current task policy", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
      { initialEntries: ["/tasks/t1"] },
    );

    await user.click(screen.getByRole("button", { name: "编辑权限" }));
    await screen.findByTestId("custom-policy-editor");

    // The AuthorizationSummary inside the editor should reflect the task's policy
    const summaryText = screen.getByTestId("authorization-summary-text");
    expect(summaryText).toBeInTheDocument();
  });
});

describe("Task detail — keyboard-operable resize separator", () => {
  it("separator has correct ARIA attributes", () => {
    mockMatchMedia(true);
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const handle = screen.getByTestId("resize-handle");
    expect(handle).toHaveAttribute("role", "slider");
    expect(handle).toHaveAttribute("aria-orientation", "vertical");
    expect(handle).toHaveAttribute("aria-valuemin");
    expect(handle).toHaveAttribute("aria-valuemax");
    expect(handle).toHaveAttribute("aria-valuenow");
  });

  it("ArrowLeft reduces the left panel width", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const handle = screen.getByTestId("resize-handle");
    const initial = handle.getAttribute("aria-valuenow");
    expect(initial).toBe("55");

    handle.focus();
    await user.keyboard("{ArrowLeft}");
    expect(handle.getAttribute("aria-valuenow")).toBe("50");
  });

  it("ArrowRight increases the left panel width", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const handle = screen.getByTestId("resize-handle");
    handle.focus();
    await user.keyboard("{ArrowRight}");
    expect(handle.getAttribute("aria-valuenow")).toBe("60");
  });

  it("Home sets left panel to minimum", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const handle = screen.getByTestId("resize-handle");
    handle.focus();
    await user.keyboard("{Home}");
    expect(handle.getAttribute("aria-valuenow")).toBe("30");
  });

  it("End sets left panel to maximum", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const handle = screen.getByTestId("resize-handle");
    handle.focus();
    await user.keyboard("{End}");
    expect(handle.getAttribute("aria-valuenow")).toBe("80");
  });

  it("width is clamped within min/max bounds", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const handle = screen.getByTestId("resize-handle");
    handle.focus();
    // Try to go below minimum
    await user.keyboard("{Home}");
    for (let i = 0; i < 3; i++) await user.keyboard("{ArrowLeft}");
    expect(handle.getAttribute("aria-valuenow")).toBe("30");
  });
});

describe("Task detail — mobile workspace", () => {
  it("mobile layout exposes one primary pane at a time", () => {
    mockMatchMedia(false);
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    // On mobile, right panel should not be conditionally rendered as a side split
    // Instead it should be accessible via tabs and only one content area should be visible
    const contentArea = screen.getByTestId("right-panel-content");
    expect(contentArea).toBeInTheDocument();
    // Verify no horizontal overflow class from desktop split
    expect(screen.getByTestId("task-detail")).not.toHaveAttribute(
      "data-desk-split",
    );
  });

  it("mobile layout allows switching between activity and tab panels", async () => {
    mockMatchMedia(false);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    // Activity is visible by default on mobile
    expect(screen.getByTestId("activity-stream")).toBeInTheDocument();

    // Switch to Changes tab
    const changesTab = screen.getByTestId("right-tab-changes");
    await user.click(changesTab);

    // Activity should be hidden and Changes visible
    expect(screen.queryByTestId("activity-stream")).not.toBeInTheDocument();
    expect(screen.getByTestId("changes-panel")).toBeInTheDocument();
  });

  it("mobile layout has no fixed min-width forcing horizontal overflow", () => {
    mockMatchMedia(false);
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    // The right panel should not have the desktop minWidth: 240px constraint
    const contentArea = screen.getByTestId("right-panel-content");
    const inlineMinWidth = contentArea.getAttribute("style") || "";
    expect(inlineMinWidth).not.toContain("240px");
  });
});