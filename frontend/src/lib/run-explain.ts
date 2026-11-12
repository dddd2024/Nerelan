import type { PlatformRunActivityEvent, PlatformTaskFailure } from "@/lib/platform-client";
import { runtimeMessage } from "@/lib/runtime-labels";

/** A short, readable model name: the binding without its gateway prefix. */
export function modelName(binding?: string): string {
  if (!binding) return "";
  return binding.replace(/^magpie-/, "").replace(/^opencode-zen-free-/, "").replace(/^coding-/, "");
}

/** Why one attempt stopped, in product language, with the host's own words underneath. */
export function failureText(failure?: PlatformTaskFailure | null): { label: string; nextStep: string; detail: string } {
  if (!failure) return { label: "已停止", nextStep: "", detail: "" };
  // The class decides the label; a known code inside the detail (e.g. opencode_stalled) is more specific.
  const detailCode = /(?:^|[:\s])(opencode_stalled|opencode_timeout|functional_check_failed|executor_stalled)/.exec(failure.detail)?.[1];
  const primary = runtimeMessage(failure.classification || "failed");
  const specific = detailCode ? runtimeMessage(detailCode) : null;
  const chosen = specific && specific.nextStep ? specific : primary.nextStep ? primary : specific ?? primary;
  const label = chosen.label === (failure.classification || "failed") ? "已停止" : chosen.label;
  return { label, nextStep: chosen.nextStep, detail: failure.message || failure.detail };
}

export function eventDetail(event: PlatformRunActivityEvent): string {
  if (event.title === "Model selected") {
    // "<model> [<binding>]: <reason> (difficulty …). Candidates: …" → just the chosen model.
    const model = (event.description ?? "").split(" [", 1)[0].trim();
    return model ? `选择模型：${model}` : "选择模型";
  }
  if (event.path) return event.path;
  if (event.command) return event.command.summary;
  if (event.test) return event.test.summary;
  return event.description ?? "";
}

/** Adjacent rows that say the same thing (same title, category and detail) become one row with a count. */
export function collapseRepeats<T extends { event: PlatformRunActivityEvent; key: string }>(rows: T[]) {
  const out: Array<T & { repeats: number }> = [];
  for (const row of rows) {
    const previous = out[out.length - 1];
    if (previous && previous.event.title === row.event.title && previous.event.category === row.event.category
        && eventDetail(previous.event) === eventDetail(row.event)) {
      previous.repeats += 1;
    } else {
      out.push({ ...row, repeats: 1 });
    }
  }
  return out;
}

const LIFECYCLE = new Set(["AGENT_STARTED", "AGENT_COMPLETED", "PLAN", "CHECKPOINT", "VERIFY"]);

/**
 * The actions worth reading: lifecycle markers with nothing to say and raw
 * failure-class echoes (the stop card states the reason) are left out.
 */
export function meaningfulEvents(events: PlatformRunActivityEvent[]): PlatformRunActivityEvent[] {
  return events.filter((event) => {
    if ((event.description ?? "").startsWith("failure_classification=")) return false;
    if (event.title === "Model selected") return true;
    const detail = event.path || event.command?.summary || event.test?.summary || event.description;
    return !(LIFECYCLE.has(String(event.category)) && !detail);
  });
}

/** A person-readable agent name, never a derived hash or execution id. */
export function readableAgent(event: PlatformRunActivityEvent): string {
  const name = event.agent?.display_name || event.agent?.role || event.role || "";
  return /^(agent|exec)-[0-9a-z-]{6,}$/i.test(name) ? "" : name;
}
