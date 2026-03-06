import React, { useState, useEffect, useMemo } from 'react';
import Navbar from '../components/Navbar';
import LoadingSpinner from '../components/LoadingSpinner';
import { getLeaderboard } from '../services/api';
import { Trophy, ArrowLeft, Search, Filter, TrendingUp, Users, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ROLES = ['All', 'Batter', 'Bowler', 'Allrounder'];

const Leaderboard = () => {
  const [rawData, setRawData] = useState({ All: [], Batter: [], Bowler: [], Allrounder: [] });
  const [loading, setLoading] = useState(true);
  const [activeRole, setActiveRole] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('Avg_IM');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getLeaderboard();
        // New endpoint returns { All: [...], Batter: [...], Bowler: [...], Allrounder: [...] }
        if (response && response.All) {
          setRawData(response);
        } else if (response && response.top_rolling) {
          // Fallback: legacy tournament format
          setRawData({ All: response.top_rolling, Batter: [], Bowler: [], Allrounder: [] });
        }
      } catch (error) {
        console.error("Error fetching leaderboard", error);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  // Active role selects from pre-segmented API data
  const allData = rawData[activeRole] || [];

  // Computed: search filter + sort
  const filteredData = useMemo(() => {
    let result = [...allData];
    if (searchQuery.trim()) {
      result = result.filter(p =>
        p.player.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    result.sort((a, b) => parseFloat(b[sortBy] || 0) - parseFloat(a[sortBy] || 0));
    return result;
  }, [allData, searchQuery, sortBy]);

  // Compute the max score for progress bar rendering
  const maxScore = useMemo(() => {
    if (filteredData.length === 0) return 100;
    return Math.max(...filteredData.map(p => parseFloat(p.Rolling_Impact || 0)));
  }, [filteredData]);

  const roleTabStyle = (role) => ({
    padding: '8px 20px',
    borderRadius: '8px',
    border: '1px solid',
    borderColor: activeRole === role ? 'var(--primary)' : 'var(--border)',
    background: activeRole === role ? 'rgba(56,189,248,0.15)' : 'transparent',
    color: activeRole === role ? 'var(--primary)' : 'var(--text-muted)',
    cursor: 'pointer',
    fontWeight: activeRole === role ? 700 : 500,
    fontSize: '0.9rem',
    transition: 'all 0.2s ease',
  });

  // Role to badge color map
  const getRoleBadgeClass = (role) => {
    switch ((role || '').toLowerCase()) {
      case 'batter': return 'badge-batter';
      case 'bowler': return 'badge-bowler';
      case 'allrounder': return 'badge-allrounder';
      default: return 'badge-utility';
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <div
        className="page-content animate-fade-in"
        style={{ padding: '40px 50px', flexGrow: 1, maxWidth: '1100px', margin: '0 auto', width: '100%' }}
      >

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '30px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <button
              onClick={() => navigate(-1)}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 18px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem', transition: 'all 0.2s ease' }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--primary)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <ArrowLeft size={16} /> Back
            </button>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
              <Trophy size={30} style={{ color: 'var(--accent-gold)' }} />
              Top Impact Players
            </h2>
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontWeight: 500 }}>
            <span style={{ color: 'var(--primary)', fontWeight: 700 }}>2007 – 2025</span> &nbsp;|&nbsp; IPL Dataset
          </div>
        </div>

        {/* Controls: Role Filter + Search + Sort */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '15px', marginBottom: '25px' }}>
          {/* Role tabs */}
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {ROLES.map(role => (
              <button key={role} style={roleTabStyle(role)} onClick={() => setActiveRole(role)}>
                {role === 'All' && <Users size={14} style={{ marginRight: '6px', display: 'inline' }} />}
                {role === 'Batter' && '🏏 '}
                {role === 'Bowler' && '⚾ '}
                {role === 'Allrounder' && '⚡ '}
                {role}
              </button>
            ))}
          </div>

          {/* Search box */}
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              placeholder="Search player..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                backgroundColor: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '10px 15px 10px 40px',
                color: 'var(--text-main)',
                fontSize: '0.9rem',
                outline: 'none',
                width: '220px',
              }}
            />
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)', pointerEvents: 'none' }} />
          </div>
        </div>

        {/* Stats strip */}
        {!loading && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px', marginBottom: '25px' }}>
            {[
              { label: 'Total Players', value: filteredData.length, icon: <Users size={18} /> },
              { label: 'Avg Impact', value: (filteredData.reduce((s, p) => s + parseFloat(p.Avg_IM || 0), 0) / (filteredData.length || 1)).toFixed(1), icon: <TrendingUp size={18} /> },
              { label: '#1 This View', value: filteredData[0]?.player || '—', icon: <Trophy size={18} /> },
            ].map(({ label, value, icon }) => (
              <div key={label} className="metric-card" style={{ padding: '18px 22px', flexDirection: 'row', alignItems: 'center', gap: '12px' }}>
                <div style={{ color: 'var(--primary)' }}>{icon}</div>
                <div>
                  <div className="label" style={{ fontSize: '0.8rem' }}>{label}</div>
                  <div className="value" style={{ fontSize: '1.4rem' }}>{value}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '100px' }}>
            <LoadingSpinner />
          </div>
        ) : filteredData.length === 0 ? (
          <div className="glass-panel" style={{ padding: '60px', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>No players match your filter. Try changing the role or search term.</p>
          </div>
        ) : (
          <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '70px', textAlign: 'center' }}>Rank</th>
                   <th>Player</th>
                   <th>Score Distribution</th>
                   <th style={{ textAlign: 'right', width: '90px' }}>Avg IM</th>
                   <th style={{ textAlign: 'right', width: '90px' }}>Peak IM</th>
                   <th style={{ textAlign: 'right', width: '80px' }}>Matches</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((player, index) => {
                  const score = parseFloat(player.Avg_IM || player.Rolling_Impact || 0);
                  const peakScore = parseFloat(player.Peak_IM || 0);
                  const matches = player.Matches || '—';
                  const barWidth = ((score / maxScore) * 100).toFixed(1);
                  const barColor = index === 0
                    ? 'var(--accent-gold)'
                    : index < 3 ? 'var(--primary)' : 'rgba(56,189,248,0.5)';

                  return (
                    <tr
                      key={index}
                      style={{ cursor: 'pointer', transition: 'background 0.2s' }}
                      onClick={() => navigate(`/player/${encodeURIComponent(player.player)}`)}
                    >
                      <td style={{ textAlign: 'center' }}>
                        <span className={`rank-circle rank-style-${index < 3 ? index + 1 : 'other'}`}>
                          {index + 1}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div>
                            <div style={{ fontWeight: 800, fontSize: '1.1rem', color: index < 3 ? 'var(--text-main)' : 'var(--text-muted)' }}>
                              {player.player}
                            </div>
                            <span className={`role-badge ${getRoleBadgeClass(player.role)}`} style={{ fontSize: '0.65rem', padding: '2px 9px', marginTop: '4px', display: 'inline-block' }}>
                              {player.role || 'Utility'}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td style={{ paddingRight: '20px' }}>
                        {/* Visual Score Bar */}
                        <div style={{ height: '8px', background: 'rgba(255,255,255,0.07)', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${barWidth}%`, background: barColor, borderRadius: '4px', transition: 'width 0.6s ease' }} />
                        </div>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span style={{ fontWeight: 900, color: index === 0 ? 'var(--accent-gold)' : 'var(--primary)', fontSize: '1.2rem' }}>
                          {score.toFixed(1)}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', color: 'var(--accent-green)', fontWeight: 700 }}>
                        {peakScore.toFixed(1)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
                          <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{matches}</span>
                          <ChevronRight size={14} color="var(--text-very-muted)" />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Leaderboard;
