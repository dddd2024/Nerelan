import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NewTaskComposer } from "@/components/new-task-composer";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

describe("model-aware task composer", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("preselects the default enabled model profile", async () => {
    renderWithProviders(
      <NewTaskComposer open onClose={vi.fn()} onSubmit={vi.fn()} />,
    );

    const selector = await screen.findByLabelText("模型配置");
    await waitFor(() => {
      expect(selector).toHaveValue("coding-default");
    });
  });

  it("submits the selected model profile with the task", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onClose = vi.fn();
    renderWithProviders(
      <NewTaskComposer open onClose={onClose} onSubmit={onSubmit} />,
    );

    await screen.findByLabelText("模型配置");
    await user.type(screen.getByLabelText("任务标题"), "修改 README 并运行测试");
    await user.click(screen.getByTestId("submit-new-task"));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "修改 README 并运行测试",
        modelProfileId: "coding-default",
        permissionProfile: "ASK_FOR_APPROVAL",
      }),
    );
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
