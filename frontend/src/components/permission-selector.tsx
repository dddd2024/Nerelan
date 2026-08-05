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
 * Compact dropdown for the 4 permission modes. Keyboard accessible.
 */
export function PermissionSelector({
  value,
  onChange,
  id = "permission-mode",
  label = "Permission profile",
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
    <div className="relative inline-block" data-testid="permission-selector">
      {label ? (
        <label htmlFor={id} className="mb-1 block text-xs text-slate-500">
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
          "inline-flex w-full items-center justify-between gap-2 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700",
          "hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400",
        )}
      >
        <span>{permissionModeLabel(value)}</span>
        <ChevronDown aria-hidden="true" className="h-4 w-4 text-slate-400" />
      </button>
      {open ? (
        <ul
          ref={listRef}
          role="listbox"
          aria-label={label}
          className="absolute z-20 mt-1 w-full overflow-auto rounded-md border border-slate-200 bg-white py-1 shadow-sm"
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
                    "hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-inset",
                    selected && "bg-slate-50",
                  )}
                  data-testid={`permission-option-${m}`}
                >
                  <span>{permissionModeLabel(m)}</span>
                  {selected ? (
                    <Check aria-hidden="true" className="h-3.5 w-3.5 text-slate-500" />
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
