import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { GoalComposer } from "@/components/goal-composer";

describe("GoalComposer compact progressive disclosure", () => {
  it("starts compact and keeps secondary configuration out of the empty idle surface", async () => {
    const user = userEvent.setup();
    render(<GoalComposer busy={false} onSubmit={() => {}} />);

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

  it("reveals options after objective input and preserves explicit confirmation plus submit payload", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<GoalComposer busy={false} onSubmit={onSubmit} />);

    const objective = screen.getByLabelText("描述最终目标");
    const submit = screen.getByLabelText("规划并运行");

    await user.type(objective, "完成 provider-free 多 Agent 验证");

    expect(screen.getByTestId("goal-composer-options")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "输入选项" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    await user.selectOptions(
      screen.getByLabelText("执行模式"),
      "deterministic_fixture",
    );

    expect(screen.queryByLabelText("模型绑定")).not.toBeInTheDocument();
    expect(submit).toBeDisabled();

    await user.click(screen.getByText("启用 2 小时自治窗口"));
    expect(submit).toBeEnabled();
    await user.click(submit);

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith({
      objective: "完成 provider-free 多 Agent 验证",
      repository: "dddd2024/Nerelan",
      executorKind: "deterministic_fixture",
      bindingRef: "coding-default",
      autonomyHours: 2,
    });
    expect(objective).toHaveValue("");
    expect(screen.queryByTestId("goal-composer-options")).not.toBeInTheDocument();
  });
});
