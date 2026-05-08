"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Briefcase,
  ExternalLink,
  Flame,
  Linkedin,
  MapPin,
  RefreshCw,
  Sparkles,
  Star,
  Users,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CompanyBrief, JobOut, LeadershipOut } from "@/lib/api";
import { PeopleSignals } from "@/components/people-signals";
import { TriggersPanel } from "@/components/triggers-panel";

interface Props {
  brief: CompanyBrief;
  onTrack?: () => void;
  onRefresh?: () => void;
  refreshing?: boolean;
  isTracked?: boolean;
  trackBusy?: boolean;
  editableLocation?: string;
  onLocationChange?: (location: string) => void;
}

function formatRelative(iso?: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "-";
  const days = Math.round((Date.now() - d.getTime()) / 86_400_000);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days}d ago`;
  return d.toLocaleDateString();
}

function LeaderCard({ leader }: { leader: LeadershipOut }) {
  const isHighConfidence = leader.confidence >= 0.85;
  return (
    <div
      className={`flex items-start justify-between gap-4 rounded-xl border p-4 transition-all ${
        isHighConfidence
          ? "border-blue-200 bg-gradient-to-r from-blue-50 to-transparent"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex flex-wrap items-center gap-2">
          <p className="truncate font-semibold text-slate-900">{leader.name}</p>
          {isHighConfidence ? (
            <Badge className="bg-blue-600 text-white" title="Verified leader">
              <Sparkles className="mr-1 h-3 w-3" />
              Verified
            </Badge>
          ) : (
            <Badge variant="outline" title="Confidence below threshold">
              Unverified
            </Badge>
          )}
        </div>
        <p className="text-sm font-medium text-slate-600">{leader.title}</p>
        <div className="mt-2 flex items-center gap-4">
          <p className="text-xs text-slate-500">Discovered {formatRelative(leader.discovered_at)}</p>
          <div className="flex items-center gap-1 text-xs">
            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full bg-gradient-to-r from-blue-400 to-blue-600"
                style={{ width: `${Math.min(leader.confidence * 100, 100)}%` }}
              />
            </div>
            <span className="text-slate-500">{Math.round(leader.confidence * 100)}%</span>
          </div>
        </div>
      </div>
      {leader.linkedin_url && (
        <a href={leader.linkedin_url} target="_blank" rel="noreferrer" className="shrink-0">
          <Button variant="outline" size="sm" className="border-blue-200 hover:bg-blue-50">
            <Linkedin className="h-4 w-4" />
          </Button>
        </a>
      )}
    </div>
  );
}

function JobCard({ job }: { job: JobOut }) {
  const stale =
    job.posted_at && Date.now() - new Date(job.posted_at).getTime() > 45 * 86_400_000;

  return (
    <div
      className={`rounded-xl border p-4 transition-all ${
        stale
          ? "border-slate-200 bg-slate-50 opacity-70"
          : "border-emerald-200 bg-gradient-to-r from-emerald-50 to-transparent"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-start gap-2">
            <div className="flex-1">
              <p className="font-semibold text-slate-900">{job.title}</p>
              {job.summary && <p className="mt-1 line-clamp-2 text-xs text-slate-600">{job.summary}</p>}
            </div>
            {!stale && <Flame className="h-4 w-4 shrink-0 text-orange-500" />}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            {job.location && (
              <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-200">
                <MapPin className="mr-1 h-3 w-3" /> {job.location}
              </Badge>
            )}
            <Badge variant="outline" className="text-xs">
              {job.source_platform}
            </Badge>
            {job.role_type && (
              <Badge variant="outline" className="text-xs">
                {job.role_type}
              </Badge>
            )}
            {job.seniority && (
              <Badge variant="outline" className="text-xs">
                {job.seniority}
              </Badge>
            )}
            {stale && <Badge variant="outline">May be closed</Badge>}
          </div>
          <p className="mt-2 text-xs text-slate-500">Posted {formatRelative(job.posted_at)}</p>
        </div>
        <a href={job.source_url} target="_blank" rel="noreferrer" className="shrink-0">
          <Button variant="outline" size="sm" className="border-emerald-200">
            <ExternalLink className="h-4 w-4" /> Apply
          </Button>
        </a>
      </div>
    </div>
  );
}

export function CompanyBriefView({
  brief,
  onTrack,
  onRefresh,
  refreshing,
  isTracked,
  trackBusy,
  editableLocation,
  onLocationChange: _onLocationChange,
}: Props) {
  const {
    company,
    leadership,
    jobs,
    people_signals: peopleSignals = [],
    triggers = [],
  } = brief;

  const [editableLoc, setEditableLoc] = useState(editableLocation || company.location || "");

  useEffect(() => {
    setEditableLoc(editableLocation ?? company.location ?? "");
  }, [editableLocation, company.location]);

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-slate-200/90 bg-white/90 shadow-[0_18px_52px_-34px_rgba(30,64,175,0.55)]">
        <CardHeader className="border-b border-slate-100 bg-gradient-to-r from-sky-50/90 via-white to-cyan-50/80">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <CardTitle className="text-3xl text-slate-900">{company.name}</CardTitle>
              <CardDescription className="text-slate-600">
                {company.last_refreshed_at && `Updated ${formatRelative(company.last_refreshed_at)}`}
              </CardDescription>
              {editableLoc && (
                <div className="mt-2 flex items-center gap-2 text-sm text-slate-600">
                  <MapPin className="h-4 w-4" />
                  <span>{editableLoc}</span>
                </div>
              )}
              {company.website && (
                <a
                  href={company.website}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-sm text-sky-700 hover:underline"
                >
                  {company.website} <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
            <div className="flex gap-2">
              {onRefresh && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRefresh}
                  disabled={refreshing}
                  className="border-sky-200 bg-white"
                >
                  <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
              )}
              {onTrack && (
                <Button
                  size="sm"
                  variant={isTracked ? "outline" : "default"}
                  onClick={onTrack}
                  disabled={trackBusy}
                  className={isTracked ? "border-cyan-200" : "bg-sky-700 hover:bg-sky-800"}
                >
                  <Star className="h-4 w-4" />
                  {isTracked ? "Tracking" : "Track Company"}
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="pt-4">
            <div className="mb-2 flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-600" />
              <span className="text-xs font-medium text-blue-600">Leadership</span>
            </div>
            <p className="text-2xl font-bold text-blue-900">{leadership.length}</p>
            <p className="mt-1 text-xs text-blue-700">executives found</p>
          </CardContent>
        </Card>

        <Card className="border-emerald-200 bg-gradient-to-br from-emerald-50 to-emerald-100">
          <CardContent className="pt-4">
            <div className="mb-2 flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-emerald-600" />
              <span className="text-xs font-medium text-emerald-600">Jobs</span>
            </div>
            <p className="text-2xl font-bold text-emerald-900">{jobs.length}</p>
            <p className="mt-1 text-xs text-emerald-700">active openings</p>
          </CardContent>
        </Card>

        <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50 to-indigo-100">
          <CardContent className="pt-4">
            <div className="mb-2 flex items-center gap-2">
              <Zap className="h-4 w-4 text-indigo-600" />
              <span className="text-xs font-medium text-indigo-600">Signals</span>
            </div>
            <p className="text-2xl font-bold text-indigo-900">{peopleSignals.length}</p>
            <p className="mt-1 text-xs text-indigo-700">hiring signals</p>
          </CardContent>
        </Card>

        <Card className="border-amber-200 bg-gradient-to-br from-amber-50 to-amber-100">
          <CardContent className="pt-4">
            <div className="mb-2 flex items-center gap-2">
              <Activity className="h-4 w-4 text-amber-600" />
              <span className="text-xs font-medium text-amber-600">Events</span>
            </div>
            <p className="text-2xl font-bold text-amber-900">{triggers.length}</p>
            <p className="mt-1 text-xs text-amber-700">recent activity</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-blue-200/90 bg-white/90 shadow-[0_12px_34px_-28px_rgba(30,64,175,0.7)]">
          <CardHeader className="border-b border-blue-100 bg-gradient-to-r from-blue-50 to-transparent">
            <CardTitle className="flex items-center gap-2 text-lg text-blue-900">
              <Users className="h-5 w-5 text-blue-600" />
              Leadership Team
              <Badge className="ml-auto bg-blue-600">{leadership.length}</Badge>
            </CardTitle>
            <CardDescription className="mt-2 text-blue-700">
              C-suite executives and key decision makers
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {leadership.length === 0 ? (
              <p className="py-6 text-center text-sm text-slate-500">
                No leadership data found yet. Try Refresh to re-fetch.
              </p>
            ) : (
              leadership.map((l) => <LeaderCard key={l.id} leader={l} />)
            )}
          </CardContent>
        </Card>

        <Card className="border-emerald-200/90 bg-white/90 shadow-[0_12px_34px_-28px_rgba(5,150,105,0.7)]">
          <CardHeader className="border-b border-emerald-100 bg-gradient-to-r from-emerald-50 to-transparent">
            <CardTitle className="flex items-center gap-2 text-lg text-emerald-900">
              <Briefcase className="h-5 w-5 text-emerald-600" />
              Active Job Openings
              <Badge className="ml-auto bg-emerald-600">{jobs.length}</Badge>
            </CardTitle>
            <CardDescription className="mt-2 text-emerald-700">
              Aggregated from LinkedIn, Naukri, Indeed, Foundit and WorkIndia
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {jobs.length === 0 ? (
              <p className="py-6 text-center text-sm text-slate-500">No active job postings found.</p>
            ) : (
              jobs.map((j) => <JobCard key={j.id} job={j} />)
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-2xl border border-slate-200/90 bg-white/90 p-1 shadow-[0_12px_32px_-30px_rgba(30,41,59,0.7)]">
          <TriggersPanel
            slug={company.slug}
            initialTriggers={triggers}
            defaultLocation={editableLoc}
          />
        </div>
        <div className="rounded-2xl border border-slate-200/90 bg-white/90 p-1 shadow-[0_12px_32px_-30px_rgba(30,41,59,0.7)]">
          <PeopleSignals signals={peopleSignals} />
        </div>
      </div>
    </div>
  );
}
