import * as React from "react";
import { cn } from "@/lib/cn";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent focus-visible:ring-offset-2 focus-visible:ring-offset-ra-base disabled:pointer-events-none disabled:opacity-50",
          variant === "default" && "bg-ra-accent text-ra-base hover:bg-ra-accent-hover shadow-sm",
          variant === "destructive" && "bg-red-500 text-white hover:bg-red-600 shadow-sm",
          variant === "outline" && "border border-ra-border bg-ra-light hover:bg-ra-tertiary text-ra-text",
          variant === "secondary" && "bg-ra-tertiary text-ra-text hover:bg-ra-input",
          variant === "ghost" && "hover:bg-ra-tertiary text-ra-text-secondary hover:text-ra-text",
          variant === "link" && "text-ra-accent underline-offset-4 hover:underline",
          size === "default" && "h-10 px-4 py-2",
          size === "sm" && "h-8 rounded-md px-3 text-xs",
          size === "lg" && "h-12 rounded-lg px-6 text-base",
          size === "icon" && "h-10 w-10",
          className
        )}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg
            className="mr-2 h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";

export { Button };
