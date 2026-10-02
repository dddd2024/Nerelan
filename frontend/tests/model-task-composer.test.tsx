import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GoalComposer } from "@/components/goal-composer";
import { NewTaskComposer } from "@/components/new-task-composer";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

const FAKE_REPOS = [
  {
    full_name: "dddd2024/reverse-agent",
    html_url: "https://github.com/dddd2024/reverse-agent",
    is_private: false,
    visibility: "public",
    default_branch: "main",
  },
];

function makeQueryClient() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: Infinity },
    },
  });
  qc.setQueryData(["repositories"], FAKE_REPOS);
  return qc;
}

function ComposerMount({
  submit,
  onClose,
  queryClient,
}: {
  submit: (input: unknown) => void;
  onClose?: () => void;
  queryClient?: QueryClient;
}) {
  const qc = queryClient ?? makeQueryClient();
  return (
    <QueryClientProvider client={qc}>
      <NewTaskComposer
        open={true}
        onClose={onClose ?? (() => undefined)}
        onSubmit={submit}
      />
    </QueryClientProvider>
  );
}

describe("Connection/Binding-aware task composer", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it.each([true, false])("native Goal requires its own binding (available=%s)", async (available) => {
    window.sessionStorage.clear();
    const user = userEvent.setup();
    const submit = vi.fn(async () => {});
    const queryClient = makeQueryClient();
    queryClient.setQueryData(["bindings"], [
      { bindingId: "other-binding", name: "Other executor", executorId: "opencode", connectionId: "other", modelId: "other", enabled: true },
      ...(available ? [{ bindingId: "native-binding", name: "Native model", executorId: "codex", connectionId: "native-login", modelId: "gpt-5.4", enabled: true }] : []),
    ]);
    renderWithProviders(<QueryClientProvider client={queryClient}><GoalComposer busy={false} onSubmit={submit} /></QueryClientProvider>);
    await user.type(screen.getByLabelText("描述最终目标"), "Native bounded Goal request");
    await user.selectOptions(screen.getByLabelText("执行模式"), "codex");
    expect(screen.getByLabelText("模型绑定")).not.toHaveTextContent("Other executor");
    const button = screen.getByLabelText("创建并审阅目标");
    if (available) {
      await waitFor(() => expect(screen.getByLabelText("模型绑定")).toHaveValue("native-binding"));
      await user.click(button);
      expect(submit).toHaveBeenCalledWith(expect.objectContaining({ executorKind: "codex", bindingRef: "native-binding" }));
    } else {
      expect(button).toBeDisabled();
      expect(submit).not.toHaveBeenCalled();
    }
    window.sessionStorage.clear();
  });

  it("submits native Codex with its own saved binding and excludes OpenCode bindings", async () => {
    const user = userEvent.setup();
    const submit = vi.fn();
    const queryClient = makeQueryClient();
    queryClient.setQueryData(["bindings"], [
      { bindingId: "native-binding", name: "Native model", executorId: "codex", connectionId: "native-login", modelId: "gpt-5.4", enabled: true },
      { bindingId: "other-binding", name: "Other executor", executorId: "opencode", connectionId: "other", modelId: "other", enabled: true },
    ]);
    renderWithProviders(<ComposerMount submit={submit} queryClient={queryClient} />);
    await user.click(screen.getByTestId("executor-option-codex"));
    const select = await screen.findByTestId("task-opencode-binding-select");
    expect(select).not.toHaveTextContent("Other executor");
    await user.selectOptions(select, "native-binding");
    await waitFor(() => expect(screen.getByTestId("task-opencode-repository-select")).toHaveValue(FAKE_REPOS[0].html_url));
    await user.type(screen.getByLabelText("任务标题"), "Native bounded task");
    await user.click(screen.getByTestId("submit-new-task"));
    expect(submit).toHaveBeenCalledWith(expect.objectContaining({ executorKind: "codex", bindingRef: "native-binding", repository: FAKE_REPOS[0].full_name }));
    expect(screen.queryByLabelText("API Key")).not.toBeInTheDocument();
  });

  it("preselects the first enabled OpenCode Binding for the OpenCode executor", async () => {
    renderWithProviders(
      <ComposerMount submit={vi.fn()} />,
    );

    const bindingSelect = await screen.findByTestId("task-opencode-binding-select");
    await waitFor(() => {
      expect(bindingSelect).toHaveValue("coding-binding");
    }, { timeout: 3000 });
  });

  it("preselects the first available GitHub repository for the OpenCode executor", async () => {
    renderWithProviders(
      <ComposerMount submit={vi.fn()} />,
    );

    const repoSelect = await screen.findByTestId("task-opencode-repository-select");
    await waitFor(() => {
      expect(repoSelect).toHaveValue("https://github.com/dddd2024/reverse-agent");
    }, { timeout: 3000 });
  });

  it("submits the selected Binding and Repository for OpenCode with no API Key prompt", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onClose = vi.fn();
    renderWithProviders(
      <ComposerMount submit={onSubmit} onClose={onClose} />,
    );

    await screen.findByTestId("task-opencode-binding-select");
    await screen.findByTestId("task-opencode-repository-select");

    await user.type(screen.getByLabelText("任务标题"), "通过绑定和仓库提交 OpenCode 任务");
    await user.click(screen.getByTestId("submit-new-task"));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "通过绑定和仓库提交 OpenCode 任务",
        executorKind: "opencode",
        bindingRef: "coding-binding",
        repository: "https://github.com/dddd2024/reverse-agent",
        permissionProfile: "ASK_FOR_APPROVAL",
      }),
    );
    expect((onSubmit.mock.calls[0][0] as { modelProfileId?: string }).modelProfileId).toBeUndefined();
    expect(screen.queryByLabelText("API Key")).not.toBeInTheDocument();
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("fixture executor submits without ModelProfile, Binding, or Repository", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onClose = vi.fn();
    renderWithProviders(
      <NewTaskComposer open onClose={onClose} onSubmit={onSubmit} />,
    );

    await user.click(screen.getByTestId("executor-option-deterministic_fixture"));

    expect(screen.queryByLabelText("模型配置")).not.toBeInTheDocument();

    await user.type(screen.getByLabelText("任务标题"), "fixture task");
    await user.click(screen.getByTestId("submit-new-task"));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "fixture task",
        executorKind: "deterministic_fixture",
        permissionProfile: "ASK_FOR_APPROVAL",
      }),
    );
    expect((onSubmit.mock.calls[0][0] as { modelProfileId?: string }).modelProfileId).toBeUndefined();
    expect((onSubmit.mock.calls[0][0] as { bindingRef?: string }).bindingRef).toBeUndefined();
    expect((onSubmit.mock.calls[0][0] as { repository?: string }).repository).toBeUndefined();
  });
});
