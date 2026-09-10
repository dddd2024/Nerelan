import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GoalComposer } from "@/components/goal-composer";
import type { StartGoalInput } from "@/lib/goal-start-operation";

function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

describe("GoalComposer compact progressive disclosure", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  afterEach(() => {
    window.sessionStorage.clear();
  });

  it("starts compact and keeps secondary configuration out of the empty idle surface", async () => {
    const user = userEvent.setup();
    render(<GoalComposer busy={false} onSubmit={async () => {}} />);

    const objective = screen.getByLabelText("描述最终目标");
    expect(objective).toHaveAttribute("rows", "1");
    expect(screen.queryByTestId("goal-composer-options")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("执行模式")).not.toBeInTheDocument();

    const options = screen.getByRole("button", { name: "输入选项" });
    expect(options).toHaveAttribute("aria-expanded", "false");
    await user.click(options);

    expect(options).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("goal-composer-options")).toBeInTheDocument();
    expect(screen.getByLabelText("仓库")).toBeInTheDocument();
    expect(screen.getByLabelText("执行模式")).toBeInTheDocument();
    expect(screen.getByLabelText("模型绑定")).toBeInTheDocument();
    expect(screen.getByText("启用 2 小时自治窗口")).toBeInTheDocument();
  });

  it("keeps the submitted draft visible until success, then clears only that operation", async () => {
    const submission = deferred();
    const onSubmit = vi.fn((_input: StartGoalInput) => submission.promise);
    const user = userEvent.setup();
    render(<GoalComposer busy={false} onSubmit={onSubmit} />);

    const objective = screen.getByLabelText("描述最终目标");
    const submit = screen.getByLabelText("规划并运行");

    await user.type(objective, "完成 provider-free 多 Agent 验证");
    await user.selectOptions(
      screen.getByLabelText("执行模式"),
      "deterministic_fixture",
    );
    await user.click(screen.getByText("启用 2 小时自治窗口"));
    await user.click(submit);

    expect(onSubmit).toHaveBeenCalledTimes(1);
    const sent = onSubmit.mock.calls[0][0];
    expect(sent).toMatchObject({
      objective: "完成 provider-free 多 Agent 验证",
      repository: "dddd2024/reverse-agent",
      executorKind: "deterministic_fixture",
      bindingRef: "coding-default",
      autonomyHours: 2,
    });
    expect(sent.operationId).toMatch(/^[A-Za-z0-9._:-]{8,160}$/);
    expect(objective).toHaveValue("完成 provider-free 多 Agent 验证");

    await user.type(objective, " 新草稿");
    submission.resolve();
    await waitFor(() =>
      expect(objective).toHaveValue("完成 provider-free 多 Agent 验证 新草稿"),
    );

    const second = deferred();
    onSubmit.mockImplementationOnce((_input: StartGoalInput) => second.promise);
    await user.click(submit);
    const secondSent = onSubmit.mock.calls[1][0];
    expect(secondSent.operationId).not.toBe(sent.operationId);
    second.resolve();
    await waitFor(() => expect(objective).toHaveValue(""));
    expect(screen.queryByTestId("goal-composer-options")).not.toBeInTheDocument();
  });

  it("retains failed draft and operation identity across remount, then rotates identity after editing", async () => {
    const onSubmit = vi.fn((_input: StartGoalInput) =>
      Promise.reject(new Error("connection_lost")),
    );
    const user = userEvent.setup();
    const view = render(<GoalComposer busy={false} onSubmit={onSubmit} />);

    await user.type(
      screen.getByLabelText("描述最终目标"),
      "恢复同一个 Goal 启动操作",
    );
    await user.selectOptions(
      screen.getByLabelText("执行模式"),
      "deterministic_fixture",
    );
    await user.click(screen.getByText("启用 2 小时自治窗口"));
    await user.click(screen.getByLabelText("规划并运行"));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    const firstOperation = onSubmit.mock.calls[0][0].operationId;
    expect(screen.getByLabelText("描述最终目标")).toHaveValue(
      "恢复同一个 Goal 启动操作",
    );

    view.unmount();
    const retrySubmit = vi.fn((_input: StartGoalInput) =>
      Promise.reject(new Error("still_offline")),
    );
    render(<GoalComposer busy={false} onSubmit={retrySubmit} />);

    expect(screen.getByLabelText("描述最终目标")).toHaveValue(
      "恢复同一个 Goal 启动操作",
    );
    expect(screen.getByLabelText("执行模式")).toHaveValue(
      "deterministic_fixture",
    );
    expect(screen.getByRole("checkbox")).toBeChecked();

    await user.click(screen.getByLabelText("规划并运行"));
    await waitFor(() => expect(retrySubmit).toHaveBeenCalledTimes(1));
    expect(retrySubmit.mock.calls[0][0].operationId).toBe(firstOperation);

    await user.type(screen.getByLabelText("描述最终目标"), " 修改");
    await user.click(screen.getByLabelText("规划并运行"));
    await waitFor(() => expect(retrySubmit).toHaveBeenCalledTimes(2));
    expect(retrySubmit.mock.calls[1][0].operationId).not.toBe(firstOperation);
  });
});
