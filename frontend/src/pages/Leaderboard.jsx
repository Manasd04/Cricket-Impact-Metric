import React, { useState, useEffect, useMemo } from 'react';
import Navbar from '../components/Navbar';
import LoadingSpinner from '../components/LoadingSpinner';
import { getLeaderboard, getTeams } from '../services/api';
import { Trophy, ArrowLeft, Search, TrendingUp, Users, ChevronRight, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ROLES = ['All', 'Batter', 'Bowler', 'Allrounder'];

const Leaderboard = () => {
  const [rawData, setRawData] = useState({ All: [], Batter: [], Bowler: [], Allrounder: [] });
  const [loading, setLoading] = useState(true);
  const [activeRole, setActiveRole] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeason, setSelectedSeason] = useState('All Time');
  const [selectedTeam, setSelectedTeam] = useState('All');
  const [teams, setTeams] = useState([]);
  const [sortBy, setSortBy] = useState('Avg_IM');
  const navigate = useNavigate();

  // Fetch team list once on mount
  useEffect(() => {
    getTeams()
      .then(res => { if (res?.teams) setTeams(res.teams); })
      .catch(err => console.error('Teams fetch error:', err));
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const seasonParam = selectedSeason === 'All Time' ? undefined : selectedSeason;
        const teamParam   = selectedTeam  === 'All'      ? undefined : selectedTeam;
        const response = await getLeaderboard(seasonParam, teamParam);
        if (response && response.All) {
          setRawData(response);
        } else if (response && response.top_rolling) {
          setRawData({ All: response.top_rolling, Batter: [], Bowler: [], Allrounder: [] });
        }
      } catch (error) {
        console.error('Error fetching leaderboard', error);
      }
      setLoading(false);
    };
    fetchData();
  }, [selectedSeason, selectedTeam]);

  // Generate Season Options (2008 to 2025)
  const seasonOptions = ['All Time', ...Array.from({ length: 18 }, (_, i) => (2025 - i).toString())];

  // Active role selects from pre-segmented API data
  const allData = rawData[activeRole] || [];

  // Step 1: Sort the FULL list and assign real global ranks
  const rankedData = useMemo(() => {
    const result = [...allData];
    result.sort((a, b) => parseFloat(b[sortBy] || 0) - parseFloat(a[sortBy] || 0));
    return result.map((p, i) => ({ ...p, _rank: i + 1 })); // attach real rank
  }, [allData, sortBy]);

  // Step 2: Apply search filter (preserving real ranks) OR show top 10
  const filteredData = useMemo(() => {
    if (searchQuery.trim()) {
      // Show all matched players with their actual rank in the full leaderboard
      return rankedData.filter(p =>
        p.player.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    // Default: top 10 only
    return rankedData.slice(0, 10);
  }, [rankedData, searchQuery]);


  const maxScore = 100;

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
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span><span style={{ color: 'var(--primary)', fontWeight: 700 }}>2008 – 2025</span> &nbsp;|&nbsp; IPL Dataset</span>

            {/* Season filter */}
            <select
              value={selectedSeason}
              onChange={(e) => setSelectedSeason(e.target.value)}
              style={{ padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border)', background: 'rgba(15, 23, 42, 0.6)', color: 'var(--text-main)', cursor: 'pointer' }}
            >
              {seasonOptions.map(s => <option key={s} value={s}>{s}</option>)}
            </select>

            {/* Team filter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Shield size={15} style={{ color: 'var(--accent-gold)' }} />
              <select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
                style={{ padding: '8px 14px', borderRadius: '8px', border: `1px solid ${selectedTeam !== 'All' ? 'var(--accent-gold)' : 'var(--border)'}`, background: 'rgba(15, 23, 42, 0.6)', color: selectedTeam !== 'All' ? 'var(--accent-gold)' : 'var(--text-main)', cursor: 'pointer', fontWeight: selectedTeam !== 'All' ? 700 : 400 }}
              >
                <option value="All">All Teams</option>
                {teams.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
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

          <div style={{ display: 'flex', gap: '15px' }}>
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

            {/* Sort dropdown */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{ padding: '10px 30px 10px 15px', borderRadius: '8px', border: '1px solid var(--border)', background: 'rgba(15, 23, 42, 0.6)', color: 'var(--text-main)' }}
            >
              <option value="Avg_IM">Sort: Average IM</option>
              <option value="Peak_IM">Sort: Peak IM</option>
              <option value="Rolling_Impact">Sort: Rolling Impact</option>
            </select>
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
                  <th>Score Distribution ({sortBy.replace('_', ' ')})</th>
                  <th style={{ textAlign: 'center', width: '110px' }}>Rolling Impact</th>
                  <th style={{ textAlign: 'right', width: '90px' }}>Avg IM</th>
                  <th style={{ textAlign: 'right', width: '90px' }}>Peak IM</th>
                  <th style={{ textAlign: 'right', width: '80px' }}>Matches</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((player, index) => {
                  const avgScore = parseFloat(player.Avg_IM || 0);
                  const peakScore = parseFloat(player.Peak_IM || 0);
                  const rollingScore = parseFloat(player.Rolling_Impact || 0);
                  const matches = player.Matches || '—';

                  let distributionScore = avgScore;
                  if (sortBy === 'Peak_IM') distributionScore = peakScore;
                  if (sortBy === 'Rolling_Impact') distributionScore = rollingScore;

                  // The impact score is out of 100.
                  const barWidth = Math.min(Math.max(distributionScore, 0), 100).toFixed(1);

                  const barColor = player._rank <= 3 ? 'var(--primary)' : 'rgba(56,189,248,0.5)';

                  return (
                    <tr
                      key={index}
                      style={{ cursor: 'pointer', transition: 'background 0.2s' }}
                      onClick={() => navigate(`/player/${encodeURIComponent(player.player)}`)}
                    >
                      <td style={{ textAlign: 'center' }}>
                        <span className={`rank-circle rank-style-${player._rank <= 3 ? player._rank : 'other'}`}>
                          {player._rank}
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
                      <td style={{ textAlign: 'center' }}>
                        <span style={{ fontWeight: sortBy === 'Rolling_Impact' ? 900 : 600, color: sortBy === 'Rolling_Impact' ? 'var(--primary)' : 'var(--text-main)', fontSize: sortBy === 'Rolling_Impact' ? '1.2rem' : '1.1rem' }}>
                          {rollingScore ? rollingScore.toFixed(1) : '—'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span style={{ fontWeight: sortBy === 'Avg_IM' ? 900 : 500, color: sortBy === 'Avg_IM' ? 'var(--primary)' : 'var(--text-main)', fontSize: sortBy === 'Avg_IM' ? '1.2rem' : '1.1rem' }}>
                          {avgScore.toFixed(1)}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', color: sortBy === 'Peak_IM' ? 'var(--accent-green)' : 'var(--text-main)', fontWeight: sortBy === 'Peak_IM' ? 900 : 500, fontSize: sortBy === 'Peak_IM' ? '1.2rem' : '1.1rem' }}>
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