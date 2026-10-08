import React, { useState } from 'react';
import { Play, CloudRain, Cpu, Sliders, CheckCircle2, Zap } from 'lucide-react';
import { api } from '../api/client';

interface WhatIfPanelProps {
  district: string;
  onSimulationComplete: (scenarioId: string, scenarioName: string) => void;
}

export const WhatIfPanel: React.FC<WhatIfPanelProps> = ({
  district,
  onSimulationComplete,
}) => {
  const [scenarioName, setScenarioName] = useState('Monsoon Surge 1.5x');
  const [rainfallMultiplier, setRainfallMultiplier] = useState(1.5);
  const [solverMethod, setSolverMethod] = useState<'greedy' | 'ilp_ortools'>('greedy');
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);

  const handleRunSimulation = async () => {
    setIsExecuting(true);
    const startTime = performance.now();
    try {
      const res = await api.runScenario({
        district_id: district,
        name: scenarioName,
        rainfall_multiplier: rainfallMultiplier,
        solver_method: solverMethod,
      });
      const durationMs = Math.round(performance.now() - startTime);
      setLastResult({ ...res, execution_time_ms: durationMs });
      onSimulationComplete(res.scenario_id, scenarioName);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message || 'Unknown error'}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sliders size={16} color="#38bdf8" />
          What-If Scenario Simulation
        </h3>
        <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
          <Zap size={11} /> Fast Solver &lt; 5s
        </span>
      </div>

      {/* Scenario Name */}
      <div>
        <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
          Scenario Name
        </label>
        <input
          type="text"
          value={scenarioName}
          onChange={(e) => setScenarioName(e.target.value)}
          style={{
            width: '100%',
            padding: '7px 12px',
            background: 'rgba(0,0,0,0.3)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '6px',
            color: '#fff',
            fontSize: '0.82rem',
          }}
        />
      </div>

      {/* Rainfall Multiplier Slider */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
          <span style={{ color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <CloudRain size={14} color="#38bdf8" /> Rainfall Multiplier (Stress Test)
          </span>
          <strong style={{ color: rainfallMultiplier > 1.4 ? '#ef4444' : '#38bdf8', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
            {rainfallMultiplier.toFixed(1)}x
          </strong>
        </div>
        <input
          type="range"
          min="1.0"
          max="3.0"
          step="0.1"
          value={rainfallMultiplier}
          onChange={(e) => setRainfallMultiplier(parseFloat(e.target.value))}
          style={{ width: '100%', cursor: 'pointer', accentColor: rainfallMultiplier > 1.4 ? '#ef4444' : '#38bdf8' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b', marginTop: '2px' }}>
          <span>1.0x (Baseline)</span>
          <span>1.5x (Orange Alert)</span>
          <span>2.0x+ (Red Alert Surge)</span>
        </div>
      </div>

      {/* Solver Algorithm Selection */}
      <div>
        <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
          Assignment Optimization Solver
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setSolverMethod('greedy')}
            style={{
              padding: '8px',
              borderRadius: '8px',
              border: solverMethod === 'greedy' ? '1px solid #3b82f6' : '1px solid rgba(255,255,255,0.08)',
              background: solverMethod === 'greedy' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(0,0,0,0.2)',
              color: '#ffffff',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '2px',
            }}
          >
            <Cpu size={14} color={solverMethod === 'greedy' ? '#38bdf8' : '#94a3b8'} />
            Greedy (Fast Priority)
          </button>
          <button
            type="button"
            onClick={() => setSolverMethod('ilp_ortools')}
            style={{
              padding: '8px',
              borderRadius: '8px',
              border: solverMethod === 'ilp_ortools' ? '1px solid #8b5cf6' : '1px solid rgba(255,255,255,0.08)',
              background: solverMethod === 'ilp_ortools' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(0,0,0,0.2)',
              color: '#ffffff',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '2px',
            }}
          >
            <Zap size={14} color={solverMethod === 'ilp_ortools' ? '#c4b5fd' : '#94a3b8'} />
            OR-Tools CP-SAT (ILP)
          </button>
        </div>
      </div>

      {/* Execute Button */}
      <button
        onClick={handleRunSimulation}
        disabled={isExecuting}
        className="btn-primary"
        style={{ width: '100%', justifyContent: 'center', padding: '10px' }}
      >
        <Play size={16} />
        {isExecuting ? 'Simulating Dynamic Relocation...' : 'Execute What-If Relocation'}
      </button>

      {/* Results Snapshot */}
      {lastResult && (
        <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px', padding: '10px 12px', fontSize: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#6ee7b7', fontWeight: 700, marginBottom: '4px' }}>
            <CheckCircle2 size={14} /> Simulation Complete ({lastResult.execution_time_ms} ms)
          </div>
          <div style={{ color: '#cbd5e1' }}>
            Assigned: <strong style={{ color: '#ffffff' }}>{lastResult.total_assigned}</strong> habitations &bull; Unassigned: <strong style={{ color: '#fca5a5' }}>{lastResult.total_unassigned}</strong>
          </div>
        </div>
      )}
    </div>
  );
};
