import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { Swords, Cpu } from 'lucide-react';

const HeadToHead = () => {
  const [players, setPlayers] = useState([]);
  const [playerA, setPlayerA] = useState('');
  const [playerB, setPlayerB] = useState('');
  const [dataA, setDataA] = useState(null);
  const [dataB, setDataB] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get(`http://127.0.0.1:5000/api/v1/players`)
      .then(res => {
        setPlayers(res.data.players);
        if (res.data.players.length >= 2) {
          setPlayerA(res.data.players[0]);
          setPlayerB(res.data.players[1]);
        }
      })
      .catch(err => console.error(err));
  }, []);

  const handleCompare = async () => {
    if (!playerA || !playerB || playerA === playerB) return;
    setLoading(true);
    try {
      const [resA, resB] = await Promise.all([
        axios.get(`http://127.0.0.1:5000/api/v1/player/${encodeURIComponent(playerA)}`),
        axios.get(`http://127.0.0.1:5000/api/v1/player/${encodeURIComponent(playerB)}`)
      ]);
      setDataA(resA.data);
      setDataB(resB.data);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  const getWinner = (valA, valB, metric) => {
    // If metric is economy/bowling we want lower numbers, but our "Avg Bowl Perf" maps higher = better, so higher is always better here.
    const a = parseFloat(valA) || 0;
    const b = parseFloat(valB) || 0;
    if(a > b) return { winner: playerA, color: 'var(--primary)', indicator: '◀' };
    if(b > a) return { winner: playerB, color: 'var(--accent-red)', indicator: '▶' };
    return { winner: 'Tie', color: 'var(--text-muted)', indicator: '—' };
  };

  return (
    <div className="page-content animate-fade-in">
      <div className="header-flex">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <Swords size={34} style={{ color: 'var(--primary)' }} /> 
          Head-to-Head Combats
        </h2>
      </div>

      <div className="glass-panel animate-fade-in delay-100" style={{ marginBottom: '30px', padding: '30px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '30px', alignItems: 'end' }}>
          <div>
            <label className="font-bold" style={{ color: 'var(--primary)', marginBottom: '8px', display: 'block' }}>Operator Alpha:</label>
            <select className="player-select w-full" style={{ padding: '12px 16px', fontSize: '1.1rem' }} value={playerA} onChange={e => setPlayerA(e.target.value)}>
              {players.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', paddingBottom: '2px' }}>
            <button className="primary-btn" style={{ padding: '12px 30px', fontSize: '1.1rem', background: 'var(--bg-base)', border: '1px solid var(--border)', color: 'var(--text-main)' }} onClick={handleCompare} disabled={loading || playerA === playerB}>
              {loading ? 'SIMULATING...' : 'ENGAGE'}
            </button>
          </div>
          <div>
            <label className="font-bold" style={{ color: 'var(--accent-red)', marginBottom: '8px', display: 'block' }}>Operator Beta:</label>
            <select className="player-select w-full" style={{ padding: '12px 16px', fontSize: '1.1rem' }} value={playerB} onChange={e => setPlayerB(e.target.value)}>
              {players.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
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
                  const win = row.k === 'role' ? {winner: '-', color:'var(--text-muted)', indicator: ''} : getWinner(valA, valB, row.k);
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
        </>
      )}
    </div>
  );
};

export default HeadToHead;
