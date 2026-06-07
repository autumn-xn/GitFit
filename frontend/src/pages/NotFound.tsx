// ─── frontend/src/pages/NotFound.tsx ─────────────────────────────────────────
// 404 fallback page. Matches the dark-navy design system of Results.tsx.

import { useNavigate } from "react-router-dom";

function injectKf() {
  if (document.getElementById("nf-kf")) return;
  const s = document.createElement("style");
  s.id = "nf-kf";
  s.textContent = `
    @keyframes fadeUp  { from{opacity:0;transform:translateY(22px)} to{opacity:1;transform:translateY(0)} }
    @keyframes pulseNF { 0%,100%{opacity:1} 50%{opacity:.3} }
    .nf-btn:hover { opacity: .82; transform: scale(.98); }
    .nf-btn:active{ transform: scale(.95); }
  `;
  document.head.appendChild(s);
}

export default function NotFound() {
  injectKf();
  const navigate = useNavigate();

  return (
    <div style={{
      fontFamily: "'Syne', 'Segoe UI', sans-serif",
      minHeight: "100vh",
      backgroundColor: "#070d1c",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "2rem",
      position: "relative",
      overflow: "hidden",
    }}>

      {/* Dot grid */}
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none",
        backgroundImage: "radial-gradient(circle, rgba(90,143,216,0.11) 1px, transparent 1px)",
        backgroundSize: "28px 28px",
      }} aria-hidden="true" />

      {/* Diagonal accent — bottom-right */}
      <svg style={{
        position: "absolute", inset: 0, width: "100%", height: "100%",
        pointerEvents: "none", zIndex: 0,
      }} viewBox="0 0 900 600" aria-hidden="true" preserveAspectRatio="xMidYMid slice">
        <polygon points="900,600 340,600 540,380 900,440" fill="#1a3a8f" opacity="0.35" />
        <polygon points="900,560 240,600 440,420 900,400" fill="#cc1f1f"  opacity="0.25" />
      </svg>

      {/* Card */}
      <div style={{
        position: "relative", zIndex: 1,
        backgroundColor: "rgba(255,255,255,0.04)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        border: "0.5px solid rgba(90,143,216,0.18)",
        borderRadius: 20,
        padding: "3rem 3.5rem",
        textAlign: "center",
        animation: "fadeUp 0.45s cubic-bezier(.22,.68,0,1.2) both",
        maxWidth: 420,
        width: "100%",
      }}>

        {/* Huge mono 404 */}
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 112,
          fontWeight: 700,
          lineHeight: 1,
          color: "#1a3a8f",
          letterSpacing: "-0.06em",
          marginBottom: "0.75rem",
          userSelect: "none",
        }}>
          404
        </div>

        {/* Red pulse line */}
        <div style={{
          width: 40, height: 3,
          backgroundColor: "#cc1f1f",
          borderRadius: 2,
          margin: "0 auto 1.5rem",
          animation: "pulseNF 2s ease-in-out infinite",
        }} />

        <h1 style={{
          fontFamily: "'Syne', sans-serif",
          fontSize: 20, fontWeight: 700,
          color: "#e8f4ff",
          margin: "0 0 0.5rem",
          letterSpacing: "-0.02em",
        }}>
          Page not found
        </h1>

        <p style={{
          fontSize: 14, color: "#5a8fd8",
          margin: "0 0 2rem",
          lineHeight: 1.65,
        }}>
          This page doesn't exist. Head back home and paste a GitHub URL to get started.
        </p>

        <button
          className="nf-btn"
          onClick={() => navigate("/")}
          style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            backgroundColor: "#cc1f1f",
            color: "#ffffff",
            border: "none", borderRadius: 12,
            padding: "12px 24px",
            fontFamily: "'Syne', sans-serif",
            fontSize: 14, fontWeight: 600,
            cursor: "pointer",
            transition: "opacity 0.15s, transform 0.1s",
            letterSpacing: "0.01em",
          }}
          aria-label="Go home"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back to GitFit
        </button>

        {/* Bottom status badge */}
        <div style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10, color: "#3a5070",
          marginTop: "2rem",
          letterSpacing: "0.04em",
        }}>
          <span style={{
            width: 5, height: 5, borderRadius: "50%",
            backgroundColor: "#1a3a8f",
          }} />
          gitfit · repo analyzer
        </div>
      </div>
    </div>
  );
}