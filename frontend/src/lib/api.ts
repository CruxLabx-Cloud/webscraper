const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || "60000", 10);
const DEBUG = process.env.NEXT_PUBLIC_DEBUG === "true";

const TOKEN_STORAGE_KEY = "citracker:token";

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

// ---- Company Intelligence types ----

export interface CompanyOut {
  id: number;
  slug: string;
  name: string;
  website?: string | null;
  location?: string | null;
  description?: string | null;
  linkedin_url?: string | null;
  last_refreshed_at?: string | null;
  created_at: string;
}

export interface LeadershipOut {
  id: number;
  name: string;
  title: string;
  linkedin_url?: string | null;
  source_url?: string | null;
  confidence: number;
  discovered_at: string;
}

export interface JobOut {
  id: number;
  title: string;
  location?: string | null;
  seniority?: string | null;
  role_type?: string | null;
  posted_at?: string | null;
  source_platform: string;
  source_url: string;
  summary?: string | null;
  discovered_at: string;
}

export interface PeopleSignalOut {
  id: number;
  person_name?: string | null;
  person_title?: string | null;
  signal_type: string;
  snippet: string;
  source_url: string;
  source_platform: string;
  skills_mentioned?: string | null;
  linkedin_url?: string | null;
  discovered_at: string;
}

export interface CompanyTriggerOut {
  id: number;
  trigger_type: string;
  title: string;
  snippet?: string | null;
  location?: string | null;
  source_url: string;
  source_platform: string;
  occurred_at?: string | null;
  importance: number;
  discovered_at: string;
}

export interface CompanyBrief {
  company: CompanyOut;
  leadership: LeadershipOut[];
  jobs: JobOut[];
  people_signals: PeopleSignalOut[];
  triggers: CompanyTriggerOut[];
}

export interface CompanySuggestion {
  name: string;
  slug: string;
  description?: string | null;
}

export type Cadence = "off" | "biweekly" | "weekly";

export interface WatchlistEntryOut {
  id: number;
  company: CompanyOut;
  cadence: Cadence;
  weekly_day: number;
  last_digest_at?: string | null;
}

export type JobPlatform =
  | "naukri"
  | "linkedin"
  | "indeed"
  | "foundit"
  | "workindia";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public retryable: boolean = false,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function validateUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return /^https?:/.test(parsed.protocol);
  } catch {
    return false;
  }
}

function logError(context: string, error: unknown): void {
  if (!DEBUG) return;
  const safe = error instanceof Error ? error.message : String(error);
  console.error(`[CITracker] ${context}:`, safe);
}

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeout: number = API_TIMEOUT,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

interface RequestOpts {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | undefined>;
  timeout?: number;
}

async function request<T>(path: string, opts: RequestOpts = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";

  let url = `${API_URL}${path}`;
  if (opts.query) {
    const qs = new URLSearchParams();
    Object.entries(opts.query).forEach(([k, v]) => {
      if (v !== undefined && v !== null) qs.set(k, String(v));
    });
    const s = qs.toString();
    if (s) url += `?${s}`;
  }

  try {
    const res = await fetchWithTimeout(
      url,
      {
        method: opts.method ?? (opts.body !== undefined ? "POST" : "GET"),
        headers,
        body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      },
      opts.timeout,
    );

    if (res.status === 204) return undefined as T;

    if (!res.ok) {
      let detail = "";
      try {
        const data = (await res.json()) as { detail?: string };
        detail = data.detail || "";
      } catch {
        detail = await res.text();
      }
      const retryable = res.status >= 500 || res.status === 429;
      const message = detail
        ? detail.slice(0, 300)
        : `Request failed: ${res.status} ${res.statusText}`;
      throw new ApiError(res.status, message, retryable);
    }

    return (await res.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new ApiError(0, "Network error. Check your connection.", true);
    }
    logError("request", error);
    throw new ApiError(
      0,
      error instanceof Error ? error.message : "Unknown error",
      true,
    );
  }
}

// ---- Public API surface ----

export const api = {
  // ScrapeFlow legacy (kept for backwards compatibility with existing tests)
  search: (query: string, maxResults = 10) => {
    if (!query || query.trim().length === 0) {
      throw new ApiError(400, "Search query cannot be empty", false);
    }
    if (maxResults < 1 || maxResults > 50) {
      throw new ApiError(400, "Max results must be between 1 and 50", false);
    }
    return request<{ query: string; results: SearchResultItem[] }>(
      "/api/search",
      {
        body: {
          query: query.trim(),
          max_results: Math.min(Math.max(1, maxResults), 50),
        },
      },
    );
  },

  scrape: (
    urls: string[],
    opts?: {
      formats?: string[];
      onlyMainContent?: boolean;
      extractionPrompt?: string;
    },
  ) => {
    if (!Array.isArray(urls) || urls.length === 0) {
      throw new ApiError(400, "At least one URL is required", false);
    }
    const validUrls = urls.map((u) => u.trim()).filter(Boolean).slice(0, 100);
    if (validUrls.length === 0) {
      throw new ApiError(400, "At least one valid URL is required", false);
    }
    const invalid = validUrls.filter((u) => !validateUrl(u));
    if (invalid.length > 0) {
      throw new ApiError(
        400,
        `Invalid URLs: ${invalid.slice(0, 3).join(", ")}`,
        false,
      );
    }
    return request<ScrapeResponse>("/api/scrape", {
      body: {
        urls: validUrls,
        formats: opts?.formats ?? ["markdown"],
        only_main_content: opts?.onlyMainContent ?? true,
        extraction_prompt: opts?.extractionPrompt ?? null,
      },
    });
  },

  exportUrl: (fmt: "json" | "csv") => {
    if (!["json", "csv"].includes(fmt)) {
      throw new ApiError(400, "Export format must be 'json' or 'csv'", false);
    }
    return `${API_URL}/api/export?fmt=${fmt}`;
  },

  // ---- Company intelligence ----
  suggestCompanies: (q: string, limit = 8) =>
    request<CompanySuggestion[]>("/api/companies/suggest", {
      query: { q, limit },
    }),

  searchCompany: (
    name: string,
    opts?: {
      refresh?: boolean;
      jobPlatforms?: JobPlatform[];
      location?: string;
    },
  ) =>
    request<CompanyBrief>("/api/companies/search", {
      body: {
        name: name.trim(),
        refresh: opts?.refresh ?? false,
        location: opts?.location?.trim() || null,
        job_platforms: opts?.jobPlatforms ?? ["naukri", "linkedin", "indeed"],
      },
      timeout: 30_000,
    }),

  getCompany: (
    slug: string,
    opts?: { location?: string; maxAgeHours?: number },
  ) =>
    request<CompanyBrief>(`/api/companies/${encodeURIComponent(slug)}`, {
      query: {
        location: opts?.location,
        max_age_hours: opts?.maxAgeHours,
      },
    }),

  refreshCompany: (
    slug: string,
    platforms?: JobPlatform[],
    location?: string,
  ) =>
    request<CompanyBrief>(
      `/api/companies/${encodeURIComponent(slug)}/refresh`,
      {
        body: platforms ?? ["naukri", "linkedin", "indeed"],
        timeout: 30_000,
        query: { location },
      },
    ),

  listTriggers: (
    slug: string,
    opts?: { location?: string; maxAgeHours?: number; triggerType?: string },
  ) =>
    request<CompanyTriggerOut[]>(
      `/api/companies/${encodeURIComponent(slug)}/triggers`,
      {
        query: {
          location: opts?.location,
          max_age_hours: opts?.maxAgeHours,
          trigger_type: opts?.triggerType,
        },
      },
    ),

  // ---- Watchlist ----
  listWatchlist: () =>
    request<WatchlistEntryOut[]>("/api/watchlist", {}),

  addWatchlist: (companyId: number, cadence: Cadence = "weekly", weeklyDay = 0) =>
    request<WatchlistEntryOut>("/api/watchlist", {
      body: { company_id: companyId, cadence, weekly_day: weeklyDay },
    }),

  updateWatchlist: (id: number, cadence: Cadence, weeklyDay = 0) =>
    request<WatchlistEntryOut>(`/api/watchlist/${id}`, {
      method: "PATCH",
      body: { cadence, weekly_day: weeklyDay },
    }),

  removeWatchlist: (id: number) =>
    request<void>(`/api/watchlist/${id}`, { method: "DELETE" }),

  triggerDigest: () =>
    request<{
      status: string;
      company_count: number;
      new_jobs: number;
      new_leaders: number;
      error?: string | null;
    }>("/api/watchlist/digest/preview", { body: {} }),

  // ---- Lead Opportunity scanner ----
  scanLeads: (
    service: string,
    opts?: { platforms?: LeadPlatform[]; subreddits?: string[]; persist?: boolean },
  ) =>
    request<LeadOpportunityOut[]>("/api/leads/scan", {
      body: {
        service: service.trim(),
        platforms: opts?.platforms ?? [
          "reddit",
          "twitter",
          "indiehackers",
          "stackoverflow",
          "quora",
          "hn",
        ],
        subreddits: opts?.subreddits,
        persist: opts?.persist ?? true,
      },
      timeout: 30_000,
    }),

  listLeads: (opts?: { service?: string; saved?: boolean; contacted?: boolean }) =>
    request<LeadOpportunityOut[]>("/api/leads", {
      query: {
        service: opts?.service,
        saved: opts?.saved !== undefined ? String(opts.saved) : undefined,
        contacted:
          opts?.contacted !== undefined ? String(opts.contacted) : undefined,
      },
    }),

  updateLead: (id: number, patch: { saved?: boolean; contacted?: boolean }) =>
    request<LeadOpportunityOut>(`/api/leads/${id}`, {
      method: "PATCH",
      body: patch,
    }),

  deleteLead: (id: number) =>
    request<void>(`/api/leads/${id}`, { method: "DELETE" }),

  listLeadServices: () =>
    request<string[]>("/api/leads/services", {}),
};

export type LeadPlatform =
  | "reddit"
  | "twitter"
  | "indiehackers"
  | "stackoverflow"
  | "quora"
  | "hn";

export interface LeadOpportunityOut {
  id: number;
  title: string;
  snippet: string;
  source_platform: string;
  source_url: string;
  author?: string | null;
  posted_at?: string | null;
  intent_score: number;
  matched_keywords?: string | null;
  service_query: string;
  contact_hint?: string | null;
  saved: boolean;
  contacted: boolean;
  discovered_at: string;
}

export async function downloadExport(
  items: Record<string, unknown>[],
  fmt: "json" | "csv",
) {
  if (!items || items.length === 0) {
    throw new ApiError(400, "No items to export", false);
  }
  if (!["json", "csv"].includes(fmt)) {
    throw new ApiError(400, "Invalid export format", false);
  }
  try {
    const res = await fetchWithTimeout(api.exportUrl(fmt), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items }),
    });
    if (!res.ok) {
      throw new ApiError(
        res.status,
        `Export failed: ${res.statusText}`,
        res.status >= 500,
      );
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `citracker-export.${fmt}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    logError("downloadExport", error);
    throw new ApiError(0, "Failed to download export", false);
  }
}
