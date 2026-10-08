import React from 'react';
import { ShieldAlert, RefreshCw, Layers, Database, Activity } from 'lucide-react';

interface NavbarProps {
  district: string;
  activeScenarioName: string;
  isSimulating: boolean;
  onRefresh: () => void;
  onSeedData: () => void;
  activeTab: 'map' | 'priority' | 'capacity' | 'scenarios';
  setActiveTab: (tab: 'map' | 'priority' | 'capacity' | 'scenarios') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  district,
  activeScenarioName,
  isSimulating,
  onRefresh,
  onSeedData,
  activeTab,
  setActiveTab,
}) => {
  return (
    <header className="glass-panel" style={{ margin: '12px 16px', padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderRadius: '12px' }}>
      {/* Brand & District Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ background: 'linear-gradient(135deg, #ef4444, #f97316)', padding: '10px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 16px rgba(239, 68, 68, 0.4)' }}>
          <ShieldAlert size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #ffffff, #cbd5e1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Surakshit Basti
            </h1>
            <span className="badge badge-red">
              <span className="pulsing-dot-red" />
              MHA / NDRF SIH26191
            </span>
          </div>
          <p style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
            Pilot District: <strong style={{ color: '#f8fafc', textTransform: 'capitalize' }}>{district}</strong> &bull; Active Plan: <span style={{ color: '#38bdf8' }}>{activeScenarioName}</span>
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav style={{ display: 'flex', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
        <button
          onClick={() => setActiveTab('map')}
          className={activeTab === 'map' ? 'btn-primary' : 'btn-secondary'}
          style={{ fontSize: '0.82rem', padding: '6px 14px', border: 'none' }}
        >
          <Layers size={15} /> GIS Operations Map
        </button>
        <button
          onClick={() => setActiveTab('priority')}
          className={activeTab === 'priority' ? 'btn-primary' : 'btn-secondary'}
          style={{ fontSize: '0.82rem', padding: '6px 14px', border: 'none' }}
        >
          <Activity size={15} /> Action Priority Table
        </button>
        <button
          onClick={() => setActiveTab('capacity')}
          className={activeTab === 'capacity' ? 'btn-primary' : 'btn-secondary'}
          style={{ fontSize: '0.82rem', padding: '6px 14px', border: 'none' }}
        >
          <Database size={15} /> Relocation Capacity
        </button>
      </nav>

      {/* Action Controls & Provenance */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div className="provenance-pill" title="Data Origin Envelope">
          <span style={{ color: '#f59e0b' }}>●</span> DEMO_SYNTHETIC
        </div>

        <button
          onClick={onSeedData}
          className="btn-secondary"
          style={{ fontSize: '0.78rem', padding: '6px 12px' }}
          title="Reset & seed demo datasets"
        >
          <Database size={14} /> Re-Seed
        </button>

        <button
          onClick={onRefresh}
          disabled={isSimulating}
          className="btn-secondary"
          style={{ fontSize: '0.78rem', padding: '6px 12px' }}
          title="Refresh real-time data"
        >
          <RefreshCw size={14} className={isSimulating ? 'spin-anim' : ''} />
          {isSimulating ? 'Processing...' : 'Refresh'}
        </button>
      </div>
    </header>
  );
};
