import React from 'react';
import type { LanguageBreakdown } from '../types';

const LANG_COLORS: Record<string, string> = {
  TypeScript: "#3178c6", JavaScript: "#f7df1e", Python: "#3572A5",
  Java: "#b07219", "C++": "#f34b7d", Rust: "#dea584", Go: "#00ADD8",
  Ruby: "#701516", CSS: "#563d7c", HTML: "#e34c26", Other: "#8b9ab5",
};

export default function TechStackChart({ languages }: { languages: LanguageBreakdown[] }) {
  if (!languages || languages.length === 0) return null;
  return (
    <div style={{ marginTop: '1.5rem', width: '100%' }}>
      <div style={{ display: 'flex', height: 16, borderRadius: 8, overflow: 'hidden', marginBottom: '1.25rem', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)' }}>
        {languages.map((l) => (
          <div 
            key={l.language} 
            style={{ width: `${l.percentage}%`, background: LANG_COLORS[l.language] || "#5a8fd8", transition: "width 1s cubic-bezier(.22,.68,0,1.2)" }} 
            title={`${l.language}: ${l.percentage.toFixed(1)}%`} 
          />
        ))}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem' }}>
        {languages.map((l) => (
           <div key={l.language} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
             <span style={{ width: 10, height: 10, borderRadius: '50%', background: LANG_COLORS[l.language] || "#5a8fd8", boxShadow: `0 0 8px ${LANG_COLORS[l.language] || "#5a8fd8"}80` }} />
             <span style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, color: "#0a1128", fontWeight: 700 }}>{l.language}</span>
             <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "#4a5568", fontWeight: 600 }}>{l.percentage.toFixed(1)}%</span>
           </div>
        ))}
      </div>
    </div>
  );
}
