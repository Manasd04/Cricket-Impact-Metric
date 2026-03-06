import React from 'react';
import Navbar from '../components/Navbar';
import PlayerSearch from '../components/PlayerSearch';
import { Activity, Target, Database, Zap } from 'lucide-react';

const FEATURES = [
  { icon: <Activity size={22} color="#38bdf8" />, title: 'Rolling Impact', desc: 'Last 10 innings weighted form' },
  { icon: <Target size={22} color="#10b981" />, title: 'Context-Aware', desc: 'Phase, wickets & opposition' },
  { icon: <Database size={22} color="#a78bfa" />, title: '2007–2025 Data', desc: 'Full IPL ball-by-ball dataset' },
  { icon: <Zap size={22} color="#fbbf24" />, title: 'Pressure Index', desc: 'Under-fire performance metric' },
];

const Home = () => {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <div
        className="page-content animate-fade-in"
        style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '40px 20px', position: 'relative', gap: '40px' }}
      >
        {/* Decorative glowing background */}
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: '70vw', height: '70vw', background: 'radial-gradient(circle, rgba(56, 189, 248, 0.04) 0%, transparent 70%)', zIndex: 0, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', top: '20%', left: '10%', width: '300px', height: '300px', background: 'radial-gradient(circle, rgba(167,139,250,0.04) 0%, transparent 70%)', zIndex: 0, pointerEvents: 'none' }} />

        <div style={{ zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0' }}>
          {/* Badge */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', background: 'rgba(56,189,248,0.1)', padding: '8px 20px', borderRadius: '30px', border: '1px solid rgba(56,189,248,0.3)', marginBottom: '24px' }}>
            <Activity color="var(--primary)" size={18} />
            <span style={{ color: 'var(--primary)', fontWeight: 700, letterSpacing: '2px', fontSize: '0.85rem' }}>HACKATHON 2025</span>
          </div>

          {/* Title */}
          <h1 style={{ fontSize: '5rem', fontWeight: 900, marginBottom: '18px', background: 'linear-gradient(135deg, #ffffff 40%, var(--primary))', WebkitBackgroundClip: 'text', color: 'transparent', letterSpacing: '-3px', lineHeight: 1 }}>
            Cricket Impact
            <br />Metric
          </h1>
          <p style={{ fontSize: '1.15rem', color: 'var(--text-muted)', marginBottom: '40px', maxWidth: '550px', lineHeight: 1.7 }}>
            Quantify a cricketer's true match influence beyond runs and wickets. Powered by ball-by-ball IPL data from 2007 to 2025.
          </p>

          {/* Search card */}
          <div className="glass-panel hover-glow" style={{ width: '100%', maxWidth: '600px', padding: '40px', position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '3px', background: 'linear-gradient(90deg, transparent, var(--primary), transparent)' }} />
            <PlayerSearch />
          </div>
        </div>

        {/* Feature cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', maxWidth: '900px', width: '100%', zIndex: 1 }}>
          {FEATURES.map(({ icon, title, desc }) => (
            <div
              key={title}
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 16px', textAlign: 'center', transition: 'all 0.25s ease', cursor: 'default' }}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.borderColor = 'rgba(56,189,248,0.25)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
            >
              <div style={{ marginBottom: '10px' }}>{icon}</div>
              <div style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--text-main)', marginBottom: '4px' }}>{title}</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Home;
