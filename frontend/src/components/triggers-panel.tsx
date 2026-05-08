"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bell,
  Briefcase,
  DollarSign,
  ExternalLink,
  Loader2,
  MapPin,
  MessageCircle,
  Sparkles,
  TrendingUp,
  UserPlus,
  Volume2,
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
import { api, ApiError, type CompanyTriggerOut } from "@/lib/api";

const WINDOWS: { label: string; hours: number }[] = [
  { label: "Last 1h", hours: 1 },
  { label: "Last 24h", hours: 24 },
  { label: "Last 7d", hours: 24 * 7 },
  { label: "Last 30d", hours: 24 * 30 },
];

const TYPES: { key: string; label: string; Icon: typeof Bell; color: string }[] = [
  { key: "all", label: "All", Icon: Bell, color: "text-blue-600" },
  { key: "hiring", label: "Hiring", Icon: Briefcase, color: "text-emerald-600" },
  {
    key: "leadership_change",
    label: "Leadership",
    Icon: UserPlus,
    color: "text-purple-600",
  },
  { key: "funding", label: "Funding", Icon: DollarSign, color: "text-amber-600" },
  {
    key: "linkedin_post",
    label: "Posts",
    Icon: MessageCircle,
    color: "text-sky-600",
  },
  { key: "mention", label: "Mentions", Icon: Sparkles, color: "text-rose-600" },
];

function timeAgo(iso?: string | null): string {
  if (!iso) return "recent";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "recent";
  const mins = Math.round((Date.now() - d.getTime()) / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.round(mins / 60)}h ago`;
  return `${Math.round(mins / 1440)}d ago`;
}

interface Props {
  slug: string;
  initialTriggers?: CompanyTriggerOut[];
  defaultLocation?: string;
  pollIntervalMs?: number;
}

export function TriggersPanel({
  slug,
  initialTriggers = [],
  defaultLocation,
  pollIntervalMs = 45000,
}: Props) {
  const [windowHours, setWindowHours] = useState(24 * 7);
  const [type, setType] = useState<string>("all");
  const [location, setLocation] = useState(defaultLocation || "");
  const [triggers, setTriggers] = useState<CompanyTriggerOut[]>(initialTriggers);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [browserAlertsEnabled, setBrowserAlertsEnabled] = useState(
    typeof window !== "undefined" && "Notification" in window
      ? Notification.permission === "granted"
      : false,
  );
  const previousIdsRef = useRef<Set<number>>(new Set(initialTriggers.map((t) => t.id)));
  const mountedRef = useRef(false);
  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    setLocation(defaultLocation || "");
  }, [defaultLocation]);

  const playNotificationSound = () => {
    if (!soundEnabled || typeof window === "undefined") return;
    const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextCtor) return;
    const context = audioContextRef.current || new AudioContextCtor();
    audioContextRef.current = context;
    if (context.state === "suspended") {
      context.resume().catch(() => {});
    }
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = 880;
    gain.gain.value = 0.0001;
    oscillator.connect(gain);
    gain.connect(context.destination);
    const now = context.currentTime;
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.06, now + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.32);
    oscillator.start(now);
    oscillator.stop(now + 0.35);
  };

  const showBrowserNotification = (trigger: CompanyTriggerOut) => {
    if (typeof window === "undefined" || !("Notification" in window)) return;
    if (Notification.permission === "granted") {
      new Notification(`New ${trigger.trigger_type} for ${trigger.source_platform}`, {
        body: trigger.title,
        icon: "/favicon.ico",
      });
    }
  };

  async function requestBrowserNotifications() {
    if (typeof window === "undefined" || !("Notification" in window)) return;
    if (Notification.permission === "granted") {
      setBrowserAlertsEnabled(true);
      return;
    }
    const permission = await Notification.requestPermission();
    setBrowserAlertsEnabled(permission === "granted");
  }

  useEffect(() => {
    let cancelled = false;

    const fetchTriggers = async () => {
      setLoading(true);
      setError(null);
      try {
        const latest = await api.listTriggers(slug, {
          location: location.trim() || undefined,
          maxAgeHours: windowHours,
          triggerType: type === "all" ? undefined : type,
        });

        if (cancelled) return;

        const previousIds = previousIdsRef.current;
        const nextIds = new Set(latest.map((t) => t.id));
        const newTriggers = latest.filter((t) => !previousIds.has(t.id));

        if (mountedRef.current && newTriggers.length > 0) {
          playNotificationSound();
          if (browserAlertsEnabled) {
            newTriggers.forEach(showBrowserNotification);
          }
        }

        previousIdsRef.current = nextIds;
        mountedRef.current = true;
        setTriggers(latest);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void fetchTriggers();

    if (pollIntervalMs > 0) {
      const interval = setInterval(() => {
        void fetchTriggers();
      }, pollIntervalMs);

      return () => {
        cancelled = true;
        clearInterval(interval);
      };
    }

    return () => {
      cancelled = true;
    };
  }, [slug, windowHours, type, location, pollIntervalMs, browserAlertsEnabled]);

  const grouped = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const t of triggers) counts[t.trigger_type] = (counts[t.trigger_type] || 0) + 1;
    return counts;
  }, [triggers]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Bell className="h-5 w-5 text-blue-600" /> Live Triggers (
          {triggers.length})
        </CardTitle>
        <CardDescription>
          Time-windowed events for this company — hires, funding, posts, and
          mentions. Filter by city and recency.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2 items-center justify-between">
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-xs font-medium text-muted-foreground mr-1">
              Window:
            </span>
            {WINDOWS.map((w) => (
              <Badge
                key={w.label}
                variant={windowHours === w.hours ? "default" : "outline"}
                className="cursor-pointer select-none"
                onClick={() => setWindowHours(w.hours)}
              >
                {w.label}
              </Badge>
            ))}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSoundEnabled(!soundEnabled)}
            title={soundEnabled ? "Disable notifications" : "Enable notifications"}
          >
            <Volume2 className={`h-4 w-4 ${soundEnabled ? "text-blue-600" : "text-muted-foreground"}`} />
          </Button>
          {typeof window !== "undefined" && "Notification" in window && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => void requestBrowserNotifications()}
              title={browserAlertsEnabled ? "Browser alerts enabled" : "Enable browser alerts"}
            >
              <Bell className={`h-4 w-4 ${browserAlertsEnabled ? "text-blue-600" : "text-muted-foreground"}`} />
            </Button>
          )}
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-xs font-medium text-muted-foreground mr-1">
            Type:
          </span>
          {TYPES.map((t) => {
            const count = grouped[t.key] || 0;
            return (
              <Badge
                key={t.key}
                variant={type === t.key ? "default" : "outline"}
                className="cursor-pointer select-none flex items-center gap-1"
                onClick={() => setType(t.key)}
              >
                <t.Icon className={`h-3 w-3 ${type === t.key ? "" : t.color}`} />
                {t.label}
                {t.key !== "all" && count > 0 && (
                  <span className="ml-1 text-[10px] opacity-70">{count}</span>
                )}
              </Badge>
            );
          })}
        </div>

        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Filter by city (e.g. Chennai)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="flex-1 h-9 rounded-md border border-border bg-transparent px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          />
          {location && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setLocation("")}
              className="text-xs"
            >
              Clear
            </Button>
          )}
        </div>

        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground py-3">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading triggers…
          </div>
        )}
        {error && (
          <p className="text-sm text-red-600 py-2">{error}</p>
        )}
        {!loading && triggers.length === 0 && !error && (
          <p className="text-sm text-muted-foreground py-6 text-center">
            No triggers match these filters. Try a wider time window or remove
            the location filter.
          </p>
        )}
        <div className="space-y-2">
          {triggers.map((t, idx) => {
            const TypeIcon =
              TYPES.find((x) => x.key === t.trigger_type)?.Icon ?? Bell;
            const typeColor =
              TYPES.find((x) => x.key === t.trigger_type)?.color ??
              "text-muted-foreground";
            return (
              <div
                key={t.id}
                className="border border-border rounded-lg p-3 hover:bg-accent/30 transition-colors animate-fade-in-up"
                style={{ animationDelay: `${Math.min(idx, 8) * 30}ms` }}
              >
                <div className="flex items-start gap-3">
                  <span
                    className={`flex h-8 w-8 items-center justify-center rounded-full bg-muted shrink-0 ${typeColor}`}
                  >
                    <TypeIcon className="h-4 w-4" />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <Badge variant="outline" className="capitalize">
                        {t.trigger_type.replace("_", " ")}
                      </Badge>
                      {t.location && (
                        <Badge variant="outline" className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" /> {t.location}
                        </Badge>
                      )}
                      <Badge variant="outline">{t.source_platform}</Badge>
                      <span className="text-xs text-muted-foreground ml-auto">
                        {timeAgo(t.occurred_at || t.discovered_at)}
                      </span>
                      {t.importance >= 0.85 && (
                        <Badge variant="default" className="flex items-center gap-1">
                          <TrendingUp className="h-3 w-3" /> High
                        </Badge>
                      )}
                    </div>
                    <a
                      href={t.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="block group"
                    >
                      <p className="font-medium text-sm leading-tight group-hover:text-blue-600 group-hover:underline">
                        {t.title}
                      </p>
                    </a>
                    {t.snippet && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                        {t.snippet}
                      </p>
                    )}
                  </div>
                  <a
                    href={t.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="shrink-0"
                  >
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}