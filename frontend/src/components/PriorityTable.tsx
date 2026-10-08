import React, { useState } from 'react';
import { Search, AlertTriangle, ChevronRight, UserCheck, UserX } from 'lucide-react';
import type { Habitation } from '../types';

interface PriorityTableProps {
  habitations: Habitation[];
  selectedHabitationId: string | null;
  onSelectHabitation: (hab: Habitation) => void;
}

export const PriorityTable: React.FC<PriorityTableProps> = ({
  habitations,
  selectedHabitationId,
  onSelectHabitation,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBucket, setSelectedBucket] = useState<string>('ALL');

  const filteredHabs = habitations.filter((h) => {
    const matchesSearch = h.name.toLowerCase().includes(searchTerm.toLowerCase()) || h.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesBucket = selectedBucket === 'ALL' || h.bucket === selectedBucket;
    return matchesSearch && matchesBucket;
  });

  const getBucketBadge = (bucket: string) => {
    switch (bucket) {
      case 'Immediate':
        return <span className="badge badge-red"><span className="pulsing-dot-red" /> Immediate</span>;
      case 'Short-term':
        return <span className="badge badge-amber">Short-term</span>;
      case 'Medium-term':
        return <span className="badge badge-blue">Medium-term</span>;
      default:
        return <span className="badge badge-gray">None</span>;
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header & Filters */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="#ef4444" />
            Vulnerability-Weighted Relocation Priority Table
          </h3>
          <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>
            Ranked by Urgency Score <span style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>U_i = f(Hazard, Vulnerability, Time, Population)</span>
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Search Box */}
          <div style={{ position: 'relative', minWidth: '220px' }}>
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
            <input
              type="text"
              placeholder="Search habitation..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 12px 7px 32px',
                background: 'rgba(0, 0, 0, 0.35)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '0.82rem',
                outline: 'none',
              }}
            />
          </div>

          {/* Bucket Filter Pills */}
          <div style={{ display: 'flex', gap: '4px', background: 'rgba(0,0,0,0.3)', padding: '3px', borderRadius: '8px' }}>
            {['ALL', 'Immediate', 'Short-term', 'Medium-term'].map((b) => (
              <button
                key={b}
                onClick={() => setSelectedBucket(b)}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: selectedBucket === b ? 'rgba(255,255,255,0.15)' : 'transparent',
                  color: selectedBucket === b ? '#ffffff' : '#94a3b8',
                }}
              >
                {b}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Habitation</th>
              <th>Bucket</th>
              <th>Urgency Score</th>
              <th>Vulnerability (V_i)</th>
              <th>Hazard (H_i)</th>
              <th>Population</th>
              <th>Households</th>
              <th>Relocation Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredHabs.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '32px', color: '#64748b' }}>
                  No habitations match the current filters.
                </td>
              </tr>
            ) : (
              filteredHabs.map((h, idx) => {
                const isSelected = h.id === selectedHabitationId;
                return (
                  <tr
                    key={h.id}
                    onClick={() => onSelectHabitation(h)}
                    style={{
                      background: isSelected ? 'rgba(59, 130, 246, 0.15)' : undefined,
                      borderLeft: isSelected ? '3px solid #3b82f6' : '3px solid transparent',
                    }}
                  >
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#94a3b8' }}>
                      #{idx + 1}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: '#f8fafc' }}>{h.name}</div>
                      <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>{h.id}</div>
                    </td>
                    <td>{getBucketBadge(h.bucket)}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '45px', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${Math.min(100, h.urgency_score * 100)}%`,
                              height: '100%',
                              background: h.urgency_score > 0.6 ? '#ef4444' : h.urgency_score > 0.35 ? '#f59e0b' : '#10b981',
                            }}
                          />
                        </div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{h.urgency_score.toFixed(3)}</span>
                      </div>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{h.vulnerability_index.toFixed(3)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: h.hazard_score > 0.6 ? '#ef4444' : h.hazard_score > 0.35 ? '#f59e0b' : '#10b981' }}>
                        {h.hazard_score.toFixed(3)}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{h.population.toLocaleString()}</td>
                    <td>{h.households.toLocaleString()}</td>
                    <td>
                      {h.assigned_site_id ? (
                        <span className="badge badge-green" style={{ fontSize: '0.7rem' }}>
                          <UserCheck size={12} /> Assigned: {h.assigned_site_id.replace('wayanad_site_', '')}
                        </span>
                      ) : (
                        <span className="badge badge-gray" style={{ fontSize: '0.7rem' }}>
                          <UserX size={12} /> Unassigned
                        </span>
                      )}
                    </td>
                    <td>
                      <button className="btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
                        Inspect <ChevronRight size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
