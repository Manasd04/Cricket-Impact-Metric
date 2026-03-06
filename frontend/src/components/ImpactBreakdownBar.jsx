import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList } from 'recharts';
import { Layers } from 'lucide-react';

const ImpactBreakdownBar = ({ inningsData }) => {
  if (!inningsData || inningsData.length === 0) return null;

  // Use last 10 innings. Field names from ML API:
  //   perf_bat  → batting performance (0–30ish)
  //   Context   → match context multiplier (1.0–2.0) → scale ×30 to visualize
  //   Situation → pressure multiplier (1.0–2.0) → scale ×30
  //   Impact_Score → final overall (0–100)
  const data = inningsData.slice(-10).map((item, i) => ({
    name: `I${i + 1}`,
    Batting:  parseFloat((parseFloat(item.perf_bat || item.Bat_Performance || 0) * 3).toFixed(1)),
    Context:  parseFloat(((parseFloat(item.Context || item.Context_Score || 1) - 1) * 60).toFixed(1)),
    Pressure: parseFloat(((parseFloat(item.Situation || item.Situation_Score || 1) - 1) * 60).toFixed(1)),
    Impact:   parseFloat(parseFloat(item.Impact_Score || 0).toFixed(1)),
  }));

  return (
    <div className="glass-panel animate-fade-in delay-400" style={{ padding: '30px' }}>
      <h3 className="section-header">
        <Layers size={22} style={{ color: 'var(--accent-green)' }} />
        Innings Breakdown
      </h3>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px' }}>Batting, Context, and Pressure score per innings</p>

      <div style={{ height: '250px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barGap={2}>
            <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} stroke="transparent" />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} stroke="transparent" />
            <Tooltip
              contentStyle={{ backgroundColor: 'rgba(17, 24, 39, 0.95)', borderColor: 'var(--border)', color: 'white', borderRadius: '8px' }}
            />
            <Bar dataKey="Batting" fill="#38bdf8" radius={[4, 4, 0, 0]} name="Batting (normalized)" />
            <Bar dataKey="Context" fill="#10b981" radius={[4, 4, 0, 0]} name="Context Boost" />
            <Bar dataKey="Pressure" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Pressure Boost" />
            <Bar dataKey="Impact" fill="#a78bfa" radius={[4, 4, 0, 0]} name="Impact Score" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: 'flex', gap: '20px', marginTop: '15px', justifyContent: 'center', flexWrap: 'wrap' }}>
        {[['#38bdf8', 'Batting'], ['#10b981', 'Context'], ['#f59e0b', 'Pressure'], ['#a78bfa', 'Impact']].map(([color, label]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: color }}></div>
            {label}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ImpactBreakdownBar;
