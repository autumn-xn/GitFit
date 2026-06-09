import React from 'react';
import type { WeeklyActivity } from '../types';

export default function ActivityGraph({ activity }: { activity: WeeklyActivity[] }) {
  if (!activity || activity.length === 0) return null;
  
  const maxCommits = Math.max(...activity.map(a => a.commits), 1);
  
  return (
    <div style={{ marginTop: '1.5rem', width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 80 }}>
        {activity.map((w, i) => {
          const heightPct = (w.commits / maxCommits) * 100;
          return (
            <div 
              key={w.week} 
              style={{ 
                flex: 1, 
                display: 'flex', 
                flexDirection: 'column', 
                justifyContent: 'flex-end', 
                height: '100%',
                cursor: 'pointer'
              }}
              title={`Week of ${new Date(w.week).toLocaleDateString()}: ${w.commits} commits`}
            >
              <div 
                style={{ 
                  width: '100%', 
                  height: `${Math.max(heightPct, 4)}%`, 
                  background: w.commits > 0 ? 'linear-gradient(180deg, #5a8fd8 0%, #1a3a8f 100%)' : 'rgba(26,58,143,0.05)', 
                  borderRadius: '4px 4px 0 0',
                  transition: 'height 0.8s cubic-bezier(.22,.68,0,1.2)',
                  opacity: w.commits > 0 ? 0.85 : 1
                }}
                onMouseOver={(e) => { if(w.commits > 0) e.currentTarget.style.opacity = '1'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                onMouseOut={(e) => { if(w.commits > 0) e.currentTarget.style.opacity = '0.85'; e.currentTarget.style.transform = 'translateY(0)' }}
              />
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: '#4a5568' }}>
        <span>1 Year Ago</span>
        <span>Today</span>
      </div>
    </div>
  );
}
