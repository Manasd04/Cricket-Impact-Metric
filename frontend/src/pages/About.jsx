import React from 'react';
import { BookOpen, Target, Calculator, Scale } from 'lucide-react';

const About = () => {
  return (
    <div className="page-content animate-fade-in">
      <div className="header-flex">
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <BookOpen size={32} style={{ color: 'var(--primary)' }} />
            Impact Methodology
          </h2>
          <p style={{ color: 'var(--text-muted)', marginTop: '5px' }}>Deconstructing the algorithmic approach to player evaluation</p>
        </div>
      </div>

      <div className="glass-panel animate-fade-in delay-100" style={{ marginBottom: '30px' }}>
        <h3 className="section-header">
          <Target size={22} style={{ color: 'var(--primary)' }} /> 
          What Is Kinetic Impact?
        </h3>
        <div style={{ padding: '10px 0', lineHeight: '1.8', fontSize: '1.1rem', color: 'var(--text-main)' }}>
          <p>
            Impact in cricket is a <strong style={{ color: 'var(--primary)' }}>unified, context-aware score (0–100)</strong> that quantifies how decisively an operator
            shifted the match outcome in their franchise's favour — not merely <em>what</em> they did, but <em>when</em> and <em>under 
            how much pressure</em> they did it.
          </p>
          <div style={{ marginTop: '20px', padding: '20px', background: 'rgba(56, 189, 248, 0.05)', borderLeft: '4px solid var(--primary)', borderRadius: '0 8px 8px 0' }}>
            <p style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
              "A 30-ball 60 in a death-over chase with 3 wickets left carries significantly higher telemetry weight than a 60-ball 60 in a comfortable powerplay."
            </p>
          </div>
        </div>
      </div>

      <div className="dashboard-columns animate-fade-in delay-200">
        <div className="glass-panel">
          <h3 className="section-header">
            <Calculator size={22} style={{ color: 'var(--accent-gold)' }} /> 
            Core Equation
          </h3>
          <div className="code-block" style={{ background: 'rgba(0,0,0,0.5)', padding: '20px', borderRadius: '8px', border: '1px solid var(--border-light)', fontFamily: 'monospace', color: 'var(--accent-green)', fontSize: '1.1rem', marginBottom: '20px' }}>
            IMPACT = 100 / (1 + e<sup>-5 * (RawImpact - 1)</sup>)
          </div>
          <p style={{ color: 'var(--text-muted)', marginBottom: '15px' }}>Where the primary tensor is calculated as:</p>
          <div style={{ padding: '15px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border)' }}>
            <code style={{ color: 'var(--primary)', fontSize: '1.05rem' }}>RawImpact = TotalPerformance × Context × Situation</code>
          </div>
        </div>

        <div className="glass-panel">
          <h3 className="section-header">
            <Scale size={22} style={{ color: 'var(--accent-green)' }} /> 
            Weight Distributions
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <h4 style={{ color: 'var(--primary)', marginBottom: '15px' }}>Offensive (Batting)</h4>
              <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ color: 'var(--accent-gold)' }}>■</span> <strong>Runs (40%)</strong> — Primary output</li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ color: 'var(--accent-green)' }}>■</span> <strong>Strike Rate (30%)</strong> — Aggression</li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ color: 'var(--primary)' }}>■</span> <strong>Boundaries (30%)</strong> — Ball striking</li>
              </ul>
            </div>
            <div>
              <h4 style={{ color: 'var(--accent-red)', marginBottom: '15px' }}>Defensive (Bowling)</h4>
              <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ color: 'var(--accent-gold)' }}>■</span> <strong>Wickets (50%)</strong> — Decisive action</li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ color: 'var(--accent-green)' }}>■</span> <strong>Economy (30%)</strong> — Control</li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ color: 'var(--primary)' }}>■</span> <strong>Dot Balls (20%)</strong> — Pressure</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;
