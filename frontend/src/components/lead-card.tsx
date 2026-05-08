"use client";

import { useState } from "react";
import {
  Bookmark,
  BookmarkCheck,
  CheckCircle2,
  ExternalLink,
  Send,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, ApiError, type LeadOpportunityOut } from "@/lib/api";

const PLATFORM_COLORS: Record<string, string> = {
  reddit: "bg-orange-500",
  twitter: "bg-sky-500",
  indiehackers: "bg-purple-500",
  stackoverflow: "bg-amber-500",
  quora: "bg-rose-500",
  hn: "bg-amber-700",
};

function timeAgo(iso?: string | null): string {
  if (!iso) return "recent";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "recent";
  const mins = Math.round((Date.now() - d.getTime()) / 60_000);
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.round(mins / 60)}h ago`;
  return `${Math.round(mins / 1440)}d ago`;
}

interface Props {
  lead: LeadOpportunityOut;
  onUpdate?: (next: LeadOpportunityOut) => void;
  onRemove?: (id: number) => void;
  index?: number;
}

export function LeadCard({ lead, onUpdate, onRemove, index = 0 }: Props) {
  const [busy, setBusy] = useState(false);
  const [removing, setRemoving] = useState(false);
  const platformDot = PLATFORM_COLORS[lead.source_platform] ?? "bg-muted";

  async function patch(patchBody: { saved?: boolean; contacted?: boolean }) {
    if (lead.id === 0) return;
    setBusy(true);
    try {
      const next = await api.updateLead(lead.id, patchBody);
      onUpdate?.(next);
    } catch (err) {
      console.error(err instanceof ApiError ? err.message : err);
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (lead.id === 0 || !onRemove) return;
    if (!confirm("Remove this lead?")) return;
    setRemoving(true);
    try {
      await api.deleteLead(lead.id);
      onRemove(lead.id);
    } catch (err) {
      console.error(err instanceof ApiError ? err.message : err);
      setRemoving(false);
    }
  }

  const intentPct = Math.round(lead.intent_score * 100);

  return (
    <div
      className="border border-border rounded-lg p-4 transition-all hover:shadow-md hover:border-blue-300 animate-fade-in-up"
      style={{
        animationDelay: `${Math.min(index, 8) * 40}ms`,
        animationFillMode: "both",
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span
              className={`inline-block h-2 w-2 rounded-full ${platformDot}`}
            />
            <Badge variant="outline" className="capitalize">
              {lead.source_platform}
            </Badge>
            {lead.posted_at && (
              <span className="text-xs text-muted-foreground">
                {timeAgo(lead.posted_at)}
              </span>
            )}
            <Badge variant="default" className="ml-auto flex items-center gap-1">
              <TrendingUp className="h-3 w-3" /> {intentPct}% intent
            </Badge>
          </div>
          <a
            href={lead.source_url}
            target="_blank"
            rel="noreferrer"
            className="block group"
          >
            <h3 className="font-semibold leading-tight mb-1 group-hover:text-blue-600 group-hover:underline">
              {lead.title}
            </h3>
          </a>
          <p className="text-sm text-muted-foreground line-clamp-3 mb-2">
            {lead.snippet}
          </p>
          {lead.matched_keywords && (
            <div className="flex flex-wrap gap-1 mb-2">
              {lead.matched_keywords.split(",").map((kw) => (
                <Badge key={kw} variant="outline" className="text-[10px]">
                  <Sparkles className="h-2.5 w-2.5 mr-1" />
                  {kw.trim()}
                </Badge>
              ))}
            </div>
          )}
          {(lead.author || lead.contact_hint) && (
            <p className="text-xs text-muted-foreground">
              {lead.author && <>by {lead.author} • </>}
              {lead.contact_hint}
            </p>
          )}
        </div>
        <div className="flex flex-col gap-2 shrink-0 min-w-[120px]">
          <a href={lead.source_url} target="_blank" rel="noreferrer">
            <Button variant="default" size="sm" className="w-full">
              <ExternalLink className="h-4 w-4" /> View post
            </Button>
          </a>
          <Button
            size="sm"
            variant={lead.saved ? "default" : "outline"}
            disabled={busy || removing || lead.id === 0}
            onClick={() => patch({ saved: !lead.saved })}
          >
            {lead.saved ? (
              <>
                <BookmarkCheck className="h-4 w-4" /> Saved
              </>
            ) : (
              <>
                <Bookmark className="h-4 w-4" /> Save
              </>
            )}
          </Button>
          <Button
            size="sm"
            variant={lead.contacted ? "default" : "outline"}
            disabled={busy || removing || lead.id === 0}
            onClick={() => patch({ contacted: !lead.contacted })}
          >
            {lead.contacted ? (
              <>
                <CheckCircle2 className="h-4 w-4" /> Contacted
              </>
            ) : (
              <>
                <Send className="h-4 w-4" /> Mark contacted
              </>
            )}
          </Button>
          {onRemove && lead.id !== 0 && (
            <Button
              size="sm"
              variant="ghost"
              disabled={removing}
              onClick={remove}
            >
              Remove
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
