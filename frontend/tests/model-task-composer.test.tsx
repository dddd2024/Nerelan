import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NewTaskComposer } from "@/components/new-task-composer";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

describe("Connection/Binding-aware task composer", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("preselects the first enabled OpenCode Binding for the OpenCode executor", async () => {
    renderWithProviders(
      <NewTaskComposer open onClose={vi.fn()} onSubmit={vi.fn()} />,
    );

    const bindingSelect = await screen.findByTestId("task-opencode-binding-select");
    await waitFor(() => {
      expect(bindingSelect).toHaveValue("coding-binding");
    });
  });

  it("submits the selected Binding for OpenCode with no API Key prompt", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onClose = vi.fn();
    renderWithProviders(
      <NewTaskComposer open onClose={onClose} onSubmit={onSubmit} />,
    );

    await screen.findByTestId("task-opencode-binding-select");
    await user.type(screen.getByLabelText("任务标题"), "通过绑定提交 OpenCode 任务");
    await user.click(screen.getByTestId("submit-new-task"));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "通过绑定提交 OpenCode 任务",
        executorKind: "opencode",
        bindingRef: "coding-binding",
        permissionProfile: "ASK_FOR_APPROVAL",
      }),
    );
    expect((onSubmit.mock.calls[0][0] as { modelProfileId?: string }).modelProfileId).toBeUndefined();
    expect(screen.queryByLabelText("API Key")).not.toBeInTheDocument();
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("fixture executor still uses modelProfileId and does not require a Binding", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onClose = vi.fn();
    renderWithProviders(
      <NewTaskComposer open onClose={onClose} onSubmit={onSubmit} />,
    );

    await screen.findByTestId("task-opencode-binding-select");
    await user.click(screen.getByTestId("executor-option-deterministic_fixture"));

    await screen.findByTestId("task-model-profile-select");
    await user.type(screen.getByLabelText("任务标题"), "fixture task");
    await user.click(screen.getByTestId("submit-new-task"));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "fixture task",
        executorKind: "deterministic_fixture",
        modelProfileId: "coding-default",
        permissionProfile: "ASK_FOR_APPROVAL",
      }),
    );
    expect((onSubmit.mock.calls[0][0] as { bindingRef?: string }).bindingRef).toBeUndefined();
  });
});