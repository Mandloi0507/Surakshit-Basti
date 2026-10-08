import React, { useEffect, useState, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { MapLibreMap } from './components/MapLibreMap';
import { PriorityTable } from './components/PriorityTable';
import { DetailDrawer } from './components/DetailDrawer';
import { CapacityVisualizer } from './components/CapacityVisualizer';
import { WhatIfPanel } from './components/WhatIfPanel';
import { ExportBar } from './components/ExportBar';
import { api } from './api/client';
import type { GeoJSONFeatureCollection, Habitation, Site } from './types';

export const App: React.FC = () => {
  const [district] = useState('wayanad');
  const [activeTab, setActiveTab] = useState<'map' | 'priority' | 'capacity' | 'scenarios'>('map');
  const [isLoading, setIsLoading] = useState(false);

  // Domain State
  const [cellsData, setCellsData] = useState<GeoJSONFeatureCollection | null>(null);
  const [habitationsData, setHabitationsData] = useState<GeoJSONFeatureCollection<Habitation> | null>(null);
  const [habitationsList, setHabitationsList] = useState<Habitation[]>([]);
  const [sitesData, setSitesData] = useState<GeoJSONFeatureCollection<Site> | null>(null);
  const [sitesList, setSitesList] = useState<Site[]>([]);
  const [flowData, setFlowData] = useState<GeoJSONFeatureCollection | null>(null);

  const [activeScenarioId, setActiveScenarioId] = useState<string>('scen_baseline_ilp');
  const [activeScenarioName, setActiveScenarioName] = useState<string>('Baseline ILP Relocation Plan');

  // Selected Entities for XAI inspection
  const [selectedHabitation, setSelectedHabitation] = useState<Habitation | null>(null);
  const [, setSelectedSite] = useState<Site | null>(null);

  // Data Loading Routine
  const loadDashboardData = useCallback(async (scenarioIdToLoad?: string) => {
    setIsLoading(true);
    try {
      const currentScenId = scenarioIdToLoad || activeScenarioId;

      // Parallel fetch
      const [cells, habsGeo, habsTable, sitesGeo, flows] = await Promise.all([
        api.getCells(district, undefined, 2500).catch(() => null),
        api.getHabitationsGeoJSON(district).catch(() => null),
        api.getPriorityTable(district).catch(() => []),
        api.getSitesGeoJSON(district).catch(() => null),
        api.getAssignmentFlows(currentScenId).catch(() => null),
      ]);

      if (cells) setCellsData(cells);
      if (habsGeo) setHabitationsData(habsGeo);
      if (habsTable) setHabitationsList(habsTable);
      if (sitesGeo) {
        setSitesData(sitesGeo);
        setSitesList(sitesGeo.features.map((f) => f.properties));
      }
      if (flows) setFlowData(flows);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [district, activeScenarioId]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Handle Simulation Complete
  const handleSimulationComplete = (newScenId: string, newScenName: string) => {
    setActiveScenarioId(newScenId);
    setActiveScenarioName(newScenName);
    loadDashboardData(newScenId);
  };

  // Handle Re-Seed
  const handleSeedData = async () => {
    if (!confirm('Re-seed deterministic demo dataset for Wayanad?')) return;
    setIsLoading(true);
    try {
      await api.seedDemoData(district);
      await loadDashboardData();
      alert('Demo data successfully re-seeded!');
    } catch (err: any) {
      alert(`Seed failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
      {/* Top Navbar */}
      <Navbar
        district={district}
        activeScenarioName={activeScenarioName}
        isSimulating={isLoading}
        onRefresh={() => loadDashboardData()}
        onSeedData={handleSeedData}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Content Area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '0 16px 16px', gap: '12px' }}>
        {activeTab === 'map' && (
          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 340px', gap: '14px', minHeight: '680px' }}>
            {/* GIS Map */}
            <div style={{ height: '100%', minHeight: '680px' }}>
              <MapLibreMap
                cellsGeoJSON={cellsData}
                habitationsGeoJSON={habitationsData}
                sitesGeoJSON={sitesData}
                flowGeoJSON={flowData}
                selectedHabitationId={selectedHabitation?.id || null}
                onSelectHabitation={(hab) => setSelectedHabitation(hab)}
                onSelectSite={(site) => setSelectedSite(site)}
              />
            </div>

            {/* Sidebar with What-If Simulation & Quick Stats */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <WhatIfPanel
                district={district}
                onSimulationComplete={handleSimulationComplete}
              />
              <ExportBar activeScenarioId={activeScenarioId} />
            </div>
          </div>
        )}

        {activeTab === 'priority' && (
          <div style={{ flex: 1, minHeight: '680px' }}>
            <PriorityTable
              habitations={habitationsList}
              selectedHabitationId={selectedHabitation?.id || null}
              onSelectHabitation={(hab) => setSelectedHabitation(hab)}
            />
          </div>
        )}

        {activeTab === 'capacity' && (
          <div style={{ flex: 1, minHeight: '680px' }}>
            <CapacityVisualizer
              sites={sitesList}
              onSelectSite={(site) => setSelectedSite(site)}
            />
          </div>
        )}
      </main>

      {/* Slide-in Detail Drawer for Explainable AI */}
      <DetailDrawer
        habitation={selectedHabitation}
        onClose={() => setSelectedHabitation(null)}
      />
    </div>
  );
};

export default App;
