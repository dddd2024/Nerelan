import { useRef, useEffect, useState } from "react";
import { ChevronDown, Check } from "lucide-react";
import type { PermissionMode } from "@/types";
import { permissionModeLabel } from "@/lib/format";
import { cn } from "@/lib/cn";

const MODES: PermissionMode[] = [
  "ASK_FOR_APPROVAL",
  "CONTROLLER_REVIEW",
  "OWNER_CONTROL",
  "CUSTOM",
];

interface PermissionSelectorProps {
  value: PermissionMode;
  onChange: (mode: PermissionMode) => void;
  id?: string;
  label?: string;
}

/**
 * OpenHands-style permission profile selector.
 *
 * Upstream reference:
 *   frontend/src/components/features/chat/components/chat-input-row.tsx
 *   — dropdown-style controls in the chat input area
 *   frontend/src/components/shared/buttons/conversation-panel-button.tsx
 *   — icon buttons with tooltip (concept for compact selectable)
 *   frontend/src/components/features/conversation/conversation-name.tsx
 *   — dropdown with context menu pattern
 *
 * Structurally ported: dropdown select with trigger button
 * (`rounded-md border bg-ra-input`), listbox with hover/select states
 * using OpenHands dark palette colors (bg-[#454545] on hover,
 * text-[#A3A3A3] for muted items, text-white for selected).
 *
 * Modifications: permission profiles replace LLM model selection;
 * no provider/model icons; OpenHands brand text removed.
 * License: MIT (inherited from OpenHands)
 */
export function PermissionSelector({
  value,
  onChange,
  id = "permission-mode",
  label = "权限配置",
}: PermissionSelectorProps) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node) &&
        listRef.current &&
        !listRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="relative inline-block w-full" data-testid="permission-selector">
      {label ? (
        <label htmlFor={id} className="mb-1 block text-xs text-ra-text-tertiary">
          {label}
        </label>
      ) : null}
      <button
        ref={triggerRef}
        id={id}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={label}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
            e.preventDefault();
            setOpen(true);
          }
        }}
        className={cn(
          "inline-flex w-full items-center justify-between gap-2 rounded-md",
          "border border-ra-border bg-ra-input px-3 py-1.5 text-sm text-ra-text",
          "hover:bg-ra-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
        )}
      >
        <span>{permissionModeLabel(value)}</span>
        <ChevronDown aria-hidden="true" className="h-4 w-4 text-ra-text-tertiary" />
      </button>
      {open ? (
        <ul
          ref={listRef}
          role="listbox"
          aria-label={label}
          className="absolute z-20 mt-1 w-full overflow-auto rounded-md border border-ra-border bg-ra-light py-1 shadow-lg"
        >
          {MODES.map((m, i) => {
            const selected = m === value;
            return (
              <li key={m} role="option" aria-selected={selected}>
                <button
                  type="button"
                  ref={(el) => {
                    if (i === 0) (el as HTMLButtonElement | null)?.focus?.();
                  }}
                  onClick={() => {
                    onChange(m);
                    setOpen(false);
                    triggerRef.current?.focus();
                  }}
                  className={cn(
                    "flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-sm",
                    "text-ra-text-secondary hover:text-ra-text hover:bg-ra-tertiary",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent focus-visible:ring-inset",
                    selected && "bg-ra-tertiary text-ra-text",
                  )}
                  data-testid={`permission-option-${m}`}
                >
                  <span>{permissionModeLabel(m)}</span>
                  {selected ? (
                    <Check aria-hidden="true" className="h-3.5 w-3.5 text-ra-accent" />
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
