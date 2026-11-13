import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import type { Binding, Connection } from "@/schemas/model-access";
import { cn } from "@/lib/cn";

interface BindingListProps {
  bindings: Binding[];
  connections: Connection[];
  selectedId: string | null;
  onSelect: (bindingId: string) => void;
}

interface Group {
  connectionId: string;
  label: string;
  items: Binding[];
  enabled: number;
}

const GROUP_OPEN_LIMIT = 8;

function searchable(binding: Binding) {
  return [binding.name, binding.modelId, binding.executorId, binding.connectionId, binding.bindingId]
    .join(" ").toLocaleLowerCase();
}

/**
 * Bindings grouped by the connection (service) they use, enabled first, with a
 * search box. A list of 60 flat rows gave no way to find one or to see which
 * service had none enabled. Same-named bindings are flagged so leftovers from
 * tests can be cleaned up; nothing here deletes anything.
 */
export function BindingList({ bindings, connections, selectedId, onSelect }: BindingListProps) {
  const [query, setQuery] = useState("");
  const normalized = query.trim().toLocaleLowerCase();

  const groups = useMemo<Group[]>(() => {
    const names = new Map(connections.map((connection) => [connection.connectionId, connection.name || connection.connectionId]));
    const byConnection = new Map<string, Binding[]>();
    for (const binding of bindings) {
      if (normalized && !searchable(binding).includes(normalized)) continue;
      const list = byConnection.get(binding.connectionId) ?? [];
      list.push(binding);
      byConnection.set(binding.connectionId, list);
    }
    return [...byConnection.entries()]
      .map(([connectionId, items]) => ({
        connectionId,
        label: names.get(connectionId) ?? connectionId,
        items: [...items].sort((a, b) => Number(b.enabled) - Number(a.enabled) || a.name.localeCompare(b.name, "zh-CN")),
        enabled: items.filter((item) => item.enabled).length,
      }))
      .sort((a, b) => Number(b.enabled > 0) - Number(a.enabled > 0) || a.label.localeCompare(b.label, "zh-CN"));
  }, [bindings, connections, normalized]);

  const sameName = useMemo(() => {
    const counts = new Map<string, number>();
    for (const binding of bindings) {
      const key = `${binding.connectionId}\u0000${binding.name.trim().toLocaleLowerCase()}`;
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return (binding: Binding) => counts.get(`${binding.connectionId}\u0000${binding.name.trim().toLocaleLowerCase()}`) ?? 1;
  }, [bindings]);

  const shown = groups.reduce((sum, group) => sum + group.items.length, 0);

  return (
    <div data-testid="binding-list" className="flex flex-col gap-1">
      <label className="mx-2 mb-1 flex items-center gap-2 rounded-md border border-ra-border bg-ra-base/40 px-2 py-1.5 text-xs text-ra-text-secondary">
        <Search className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        <input
          aria-label="搜索绑定"
          data-testid="binding-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`在 ${bindings.length} 个绑定中搜索名称或模型`}
          className="min-w-0 flex-1 bg-transparent text-ra-text placeholder:text-ra-text-tertiary focus:outline-none"
        />
      </label>
      {shown === 0 ? (
        <p className="px-2 py-2 text-sm text-ra-text-tertiary">没有匹配的绑定。</p>
      ) : null}
      {groups.map((group) => {
        const open = Boolean(normalized) || group.items.length <= GROUP_OPEN_LIMIT
          || group.items.some((item) => item.bindingId === selectedId);
        return (
          <details key={group.connectionId} open={open} data-testid={`binding-group-${group.connectionId}`} className="group">
            <summary className="flex cursor-pointer select-none items-center gap-2 rounded-md px-2 py-1 text-xs text-ra-text-secondary hover:bg-ra-tertiary/60">
              <span className="truncate font-medium text-ra-text">{group.label}</span>
              <span className="ml-auto shrink-0 tabular-nums text-ra-text-tertiary">
                {group.enabled > 0 ? `${group.enabled} 启用 / ${group.items.length}` : `全部停用 · ${group.items.length}`}
              </span>
            </summary>
            <div className="mt-0.5 flex flex-col gap-0.5">
              {group.items.map((bind) => {
                const twins = sameName(bind);
                return (
                  <button
                    key={bind.bindingId}
                    type="button"
                    data-testid={`binding-item-${bind.bindingId}`}
                    onClick={() => onSelect(bind.bindingId)}
                    className={cn(
                      "flex w-full flex-col gap-0.5 rounded-md px-2 py-1.5 pl-4 text-left transition-colors",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                      selectedId === bind.bindingId ? "bg-ra-tertiary" : "hover:bg-ra-tertiary/70",
                      !bind.enabled && "opacity-70",
                    )}
                  >
                    <span className="flex w-full items-center gap-2">
                      <span className="truncate text-sm font-medium text-ra-text">{bind.name}</span>
                      <span className={cn("ml-auto shrink-0 text-xs font-medium", bind.enabled ? "text-ra-accent" : "text-ra-text-tertiary")}>
                        {bind.enabled ? "启用" : "停用"}
                      </span>
                    </span>
                    <span className="truncate text-xs text-ra-text-tertiary">
                      {bind.executorId} · {bind.modelId}
                    </span>
                    {twins > 1 ? (
                      <span data-testid={`binding-duplicate-${bind.bindingId}`} className="text-xs text-ra-status-warning">
                        同一连接下有 {twins} 个同名绑定，可能是测试遗留
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </details>
        );
      })}
    </div>
  );
}
