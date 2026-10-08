import React from 'react';
import { Database, ShieldCheck, MapPin, Droplets, Sparkles, Navigation, Layers } from 'lucide-react';
import type { Site } from '../types';

interface CapacityVisualizerProps {
  sites: Site[];
  onSelectSite: (site: Site) => void;
}

export const CapacityVisualizer: React.FC<CapacityVisualizerProps> = ({
  sites,
  onSelectSite,
}) => {
  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', overflowY: 'auto' }}>
      <div>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Database size={18} color="#10b981" />
          Multi-Resource Carrying Capacity (C_j = min(C_land, C_water, C_san, C_road, C_serv))
        </h3>
        <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>
          Real-time candidate relocation site capacity norms, GIS screening eligibility, and allocated population.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
        {sites.map((site) => {
          const fillPercent = site.final_capacity > 0 ? (site.allocated_population / site.final_capacity) * 100 : 0;
          const isFull = site.remaining_capacity <= 0;

          return (
            <div
              key={site.id}
              onClick={() => onSelectSite(site)}
              className="glass-panel"
              style={{
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                cursor: 'pointer',
                background: 'rgba(30, 41, 59, 0.45)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                transition: 'transform 0.15s ease, border-color 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.borderColor = 'rgba(16, 185, 129, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
              }}
            >
              {/* Site Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className={`badge ${site.tier === 'permanent_site' ? 'badge-blue' : 'badge-amber'}`}>
                      {site.tier.replace('_', ' ')}
                    </span>
                    <span className="badge badge-green">
                      <ShieldCheck size={12} /> {site.confidence_level} confidence
                    </span>
                  </div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff', marginTop: '6px' }}>{site.name}</h4>
                  <p style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>{site.id}</p>
                </div>

                {/* Final Capacity Number */}
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Carrying Capacity</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)' }}>
                    {site.final_capacity.toLocaleString()} <span style={{ fontSize: '0.75rem', color: '#64748b' }}>persons</span>
                  </div>
                </div>
              </div>

              {/* Live Allocation Fill Bar */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                  <span style={{ color: '#94a3b8' }}>
                    Allocated: <strong style={{ color: '#f8fafc' }}>{site.allocated_population}</strong> / {site.final_capacity}
                  </span>
                  <span style={{ color: isFull ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                    {isFull ? 'FULL' : `${site.remaining_capacity} remaining`}
                  </span>
                </div>
                <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(100, fillPercent)}%`,
                      height: '100%',
                      background: isFull ? '#ef4444' : 'linear-gradient(90deg, #10b981, #38bdf8)',
                    }}
                  />
                </div>
              </div>

              {/* 5-Resource Breakdown Grid */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '8px', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '4px', textAlign: 'center' }}>
                {[
                  { label: 'Land', val: site.cap_land, key: 'land', icon: Layers },
                  { label: 'Water', val: site.cap_water, key: 'water', icon: Droplets },
                  { label: 'Sanit.', val: site.cap_sanitation, key: 'sanitation', icon: Sparkles },
                  { label: 'Road', val: site.cap_road, key: 'road', icon: Navigation },
                  { label: 'Serv.', val: site.cap_services, key: 'services', icon: MapPin },
                ].map((res) => {
                  const isLimiting = site.limiting_factor === res.key;
                  return (
                    <div
                      key={res.key}
                      style={{
                        padding: '4px 2px',
                        borderRadius: '4px',
                        background: isLimiting ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
                        border: isLimiting ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid transparent',
                      }}
                    >
                      <div style={{ fontSize: '0.65rem', color: isLimiting ? '#fca5a5' : '#94a3b8' }}>{res.label}</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: isLimiting ? '#ef4444' : '#f8fafc' }}>
                        {res.val}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Limiting Factor Tag */}
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>
                  Limiting Constraint: <strong style={{ color: '#ef4444', textTransform: 'uppercase' }}>{site.limiting_factor}</strong>
                </span>
                <span style={{ color: '#64748b' }}>Area: {site.area_sqm.toLocaleString()} m²</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
