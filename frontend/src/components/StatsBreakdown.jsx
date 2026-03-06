import React from 'react';
import { Target, Zap, Shield, TrendingUp } from 'lucide-react';

const StatsBreakdown = ({ performance, context, pressure }) => {
  const stats = [
    {
      icon: <Shield color="#38bdf8" size={22} />,
      label: 'Performance Impact',
      desc: 'Batting & Bowling output',
      value: parseFloat(performance),
      max: 30,
      color: '56, 189, 248',
    },
    {
      icon: <Target color="#10b981" size={22} />,
      label: 'Match Context',
      desc: 'Situation & phase modifier',
      value: parseFloat(context),
      max: 3,
      color: '16, 185, 129',
    },
    {
      icon: <Zap color="#f59e0b" size={22} />,
      label: 'Pressure Factor',
      desc: 'Under-fire multiplier',
      value: parseFloat(pressure),
      max: 3,
      color: '245, 158, 11',
    },
  ];

  return (
    <div className="glass-panel animate-fade-in delay-300" style={{ padding: '30px' }}>
      <h3 className="section-header" style={{ marginBottom: '8px' }}>
        <TrendingUp size={22} style={{ color: 'var(--primary)' }} />
        Impact Breakdown
      </h3>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '25px' }}>
        Contributions to the final IM score
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {stats.map(({ icon, label, desc, value, max, color }) => {
          const barPct = Math.min(100, ((value / max) * 100)).toFixed(0);
          const displayValue = isNaN(value) ? '—' : value.toFixed(2);
          return (
            <div key={label}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: `rgba(${color}, 0.1)`, display: 'flex', alignItems: 'center', justifyContent: 'center', border: `1px solid rgba(${color}, 0.25)` }}>
                    {icon}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>{label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{desc}</div>
                  </div>
                </div>
                <span style={{ fontWeight: 900, fontSize: '1.3rem', color: `rgba(${color}, 1)` }}>{displayValue}</span>
              </div>
              {/* Progress bar */}
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.07)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${barPct}%`, background: `rgba(${color}, 0.8)`, borderRadius: '3px', transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)' }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StatsBreakdown;
