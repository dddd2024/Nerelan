import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router";
import { beforeEach, expect, it, vi } from "vitest";
import { GoalReviewEditor } from "@/components/goal-review-editor";
import { InboxPage } from "@/routes/inbox";
import { ApprovalsPage } from "@/routes/approvals";
import { HomePage } from "@/routes/home";
import { fetchGoal, type PlatformGoal } from "@/lib/platform-client";

const queries = vi.hoisted(() => ({ bindings: vi.fn(), repositories: vi.fn() }));
vi.mock("@/hooks/use-model-access", () => ({ useBindings: queries.bindings }));
vi.mock("@/hooks/use-repositories", () => ({ useRepositories: queries.repositories }));

const binding = { bindingId: "coding-selected", name: "Selected model", modelId: "model-test", executorId: "opencode", enabled: true };
const repository = { full_name: "owner/selected", html_url: "https://github.com/owner/selected" };
const fixture: PlatformGoal = { id: "goal-editor-1", title: "Editable Goal", objective: "Original specification",
  repository: "owner/original", status: "PLANNED", revision: 1, spec_markdown: "Original specification",
  plan_markdown: "Current plan", tasks: [
    { id: "A", title: "Implement", instruction: "Original instruction", dependencies: [], capability: "execute_task" },
    { id: "B", title: "Verify", instruction: "Verify the artifact", dependencies: ["A"], capability: "validate_task" },
  ], acceptance_criteria: ["Original criterion"], artifact_digest: "original-plan", executor_kind: "deterministic_fixture",
  orchestration_mode: "single", binding_ref: "", task_links: [], window_id: "", created_at: "now", updated_at: "now" };

beforeEach(() => {
  vi.unstubAllEnvs();
  queries.bindings.mockReturnValue({ data: [binding], isPending: false, isError: false, refetch: vi.fn() });
  queries.repositories.mockReturnValue({ data: [repository], isPending: false, isError: false, refetch: vi.fn() });
});

function props(goal = structuredClone(fixture)) {
  return { goal, busy: false, onEditingChange: vi.fn(), onConfigurationReady: vi.fn(),
    onSaveConfiguration: vi.fn().mockResolvedValue(undefined), onSavePlan: vi.fn().mockResolvedValue(undefined) };
}

it("saves explicitly selected executor, repository and Binding on the observed Goal", async () => {
  const current = props();
  render(<GoalReviewEditor {...current} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "编辑目标配置" }));
  await user.selectOptions(screen.getByLabelText("目标执行器"), "opencode");
  expect(screen.getByRole("button", { name: "保存目标配置" })).toBeDisabled();
  await user.selectOptions(screen.getByLabelText("目标仓库"), "owner/selected");
  await user.selectOptions(screen.getByLabelText("目标模型绑定"), "coding-selected");
  await user.click(screen.getByRole("button", { name: "保存目标配置" }));
  await waitFor(() => expect(current.onSaveConfiguration).toHaveBeenCalledWith(current.goal, {
    objective: fixture.objective, repository: "owner/selected", executor_kind: "opencode",
    orchestration_mode: "sequential_team", binding_ref: "coding-selected",
  }));
  expect(current.onSavePlan).not.toHaveBeenCalled();
});

it("retains edits on failure and newer server revisions until an explicit reload", async () => {
  const current = props();
  current.onSaveConfiguration.mockRejectedValue(new Error("Connection lost; retry after reading state"));
  const view = render(<GoalReviewEditor {...current} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "编辑目标配置" }));
  await user.clear(screen.getByLabelText("目标规格"));
  await user.type(screen.getByLabelText("目标规格"), "My unsaved specification");
  await user.click(screen.getByRole("button", { name: "保存目标配置" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Connection lost");
  const newer = { ...current.goal, revision: 2, objective: "Another owner's update" };
  view.rerender(<GoalReviewEditor {...current} goal={newer} />);
  expect(screen.getByLabelText("目标规格")).toHaveValue("My unsaved specification");
  expect(screen.getByRole("button", { name: "保存目标配置" })).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "放弃本地修改并重新载入" }));
  expect(screen.getByLabelText("目标规格")).toHaveValue(newer.objective);
  expect(current.onSaveConfiguration).toHaveBeenCalledTimes(1);
});

it("edits task instructions and criteria while preserving ids, dependencies, capability and count", async () => {
  const current = props();
  render(<GoalReviewEditor {...current} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "编辑当前计划" }));
  await user.clear(screen.getByLabelText("任务 A 说明"));
  await user.type(screen.getByLabelText("任务 A 说明"), "Edited implementation");
  await user.clear(screen.getByLabelText("计划验收标准"));
  await user.type(screen.getByLabelText("计划验收标准"), "Exact artifact is verified");
  await user.click(screen.getByRole("button", { name: "保存计划修改" }));
  expect(current.onSavePlan).toHaveBeenCalledWith(current.goal, {
    tasks: [{ ...fixture.tasks[0], instruction: "Edited implementation" }, fixture.tasks[1]],
    acceptance_criteria: ["Exact artifact is verified"],
  });
  expect(current.onSaveConfiguration).not.toHaveBeenCalled();
});

it.each(["pending", "error", "empty", "disabled"])("blocks unavailable %s metadata without choosing another Binding", async (state) => {
  queries.bindings.mockReturnValue({ data: state === "disabled" ? [{ ...binding, enabled: false }] : undefined,
    isPending: state === "pending", isError: state === "error", refetch: vi.fn() });
  const current = props({ ...fixture, executor_kind: "opencode", binding_ref: "coding-selected", repository: "owner/selected" });
  render(<GoalReviewEditor {...current} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "编辑目标配置" }));
  expect(screen.getByLabelText("目标模型绑定")).toHaveValue("coding-selected");
  expect(screen.getByRole("button", { name: "保存目标配置" })).toBeDisabled();
  expect(current.onConfigurationReady).toHaveBeenLastCalledWith(false);
  if (state === "error") {
    expect(screen.getByRole("alert")).toHaveTextContent("模型绑定读取失败");
    expect(screen.queryByText(/暂无可用的 OpenCode/)).not.toBeInTheDocument();
  }
  if (state === "pending") expect(screen.getByText("正在读取仓库与模型绑定…")).toBeInTheDocument();
  expect(current.onSaveConfiguration).not.toHaveBeenCalled();
});

it("completes Inbox capture, configuration, edited-plan review and explicit launch on the same Goal", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/inbox"]}><Routes>
    <Route path="/inbox" element={<InboxPage />} /><Route path="/approvals" element={<ApprovalsPage />} />
    <Route path="/" element={<HomePage />} />
  </Routes></MemoryRouter></QueryClientProvider>);
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("描述想法"), "Inbox full review journey");
  await user.click(screen.getByRole("button", { name: "捕获想法" }));
  await user.click(await screen.findByRole("button", { name: "晋升 Inbox full review journey 为目标" }));
  const link = await screen.findByRole("link", { name: "继续目标" });
  const goalId = new URL(link.getAttribute("href")!, "http://localhost").searchParams.get("goal")!;
  await user.click(link);
  await user.click(await screen.findByRole("button", { name: "编辑目标配置" }));
  await user.selectOptions(screen.getByLabelText("目标执行器"), "opencode");
  await user.selectOptions(screen.getByLabelText("目标仓库"), "owner/selected");
  await user.selectOptions(screen.getByLabelText("目标模型绑定"), "coding-selected");
  await user.click(screen.getByRole("button", { name: "保存目标配置" }));
  await waitFor(() => expect(screen.getByTestId("approval-plan-button")).toBeEnabled());
  await user.click(screen.getByTestId("approval-plan-button"));
  await user.click(await screen.findByRole("button", { name: "编辑当前计划" }));
  expect(screen.getByTestId("approval-approve-button")).toBeDisabled();
  await user.clear(screen.getByLabelText("任务 T001 说明"));
  await user.type(screen.getByLabelText("任务 T001 说明"), "Edited full journey implementation");
  await user.click(screen.getByRole("button", { name: "保存计划修改" }));
  await waitFor(() => expect(screen.getByTestId("approval-plan")).toHaveTextContent("Edited full journey implementation"));
  await user.click(screen.getByTestId("approval-approve-button"));
  expect(await screen.findByTestId("approval-launch-button")).toBeDisabled();
  await user.click(screen.getByLabelText("确认启动当前计划"));
  await user.click(screen.getByTestId("approval-launch-button"));
  await screen.findByTestId("goal-progress-bar");
  const saved = await fetchGoal(goalId);
  expect(saved).toMatchObject({ id: goalId, status: "RUNNING", revision: 3, executor_kind: "opencode",
    repository: "owner/selected", binding_ref: "coding-selected", orchestration_mode: "sequential_team" });
  expect(saved.tasks[0].instruction).toBe("Edited full journey implementation");
  expect(saved.task_links).toHaveLength(1);
  client.clear();
});

it("selects fixed checks, blocks duplicates and bad directories, and explicitly removes the last selection", async () => {
  const current = props();
  render(<GoalReviewEditor {...current} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "编辑当前计划" }));
  await user.click(screen.getByRole("button", { name: "添加任务 A 功能检查" }));
  await user.click(screen.getByRole("button", { name: "添加任务 A 功能检查" }));
  expect(screen.getByRole("alert")).toHaveTextContent("同一检查与目录不能重复");
  expect(screen.getByRole("button", { name: "保存计划修改" })).toBeDisabled();
  await user.selectOptions(screen.getByLabelText("任务 A 检查 2 类型"), "npm_test");
  await user.clear(screen.getByLabelText("任务 A 检查 2 目录"));
  await user.type(screen.getByLabelText("任务 A 检查 2 目录"), "../outside");
  expect(screen.getByRole("button", { name: "保存计划修改" })).toBeDisabled();
  await user.clear(screen.getByLabelText("任务 A 检查 2 目录"));
  await user.type(screen.getByLabelText("任务 A 检查 2 目录"), "frontend");
  await user.click(screen.getByRole("button", { name: "保存计划修改" }));
  expect(current.onSavePlan.mock.calls[0][1].tasks[0].validation_checks).toEqual([
    { profile_id: "python_pytest", working_directory: "." }, { profile_id: "npm_test", working_directory: "frontend" },
  ]);
  expect(current.onSavePlan.mock.calls[0][1].tasks[1]).not.toHaveProperty("validation_checks");
});

it("preserves saved checks during instruction edits and submits an explicit empty selection on removal", async () => {
  const current = props({ ...fixture, tasks: [{ ...fixture.tasks[0], validation_checks: [{ profile_id: "python_pytest", working_directory: "backend" }] }] });
  render(<GoalReviewEditor {...current} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "编辑当前计划" }));
  await user.type(screen.getByLabelText("任务 A 说明"), " additional detail");
  await user.click(screen.getByRole("button", { name: "保存计划修改" }));
  expect(current.onSavePlan.mock.calls[0][1].tasks[0].validation_checks).toEqual(current.goal.tasks[0].validation_checks);
  await user.click(screen.getByRole("button", { name: "编辑当前计划" }));
  await user.click(screen.getByRole("button", { name: "移除任务 A 检查 1" }));
  await user.click(screen.getByRole("button", { name: "保存计划修改" }));
  expect(current.onSavePlan.mock.calls[1][1].tasks[0].validation_checks).toEqual([]);
});

it("retains local check selection across a stale plan and reloads only on explicit discard", async () => {
  const current = props();
  const view = render(<GoalReviewEditor {...current} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "编辑当前计划" }));
  await user.click(screen.getByRole("button", { name: "添加任务 A 功能检查" }));
  view.rerender(<GoalReviewEditor {...current} goal={{ ...current.goal, revision: 2 }} />);
  expect(screen.getByLabelText("任务 A 检查 1 类型")).toHaveValue("python_pytest");
  expect(screen.getByRole("button", { name: "保存计划修改" })).toBeDisabled();
  expect(current.onSavePlan).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: "放弃本地修改并重新载入" }));
  expect(screen.queryByLabelText("任务 A 检查 1 类型")).not.toBeInTheDocument();
});

it("limits each task to eight check pairs and leaves approved plans immutable", async () => {
  const current = props({ ...fixture, tasks: [{ ...fixture.tasks[0], validation_checks: Array.from({ length: 8 }, (_, i) => ({ profile_id: "python_pytest" as const, working_directory: `part${i}` })) }] });
  const view = render(<GoalReviewEditor {...current} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "编辑当前计划" }));
  expect(screen.getByRole("button", { name: "添加任务 A 功能检查" })).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "取消编辑" }));
  view.rerender(<GoalReviewEditor {...current} goal={{ ...current.goal, status: "APPROVED" }} />);
  expect(screen.queryByRole("button", { name: "编辑当前计划" })).not.toBeInTheDocument();
});
