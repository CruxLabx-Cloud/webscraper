"use client";

import { use, useEffect, useState } from "react";
import {
  api,
  ApiError,
  type CompanyBrief,
  type JobPlatform,
  type WatchlistEntryOut,
} from "@/lib/api";
import { Alert } from "@/components/alert";
import { CardSkeleton } from "@/components/skeleton";
import { CompanyBriefView } from "@/components/company-brief";

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

export default function CompanyDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [brief, setBrief] = useState<CompanyBrief | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [trackBusy, setTrackBusy] = useState(false);
  const [tracked, setTracked] = useState<WatchlistEntryOut[]>([]);
  const [location, setLocation] = useState("");

  useEffect(() => {
    setTracked(getLocalStorageWatchlist());
  }, []);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      api
        .getCompany(slug, { location: location.trim() || undefined })
        .then((next) => {
          if (!cancelled) setBrief(next);
        })
        .catch((err) => {
          if (!cancelled) {
            setError(err instanceof ApiError ? err.message : String(err));
          }
        });
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [slug, location]);

  useEffect(() => {
    if (brief?.company.location && !location) {
      setLocation(brief.company.location);
    }
  }, [brief?.company.location, location]);

  const isTracked =
    brief !== null && tracked.some((t) => t.company.id === brief.company.id);

  async function refresh() {
    if (!brief) return;
    setRefreshing(true);
    setError(null);
    try {
      const platforms: JobPlatform[] = ["naukri", "linkedin"];
      const updated = await api.refreshCompany(
        brief.company.slug,
        platforms,
        location.trim() || undefined,
      );
      setBrief(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setRefreshing(false);
    }
  }

  async function track() {
    if (!brief) return;
    setTrackBusy(true);
    setError(null);
    try {
      if (isTracked) {
        const entry = tracked.find((t) => t.company.id === brief.company.id)!;
        setTracked((prev) => {
          const updated = prev.filter((t) => t.id !== entry.id);
          saveLocalStorageWatchlist(updated);
          return updated;
        });
      } else {
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
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setTrackBusy(false);
    }
  }

  return (
    <div className="container mx-auto max-w-6xl py-10 px-6">
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}
      {!brief && !error && <CardSkeleton />}
      {brief && (
        <CompanyBriefView
          brief={brief}
          onRefresh={refresh}
          refreshing={refreshing}
          onTrack={track}
          trackBusy={trackBusy}
          isTracked={isTracked}
          editableLocation={location}
          onLocationChange={setLocation}
        />
      )}
    </div>
  );
}