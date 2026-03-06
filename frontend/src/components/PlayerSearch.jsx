import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPlayersList } from '../services/api';
import { Search, Clock, X } from 'lucide-react';

const RECENT_KEY = 'cim_recent_players';

const PlayerSearch = ({ compact = false }) => {
  const [players, setPlayers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [recentSearches, setRecentSearches] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const data = await getPlayersList();
        setPlayers(data.players || []);
      } catch (error) {
        console.error("Failed to fetch players", error);
      }
    };
    fetchPlayers();
    // Load recent from localStorage
    try {
      const stored = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
      setRecentSearches(stored);
    } catch { }
  }, []);

  const navigateToPlayer = (player) => {
    if (!player) return;
    // Save to recent searches
    const updated = [player, ...recentSearches.filter(p => p !== player)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
    navigate(`/player/${encodeURIComponent(player)}`);
    if (compact) setSearchTerm('');
  };

  const clearRecent = (e) => {
    e.stopPropagation();
    setRecentSearches([]);
    localStorage.removeItem(RECENT_KEY);
  };

  const [showSuggestions, setShowSuggestions] = useState(false);

  const filteredPlayers = searchTerm.trim().length > 0
    ? players.filter(p => p.toLowerCase().includes(searchTerm.toLowerCase())).slice(0, 8)
    : [];

  const handleCompactSubmit = (player) => {
    setSearchTerm('');
    setShowSuggestions(false);
    navigateToPlayer(player);
  };

  if (compact) {
    return (
      <div style={{ position: 'relative', width: '240px' }} onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setShowSuggestions(false);
      }}>
        {/* Text input */}
        <input
          type="text"
          placeholder="Search player..."
          value={searchTerm}
          onChange={(e) => { setSearchTerm(e.target.value); setShowSuggestions(true); }}
          onFocus={() => setShowSuggestions(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && filteredPlayers.length > 0) handleCompactSubmit(filteredPlayers[0]);
            if (e.key === 'Escape') setShowSuggestions(false);
          }}
          style={{ width: '100%', backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 36px 9px 14px', color: 'var(--text-main)', fontSize: '0.88rem', outline: 'none', transition: 'border-color 0.2s, box-shadow 0.2s' }}
          onMouseEnter={e => e.target.style.borderColor = 'var(--primary)'}
          onMouseLeave={e => { if (document.activeElement !== e.target) e.target.style.borderColor = 'var(--border)'; }}
        />
        <Search size={15} style={{ position: 'absolute', right: '11px', top: '11px', color: 'var(--text-muted)', pointerEvents: 'none' }} />

        {/* Dropdown suggestions */}
        {showSuggestions && filteredPlayers.length > 0 && (
          <div style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, width: '100%', background: 'var(--bg-surface)', border: '1px solid var(--border-primary)', borderRadius: '10px', overflow: 'hidden', zIndex: 1000, boxShadow: '0 12px 30px rgba(0,0,0,0.5)' }}>
            {filteredPlayers.map((player) => (
              <div
                key={player}
                tabIndex={0}
                onMouseDown={() => handleCompactSubmit(player)}
                style={{ padding: '10px 15px', cursor: 'pointer', fontSize: '0.88rem', color: 'var(--text-main)', fontWeight: 600, borderBottom: '1px solid var(--border)', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(56,189,248,0.1)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {player}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '500px', width: '100%', margin: '0 auto' }}>
      <div style={{ position: 'relative' }}>
        <select
          style={{ width: '100%', backgroundColor: '#0f172a', border: '1px solid rgba(56, 189, 248, 0.4)', borderRadius: '12px', padding: '16px 20px', color: 'white', fontSize: '1.1rem', fontWeight: 600, appearance: 'none' }}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        >
          <option value="" disabled>Select a player...</option>
          {players.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <Search style={{ position: 'absolute', right: '15px', top: '16px', color: 'var(--text-muted)', pointerEvents: 'none' }} />
      </div>

      <button
        onClick={() => navigateToPlayer(searchTerm)}
        disabled={!searchTerm}
        style={{ width: '100%', padding: '16px', borderRadius: '12px', background: searchTerm ? 'linear-gradient(135deg, var(--primary), #0284c7)' : 'rgba(56,189,248,0.1)', color: 'white', border: '1px solid rgba(56,189,248,0.4)', fontSize: '1.1rem', fontWeight: 800, cursor: searchTerm ? 'pointer' : 'not-allowed', opacity: searchTerm ? 1 : 0.6, letterSpacing: '1px', transition: 'all 0.2s ease' }}
      >
        CALCULATE IMPACT
      </button>

      {/* Recent Searches */}
      {recentSearches.length > 0 && (
        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid var(--border)', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
              <Clock size={13} /> Recent
            </span>
            <button onClick={clearRecent} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-very-muted)', display: 'flex', alignItems: 'center' }}>
              <X size={14} />
            </button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {recentSearches.map(player => (
              <button
                key={player}
                onClick={() => navigateToPlayer(player)}
                style={{ padding: '6px 14px', background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.2)', borderRadius: '20px', color: 'var(--primary)', fontSize: '0.85rem', cursor: 'pointer', fontWeight: 600, transition: 'all 0.2s ease' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(56,189,248,0.18)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(56,189,248,0.08)'}
              >
                {player}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerSearch;
