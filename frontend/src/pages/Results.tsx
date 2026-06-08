// ─── frontend/src/pages/Results.tsx ──────────────────────────────────────────
// Professional results dashboard — tuned to match the home page geometry.
// Deep navy (#1a3a8f), bold red (#cc1f1f), sky blue (#5a8fd8).
// Muted glassmorphism, heavy geometric background, high red prominence.

import { useLocation, useNavigate } from "react-router-dom";
import type { AnalysisResult } from "../types";

// ─── Keyframes & Global CSS ───────────────────────────────────────────────────
function injectKF() {
  if (document.getElementById("results-kf")) return;
  const s = document.createElement("style");
  s.id = "results-kf";
  s.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600;700;800&display=swap');

    @keyframes fadeUp   { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:translateY(0); } }
    @keyframes barGrow  { from { width:0%; } to { width:var(--w); } }
    @keyframes ringFill { from { stroke-dashoffset: 283; } to { stroke-dashoffset: var(--offset); } }
    @keyframes pulse    { 0%,100%{opacity:1} 50%{opacity:.35} }
    @keyframes float    { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-5px)} }

    .bento-grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }

    .col-span-12 { grid-column: span 12; }
    .col-span-8  { grid-column: span 8; }
    .col-span-6  { grid-column: span 6; }
    .col-span-4  { grid-column: span 4; }

    @media (max-width: 1024px) {
      .col-span-4 { grid-column: span 6; }
    }
    @media (max-width: 768px) {
      .col-span-4, .col-span-6, .col-span-8 { grid-column: span 12; }
    }

    /* Muted, high-blur glassmorphism to match the image */
    .res-card { 
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
      background: rgba(255, 255, 255, 0.45);
      backdrop-filter: blur(40px) saturate(1.8);
      -webkit-backdrop-filter: blur(40px) saturate(1.8);
      border: 1px solid rgba(255, 255, 255, 0.6);
      box-shadow: 0 12px 40px rgba(26,58,143,0.08), inset 0 1px 0 rgba(255,255,255,0.8);
    }
    .res-card:hover { 
      box-shadow: 0 20px 50px rgba(204,31,31,0.08), 0 0 0 1px rgba(204,31,31,0.1) !important; 
      transform: translateY(-4px); 
    }

    .lang-bar-fill { animation: barGrow 1s cubic-bezier(.22,.68,0,1.2) both; }
    .score-ring circle:last-child { animation: ringFill 1.2s cubic-bezier(.22,.68,0,1.2) 0.3s both; }

    .back-btn:hover { background: rgba(204,31,31,0.08) !important; color: #cc1f1f !important; border-color: rgba(204,31,31,0.35) !important; }
    .tag-chip:hover { background: rgba(204,31,31,0.8) !important; color: #fff !important; transform: scale(1.05); }
    .contrib-row:hover { background: rgba(204,31,31,0.04) !important; padding-left: 10px !important; border-color: rgba(204,31,31,0.15) !important; }
  `;
  document.head.appendChild(s);
}

// ─── Color palette ────────────────────────────────────────────────────────────
const C = {
  navy:  "#1a3a8f",
  red:   "#cc1f1f",
  sky:   "#5a8fd8",
  ink:   "#0a1128",
  slate: "#4a5568",
  mist:  "#f4f7fb",
  white: "#ffffff",
};

const LANG_COLORS: Record<string, string> = {
  TypeScript: "#3178c6", JavaScript: "#f7df1e", Python: "#3572A5",
  Java: "#b07219",       "C++": "#f34b7d",       Rust: "#dea584",
  Go: "#00ADD8",         Ruby: "#701516",         CSS: "#563d7c",
  HTML: "#e34c26",       Shell: "#89e051",        Kotlin: "#A97BFF",
  Swift: "#F05138",      Dart: "#00B4AB",         Vue: "#41b883",
  Other: "#8b9ab5",
};
function langColor(lang: string) { return LANG_COLORS[lang] ?? C.sky; }

// ─── Number formatter ─────────────────────────────────────────────────────────
function fmt(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}
function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { year:"numeric", month:"short", day:"numeric" });
}

// ─── Components ───────────────────────────────────────────────────────────────
function Card({ children, className = "", delay = "0s" }: { children: React.ReactNode; className?: string; delay?: string }) {
  return (
    <div className={`res-card ${className}`} style={{
      borderRadius: 24, // Matching home page rounded corners
      padding: "1.75rem",
      animation: `fadeUp 0.6s cubic-bezier(.22,.68,0,1.2) ${delay} both`,
      display: "flex", flexDirection: "column"
    }}>
      {children}
    </div>
  );
}

function SectionHead({ icon, label }: { icon: string; label: string }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:"1.5rem" }}>
      <div style={{ 
        width: 32, height: 32, borderRadius: 10, background: `linear-gradient(135deg, ${C.red}, #f87171)`, 
        display:"flex", alignItems:"center", justifyContent:"center", color: "#fff",
        fontFamily:"'JetBrains Mono',monospace", fontSize:16,
        boxShadow: `0 4px 10px ${C.red}40`
      }}>
        {icon}
      </div>
      <span style={{
        fontFamily:"'Syne',sans-serif", fontSize:14, fontWeight:800,
        color: C.ink, letterSpacing:"0.05em", textTransform:"uppercase",
      }}>{label}</span>
      <div style={{ flex:1, height:"1px", background:`linear-gradient(90deg, rgba(204,31,31,0.2), transparent)` }} />
    </div>
  );
}

function StatBadge({ value, label, accent = false }: { value: string; label: string; accent?: boolean }) {
  return (
    <div style={{
      display:"flex", flexDirection:"column", justifyContent:"center",
      padding:"1rem", flex: 1, minWidth: 90,
      background: accent ? `linear-gradient(135deg, rgba(204,31,31,0.1), rgba(204,31,31,0.02))` : "rgba(255,255,255,0.4)",
      border: `1px solid ${accent ? "rgba(204,31,31,0.2)" : "rgba(26,58,143,0.08)"}`,
      borderRadius:16, transition: "transform 0.2s"
    }}>
      <span style={{ fontFamily:"'Syne',sans-serif", fontSize:24, fontWeight:800, color: accent ? C.red : C.ink, lineHeight:1.2 }}>
        {value}
      </span>
      <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.slate, letterSpacing:"0.02em" }}>
        {label}
      </span>
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  // Make the primary color red if it's below 75, otherwise green. Increases red visibility.
  const color = score >= 85 ? "#10b981" : score >= 60 ? C.sky : C.red;

  return (
    <div style={{ position:"relative", width:140, height:140, animation: "float 6s ease-in-out infinite" }}>
      <svg width="140" height="140" viewBox="0 0 140 140" className="score-ring" style={{ transform:"rotate(-90deg)", filter: `drop-shadow(0 0 12px ${color}50)` }}>
        <circle cx="70" cy="70" r={r} fill="rgba(0,0,0,0.15)" strokeWidth="12" stroke="rgba(255,255,255,0.1)" />
        <circle cx="70" cy="70" r={r} fill="none" strokeWidth="12" stroke={color} strokeLinecap="round"
                strokeDasharray={circ} style={{ "--offset": offset } as React.CSSProperties} strokeDashoffset={offset} />
      </svg>
      <div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center" }}>
        <span style={{ fontFamily:"'Syne',sans-serif", fontSize:36, fontWeight:800, color:"#fff", lineHeight:1 }}>{score}</span>
        <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, color:"rgba(255,255,255,0.7)", letterSpacing:"0.1em" }}>SCORE</span>
      </div>
    </div>
  );
}

function FlagPill({ label, active, icon }: { label: string; active: boolean; icon: string }) {
  return (
    <div style={{
      display:"flex", alignItems:"center", gap:8, padding:"8px 14px", flex: "1 1 calc(50% - 8px)",
      background: active ? "rgba(255,255,255,0.4)" : "rgba(204,31,31,0.08)",
      border: `1px solid ${active ? "rgba(16,185,129,0.2)" : "rgba(204,31,31,0.25)"}`,
      borderRadius: 12, fontFamily:"'JetBrains Mono',monospace", fontSize:12, fontWeight:500,
      color: active ? "#059669" : C.red,
    }}>
      <span style={{ fontSize:14 }}>{icon}</span>
      <span style={{ flex:1 }}>{label}</span>
      <span>{active ? "✓" : "✗"}</span>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function Results() {
  injectKF();
  const navigate  = useNavigate();
  const location  = useLocation();
  const result    = (location.state as { result?: AnalysisResult })?.result;

  if (!result) { navigate("/", { replace: true }); return null; }
  const { meta, languages, contributors, activity, architecture, code_quality, security, analyzed_at } = result;

  const totalCommits = activity.reduce((s, w) => s + w.commits, 0);
  const totalAdditions = activity.reduce((s, w) => s + w.additions, 0);
  const peakWeek = activity.reduce((mx, w) => w.commits > mx.commits ? w : mx, activity[0] ?? { commits: 0, week: "" });

  return (
    <div style={{ fontFamily:"'Syne','Segoe UI',sans-serif", minHeight:"100vh", background: C.mist, paddingBottom:"4rem", position: "relative", overflowX: "hidden" }}>
      
      {/* ── BACKGROUND GEOMETRY (Matching Image) ────────────────────── */}
      <div style={{ position:"fixed", inset:0, zIndex:0, pointerEvents:"none", backgroundImage: "radial-gradient(circle, rgba(26,58,143,0.1) 1.5px, transparent 1.5px)", backgroundSize: "32px 32px" }} />
      
      <svg style={{ position:"fixed", inset:0, width:"100%", height:"100%", zIndex:0, pointerEvents:"none", opacity: 0.85 }} viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">
        {/* Top Left Block */}
        <polygon points="-100,-100 800,-100 400,300 -100,200" fill={C.red} opacity="0.9" />
        <polygon points="-100,-100 600,-100 300,400 -100,300" fill={C.navy} opacity="0.8" />
        <polygon points="-100,-100 900,-100 500,200 -100,100" fill={C.sky} opacity="0.4" />
        
        {/* Abstract Triangles Top Left */}
        <polygon points="200,80 220,60 220,100" fill={C.navy} opacity="0.7" />
        <polygon points="300,180 340,160 320,200" fill={C.navy} opacity="0.5" />

        {/* Bottom Right Block */}
        <polygon points="1540,1000 600,1000 1000,600 1540,700" fill={C.red} opacity="0.8" />
        <polygon points="1540,1000 800,1000 1100,500 1540,600" fill={C.navy} opacity="0.85" />
        <polygon points="1540,1000 500,1000 900,700 1540,800" fill={C.sky} opacity="0.4" />

        {/* Abstract Triangles Bottom Right */}
        <polygon points="1200,820 1180,840 1180,800" fill={C.navy} opacity="0.7" />
        <polygon points="1350,650 1310,670 1330,630" fill={C.red} opacity="0.6" />
      </svg>

      {/* ── HEADER ─────────────────────────────────────────────────── */}
      <header style={{
        position:"sticky", top:0, zIndex:100, background:"rgba(255,255,255,0.6)",
        backdropFilter:"blur(24px)", borderBottom:"1px solid rgba(204,31,31,0.1)",
        display:"flex", alignItems:"center", justifyContent:"space-between", padding:"0 2rem", height:64,
      }}>
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ width:32, height:32, borderRadius:10, background:C.red, display:"flex", alignItems:"center", justifyContent:"center", boxShadow: `0 4px 12px ${C.red}50` }}>
            <span style={{ color:"#fff", fontSize:16, fontFamily:"'JetBrains Mono',monospace" }}>⌥</span>
          </div>
          <span style={{ fontFamily:"'Syne',sans-serif", fontWeight:800, fontSize:18, color:C.ink }}>GitFit</span>
          <div style={{ width: 1, height: 16, background: "rgba(204,31,31,0.3)" }} />
          <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.slate, textTransform: "uppercase", letterSpacing:"0.05em" }}>Intelligence Report</span>
        </div>
        <button className="back-btn" onClick={() => navigate("/")} style={{
          display:"flex", alignItems:"center", gap:8, padding:"8px 18px", fontFamily:"'Syne',sans-serif", fontSize:13, fontWeight:700,
          color:C.red, background:"rgba(255,255,255,0.8)", border:`1px solid rgba(204,31,31,0.25)`, borderRadius:99, cursor:"pointer", transition:"all 0.2s",
          boxShadow: "0 2px 8px rgba(204,31,31,0.1)"
        }}>
          ← New Scan
        </button>
      </header>

      {/* ── MAIN LAYOUT ────────────────────────────────────────────────── */}
      <div style={{ position:"relative", zIndex:10, maxWidth:1280, margin:"0 auto", padding:"2.5rem 1.5rem" }}>
        
        {/* ── HERO SECTION (Col 12) ─────────────────────────────────────── */}
        <div className="bento-grid">
          <div className="col-span-12" style={{
            background:`linear-gradient(135deg, rgba(10,17,40,0.9) 0%, rgba(204,31,31,0.85) 100%)`,
            backdropFilter: "blur(20px)",
            borderRadius: 32, padding:"3rem", position:"relative", overflow:"hidden",
            boxShadow:"0 24px 48px rgba(204,31,31,0.15), inset 0 1px 0 rgba(255,255,255,0.2)",
            animation:"fadeUp 0.6s cubic-bezier(.22,.68,0,1.2) both",
          }}>
            <div style={{ position:"relative", zIndex:2, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "2rem" }}>
              <div style={{ flex: "1 1 500px" }}>
                <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:16 }}>
                  <span style={{ background:"rgba(255,255,255,0.15)", backdropFilter: "blur(10px)", borderRadius:8, padding:"6px 12px", fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:"#fff", letterSpacing:"0.05em" }}>github.com</span>
                  <div style={{ display:"flex", alignItems:"center", gap:8, background:"rgba(255,255,255,0.2)", border:"1px solid rgba(255,255,255,0.4)", borderRadius:99, padding:"4px 12px", fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:"#fff" }}>
                    <span style={{ width:6, height:6, borderRadius:"50%", background:"#fff", animation:"pulse 2s infinite" }} /> Verified Scan
                  </div>
                </div>

                <h1 style={{ fontFamily:"'Syne',sans-serif", fontSize:"clamp(2rem, 4vw, 3rem)", fontWeight:800, color:"#fff", margin:0, lineHeight:1.1, letterSpacing:"-0.03em" }}>
                  {meta.owner} <span style={{ color:"rgba(255,255,255,0.4)", fontWeight: 400 }}>/</span> <span style={{ color:"#fff" }}>{meta.name}</span>
                </h1>
                
                {meta.description && <p style={{ fontFamily:"'Syne',sans-serif", fontSize:16, color:"rgba(255,255,255,0.8)", margin:"1rem 0 0", maxWidth: 650, lineHeight:1.6 }}>{meta.description}</p>}

                {meta.topics.length > 0 && (
                  <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginTop:"1.5rem" }}>
                    {meta.topics.map(t => (
                      <span key={t} className="tag-chip" style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.red, background:"rgba(255,255,255,0.9)", border:"1px solid rgba(255,255,255,1)", borderRadius:99, padding:"6px 14px", cursor:"default", transition:"all 0.2s" }}>
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Score & Stats right block */}
              <div style={{ display: "flex", gap: "2rem", alignItems: "center", background: "rgba(0,0,0,0.25)", padding: "1.5rem", borderRadius: 24, border: "1px solid rgba(255,255,255,0.15)", backdropFilter: "blur(12px)" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div><div style={{color:"#fff", fontSize: 20, fontWeight: 700, fontFamily: "Syne"}}>{fmt(meta.stars)}</div><div style={{color: "rgba(255,255,255,0.6)", fontSize: 11, fontFamily: "JetBrains Mono"}}>STARS</div></div>
                  <div><div style={{color:"#fff", fontSize: 20, fontWeight: 700, fontFamily: "Syne"}}>{fmt(meta.forks)}</div><div style={{color: "rgba(255,255,255,0.6)", fontSize: 11, fontFamily: "JetBrains Mono"}}>FORKS</div></div>
                  <div><div style={{color:"#fff", fontSize: 20, fontWeight: 700, fontFamily: "Syne"}}>{fmt(meta.open_issues)}</div><div style={{color: "rgba(255,255,255,0.6)", fontSize: 11, fontFamily: "JetBrains Mono"}}>ISSUES</div></div>
                  <div><div style={{color:"#fff", fontSize: 20, fontWeight: 700, fontFamily: "Syne"}}>{contributors.length}</div><div style={{color: "rgba(255,255,255,0.6)", fontSize: 11, fontFamily: "JetBrains Mono"}}>CONTRIBS</div></div>
                </div>
                <div style={{ width: 1, height: 100, background: "rgba(255,255,255,0.2)" }} />
                <ScoreRing score={code_quality.score} />
              </div>
            </div>
          </div>
        </div>

        {/* ── BENTO GRID START ─────────────────────────────────────────── */}
        <div className="bento-grid">
          
          {/* Architecture (Col 4) */}
          <Card className="col-span-4" delay="0.1s">
            <SectionHead icon="⌁" label="Architecture" />
            <p style={{ fontFamily:"'Syne',sans-serif", fontSize:14, color:C.slate, lineHeight:1.7, margin:"0 0 1.5rem", flex: 1 }}>{architecture.summary}</p>
            <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom: "1.5rem" }}>
              {architecture.patterns.map(p => (
                <span key={p} style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.red, background:"rgba(255,255,255,0.5)", border:"1px solid rgba(204,31,31,0.2)", borderRadius:8, padding:"6px 12px", fontWeight: 500 }}>{p}</span>
              ))}
            </div>
            {architecture.entry_points.length > 0 && (
              <div style={{ background: "rgba(255,255,255,0.4)", padding: "1rem", borderRadius: 12, border: "1px dashed rgba(204,31,31,0.25)" }}>
                <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, color:C.red, letterSpacing:"0.05em", textTransform:"uppercase", marginBottom:8 }}>Entry Points</div>
                <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  {architecture.entry_points.map(e => (
                    <div key={e} style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:12, color:C.ink }}>• {e}</div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Code Quality (Col 4) */}
          <Card className="col-span-4" delay="0.15s">
            <SectionHead icon="◎" label="Code Quality" />
            <div style={{ display:"flex", flexWrap:"wrap", gap:10, marginBottom:"1.5rem" }}>
              <FlagPill label="Tests"  active={code_quality.has_tests}  icon="🧪" />
              <FlagPill label="CI/CD"  active={code_quality.has_ci}     icon="⚡" />
              <FlagPill label="Docs"   active={code_quality.has_docs}   icon="📖" />
              <FlagPill label="Linter" active={code_quality.has_linter} icon="⚙️" />
            </div>
            <div style={{ flex: 1, background: "rgba(255,255,255,0.4)", borderRadius: 16, padding: "1rem", border: "1px solid rgba(26,58,143,0.05)" }}>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, color:C.slate, letterSpacing:"0.05em", textTransform:"uppercase", marginBottom:12 }}>Analysis Notes</div>
              {code_quality.notes.map((n, i) => (
                <div key={i} style={{ display:"flex", alignItems:"flex-start", gap:10, marginBottom:10 }}>
                  <span style={{ color: n.includes("No ") ? C.red : "#10b981", fontSize:14, lineHeight: 1.2 }}>{n.includes("No ") ? "→" : "✓"}</span>
                  <span style={{ fontFamily:"'Syne',sans-serif", fontSize:13, color:C.slate, lineHeight:1.5 }}>{n}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Security (Col 4) */}
          <Card className="col-span-4" delay="0.2s">
            <SectionHead icon="⚿" label="Security & Meta" />
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", background: security.exposes_secrets ? "rgba(204,31,31,0.05)" : "rgba(255,255,255,0.5)", border:`1px solid ${security.exposes_secrets ? "rgba(204,31,31,0.2)" : "rgba(16,185,129,0.2)"}`, borderRadius:16, padding:"1rem 1.25rem", marginBottom:"1.25rem" }}>
              <span style={{ fontFamily:"'Syne',sans-serif", fontSize:14, fontWeight:700, color:C.ink }}>Dep Audit</span>
              <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:12, fontWeight: 700, color: security.dependency_audit === "clean" ? "#059669" : C.red, textTransform:"uppercase" }}>{security.dependency_audit}</span>
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:"1.5rem" }}>
              <FlagPill label=".env protection" active={security.has_env_example} icon="🛡️" />
              <FlagPill label="Secrets clean" active={!security.exposes_secrets} icon="🔑" />
            </div>
            
            <div style={{ marginTop: "auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[
                { label:"Created",  value: fmtDate(meta.created_at) },
                { label:"Updated",  value: fmtDate(meta.updated_at) },
                { label:"Branch",   value: meta.default_branch },
                { label:"License",  value: meta.license ?? "None" },
              ].map(r => (
                <div key={r.label} style={{ background:"rgba(255,255,255,0.4)", borderRadius:12, padding:"10px 12px", border: "1px solid rgba(255,255,255,0.6)" }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, color:C.red, textTransform:"uppercase", marginBottom:4 }}>{r.label}</div>
                  <div style={{ fontFamily:"'Syne',sans-serif", fontSize:13, fontWeight:700, color:C.ink, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{r.value}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* Commit Activity (Col 8) */}
          <Card className="col-span-8" delay="0.25s">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom:"1rem" }}>
              <SectionHead icon="📈" label="Commit Velocity (12w)" />
              <div style={{ display: "flex", gap: "1rem" }}>
                <div style={{ textAlign: "right" }}><div style={{ fontFamily: "Syne", fontSize: 20, fontWeight: 800, color: C.ink }}>{totalCommits}</div><div style={{ fontFamily: "JetBrains Mono", fontSize: 10, color: C.slate }}>TOTAL</div></div>
                <div style={{ textAlign: "right" }}><div style={{ fontFamily: "Syne", fontSize: 20, fontWeight: 800, color: C.red }}>+{fmt(totalAdditions)}</div><div style={{ fontFamily: "JetBrains Mono", fontSize: 10, color: C.slate }}>ADDITIONS</div></div>
              </div>
            </div>

            <div style={{ flex: 1, display: "flex", alignItems: "flex-end", gap: 6, height: 140, marginTop: "1rem", paddingBottom: 24, position: "relative", borderBottom: "1px solid rgba(204,31,31,0.2)" }}>
              {activity.map((w, i) => {
                const maxC = Math.max(...activity.map(x => x.commits), 1);
                const h = (w.commits / maxC) * 100;
                const isPeak = w.commits === maxC;
                return (
                  <div key={i} style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", gap:6, position: "relative" }}>
                    <div title={`Week ${w.week?.slice(0,10)}: ${w.commits} commits`} style={{
                      width:"100%", height:`${h}%`, minHeight: w.commits > 0 ? 4 : 0,
                      background: isPeak ? `linear-gradient(180deg, ${C.red}, rgba(204,31,31,0.4))` : `linear-gradient(180deg, ${C.navy}, rgba(26,58,143,0.3))`,
                      borderRadius: "6px 6px 0 0", transition:"height 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
                      boxShadow: isPeak ? `0 -4px 12px rgba(204,31,31,0.4)` : "none"
                    }} />
                    {i % 2 === 0 && <span style={{ position: "absolute", bottom: -24, fontFamily:"'JetBrains Mono',monospace", fontSize: 9, color: C.slate }}>{w.week?.slice(5,10)}</span>}
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Languages (Col 4) */}
          <Card className="col-span-4" delay="0.3s">
            <SectionHead icon="⎇" label="Languages" />
            <div style={{ display: "flex", gap: "1.5rem", alignItems: "center" }}>
              <div style={{ flex: 1 }}>
                {languages.slice(0, 5).map((l, i) => (
                  <div key={l.language} style={{ marginBottom:"0.8rem" }}>
                    <div style={{ display:"flex", justifyContent:"space-between", marginBottom:6 }}>
                      <span style={{ display:"flex", alignItems:"center", gap:8 }}>
                        <span style={{ width:10, height:10, borderRadius:"3px", background:langColor(l.language) }} />
                        <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:12, color:C.ink, fontWeight:600 }}>{l.language}</span>
                      </span>
                      <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.slate }}>{l.percentage}%</span>
                    </div>
                    <div style={{ height:6, background:"rgba(255,255,255,0.6)", border: "1px solid rgba(0,0,0,0.05)", borderRadius:99, overflow:"hidden" }}>
                      <div className="lang-bar-fill" style={{ height:"100%", borderRadius:99, background:langColor(l.language), "--w": `${l.percentage}%`, animationDelay: `${i * 100}ms` } as React.CSSProperties} />
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ position: "relative", width: 90, height: 90 }}>
                 <svg viewBox="0 0 120 120" width="90" height="90" style={{ filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.1))" }}>
                  {(() => {
                    let start = 0; const r = 48, cx = 60, cy = 60, circ = 2 * Math.PI * r;
                    return languages.slice(0, 8).map(l => {
                      const pct = l.percentage / 100, dash = pct * circ, gap = circ - dash, offset = -start * circ; start += pct;
                      return <circle key={l.language} cx={cx} cy={cy} r={r} fill="none" strokeWidth="18" stroke={langColor(l.language)} strokeDasharray={`${dash} ${gap}`} strokeDashoffset={offset} style={{ transform:`rotate(-90deg)`, transformOrigin:"60px 60px", transition: "stroke-dashoffset 1s" }} />;
                    });
                  })()}
                </svg>
              </div>
            </div>
          </Card>

          {/* Contributors (Col 8) */}
          <Card className="col-span-8" delay="0.35s">
            <SectionHead icon="◈" label="Key Contributors" />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "1rem" }}>
              {contributors.slice(0, 6).map((c, i) => {
                const maxContribs = contributors[0]?.contributions || 1;
                const pct = (c.contributions / maxContribs) * 100;
                return (
                  <div key={c.login} className="contrib-row" style={{ display:"flex", alignItems:"center", gap:14, padding:"12px", background: "rgba(255,255,255,0.4)", borderRadius:16, border: "1px solid rgba(255,255,255,0.6)", transition: "all 0.2s" }}>
                    <img src={c.avatar_url} alt={c.login} style={{ width:40, height:40, borderRadius:"50%", border:`2px solid ${i === 0 ? C.red : "transparent"}`, boxShadow: i === 0 ? `0 0 0 2px rgba(204,31,31,0.2)` : "none" }} />
                    <div style={{ flex:1, minWidth:0 }}>
                      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:6, alignItems: "center" }}>
                        <span style={{ fontFamily:"'Syne',sans-serif", fontSize:14, fontWeight:700, color:C.ink, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{c.login}</span>
                        <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.red, fontWeight: 600 }}>{fmt(c.contributions)}</span>
                      </div>
                      <div style={{ height:4, background:"rgba(255,255,255,0.8)", borderRadius:99, overflow:"hidden" }}>
                        <div style={{ height:"100%", width:`${pct}%`, background: i === 0 ? `linear-gradient(90deg, ${C.red}, #f87171)` : `linear-gradient(90deg, ${C.navy}, #93c5fd)`, borderRadius:99 }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Key Directories (Col 4) */}
          {architecture.key_directories.length > 0 && (
            <Card className="col-span-4" delay="0.4s">
              <SectionHead icon="⌂" label="Structure Map" />
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                {architecture.key_directories.map(d => (
                  <div key={d} style={{ display:"flex", alignItems:"center", gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:13, color:C.ink, background:"rgba(255,255,255,0.4)", border:"1px solid rgba(255,255,255,0.6)", borderRadius:12, padding:"10px 16px", transition: "transform 0.2s" }} className="contrib-row">
                    <span style={{ color:C.red, fontSize:14 }}>📁</span>
                    {d}
                  </div>
                ))}
              </div>
            </Card>
          )}

        </div>
        {/* ── BENTO GRID END ─────────────────────────────────────────────── */}

        {/* ── FOOTER ───────────────────────────────────────────────────── */}
        <div style={{ marginTop:"3rem", textAlign:"center", fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.navy, opacity: 0.6, letterSpacing:"0.08em", textTransform: "uppercase" }}>
          GitFit Intelligence · {fmtDate(analyzed_at)}
        </div>
      </div>
    </div>
  );
}