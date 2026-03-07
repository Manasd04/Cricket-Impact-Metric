import React from 'react';
import GaugeChart from 'react-gauge-chart';
import { Activity, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';

const ImpactMeter = ({ score, previousScore }) => {
  const numScore = parseFloat(score) || 0;
  const normalizedScore = Math.max(0, Math.min(100, numScore)) / 100;

  // Classify tier
  const getTier = (s) => {
    if (s >= 85) return { label: 'ELITE', color: '#fbbf24' };
    if (s >= 70) return { label: 'HIGH IMPACT', color: '#10b981' };
    if (s >= 50) return { label: 'AVERAGE', color: '#38bdf8' };
    return { label: 'LOW FORM', color: '#f87171' };
  };

  const tier = getTier(numScore);

  // Compute trend
  const prev = parseFloat(previousScore);
  const hasTrend = !isNaN(prev) && previousScore !== undefined;
  const diff = hasTrend ? (numScore - prev).toFixed(1) : null;
  const TrendIcon = diff > 0 ? TrendingUp : diff < 0 ? TrendingDown : Minus;
  const trendColor = diff > 0 ? 'var(--accent-green)' : diff < 0 ? 'var(--accent-red)' : 'var(--text-muted)';

  const tooltipText = "Impact Score Formula\n\nImpact =\n((Batting Performance × Batting Context)\n+\n(Bowling Performance × Bowling Context))\n× Pressure Factor\n\nThe result is then normalized to a 0–100 scale using logistic scaling.";

  return (
    <div className="glass-panel animate-fade-in delay-200" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '30px', height: '100%' }}>
      <div style={{ alignSelf: 'stretch', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 className="section-header" style={{ marginBottom: 0 }}>
            <Activity size={22} style={{ color: 'var(--primary)' }} />
            Impact Score
          </h3>
          <div title={tooltipText} style={{ cursor: 'help', color: 'var(--text-muted)' }}>
            <Info size={16} />
          </div>
        </div>
        {/* Tier Badge */}
        <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 800, letterSpacing: '1px', background: `rgba(${tier.color === '#fbbf24' ? '251,191,36' : tier.color === '#10b981' ? '16,185,129' : tier.color === '#38bdf8' ? '56,189,248' : '248,113,113'}, 0.15)`, color: tier.color, border: `1px solid ${tier.color}` }}>
          {tier.label}
        </span>
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '10px', alignSelf: 'flex-start' }}>Kinetic Form (Rolling Impact)</p>

      <div style={{ width: '100%', maxWidth: '380px', marginTop: 'auto', marginBottom: 'auto' }}>
        <GaugeChart
          id="impact-gauge"
          nrOfLevels={30}
          colors={['#ef4444', '#f59e0b', '#10b981', '#3b82f6']}
          arcWidth={0.22}
          percent={normalizedScore}
          textColor="var(--text-main)"
          needleColor="#64748b"
          needleBaseColor="var(--text-main)"
          formatTextValue={() => numScore.toFixed(1)}
        />
      </div>

      {/* Trend Indicator */}
      {hasTrend && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '-10px', color: trendColor, fontWeight: 700, fontSize: '0.9rem' }}>
          <TrendIcon size={16} />
          <span>{diff > 0 ? '+' : ''}{diff} vs last reading</span>
        </div>
      )}
    </div>
  );
};

export default ImpactMeter;
