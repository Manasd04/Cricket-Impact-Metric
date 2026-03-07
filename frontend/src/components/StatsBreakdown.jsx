import React from 'react';
import { Target, Zap, Shield, TrendingUp } from 'lucide-react';

const StatsBreakdown = ({ battingImpact, bowlingImpact, context, pressure }) => {
  // ML clipping ranges:
  //   Performance max ~10, Context: 0.9–1.5, Situation: 1.0–1.5
  // We approximate Batting & Bowling impact max to 2.5 for visualization 
  const contextPct = Math.max(0, Math.min(100, (((parseFloat(context) - 0.9) / (1.5 - 0.9)) * 100)));
  const pressurePct = Math.max(0, Math.min(100, (((parseFloat(pressure) - 1.0) / (1.5 - 1.0)) * 100)));
  const batPct = Math.max(0, Math.min(100, ((parseFloat(battingImpact) / 2.5) * 100)));
  const bowlPct = Math.max(0, Math.min(100, ((parseFloat(bowlingImpact) / 2.5) * 100)));

  const stats = [
    {
      icon: <Shield color="#0ea5e9" size={22} />,
      label: 'Batting Impact',
      desc: 'Batting contribution adjusted for match context',
      value: parseFloat(battingImpact),
      barPct: batPct,
      color: '14, 165, 233', // cyan/blue
    },
    {
      icon: <Shield color="#8b5cf6" size={22} />,
      label: 'Bowling Impact',
      desc: 'Bowling contribution adjusted for match context',
      value: parseFloat(bowlingImpact),
      barPct: bowlPct,
      color: '139, 92, 246', // violet/purple
    },
    {
      icon: <Target color="#10b981" size={22} />,
      label: 'Context Multiplier',
      desc: 'Match difficulty and opposition strength modifier',
      value: parseFloat(context),
      barPct: contextPct,
      color: '16, 185, 129',
    },
    {
      icon: <Zap color="#f59e0b" size={22} />,
      label: 'Pressure Factor',
      desc: 'High-pressure match multiplier (1.0–1.5)',
      value: parseFloat(pressure),
      barPct: pressurePct,
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
        {stats.map(({ icon, label, desc, value, barPct, color }) => {
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