import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskDetail } from "@/components/task-detail";
import { useTask } from "@/hooks/use-task";
import { renderWithProviders } from "./test-utils";

const TASK_ID = "task-publication-731";
const REPOSITORY = "dddd2024/Nerelan";
const CHANGED_PATHS = [
  "reverse_agent/platform_v1/task_service.py",
  "frontend/src/components/task-detail.tsx",
];

const COMPLETE_PUBLICATION = {
  status: "COMPLETE",
  branch: "nerelan/task-publication-731",
  commit_sha: "711bb49d17be6521b11b76a0407aa948183509f6",
  pr_number: 732,
  pr_url: "https://github.com/dddd2024/Nerelan/pull/732",
  base_branch: "main",
  failure_classification: "",
};

function taskResponse(publication: Record<string, unknown> | null) {
  const changes = CHANGED_PATHS.map((path) => ({
    path,
    status: "modified",
    additions: 1,
    deletions: 0,
    diff: "",
  }));
  return {
    id: TASK_ID,
    title: "Publish the reviewed task",
    repository: REPOSITORY,
    status: "READY_FOR_REVIEW",
    state: "READY_FOR_HUMAN",
    executor_kind: "opencode",
    execution_id: "exec-publication-731",
    model_profile_ref: "",
    binding_ref: "coding-default",
    permission_profile: "ASK_FOR_APPROVAL",
    branch: "owner/task-publication-731",
    created_at: "2026-09-10T04:00:00Z",
    updated_at: "2026-09-10T04:30:00Z",
    failure_classification: "",
    failure_detail: "",
    validation_command_id: "git_diff_check",
    validation_exit_code: 0,
    changed_files: changes,
    evidence: [],
    events: [],
    publication,
    frontend_task: {
      id: TASK_ID,
      title: "Publish the reviewed task",
      state: "READY_FOR_HUMAN",
      riskTier: "R1",
      updatedAt: "2026-09-10T04:30:00Z",
      blocker: "",
      nextAction: "Owner review of validated result",
      permissionProfile: "ASK_FOR_APPROVAL",
      branch: "owner/task-publication-731",
      activity: [],
      changes,
      evidence: [],
      authorityStatus: "APPROVED",
      testStatus: "PASS",
      workflowStatus: "SUCCESS",
      executor: "opencode",
    },
  };
}

function platformStatus() {
  return {
    service: "reverse-agent-platform-v2",
    autonomy: {
      autonomy_enabled: true,
      mode: "owner_activated_bounded_window",
      active_window: {
        id: "window-publication-731",
        policy_id: "publication-ui-test",
        status: "ACTIVE",
        expires_at: "2026-09-11T04:30:00Z",
        repositories: [REPOSITORY],
        capabilities: ["open_draft_pr"],
        max_tasks: 3,
        tasks_started: 1,
        tasks_completed: 1,
        max_token_units: 0,
        max_cost_micro_units: 0,
        per_task_token_reservation: 0,
        per_task_cost_reservation: 0,
        provider_quota_state: "NOT_CONFIGURED",
        enforcement_class: "POST_RUN_OBSERVED",
        observed_token_units: 0,
        observed_cost_micro_units: 0,
        unknown_observation_count: 0,
      },
    },
    coordinator: {
      enabled: false,
      active_window_id: "window-publication-731",
      last_error: "",
    },
    task_count: 1,
    goal_count: 0,
    capability_count: 1,
    live_model_calls: false,
  };
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function Harness() {
  const query = useTask(TASK_ID);
  return (
    <TaskDetail
      task={query.data}
      isLoading={query.isLoading}
      isError={query.isError}
      error={query.error}
    />
  );
}

describe("Task Draft PR publication flow", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("publishes exact server-read changed paths then refetches persisted Draft PR truth", async () => {
    let taskReads = 0;
    const publishBodies: Array<Record<string, unknown>> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const method = init?.method ?? "GET";
        if (url.endsWith("/api/platform/status")) {
          return jsonResponse(platformStatus());
        }
        if (url.endsWith(`/api/tasks/${TASK_ID}/publish`) && method === "POST") {
          publishBodies.push(JSON.parse(String(init?.body ?? "{}")));
          return jsonResponse(COMPLETE_PUBLICATION);
        }
        if (url.endsWith(`/api/tasks/${TASK_ID}`) && method === "GET") {
          taskReads += 1;
          return jsonResponse(
            taskResponse(taskReads >= 2 ? COMPLETE_PUBLICATION : null),
          );
        }
        throw new Error(`unexpected fetch: ${method} ${url}`);
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<Harness />);

    const publish = await screen.findByRole("button", { name: "Publish Draft PR" });
    await user.click(publish);

    await screen.findByRole("link", { name: /Draft PR #732/ });
    expect(screen.queryByRole("button", { name: "Publish Draft PR" })).not.toBeInTheDocument();
    expect(taskReads).toBeGreaterThanOrEqual(2);
    expect(publishBodies).toEqual([
      {
        window_id: "window-publication-731",
        base_branch: "main",
        allowed_paths: CHANGED_PATHS,
        title: "Publish the reviewed task",
        body: "",
      },
    ]);
  });

  it("restores an existing completed Draft PR on the first server read", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const method = init?.method ?? "GET";
        if (url.endsWith("/api/platform/status")) return jsonResponse(platformStatus());
        if (url.endsWith(`/api/tasks/${TASK_ID}`) && method === "GET") {
          return jsonResponse(taskResponse(COMPLETE_PUBLICATION));
        }
        throw new Error(`unexpected fetch: ${method} ${url}`);
      }),
    );

    renderWithProviders(<Harness />);

    const link = await screen.findByRole("link", { name: /Draft PR #732/ });
    expect(link).toHaveAttribute("href", COMPLETE_PUBLICATION.pr_url);
    expect(screen.queryByRole("button", { name: "Publish Draft PR" })).not.toBeInTheDocument();
  });

  it("keeps a failed publication visible and retryable without inventing a PR", async () => {
    const failed = {
      ...COMPLETE_PUBLICATION,
      status: "FAILED",
      commit_sha: "",
      pr_number: 0,
      pr_url: "",
      failure_classification: "github_draft_pr_failed",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const method = init?.method ?? "GET";
        if (url.endsWith("/api/platform/status")) return jsonResponse(platformStatus());
        if (url.endsWith(`/api/tasks/${TASK_ID}`) && method === "GET") {
          return jsonResponse(taskResponse(failed));
        }
        throw new Error(`unexpected fetch: ${method} ${url}`);
      }),
    );

    renderWithProviders(<Harness />);

    expect(
      await screen.findByText("Draft PR publication failed: github_draft_pr_failed"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("task-draft-pr")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Publish Draft PR" })).toBeEnabled();
  });

  it("disables duplicate submission while publication is pending", async () => {
    let releasePublish: ((response: Response) => void) | undefined;
    const pending = new Promise<Response>((resolve) => {
      releasePublish = resolve;
    });
    let publishCalls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const method = init?.method ?? "GET";
        if (url.endsWith("/api/platform/status")) return jsonResponse(platformStatus());
        if (url.endsWith(`/api/tasks/${TASK_ID}`) && method === "GET") {
          return jsonResponse(taskResponse(null));
        }
        if (url.endsWith(`/api/tasks/${TASK_ID}/publish`) && method === "POST") {
          publishCalls += 1;
          return pending;
        }
        throw new Error(`unexpected fetch: ${method} ${url}`);
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<Harness />);
    const publish = await screen.findByRole("button", { name: "Publish Draft PR" });
    await user.click(publish);

    await waitFor(() => expect(publish).toBeDisabled());
    await user.click(publish);
    expect(publishCalls).toBe(1);

    releasePublish?.(jsonResponse(COMPLETE_PUBLICATION));
  });
});
