import React from 'react';
import { User, Star, Award } from 'lucide-react';

const PlayerCard = ({ name, role, impactScore }) => {
  const numScore = parseFloat(impactScore) || 0;
  const score = isNaN(numScore) ? '--' : numScore.toFixed(1);

  const getRoleClass = (r) => {
    switch (r) {
      case 'Batter': return 'badge-batter';
      case 'Bowler': return 'badge-bowler';
      case 'Allrounder': return 'badge-allrounder';
      default: return 'badge-utility';
    }
  };

  const getFormLabel = (s) => {
    if (s >= 85) return { text: '🔥 Elite Form', color: '#fbbf24' };
    if (s >= 70) return { text: '⬆ In Form', color: '#10b981' };
    if (s >= 50) return { text: '— Average', color: '#94a3b8' };
    return { text: '⬇ Below Par', color: '#f87171' };
  };

  const getAvatarGradient = (r) => {
    switch (r) {
      case 'Batter': return 'linear-gradient(135deg, #3b82f6, #6366f1)';
      case 'Bowler': return 'linear-gradient(135deg, #10b981, #0d9488)';
      case 'Allrounder': return 'linear-gradient(135deg, #f59e0b, #ef4444)';
      default: return 'linear-gradient(135deg, #8b5cf6, #6366f1)';
    }
  };

  const formInfo = getFormLabel(numScore);

  return (
    <div className="glass-panel animate-fade-in delay-100" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '35px 30px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
      {/* Glow background */}
      <div style={{ position: 'absolute', top: '-20px', right: '-20px', width: '120px', height: '120px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(56,189,248,0.1) 0%, transparent 70%)', pointerEvents: 'none' }} />

      {/* Avatar */}
      <div style={{ width: '90px', height: '90px', borderRadius: '50%', background: getAvatarGradient(role), display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '18px', boxShadow: '0 12px 30px rgba(0,0,0,0.4)', border: '2px solid rgba(255,255,255,0.15)' }}>
        <User size={44} color="white" strokeWidth={1.5} />
      </div>

      {/* Name */}
      <h2 style={{ fontSize: name?.length > 15 ? '1.5rem' : '2rem', fontWeight: 900, margin: '0 0 8px 0', color: 'var(--text-main)', letterSpacing: '-0.5px', lineHeight: 1.1 }}>{name}</h2>

      {/* Role badge */}
      <span className={`role-badge ${getRoleClass(role)}`} style={{ fontSize: '0.85rem', padding: '5px 16px', marginBottom: '6px' }}>{role}</span>

      {/* Form label */}
      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: formInfo.color, marginBottom: '20px' }}>{formInfo.text}</span>

      {/* Score card */}
      <div style={{ width: '100%', padding: '18px', background: 'rgba(255,255,255,0.03)', borderRadius: '14px', border: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '4px', fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1.5px', fontWeight: 700 }}>
          <Award size={14} /> Rolling Form Score
        </div>
        <div style={{ fontSize: '3.2rem', fontWeight: 900, color: numScore >= 85 ? '#fbbf24' : numScore >= 70 ? '#34d399' : 'var(--primary)', lineHeight: 1 }}>{score}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-very-muted)', marginTop: '4px' }}>out of 100</div>
      </div>
    </div>
  );
};

export default PlayerCard;
