"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Trash2, Send } from "lucide-react";
import {
  ApiError,
  type Cadence,
  type WatchlistEntryOut,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CardSkeleton } from "@/components/skeleton";
import { Alert } from "@/components/alert";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
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

export default function WatchlistPage() {
  const [entries, setEntries] = useState<WatchlistEntryOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  useEffect(() => {
    setEntries(getLocalStorageWatchlist());
  }, []);

  async function remove(entry: WatchlistEntryOut) {
    if (!confirm(`Stop tracking ${entry.company.name}?`)) return;
    setBusyId(entry.id);
    try {
      setEntries((prev) => {
        const updated = (prev || []).filter((e) => e.id !== entry.id);
        saveLocalStorageWatchlist(updated);
        return updated;
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  }

  if (entries === null) {
    return (
      <div className="container mx-auto max-w-4xl py-10 px-6">
        <CardSkeleton />
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl py-10 px-6">
      <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Your Watchlist</h1>
          <p className="text-muted-foreground text-sm">
            Tracked companies stored locally in your browser.
          </p>
        </div>
      </div>

      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      {entries.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <p>You aren&apos;t tracking any companies yet.</p>
            <Link href="/" className="text-blue-600 hover:underline">
              Search for one →
            </Link>
          </CardContent>
        </Card>
      )}

      {entries.map((entry) => {
        const busy = busyId === entry.id;
        return (
          <Card key={entry.id} className="mb-4">
            <CardHeader>
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <CardTitle className="text-lg">
                    <Link
                      href={`/companies/${entry.company.slug}`}
                      className="hover:underline"
                    >
                      {entry.company.name}
                    </Link>
                  </CardTitle>
                  <CardDescription>
                    {entry.company.location || "Location unknown"}
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => remove(entry)}
                  disabled={busy}
                >
                  <Trash2 className="h-4 w-4" /> Remove
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Tracked locally. Refresh the page to see the latest updates.
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}