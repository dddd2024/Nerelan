import { screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
  {
    full_name: "dddd2024/private-repo",
    html_url: "https://github.com/dddd2024/private-repo",
    is_private: true,
    visibility: "private",
    default_branch: "develop",
  },
];

function makeQueryClientWithRepos(repos = FAKE_REPOS) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: Infinity },
    },
  });
  qc.setQueryData(["repositories"], repos);
  return qc;
}

function ComposerMount({
  submit,
  queryClient,
}: {
  submit: (input: unknown) => void;
  queryClient?: QueryClient;
}) {
  const qc = queryClient ?? makeQueryClientWithRepos();
  return (
    <QueryClientProvider client={qc}>
      <NewTaskComposer open={true} onClose={() => undefined} onSubmit={submit} />
    </QueryClientProvider>
  );
}

describe("repository selection for real-executor tasks", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("repository list is loaded and available in the dropdown", async () => {
    renderWithProviders(<ComposerMount submit={vi.fn()} />);

    const select = await screen.findByTestId("task-opencode-repository-select");
    expect(select).toBeInTheDocument();

    await waitFor(() => {
      const options = Array.from((select as HTMLSelectElement).options);
      expect(options.length).toBeGreaterThanOrEqual(2);
      expect(options[0].value).toBe(
        "https://github.com/dddd2024/reverse-agent",
      );
    }, { timeout: 3000 });
  });

  it("a repository can be selected and its canonical URL is sent as task repository", async () => {
    const mockSubmit = vi.fn();
    renderWithProviders(
      <ComposerMount submit={mockSubmit} queryClient={makeQueryClientWithRepos(FAKE_REPOS)} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "real opencode task with repo" },
    });

    await waitFor(() => {
      expect(screen.getByTestId("task-opencode-binding-select")).toHaveValue("coding-binding");
    }, { timeout: 3000 });
    await waitFor(() => {
      expect(screen.getByTestId("task-opencode-repository-select")).toHaveValue(
        "https://github.com/dddd2024/reverse-agent",
      );
    }, { timeout: 3000 });

    fireEvent.change(screen.getByTestId("task-opencode-repository-select"), {
      target: { value: "https://github.com/dddd2024/private-repo" },
    });

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const submitted = mockSubmit.mock.calls[0][0] as {
      title?: string;
      executorKind?: string;
      bindingRef?: string;
      repository?: string;
    };
    expect(submitted.title).toBe("real opencode task with repo");
    expect(submitted.executorKind).toBe("opencode");
    expect(submitted.bindingRef).toBe("coding-binding");
    expect(submitted.repository).toBe("https://github.com/dddd2024/private-repo");
  });

  it("real-executor submission without repository is disabled (fail-closed)", async () => {
    const qc = makeQueryClientWithRepos([]);
    const mockSubmit = vi.fn();
    renderWithProviders(
      <ComposerMount submit={mockSubmit} queryClient={qc} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "no repo task" },
    });

    await waitFor(() => {
      expect(screen.getByTestId("task-opencode-binding-select")).toHaveValue("coding-binding");
    }, { timeout: 3000 });

    const submitBtn = screen.getByTestId("submit-new-task") as HTMLButtonElement;
    expect(submitBtn).toBeDisabled();

    fireEvent.click(screen.getByTestId("submit-new-task"));
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it("discovery failure shows a visible error state", async () => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: Infinity },
      },
    });
    qc.setQueryData(["repositories"], []);

    renderWithProviders(<ComposerMount submit={vi.fn()} queryClient={qc} />);

    await waitFor(() => {
      expect(
        screen.queryByTestId("no-repositories-hint"),
      ).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("no old sample repository fallback in composer", async () => {
    const mockSubmit = vi.fn();
    renderWithProviders(<ComposerMount submit={mockSubmit} />);

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "test" },
    });

    const composerContent = screen.getByTestId("new-task-composer-content");
    expect(composerContent.textContent).not.toContain(
      "https://github.com/example/reverse-agent.git",
    );
  });

  it("fixture executor does not require repository selection", async () => {
    const qc = makeQueryClientWithRepos([]);
    const mockSubmit = vi.fn();
    renderWithProviders(
      <ComposerMount submit={mockSubmit} queryClient={qc} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "fixture task" },
    });

    fireEvent.click(screen.getByTestId("executor-option-deterministic_fixture"));

    await waitFor(() => {
      expect(screen.getByTestId("submit-new-task")).not.toBeDisabled();
    }, { timeout: 3000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const submitted = mockSubmit.mock.calls[0][0] as {
      executorKind?: string;
      repository?: string;
      bindingRef?: string;
      title?: string;
    };
    expect(submitted.executorKind).toBe("deterministic_fixture");
    expect(submitted.repository).toBeUndefined();
    expect(submitted.bindingRef).toBeUndefined();
    expect(submitted.title).toBe("fixture task");
  });

  it("existing Binding semantics remain intact (repository is separate from binding)", async () => {
    const mockSubmit = vi.fn();
    renderWithProviders(<ComposerMount submit={mockSubmit} />);

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "separate concerns" },
    });

    await waitFor(() => {
      expect(screen.getByTestId("task-opencode-binding-select")).toHaveValue("coding-binding");
    }, { timeout: 3000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const submitted = mockSubmit.mock.calls[0][0] as {
      bindingRef?: string;
      repository?: string;
    };
    expect(submitted.bindingRef).toBe("coding-binding");
    expect(submitted.repository).toBe("https://github.com/dddd2024/reverse-agent");
    expect(submitted.bindingRef).not.toContain("github");
    expect(submitted.repository).not.toContain("coding-binding");
  });
});
