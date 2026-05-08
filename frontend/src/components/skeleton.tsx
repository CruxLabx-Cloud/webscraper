import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

/**
 * Skeleton loader component for loading states
 */
export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className,
      )}
    />
  );
}

/**
 * Table skeleton for displaying loading state
 */
export function TableSkeleton() {
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <div className="bg-muted h-12 flex items-center px-4">
        <Skeleton className="h-4 w-1/3" />
      </div>
      <div className="space-y-2 p-4">
        {Array(3)
          .fill(0)
          .map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
      </div>
    </div>
  );
}

/**
 * Card skeleton for displaying loading state
 */
export function CardSkeleton() {
  return (
    <div className="rounded-lg border border-border p-6 space-y-3">
      <Skeleton className="h-6 w-1/3" />
      <Skeleton className="h-4 w-2/3" />
      <div className="space-y-2 pt-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-4/5" />
      </div>
    </div>
  );
}
