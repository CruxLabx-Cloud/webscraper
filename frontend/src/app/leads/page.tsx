"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, Radar, Search, Sparkles, Target } from "lucide-react";
import {
  api,
  ApiError,
  type LeadOpportunityOut,
  type LeadPlatform,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert } from "@/components/alert";
import { LeadCard } from "@/components/lead-card";

const ALL_PLATFORMS: LeadPlatform[] = [
  "reddit",
  "twitter",
  "indiehackers",
  "stackoverflow",
  "quora",
  "hn",
];

const PLATFORM_LABELS: Record<LeadPlatform, string> = {
  reddit: "Reddit",
  twitter: "Twitter",
  indiehackers: "Indie Hackers",
  stackoverflow: "Stack Overflow",
  quora: "Quora",
  hn: "Hacker News",
};

const PRESETS = [
  "voice agents for customer support",
  "AI chatbot for SaaS",
  "SEO consultant for small business",
  "social media marketing",
  "shopify developer",
  "data scraping service",
];

const LEADS_KEY = "citracker:leads";

function getLocalStorageLeads(): LeadOpportunityOut[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = window.localStorage.getItem(LEADS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveLocalStorageLeads(leads: LeadOpportunityOut[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(LEADS_KEY, JSON.stringify(leads));
}

export default function LeadsPage() {
  const [service, setService] = useState("");
  const [platforms, setPlatforms] = useState<LeadPlatform[]>(ALL_PLATFORMS);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [leads, setLeads] = useState<LeadOpportunityOut[]>([]);
  const [tab, setTab] = useState<"all" | "saved" | "contacted">("all");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [services, setServices] = useState<string[]>([]);

  useEffect(() => {
    setLeads(getLocalStorageLeads());
  }, []);


  useEffect(() => {
    if (!scanning) return;
    const start = Date.now();
    const id = setInterval(() => setElapsedMs(Date.now() - start), 100);
    return () => clearInterval(id);
  }, [scanning]);

  const togglePlatform = (p: LeadPlatform) => {
    setPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
    );
  };

  async function runScan(presetQuery?: string) {
    const q = (presetQuery ?? service).trim();
    if (q.length < 3) {
      setError("Describe what service you offer (at least 3 chars).");
      return;
    }
    setError(null);
    setInfo(null);
    setLeads([]);
    setScanning(true);
    setElapsedMs(0);
    try {
      const result = await api.scanLeads(q, { platforms });
      setLeads(result);
      setService(q);
      if (!services.includes(q)) setServices((s) => [q, ...s]);
      setInfo(
        result.length === 0
          ? "No high-intent posts found this round — try broader keywords or fewer platforms."
          : `Found ${result.length} prospects in ${(elapsedMs / 1000).toFixed(1)}s.`,
      );
      saveLocalStorageLeads(result);
      logger.info("leads", "scan complete", { service: q, count: result.length });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : String(err);
      setError(msg);
      logger.error("leads", "scan failed", err);
    } finally {
      setScanning(false);
    }
  }

  const filtered = useMemo(() => {
    if (tab === "saved") return leads.filter((l) => l.saved);
    if (tab === "contacted") return leads.filter((l) => l.contacted);
    return leads;
  }, [leads, tab]);

  const counts = useMemo(
    () => ({
      all: leads.length,
      saved: leads.filter((l) => l.saved).length,
      contacted: leads.filter((l) => l.contacted).length,
    }),
    [leads],
  );

  return (
    <div className="container mx-auto max-w-5xl py-10 px-6">
      <header className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Target className="h-7 w-7 text-blue-600" />
          <h1 className="text-3xl font-bold tracking-tight">Find Clients</h1>
        </div>
        <p className="text-muted-foreground">
          Describe what you offer. We scan Reddit, X/Twitter, Indie Hackers,
          Stack Overflow, Quora and Hacker News for people actively asking for
          it — ranked by buying intent.
        </p>
      </header>

      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}
      {info && !scanning && (
        <Alert variant="success" className="mb-4">
          {info}
        </Alert>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>What service do you offer?</CardTitle>
          <CardDescription>
            Be specific — &quot;voice agents for customer support&quot; beats
            &quot;AI&quot;.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="e.g. voice agents for customer support"
              value={service}
              onChange={(e) => setService(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runScan()}
              disabled={scanning}
            />
            <Button onClick={() => runScan()} disabled={scanning} size="lg">
              {scanning ? (
                <>
                  <Radar className="h-4 w-4 mr-2 animate-spin" />
                  Scanning…
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" /> Find prospects
                </>
              )}
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p) => (
              <Badge
                key={p}
                variant="outline"
                className="cursor-pointer select-none hover:border-blue-400"
                onClick={() => {
                  setService(p);
                  runScan(p);
                }}
              >
                <Sparkles className="h-3 w-3 mr-1" /> {p}
              </Badge>
            ))}
          </div>

          <div>
            <p className="text-sm font-medium mb-2">Platforms</p>
            <div className="flex flex-wrap gap-2">
              {ALL_PLATFORMS.map((p) => (
                <Badge
                  key={p}
                  variant={platforms.includes(p) ? "default" : "outline"}
                  className="cursor-pointer select-none"
                  onClick={() => togglePlatform(p)}
                >
                  {PLATFORM_LABELS[p]}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {scanning && (
        <Card className="overflow-hidden mb-6">
          <div className="h-1 bg-muted relative overflow-hidden">
            <div
              className="absolute inset-y-0 left-0 bg-blue-600 transition-all duration-200 ease-linear"
              style={{ width: `${Math.min(100, (elapsedMs / 9000) * 100)}%` }}
            />
          </div>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Radar className="h-5 w-5 text-blue-600 animate-spin" />
              <p className="font-semibold">Scanning the open web…</p>
              <span className="ml-auto text-xs text-muted-foreground tabular-nums">
                {(elapsedMs / 1000).toFixed(1)}s
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Querying Reddit (subreddit + sitewide), X/Twitter, Indie
              Hackers, Stack Overflow, Quora, and Hacker News in parallel.
              Filtering for high buying-intent.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-4">
              {platforms.map((p) => (
                <div
                  key={p}
                  className="flex items-center gap-2 text-xs text-muted-foreground border border-border rounded-md p-2 animate-pulse"
                >
                  <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                  {PLATFORM_LABELS[p]}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {!scanning && leads.length > 0 && (
        <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)}>
          <TabsList className="mb-4">
            <TabsTrigger value="all">All ({counts.all})</TabsTrigger>
            <TabsTrigger value="saved">Saved ({counts.saved})</TabsTrigger>
            <TabsTrigger value="contacted">
              Contacted ({counts.contacted})
            </TabsTrigger>
          </TabsList>
          <TabsContent value={tab}>
            <div className="space-y-3">
              {filtered.map((lead, idx) => (
                <LeadCard
                  key={lead.id || lead.source_url}
                  lead={lead}
                  index={idx}
                  onUpdate={(next) =>
                    setLeads((prev) =>
                      prev.map((l) => (l.id === next.id ? next : l)),
                    )
                  }
                  onRemove={(id) =>
                    setLeads((prev) => prev.filter((l) => l.id !== id))
                  }
                />
              ))}
            </div>
          </TabsContent>
        </Tabs>
      )}

      {!scanning && leads.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Target className="h-10 w-10 mx-auto mb-3" />
            <p>No prospects yet. Describe your service above to start scanning.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}