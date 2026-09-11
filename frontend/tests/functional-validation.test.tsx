import { afterEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { FunctionalValidationView } from "@/components/functional-validation";
import { TaskDetail } from "@/components/task-detail";
import { normalizeFunctionalValidation, functionalChecksError } from "@/lib/functional-validation";
import { useTask } from "@/hooks/use-task";
import { useTasks } from "@/hooks/use-tasks";
import { renderWithProviders } from "./test-utils";
import type { FunctionalValidation } from "@/types";

vi.mock("@/hooks/use-platform", () => ({ usePlatformStatus: () => ({ data: undefined }) }));
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

const verified: FunctionalValidation = {
  status: "VERIFIED", verified: true, contract_digest: "a".repeat(64), result_digest: "b".repeat(64),
  base_commit: "c".repeat(40), head: "d".repeat(40), tree: "e".repeat(40), run_id: "run-bound", lease_epoch: 2,
  checks: [{ profile_id: "python_pytest", working_directory: ".", exit_code: 0, timed_out: false,
    duration_ms: 42, output_digest: "f".repeat(64), output_bytes: 128, output_truncated: false,
    test_report: { format: "junit", tests: 3, passed: 2, failed: 0, skipped: 1, accepted: true } }],
};

it("shows only complete consumed-input identity and rejects malformed positive claims", () => {
  const input = { plan_task_id: "A", task_id: "task-source", execution_id: "exec-source",
    commit: "1".repeat(40), tree: "2".repeat(40), result_digest: "3".repeat(64), binding_digest: "4".repeat(64) };
  const evidence = { ...verified, artifact_input: { ...input, workspace: "PRIVATE PATH", env: "PRIVATE ENV" } };
  expect(normalizeFunctionalValidation(evidence, "opencode").artifact_input).toEqual(input);
  render(<FunctionalValidationView evidence={evidence} executor="opencode" />);
  expect(screen.getByText(/输入产物来自任务 A/)).toBeInTheDocument();
  expect(screen.getByText(input.commit)).toBeInTheDocument();
  expect(screen.queryByText(/PRIVATE/)).not.toBeInTheDocument();
  expect(normalizeFunctionalValidation({ ...evidence, artifact_input: { ...input, commit: "missing" } }, "opencode").verified).toBe(false);
});

it("shows the host-bound artifact, exact counts and digests without rendering unapproved output fields", () => {
  render(<FunctionalValidationView evidence={{ ...verified, stdout: "PRIVATE OUTPUT", argv: ["PRIVATE COMMAND"] }} executor="opencode" />);
  expect(screen.getByText("功能已验证")).toBeInTheDocument();
  expect(screen.getByText("共 3 项 · 通过 2 · 失败 0 · 跳过 1")).toBeInTheDocument();
  expect(screen.getByText(verified.tree!)).toBeInTheDocument();
  expect(screen.getByText(verified.result_digest!)).toBeInTheDocument();
  expect(screen.queryByText(/PRIVATE/)).not.toBeInTheDocument();
});

it.each([
  ["missing", undefined], ["stale", { ...verified, status: "UNVERIFIED", verified: false }],
  ["missing tree", { ...verified, tree: "" }], ["zero tests", { ...verified, checks: [] }],
  ["unknown profile", { ...verified, checks: [{ ...verified.checks![0], profile_id: "shell" }] }],
  ["incomplete report", { ...verified, checks: [{ ...verified.checks![0], test_report: undefined }] }],
  ["timeout", { ...verified, checks: [{ ...verified.checks![0], timed_out: true }] }],
  ["contradictory counts", { ...verified, checks: [{ ...verified.checks![0], test_report: { ...verified.checks![0].test_report, tests: 99 } }] }],
])("does not promote %s evidence to functional success", (_, evidence) => {
  render(<FunctionalValidationView evidence={evidence} executor="opencode" />);
  expect(screen.getByText("功能尚未验证")).toBeInTheDocument();
  expect(screen.queryByText("功能已验证")).not.toBeInTheDocument();
});

it("keeps fixture, failed checks and escaped failure reason visibly distinct", () => {
  const view = render(<FunctionalValidationView evidence={{ ...verified, status: "FIXTURE_VERIFIED", verified: false }} executor="deterministic_fixture" />);
  expect(screen.getByText("仅测试夹具通过")).toBeInTheDocument();
  expect(normalizeFunctionalValidation(verified, "deterministic_fixture").verified).toBe(false);
  view.rerender(<FunctionalValidationView evidence={{ ...verified, status: "FAILED", verified: false, reason: "<script>unsafe()</script>",
    checks: [{ ...verified.checks![0], exit_code: 1, test_report: { format: "junit", tests: 3, passed: 1, failed: 1, skipped: 1, accepted: false } }] }} executor="opencode" />);
  expect(screen.getByText("功能检查未通过")).toBeInTheDocument();
  expect(screen.getByText("共 3 项 · 通过 1 · 失败 1 · 跳过 1")).toBeInTheDocument();
  expect(screen.getByText("<script>unsafe()</script>")).toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
});

it.each(["../secret", "/tmp", "C:/repo", "a\\b", "a/../b", "a//b", "a/./b", " a", "", "a".repeat(241), ...[0, 10, 31].map((code) => `a${String.fromCharCode(code)}b`)])("rejects invalid check directory %s", (path) => {
  expect(functionalChecksError([{ profile_id: "python_pytest", working_directory: path }])).not.toBe("");
});

function TaskFlow({ list }: { list: boolean }) {
  const detail = useTask(list ? undefined : "task-bound");
  const tasks = useTasks();
  const task = list ? tasks.data?.[0] : detail.data;
  return <><output data-testid="mapped-identities">{JSON.stringify(task)}</output><TaskDetail task={task} isLoading={!task} isError={false} /></>;
}

it.each([false, true])("retains evidence and execution identity through HTTP client, %s list hook and TaskDetail", async (list) => {
  vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
  const task = { id: "task-bound", title: "Bound implementation", repository: "owner/repo", status: "READY_FOR_REVIEW",
    executor_kind: "opencode", execution_id: "execution-bound", validation_command_id: "approved_functional_checks", validation_exit_code: 0,
    functionalValidation: verified, frontend_task: { id: "task-bound", title: "Bound implementation", state: "READY_FOR_HUMAN", executor: "opencode", testStatus: "PASS" } };
  vi.stubGlobal("fetch", vi.fn(async (url: string) => new Response(JSON.stringify(url.endsWith("/api/tasks") ? { tasks: [task] } : task))));
  renderWithProviders(<TaskFlow list={list} />);
  await waitFor(() => expect(screen.getByText("功能已验证")).toBeInTheDocument());
  const mapped = JSON.parse(screen.getByTestId("mapped-identities").textContent!);
  expect(mapped).toMatchObject({ executionId: "execution-bound", validationCommandId: "approved_functional_checks", validationExitCode: 0, testStatus: "PASS", functionalValidation: verified });
  expect(screen.getByText("execution-bound")).toBeInTheDocument();
});
