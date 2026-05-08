"use client";

import { useEffect, useState } from "react";
import { Briefcase, Loader2, MapPin, Search, Sparkles } from "lucide-react";
import {
  api,
  ApiError,
  type CompanyBrief,
  type CompanySuggestion,
  type JobPlatform,
  type WatchlistEntryOut,
} from "@/lib/api";
import { logger } from "@/lib/logger";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert } from "@/components/alert";
import { CompanyBriefView } from "@/components/company-brief";
import { ScanProgress } from "@/components/scan-progress";

const ALL_PLATFORMS: JobPlatform[] = [
  "naukri",
  "linkedin",
  "indeed",
  "foundit",
  "workindia",
];

const WATCHLIST_KEY = "citracker:watchlist";

function getLocalStorageWatchlist(): WatchlistEntryOut[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = window.localStorage.getItem(WATCHLIST_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveLocalStorageWatchlist(list: WatchlistEntryOut[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
}

export default function HomePage() {
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [platforms, setPlatforms] = useState<JobPlatform[]>([
    "naukri",
    "linkedin",
    "indeed",
  ]);
  const [suggestions, setSuggestions] = useState<CompanySuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [trackBusy, setTrackBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [brief, setBrief] = useState<CompanyBrief | null>(null);
  const [tracked, setTracked] = useState<WatchlistEntryOut[]>([]);

  useEffect(() => {
    setTracked(getLocalStorageWatchlist());
  }, []);

  useEffect(() => {
    if (!location.trim() || !name || name.trim().length < 3) {
      setSuggestions([]);
      return;
    }
    const handle = setTimeout(() => {
      api
        .suggestCompanies(name.trim(), 6)
        .then(setSuggestions)
        .catch((err) => logger.warn("suggest", "autocomplete failed", err));
    }, 350);
    return () => clearTimeout(handle);
  }, [name, location]);

  const togglePlatform = (p: JobPlatform) => {
    setPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
    );
  };

  const isTracked =
    brief !== null && tracked.some((t) => t.company.id === brief.company.id);

  async function runSearch(query?: string, refresh = false) {
    const target = (query ?? name).trim();
    if (!target) {
      setError("Enter a company name");
      return;
    }
    if (!location.trim()) {
      setError("Enter a location first. Company search depends on location.");
      return;
    }

    setError(null);
    setLoading(true);
    setBrief(null);

    try {
      const result = await api.searchCompany(target, {
        refresh,
        location: location.trim() || undefined,
        jobPlatforms: platforms.length ? platforms : ["naukri", "linkedin"],
      });
      setBrief(result);
      logger.info("search", "company brief loaded", {
        slug: result.company.slug,
        leaders: result.leadership.length,
        jobs: result.jobs.length,
      });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : String(err);
      setError(msg);
      logger.error("search", "company search failed", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    if (!brief) return;
    setRefreshing(true);
    try {
      const next = await api.refreshCompany(
        brief.company.slug,
        platforms,
        location.trim() || undefined,
      );
      setBrief(next);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setRefreshing(false);
    }
  }

  async function handleTrack() {
    if (!brief) return;
    setTrackBusy(true);
    setError(null);
    try {
      if (isTracked) {
        const entry = tracked.find((t) => t.company.id === brief.company.id);
        if (!entry) return;
        setTracked((prev) => {
          const updated = prev.filter((t) => t.id !== entry.id);
          saveLocalStorageWatchlist(updated);
          return updated;
        });
        return;
      }
      const newEntry: WatchlistEntryOut = {
        id: Date.now(),
        company: brief.company,
        cadence: "weekly",
        weekly_day: 0,
      };
      setTracked((prev) => {
        const updated = [newEntry, ...prev];
        saveLocalStorageWatchlist(updated);
        return updated;
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setTrackBusy(false);
    }
  }

  return (
    <div className="container mx-auto max-w-7xl px-5 py-10 md:px-8 md:py-14">
      <header className="mb-8 rounded-2xl border border-sky-100 bg-white/80 p-6 shadow-[0_10px_40px_-24px_rgba(8,47,73,0.7)] backdrop-blur-md md:p-8">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-sky-100 bg-gradient-to-r from-sky-100 to-cyan-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-sky-700">
          <Sparkles className="h-3.5 w-3.5" />
          Revenue Signal Intelligence
        </div>

        <div className="grid gap-5 md:grid-cols-[1.35fr_1fr] md:items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 md:text-5xl">
              Company Intelligence,
              <span className="block text-sky-700">Briefing-Grade in One Scan</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-600 md:text-base">
              Collect leadership, hiring velocity, and opportunity triggers across LinkedIn,
              Naukri, Indeed, Foundit, and WorkIndia in a single briefing panel.
            </p>
          </div>
          <div className="rounded-xl border border-cyan-100 bg-gradient-to-br from-sky-50 to-cyan-50 p-4 text-sm text-slate-700">
            <p className="text-xs font-semibold uppercase tracking-wide text-sky-700">Live Data Surface</p>
            <p className="mt-2">
              Use location-first filtering to keep output relevant for your exact expansion market.
            </p>
          </div>
        </div>
      </header>

      {error && (
        <Alert variant="error" className="mb-6">
          {error}
        </Alert>
      )}

      <Card className="mb-6 overflow-hidden border-slate-200/90 bg-white/85 shadow-[0_20px_50px_-35px_rgba(30,64,175,0.45)]">
        <CardHeader className="border-b border-slate-100 bg-gradient-to-r from-white via-sky-50/80 to-cyan-50/80">
          <CardTitle className="text-xl text-slate-900">Search Console</CardTitle>
          <CardDescription className="text-slate-600">
            Run a focused company scan with location and platform scope controls.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5 p-5 md:p-7">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-sky-100 bg-sky-50/50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-sky-700">Step 1</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">Set Target Location</p>
              <p className="mt-1 text-xs text-slate-600">Search is locked until this field is provided.</p>
              <div className="mt-3">
                <p className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                  <MapPin className="h-4 w-4" /> Location filter
                </p>
                <Input
                  placeholder="e.g. Chennai, Bengaluru, Mumbai"
                  value={location}
                  onChange={(e) => {
                    setLocation(e.target.value);
                    if (!e.target.value.trim()) {
                      setShowSuggestions(false);
                      setSuggestions([]);
                    }
                  }}
                  disabled={loading}
                  className="border-sky-200 bg-white"
                />
              </div>
            </div>

            <div className="rounded-xl border border-cyan-100 bg-cyan-50/40 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-cyan-700">Step 2</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">Choose Company</p>
              <p className="mt-1 text-xs text-slate-600">Autocomplete activates after 3 characters.</p>

              <div className="relative mt-3">
                <Input
                  placeholder="Company name (e.g. Zoho)"
                  value={name}
                  onFocus={() => setShowSuggestions(true)}
                  onBlur={() => {
                    window.setTimeout(() => setShowSuggestions(false), 120);
                  }}
                  onChange={(e) => {
                    setName(e.target.value);
                    setShowSuggestions(true);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") runSearch();
                    if (e.key === "Escape") setShowSuggestions(false);
                  }}
                  disabled={loading || !location.trim()}
                  className="border-cyan-200 bg-white"
                />

                {showSuggestions && suggestions.length > 0 && !loading && location.trim() && (
                  <div className="absolute z-30 mt-1 max-h-72 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-md">
                    {suggestions.map((s) => (
                      <button
                        key={s.slug}
                        type="button"
                        className="w-full px-3 py-2 text-left text-sm hover:bg-sky-50"
                        onClick={() => {
                          setName(s.name);
                          setSuggestions([]);
                          setShowSuggestions(false);
                          if (location.trim()) {
                            runSearch(s.name);
                            return;
                          }
                          setError("Enter a location first. Company search depends on location.");
                        }}
                      >
                        <p className="font-medium text-slate-900">{s.name}</p>
                        {s.description && (
                          <p className="line-clamp-1 text-xs text-slate-500">{s.description}</p>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
            <p className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
              <Briefcase className="h-4 w-4" /> Job platforms
            </p>
            <div className="flex flex-wrap gap-2">
              {ALL_PLATFORMS.map((p) => (
                <Badge
                  key={p}
                  variant={platforms.includes(p) ? "default" : "outline"}
                  className="cursor-pointer select-none rounded-lg px-3 py-1 text-xs uppercase tracking-wide"
                  onClick={() => togglePlatform(p)}
                >
                  {p}
                </Badge>
              ))}
            </div>
          </div>

          <Button
            onClick={() => runSearch()}
            disabled={loading || !location.trim()}
            size="lg"
            className="w-full bg-sky-700 text-white hover:bg-sky-800"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Aggregating signals...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Generate Brief
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {loading && <ScanProgress companyName={name.trim() || undefined} />}

      {brief && !loading && (
        <CompanyBriefView
          brief={brief}
          onTrack={handleTrack}
          onRefresh={handleRefresh}
          refreshing={refreshing}
          isTracked={isTracked}
          trackBusy={trackBusy}
          editableLocation={location}
          onLocationChange={setLocation}
        />
      )}

      {!brief && !loading && (
        <Card className="border-slate-200 bg-white/80">
          <CardContent className="py-14 text-center text-slate-600">
            <Search className="mx-auto mb-3 h-10 w-10 text-sky-600" />
            <p className="text-base">Run a scan to load leadership, jobs, and live trigger intelligence.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
