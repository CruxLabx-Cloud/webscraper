import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { api, ApiError, downloadExport } from "@/lib/api";

describe("API integration", () => {
  const fetchMock: any = jest.fn();

  function okJsonResponse(payload: unknown) {
    return {
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => payload,
      text: async () => JSON.stringify(payload),
      blob: async () => new Blob(),
    };
  }

  beforeEach(() => {
    fetchMock.mockReset();
    global.fetch = fetchMock as typeof fetch;
  });

  it("validates search input before making requests", () => {
    expect(() => api.search(""))
      .toThrow(ApiError);
    expect(() => api.search("   "))
      .toThrow(ApiError);
    expect(() => api.search("valid query", 0))
      .toThrow(ApiError);
    expect(() => api.search("valid query", 51))
      .toThrow(ApiError);
  });

  it("sends a trimmed search request with max_results", async () => {
    fetchMock.mockResolvedValueOnce(okJsonResponse({ query: "test", results: [] }));

    await api.search("  test  ", 20);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/search",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }),
    );

    const requestBody = JSON.parse(
      (fetchMock.mock.calls[0][1] as RequestInit).body as string,
    ) as {
      query: string;
      max_results: number;
    };
    expect(requestBody).toEqual({ query: "test", max_results: 20 });
  });

  it("validates scrape input and rejects invalid urls", () => {
    expect(() => api.scrape([])).toThrow(ApiError);
    expect(() => api.scrape(["not-a-url"])).toThrow(ApiError);
    expect(() => api.scrape(["ftp://example.com"])).toThrow(ApiError);
  });

  it("sends a scrape request with normalized urls", async () => {
    fetchMock.mockResolvedValueOnce(
      okJsonResponse({ total: 1, succeeded: 1, failed: 0, results: [] }),
    );

    await api.scrape(["https://example.com/page"], {
      formats: ["markdown"],
      onlyMainContent: true,
      extractionPrompt: "Summarize the page",
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const requestBody = JSON.parse(
      (fetchMock.mock.calls[0][1] as RequestInit).body as string,
    ) as {
      urls: string[];
      formats: string[];
      only_main_content: boolean;
      extraction_prompt: string;
    };
    expect(requestBody).toEqual({
      urls: ["https://example.com/page"],
      formats: ["markdown"],
      only_main_content: true,
      extraction_prompt: "Summarize the page",
    });
  });

  it("exports supported formats and rejects unsupported ones", () => {
    expect(api.exportUrl("json")).toBe("http://localhost:8000/api/export?fmt=json");
    expect(api.exportUrl("csv")).toBe("http://localhost:8000/api/export?fmt=csv");
    expect(() => api.exportUrl("xml" as never)).toThrow(ApiError);
  });

  it("rejects empty export payloads", async () => {
    await expect(downloadExport([], "json")).rejects.toBeInstanceOf(ApiError);
  });
});
