import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import type { Binding, Connection } from "@/schemas/model-access";
import type { Task } from "@/types";
import { BindingList } from "@/components/binding-list";
import { TaskInbox } from "@/components/task-inbox";
import { taskActionCopy } from "@/lib/task-status-copy";
import { runtimeExplanation } from "@/lib/runtime-labels";
import { UI_LOCALE_STORAGE_KEY } from "@/lib/ui-locale";

const binding = (over: Partial<Binding>): Binding => ({
  bindingId: "b", name: "n", connectionId: "magpie", executorId: "opencode", modelId: "m", enabled: true, ...over,
} as Binding);

const BINDINGS = [
  binding({ bindingId: "b1", name: "GPT 6.1", modelId: "gpt-6.1" }),
  binding({ bindingId: "b2", name: "Supervised health mistral", modelId: "mistral", enabled: false }),
  binding({ bindingId: "b3", name: "Supervised health mistral", modelId: "mistral", enabled: false }),
  binding({ bindingId: "b4", name: "DeepSeek", connectionId: "zen", modelId: "deepseek-v4" }),
  binding({ bindingId: "b5", name: "Old", connectionId: "legacy", enabled: false }),
];
const CONNECTIONS = [{ connectionId: "magpie", name: "Magpie" }, { connectionId: "zen", name: "OpenCode Zen" }] as Connection[];

describe("binding list", () => {
  it("groups by connection, enabled first, and flags same-named leftovers", async () => {
    const onSelect = vi.fn();
    render(<BindingList bindings={BINDINGS} connections={CONNECTIONS} selectedId={null} onSelect={onSelect} />);
    const groups = screen.getAllByTestId(/^binding-group-/).map((group) => group.getAttribute("data-testid"));
    expect(groups).toEqual(["binding-group-magpie", "binding-group-zen", "binding-group-legacy"]);
    expect(within(screen.getByTestId("binding-group-magpie")).getByText("1 启用 / 3")).toBeInTheDocument();
    expect(within(screen.getByTestId("binding-group-legacy")).getByText("全部停用 · 1")).toBeInTheDocument();
    expect(screen.getByTestId("binding-duplicate-b2")).toHaveTextContent("2 个同名绑定");
    expect(screen.queryByTestId("binding-duplicate-b1")).not.toBeInTheDocument();

    await userEvent.type(screen.getByTestId("binding-search"), "deepseek");
    expect(screen.getByTestId("binding-item-b4")).toBeInTheDocument();
    expect(screen.queryByTestId("binding-item-b1")).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("binding-item-b4"));
    expect(onSelect).toHaveBeenCalledWith("b4");

    await userEvent.clear(screen.getByTestId("binding-search"));
    await userEvent.type(screen.getByTestId("binding-search"), "nothing-like-this");
    expect(screen.getByText("没有匹配的绑定。")).toBeInTheDocument();
  });
});

const task = (over: Partial<Task>): Task => ({
  id: "t", title: "任务", issueNumber: null, state: "WAITING_FOR_OWNER", riskTier: "UNKNOWN", updatedAt: "",
  permissionProfile: "ASK_FOR_APPROVAL", branch: "", activity: [], changes: [], evidence: [],
  authorityStatus: "MISSING", testStatus: "PENDING", workflowStatus: "UNKNOWN", ...over,
} as Task);

describe("task inbox", () => {
  it("keeps queued tasks out of 需要你处理", () => {
    render(<MemoryRouter><TaskInbox isLoading={false} isError={false} error={null} tasks={[
      task({ id: "q1", nextAction: "Waiting for executor dispatch" }),
      task({ id: "q2", nextAction: "Waiting for executor dispatch" }),
      task({ id: "r1", state: "READY_FOR_HUMAN", nextAction: "Owner review of functionally validated result" }),
      task({ id: "i1", blocker: "opencode_stalled:900" }),
    ]} /></MemoryRouter>);
    expect(within(screen.getByTestId("section-needs-attention")).getByText("(2)")).toBeInTheDocument();
    const queued = screen.getByTestId("section-queued");
    expect(queued).not.toHaveAttribute("open");
    expect(within(queued).getByText("(2)")).toBeInTheDocument();
  });

  it("says the host's next action in Chinese", () => {
    expect(taskActionCopy("Waiting for executor dispatch")).toBe("排队中：等待执行窗口派发");
    expect(taskActionCopy("Owner review; functional acceptance evidence still required")).toBe("等你审查（还缺功能验收证据）");
  });

  it("keeps host actions in English when the stored locale is English", () => {
    localStorage.setItem(UI_LOCALE_STORAGE_KEY, "en");
    try {
      expect(taskActionCopy("Waiting for executor dispatch")).toBe(runtimeExplanation("Waiting for executor dispatch"));
      expect(taskActionCopy("Waiting for executor dispatch", "zh-CN")).toBe("排队中：等待执行窗口派发");
    } finally {
      localStorage.removeItem(UI_LOCALE_STORAGE_KEY);
    }
  });
});
