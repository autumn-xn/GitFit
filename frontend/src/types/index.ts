// ─── frontend/src/types/index.ts ──────────────────────────────────────────────
// Central type definitions. Every other file imports from here.
// Mirrors the backend Pydantic schemas in backend/api/schemas.py

// ─── Repo metadata (from GitHub API) ─────────────────────────────────────────

export interface RepoMeta {
  owner: string;
  name: string;
  full_name: string;          // "owner/repo"
  description: string | null;
  url: string;
  stars: number;
  forks: number;
  open_issues: number;
  watchers: number;
  default_branch: string;
  created_at: string;         // ISO 8601
  updated_at: string;         // ISO 8601
  license: string | null;
  is_private: boolean;
  topics: string[];
}

// ─── Language breakdown ───────────────────────────────────────────────────────

export interface LanguageBreakdown {
  language: string;
  bytes: number;
  percentage: number;         // 0–100, rounded to 1 decimal
}

// ─── Contributor data ─────────────────────────────────────────────────────────

export interface Contributor {
  login: string;
  avatar_url: string;
  profile_url: string;
  contributions: number;      // commit count
}

// ─── Commit activity (weekly buckets, last 52 weeks) ─────────────────────────

export interface WeeklyActivity {
  week: string;               // ISO date string for start of week
  commits: number;
  additions: number;
  deletions: number;
}

// ─── AI-generated analysis sections ──────────────────────────────────────────

export interface ArchitectureInsight {
  summary: string;            // 2–3 sentence overview
  patterns: string[];         // e.g. ["MVC", "REST API", "Monorepo"]
  entry_points: string[];     // e.g. ["src/main.py", "index.ts"]
  key_directories: string[];  // e.g. ["src/", "tests/", "docs/"]
}

export interface CodeQuality {
  score: number;              // 0–100
  has_tests: boolean;
  has_ci: boolean;
  has_docs: boolean;
  has_linter: boolean;
  has_docker: boolean;
  notes: string[];            // bullet observations from AI
}

export interface SecurityFlags {
  has_env_example: boolean;
  exposes_secrets: boolean;   // detected .env / hardcoded keys
  dependency_audit: string;   // "clean" | "outdated" | "vulnerable" | "unknown"
  notes: string[];
}

// ─── Full analysis result (what backend returns) ──────────────────────────────

export interface AnalysisResult {
  meta: RepoMeta;
  languages: LanguageBreakdown[];
  contributors: Contributor[];
  activity: WeeklyActivity[];
  architecture: ArchitectureInsight;
  code_quality: CodeQuality;
  security: SecurityFlags;
  analyzed_at: string;        // ISO 8601 timestamp
}

// ─── API request / response shapes ───────────────────────────────────────────

export interface AnalyzeRequest {
  url: string;                // full GitHub URL
}

export interface AnalyzeResponse {
  success: boolean;
  data?: AnalysisResult;
  error?: string;
}

// ─── Hook state machine ───────────────────────────────────────────────────────

export type AnalysisStatus = "idle" | "loading" | "success" | "error";

export interface AnalysisState {
  status: AnalysisStatus;
  result: AnalysisResult | null;
  error: string | null;
}