import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import LoadingSpinner from '../components/LoadingSpinner';
import PlayerCard from '../components/PlayerCard';
import ImpactMeter from '../components/ImpactMeter';
import StatsBreakdown from '../components/StatsBreakdown';
import ImpactTrendChart from '../components/ImpactTrendChart';
import InningsTable from '../components/InningsTable';
import { getPlayerImpact } from '../services/api';
import { ArrowLeft, RefreshCw, Award } from 'lucide-react';



const PlayerDashboard = () => {
  const { playerName } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selectedSeason, setSelectedSeason] = useState('All Time');
  const [selectedWindow, setSelectedWindow] = useState('All Time');

  const fetchPlayer = async (name, seasonVal, windowVal) => {
    setLoading(true);
    setError(false);
    try {
      const apiSeason = seasonVal === 'All Time' ? undefined : seasonVal;
      const apiWindow = windowVal === 'All Time' ? undefined : windowVal;
      const response = await getPlayerImpact(name, { season: apiSeason, window: apiWindow });
      if (response.error) { setError(true); }
      else { setData(response); }
    } catch (err) {
      console.error('Error:', err);
      setError(true);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (playerName) fetchPlayer(playerName, selectedSeason, selectedWindow);
  }, [playerName, selectedSeason, selectedWindow]);

  const decodedName = decodeURIComponent(playerName);
  const summary = data?.summary || {};
  const rollingScore = parseFloat(summary['Rolling Form'] || summary['Avg Impact'] || 0).toFixed(1);
  const peakScore = parseFloat(summary['Peak Impact'] || 0).toFixed(1);
  const avgBat = parseFloat(summary['Avg Bat Perf'] || 0).toFixed(2);
  const avgContext = parseFloat(summary['Avg Context'] || 1.0).toFixed(2);
  const avgSituation = parseFloat(summary['Avg Situation'] || 1.0).toFixed(2);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <div style={{ padding: '30px 50px', flexGrow: 1, maxWidth: '1400px', margin: '0 auto', width: '100%' }}>

        {/* Page Header with back nav and season filter */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '30px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <button
              onClick={() => navigate(-1)}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 18px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem', transition: 'all 0.2s ease' }}
              onMouseEnter={e => { e.target.style.color = 'var(--text-main)'; e.target.style.borderColor = 'var(--primary)'; }}
              onMouseLeave={e => { e.target.style.color = 'var(--text-muted)'; e.target.style.borderColor = 'var(--border)'; }}
            >
              <ArrowLeft size={16} /> Back
            </button>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)' }}>
              {decodedName}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Season:</span>
              <select
                value={selectedSeason}
                onChange={(e) => {
                  setSelectedSeason(e.target.value);
                  setSelectedWindow('All Time'); // reset window when season changes
                }}
                style={{ padding: '8px 14px', fontSize: '0.9rem', borderRadius: '6px', background: 'rgba(15, 23, 42, 0.6)', color: 'var(--text-main)', border: '1px solid var(--border)' }}
              >
                <option value="All Time">All Time</option>
                {(data?.available_seasons || []).map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <button
              onClick={() => fetchPlayer(playerName, selectedSeason, selectedWindow)}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(56,189,248,0.1)', border: '1px solid var(--primary)', borderRadius: '8px', padding: '10px 18px', color: 'var(--primary)', cursor: 'pointer', fontSize: '0.9rem' }}
            >
              <RefreshCw size={16} /> Refresh
            </button>
            <Link to="/leaderboard" style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(251,191,36,0.1)', border: '1px solid var(--accent-gold)', borderRadius: '8px', padding: '10px 18px', color: 'var(--accent-gold)', cursor: 'pointer', fontSize: '0.9rem', textDecoration: 'none' }}>
              <Award size={16} /> Leaderboard
            </Link>
          </div>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', marginTop: '40px', border: '1px solid rgba(248, 113, 113, 0.3)' }}>
            <h3 style={{ color: 'var(--accent-red)', marginBottom: '15px', fontSize: '1.5rem' }}>⚠ Unable to Load Player</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '25px' }}>Could not calculate impact metrics for <strong style={{ color: 'var(--text-main)' }}>{decodedName}</strong>. The player may not have enough innings data.</p>
            <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
              <button onClick={() => navigate('/')} style={{ padding: '12px 24px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 700 }}>
                Go Home
              </button>
              <button onClick={() => fetchPlayer(playerName)} style={{ padding: '12px 24px', background: 'transparent', color: 'var(--text-muted)', border: '1px solid var(--border)', borderRadius: '8px', cursor: 'pointer' }}>
                Retry
              </button>
            </div>
          </div>
        ) : data ? (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>

            {/* Row 1: Player Card + Impact Meter + Stats Breakdown */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '25px' }}>
              <PlayerCard
                name={decodedName}
                role={summary.role || 'Utility'}
                impactScore={rollingScore}
              />
              <ImpactMeter score={parseFloat(rollingScore)} />
              <StatsBreakdown
                performance={avgBat}
                context={avgContext}
                pressure={avgSituation}
              />
            </div>

            {/* Row 2: Impact Trend + Quick Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '25px' }}>
              <ImpactTrendChart
                data={data.trend}
                window={selectedWindow}
                onWindowChange={setSelectedWindow}
              />

              {/* Quick Stats Panel */}
              <div className="glass-panel animate-fade-in delay-400" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
                <h3 className="section-header">Quick Stats</h3>
                {[
                  { label: 'Innings Played', value: summary['Innings Played'] || '--' },
                  { label: 'Average Impact', value: summary['Avg Impact'] || '--' },
                  { label: 'Peak Impact', value: peakScore },
                  { label: 'Elite Innings (≥85)', value: summary['Elite Innings'] || '--' },
                  { label: 'Avg Bat Perf', value: avgBat },
                  { label: 'Avg Bowling Perf', value: summary['Avg Bowl Perf'] || 'N/A' },
                ].map(({ label, value }) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '12px', borderBottom: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{label}</span>
                    <span style={{ fontWeight: 800, color: 'var(--text-main)', fontSize: '1rem' }}>{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Row 3: Innings Breakdown Table */}
            <InningsTable inningsData={data.trend} />
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default PlayerDashboard;
