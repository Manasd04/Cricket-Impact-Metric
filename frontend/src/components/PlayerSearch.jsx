import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPlayersList } from '../services/api';
import { Search, Clock, X } from 'lucide-react';

const RECENT_KEY = 'cim_recent_players';

const PlayerSearch = ({ compact = false }) => {
  const [players, setPlayers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [recentSearches, setRecentSearches] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const navigate = useNavigate();
  const wrapperRef = useRef(null);

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
    try {
      const stored = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
      setRecentSearches(stored);
    } catch { }
  }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [wrapperRef]);

  const navigateToPlayer = (player) => {
    if (!player) return;
    const updated = [player, ...recentSearches.filter(p => p !== player)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
    navigate(`/player/${encodeURIComponent(player)}`);
    if (compact) setShowSuggestions(false);
  };

  const clearRecent = (e) => {
    e.stopPropagation();
    setRecentSearches([]);
    localStorage.removeItem(RECENT_KEY);
  };

  // Allow searching for parts of a name (e.g., "m s dhoni" finds "MS Dhoni")
  const searchWords = searchTerm.toLowerCase().trim().split(/\s+/);
  const filteredPlayers = searchTerm.trim().length > 0
    ? players.filter(p => searchWords.every(word => p.toLowerCase().includes(word)))
    : (compact ? [] : players);
  
  // Cap the initial list if not searching to prevent lag
  const displayPlayers = searchTerm.trim().length > 0 ? filteredPlayers : players.slice(0, 100);

  const handleSelectPlayer = (player) => {
    setSearchTerm(player);
    setShowSuggestions(false);
    if (compact) {
      navigateToPlayer(player);
    }
  };

  if (compact) {
    return (
      <div ref={wrapperRef} style={{ position: 'relative', width: '240px' }}>
        <input
          type="text"
          placeholder="Search player..."
          value={searchTerm}
          onChange={(e) => { setSearchTerm(e.target.value); setShowSuggestions(true); }}
          onFocus={() => setShowSuggestions(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && filteredPlayers.length > 0) handleSelectPlayer(filteredPlayers[0]);
            if (e.key === 'Escape') setShowSuggestions(false);
          }}
          style={{ width: '100%', backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 36px 9px 14px', color: 'var(--text-main)', fontSize: '0.88rem', outline: 'none', transition: 'border-color 0.2s, box-shadow 0.2s' }}
          onMouseEnter={e => e.target.style.borderColor = 'var(--primary)'}
          onMouseLeave={e => { if (document.activeElement !== e.target) e.target.style.borderColor = 'var(--border)'; }}
        />
        <Search size={15} style={{ position: 'absolute', right: '11px', top: '11px', color: 'var(--text-muted)', pointerEvents: 'none' }} />

        {showSuggestions && filteredPlayers.length > 0 && (
          <div className="custom-scrollbar" style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, width: '100%', maxHeight: '400px', overflowY: 'auto', background: 'var(--bg-surface)', border: '1px solid var(--border-primary)', borderRadius: '10px', zIndex: 1000, boxShadow: '0 12px 30px rgba(0,0,0,0.5)' }}>
            {filteredPlayers.map((player) => (
              <div
                key={player}
                onMouseDown={(e) => { e.preventDefault(); handleSelectPlayer(player); }}
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
    <div ref={wrapperRef} style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '500px', width: '100%', margin: '0 auto' }}>
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          placeholder="Search by name (e.g. MS Dhoni)..."
          value={searchTerm}
          onChange={(e) => { setSearchTerm(e.target.value); setShowSuggestions(true); }}
          onFocus={() => setShowSuggestions(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
               if (players.includes(searchTerm)) navigateToPlayer(searchTerm);
               else if (displayPlayers.length > 0) handleSelectPlayer(displayPlayers[0]);
            }
            if (e.key === 'Escape') setShowSuggestions(false);
          }}
          style={{ width: '100%', backgroundColor: '#0f172a', border: '1px solid rgba(56, 189, 248, 0.4)', borderRadius: '12px', padding: '16px 20px', color: 'white', fontSize: '1.1rem', fontWeight: 600, outline: 'none' }}
        />
        <Search style={{ position: 'absolute', right: '15px', top: '16px', color: 'var(--text-muted)', pointerEvents: 'none' }} />

        {showSuggestions && (searchTerm.trim().length > 0 || displayPlayers.length > 0) && (
          <div className="custom-scrollbar" style={{ position: 'absolute', top: 'calc(100% + 8px)', left: 0, width: '100%', maxHeight: '300px', overflowY: 'auto', background: '#0f172a', border: '1px solid rgba(56, 189, 248, 0.4)', borderRadius: '12px', zIndex: 1000, boxShadow: '0 12px 30px rgba(0,0,0,0.5)', textAlign: 'left' }}>
            {displayPlayers.length === 0 ? (
               <div style={{ padding: '15px 20px', color: 'var(--text-muted)' }}>No players found.</div>
            ) : (
              displayPlayers.map((player) => (
                <div
                  key={player}
                  onMouseDown={(e) => { e.preventDefault(); handleSelectPlayer(player); }}
                  style={{ padding: '12px 20px', cursor: 'pointer', fontSize: '1rem', color: 'white', fontWeight: 500, borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(56,189,248,0.15)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {player}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <button
        onClick={() => navigateToPlayer(searchTerm)}
        disabled={!players.includes(searchTerm)}
        style={{ width: '100%', padding: '16px', borderRadius: '12px', background: players.includes(searchTerm) ? 'linear-gradient(135deg, var(--primary), #0284c7)' : 'rgba(56,189,248,0.1)', color: 'white', border: '1px solid rgba(56,189,248,0.4)', fontSize: '1.1rem', fontWeight: 800, cursor: players.includes(searchTerm) ? 'pointer' : 'not-allowed', opacity: players.includes(searchTerm) ? 1 : 0.6, letterSpacing: '1px', transition: 'all 0.2s ease' }}
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
