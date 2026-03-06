import React from 'react';
import { FileText } from 'lucide-react';

const InningsTable = ({ inningsData }) => {
  if (!inningsData || inningsData.length === 0) return null;

  // We want to sort the data newest to oldest ideally, but the chart is oldest-to-newest.
  // The data passed in `trend` is chronological (oldest -> newest for the chart).
  // So we reverse it just for the table to show the most recent innings at the top.
  const tableData = [...inningsData].reverse();

  return (
    <div className="glass-panel animate-fade-in delay-600" style={{ padding: 0, overflow: 'hidden', marginTop: '25px', width: '100%' }}>
      
      {/* Table Header Area */}
      <div style={{ padding: '20px 25px', background: 'rgba(56,189,248,0.1)', borderBottom: '1px solid var(--border)' }}>
        <h3 className="section-header" style={{ marginBottom: 0 }}>
          <FileText size={20} style={{ color: 'var(--text-main)' }} />
          Recent Innings Breakdown
        </h3>
      </div>

      <div style={{ maxHeight: '400px', overflowY: 'auto' }} className="custom-scrollbar">
        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-surface)', zIndex: 10, borderBottom: '1px solid var(--border-primary)' }}>
            <tr>
              <th style={{ textAlign: 'left', padding: '16px 25px' }}>Match Label</th>
              <th style={{ textAlign: 'center' }}>Season</th>
              <th style={{ textAlign: 'center' }}>Date</th>
              <th style={{ textAlign: 'right' }}>Bat Perf</th>
              <th style={{ textAlign: 'right' }}>Bowl Perf</th>
              <th style={{ textAlign: 'right' }}>Total Perf</th>
              <th style={{ textAlign: 'right' }}>Context</th>
              <th style={{ textAlign: 'center' }}>Situation</th>
              <th style={{ textAlign: 'right', paddingRight: '25px', color: 'var(--primary)' }}>Impact Score</th>
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, index) => (
              <tr key={index} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.2s', fontSize: '0.88rem' }}>
                <td style={{ textAlign: 'left', padding: '14px 25px', color: 'var(--text-main)', maxWidth: '280px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={row.match_label}>
                  {row.match_label || 'Match'}
                </td>
                <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{row.season || '--'}</td>
                <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{row.start_date || '--'}</td>
                
                <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{parseFloat(row.perf_bat || 0).toFixed(2)}</td>
                <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{parseFloat(row.perf_bowl || 0).toFixed(2)}</td>
                <td style={{ textAlign: 'right', color: 'var(--text-main)', fontWeight: 600 }}>{parseFloat(row.Total_Performance || 0).toFixed(2)}</td>
                
                <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{parseFloat(row.Context || 1).toFixed(2)}</td>
                <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{parseFloat(row.Situation || 1).toFixed(2)}</td>
                
                <td style={{ textAlign: 'right', paddingRight: '25px', color: row.Impact_Score >= 70 ? 'var(--accent-green)' : row.Impact_Score >= 50 ? 'var(--primary)' : 'var(--text-main)', fontWeight: 800, fontSize: '1rem' }}>
                  {parseFloat(row.Impact_Score || 0).toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default InningsTable;
