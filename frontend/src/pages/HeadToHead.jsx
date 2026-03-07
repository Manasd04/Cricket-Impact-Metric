import React, { useState, useEffect } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Swords, Cpu, Activity, ArrowLeft } from 'lucide-react';
import { getPlayersList, getPlayerImpact } from '../services/api';
import Navbar from '../components/Navbar';
import { useNavigate } from 'react-router-dom';
import PlayerCombobox from '../components/PlayerCombobox';

const HeadToHead = () => {
  const navigate = useNavigate();
  const [players, setPlayers] = useState([]);
  const [playerA, setPlayerA] = useState('');
  const [playerB, setPlayerB] = useState('');
  const [dataA, setDataA] = useState(null);
  const [dataB, setDataB] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getPlayersList()
      .then(res => {
        setPlayers(res.players);
        if (res.players.length >= 2) {
          setPlayerA(res.players[0]);
          setPlayerB(res.players[1]);
        }
      })
      .catch(err => console.error(err));
  }, []);

  const handleCompare = async () => {
    if (!playerA || !playerB || playerA === playerB) return;
    setLoading(true);
    try {
      const [resA, resB] = await Promise.all([
        getPlayerImpact(playerA),
        getPlayerImpact(playerB)
      ]);
      setDataA(resA);
      setDataB(resB);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  const getWinner = (valA, valB, metric) => {
    // If metric is economy/bowling we want lower numbers, but our "Avg Bowl Perf" maps higher = better, so higher is always better here.
    const a = parseFloat(valA) || 0;
    const b = parseFloat(valB) || 0;
    if (a > b) return { winner: playerA, color: 'var(--primary)', indicator: '◀' };
    if (b > a) return { winner: playerB, color: 'var(--accent-red)', indicator: '▶' };
    return { winner: 'Tie', color: 'var(--text-muted)', indicator: '—' };
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <div className="page-content animate-fade-in" style={{ padding: '40px 50px', flexGrow: 1, maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '30px' }}>
          <button
            onClick={() => navigate(-1)}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 18px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem', transition: 'all 0.2s ease' }}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--primary)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <ArrowLeft size={16} /> Back
          </button>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '15px', margin: 0 }}>
            <Swords size={34} style={{ color: 'var(--primary)' }} />
            Head-to-Head Combats
          </h2>
        </div>

        <div className="glass-panel animate-fade-in delay-100" style={{ marginBottom: '30px', padding: '30px', overflow: 'visible', position: 'relative', zIndex: 50 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '30px', alignItems: 'end' }}>
            <div>
              <label className="font-bold" style={{ color: 'var(--primary)', marginBottom: '8px', display: 'block' }}>Operator Alpha:</label>
              <PlayerCombobox value={playerA} onChange={setPlayerA} players={players} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', paddingBottom: '2px' }}>
              <button className="primary-btn" style={{ padding: '12px 30px', fontSize: '1.1rem', background: 'var(--bg-base)', border: '1px solid var(--border)', color: 'var(--text-main)' }} onClick={handleCompare} disabled={loading || playerA === playerB}>
                {loading ? 'SIMULATING...' : 'ENGAGE'}
              </button>
            </div>
            <div>
              <label className="font-bold" style={{ color: 'var(--accent-red)', marginBottom: '8px', display: 'block' }}>Operator Beta:</label>
              <PlayerCombobox value={playerB} onChange={setPlayerB} players={players} />
            </div>
          </div>
        </div>

        {loading && (
          <div className="loader-container">
            <div className="spinner"></div>
            <p style={{ color: 'var(--text-muted)' }}>Running simulation matrices...</p>
          </div>
        )}

        {!loading && dataA && dataB && !dataA.error && !dataB.error && (
          <>
            <h3 className="section-header animate-fade-in delay-200">
              <Cpu size={22} style={{ color: 'var(--accent-gold)' }} />
              Simulation Highlights
            </h3>
            <div className="glass-panel animate-fade-in delay-300" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="data-table text-center" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'rgba(0,0,0,0.3)' }}>
                    <th style={{ textAlign: 'left', paddingLeft: '30px', color: 'var(--text-very-muted)' }}>Telemetry Metric</th>
                    <th style={{ color: 'var(--primary)', fontSize: '1.2rem', padding: '20px' }}>{playerA}</th>
                    <th style={{ color: 'var(--accent-red)', fontSize: '1.2rem', padding: '20px' }}>{playerB}</th>
                    <th style={{ color: 'var(--text-very-muted)' }}>Advantage</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: 'Role Class', k: 'role' },
                    { label: 'Average Matrix Impact', k: 'Avg Impact' },
                    { label: 'Peak Singular Impact', k: 'Peak Impact' },
                    { label: 'Kinetic Form (Rolling)', k: 'Rolling Form' },
                    { label: 'Elite Outputs (≥85)', k: 'Elite Innings' },
                    { label: 'Total Deployments', k: 'Innings Played' },
                  ].map((row, i) => {
                    const valA = dataA.summary[row.k];
                    const valB = dataB.summary[row.k];
                    const win = row.k === 'role' ? { winner: '-', color: 'var(--text-muted)', indicator: '' } : getWinner(valA, valB, row.k);
                    return (
                      <tr key={i} style={{ borderBottom: i === 5 ? 'none' : '1px solid var(--border)' }}>
                        <td className="font-bold" style={{ textAlign: 'left', paddingLeft: '30px', color: 'var(--text-muted)' }}>{row.label}</td>
                        <td style={{ fontSize: '1.1rem', fontWeight: win.winner === playerA ? 800 : 400, color: win.winner === playerA ? 'var(--primary)' : 'var(--text-main)' }}>{valA}</td>
                        <td style={{ fontSize: '1.1rem', fontWeight: win.winner === playerB ? 800 : 400, color: win.winner === playerB ? 'var(--accent-red)' : 'var(--text-main)' }}>{valB}</td>
                        <td style={{ color: win.color, fontWeight: 'bold', fontSize: '1.1rem' }}>
                          <span style={{ marginRight: '8px' }}>{win.indicator}</span> {win.winner}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <h3 className="section-header animate-fade-in delay-400" style={{ marginTop: '40px' }}>
              <Activity size={22} style={{ color: 'var(--primary)' }} />
              Tactical Vector Comparison
            </h3>
            <div className="glass-panel animate-fade-in delay-500" style={{ padding: '30px', height: '450px', display: 'flex', justifyContent: 'center' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart
                  cx="50%" cy="50%" outerRadius="75%"
                  data={[
                    {
                      subject: 'Batting Phase',
                      A: dataA.summary['Avg Bat Perf'],
                      B: dataB.summary['Avg Bat Perf'],
                      fullMark: 5,
                    },
                    {
                      subject: 'Bowling Control',
                      A: dataA.summary['Avg Bowl Perf'] === 'N/A' ? 0 : dataA.summary['Avg Bowl Perf'],
                      B: dataB.summary['Avg Bowl Perf'] === 'N/A' ? 0 : dataB.summary['Avg Bowl Perf'],
                      fullMark: 5,
                    },
                    {
                      subject: 'Match Context',
                      A: dataA.summary['Avg Context'] || 1,
                      B: dataB.summary['Avg Context'] || 1,
                      fullMark: 1.5,
                    },
                    {
                      subject: 'Crisis Situation',
                      A: dataA.summary['Avg Situation'] || 1,
                      B: dataB.summary['Avg Situation'] || 1,
                      fullMark: 1.5,
                    },
                  ]}
                >
                  <PolarGrid gridType="polygon" stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 13, fontWeight: 600 }} />
                  <Tooltip
                    wrapperStyle={{ outline: 'none' }}
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      color: 'var(--text-main)',
                      boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
                    }}
                    itemStyle={{ fontWeight: 800 }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                  <Radar name={playerA} dataKey="A" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.3} />
                  <Radar name={playerB} dataKey="B" stroke="var(--accent-red)" fill="var(--accent-red)" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default HeadToHead;
