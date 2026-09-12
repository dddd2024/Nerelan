import type { FunctionalCheckInput, FunctionalCheckResult, FunctionalValidation, TestStatus } from "@/types";

export const FUNCTIONAL_PROFILES = { python_pytest: "Python · pytest", npm_test: "JavaScript · npm test" } as const;

export const FUNCTIONAL_STATUS_LABELS: Record<FunctionalValidation["status"], string> = {
  VERIFIED: "功能已验证",
  UNVERIFIED: "功能尚未验证",
  FAILED: "功能检查未通过",
  FIXTURE_VERIFIED: "仅测试夹具通过",
};

export function functionalChecksError(checks: FunctionalCheckInput[] = []): string {
  if (checks.length > 8) return "每个任务最多选择 8 项功能检查。";
  const seen = new Set<string>();
  for (const check of checks) {
    if (!Object.hasOwn(FUNCTIONAL_PROFILES, check.profile_id)) return "请选择支持的功能检查。";
    const path = check.working_directory;
    if (!path || path.length > 240 || path !== path.trim() || /[\\:]/.test(path) || Array.from(path).some((character) => character.charCodeAt(0) < 32)
      || (path !== "." && path.split("/").some((part) => !part || part === "." || part === ".."))) {
      return "检查目录须为仓库内的相对路径，例如 . 或 frontend；不能包含上级目录。";
    }
    const identity = `${check.profile_id}:${path}`;
    if (seen.has(identity)) return "同一检查与目录不能重复。";
    seen.add(identity);
  }
  return "";
}

function record(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
function integer(value: unknown): value is number { return typeof value === "number" && Number.isSafeInteger(value); }
function count(value: unknown): value is number { return integer(value) && value >= 0; }
function hash(value: unknown, length: number): value is string { return typeof value === "string" && new RegExp(`^[a-f0-9]{${length}}$`).test(value); }

/** Whitelist presentation fields and fail closed on incomplete positive responses.
 * Host validation remains authoritative, including freshness and artifact binding. */
export function normalizeFunctionalValidation(value: unknown, executor?: string): FunctionalValidation {
  const raw = record(value);
  const proof: FunctionalValidation = { status: "UNVERIFIED", verified: false };
  for (const key of ["contract_digest", "result_digest"] as const) if (hash(raw[key], 64)) proof[key] = raw[key];
  for (const key of ["base_commit", "head", "tree"] as const) if (hash(raw[key], 40)) proof[key] = raw[key];
  for (const key of ["reason", "run_id"] as const) if (typeof raw[key] === "string") proof[key] = raw[key].slice(0, 512);
  if (count(raw.lease_epoch)) proof.lease_epoch = raw.lease_epoch;
  const input = record(raw.artifact_input);
  const validInput = ["plan_task_id", "task_id", "execution_id"].every((key) =>
    typeof input[key] === "string" && /^[A-Za-z0-9_-]{1,160}$/.test(input[key] as string))
    && hash(input.commit, 40) && hash(input.tree, 40) && hash(input.result_digest, 64) && hash(input.binding_digest, 64);
  if (validInput) proof.artifact_input = {
    plan_task_id: input.plan_task_id as string, task_id: input.task_id as string, execution_id: input.execution_id as string,
    commit: input.commit as string, tree: input.tree as string, result_digest: input.result_digest as string, binding_digest: input.binding_digest as string,
  };
  const checks = Array.isArray(raw.checks) ? raw.checks.slice(0, 8) : [];
  proof.checks = checks.flatMap((value): FunctionalCheckResult[] => {
    const check = record(value);
    if (typeof check.profile_id !== "string" || !Object.hasOwn(FUNCTIONAL_PROFILES, check.profile_id)
      || typeof check.working_directory !== "string") return [];
    const item: FunctionalCheckResult = {
      profile_id: check.profile_id as FunctionalCheckInput["profile_id"], working_directory: check.working_directory,
    };
    if (functionalChecksError([item])) return [];
    if (integer(check.exit_code)) item.exit_code = check.exit_code;
    if (typeof check.timed_out === "boolean") item.timed_out = check.timed_out;
    if (count(check.duration_ms)) item.duration_ms = check.duration_ms;
    if (hash(check.output_digest, 64)) item.output_digest = check.output_digest;
    if (count(check.output_bytes)) item.output_bytes = check.output_bytes;
    if (typeof check.output_truncated === "boolean") item.output_truncated = check.output_truncated;
    const report = record(check.test_report);
    if ((report.format === "junit" || report.format === "tap") && count(report.tests) && count(report.passed)
      && count(report.failed) && count(report.skipped) && report.tests === report.passed + report.failed + report.skipped) {
      item.test_report = { format: report.format, tests: report.tests, passed: report.passed, failed: report.failed,
        skipped: report.skipped, accepted: report.accepted === true && report.passed > 0 && report.failed === 0 };
    }
    return [item];
  });
  if (raw.status === "FAILED" || raw.status === "FIXTURE_VERIFIED") proof.status = raw.status;
  const complete = proof.contract_digest && proof.result_digest && proof.base_commit && proof.head && proof.tree
    && (raw.artifact_input === undefined || validInput)
    && Array.isArray(raw.checks) && raw.checks.length === proof.checks.length && proof.checks.length > 0
    && !functionalChecksError(proof.checks)
    && proof.checks.every((check) => check.exit_code === 0 && check.timed_out === false && check.test_report?.accepted);
  if (raw.status === "VERIFIED" && raw.verified === true && executor === "opencode" && complete) {
    proof.status = "VERIFIED";
    proof.verified = true;
  }
  return proof;
}

export function functionalTestStatus(status: TestStatus, proof: FunctionalValidation | undefined, command?: string): TestStatus {
  if (status === "FAIL" || proof?.status === "FAILED") return "FAIL";
  if (proof?.verified) return "PASS";
  if (proof || command === "approved_functional_checks") return status === "RUNNING" ? "RUNNING" : "PENDING";
  return status;
}
