import { useState } from "react";
import type { EvidenceItem, EvidenceStatus } from "@/types";
import { Badge } from "@/components/badge";
import { CollapsibleSection } from "@/components/collapsible-section";
import { cn } from "@/lib/cn";

interface EvidencePanelProps {
  evidence: EvidenceItem[];
}

const STATUS_STYLE: Record<EvidenceStatus, { badge: string; label: string }> = {
  pass: { badge: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "通过" },
  fail: { badge: "bg-rose-50 text-rose-700 border-rose-200", label: "失败" },
  pending: { badge: "bg-amber-50 text-amber-700 border-amber-200", label: "待处理" },
  info: { badge: "bg-slate-50 text-slate-700 border-slate-200", label: "信息" },
};

/**
 * Summary-first panels for Authority, Decision, Command Plan, Preflight,
 * local checks, workflow checks, commit identity, Draft PR identity,
 * evidence provenance, failure classification. Full SHA and raw JSON
 * collapsed by default.
 */
export function EvidencePanel({ evidence }: EvidencePanelProps) {
  if (evidence.length === 0) {
    return (
      <p className="text-sm text-slate-500" data-testid="evidence-empty">
        暂无证据记录。
      </p>
    );
  }

  const categories = unique(evidence.map((e) => e.category));
  return (
    <div data-testid="evidence-panel" className="space-y-3">
      <EvidenceSummary evidence={evidence} />
      {categories.map((cat) => {
        const items = evidence.filter((e) => e.category === cat);
        return (
          <CollapsibleSection
            key={cat}
            title={cat}
            defaultOpen={false}
            summary={`${items.length} 项`}
          >
            <ul className="space-y-2">
              {items.map((item) => (
                <li key={item.id}>
                  <EvidenceRow item={item} />
                </li>
              ))}
            </ul>
          </CollapsibleSection>
        );
      })}
    </div>
  );
}

function EvidenceSummary({ evidence }: { evidence: EvidenceItem[] }) {
  const pass = evidence.filter((e) => e.status === "pass").length;
  const fail = evidence.filter((e) => e.status === "fail").length;
  const pending = evidence.filter((e) => e.status === "pending").length;
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-xs">
      <span className="font-medium text-slate-700">证据摘要</span>
      <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">
        {pass} 通过
      </Badge>
      <Badge className="border-rose-200 bg-rose-50 text-rose-700">{fail} 失败</Badge>
      <Badge className="border-amber-200 bg-amber-50 text-amber-700">
        {pending} 待处理
      </Badge>
    </div>
  );
}

function EvidenceRow({ item }: { item: EvidenceItem }) {
  const [showRaw, setShowRaw] = useState(false);
  const style = STATUS_STYLE[item.status];
  const looksLikeSha = /^[0-9a-f]{6,}$/i.test(item.value);
  return (
    <div className="rounded-md border border-slate-100 bg-slate-50/50 p-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-slate-700">{item.label}</span>
        <Badge className={cn(style.badge)}>{style.label}</Badge>
      </div>
      <div className="mt-1 flex items-center gap-2">
        <span
          className={cn(
            "font-mono text-xs text-slate-600",
            looksLikeSha && "truncate",
          )}
          title={looksLikeSha ? item.value : undefined}
        >
          {item.value}
        </span>
        {item.detail ? (
          <span className="text-xs text-slate-400">· {item.detail}</span>
        ) : null}
      </div>
      {item.rawJson ? (
        <div className="mt-1">
          <button
            type="button"
            aria-expanded={showRaw}
            aria-controls={`raw-json-${item.id}`}
            onClick={() => setShowRaw((s) => !s)}
            className="text-xs text-slate-500 underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            data-testid={`evidence-raw-toggle-${item.id}`}
          >
            {showRaw ? "隐藏原始 JSON" : "显示原始 JSON"}
          </button>
          {showRaw ? (
            <pre
              id={`raw-json-${item.id}`}
              data-testid={`evidence-raw-${item.id}`}
              className="mt-1 overflow-x-auto rounded-md border border-slate-200 bg-white p-2 font-mono text-xs text-slate-700"
            >
              {item.rawJson}
            </pre>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function unique<T>(arr: T[]): T[] {
  return Array.from(new Set(arr));
}
