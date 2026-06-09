import React from 'react';

export default function RepoImage({ owner, name }: { owner: string; name: string }) {
  const ogUrl = `https://opengraph.githubassets.com/1/${owner}/${name}`;
  
  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      borderRadius: 16, 
      overflow: 'hidden', 
      position: 'relative',
      boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
      border: '1px solid rgba(255,255,255,0.1)'
    }}>
      <img 
        src={ogUrl} 
        alt={`${owner}/${name} repository`} 
        style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
        onError={(e) => {
          // Fallback to a gradient if image fails
          e.currentTarget.style.display = 'none';
          if (e.currentTarget.parentElement) {
            e.currentTarget.parentElement.style.background = 'linear-gradient(135deg, #1a3a8f, #cc1f1f)';
          }
        }}
      />
    </div>
  );
}
