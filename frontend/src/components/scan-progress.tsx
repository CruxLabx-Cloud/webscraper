"use client";

import { useEffect, useState } from "react";
import { Briefcase, CheckCircle2, Loader2, Sparkles, Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface Stage {
  key: string;
  label: string;
  Icon: typeof Loader2;
  delayMs: number;
}

const STAGES: Stage[] = [
  { key: "discover", label: "Discovering company sources", Icon: Sparkles, delayMs: 0 },
  { key: "leadership", label: "Mapping C-suite leadership", Icon: Users, delayMs: 1000 },
  { key: "jobs", label: "Aggregating live job openings", Icon: Briefcase, delayMs: 2200 },
  { key: "people", label: "Surfacing recruiter & hiring-manager signals", Icon: Sparkles, delayMs: 3600 },
];

/**
 * Live-progress card shown while the search is running. Stages tick in based
 * on cumulative elapsed milliseconds — gives the UI a feeling of momentum
 * without coupling to actual backend events (the pipeline is parallel anyway).
 */
export function ScanProgress({ companyName }: { companyName?: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => setElapsed(Date.now() - start), 100);
    return () => clearInterval(id);
  }, []);

  return (
    <Card className="overflow-hidden">
      <div className="h-1 bg-muted relative overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-blue-600 transition-all duration-200 ease-linear"
          style={{ width: `${Math.min(100, (elapsed / 9000) * 100)}%` }}
        />
      </div>
      <CardContent className="pt-6 space-y-3">
        <div className="flex items-center gap-3 mb-2">
          <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
          <p className="font-semibold">
            Aggregating intelligence{companyName ? ` for ${companyName}` : ""}…
          </p>
          <span className="ml-auto text-xs text-muted-foreground tabular-nums">
            {(elapsed / 1000).toFixed(1)}s
          </span>
        </div>
        <ol className="space-y-2">
          {STAGES.map((s) => {
            const active = elapsed >= s.delayMs;
            const done = elapsed >= s.delayMs + 1500;
            return (
              <li
                key={s.key}
                className="flex items-center gap-3 text-sm transition-opacity"
                style={{ opacity: active ? 1 : 0.4 }}
              >
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full transition-colors ${
                    done
                      ? "bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300"
                      : active
                        ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {done ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : active ? (
                    <s.Icon className="h-4 w-4 animate-pulse" />
                  ) : (
                    <s.Icon className="h-4 w-4" />
                  )}
                </span>
                <span className={done ? "text-muted-foreground line-through" : ""}>
                  {s.label}
                </span>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
