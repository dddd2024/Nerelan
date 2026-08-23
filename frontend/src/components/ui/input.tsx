import * as React from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-lg border border-ra-border bg-ra-base px-3 py-2 text-sm text-ra-text ring-offset-ra-base file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-ra-text-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
