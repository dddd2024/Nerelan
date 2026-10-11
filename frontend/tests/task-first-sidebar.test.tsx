import { afterEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { Sidebar } from "@/components/sidebar";
import { ConversationPanel } from "@/components/conversation-panel";
import { TasksPage } from "@/routes/tasks";

const taskReadState = vi.hoisted(() => ({
  override: undefined as undefined | {
    data: never[];
    isLoading: boolean;
    isError: boolean;
    error?: Error;
  },
}));

vi.mock("@/hooks/use-tasks", () => {
  const base = {
    riskTier: "R1" as const,
    permissionProfile: "CONTROLLER_REVIEW" as const,
    activity: [],
    changes: [],
    evidence: [],
    authorityStatus: "APPROVED" as const,
    testStatus: "PASS" as const,
    workflowStatus: "SUCCESS" as const,
  };
  const tasks = [
    {
      ...base,
      id: "task-old",
      title: "Older alpha task",
      issueNumber: 11,
      state: "READY_FOR_HUMAN" as const,
      updatedAt: "2026-08-01T08:00:00Z",
      branch: "alpha-old",
      repository: "org/alpha",
    },
    {
      ...base,
      id: "task-newest",
      title: "Newest alpha task",
      issueNumber: 12,
      state: "RUNNING" as const,
      updatedAt: "2026-08-03T08:00:00Z",
      branch: "alpha-new",
      repository: "org/alpha",
    },
    {
      ...base,
      id: "task-beta",
      title: "Beta validation task",
      issueNumber: 13,
      state: "BLOCKED_EXTERNAL" as const,
      updatedAt: "2026-08-02T08:00:00Z",
      branch: "beta-check",
      repository: "org/beta",
    },
  ];
  return {
    useTasks: () => taskReadState.override ?? { data: tasks, isLoading: false, isError: false, error: null },
  };
});

function sidebar(initialEntries = ["/"]) {
  const onOpen = vi.fn();
  renderWithProviders(
    <Sidebar
      onNewTask={() => {}}
      onOpenConversationPanel={onOpen}
      onConversationPanelClose={() => {}}
      conversationPanelOpen={false}
    />,
    { initialEntries },
  );
  return { onOpen };
}

afterEach(() => { taskReadState.override = undefined; });

describe("sidebar task read states", () => {
  it("shows loading without claiming the database is empty", () => {
    taskReadState.override = { data: [], isLoading: true, isError: false };
    sidebar();
    expect(screen.getByText("正在加载最近任务…")).toBeInTheDocument();
    expect(screen.getByText("正在加载项目…")).toBeInTheDocument();
    expect(screen.queryByText("暂无最近任务")).not.toBeInTheDocument();
    expect(screen.queryByText("暂无项目")).not.toBeInTheDocument();
  });

  it("reports a failed read without displaying raw errors or an empty result", () => {
    taskReadState.override = { data: [], isLoading: false, isError: true, error: new Error("private diagnostic") };
    sidebar();
    expect(screen.getByRole("alert")).toHaveTextContent("最近任务读取失败，请检查服务连接");
    expect(screen.queryByText("暂无最近任务")).not.toBeInTheDocument();
    expect(screen.queryByText("暂无项目")).not.toBeInTheDocument();
    expect(screen.queryByText(/private diagnostic/)).not.toBeInTheDocument();
  });

  it("shows empty only after a successful empty read", () => {
    taskReadState.override = { data: [], isLoading: false, isError: false };
    sidebar();
    expect(screen.getByText("暂无最近任务")).toBeInTheDocument();
    expect(screen.getByText("暂无项目")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("task-first sidebar IA", () => {
  it("uses the compact width and orders Recent by authoritative updatedAt", () => {
    sidebar(["/tasks/task-newest"]);

    expect(screen.getByTestId("sidebar")).toHaveClass("w-[232px]");
    expect(screen.getByTestId("sidebar-section-recent")).toHaveTextContent("最近任务");
    const recent = screen.getAllByTestId(/^sidebar-recent-task-/);
    expect(recent.map((item) => item.textContent)).toEqual([
      "Newest alpha task",
      "Beta validation task",
      "Older alpha task",
    ]);
    expect(screen.getByTestId("sidebar-recent-task-task-newest")).toHaveAttribute(
      "data-selected",
      "true",
    );
  });

  it("deduplicates Projects from task repositories and keeps project emphasis weaker", () => {
    sidebar(["/tasks?repository=org%2Falpha"]);

    expect(screen.getByTestId("sidebar-section-projects")).toHaveTextContent("项目");
    expect(screen.getAllByTestId(/^sidebar-project-/)).toHaveLength(2);
    const alpha = screen.getByTestId("sidebar-project-org/alpha");
    expect(alpha).toHaveAttribute("href", "/tasks?repository=org%2Falpha");
    expect(alpha).toHaveAttribute("data-selected", "true");
    expect(alpha).not.toHaveClass("bg-ra-tertiary");
  });

  it("opens Search directly and keeps lower-frequency routes behind More", async () => {
    const user = userEvent.setup();
    const { onOpen } = sidebar();

    await user.click(screen.getByTestId("toggle-conversation-panel"));
    expect(onOpen).toHaveBeenCalledTimes(1);

    expect(screen.getByTestId("sidebar-more-menu")).not.toBeVisible();
    await user.click(screen.getByTestId("sidebar-more-toggle"));
    expect(screen.getByTestId("sidebar-more-menu")).toBeVisible();
    expect(screen.getByTestId("sidebar-nav-任务")).toHaveAttribute("href", "/tasks");
    expect(screen.getByTestId("sidebar-nav-收件箱")).toHaveAttribute("href", "/inbox");
    expect(screen.getByTestId("sidebar-nav-路线图")).toHaveAttribute("href", "/roadmap");
    expect(screen.getByTestId("sidebar-nav-Agent 运行")).toHaveAttribute("href", "/runs");
    expect(screen.getByTestId("sidebar-nav-设置")).toHaveAttribute("href", "/settings");
  });
});

describe("task Search and project filtering", () => {
  it("filters task truth by repository/branch/title and closes on selection", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(<ConversationPanel open={true} onClose={onClose} />);

    const input = screen.getByTestId("task-search-input");
    await user.type(input, "beta-check");
    expect(screen.getByTestId("conversation-task-task-beta")).toBeInTheDocument();
    expect(screen.queryByTestId("conversation-task-task-newest")).not.toBeInTheDocument();

    await user.click(screen.getByTestId("conversation-task-task-beta"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("filters the Tasks surface by the repository query without a second store", () => {
    renderWithProviders(<TasksPage />, {
      initialEntries: ["/tasks?repository=org%2Fbeta"],
    });

    expect(screen.getByTestId("tasks-repository-filter")).toHaveTextContent("org/beta");
    expect(screen.getByText(/Beta validation task/)).toBeInTheDocument();
    expect(screen.queryByText(/Newest alpha task/)).not.toBeInTheDocument();
  });
});
