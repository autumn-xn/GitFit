// ─── frontend/src/pages/Results.tsx ──────────────────────────────────────────
// Enterprise Data Intelligence Dashboard
// Palette: Deep navy (#1a3a8f), bold red (#cc1f1f), sky blue (#5a8fd8).
// Features: Advanced glassmorphism, gradient borders, contextual reference links.

import { useLocation, useNavigate } from "react-router-dom";
import type { AnalysisResult } from "../types";

import ActivityGraph from "../components/ActivityGraph";
import TechStackChart from "../components/TechStackChart";
import ArchDiagram from "../components/ArchDiagram";
import RepoImage from "../components/RepoImage";

// ─── Keyframes & Global CSS ───────────────────────────────────────────────────
function injectKF() {
  if (document.getElementById("results-kf")) return;
  const s = document.createElement("style");
  s.id = "results-kf";
  s.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600;700;800&display=swap');

    @keyframes fadeUp   { from { opacity:0; transform:translateY(30px); } to { opacity:1; transform:translateY(0); } }
    @keyframes barGrow  { from { width:0%; } to { width:var(--w); } }
    @keyframes ringFill { from { stroke-dashoffset: 283; } to { stroke-dashoffset: var(--offset); } }
    @keyframes pulse    { 0%,100%{opacity:1; transform:scale(1);} 50%{opacity:.5; transform:scale(1.1);} }
    @keyframes float    { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
    @keyframes slideBg  { 0% { background-position: 0% 50%; } 100% { background-position: 200% 50%; } }

    .bento-grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .col-span-12 { grid-column: span 12; }
    .col-span-8  { grid-column: span 8; }
    .col-span-6  { grid-column: span 6; }
    .col-span-4  { grid-column: span 4; }

    @media (max-width: 1024px) { .col-span-4 { grid-column: span 6; } }
    @media (max-width: 768px) { .col-span-4, .col-span-6, .col-span-8 { grid-column: span 12; } }

    /* Advanced Glowing Border Card */
    .res-card { 
      position: relative;
      background: rgba(255, 255, 255, 0.55);
      backdrop-filter: blur(40px) saturate(1.8);
      -webkit-backdrop-filter: blur(40px) saturate(1.8);
      border-radius: 20px;
      padding: 2rem;
      display: flex;
      flex-direction: column;
      transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
      box-shadow: 0 10px 30px rgba(26,58,143,0.05);
    }
    
    /* Gradient Border Masking */
    .res-card::before {
      content: ""; position: absolute; inset: 0; border-radius: 20px;
      padding: 1px; /* border width */
      background: linear-gradient(135deg, rgba(204,31,31,0.4), rgba(255,255,255,0.8), rgba(90,143,216,0.4));
      -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
      -webkit-mask-composite: xor;
      mask-composite: exclude;
      pointer-events: none;
    }

    .res-card:hover { 
      transform: translateY(-5px);
      box-shadow: 0 20px 40px rgba(204,31,31,0.12), 0 8px 16px rgba(26,58,143,0.08);
    }

    .lang-bar-fill { animation: barGrow 1s cubic-bezier(.22,.68,0,1.2) both; }
    .score-ring circle:last-child { animation: ringFill 1.5s cubic-bezier(.22,.68,0,1.2) 0.2s both; }

    /* Custom Hyperlink styling */
    .ref-link {
      display: inline-flex; align-items: center; gap: 8px;
      font-family: 'Syne', sans-serif; font-weight: 700; font-size: 13px;
      color: #cc1f1f; text-decoration: none; position: relative;
      transition: all 0.2s;
    }
    .ref-link .arrow { transition: transform 0.2s; }
    .ref-link:hover .arrow { transform: translateX(4px); }
    .ref-link::after {
      content: ''; position: absolute; bottom: -2px; left: 0; width: 0%; height: 1.5px;
      background: #cc1f1f; transition: width 0.3s cubic-bezier(.22,.68,0,1.2);
    }
    .ref-link:hover::after { width: 100%; }

    .tag-chip:hover { background: rgba(204,31,31,0.9) !important; color: #fff !important; transform: translateY(-2px); }
  `;
  document.head.appendChild(s);
}

// ─── Color palette ────────────────────────────────────────────────────────────
const C = {
  navy:  "#1a3a8f", red:   "#cc1f1f", sky:   "#5a8fd8",
  ink:   "#0a1128", slate: "#4a5568", mist:  "#f0f4f8", white: "#ffffff"
};

const LANG_COLORS: Record<string, string> = {
  TypeScript: "#3178c6", JavaScript: "#f7df1e", Python: "#3572A5",
  Java: "#b07219", "C++": "#f34b7d", Rust: "#dea584", Go: "#00ADD8",
  Ruby: "#701516", CSS: "#563d7c", HTML: "#e34c26", Other: "#8b9ab5",
};
function langColor(lang: string) { return LANG_COLORS[lang] ?? C.sky; }

function fmt(n: number) { return n >= 1_000_000 ? `${(n/1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n/1_000).toFixed(1)}k` : String(n); }
function fmtDate(iso: string) { return new Date(iso).toLocaleDateString("en-US", { year:"numeric", month:"short", day:"numeric" }); }

// ─── Components ───────────────────────────────────────────────────────────────
function Card({ children, className = "", delay = "0s" }: { children: React.ReactNode; className?: string; delay?: string }) {
  return (
    <div className={`res-card ${className}`} style={{ animation: `fadeUp 0.7s cubic-bezier(0.165, 0.84, 0.44, 1) ${delay} both` }}>
      {children}
    </div>
  );
}

function SectionHead({ icon, label }: { icon: string; label: string }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:"1.5rem" }}>
      <div style={{ 
        width: 36, height: 36, borderRadius: 12, background: `linear-gradient(135deg, ${C.red}, #f87171)`, 
        display:"flex", alignItems:"center", justifyContent:"center", color: "#fff",
        fontFamily:"'JetBrains Mono',monospace", fontSize:16, boxShadow: `0 4px 12px ${C.red}40`
      }}>
        {icon}
      </div>
      <span style={{ fontFamily:"'Syne',sans-serif", fontSize:15, fontWeight:800, color: C.ink, letterSpacing:"0.06em", textTransform:"uppercase" }}>{label}</span>
      <div style={{ flex:1, height:"1px", background:`linear-gradient(90deg, rgba(204,31,31,0.2), transparent)` }} />
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const r = 58; const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 85 ? "#10b981" : score >= 60 ? C.sky : C.red;

  return (
    <div style={{ position:"relative", width:150, height:150, animation: "float 6s ease-in-out infinite" }}>
      <svg width="150" height="150" viewBox="0 0 150 150" className="score-ring" style={{ transform:"rotate(-90deg)", filter: `drop-shadow(0 0 16px ${color}60)` }}>
        <circle cx="75" cy="75" r={r} fill="rgba(0,0,0,0.2)" strokeWidth="10" stroke="rgba(255,255,255,0.05)" />
        <circle cx="75" cy="75" r={r} fill="none" strokeWidth="10" stroke={color} strokeLinecap="round" strokeDasharray={circ} style={{ "--offset": offset } as React.CSSProperties} strokeDashoffset={offset} />
      </svg>
      <div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center" }}>
        <span style={{ fontFamily:"'Syne',sans-serif", fontSize:42, fontWeight:800, color:"#fff", lineHeight:1, textShadow: "0 2px 10px rgba(0,0,0,0.5)" }}>{score}</span>
        <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, color:"rgba(255,255,255,0.8)", letterSpacing:"0.15em", marginTop:4 }}>RATING</span>
      </div>
    </div>
  );
}

function RefLink({ href, text }: { href: string; text: string }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="ref-link">
      {text} <span className="arrow">↗</span>
    </a>
  );
}

// Full width strip linking out to resources
function ReferenceStrip({ href, title, description, delay = "0s" }: { href: string; title: string; description: string; delay?: string }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" style={{
      textDecoration: "none", display: "block", marginBottom: "2rem",
      animation: `fadeUp 0.7s cubic-bezier(0.165, 0.84, 0.44, 1) ${delay} both`
    }}>
      <div style={{
        background: `linear-gradient(90deg, rgba(26,58,143,0.05) 0%, rgba(204,31,31,0.05) 100%)`,
        border: "1px solid rgba(26,58,143,0.1)", borderRadius: 16, padding: "1.25rem 2rem",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        transition: "all 0.3s cubic-bezier(.25,.8,.25,1)",
      }} className="hover:bg-white hover:shadow-lg"
         onMouseEnter={(e) => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.boxShadow = `0 10px 30px rgba(204,31,31,0.08)`; e.currentTarget.style.transform = 'translateY(-2px)'; }}
         onMouseLeave={(e) => { e.currentTarget.style.background = `linear-gradient(90deg, rgba(26,58,143,0.05) 0%, rgba(204,31,31,0.05) 100%)`; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none'; }}>
        
        <div>
          <h4 style={{ margin: 0, fontFamily: "'Syne', sans-serif", fontSize: 16, fontWeight: 700, color: C.ink }}>{title}</h4>
          <p style={{ margin: "4px 0 0 0", fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: C.slate }}>{description}</p>
        </div>
        <div style={{ width: 40, height: 40, borderRadius: 20, background: "rgba(204,31,31,0.1)", display: "flex", alignItems: "center", justifyContent: "center", color: C.red, fontSize: 20 }}>
          →
        </div>
      </div>
    </a>
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

  return (
    <div style={{ fontFamily:"'Syne','Segoe UI',sans-serif", minHeight:"100vh", background: C.mist, paddingBottom:"4rem", position: "relative", overflowX: "hidden" }}>
      
      {/* ── BACKGROUND GEOMETRY ────────────────────── */}
      <div style={{ position:"fixed", inset:0, zIndex:0, pointerEvents:"none", backgroundImage: "radial-gradient(circle, rgba(26,58,143,0.12) 1.5px, transparent 1.5px)", backgroundSize: "28px 28px" }} />
      <svg style={{ position:"fixed", inset:0, width:"100%", height:"100%", zIndex:0, pointerEvents:"none", opacity: 0.8 }} viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">
        <polygon points="-100,-100 850,-100 350,350 -100,200" fill={C.red} opacity="0.9" />
        <polygon points="-100,-100 650,-100 250,450 -100,300" fill={C.navy} opacity="0.8" />
        <polygon points="1540,1000 550,1000 1050,550 1540,650" fill={C.red} opacity="0.8" />
        <polygon points="1540,1000 750,1000 1150,450 1540,550" fill={C.navy} opacity="0.85" />
      </svg>

      {/* ── HEADER ─────────────────────────────────────────────────── */}
      <header style={{
        position:"sticky", top:0, zIndex:100, background:"rgba(255,255,255,0.75)",
        backdropFilter:"blur(24px)", borderBottom:"1px solid rgba(204,31,31,0.15)",
        display:"flex", alignItems:"center", justifyContent:"space-between", padding:"0 2rem", height:70,
        boxShadow: "0 4px 20px rgba(0,0,0,0.02)"
      }}>
        <div style={{ display:"flex", alignItems:"center", gap:16 }}>
          <div style={{ width:36, height:36, borderRadius:10, background:C.red, display:"flex", alignItems:"center", justifyContent:"center", boxShadow: `0 4px 14px ${C.red}50` }}>
            <span style={{ color:"#fff", fontSize:18, fontFamily:"'JetBrains Mono',monospace" }}>⌥</span>
          </div>
          <span style={{ fontFamily:"'Syne',sans-serif", fontWeight:800, fontSize:20, color:C.ink, letterSpacing: "-0.5px" }}>GitFit</span>
        </div>
        <button onClick={() => navigate("/")} style={{
          display:"flex", alignItems:"center", gap:8, padding:"10px 20px", fontFamily:"'Syne',sans-serif", fontSize:13, fontWeight:700,
          color:"#fff", background: C.ink, border:`none`, borderRadius:99, cursor:"pointer", transition:"all 0.2s",
          boxShadow: "0 4px 12px rgba(10,17,40,0.3)"
        }} onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'} onMouseOut={e => e.currentTarget.style.transform = 'none'}>
          ← New Analysis
        </button>
      </header>

      {/* ── MAIN LAYOUT ────────────────────────────────────────────────── */}
      <div style={{ position:"relative", zIndex:10, maxWidth:1320, margin:"0 auto", padding:"3rem 1.5rem" }}>
        
        {/* ── HERO SECTION ─────────────────────────────────────── */}
        <div className="bento-grid">
          <div className="col-span-12" style={{
            background:`linear-gradient(135deg, rgba(10,17,40,0.92) 0%, rgba(26,58,143,0.9) 100%)`,
            backdropFilter: "blur(20px)", borderRadius: 32, padding:"3.5rem", position:"relative", overflow:"hidden",
            boxShadow:"0 30px 60px rgba(26,58,143,0.25), inset 0 1px 0 rgba(255,255,255,0.15)",
            animation:"fadeUp 0.6s cubic-bezier(0.165, 0.84, 0.44, 1) both",
          }}>
            {/* Animated background element */}
            <div style={{
              position:"absolute", top: 0, right: 0, width: "50%", height: "100%",
              background: `linear-gradient(90deg, transparent, rgba(204,31,31,0.2), transparent)`,
              backgroundSize: "200% 100%", animation: "slideBg 5s ease-in-out infinite alternate", pointerEvents: "none"
            }} />

            <div style={{ position:"relative", zIndex:2, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "3rem" }}>
              <div style={{ flex: "1 1 500px" }}>
                <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:20 }}>
                  <span style={{ background:"rgba(255,255,255,0.1)", backdropFilter: "blur(10px)", border: "1px solid rgba(255,255,255,0.2)", borderRadius:8, padding:"6px 14px", fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:"#fff", letterSpacing:"0.05em" }}>github.com</span>
                  <div style={{ display:"flex", alignItems:"center", gap:8, background:"rgba(16,185,129,0.15)", border:"1px solid rgba(16,185,129,0.4)", borderRadius:99, padding:"4px 14px", fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:"#34d399", fontWeight: 700 }}>
                    <span style={{ width:6, height:6, borderRadius:"50%", background:"#34d399", animation:"pulse 2s infinite" }} /> Intelligence Acquired
                  </div>
                </div>

                <h1 style={{ fontFamily:"'Syne',sans-serif", fontSize:"clamp(2.5rem, 5vw, 3.5rem)", fontWeight:800, color:"#fff", margin:0, lineHeight:1.05, letterSpacing:"-0.04em" }}>
                  {meta.owner} <span style={{ color:"rgba(255,255,255,0.3)", fontWeight: 400 }}>/</span> <span style={{ color:C.sky }}>{meta.name}</span>
                </h1>
                
                {meta.description && <p style={{ fontFamily:"'Syne',sans-serif", fontSize:17, color:"rgba(255,255,255,0.75)", margin:"1.5rem 0 0", maxWidth: 650, lineHeight:1.6 }}>{meta.description}</p>}

                {meta.topics.length > 0 && (
                  <div style={{ display:"flex", flexWrap:"wrap", gap:10, marginTop:"2rem" }}>
                    {meta.topics.map(t => (
                      <span key={t} className="tag-chip" style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:"#fff", background:"rgba(204,31,31,0.2)", border:"1px solid rgba(204,31,31,0.5)", borderRadius:99, padding:"8px 16px", cursor:"default", transition:"all 0.3s" }}>
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Data Node right block */}
              <div style={{ display: "flex", gap: "2.5rem", alignItems: "center", background: "rgba(255,255,255,0.05)", padding: "2rem", borderRadius: 28, border: "1px solid rgba(255,255,255,0.1)", backdropFilter: "blur(16px)", boxShadow: "inset 0 0 40px rgba(0,0,0,0.2)" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                  <div><div style={{color:"#fff", fontSize: 24, fontWeight: 800, fontFamily: "Syne"}}>{fmt(meta.stars)}</div><div style={{color: C.sky, fontSize: 11, fontFamily: "JetBrains Mono", fontWeight: 700}}>STARS</div></div>
                  <div><div style={{color:"#fff", fontSize: 24, fontWeight: 800, fontFamily: "Syne"}}>{fmt(meta.forks)}</div><div style={{color: C.sky, fontSize: 11, fontFamily: "JetBrains Mono", fontWeight: 700}}>FORKS</div></div>
                  <div><div style={{color:"#fff", fontSize: 24, fontWeight: 800, fontFamily: "Syne"}}>{fmt(meta.open_issues)}</div><div style={{color: C.sky, fontSize: 11, fontFamily: "JetBrains Mono", fontWeight: 700}}>ISSUES</div></div>
                  <div><div style={{color:"#fff", fontSize: 24, fontWeight: 800, fontFamily: "Syne"}}>{contributors.length}</div><div style={{color: C.sky, fontSize: 11, fontFamily: "JetBrains Mono", fontWeight: 700}}>CONTRIBS</div></div>
                </div>
                <div style={{ width: 1, height: 120, background: "linear-gradient(to bottom, transparent, rgba(255,255,255,0.2), transparent)" }} />
                <ScoreRing score={code_quality.score} />
              </div>
            </div>
          </div>
        </div>

        {/* ── BENTO ROW 1 ─────────────────────────────────────────── */}
        <div className="bento-grid">
          
          <Card className="col-span-8" delay="0.1s">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <SectionHead icon="⌁" label="Architecture & Patterns" />
              <RefLink href="https://docs.github.com/en/repositories" text="Repo Docs" />
            </div>
            
            <p style={{ fontFamily:"'Syne',sans-serif", fontSize:15, color:C.slate, lineHeight:1.7, margin:"0 0 1.5rem" }}>{architecture.summary}</p>
            
            <div style={{ display:"flex", flexWrap:"wrap", gap:10, marginBottom: "2rem" }}>
              {architecture.patterns.map(p => (
                <span key={p} style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:12, color:C.ink, background:"rgba(26,58,143,0.04)", border:"1px solid rgba(26,58,143,0.15)", borderRadius:8, padding:"8px 14px", fontWeight: 600 }}>{p}</span>
              ))}
            </div>

            <div style={{ display: "flex", gap: "1.5rem" }}>
              {architecture.key_directories.length > 0 && (
                <div style={{ flex: 1, background: "rgba(255,255,255,0.6)", padding: "1.25rem", borderRadius: 16, border: "1px solid rgba(0,0,0,0.05)" }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.slate, letterSpacing:"0.05em", textTransform:"uppercase", marginBottom:12 }}>Key Directories</div>
                  <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                    {architecture.key_directories.slice(0,3).map(d => (
                      <div key={d} style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:13, color:C.red, fontWeight: 500 }}>📂 {d}</div>
                    ))}
                  </div>
                </div>
              )}
              {architecture.entry_points.length > 0 && (
                 <div style={{ flex: 1, background: "rgba(255,255,255,0.6)", padding: "1.25rem", borderRadius: 16, border: "1px solid rgba(0,0,0,0.05)" }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.slate, letterSpacing:"0.05em", textTransform:"uppercase", marginBottom:12 }}>Entry Points</div>
                  <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                    {architecture.entry_points.map(e => (
                      <div key={e} style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:13, color:C.ink, fontWeight: 500 }}>⚡ {e}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <ArchDiagram patterns={architecture.patterns} dirs={architecture.key_directories} />
          </Card>

          <Card className="col-span-4" delay="0.15s">
            <SectionHead icon="⚿" label="Security Audit" />
            
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", background: security.exposes_secrets ? "rgba(204,31,31,0.05)" : "rgba(16,185,129,0.08)", border:`1px solid ${security.exposes_secrets ? "rgba(204,31,31,0.3)" : "rgba(16,185,129,0.3)"}`, borderRadius:16, padding:"1.25rem", marginBottom:"1.5rem" }}>
              <span style={{ fontFamily:"'Syne',sans-serif", fontSize:15, fontWeight:800, color:C.ink }}>Status</span>
              <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:14, fontWeight: 700, color: security.dependency_audit === "clean" ? "#059669" : C.red, textTransform:"uppercase" }}>{security.dependency_audit}</span>
            </div>

            <div style={{ display:"flex", flexDirection:"column", gap:12, marginBottom:"2rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: 12, borderBottom: "1px solid rgba(0,0,0,0.05)" }}>
                <span style={{ fontFamily:"'Syne',sans-serif", fontSize:14, fontWeight: 600, color:C.slate }}>Environment Protection</span>
                <span style={{ fontSize: 16 }}>{security.has_env_example ? "✅" : "⚠️"}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontFamily:"'Syne',sans-serif", fontSize:14, fontWeight: 600, color:C.slate }}>Secrets Exposure</span>
                <span style={{ fontSize: 16 }}>{!security.exposes_secrets ? "✅" : "❌"}</span>
              </div>
            </div>

            <div style={{ marginTop: "auto" }}>
               <RefLink href="https://docs.github.com/en/code-security" text="Review Security Best Practices" />
            </div>
          </Card>
        </div>

        {/* ── HYPERLINK STRIP 1 ─────────────────────────────────────────── */}
        <ReferenceStrip 
          href={`https://github.com/${meta.owner}/${meta.name}/graphs/commit-activity`}
          title="Analyze Raw Commit Activity on GitHub"
          description={`Deep dive into the timeline of ${totalCommits} commits across the repository.`}
          delay="0.2s"
        />

        {/* ── BENTO ROW 2 ─────────────────────────────────────────── */}
        <div className="bento-grid">
          
          <Card className="col-span-4" delay="0.25s">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <SectionHead icon="◎" label="Code Health" />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
              {[
                { l: "Tests", a: code_quality.has_tests }, { l: "CI/CD", a: code_quality.has_ci },
                { l: "Docs", a: code_quality.has_docs }, { l: "Linter", a: code_quality.has_linter }
              ].map(t => (
                <div key={t.l} style={{ background: t.a ? "rgba(16,185,129,0.05)" : "rgba(204,31,31,0.05)", border: `1px solid ${t.a ? "rgba(16,185,129,0.2)" : "rgba(204,31,31,0.2)"}`, borderRadius: 12, padding: "12px", textAlign: "center" }}>
                   <div style={{ fontSize: 20, marginBottom: 4 }}>{t.a ? "🛡️" : "⚠️"}</div>
                   <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600, color: t.a ? "#059669" : C.red }}>{t.l}</div>
                </div>
              ))}
            </div>
            <div style={{ flex: 1, background: "rgba(255,255,255,0.7)", borderRadius: 16, padding: "1.25rem", border: "1px solid rgba(26,58,143,0.08)" }}>
              {code_quality.notes.map((n, i) => (
                <div key={i} style={{ display:"flex", alignItems:"flex-start", gap:10, marginBottom:10 }}>
                  <span style={{ color: n.includes("No ") ? C.red : "#10b981", fontSize:16, lineHeight: 1 }}>•</span>
                  <span style={{ fontFamily:"'Syne',sans-serif", fontSize:13, color:C.slate, lineHeight:1.5 }}>{n}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card className="col-span-8" delay="0.3s">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <SectionHead icon="◈" label="Contribution Matrix" />
              <RefLink href={`https://github.com/${meta.owner}/${meta.name}/graphs/contributors`} text="View All" />
            </div>
            
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1.25rem" }}>
              {contributors.slice(0, 6).map((c, i) => {
                const maxContribs = contributors[0]?.contributions || 1;
                const pct = (c.contributions / maxContribs) * 100;
                return (
                  <div key={c.login} style={{ display:"flex", alignItems:"center", gap:16, padding:"16px", background: "rgba(255,255,255,0.8)", borderRadius:16, border: "1px solid rgba(0,0,0,0.05)", transition: "all 0.2s" }}>
                    <img src={c.avatar_url} alt={c.login} style={{ width:48, height:48, borderRadius:"50%", border:`2px solid ${i === 0 ? C.red : "transparent"}`, padding: 2 }} />
                    <div style={{ flex:1, minWidth:0 }}>
                      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8, alignItems: "center" }}>
                        <span style={{ fontFamily:"'Syne',sans-serif", fontSize:15, fontWeight:800, color:C.ink, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{c.login}</span>
                        <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:12, color: i===0 ? C.red : C.slate, fontWeight: 700 }}>{fmt(c.contributions)}</span>
                      </div>
                      <div style={{ height:6, background:"rgba(26,58,143,0.05)", borderRadius:99, overflow:"hidden" }}>
                        <div style={{ height:"100%", width:`${pct}%`, background: i === 0 ? `linear-gradient(90deg, ${C.red}, #f87171)` : `linear-gradient(90deg, ${C.navy}, #93c5fd)`, borderRadius:99 }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* ── BENTO ROW 3 ─────────────────────────────────────────── */}
        <div className="bento-grid">
          <Card className="col-span-8" delay="0.35s">
            <SectionHead icon="📈" label="Commit Activity Timeline" />
            <ActivityGraph activity={activity} />
          </Card>
          
          <Card className="col-span-4" delay="0.4s">
            <SectionHead icon="🌐" label="Technology Stack" />
            <TechStackChart languages={languages} />
          </Card>
        </div>
        
        {/* ── BENTO ROW 4 ─────────────────────────────────────────── */}
        <div className="bento-grid">
          <div className="col-span-12" style={{ height: '300px', animation: "fadeUp 0.7s cubic-bezier(0.165, 0.84, 0.44, 1) 0.45s both" }}>
             <RepoImage owner={meta.owner} name={meta.name} />
          </div>
        </div>

        {/* ── FOOTER METADATA ─────────────────────────────────────────── */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "3rem", paddingTop: "2rem", borderTop: "1px solid rgba(204,31,31,0.15)" }}>
          <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.slate, letterSpacing:"0.08em", textTransform: "uppercase" }}>
            Data acquired: {fmtDate(analyzed_at)}
          </div>
          <div style={{ display: "flex", gap: "1rem" }}>
            <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.ink, fontWeight: 600 }}>Branch: {meta.default_branch}</span>
            <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:C.ink, fontWeight: 600 }}>License: {meta.license ?? "None"}</span>
          </div>
        </div>

      </div>
    </div>
  );
}