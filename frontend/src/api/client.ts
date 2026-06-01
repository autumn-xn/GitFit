// ─── frontend/src/api/client.ts ───────────────────────────────────────────────
// Pure fetch wrapper. No React, no state — just typed HTTP calls.
// Import this in useAnalysis.ts, never call it directly from components.

import type { AnalyzeRequest, AnalyzeResponse, AnalysisResult } from "../types";

// ─── Config ───────────────────────────────────────────────────────────────────

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ─── Helpers ──────────────────────────────────────────────────────────────────

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseResponse<T>(res: Response): Promise<T> {
  const contentType = res.headers.get("content-type") ?? "";

  if (!res.ok) {
    // Try to get a meaningful error message from the body
    const body = contentType.includes("application/json")
      ? await res.json().catch(() => ({}))
      : await res.text().catch(() => "");
    const message =
      (body as { detail?: string; error?: string })?.detail ??
      (body as { error?: string })?.error ??
      `HTTP ${res.status}`;
    throw new ApiError(res.status, message);
  }

  if (!contentType.includes("application/json")) {
    throw new ApiError(res.status, "Expected JSON response from server.");
  }

  return res.json() as Promise<T>;
}

// ─── API calls ────────────────────────────────────────────────────────────────

/**
 * POST /analyze
 * Sends a GitHub repo URL to the backend and returns the full analysis.
 * Throws ApiError on non-2xx or network failure.
 */
export async function analyzeRepo(url: string): Promise<AnalysisResult> {
  const payload: AnalyzeRequest = { url };

  const res = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(60_000),  // 60 s — LLM can be slow
  });

  const body = await parseResponse<AnalyzeResponse>(res);

  if (!body.success || !body.data) {
    throw new ApiError(200, body.error ?? "Analysis failed with no error message.");
  }

  return body.data;
}

/**
 * GET /health
 * Used at startup to check if the backend is reachable.
 * Returns true if healthy, false otherwise (never throws).
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`, {
      signal: AbortSignal.timeout(5_000),
    });
    return res.ok;
  } catch {
    return false;
  }
}