import React from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';
import { BarChart2, CheckCircle, AlertCircle } from 'lucide-react';

const PerformanceRadar = ({ performance, context, pressure }) => {
  const bat = Math.min(100, parseFloat(performance) * 3.33 || 0);
  const ctx = Math.min(100, (parseFloat(context) - 1) * 50 + 50 || 50);
  const prs = Math.min(100, (parseFloat(pressure) - 1) * 50 + 50 || 50);
  const overall = ((bat + ctx + prs) / 3).toFixed(0);

  const data = [
    { subject: 'Batting', A: bat.toFixed(0) },
    { subject: 'Context', A: ctx.toFixed(0) },
    { subject: 'Pressure', A: prs.toFixed(0) },
    { subject: 'Bowling', A: Math.min(100, performance * 2 || 0).toFixed(0) },
    { subject: 'Overall', A: overall },
  ];

  const isElite = overall >= 70;

  return (
    <div className="glass-panel animate-fade-in delay-300" style={{ padding: '30px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <h3 className="section-header" style={{ marginBottom: 0 }}>
          <BarChart2 size={22} style={{ color: 'var(--primary)' }} />
          Attribute Radar
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.78rem', color: isElite ? 'var(--accent-green)' : 'var(--text-muted)', fontWeight: 700 }}>
          {isElite ? <CheckCircle size={13} /> : <AlertCircle size={13} />}
          {isElite ? 'Elite Profile' : 'Developing Profile'}
        </div>
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '15px' }}>Multi-dimensional impact profile</p>

      <div style={{ flex: 1, minHeight: '220px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
            <PolarGrid stroke="rgba(255,255,255,0.08)" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 11, fontWeight: 600 }} />
            <Tooltip
              contentStyle={{ backgroundColor: 'rgba(17, 24, 39, 0.95)', borderColor: 'var(--primary)', color: 'white', borderRadius: '8px' }}
              formatter={(value) => [Number(value).toFixed(0), 'Score']}
            />
            <Radar name="Player" dataKey="A" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.2} strokeWidth={2} dot={{ r: 4, fill: 'var(--primary)' }} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Attributes legend */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginTop: '5px' }}>
        {data.map(({ subject, A }) => (
          <div key={subject} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '0.78rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>{subject}</span>
            <span style={{ fontWeight: 800, color: A >= 70 ? 'var(--accent-green)' : 'var(--text-main)' }}>{A}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PerformanceRadar;
