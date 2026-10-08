import React from 'react';
import { X, CheckCircle, AlertCircle, MapPin, Users, HeartPulse, Home, Info } from 'lucide-react';
import type { Habitation } from '../types';

interface DetailDrawerProps {
  habitation: Habitation | null;
  onClose: () => void;
}

export const DetailDrawer: React.FC<DetailDrawerProps> = ({
  habitation,
  onClose,
}) => {
  if (!habitation) return null;

  const vulnComponents = habitation.vulnerability_breakdown_json?.normalized_components || {
    children_under_6: habitation.vuln_children_u6,
    elderly_60_plus: habitation.vuln_elderly_60p,
    disabled_persons: habitation.vuln_disabled,
    female_headed_hh: habitation.vuln_female_head,
    kutcha_houses: habitation.vuln_kutcha,
    distance_to_health_m: Math.min(1.0, habitation.vuln_dist_health_m / 10000.0),
  };

  return (
    <div
      className="glass-panel"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '420px',
        maxWidth: '90vw',
        zIndex: 100,
        borderRadius: '16px 0 0 16px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-8px 0 32px rgba(0,0,0,0.6)',
        borderLeft: '1px solid rgba(255,255,255,0.15)',
        background: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(20px)',
      }}
    >
      {/* Header */}
      <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className={`badge badge-${habitation.bucket === 'Immediate' ? 'red' : habitation.bucket === 'Short-term' ? 'amber' : 'blue'}`}>
              {habitation.bucket} Bucket
            </span>
            <span className="provenance-pill">{habitation.data_origin}</span>
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff', marginTop: '6px' }}>{habitation.name}</h2>
          <p style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>{habitation.id}</p>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}>
          <X size={20} />
        </button>
      </div>

      {/* Content Scrollable */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Core Metric Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Urgency Score (U_i)</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: habitation.urgency_score > 0.6 ? '#ef4444' : '#f59e0b', fontFamily: 'var(--font-mono)' }}>
              {habitation.urgency_score.toFixed(3)}
            </div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Vulnerability (V_i)</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
              {habitation.vulnerability_index.toFixed(3)}
            </div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Population / HH</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
              {habitation.population} <span style={{ fontSize: '0.8rem', color: '#64748b' }}>/ {habitation.households} hh</span>
            </div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Hazard (H_i)</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
              {habitation.hazard_score.toFixed(3)}
            </div>
          </div>
        </div>

        {/* Relocation Decision Rationale Box */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '14px', borderRadius: '12px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
          <h4 style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Info size={15} /> XAI Relocation Rationale
          </h4>
          {habitation.assigned_site_id ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#4ade80', fontWeight: 600, fontSize: '0.85rem' }}>
                <CheckCircle size={15} /> Assigned to Site: {habitation.assigned_site_id}
              </div>
              <ul style={{ fontSize: '0.78rem', color: '#cbd5e1', marginTop: '8px', paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <li>Priority Rank: #{habitation.decision_reasons_json?.rank || 1}</li>
                <li>Solver Algorithm: {habitation.decision_reasons_json?.solver || 'greedy'}</li>
                {habitation.decision_reasons_json?.reasons?.map((r: string, idx: number) => (
                  <li key={idx}>{r}</li>
                ))}
              </ul>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f87171', fontWeight: 600, fontSize: '0.85rem' }}>
                <AlertCircle size={15} /> Status: Unassigned
              </div>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '6px' }}>
                {habitation.unassigned_reason || 'No candidate site met carrying capacity and tier requirements.'}
              </p>
            </div>
          )}
        </div>

        {/* Vulnerability Component Progress Bars */}
        <div>
          <h4 style={{ fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
            Vulnerability Indicators
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { label: 'Children (< 6 yrs)', val: vulnComponents.children_under_6 || 0, icon: Users },
              { label: 'Elderly (60+ yrs)', val: vulnComponents.elderly_60_plus || 0, icon: HeartPulse },
              { label: 'Persons with Disabilities', val: vulnComponents.disabled_persons || 0, icon: Users },
              { label: 'Female-headed Households', val: vulnComponents.female_headed_hh || 0, icon: Home },
              { label: 'Kutcha / Vulnerable Houses', val: vulnComponents.kutcha_houses || 0, icon: Home },
              { label: 'Distance to Health Center', val: Math.min(1.0, (habitation.vuln_dist_health_m || 1000) / 10000.0), icon: MapPin },
            ].map((item, idx) => (
              <div key={idx}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '3px' }}>
                  <span style={{ color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <item.icon size={13} color="#94a3b8" />
                    {item.label}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>
                    {(item.val * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ width: '100%', height: '5px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, item.val * 100)}%`, height: '100%', background: '#38bdf8' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
