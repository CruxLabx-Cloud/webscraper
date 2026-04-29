"use client";

import { ScrapeResultItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Fragment, useState } from "react";

export function ResultsTable({ results }: { results: ScrapeResultItem[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (results.length === 0) {
    return (
      <div className="text-sm text-muted-foreground py-8 text-center">
        No results yet. Run a job above to see extracted data here.
      </div>
    );
  }

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            <th className="px-4 py-2 text-left font-medium w-10"></th>
            <th className="px-4 py-2 text-left font-medium">URL</th>
            <th className="px-4 py-2 text-left font-medium w-24">Status</th>
            <th className="px-4 py-2 text-left font-medium w-32">Title</th>
            <th className="px-4 py-2 text-left font-medium w-20">Length</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <Fragment key={i}>
              <tr
                className="border-t border-border hover:bg-muted/50 cursor-pointer"
                onClick={() => setExpanded(expanded === i ? null : i)}
              >
                <td className="px-4 py-2 text-muted-foreground">
                  {expanded === i ? "▼" : "▶"}
                </td>
                <td className="px-4 py-2 truncate max-w-md">
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {r.url}
                  </a>
                </td>
                <td className="px-4 py-2">
                  {r.success ? (
                    <Badge variant="success">success</Badge>
                  ) : (
                    <Badge variant="destructive">failed</Badge>
                  )}
                </td>
                <td className="px-4 py-2 truncate max-w-xs">
                  {(r.metadata?.title as string) || "—"}
                </td>
                <td className="px-4 py-2 text-muted-foreground">
                  {r.markdown ? `${r.markdown.length}` : "—"}
                </td>
              </tr>
              {expanded === i && (
                <tr className="border-t border-border bg-muted/30">
                  <td colSpan={5} className="px-4 py-3">
                    {r.error ? (
                      <div className="text-destructive text-xs">
                        Error: {r.error}
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {r.extracted && (
                          <details open>
                            <summary className="cursor-pointer font-medium text-xs">
                              Extracted (structured)
                            </summary>
                            <pre className="text-xs bg-background border border-border rounded p-2 mt-1 max-h-64 overflow-auto">
                              {JSON.stringify(r.extracted, null, 2)}
                            </pre>
                          </details>
                        )}
                        {r.markdown && (
                          <details>
                            <summary className="cursor-pointer font-medium text-xs">
                              Markdown ({r.markdown.length} chars)
                            </summary>
                            <pre className="text-xs bg-background border border-border rounded p-2 mt-1 max-h-64 overflow-auto whitespace-pre-wrap">
                              {r.markdown.slice(0, 5000)}
                              {r.markdown.length > 5000 && "\n... (truncated)"}
                            </pre>
                          </details>
                        )}
                        {r.metadata && Object.keys(r.metadata).length > 0 && (
                          <details>
                            <summary className="cursor-pointer font-medium text-xs">
                              Metadata
                            </summary>
                            <pre className="text-xs bg-background border border-border rounded p-2 mt-1 max-h-48 overflow-auto">
                              {JSON.stringify(r.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
