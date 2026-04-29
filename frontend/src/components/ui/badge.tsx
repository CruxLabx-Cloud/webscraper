import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({
  variant = "default",
  className,
  ...props
}: {
  variant?: "default" | "success" | "destructive" | "outline";
} & React.HTMLAttributes<HTMLSpanElement>) {
  const styles: Record<string, string> = {
    default: "bg-primary text-primary-foreground",
    success: "bg-green-600 text-white",
    destructive: "bg-destructive text-white",
    outline: "border border-border",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        styles[variant],
        className,
      )}
      {...props}
    />
  );
}
