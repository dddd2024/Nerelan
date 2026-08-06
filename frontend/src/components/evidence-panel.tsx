import { useState } from "react";
import type { EvidenceItem, EvidenceStatus } from "@/types";
import { Badge } from "@/components/badge";
import { CollapsibleSection } from "@/components/collapsible-section";
import { cn } from "@/lib/cn";
import { Copy } from "lucide-react";

interface EvidencePanelProps {
  evidence: EvidenceItem[];
}

const STATUS_STYLE: Record<EvidenceStatus, { badge: string; label: string }> = {
  pass: { badge: "border-[#BCFF8C]/30 bg-[#BCFF8C]/10 text-[#BCFF8C]", label: "通过" },
  fail: { badge: "border-ra-status-error/30 bg-ra-status-error/10 text-ra-status-error", label: "失败" },
  pending: { badge: "border-[#FFD43B]/30 bg-[#FFD43B]/10 text-[#FFD43B]", label: "待处理" },
  info: { badge: "border-ra-text-tertiary/30 bg-ra-text-tertiary/10 text-ra-text-tertiary", label: "信息" },
};

/**
 * OpenHands-style evidence panel.
 *
 * Upstream reference:
 *   frontend/src/components/features/chat/generic-event-message.tsx
 *     (tag 1.8.0) — collapsible expandable details pattern
 *   frontend/src/components/features/diff-viewer/file-diff-viewer.tsx
 *     — status indicator badge pattern
 *
 * Structurally ported: status badges with OpenHands color scheme
 * (green/yellow/red/grey), collapsible sections, raw JSON expandable.
 * Full SHA / truncated display with copy-to-clipboard pattern.
 *
 * Modifications: reverse-agent EvidenceItem type (authority, tests,
 * audit, budgets) replaces agent observation results.
 */
export function EvidencePanel({ evidence }: EvidencePanelProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (evidence.length === 0) {
    return (
      <div
        data-testid="evidence-empty"
        className="flex flex-col items-center justify-center h-full p-6 text-center text-ra-text-tertiary"
      >
        <p className="text-sm">暂无证据记录。</p>
      </div>
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
                  <EvidenceRow
                    item={item}
                    copiedId={copiedId}
                    onCopy={(id) => setCopiedId(id)}
                  />
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
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-ra-border bg-ra-light px-4 py-3 text-xs">
      <span className="font-medium text-ra-text-secondary">证据摘要</span>
      <Badge className="border-[#BCFF8C]/30 bg-[#BCFF8C]/10 text-[#BCFF8C]">
        {pass} 通过
      </Badge>
      <Badge className="border-ra-status-error/30 bg-ra-status-error/10 text-ra-status-error">
        {fail} 失败
      </Badge>
      <Badge className="border-[#FFD43B]/30 bg-[#FFD43B]/10 text-[#FFD43B]">
        {pending} 待处理
      </Badge>
    </div>
  );
}

function EvidenceRow({
  item,
  copiedId,
  onCopy,
}: {
  item: EvidenceItem;
  copiedId: string | null;
  onCopy: (id: string) => void;
}) {
  const [showRaw, setShowRaw] = useState(false);
  const style = STATUS_STYLE[item.status];
  const looksLikeSha = /^[0-9a-f]{6,}$/i.test(item.value);

  return (
    <div className="rounded-md border border-ra-border bg-ra-tertiary/50 p-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-ra-text-secondary">
          {item.label}
        </span>
        <Badge className={cn(style.badge)}>{style.label}</Badge>
      </div>
      <div className="mt-1 flex items-center gap-2">
        <span
          className={cn(
            "font-mono text-xs text-ra-text-secondary",
            looksLikeSha && "truncate",
          )}
          title={looksLikeSha ? item.value : undefined}
        >
          {item.value}
        </span>
        {item.detail ? (
          <span className="text-xs text-ra-text-tertiary">· {item.detail}</span>
        ) : null}
        {looksLikeSha && item.rawJson && (
          <button
            type="button"
            aria-label="复制 SHA"
            onClick={() => {
              void navigator.clipboard.writeText(item.value);
              onCopy(item.id);
            }}
            className="ml-auto rounded p-0.5 text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
            data-testid={`evidence-copy-${item.id}`}
          >
            <Copy className="h-3 w-3" />
          </button>
        )}
        {copiedId === item.id ? (
          <span className="text-xs text-[#BCFF8C]" data-testid={`evidence-copied-${item.id}`}>
            已复制
          </span>
        ) : null}
      </div>
      {item.rawJson ? (
        <div className="mt-1">
          <button
            type="button"
            aria-expanded={showRaw}
            aria-controls={`raw-json-${item.id}`}
            onClick={() => setShowRaw((s) => !s)}
            className={cn(
              "text-xs font-medium text-ra-text-tertiary underline-offset-2 hover:underline",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
            )}
            data-testid={`evidence-raw-toggle-${item.id}`}
          >
            {showRaw ? "隐藏原始 JSON" : "显示原始 JSON"}
          </button>
          {showRaw ? (
            <pre
              id={`raw-json-${item.id}`}
              data-testid={`evidence-raw-${item.id}`}
              className="mt-1 overflow-x-auto rounded-md border border-ra-border bg-ra-input p-2 font-mono text-xs text-ra-text-secondary"
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
