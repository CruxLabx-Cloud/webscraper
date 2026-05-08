import { AlertCircle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function Alert({
  variant = "info",
  children,
  className,
}: {
  variant?: "info" | "success" | "error";
  children: React.ReactNode;
  className?: string;
}) {
  const styles = {
    info: "bg-muted text-foreground border-border",
    success:
      "bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200",
    error:
      "bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200",
  } as const;

  const Icon = variant === "error" ? AlertCircle : CheckCircle2;
  return (
    <div
      className={cn(
        "flex items-start gap-3 border rounded-lg p-4 text-sm",
        styles[variant],
        className,
      )}
    >
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1">{children}</div>
    </div>
  );
}
