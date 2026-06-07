// ─── frontend/src/pages/Results.tsx ──────────────────────────────────────────
// Step 3 — Full analysis results page.
// Reads AnalysisResult from location.state (passed by Home.tsx via navigate).
// If no state is present the user is redirected back to "/".

import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import type { AnalysisResult, LanguageBreakdown, WeeklyActivity, Contributor } from "../types";

// ─── Keyframe injection ───────────────────────────────────────────────────────

function injectKeyframes() {
  if (document.getElementById("results-kf")) return;
  const s = document.createElement("style");
  s.id = "results-kf";
  s.textContent = `
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(22px); }
      to   { opacity: 1; transform: translateY(0);    }
    }
    @keyframes pulseRed {
      0%,100% { opacity: 1; }
      50%     { opacity: 0.35; }
    }
    @keyframes scaleXBar {
      from { transform: scaleX(0); }
      to   { transform: scaleX(1); }
    }
    .res-back:hover   { background: rgba(90,143,216,0.14) !important; color: #fff !important; }
    .res-gh:hover     { background: rgba(90,143,216,0.1)  !important; color: #fff !important; }
    .res-contrib:hover{ background: rgba(90,143,216,0.09) !important; }
    .res-topic:hover  { border-color: rgba(90,143,216,0.55) !important; color: #c8d8f0 !important; }
  `;
  document.head.appendChild(s);
}

// ─── Language colour map ──────────────────────────────────────────────────────

const LANG_COLORS: Record<string, string> = {
  JavaScript:   "#f7df1e",
  TypeScript:   "#3178c6",
  Python:       "#3572a5",
  Java:         "#b07219",
  "C++":        "#f34b7d",
  C:            "#555555",
  "C#":         "#178600",
  Go:           "#00add8",
  Rust:         "#dea584",
  Ruby:         "#701516",
  PHP:          "#4f5d95",
  Swift:        "#f05138",
  Kotlin:       "#a97bff",
  Dart:         "#00b4ab",
  HTML:         "#e34c26",
  CSS:          "#563d7c",
  SCSS:         "#c6538c",
  Shell:        "#89e051",
  Vue:          "#41b883",
  Svelte:       "#ff3e00",
  Scala:        "#c22d40",
  Haskell:      "#5e5086",
  Lua:          "#000080",
  "Jupyter Notebook": "#da5b0b",
  Other:        "#6b7280",
};

const langColor = (name: string) => LANG_COLORS[name] ?? "#5a8fd8";

// ─── Utilities ────────────────────────────────────────────────────────────────

const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });

const fmtNum = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
};

// ─── Shared card wrapper ──────────────────────────────────────────────────────

function Card({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <div style={{
      backgroundColor: "rgba(255,255,255,0.04)",
      backdropFilter: "blur(14px) saturate(1.2)",
      WebkitBackdropFilter: "blur(14px) saturate(1.2)",
      border: "0.5px solid rgba(90,143,216,0.18)",
      borderRadius: 16,
      padding: "1.5rem",
      ...style,
    }}>
      {children}
    </div>
  );
}

// Mono uppercase section label
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 10,
      fontWeight: 500,
      color: "#5a8fd8",
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      margin: "0 0 1rem",
    }}>
      {children}
    </p>
  );
}

// Coloured true/false flag row
function Flag({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "5px 0" }}>
      <span style={{
        width: 20, height: 20, borderRadius: "50%", flexShrink: 0,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 11, fontWeight: 700,
        backgroundColor: ok ? "rgba(34,197,94,0.14)" : "rgba(204,31,31,0.12)",
        color: ok ? "#22c55e" : "#cc1f1f",
      }}>
        {ok ? "✓" : "✗"}
      </span>
      <span style={{ fontSize: 13, color: ok ? "#b8f0cc" : "#f0b8b8" }}>
        {label}
      </span>
    </div>
  );
}

// ─── Score ring (SVG) ─────────────────────────────────────────────────────────

function ScoreRing({ score }: { score: number }) {
  const R  = 40;
  const C  = 2 * Math.PI * R;
  const offset = C * (1 - score / 100);
  const color = score >= 70 ? "#22c55e" : score >= 45 ? "#f59e0b" : "#cc1f1f";

  return (
    <svg width={100} height={100} viewBox="0 0 100 100"
         aria-label={`Quality score ${score} / 100`} role="img">
      {/* track */}
      <circle cx="50" cy="50" r={R} fill="none"
        stroke="rgba(90,143,216,0.12)" strokeWidth="9" />
      {/* fill */}
      <circle cx="50" cy="50" r={R} fill="none"
        stroke={color} strokeWidth="9"
        strokeLinecap="round"
        strokeDasharray={C}
        strokeDashoffset={offset}
        transform="rotate(-90 50 50)"
        style={{ transition: "stroke-dashoffset 1s cubic-bezier(.4,0,.2,1) 0.4s" }}
      />
      {/* score number */}
      <text x="50" y="47" textAnchor="middle" dominantBaseline="middle"
        fontFamily="'Syne', sans-serif" fontSize="21" fontWeight="700"
        fill="#ffffff">
        {score}
      </text>
      <text x="50" y="63" textAnchor="middle"
        fontFamily="'JetBrains Mono', monospace" fontSize="9"
        fill="#4a7090">
        / 100
      </text>
    </svg>
  );
}

// ─── Language bar chart ───────────────────────────────────────────────────────

function LanguageChart({ langs }: { langs: LanguageBreakdown[] }) {
  return (
    <div>
      {langs.map((l, i) => (
        <div key={l.language} style={{ marginBottom: i < langs.length - 1 ? 14 : 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{
                width: 9, height: 9, borderRadius: "50%",
                backgroundColor: langColor(l.language), flexShrink: 0,
              }} />
              <span style={{ fontSize: 13, color: "#c8d8f0" }}>{l.language}</span>
            </div>
            <span style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12, color: "#5a8fd8",
            }}>
              {l.percentage}%
            </span>
          </div>
          <div style={{
            height: 5, borderRadius: 3,
            backgroundColor: "rgba(90,143,216,0.1)",
            overflow: "hidden",
          }}>
            <div style={{
              height: "100%",
              width: `${l.percentage}%`,
              backgroundColor: langColor(l.language),
              borderRadius: 3,
              transformOrigin: "left center",
              animation: `scaleXBar 0.7s cubic-bezier(.4,0,.2,1) ${0.3 + i * 0.06}s both`,
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Commit activity bar chart (inline SVG) ───────────────────────────────────

function ActivityChart({ weeks }: { weeks: WeeklyActivity[] }) {
  if (!weeks.length)
    return <p style={{ color: "#3a5070", fontSize: 13, padding: "2rem 0", textAlign: "center" }}>No activity data available.</p>;

  const max     = Math.max(...weeks.map(w => w.commits), 1);
  const BAR_W   = 22;
  const GAP     = 5;
  const CH      = 80;
  const PAD_L   = 28;
  const PAD_B   = 36;
  const svgW    = PAD_L + weeks.length * (BAR_W + GAP) - GAP;
  const svgH    = CH + PAD_B;

  return (
    <div style={{ overflowX: "auto", marginTop: 4 }}>
      <svg
        viewBox={`0 0 ${svgW} ${svgH}`}
        width="100%"
        style={{ minWidth: Math.max(weeks.length * 14, 280), display: "block" }}
        aria-label="Weekly commit activity"
        role="img"
      >
        {/* horizontal gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map(pct => {
          const y = CH - pct * CH;
          return (
            <g key={pct}>
              <line x1={PAD_L} y1={y} x2={svgW} y2={y}
                stroke="rgba(90,143,216,0.07)" strokeWidth="1" />
              {pct > 0 && (
                <text x={PAD_L - 4} y={y} textAnchor="end" dominantBaseline="middle"
                  fontSize="8" fontFamily="'JetBrains Mono', monospace" fill="#3a5070">
                  {Math.round(pct * max)}
                </text>
              )}
            </g>
          );
        })}

        {weeks.map((w, i) => {
          const barH  = w.commits > 0 ? Math.max((w.commits / max) * CH, 3) : 0;
          const x     = PAD_L + i * (BAR_W + GAP);
          const y     = CH - barH;
          const ratio = w.commits / max;
          const fill  = ratio > 0.7
            ? "#cc1f1f"
            : ratio > 0.35
            ? "#1a3a8f"
            : ratio > 0
            ? "rgba(26,58,143,0.55)"
            : "rgba(90,143,216,0.08)";

          const label = new Date(w.week).toLocaleDateString("en-US", { month: "short", day: "numeric" });

          return (
            <g key={w.week}>
              <rect x={x} y={y} width={BAR_W} height={Math.max(barH, 0)} fill={fill} rx="3" ry="3">
                <title>{`${w.commits} commit${w.commits !== 1 ? "s" : ""} · ${label}`}</title>
              </rect>
              {w.commits > 0 && (
                <text x={x + BAR_W / 2} y={y - 4}
                  textAnchor="middle" fontSize="8"
                  fontFamily="'JetBrains Mono', monospace"
                  fill="rgba(200,216,240,0.5)">
                  {w.commits}
                </text>
              )}
              <text
                x={x + BAR_W / 2} y={CH + 14}
                textAnchor="end"
                fontSize="8"
                fontFamily="'JetBrains Mono', monospace"
                fill="#3a5070"
                transform={`rotate(-42, ${x + BAR_W / 2}, ${CH + 14})`}
              >
                {label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ─── Contributors list ────────────────────────────────────────────────────────

function ContributorRow({ c, isLast }: { c: Contributor; isLast: boolean }) {
  return (
    <a
      href={c.profile_url}
      target="_blank"
      rel="noopener noreferrer"
      className="res-contrib"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "9px 8px",
        borderRadius: 8,
        textDecoration: "none",
        transition: "background 0.15s",
        borderBottom: isLast ? "none" : "0.5px solid rgba(90,143,216,0.08)",
      }}
    >
      <img src={c.avatar_url} alt={c.login} width={30} height={30} loading="lazy"
        style={{ borderRadius: "50%", border: "1.5px solid rgba(90,143,216,0.2)", flexShrink: 0 }} />
      <span style={{
        flex: 1, minWidth: 0,
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 12, color: "#c8d8f0",
        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
      }}>
        {c.login}
      </span>
      <span style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11, color: "#5a8fd8", flexShrink: 0,
      }}>
        {fmtNum(c.contributions)} commits
      </span>
    </a>
  );
}

// ─── Security audit badge colour ──────────────────────────────────────────────

function auditColor(s: string): React.CSSProperties {
  switch (s) {
    case "clean":      return { color: "#22c55e", borderColor: "rgba(34,197,94,0.3)",  backgroundColor: "rgba(34,197,94,0.07)"  };
    case "outdated":   return { color: "#f59e0b", borderColor: "rgba(245,158,11,0.3)", backgroundColor: "rgba(245,158,11,0.07)" };
    case "vulnerable": return { color: "#cc1f1f", borderColor: "rgba(204,31,31,0.3)",  backgroundColor: "rgba(204,31,31,0.07)"  };
    default:           return { color: "#5a8fd8", borderColor: "rgba(90,143,216,0.3)", backgroundColor: "rgba(90,143,216,0.07)" };
  }
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Results() {
  injectKeyframes();

  const navigate = useNavigate();
  const location = useLocation();
  const result   = (location.state as { result?: AnalysisResult } | null)?.result;

  useEffect(() => {
    if (!result) navigate("/", { replace: true });
  }, [result, navigate]);

  if (!result) return null;

  const { meta, languages, contributors, activity,
          architecture, code_quality, security, analyzed_at } = result;

  return (
    <div style={S.root}>

      {/* Fixed dot-grid backdrop */}
      <div style={S.grid} aria-hidden="true" />

      {/* ── Sticky navigation bar ─────────────────────────────────────────── */}
      <nav style={S.nav} aria-label="Page navigation">
        <button
          className="res-back"
          onClick={() => navigate("/")}
          style={S.backBtn}
          aria-label="Go back to home"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          GitFit
        </button>

        <span style={S.navRepo}>{meta.full_name}</span>

        <span style={S.navMeta}>analyzed {fmtDate(analyzed_at)}</span>
      </nav>

      {/* ── Scrollable body ───────────────────────────────────────────────── */}
      <main style={S.body}>

        {/* ── Hero ─────────────────────────────────────────────────────────── */}
        <Card style={{ marginBottom: "1.5rem", animation: "fadeUp 0.4s ease both" }}>
          <div style={S.heroRow}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 6 }}>
                <h1 style={S.heroTitle}>{meta.full_name}</h1>
                {meta.license && (
                  <span style={S.badge}>{meta.license}</span>
                )}
                {meta.is_private && (
                  <span style={{ ...S.badge, color: "#cc1f1f", borderColor: "rgba(204,31,31,0.3)", backgroundColor: "rgba(204,31,31,0.08)" }}>
                    Private
                  </span>
                )}
              </div>
              <p style={S.heroDesc}>
                {meta.description || "No description provided."}
              </p>
            </div>

            <a href={meta.url} target="_blank" rel="noopener noreferrer"
               className="res-gh" style={S.ghBtn} aria-label="Open repository on GitHub">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23A11.52 11.52 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.29-1.552 3.297-1.23 3.297-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.605-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.298 24 12c0-6.63-5.37-12-12-12z" />
              </svg>
              View on GitHub
            </a>
          </div>

          {/* Stat row */}
          <div style={S.statsRow}>
            {([ ["★", "Stars",    meta.stars],
                 ["⑂", "Forks",    meta.forks],
                 ["●", "Issues",   meta.open_issues],
                 ["◎", "Watchers", meta.watchers],
               ] as [string, string, number][]).map(([icon, label, val]) => (
              <div key={label} style={S.stat}>
                <span style={S.statIcon}>{icon}</span>
                <span style={S.statVal}>{fmtNum(val)}</span>
                <span style={S.statLabel}>{label}</span>
              </div>
            ))}
            <div style={S.stat}>
              <span style={S.statIcon}>⎇</span>
              <span style={{ ...S.statVal, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" }}>
                {meta.default_branch}
              </span>
              <span style={S.statLabel}>Branch</span>
            </div>
          </div>

          {/* Topics */}
          {meta.topics.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
              {meta.topics.slice(0, 14).map(t => (
                <span key={t} className="res-topic" style={S.topic}>{t}</span>
              ))}
            </div>
          )}
        </Card>

        {/* ── Architecture + Code Quality ──────────────────────────────────── */}
        <div style={S.grid2} role="region" aria-label="Architecture and Code Quality">

          {/* Architecture */}
          <Card style={{ animation: "fadeUp 0.4s ease 0.07s both" }}>
            <SectionLabel>Architecture</SectionLabel>
            <p style={S.archSummary}>{architecture.summary}</p>

            {architecture.patterns.length > 0 && (
              <>
                <p style={S.subHead}>Detected patterns</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: "1rem" }}>
                  {architecture.patterns.map(p => (
                    <span key={p} style={S.patternChip}>{p}</span>
                  ))}
                </div>
              </>
            )}

            {architecture.entry_points.length > 0 && (
              <>
                <p style={S.subHead}>Entry points</p>
                <div style={S.codeList}>
                  {architecture.entry_points.map(ep => (
                    <span key={ep} style={S.codeLine}>{ep}</span>
                  ))}
                </div>
              </>
            )}

            {architecture.key_directories.length > 0 && (
              <>
                <p style={S.subHead}>Key directories</p>
                <div style={S.codeList}>
                  {architecture.key_directories.slice(0, 7).map(dir => (
                    <span key={dir} style={S.codeLine}>{dir}</span>
                  ))}
                </div>
              </>
            )}
          </Card>

          {/* Code Quality */}
          <Card style={{ animation: "fadeUp 0.4s ease 0.14s both" }}>
            <SectionLabel>Code Quality</SectionLabel>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 18, marginBottom: "1.25rem" }}>
              <ScoreRing score={code_quality.score} />
              <div style={{ flex: 1 }}>
                <Flag ok={code_quality.has_tests}  label="Test suite" />
                <Flag ok={code_quality.has_ci}     label="CI / CD pipeline" />
                <Flag ok={code_quality.has_docs}   label="Documentation folder" />
                <Flag ok={code_quality.has_linter} label="Linter / formatter" />
                <Flag ok={code_quality.has_docker} label="Docker support" />
              </div>
            </div>

            {code_quality.notes.length > 0 && (
              <>
                <p style={S.subHead}>Notes</p>
                <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
                  {code_quality.notes.map((n, i) => (
                    <li key={i} style={S.noteItem}>{n}</li>
                  ))}
                </ul>
              </>
            )}
          </Card>
        </div>

        {/* ── Languages ────────────────────────────────────────────────────── */}
        {languages.length > 0 && (
          <Card style={{ marginBottom: "1.5rem", animation: "fadeUp 0.4s ease 0.2s both" }}>
            <SectionLabel>Language Breakdown</SectionLabel>
            <LanguageChart langs={languages} />
          </Card>
        )}

        {/* ── Commit activity ───────────────────────────────────────────────── */}
        <Card style={{ marginBottom: "1.5rem", animation: "fadeUp 0.4s ease 0.27s both" }}>
          <SectionLabel>Weekly Commit Activity · last 12 weeks</SectionLabel>
          <ActivityChart weeks={activity} />
        </Card>

        {/* ── Contributors + Security ───────────────────────────────────────── */}
        <div style={S.grid2} role="region" aria-label="Contributors and Security">

          {/* Contributors */}
          <Card style={{ animation: "fadeUp 0.4s ease 0.33s both" }}>
            <SectionLabel>Top Contributors</SectionLabel>
            {contributors.length === 0 ? (
              <p style={{ fontSize: 13, color: "#3a5070", padding: "0.5rem 0" }}>
                No contributor data available.
              </p>
            ) : (
              <div>
                {contributors.map((c, i) => (
                  <ContributorRow key={c.login} c={c} isLast={i === contributors.length - 1} />
                ))}
              </div>
            )}
          </Card>

          {/* Security */}
          <Card style={{ animation: "fadeUp 0.4s ease 0.38s both" }}>
            <SectionLabel>Security Signals</SectionLabel>
            <div style={{ marginBottom: "1rem" }}>
              <Flag ok={security.has_env_example}  label=".env.example present" />
              <Flag ok={!security.exposes_secrets} label="No secret files exposed" />
              <div style={{
                ...S.auditBadge,
                ...auditColor(security.dependency_audit),
              }}>
                Dependency audit: <strong>{security.dependency_audit}</strong>
              </div>
            </div>

            {security.notes.length > 0 && (
              <>
                <p style={S.subHead}>Notes</p>
                <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
                  {security.notes.map((n, i) => (
                    <li key={i} style={S.noteItem}>{n}</li>
                  ))}
                </ul>
              </>
            )}
          </Card>
        </div>

        {/* ── Footer ────────────────────────────────────────────────────────── */}
        <p style={S.footer}>
          GitFit · {meta.full_name} · analyzed {fmtDate(analyzed_at)}
        </p>
      </main>
    </div>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const S: Record<string, React.CSSProperties> = {

  // Page shell — dark navy, fixed dot grid
  root: {
    fontFamily: "'Syne', 'Segoe UI', sans-serif",
    minHeight: "100vh",
    backgroundColor: "#070d1c",
    color: "#c8d8f0",
    position: "relative",
  },

  grid: {
    position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none",
    backgroundImage: "radial-gradient(circle, rgba(90,143,216,0.11) 1px, transparent 1px)",
    backgroundSize: "28px 28px",
  },

  // Sticky nav
  nav: {
    position: "sticky", top: 0, zIndex: 100,
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "0.75rem 1.5rem",
    backgroundColor: "rgba(7,13,28,0.88)",
    backdropFilter: "blur(22px) saturate(1.4)",
    WebkitBackdropFilter: "blur(22px) saturate(1.4)",
    borderBottom: "0.5px solid rgba(90,143,216,0.14)",
    gap: 12,
  },

  backBtn: {
    display: "flex", alignItems: "center", gap: 6,
    fontFamily: "'Syne', sans-serif",
    fontSize: 13, fontWeight: 600,
    color: "#5a8fd8",
    background: "none", border: "none",
    cursor: "pointer",
    borderRadius: 8, padding: "6px 10px",
    transition: "background 0.15s, color 0.15s",
    letterSpacing: "0.01em", flexShrink: 0,
  },

  navRepo: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 13, color: "#c8d8f0",
    letterSpacing: "0.02em",
    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
  },

  navMeta: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 10, color: "#3a5070",
    flexShrink: 0, whiteSpace: "nowrap",
  },

  // Scrollable body
  body: {
    position: "relative", zIndex: 1,
    maxWidth: 1060,
    margin: "0 auto",
    padding: "2rem 1.5rem 5rem",
  },

  // Hero
  heroRow: {
    display: "flex", alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 16, flexWrap: "wrap",
    marginBottom: "1.25rem",
  },

  heroTitle: {
    fontFamily: "'Syne', sans-serif",
    fontSize: 26, fontWeight: 700,
    color: "#e8f4ff",
    letterSpacing: "-0.02em", margin: 0,
  },

  heroDesc: {
    fontSize: 14, color: "#7a9fc0",
    lineHeight: 1.75, margin: "5px 0 0",
    maxWidth: 560,
  },

  badge: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 10, padding: "2px 9px",
    borderRadius: 100,
    backgroundColor: "rgba(90,143,216,0.09)",
    color: "#5a8fd8",
    border: "0.5px solid rgba(90,143,216,0.25)",
    whiteSpace: "nowrap",
  },

  ghBtn: {
    display: "flex", alignItems: "center", gap: 8,
    fontFamily: "'Syne', sans-serif",
    fontSize: 12, fontWeight: 600,
    color: "#5a8fd8",
    textDecoration: "none",
    border: "0.5px solid rgba(90,143,216,0.25)",
    borderRadius: 9, padding: "8px 14px",
    transition: "background 0.15s, color 0.15s",
    flexShrink: 0, whiteSpace: "nowrap",
  },

  // Stats
  statsRow: {
    display: "flex", flexWrap: "wrap", gap: 8,
    marginBottom: "1rem",
  },

  stat: {
    display: "flex", flexDirection: "column", alignItems: "center",
    padding: "10px 18px", borderRadius: 10,
    backgroundColor: "rgba(90,143,216,0.06)",
    border: "0.5px solid rgba(90,143,216,0.1)",
    minWidth: 76,
  },

  statIcon:  { fontSize: 13, color: "#5a8fd8", marginBottom: 4 },
  statVal:   { fontSize: 20, fontWeight: 700, color: "#ffffff", lineHeight: 1.1 },
  statLabel: {
    fontSize: 9, color: "#5a8fd8", marginTop: 3,
    letterSpacing: "0.06em", textTransform: "uppercase",
  },

  topic: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 10, color: "#5a8fd8",
    border: "0.5px solid rgba(90,143,216,0.22)",
    borderRadius: 100, padding: "3px 10px",
    backgroundColor: "rgba(90,143,216,0.05)",
    cursor: "default",
    transition: "border-color 0.15s, color 0.15s",
  },

  // 2-column responsive grid
  grid2: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: "1.5rem",
    marginBottom: "1.5rem",
  },

  // Architecture card internals
  archSummary: {
    fontSize: 14, color: "#c0d4ec", lineHeight: 1.8,
    marginBottom: "1.25rem",
  },

  subHead: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 9, color: "#3a5070",
    letterSpacing: "0.08em", textTransform: "uppercase",
    margin: "0.9rem 0 6px",
  },

  patternChip: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 11, color: "#cc1f1f",
    border: "0.5px solid rgba(204,31,31,0.28)",
    borderRadius: 6, padding: "3px 10px",
    backgroundColor: "rgba(204,31,31,0.07)",
  },

  codeList: {
    display: "flex", flexDirection: "column", gap: 4,
  },

  codeLine: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 11, color: "#7a9fc0",
    padding: "4px 9px", borderRadius: 5,
    backgroundColor: "rgba(90,143,216,0.05)",
    border: "0.5px solid rgba(90,143,216,0.1)",
    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
  },

  // Notes
  noteItem: {
    fontSize: 12, color: "#7a9fc0",
    lineHeight: 1.65,
    paddingLeft: 12,
    borderLeft: "2px solid rgba(90,143,216,0.2)",
    marginBottom: 7,
  },

  // Audit badge
  auditBadge: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 11,
    marginTop: 12, padding: "6px 12px",
    borderRadius: 7, border: "0.5px solid",
    display: "inline-block",
  },

  // Footer
  footer: {
    textAlign: "center",
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 10, color: "#1e2e45",
    marginTop: "2rem",
    letterSpacing: "0.05em",
  },
};