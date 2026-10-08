import React from 'react';
import { FileSpreadsheet, Map, Share2 } from 'lucide-react';
import { api } from '../api/client';

interface ExportBarProps {
  activeScenarioId: string;
}

export const ExportBar: React.FC<ExportBarProps> = ({ activeScenarioId }) => {
  const handleExportCsv = () => {
    const url = api.getExportCsvUrl(activeScenarioId);
    window.open(url, '_blank');
  };

  const handleExportGeoJson = async () => {
    try {
      const data = await api.getAssignmentFlows(activeScenarioId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `relocation_flows_${activeScenarioId}.geojson`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '12px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '14px', flexWrap: 'wrap' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Share2 size={16} color="#38bdf8" />
        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f8fafc' }}>
          Decision Support Exports (Plan #{activeScenarioId})
        </span>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={handleExportCsv}
          className="btn-secondary"
          style={{ fontSize: '0.78rem', padding: '6px 12px' }}
        >
          <FileSpreadsheet size={14} color="#10b981" /> Export CSV Plan
        </button>

        <button
          onClick={handleExportGeoJson}
          className="btn-secondary"
          style={{ fontSize: '0.78rem', padding: '6px 12px' }}
        >
          <Map size={14} color="#38bdf8" /> Export GIS GeoJSON
        </button>
      </div>
    </div>
  );
};
