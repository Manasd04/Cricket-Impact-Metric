import React, { useState, useEffect } from 'react';

const MESSAGES = [
  'Crunching ball-by-ball data...',
  'Computing pressure coefficients...',
  'Calculating match context scores...',
  'Aggregating rolling impact metrics...',
  'Fetching telemetry...',
];

const LoadingSpinner = () => {
  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIndex(prev => (prev + 1) % MESSAGES.length);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loader-container">
      <div style={{ position: 'relative', width: '60px', height: '60px', marginBottom: '20px' }}>
        {/* Outer ring */}
        <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '3px solid rgba(56, 189, 248, 0.1)', borderTopColor: 'var(--primary)', animation: 'spin 1s linear infinite' }} />
        {/* Inner ring */}
        <div style={{ position: 'absolute', inset: '10px', borderRadius: '50%', border: '3px solid rgba(34, 211, 238, 0.1)', borderBottomColor: '#22d3ee', animation: 'spin 0.7s linear infinite reverse' }} />
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', letterSpacing: '0.5px', transition: 'all 0.3s', textAlign: 'center', minWidth: '220px' }}>
        {MESSAGES[msgIndex]}
      </p>
    </div>
  );
};

export default LoadingSpinner;
