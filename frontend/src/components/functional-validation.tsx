import { FUNCTIONAL_PROFILES, FUNCTIONAL_STATUS_LABELS, normalizeFunctionalValidation } from "@/lib/functional-validation";

export function FunctionalValidationView({ evidence, executor }: { evidence: unknown; executor?: string }) {
  const proof = normalizeFunctionalValidation(evidence, executor);
  const label = FUNCTIONAL_STATUS_LABELS[proof.status];
  return <section aria-label="功能验证" className="mt-3 space-y-2 rounded-xl border border-ra-border p-3 text-sm">
    <p className="font-medium">{label}</p>
    <p className="text-xs text-ra-text-secondary">{proof.status === "VERIFIED"
      ? "主机已将测试结果绑定到本次任务的代码产物。发布与交付仍需各自的验收。"
      : proof.status === "FIXTURE_VERIFIED" ? "这是无模型测试夹具结果，不能证明真实实现已交付。"
        : "需要当前代码产物的有效功能检查证据。补丁格式检查或退出码 0 不能单独证明功能通过。"}</p>
    {!proof.contract_digest && <p className="text-xs text-ra-text-secondary">可在目标计划中选择功能检查，审阅后再批准执行。</p>}
    {proof.artifact_input && <p className="text-xs">输入产物来自任务 {proof.artifact_input.plan_task_id}，已绑定到本次验证。</p>}
    {proof.checks?.length ? <ul className="space-y-2">{proof.checks.map((check, index) => <li key={`${index}:${check.profile_id}:${check.working_directory}`} className="break-words text-xs">
      <span>{FUNCTIONAL_PROFILES[check.profile_id]} · {check.working_directory}</span>
      <p>退出码：{check.exit_code ?? "未知"}{check.timed_out ? " · 已超时" : ""}</p>
      {check.test_report ? <p>共 {check.test_report.tests} 项 · 通过 {check.test_report.passed} · 失败 {check.test_report.failed} · 跳过 {check.test_report.skipped}</p> : <p>缺少完整测试报告</p>}
    </li>)}</ul> : null}
    {(proof.contract_digest || proof.reason) && <details className="text-xs">
      <summary className="cursor-pointer">查看验证证据</summary>
      <dl className="mt-2 space-y-1 break-all font-mono">{([
        ["基线 commit", proof.base_commit], ["HEAD", proof.head], ["产物 tree", proof.tree],
        ["检查契约 SHA256", proof.contract_digest], ["结果 SHA256", proof.result_digest],
        ["运行 ID", proof.run_id], ["租约版本", proof.lease_epoch], ["原因", proof.reason],
        ["输入任务 ID", proof.artifact_input?.task_id], ["输入执行 ID", proof.artifact_input?.execution_id],
        ["输入 commit", proof.artifact_input?.commit], ["输入 tree", proof.artifact_input?.tree],
        ["输入结果 SHA256", proof.artifact_input?.result_digest], ["输入绑定 SHA256", proof.artifact_input?.binding_digest],
      ] as const).map(([name, value]) => value !== undefined && value !== "" ? <div key={name}><dt>{name}</dt><dd>{value}</dd></div> : null)}</dl>
    </details>}
  </section>;
}
