import React from 'react';

export default function ArchDiagram({ patterns, dirs }: { patterns: string[], dirs: string[] }) {
  // A sleek conceptual representation of architecture flow
  const isFrontend = dirs.some(d => d.includes('src') || d.includes('components') || d.includes('pages'));
  const isBackend = dirs.some(d => d.includes('api') || d.includes('backend') || d.includes('server'));
  
  return (
    <div style={{ 
      padding: '1.5rem', 
      background: 'rgba(255,255,255,0.4)', 
      borderRadius: 16, 
      border: '1px solid rgba(255,255,255,0.3)', 
      marginTop: '1.5rem', 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center',
      gap: '1.5rem'
    }}>
       {isFrontend && (
         <div style={{ padding: '12px 24px', background: '#0a1128', color: '#fff', borderRadius: 12, fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, boxShadow: '0 10px 20px rgba(10,17,40,0.2)' }}>
           Client
         </div>
       )}
       {isFrontend && isBackend && (
         <div style={{ fontSize: 24, color: '#cc1f1f', animation: 'pulse 2s infinite' }}>⇄</div>
       )}
       {isBackend && (
         <div style={{ padding: '12px 24px', background: '#1a3a8f', color: '#fff', borderRadius: 12, fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, boxShadow: '0 10px 20px rgba(26,58,143,0.2)' }}>
           Server
         </div>
       )}
       {!isFrontend && !isBackend && (
         <div style={{ padding: '12px 24px', background: 'rgba(74,85,104,0.1)', color: '#4a5568', borderRadius: 12, fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, border: '1px dashed rgba(74,85,104,0.3)' }}>
           {patterns[0] || 'Standard Layout'}
         </div>
       )}
    </div>
  );
}
