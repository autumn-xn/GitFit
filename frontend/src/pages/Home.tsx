// ─── frontend/src/pages/Home.tsx ─────────────────────────────────────────────
// Entry page. Renders RepoInput, wires it to useAnalysis,
// and navigates to /results once analysis succeeds.

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import RepoInput from "../components/RepoInput";
import { useAnalysis } from "../hooks/useAnalysis";

export default function Home() {
  const navigate                          = useNavigate();
  const { analyze, isLoading, isSuccess,
          isError, error, result, reset } = useAnalysis();

  // ── Navigate to results as soon as we have data ───────────────────────────
  useEffect(() => {
    if (isSuccess && result) {
      navigate("/results", {
        state: { result },   // Results.tsx reads this via useLocation()
      });
    }
  }, [isSuccess, result, navigate]);

  // ── Handler passed down to RepoInput ──────────────────────────────────────
  const handleSubmit = (url: string) => {
    reset();          // clear any previous error before firing
    analyze(url);
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      {/* RepoInput owns its own full-page layout (bg, grid, card) */}
      <RepoInput onSubmit={handleSubmit} isLoading={isLoading} />

      {/* Floating error toast — only shown when backend returns an error */}
      {isError && error && (
        <div style={toastStyle} role="alert" aria-live="assertive">
          <span style={{ marginRight: 8 }}>⚠</span>
          {error}
          <button
            onClick={reset}
            style={toastCloseStyle}
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}
    </>
  );
}

// ─── Toast styles ─────────────────────────────────────────────────────────────

const toastStyle: React.CSSProperties = {
  position: "fixed",
  bottom: "2rem",
  left: "50%",
  transform: "translateX(-50%)",
  zIndex: 9999,
  display: "flex",
  alignItems: "center",
  gap: 8,
  backgroundColor: "#1a1a1a",
  color: "#ffffff",
  border: "0.5px solid rgba(204,31,31,0.5)",
  borderRadius: 12,
  padding: "12px 18px",
  fontSize: 13,
  fontFamily: "'Syne', 'Segoe UI', sans-serif",
  maxWidth: "min(480px, 90vw)",
  boxShadow: "0 4px 24px rgba(0,0,0,0.18)",
  animation: "slideIn 0.25s ease both",
};

const toastCloseStyle: React.CSSProperties = {
  marginLeft: "auto",
  background: "none",
  border: "none",
  color: "rgba(255,255,255,0.5)",
  cursor: "pointer",
  fontSize: 13,
  padding: "0 0 0 12px",
  flexShrink: 0,
};