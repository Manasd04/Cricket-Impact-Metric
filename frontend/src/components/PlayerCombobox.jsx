import React, { useState, useEffect, useRef } from 'react';

const PlayerCombobox = ({ value, onChange, players }) => {
    const [searchTerm, setSearchTerm] = useState(value || '');
    const [showSuggestions, setShowSuggestions] = useState(false);
    const wrapperRef = useRef(null);

    useEffect(() => {
        setSearchTerm(value);
    }, [value]);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setShowSuggestions(false);
                // Revert to the selected value if clicked outside
                if (value) {
                    setSearchTerm(value);
                }
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef, value]);

    const searchWords = searchTerm.toLowerCase().trim().split(/\s+/);
    const filteredPlayers = searchTerm.trim().length > 0
        ? players.filter(p => searchWords.every(word => p.toLowerCase().includes(word)))
        : players.slice(0, 100);

    const handleSelect = (player) => {
        setSearchTerm(player);
        onChange(player);
        setShowSuggestions(false);
    };

    return (
        <div ref={wrapperRef} style={{ position: 'relative', width: '100%' }}>
            <input
                type="text"
                value={searchTerm}
                className="player-select"
                onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setShowSuggestions(true);
                }}
                onFocus={() => {
                    // When focusing, allow seeing options
                    setShowSuggestions(true);
                    setSearchTerm(''); // Clear to show all options
                }}
                onBlur={() => {
                    // Restore search term if they don't pick anything on blur
                    if (!showSuggestions && value) {
                        setSearchTerm(value);
                    }
                }}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && filteredPlayers.length > 0) {
                        handleSelect(filteredPlayers[0]);
                    }
                    if (e.key === 'Escape') {
                        setShowSuggestions(false);
                        setSearchTerm(value);
                    }
                }}
                style={{
                    width: '100%',
                    backgroundColor: 'rgba(255,255,255,0.05)',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    color: 'var(--text-main)',
                    fontSize: '1.1rem',
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                    cursor: 'text'
                }}
                onMouseEnter={e => e.target.style.borderColor = 'var(--primary)'}
                onMouseLeave={e => { if (document.activeElement !== e.target) e.target.style.borderColor = 'var(--border)'; }}
                placeholder="Search player..."
            />

            {showSuggestions && filteredPlayers.length > 0 && (
                <div className="custom-scrollbar" style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, width: '100%', maxHeight: '400px', overflowY: 'auto', background: 'var(--bg-surface)', border: '1px solid var(--border-primary)', borderRadius: '10px', zIndex: 1000, boxShadow: '0 12px 30px rgba(0,0,0,0.5)' }}>
                    {filteredPlayers.map((player) => (
                        <div
                            key={player}
                            onMouseDown={(e) => { e.preventDefault(); handleSelect(player); }}
                            style={{ padding: '12px 16px', cursor: 'pointer', fontSize: '1rem', color: 'var(--text-main)', fontWeight: 500, borderBottom: '1px solid var(--border)', transition: 'background 0.15s' }}
                            onMouseEnter={e => e.currentTarget.style.background = 'rgba(56,189,248,0.1)'}
                            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                        >
                            {player}
                        </div>
                    ))}
                </div>
            )}
            {showSuggestions && filteredPlayers.length === 0 && (
                <div style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, width: '100%', background: 'var(--bg-surface)', border: '1px solid var(--border-primary)', borderRadius: '10px', zIndex: 1000, padding: '12px 16px', color: 'var(--text-muted)' }}>
                    No players found.
                </div>
            )}
        </div>
    );
};

export default PlayerCombobox;
