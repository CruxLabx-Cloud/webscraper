"use client";

import { ExternalLink, Linkedin, Sparkles, UserCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { PeopleSignalOut } from "@/lib/api";

const SIGNAL_LABELS: Record<string, string> = {
  hiring_post: "Hiring post",
  requirement: "Requirement",
  mention: "Person mention",
  funding: "Funding",
};

export function PeopleSignals({ signals }: { signals: PeopleSignalOut[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <UserCheck className="h-5 w-5 text-blue-600" /> Lead-Gen Signals (
          {signals.length})
        </CardTitle>
        <CardDescription>
          Recruiters, hiring managers, and skill requirements mentioned around
          this company — your warm-outreach shortlist.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {signals.length === 0 ? (
          <p className="text-sm text-muted-foreground py-6 text-center">
            No people signals surfaced yet — try refresh.
          </p>
        ) : (
          signals.map((s) => (
            <div
              key={s.id}
              className="border border-border rounded-lg p-4 transition-colors hover:bg-accent/30"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    {s.person_name ? (
                      <p className="font-semibold">{s.person_name}</p>
                    ) : (
                      <p className="font-semibold flex items-center gap-1">
                        <Sparkles className="h-4 w-4 text-blue-600" /> Signal
                      </p>
                    )}
                    {s.person_title && (
                      <span className="text-xs text-muted-foreground">
                        {s.person_title}
                      </span>
                    )}
                    <Badge variant="outline">
                      {SIGNAL_LABELS[s.signal_type] ?? s.signal_type}
                    </Badge>
                    <Badge variant="outline">{s.source_platform}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-3 mb-2">
                    {s.snippet}
                  </p>
                  {s.skills_mentioned && (
                    <div className="flex flex-wrap gap-1">
                      {s.skills_mentioned.split(",").map((sk) => (
                        <Badge key={sk} variant="default" className="text-[10px]">
                          {sk.trim()}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex flex-col gap-2 shrink-0">
                  {s.linkedin_url && (
                    <a href={s.linkedin_url} target="_blank" rel="noreferrer">
                      <Button variant="outline" size="sm">
                        <Linkedin className="h-4 w-4" /> Profile
                      </Button>
                    </a>
                  )}
                  <a href={s.source_url} target="_blank" rel="noreferrer">
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="h-4 w-4" /> Source
                    </Button>
                  </a>
                </div>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
