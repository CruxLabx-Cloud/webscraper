"use client";

import { useState } from "react";
import {
  api,
  downloadExport,
  ScrapeResultItem,
  SearchResultItem,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ResultsTable } from "@/components/results-table";
import {
  Download,
  FileJson,
  FileSpreadsheet,
  Globe,
  Loader2,
  Search,
  Wand2,
} from "lucide-react";

export default function Dashboard() {
  const [tab, setTab] = useState("scrape");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ScrapeResultItem[]>([]);
  const [sources, setSources] = useState<SearchResultItem[]>([]);
  const [stats, setStats] = useState<{
    total: number;
    succeeded: number;
    failed: number;
  } | null>(null);

  // Form state
  const [urls, setUrls] = useState("");
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(5);
  const [extractionPrompt, setExtractionPrompt] = useState("");

  async function runScrape() {
    setError(null);
    setLoading(true);
    setResults([]);
    setSources([]);
    try {
      const list = urls
        .split(/\r?\n/)
        .map((u) => u.trim())
        .filter(Boolean);
      if (list.length === 0) throw new Error("Enter at least one URL");
      const res = await api.scrape(list, {
        formats: ["markdown"],
        extractionPrompt: extractionPrompt || undefined,
      });
      setResults(res.results);
      setStats({
        total: res.total,
        succeeded: res.succeeded,
        failed: res.failed,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function runSearch() {
    setError(null);
    setLoading(true);
    setResults([]);
    setSources([]);
    try {
      if (!query.trim()) throw new Error("Enter a search query");
      const res = await api.search(query, maxResults);
      setSources(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function runSearchAndScrape() {
    setError(null);
    setLoading(true);
    setResults([]);
    setSources([]);
    try {
      if (!query.trim()) throw new Error("Enter a search query");
      const res = await api.searchAndScrape(
        query,
        maxResults,
        extractionPrompt || undefined,
      );
      setSources(res.sources);
      setResults(res.scraped.results);
      setStats({
        total: res.scraped.total,
        succeeded: res.scraped.succeeded,
        failed: res.scraped.failed,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleExport(fmt: "json" | "csv") {
    if (results.length === 0) return;
    const items = results.map((r) => ({
      url: r.url,
      success: r.success,
      title: (r.metadata?.title as string) ?? "",
      description: (r.metadata?.description as string) ?? "",
      markdown_length: r.markdown?.length ?? 0,
      extracted: r.extracted ?? null,
      error: r.error ?? "",
    }));
    await downloadExport(items, fmt);
  }

  return (
    <div className="container mx-auto max-w-6xl py-10 px-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">ScrapeFlow</h1>
        <p className="text-muted-foreground mt-1">
          From URL to structured data in seconds. Powered by Tavily + Firecrawl.
        </p>
      </header>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>New extraction job</CardTitle>
          <CardDescription>
            Pick an input mode below. Results appear at the bottom.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="scrape">
                <Globe className="h-4 w-4 mr-1" /> URLs
              </TabsTrigger>
              <TabsTrigger value="search">
                <Search className="h-4 w-4 mr-1" /> Search
              </TabsTrigger>
              <TabsTrigger value="combo">
                <Wand2 className="h-4 w-4 mr-1" /> Search + Scrape
              </TabsTrigger>
            </TabsList>

            <TabsContent value="scrape">
              <div className="space-y-3">
                <label className="text-sm font-medium">
                  URLs (one per line, max 100)
                </label>
                <Textarea
                  rows={5}
                  placeholder={"https://example.com\nhttps://news.ycombinator.com"}
                  value={urls}
                  onChange={(e) => setUrls(e.target.value)}
                />
                <label className="text-sm font-medium">
                  Optional extraction prompt
                </label>
                <Input
                  placeholder="e.g. Extract product name, price, and rating"
                  value={extractionPrompt}
                  onChange={(e) => setExtractionPrompt(e.target.value)}
                />
                <Button onClick={runScrape} disabled={loading}>
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Globe className="h-4 w-4" />
                  )}
                  Scrape URLs
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="search">
              <div className="space-y-3">
                <label className="text-sm font-medium">Search query</label>
                <Input
                  placeholder="e.g. Top open-source AI agent frameworks 2026"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <label className="text-sm font-medium">Max results</label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={maxResults}
                  onChange={(e) => setMaxResults(Number(e.target.value))}
                  className="w-32"
                />
                <Button onClick={runSearch} disabled={loading}>
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                  Search (Tavily)
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="combo">
              <div className="space-y-3">
                <label className="text-sm font-medium">Search query</label>
                <Input
                  placeholder="e.g. Pricing pages of leading CRM tools"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="text-sm font-medium">Max sources</label>
                    <Input
                      type="number"
                      min={1}
                      max={20}
                      value={maxResults}
                      onChange={(e) => setMaxResults(Number(e.target.value))}
                    />
                  </div>
                </div>
                <label className="text-sm font-medium">
                  Optional extraction prompt
                </label>
                <Input
                  placeholder="e.g. Extract pricing tiers and features"
                  value={extractionPrompt}
                  onChange={(e) => setExtractionPrompt(e.target.value)}
                />
                <Button onClick={runSearchAndScrape} disabled={loading}>
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Wand2 className="h-4 w-4" />
                  )}
                  Search + Scrape
                </Button>
              </div>
            </TabsContent>
          </Tabs>
          {error && (
            <div className="mt-4 text-sm text-destructive bg-destructive/10 border border-destructive/30 rounded p-3">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {sources.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Tavily sources</CardTitle>
            <CardDescription>
              Discovered {sources.length} URLs ranked by relevance.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {sources.map((s, i) => (
                <li
                  key={i}
                  className="border border-border rounded p-3 hover:bg-muted/30"
                >
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline font-medium"
                  >
                    {s.title || s.url}
                  </a>
                  {typeof s.score === "number" && (
                    <Badge variant="outline" className="ml-2">
                      score {s.score.toFixed(2)}
                    </Badge>
                  )}
                  <p className="text-muted-foreground mt-1 line-clamp-2">
                    {s.content}
                  </p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {results.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <div>
              <CardTitle>Extracted data</CardTitle>
              <CardDescription>
                {stats && (
                  <>
                    {stats.succeeded} succeeded · {stats.failed} failed ·{" "}
                    {stats.total} total
                  </>
                )}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport("json")}
              >
                <FileJson className="h-4 w-4" /> JSON
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport("csv")}
              >
                <FileSpreadsheet className="h-4 w-4" /> CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ResultsTable results={results} />
          </CardContent>
        </Card>
      )}

      <footer className="mt-10 text-xs text-muted-foreground text-center">
        ScrapeFlow MVP · respect robots.txt and the ToS of sites you scrape ·{" "}
        <Download className="h-3 w-3 inline" /> exports run client-side
      </footer>
    </div>
  );
}
