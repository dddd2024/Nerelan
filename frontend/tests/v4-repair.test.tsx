import { describe, it, expect } from "vitest";
import { fireEvent, screen, within } from "@testing-library/react";
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

function renderShell(initialEntry = "/") {
  return renderWithProviders(
    <AppShell>
      <div data-testid="workspace-content">content</div>
    </AppShell>,
    { initialEntries: [initialEntry] },
  );
}

describe("sidebar collapse/expand — OpenHands 1.8.0 adaptation", () => {
  it("starts at the 60px collapsed contract", () => {
    mockMatchMedia(true);
    renderWithProviders(
      <Sidebar
        onNewTask={() => {}}
        onOpenConversationPanel={() => {}}
        onConversationPanelClose={() => {}}
        conversationPanelOpen={false}
      />,
    );

    const sidebar = screen.getByTestId("sidebar");
    expect(sidebar).toHaveAttribute("data-collapsed", "true");
    expect(sidebar).toHaveClass("sidebar-collapsed");
    expect(screen.getByTestId("sidebar-collapse-toggle")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("expands to the 300px state by pointer or keyboard", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <Sidebar
        onNewTask={() => {}}
        onOpenConversationPanel={() => {}}
        onConversationPanelClose={() => {}}
        conversationPanelOpen={false}
      />,
    );

    const toggle = screen.getByTestId("sidebar-collapse-toggle");
    toggle.focus();
    await user.keyboard("{Space}");

    expect(screen.getByTestId("sidebar")).toHaveAttribute(
      "data-collapsed",
      "false",
    );
    expect(screen.getByTestId("sidebar")).toHaveClass("sidebar-expanded");
    expect(toggle).toHaveAttribute("aria-pressed", "false");
  });
});

describe("conversation panel stability", () => {
  it("stays open after its toggle changes AppShell state", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderShell("/tasks");

    await user.click(screen.getByTestId("toggle-conversation-panel"));

    expect(await screen.findByTestId("conversation-panel")).toBeInTheDocument();
  });

  it("closes when desktop navigation changes route", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderShell("/tasks");

    await user.click(screen.getByTestId("toggle-conversation-panel"));
    expect(await screen.findByTestId("conversation-panel")).toBeInTheDocument();
    await user.click(screen.getByTestId("sidebar-nav-首页"));

    expect(screen.queryByTestId("conversation-panel")).not.toBeInTheDocument();
  });
});

describe("accessible mobile drawer", () => {
  it("remains open after the trigger state update", async () => {
    mockMatchMedia(false);
    const user = userEvent.setup();
    renderShell();

    const trigger = screen.getByTestId("mobile-menu-button");
    await user.click(trigger);

    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("mobile-drawer")).toHaveAttribute(
      "aria-hidden",
      "false",
    );
    expect(screen.getByTestId("mobile-drawer-close")).toHaveFocus();
    expect(document.body.style.overflow).toBe("hidden");
  });

  it("removes background content from the focus order while open", async () => {
    mockMatchMedia(false);
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByTestId("mobile-menu-button"));

    expect(screen.getByTestId("mobile-menu-bar")).toHaveAttribute("inert");
    expect(screen.getByTestId("app-shell-workspace")).toHaveAttribute("inert");
    expect(screen.getByTestId("app-shell-workspace")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
  });

  it("closes on Escape, restores scrolling and returns focus", async () => {
    mockMatchMedia(false);
    const user = userEvent.setup();
    renderShell();

    const trigger = screen.getByTestId("mobile-menu-button");
    await user.click(trigger);
    await user.keyboard("{Escape}");

    expect(trigger).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByTestId("mobile-drawer")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
    expect(document.body.style.overflow).toBe("");
    expect(trigger).toHaveFocus();
  });

  it("closes through the backdrop and SPA navigation", async () => {
    mockMatchMedia(false);
    const user = userEvent.setup();
    renderShell();

    const trigger = screen.getByTestId("mobile-menu-button");
    await user.click(trigger);
    await user.click(screen.getByTestId("mobile-drawer-backdrop"));
    expect(trigger).toHaveAttribute("aria-expanded", "false");

    await user.click(trigger);
    await user.click(screen.getByTestId("mobile-nav-任务"));
    expect(trigger).toHaveAttribute("aria-expanded", "false");
  });
});

describe("New Task composer — CUSTOM policy persistence", () => {
  it("selects CUSTOM and opens the editor", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(<NewTaskComposer open={true} onClose={() => {}} />);

    await user.click(screen.getByTestId("permission-mode-composer"));
    await user.click(screen.getByTestId("permission-option-CUSTOM"));

    expect(await screen.findByTestId("custom-policy-editor")).toBeInTheDocument();
  });

  it("persists edited policy data into the authorization summary", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(<NewTaskComposer open={true} onClose={() => {}} />);

    await user.click(screen.getByTestId("permission-mode-composer"));
    await user.click(screen.getByTestId("permission-option-CUSTOM"));
    const editor = await screen.findByTestId("custom-policy-editor");
    const mergeReposInput = screen.getByTestId("merge-allowed-repos");
    await user.clear(mergeReposInput);
    await user.type(mergeReposInput, "myorg/myrepo");
    await user.click(
      within(editor).getByRole("button", { name: "关闭编辑器" }),
    );

    expect(screen.queryByTestId("custom-policy-editor")).not.toBeInTheDocument();
    expect(screen.getByTestId("authorization-summary-text")).toHaveTextContent(
      "myorg/myrepo",
    );
  });
});

describe("Task detail — policy editor reachability", () => {
  it.each([FIXTURE_TASK, FIXTURE_TASK_CUSTOM])(
    "opens the editor for profile $permissionProfile",
    async (task) => {
      mockMatchMedia(true);
      const user = userEvent.setup();
      renderWithProviders(
        <TaskDetail task={task} isLoading={false} isError={false} />,
      );

      await user.click(screen.getByRole("button", { name: "编辑权限" }));

      expect(
        await screen.findByTestId("custom-policy-editor"),
      ).toBeInTheDocument();
    },
  );
});

describe("Task detail — accessible resize separator", () => {
  it("exposes separator semantics and updates the real panel width", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const handle = screen.getByTestId("resize-handle");
    const leftPanel = screen.getByTestId("desktop-left-panel");
    expect(handle).toHaveAttribute("role", "separator");
    expect(handle).toHaveAttribute("aria-orientation", "vertical");
    expect(handle).toHaveAttribute("aria-valuenow", "55");
    expect(leftPanel).toHaveStyle({ width: "55%" });

    handle.focus();
    await user.keyboard("{ArrowRight}");

    expect(handle).toHaveAttribute("aria-valuenow", "60");
    expect(leftPanel).toHaveStyle({ width: "60%" });
  });

  it("supports Home and End while preserving the 30–80 bounds", async () => {
    mockMatchMedia(true);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const handle = screen.getByTestId("resize-handle");
    const leftPanel = screen.getByTestId("desktop-left-panel");
    handle.focus();
    await user.keyboard("{Home}{ArrowLeft}");
    expect(handle).toHaveAttribute("aria-valuenow", "30");
    expect(leftPanel).toHaveStyle({ width: "30%" });

    await user.keyboard("{End}{ArrowRight}");
    expect(handle).toHaveAttribute("aria-valuenow", "80");
    expect(leftPanel).toHaveStyle({ width: "80%" });
  });

  it("calculates pointer resizing against the full split container", () => {
    mockMatchMedia(true);
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    const split = screen.getByTestId("desktop-split-container");
    Object.defineProperty(split, "getBoundingClientRect", {
      configurable: true,
      value: () => ({
        x: 0,
        y: 0,
        left: 0,
        top: 0,
        right: 1000,
        bottom: 600,
        width: 1000,
        height: 600,
        toJSON: () => ({}),
      }),
    });

    fireEvent.mouseDown(screen.getByTestId("resize-handle-container"));
    fireEvent.mouseMove(document, { clientX: 700 });
    fireEvent.mouseUp(document);

    expect(screen.getByTestId("resize-handle")).toHaveAttribute(
      "aria-valuenow",
      "70",
    );
    expect(screen.getByTestId("desktop-left-panel")).toHaveStyle({
      width: "70%",
    });
  });
});

describe("Task detail — reversible mobile one-pane workspace", () => {
  it("shows only Activity initially", () => {
    mockMatchMedia(false);
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    expect(screen.getByTestId("activity-stream")).toBeInTheDocument();
    expect(screen.queryByTestId("changes-panel")).not.toBeInTheDocument();
    expect(screen.getByTestId("right-panel-content")).toHaveAttribute(
      "data-active-pane",
      "activity",
    );
  });

  it("switches to Changes and returns to Activity", async () => {
    mockMatchMedia(false);
    const user = userEvent.setup();
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    await user.click(screen.getByTestId("right-tab-changes"));
    expect(screen.queryByTestId("activity-stream")).not.toBeInTheDocument();
    expect(screen.getByTestId("changes-panel")).toBeInTheDocument();
    expect(screen.getByTestId("right-panel-content")).toHaveAttribute(
      "data-active-pane",
      "changes",
    );

    await user.click(screen.getByTestId("mobile-pane-activity"));
    expect(screen.getByTestId("activity-stream")).toBeInTheDocument();
    expect(screen.queryByTestId("changes-panel")).not.toBeInTheDocument();
  });

  it("does not inherit the desktop panel minimum width", () => {
    mockMatchMedia(false);
    renderWithProviders(
      <TaskDetail task={FIXTURE_TASK} isLoading={false} isError={false} />,
    );

    expect(
      screen.getByTestId("right-panel-content").getAttribute("style") ?? "",
    ).not.toContain("240px");
  });
});
