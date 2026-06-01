import { useState, useRef, useCallback } from "react";

// ─── Google Fonts ─────────────────────────────────────────────────────────────
// Add to your index.html <head>:
// <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

// ─── Types ────────────────────────────────────────────────────────────────────

interface RepoInputProps {
  onSubmit: (url: string) => void;
  isLoading?: boolean;
}

interface ExampleRepo {
  label: string;
  url: string;
  icon: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const EXAMPLE_REPOS: ExampleRepo[] = [
  { label: "facebook/react",   url: "https://github.com/facebook/react",   icon: "⚛" },
  { label: "vercel/next.js",   url: "https://github.com/vercel/next.js",   icon: "▲" },
  { label: "microsoft/vscode", url: "https://github.com/microsoft/vscode", icon: "◈" },
];

const GITHUB_REGEX =
  /^https?:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+(\/.*)?$/;

function validateUrl(url: string): string | null {
  if (!url.trim()) return "Please enter a GitHub repository URL.";
  if (!GITHUB_REGEX.test(url.trim()))
    return "Must be a valid github.com repository URL.";
  return null;
}

// ─── Keyframe injection ───────────────────────────────────────────────────────
// Injects once; safe to call multiple times.
function injectKeyframes() {
  if (document.getElementById("repo-input-kf")) return;
  const style = document.createElement("style");
  style.id = "repo-input-kf";
  style.textContent = `
    @keyframes spin   { to { transform: rotate(360deg); } }
    @keyframes pulse  { 0%,100% { opacity:1; } 50% { opacity:.35; } }
    @keyframes grain  {
      0%,100% { transform: translate(0,0); }
      10%     { transform: translate(-2%,-3%); }
      20%     { transform: translate(3%, 2%); }
      30%     { transform: translate(-1%, 4%); }
      40%     { transform: translate(4%,-1%); }
      50%     { transform: translate(-3%, 3%); }
      60%     { transform: translate(2%,-4%); }
      70%     { transform: translate(-4%, 1%); }
      80%     { transform: translate(1%, 3%); }
      90%     { transform: translate(3%,-2%); }
    }
    @keyframes slideIn {
      from { opacity:0; transform: translateY(18px); }
      to   { opacity:1; transform: translateY(0);    }
    }
    .repo-chip:hover {
      border-color: rgba(220,38,38,0.55) !important;
      color: #fff !important;
    }
    .repo-btn-analyze:hover  { opacity: .88; }
    .repo-btn-analyze:active { transform: scale(.97); }
  `;
  document.head.appendChild(style);
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function RepoInput({
  onSubmit,
  isLoading = false,
}: RepoInputProps) {
  injectKeyframes();

  const [url, setUrl]         = useState("");
  const [error, setError]     = useState<string | null>(null);
  const [touched, setTouched] = useState(false);
  const inputRef              = useRef<HTMLInputElement>(null);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setUrl(e.target.value);
      if (touched) setError(validateUrl(e.target.value));
    },
    [touched]
  );

  const handleSubmit = useCallback(() => {
    setTouched(true);
    const err = validateUrl(url);
    if (err) { setError(err); inputRef.current?.focus(); return; }
    setError(null);
    onSubmit(url.trim());
  }, [url, onSubmit]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => { if (e.key === "Enter") handleSubmit(); },
    [handleSubmit]
  );

  const fillExample = useCallback((exampleUrl: string) => {
    setUrl(exampleUrl);
    setError(null);
    setTouched(false);
    inputRef.current?.focus();
  }, []);

  // ─── Render ──────────────────────────────────────────────────────────────

  return (
    <div style={S.root}>

      {/* ── Dot-grid background ─────────────────────────────────────── */}
      <div style={S.gridBg} aria-hidden="true" />

      {/* ── Diagonal brush strokes (red + blue, layered) ────────────── */}
      <svg style={S.brushSvg} viewBox="0 0 900 600" aria-hidden="true"
           preserveAspectRatio="xMidYMid slice">
        {/* Blue top-left sweep */}
        <polygon points="-20,-20  560,-20  380,180  -20,120"
          fill="#1a3a8f" opacity="0.92" />
        {/* Red stripe above blue */}
        <polygon points="60,-20  640,-20  460,150  -20,95"
          fill="#cc1f1f" opacity="0.80" />
        {/* Light-blue / sky band */}
        <polygon points="-20,60  500,-20  310,200  -20,180"
          fill="#5a8fd8" opacity="0.45" />
        {/* White highlight slash */}
        <polygon points="120,-20  340,-20  240,90  60,90"
          fill="#ffffff" opacity="0.18" />

        {/* Bottom-right mirror */}
        <polygon points="900,620  340,620  520,420  900,480"
          fill="#1a3a8f" opacity="0.92" />
        <polygon points="900,560  260,620  440,450  900,420"
          fill="#cc1f1f" opacity="0.80" />
        <polygon points="900,540  400,620  590,400  900,460"
          fill="#5a8fd8" opacity="0.45" />
        <polygon points="760,620  980,620  900,490  700,490"
          fill="#ffffff" opacity="0.18" />

        {/* Small arrow accents */}
        <polygon points="210,55  228,46  228,64"  fill="#1a3a8f" opacity="0.9" />
        <polygon points="420,135 438,126 438,144" fill="#1a3a8f" opacity="0.9" />
        <polygon points="660,480 678,471 678,489" fill="#1a3a8f" opacity="0.9" />
        <polygon points="80,280  98,271  98,289"  fill="#ffffff"  opacity="0.6" />
        <polygon points="820,310 802,301 802,319" fill="#ffffff"  opacity="0.6" />
      </svg>

      {/* ── Grain overlay ───────────────────────────────────────────── */}
      <div style={S.grain} aria-hidden="true" />

      {/* ── Card ────────────────────────────────────────────────────── */}
      <div style={S.card}>

        {/* Status badge */}
        <div style={S.badge}>
          <span style={S.dot} />
          <span style={S.badgeText}>repo analyzer · v0.1</span>
        </div>

        <h1 style={S.heading}>
          Analyze any<br />GitHub repo
        </h1>
        <p style={S.sub}>
          Paste a repository URL for an instant breakdown of structure,
          code quality, contributors, and activity.
        </p>

        {/* Input row */}
        <div style={{ ...S.inputWrap, ...(error ? S.inputWrapError : {}) }}>
          <svg style={S.ghIcon} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23A11.52 11.52 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.29-1.552 3.297-1.23 3.297-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.605-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.298 24 12c0-6.63-5.37-12-12-12z"/>
          </svg>

          <input
            ref={inputRef}
            style={S.input}
            type="url"
            value={url}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="https://github.com/owner/repo"
            autoComplete="off"
            spellCheck={false}
            aria-label="GitHub repository URL"
            aria-invalid={!!error}
            aria-describedby={error ? "url-error" : undefined}
            disabled={isLoading}
          />

          <button
            className="repo-btn-analyze"
            style={{ ...S.btn, ...(isLoading ? S.btnDisabled : {}) }}
            onClick={handleSubmit}
            disabled={isLoading}
            aria-label="Analyze repository"
          >
            {isLoading ? (
              <span style={S.spinner} aria-hidden="true" />
            ) : (
              <svg style={{ width: 14, height: 14 }} viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
            )}
            <span>{isLoading ? "Analyzing…" : "Analyze"}</span>
          </button>
        </div>

        {/* Inline validation error */}
        {error && (
          <p id="url-error" style={S.error} role="alert">{error}</p>
        )}

        {/* Example chips */}
        <div style={S.chips} role="list" aria-label="Example repositories">
          {EXAMPLE_REPOS.map((repo) => (
            <button
              key={repo.url}
              className="repo-chip"
              style={S.chip}
              onClick={() => fillExample(repo.url)}
              disabled={isLoading}
              role="listitem"
              title={`Use ${repo.label} as example`}
            >
              <span aria-hidden="true">{repo.icon}</span>
              {repo.label}
            </button>
          ))}
        </div>

        <hr style={S.divider} />

        {/* Feature strip */}
        <div style={S.features}>
          {FEATURES.map((f) => (
            <div key={f.label} style={S.feat}>
              <span style={S.featIcon} aria-hidden="true">{f.icon}</span>
              <span style={S.featLabel}>{f.label}</span>
              <span style={S.featDesc}>{f.desc}</span>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}

// ─── Feature data ─────────────────────────────────────────────────────────────

const FEATURES = [
  { icon: "⎇", label: "Code structure",  desc: "Files, folders & languages" },
  { icon: "◎", label: "Contributors",    desc: "Commits & top authors"       },
  { icon: "⌁", label: "Activity",        desc: "Issues, PRs & releases"      },
];

// ─── Styles ───────────────────────────────────────────────────────────────────

const S: Record<string, React.CSSProperties> = {
  // ── Page shell ──────────────────────────────────────────────────────────────
  root: {
    fontFamily: "'Syne', 'Segoe UI', sans-serif",
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "2rem 1rem",
    position: "relative",
    overflow: "hidden",
    backgroundColor: "#f0f2f5",           // light neutral — red/blue pops against it
  },

  // Dot grid (unchanged structure, new color)
  gridBg: {
    position: "absolute",
    inset: 0,
    zIndex: 0,
    backgroundImage:
      "radial-gradient(circle, rgba(26,58,143,0.18) 1px, transparent 1px)",
    backgroundSize: "28px 28px",
  },

  // Diagonal brush SVG — sits above grid, below card
  brushSvg: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    zIndex: 1,
    pointerEvents: "none",
  },

  // Animated grain texture overlay
  grain: {
    position: "absolute",
    inset: "-50%",
    width: "200%",
    height: "200%",
    zIndex: 2,
    pointerEvents: "none",
    opacity: 0.055,
    backgroundImage:
      "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
    backgroundRepeat: "repeat",
    backgroundSize: "180px 180px",
    animation: "grain 7s steps(10) infinite",
  },

  // ── Card (box unchanged) ────────────────────────────────────────────────────
  card: {
    position: "relative",
    zIndex: 3,
    backgroundColor: "rgba(255,255,255,0.82)",
    backdropFilter: "blur(18px) saturate(1.4)",
    WebkitBackdropFilter: "blur(18px) saturate(1.4)",
    border: "0.5px solid rgba(255,255,255,0.7)",
    borderRadius: 20,
    padding: "2.5rem 2.5rem 2rem",
    width: "100%",
    maxWidth: 560,
    boxSizing: "border-box" as const,
    animation: "slideIn 0.45s cubic-bezier(.22,.68,0,1.2) both",
  },

  // ── Badge ───────────────────────────────────────────────────────────────────
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 7,
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 11,
    fontWeight: 500,
    backgroundColor: "rgba(26,58,143,0.08)",
    color: "#1a3a8f",
    border: "0.5px solid rgba(26,58,143,0.2)",
    borderRadius: 100,
    padding: "4px 12px",
    marginBottom: "1.5rem",
    letterSpacing: "0.04em",
  },
  badgeText: { lineHeight: 1 },
  dot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    backgroundColor: "#cc1f1f",
    flexShrink: 0,
    animation: "pulse 2s ease-in-out infinite",
  },

  // ── Heading / sub ───────────────────────────────────────────────────────────
  heading: {
    fontSize: 30,
    fontWeight: 700,
    color: "#0d1b4b",
    lineHeight: 1.2,
    margin: "0 0 0.4rem",
    letterSpacing: "-0.025em",
  },
  sub: {
    fontSize: 14,
    color: "#4a5568",
    margin: "0 0 2rem",
    lineHeight: 1.7,
  },

  // ── Input row ───────────────────────────────────────────────────────────────
  inputWrap: {
    display: "flex",
    alignItems: "center",
    border: "0.5px solid rgba(26,58,143,0.22)",
    borderRadius: 14,
    backgroundColor: "rgba(255,255,255,0.9)",
    padding: "4px 4px 4px 14px",
    gap: 8,
    transition: "border-color 0.15s, box-shadow 0.15s",
    boxShadow: "0 1px 3px rgba(26,58,143,0.08)",
  },
  inputWrapError: {
    borderColor: "rgba(204,31,31,0.55)",
    boxShadow: "0 0 0 3px rgba(204,31,31,0.08)",
  },
  ghIcon: {
    width: 18,
    height: 18,
    color: "#1a3a8f",
    flexShrink: 0,
    opacity: 0.7,
  },
  input: {
    flex: 1,
    border: "none",
    background: "transparent",
    fontFamily: "'JetBrains Mono', 'Courier New', monospace",
    fontSize: 13,
    color: "#0d1b4b",
    outline: "none",
    padding: "8px 0",
    minWidth: 0,
  },

  // Analyze button — bold red accent
  btn: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#cc1f1f",
    color: "#ffffff",
    border: "none",
    borderRadius: 10,
    padding: "9px 16px",
    fontFamily: "'Syne', sans-serif",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    whiteSpace: "nowrap" as const,
    flexShrink: 0,
    transition: "opacity 0.15s, transform 0.1s",
    letterSpacing: "0.01em",
  },
  btnDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
  spinner: {
    display: "inline-block",
    width: 12,
    height: 12,
    border: "2px solid rgba(255,255,255,0.3)",
    borderTopColor: "#ffffff",
    borderRadius: "50%",
    animation: "spin 0.7s linear infinite",
  },

  // ── Error ───────────────────────────────────────────────────────────────────
  error: {
    fontSize: 12,
    color: "#cc1f1f",
    margin: "8px 0 0",
    paddingLeft: 2,
  },

  // ── Example chips ───────────────────────────────────────────────────────────
  chips: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: 8,
    marginTop: "1.25rem",
  },
  chip: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    color: "#1a3a8f",
    border: "0.5px solid rgba(26,58,143,0.22)",
    borderRadius: 100,
    padding: "4px 12px",
    cursor: "pointer",
    transition: "border-color 0.15s, color 0.15s",
    fontFamily: "'JetBrains Mono', monospace",
    background: "rgba(26,58,143,0.04)",
  },

  // ── Divider ─────────────────────────────────────────────────────────────────
  divider: {
    border: "none",
    borderTop: "0.5px solid rgba(26,58,143,0.12)",
    margin: "1.5rem 0 1.25rem",
  },

  // ── Feature strip ───────────────────────────────────────────────────────────
  features: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 10,
  },
  feat: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 4,
    padding: "10px 12px",
    borderRadius: 10,
    backgroundColor: "rgba(26,58,143,0.05)",
    border: "0.5px solid rgba(26,58,143,0.08)",
  },
  featIcon: {
    fontSize: 16,
    color: "#cc1f1f",
    marginBottom: 2,
  },
  featLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: "#0d1b4b",
  },
  featDesc: {
    fontSize: 10,
    color: "#6b7280",
    lineHeight: 1.4,
  },
};