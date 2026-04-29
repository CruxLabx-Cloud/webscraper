const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SearchResultItem {
  url: string;
  title: string;
  content: string;
  score?: number;
}

export interface ScrapeResultItem {
  url: string;
  success: boolean;
  markdown?: string;
  html?: string;
  links?: string[];
  metadata: Record<string, unknown>;
  extracted?: Record<string, unknown> | null;
  error?: string;
}

export interface ScrapeResponse {
  total: number;
  succeeded: number;
  failed: number;
  results: ScrapeResultItem[];
}

export interface SearchAndScrapeResponse {
  query: string;
  sources: SearchResultItem[];
  scraped: ScrapeResponse;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  search: (query: string, maxResults = 10) =>
    post<{ query: string; results: SearchResultItem[] }>("/api/search", {
      query,
      max_results: maxResults,
    }),

  scrape: (
    urls: string[],
    opts?: {
      formats?: string[];
      onlyMainContent?: boolean;
      extractionPrompt?: string;
    },
  ) =>
    post<ScrapeResponse>("/api/scrape", {
      urls,
      formats: opts?.formats || ["markdown"],
      only_main_content: opts?.onlyMainContent ?? true,
      extraction_prompt: opts?.extractionPrompt || null,
    }),

  searchAndScrape: (
    query: string,
    maxResults = 5,
    extractionPrompt?: string,
  ) =>
    post<SearchAndScrapeResponse>("/api/search-and-scrape", {
      query,
      max_results: maxResults,
      formats: ["markdown"],
      extraction_prompt: extractionPrompt || null,
    }),

  exportUrl: (fmt: "json" | "csv") =>
    `${API_URL}/api/export?fmt=${fmt}`,
};

export async function downloadExport(
  items: Record<string, unknown>[],
  fmt: "json" | "csv",
) {
  const res = await fetch(api.exportUrl(fmt), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `scrapeflow-export.${fmt}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
