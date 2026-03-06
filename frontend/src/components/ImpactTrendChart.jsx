import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Area, AreaChart } from 'recharts';
import { TrendingUp, Activity } from 'lucide-react';

const CustomDot = (props) => {
  const { cx, cy, value } = props;
  const color = value >= 85 ? '#fbbf24' : value >= 70 ? '#10b981' : value >= 50 ? '#38bdf8' : '#f87171';
  return <circle cx={cx} cy={cy} r={6} fill={color} stroke="var(--bg-surface)" strokeWidth={2} />;
};

const ImpactTrendChart = ({ data, window = 'Last 10' }) => {
  const [chartType, setChartType] = useState('line');
  if (!data || data.length === 0) return null;

  const avg = data.reduce((s, d) => s + parseFloat(d.Impact_Score || 0), 0) / data.length;
  // Use numbered indices (e.g. "I1", "I2") as requested by the user
  const formattedData = data.map((d, i) => {
    return { ...d, axisLabel: `I${i + 1}` };
  });

  const ChartComponent = chartType === 'area' ? AreaChart : LineChart;

  return (
    <div className="glass-panel animate-fade-in delay-400" style={{ padding: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h3 className="section-header" style={{ marginBottom: 0 }}>
          <TrendingUp size={22} style={{ color: 'var(--primary)' }} />
          Impact Trend ({window === 'All Time' ? 'All Innings' : window + ' Innings'})
        </h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['line', 'area'].map(type => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              style={{
                padding: '5px 14px', borderRadius: '6px', border: '1px solid',
                borderColor: chartType === type ? 'var(--primary)' : 'var(--border)',
                background: chartType === type ? 'rgba(56,189,248,0.15)' : 'transparent',
                color: chartType === type ? 'var(--primary)' : 'var(--text-muted)',
                cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, textTransform: 'capitalize',
              }}
            >{type}</button>
          ))}
        </div>
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
        Avg across window: <strong style={{ color: 'var(--text-main)' }}>{avg.toFixed(1)}</strong>
      </p>

      <div style={{ height: '300px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ChartComponent data={formattedData} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
            <defs>
              <linearGradient id="impactGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="axisLabel" 
              tick={{ fill: 'var(--text-muted)', fontSize: 10 }} 
              stroke="var(--border)" 
              angle={-45} 
              textAnchor="end"
              height={60}
            />
            <YAxis domain={[0, 100]} stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
            {/* Average reference line */}
            <ReferenceLine y={avg} stroke="rgba(251,191,36,0.5)" strokeDasharray="6 3" label={{ value: `Avg ${avg.toFixed(0)}`, fill: '#fbbf24', fontSize: 11, position: 'right' }} />
            {/* Elite threshold */}
            <ReferenceLine y={85} stroke="rgba(16,185,129,0.3)" strokeDasharray="4 4" label={{ value: 'Elite', fill: '#10b981', fontSize: 10, position: 'right' }} />
            <Tooltip
              contentStyle={{ backgroundColor: 'rgba(17, 24, 39, 0.97)', borderColor: 'var(--primary)', color: 'white', borderRadius: '10px', backdropFilter: 'blur(8px)' }}
              itemStyle={{ color: 'var(--primary)' }}
              labelStyle={{ color: 'var(--text-muted)' }}
              formatter={(value) => [Number(value).toFixed(1), 'Impact Score']}
            />
            {chartType === 'area' ? (
              <Area type="monotone" dataKey="Impact_Score" stroke="var(--primary)" strokeWidth={3} fill="url(#impactGradient)" dot={<CustomDot />} activeDot={{ r: 8 }} />
            ) : (
              <Line type="monotone" dataKey="Impact_Score" stroke="var(--primary)" strokeWidth={3} dot={<CustomDot />} activeDot={{ r: 8, fill: 'var(--primary)', stroke: 'white', strokeWidth: 2 }} />
            )}
          </ChartComponent>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ImpactTrendChart;
