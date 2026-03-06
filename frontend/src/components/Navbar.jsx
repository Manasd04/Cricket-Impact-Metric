import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Home, Trophy, Activity } from 'lucide-react';
import PlayerSearch from './PlayerSearch';

const NAV_LINKS = [
  { to: '/', label: 'Home', icon: <Home size={17} />, exact: true },
  { to: '/leaderboard', label: 'Leaderboard', icon: <Trophy size={17} /> },
];

const Navbar = () => {
  const location = useLocation();
  const isOnPlayerPage = location.pathname.startsWith('/player/');
  const currentPlayer = isOnPlayerPage ? decodeURIComponent(location.pathname.split('/player/')[1]) : null;

  return (
    <nav style={{ width: '100%', background: 'rgba(17, 24, 39, 0.95)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', borderBottom: '1px solid var(--border)', padding: '14px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 100 }}>
      {/* Logo */}
      <NavLink to="/" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none' }}>
        <div style={{ background: 'linear-gradient(135deg, rgba(56,189,248,0.2), rgba(34,211,238,0.1))', padding: '8px', borderRadius: '10px', border: '1px solid rgba(56,189,248,0.25)', display: 'flex', alignItems: 'center' }}>
          <Activity color="var(--primary)" size={22} />
        </div>
        <div>
          <div style={{ fontSize: '1rem', fontWeight: 900, letterSpacing: '1px', color: 'var(--text-main)', lineHeight: 1 }}>IMPACT METRIC</div>
          {currentPlayer && (
            <div style={{ fontSize: '0.72rem', color: 'var(--primary)', fontWeight: 600, marginTop: '2px', letterSpacing: '0.5px' }}>
              → {currentPlayer}
            </div>
          )}
        </div>
      </NavLink>

      {/* Center: nav links */}
      <div style={{ display: 'flex', gap: '6px' }}>
        {NAV_LINKS.map(({ to, label, icon, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            style={({ isActive }) => ({
              textDecoration: 'none',
              color: isActive ? 'var(--primary)' : 'var(--text-muted)',
              fontWeight: isActive ? 700 : 500,
              display: 'flex',
              alignItems: 'center',
              gap: '7px',
              padding: '8px 18px',
              borderRadius: '8px',
              background: isActive ? 'rgba(56,189,248,0.1)' : 'transparent',
              border: `1px solid ${isActive ? 'rgba(56,189,248,0.3)' : 'transparent'}`,
              fontSize: '0.95rem',
              transition: 'all 0.2s ease',
            })}
          >
            {icon} {label}
          </NavLink>
        ))}
      </div>

      {/* Right: search dropdown */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-very-muted)' }}>Quick Switch:</span>
        <PlayerSearch compact={true} />
      </div>
    </nav>
  );
};

export default Navbar;
