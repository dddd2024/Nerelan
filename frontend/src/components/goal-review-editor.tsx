import { useEffect, useState } from "react";
import { useBindings } from "@/hooks/use-model-access";
import { useRepositories } from "@/hooks/use-repositories";
import type { GoalConfigurationInput, GoalPlanInput } from "@/lib/goal-continuation-operation";
import type { PlatformGoal } from "@/lib/platform-client";
import { FUNCTIONAL_PROFILES, functionalChecksError } from "@/lib/functional-validation";
import type { FunctionalCheckInput } from "@/types";

interface Props {
  goal: PlatformGoal;
  busy: boolean;
  onEditingChange: (editing: boolean) => void;
  onConfigurationReady: (ready: boolean) => void;
  onSaveConfiguration: (goal: PlatformGoal, input: GoalConfigurationInput) => Promise<unknown>;
  onSavePlan: (goal: PlatformGoal, input: GoalPlanInput) => Promise<unknown>;
}

function configuration(goal: PlatformGoal): GoalConfigurationInput {
  return { objective: goal.objective, repository: goal.repository, executor_kind: goal.executor_kind,
    orchestration_mode: goal.orchestration_mode, binding_ref: goal.binding_ref };
}

const fieldClass = "mt-1 w-full rounded-lg border border-ra-border bg-ra-base px-3 py-2 text-sm text-ra-text";
const buttonClass = "rounded-lg border border-ra-border px-3 py-2 text-sm text-ra-text disabled:opacity-50";

export function GoalReviewEditor({ goal, busy, onEditingChange, onConfigurationReady, onSaveConfiguration, onSavePlan }: Props) {
  const [mode, setMode] = useState<"configuration" | "plan" | null>(null);
  const [base, setBase] = useState(goal);
  const [draft, setDraft] = useState(() => configuration(goal));
  const [tasks, setTasks] = useState(() => structuredClone(goal.tasks));
  const [criteria, setCriteria] = useState(goal.acceptance_criteria.join("\n"));
  const [error, setError] = useState("");
  const bindingsQuery = useBindings();
  const repositoriesQuery = useRepositories({ enabled: goal.executor_kind === "opencode" || (mode === "configuration" && draft.executor_kind === "opencode") });
  const bindings = (bindingsQuery.data ?? []).filter((binding) => binding.enabled && binding.executorId === "opencode");
  const repositories = repositoriesQuery.data ?? [];
  const editable = ["DRAFT", "PLANNED", "APPROVED"].includes(goal.status) && !goal.task_links?.length;
  const stale = base.revision !== goal.revision || base.status !== goal.status;
  const isOpenCode = draft.executor_kind === "opencode";
  const configurationValid = draft.objective.trim().length > 0 && draft.repository.includes("/")
    && (!isOpenCode || (!bindingsQuery.isError && !repositoriesQuery.isError
      && bindings.some((binding) => binding.bindingId === draft.binding_ref)
      && repositories.some((repository) => repository.full_name === draft.repository)));
  const planValid = tasks.length > 0 && tasks.every((task) => task.title.trim() && task.instruction?.trim())
    && tasks.every((task) => !functionalChecksError(task.validation_checks))
    && tasks.every((task) => !task.artifact_input || (task.dependencies.includes(task.artifact_input.plan_task_id)
      && task.artifact_input.plan_task_id !== task.id && Boolean(task.validation_checks?.length)
      && tasks.some((source) => source.id === task.artifact_input?.plan_task_id && source.validation_checks?.length)))
    && criteria.split("\n").some((line) => line.trim());
  const currentConfigurationReady = goal.executor_kind === "deterministic_fixture"
    || (!bindingsQuery.isError && !repositoriesQuery.isError
      && bindings.some((binding) => binding.bindingId === goal.binding_ref)
      && repositories.some((repository) => repository.full_name === goal.repository));

  useEffect(() => { onEditingChange(mode !== null); }, [mode, onEditingChange]);
  useEffect(() => { onConfigurationReady(currentConfigurationReady); }, [currentConfigurationReady, onConfigurationReady]);

  function reload(nextMode = mode) {
    setBase(structuredClone(goal));
    setDraft(configuration(goal));
    setTasks(structuredClone(goal.tasks));
    setCriteria(goal.acceptance_criteria.join("\n"));
    setError("");
    setMode(nextMode);
  }

  async function save() {
    if (stale || !editable || busy) return;
    setError("");
    try {
      if (mode === "configuration") {
        if (!configurationValid) return;
        await onSaveConfiguration(base, { ...draft, objective: draft.objective.trim() });
      } else {
        if (!planValid || goal.status !== "PLANNED") return;
        await onSavePlan(base, { tasks, acceptance_criteria: criteria.split("\n").map((line) => line.trim()).filter(Boolean) });
      }
      setMode(null);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "保存失败，本地修改已保留。");
    }
  }

  function updateChecks(index: number, checks: FunctionalCheckInput[]) {
    setTasks(tasks.map((task, item) => item === index ? { ...task, validation_checks: checks } : task));
  }

  return <div className="mt-5" data-testid="goal-review-editor">
    {!mode && editable && <div className="flex flex-wrap gap-2">
      <button type="button" className={buttonClass} disabled={busy} onClick={() => reload("configuration")}>编辑目标配置</button>
      {goal.status === "PLANNED" && <button type="button" className={buttonClass} disabled={busy} onClick={() => reload("plan")}>编辑当前计划</button>}
    </div>}
    {mode && <div className="space-y-4 rounded-xl border border-ra-border bg-ra-light/20 p-4">
      <p className="text-sm font-medium">{mode === "configuration" ? "目标配置" : "计划内容"} · 版本 {base.revision}</p>
      <p className="text-xs text-ra-text-secondary">保存修改后需要重新审阅。编辑期间不会批准或启动目标。</p>
      {(stale || !editable) && <div role="alert" className="text-sm text-amber-600">
        目标状态已更新，本地输入仍保留。请重新载入后核对修改。
        <button type="button" className={`${buttonClass} ml-2`} disabled={busy} onClick={() => reload()}>放弃本地修改并重新载入</button>
      </div>}
      {mode === "configuration" ? <>
        <label className="block text-sm">目标规格<textarea aria-label="目标规格" className={fieldClass} value={draft.objective}
          onChange={(event) => setDraft({ ...draft, objective: event.target.value })} disabled={busy} rows={3} /></label>
        <label className="block text-sm">执行器<select aria-label="目标执行器" className={fieldClass} value={draft.executor_kind} disabled={busy}
          onChange={(event) => { const executor = event.target.value as PlatformGoal["executor_kind"];
            setDraft({ ...draft, executor_kind: executor, orchestration_mode: executor === "opencode" ? "sequential_team" : "single", binding_ref: "" }); }}>
          <option value="deterministic_fixture">确定性测试（无模型）</option><option value="opencode">OpenCode</option>
        </select></label>
        {isOpenCode ? <>
          <label className="block text-sm">仓库<select aria-label="目标仓库" className={fieldClass} value={draft.repository} disabled={busy || repositoriesQuery.isPending}
            onChange={(event) => setDraft({ ...draft, repository: event.target.value })}>
            <option value="">选择仓库</option>
            {draft.repository && !repositories.some((repository) => repository.full_name === draft.repository)
              && <option value={draft.repository} disabled>{draft.repository}（未在当前列表中找到）</option>}
            {repositories.map((repository) => <option key={repository.full_name} value={repository.full_name}>{repository.full_name}</option>)}
          </select></label>
          <label className="block text-sm">模型绑定<select aria-label="目标模型绑定" className={fieldClass} value={draft.binding_ref} disabled={busy || bindingsQuery.isPending}
            onChange={(event) => setDraft({ ...draft, binding_ref: event.target.value })}>
            <option value="">选择模型绑定</option>
            {draft.binding_ref && !bindings.some((binding) => binding.bindingId === draft.binding_ref)
              && <option value={draft.binding_ref} disabled>{draft.binding_ref}（不可用）</option>}
            {bindings.map((binding) => <option key={binding.bindingId} value={binding.bindingId}>{binding.name} · {binding.modelId}</option>)}
          </select></label>
          <label className="block text-sm">协作方式<select aria-label="目标协作方式" className={fieldClass} value={draft.orchestration_mode} disabled={busy}
            onChange={(event) => setDraft({ ...draft, orchestration_mode: event.target.value as PlatformGoal["orchestration_mode"] })}>
            <option value="sequential_team">同一任务中的多 Agent 协作</option><option value="single">单 Agent</option>
          </select></label>
          {repositoriesQuery.isError && <p role="alert">仓库列表读取失败。<button type="button" onClick={() => void repositoriesQuery.refetch()}>重试仓库列表</button></p>}
          {bindingsQuery.isError && <p role="alert">模型绑定读取失败。<button type="button" onClick={() => void bindingsQuery.refetch()}>重试模型绑定</button></p>}
          {(bindingsQuery.isPending || repositoriesQuery.isPending) && <p className="text-sm">正在读取仓库与模型绑定…</p>}
          {!bindingsQuery.isPending && !bindingsQuery.isError && bindings.length === 0 && <p className="text-sm">暂无可用的 OpenCode 模型绑定，请先在设置中配置。</p>}
          {!repositoriesQuery.isPending && !repositoriesQuery.isError && repositories.length === 0 && <p className="text-sm">暂无可选仓库。</p>}
        </> : <label className="block text-sm">仓库<input aria-label="目标仓库" className={fieldClass} value={draft.repository} disabled={busy}
          onChange={(event) => setDraft({ ...draft, repository: event.target.value })} /></label>}
      </> : <>
        {tasks.map((task, index) => <fieldset key={task.id} className="space-y-2 rounded-lg border border-ra-border p-3">
          <legend className="text-xs">{task.id} · 前置任务：{task.dependencies.join("、") || "无"}</legend>
          <label className="block text-sm">任务名称<input aria-label={`任务 ${task.id} 名称`} className={fieldClass} value={task.title} disabled={busy}
            onChange={(event) => setTasks(tasks.map((entry, item) => item === index ? { ...entry, title: event.target.value } : entry))} /></label>
          <label className="block text-sm">任务说明<textarea aria-label={`任务 ${task.id} 说明`} className={fieldClass} value={task.instruction ?? ""} disabled={busy} rows={4}
            onChange={(event) => setTasks(tasks.map((entry, item) => item === index ? { ...entry, instruction: event.target.value } : entry))} /></label>
          <label className="block text-sm">输入产物<select aria-label={`任务 ${task.id} 输入产物`} className={fieldClass}
            value={task.artifact_input?.plan_task_id ?? ""} disabled={busy}
            onChange={(event) => setTasks(tasks.map((entry, item) => item === index ? { ...entry,
              artifact_input: event.target.value ? { plan_task_id: event.target.value } : null } : entry))}>
            <option value="">不使用前置任务产物</option>
            {tasks.filter((source) => source.id !== task.id && task.dependencies.includes(source.id)).map((source) =>
              <option key={source.id} value={source.id} disabled={!source.validation_checks?.length}>{source.id} · {source.title}</option>)}
          </select></label>
          <p className="text-xs text-ra-text-secondary">选择后，本任务将使用该前置任务已通过检查的代码产物。双方都需要功能检查；仅验证任务不会修改输入。</p>
          {task.artifact_input && (!task.validation_checks?.length || !tasks.some((source) => source.id === task.artifact_input?.plan_task_id && source.validation_checks?.length))
            && <p role="alert" className="text-xs text-red-500">输入任务和当前任务都需要功能检查。</p>}
          <div className="space-y-2">
            <p className="text-sm font-medium">功能检查</p>
            <p className="text-xs text-ra-text-secondary">选择任务完成后必须通过的检查。目录相对于仓库根目录；保存后须重新审阅计划。</p>
            {(task.validation_checks ?? []).map((check, checkIndex, checks) => <div key={checkIndex} className="flex flex-wrap items-end gap-2">
              <label className="min-w-0 flex-1 text-xs">检查类型<select aria-label={`任务 ${task.id} 检查 ${checkIndex + 1} 类型`} className={fieldClass} value={check.profile_id} disabled={busy}
                onChange={(event) => updateChecks(index, checks.map((entry, item) => item === checkIndex ? { ...entry, profile_id: event.target.value as FunctionalCheckInput["profile_id"] } : entry))}>
                {Object.entries(FUNCTIONAL_PROFILES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select></label>
              <label className="min-w-0 flex-1 text-xs">检查目录<input aria-label={`任务 ${task.id} 检查 ${checkIndex + 1} 目录`} className={fieldClass} value={check.working_directory} disabled={busy}
                onChange={(event) => updateChecks(index, checks.map((entry, item) => item === checkIndex ? { ...entry, working_directory: event.target.value } : entry))} /></label>
              <button type="button" className={buttonClass} aria-label={`移除任务 ${task.id} 检查 ${checkIndex + 1}`} disabled={busy}
                onClick={() => updateChecks(index, checks.filter((_, item) => item !== checkIndex))}>移除</button>
            </div>)}
            {functionalChecksError(task.validation_checks) && <p role="alert" className="text-xs text-red-500">{functionalChecksError(task.validation_checks)}</p>}
            <button type="button" className={buttonClass} aria-label={`添加任务 ${task.id} 功能检查`} disabled={busy || (task.validation_checks?.length ?? 0) >= 8}
              onClick={() => updateChecks(index, [...(task.validation_checks ?? []), { profile_id: "python_pytest", working_directory: "." }])}>添加功能检查</button>
          </div>
        </fieldset>)}
        <label className="block text-sm">验收标准（每行一项）<textarea aria-label="计划验收标准" className={fieldClass} value={criteria} disabled={busy} rows={4}
          onChange={(event) => setCriteria(event.target.value)} /></label>
      </>}
      {error && <p role="alert" className="text-sm text-red-500">{error}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="button" className={buttonClass} disabled={busy || stale || !editable || (mode === "configuration" ? !configurationValid : !planValid)} onClick={() => void save()}>
          {mode === "configuration" ? "保存目标配置" : "保存计划修改"}
        </button>
        <button type="button" className={buttonClass} disabled={busy} onClick={() => setMode(null)}>取消编辑</button>
      </div>
    </div>}
  </div>;
}
