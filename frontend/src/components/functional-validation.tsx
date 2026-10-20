import { FUNCTIONAL_PROFILES, functionalStatusLabel, normalizeFunctionalValidation } from "@/lib/functional-validation";
import { taskCopy, type UiLocale } from "@/lib/ui-locale";

/**
 * The primary surface answers what happened and what the user can do; the
 * proof policy, exit codes and digests stay inside the `验证详情` disclosure so
 * developer audits keep exact access (#1200). Gates are unchanged: anything
 * short of host-bound VERIFIED still renders as a non-success.
 */
export function FunctionalValidationView({ evidence, executor, locale }: { evidence: unknown; executor?: string; locale?: UiLocale }) {
  const proof = normalizeFunctionalValidation(evidence, executor);
  const copy = taskCopy(locale).functional;
  const label = functionalStatusLabel(proof.status, locale);
  const body = proof.status === "VERIFIED" ? copy.verifiedBody
    : proof.status === "FIXTURE_VERIFIED" ? copy.fixtureBody
      : proof.status === "FAILED" ? copy.failedBody : copy.missingBody;
  // Only point at an operation the product actually offers (choosing checks in
  // the goal plan); otherwise say plainly that results are pending.
  const next = proof.status === "VERIFIED" ? undefined
    : proof.status === "FAILED" ? copy.nextFixFailure
      : proof.contract_digest ? copy.nextWait : copy.nextChooseChecks;
  return <section aria-label={copy.sectionLabel} className="mt-3 space-y-2 rounded-xl border border-ra-border p-3 text-sm">
    <p className="font-medium">{label}</p>
    <p className="text-xs text-ra-text-secondary">{body}</p>
    {next && <p className="text-xs text-ra-text-secondary" data-testid="functional-next-action">{copy.nextLabel}{next}</p>}
    {proof.artifact_input && <p className="text-xs">{copy.inputFrom(proof.artifact_input.plan_task_id)}</p>}
    {proof.checks?.length ? <ul className="space-y-2">{proof.checks.map((check, index) => <li key={`${index}:${check.profile_id}:${check.working_directory}`} className="break-words text-xs">
      <span>{FUNCTIONAL_PROFILES[check.profile_id]} · {check.working_directory}</span>
      <p>{copy.exitCode(check.exit_code === undefined ? copy.unknown : String(check.exit_code))}{check.timed_out ? copy.timedOut : ""}</p>
      {check.test_report ? <p>{copy.reportCounts(check.test_report.tests, check.test_report.passed, check.test_report.failed, check.test_report.skipped)}</p> : <p>{copy.reportMissing}</p>}
    </li>)}</ul> : null}
    <details className="text-xs" data-testid="functional-validation-details">
      <summary className="cursor-pointer">{copy.detailsSummary}</summary>
      <p className="mt-2 text-ra-text-secondary">{copy.proofPolicy}</p>
      <dl className="mt-2 space-y-1 break-all font-mono">{([
        [copy.fields.baseCommit, proof.base_commit], [copy.fields.head, proof.head], [copy.fields.tree, proof.tree],
        [copy.fields.contract, proof.contract_digest], [copy.fields.result, proof.result_digest],
        [copy.fields.runId, proof.run_id], [copy.fields.lease, proof.lease_epoch], [copy.fields.reason, proof.reason],
        [copy.fields.inputTask, proof.artifact_input?.task_id], [copy.fields.inputExecution, proof.artifact_input?.execution_id],
        [copy.fields.inputCommit, proof.artifact_input?.commit], [copy.fields.inputTree, proof.artifact_input?.tree],
        [copy.fields.inputResult, proof.artifact_input?.result_digest], [copy.fields.inputBinding, proof.artifact_input?.binding_digest],
      ] as const).map(([name, value]) => value !== undefined && value !== "" ? <div key={name}><dt>{name}</dt><dd>{value}</dd></div> : null)}</dl>
    </details>
  </section>;
}
