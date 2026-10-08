import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { GeoJSONFeatureCollection, Habitation, Site } from '../types';

interface MapProps {
  cellsGeoJSON: GeoJSONFeatureCollection | null;
  habitationsGeoJSON: GeoJSONFeatureCollection<Habitation> | null;
  sitesGeoJSON: GeoJSONFeatureCollection<Site> | null;
  flowGeoJSON: GeoJSONFeatureCollection | null;
  selectedHabitationId: string | null;
  onSelectHabitation: (hab: Habitation | null) => void;
  onSelectSite: (site: Site | null) => void;
}

const BASEMAP_OPTIONS = {
  dark: {
    name: 'Dark Gray Canvas',
    tiles: ['https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'],
    attribution: '&copy; Esri, HERE, Garmin, © OpenStreetMap contributors',
  },
  osm: {
    name: 'OpenStreetMap',
    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
    attribution: '&copy; OpenStreetMap contributors',
  },
  satellite: {
    name: 'Satellite Terrain',
    tiles: ['https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
    attribution: '&copy; Esri, Maxar, Earthstar Geographics',
  },
};

export const MapLibreMap: React.FC<MapProps> = ({
  cellsGeoJSON,
  habitationsGeoJSON,
  sitesGeoJSON,
  flowGeoJSON,
  selectedHabitationId,
  onSelectHabitation,
  onSelectSite,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  const [activeBasemap, setActiveBasemap] = useState<'dark' | 'osm' | 'satellite'>('dark');
  const [showCells, setShowCells] = useState(true);
  const [showHabitations, setShowHabitations] = useState(true);
  const [showSites, setShowSites] = useState(true);
  const [showFlows, setShowFlows] = useState(true);

  // Latest props stored in refs to avoid closure race conditions
  const cellsRef = useRef(cellsGeoJSON);
  const habsRef = useRef(habitationsGeoJSON);
  const sitesRef = useRef(sitesGeoJSON);
  const flowsRef = useRef(flowGeoJSON);

  useEffect(() => {
    cellsRef.current = cellsGeoJSON;
    habsRef.current = habitationsGeoJSON;
    sitesRef.current = sitesGeoJSON;
    flowsRef.current = flowGeoJSON;
  }, [cellsGeoJSON, habitationsGeoJSON, sitesGeoJSON, flowGeoJSON]);

  // Safe source updater
  const updateSource = useCallback((sourceId: string, data: GeoJSONFeatureCollection | null) => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    try {
      const src = map.getSource(sourceId) as maplibregl.GeoJSONSource | undefined;
      if (src && data) {
        src.setData(data as any);
      }
    } catch (e) {
      console.warn(`Could not update source ${sourceId}:`, e);
    }
  }, []);

  // Setup layers on map style load
  const setupLayers = useCallback((map: maplibregl.Map) => {
    // 1. Cells Source & Layer
    if (!map.getSource('cells-src')) {
      map.addSource('cells-src', {
        type: 'geojson',
        data: (cellsRef.current as any) || { type: 'FeatureCollection', features: [] },
      });
    }

    if (!map.getLayer('cells-fill')) {
      map.addLayer({
        id: 'cells-fill',
        type: 'fill',
        source: 'cells-src',
        paint: {
          'fill-color': [
            'match',
            ['get', 'hazard_class'],
            'Red',
            'rgba(239, 68, 68, 0.45)',
            'Amber',
            'rgba(245, 158, 11, 0.35)',
            'Green',
            'rgba(16, 185, 129, 0.20)',
            'rgba(100, 116, 139, 0.15)',
          ],
          'fill-outline-color': 'rgba(255, 255, 255, 0.08)',
        },
      });
    }

    // 2. Flows Source & Layer
    if (!map.getSource('flows-src')) {
      map.addSource('flows-src', {
        type: 'geojson',
        data: (flowsRef.current as any) || { type: 'FeatureCollection', features: [] },
      });
    }

    if (!map.getLayer('flows-lines')) {
      map.addLayer({
        id: 'flows-lines',
        type: 'line',
        source: 'flows-src',
        paint: {
          'line-color': '#38bdf8',
          'line-width': 2.5,
          'line-dasharray': [2, 1],
          'line-opacity': 0.85,
        },
      });
    }

    // 3. Habitations Source & Layer
    if (!map.getSource('habitations-src')) {
      map.addSource('habitations-src', {
        type: 'geojson',
        data: (habsRef.current as any) || { type: 'FeatureCollection', features: [] },
      });
    }

    if (!map.getLayer('habitations-points')) {
      map.addLayer({
        id: 'habitations-points',
        type: 'circle',
        source: 'habitations-src',
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['get', 'population'],
            100, 7,
            800, 15,
          ],
          'circle-color': [
            'match',
            ['get', 'bucket'],
            'Immediate', '#ef4444',
            'Short-term', '#f59e0b',
            'Medium-term', '#eab308',
            '#94a3b8',
          ],
          'circle-stroke-width': 2.5,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.9,
        },
      });
    }

    // 4. Sites Source & Layer
    if (!map.getSource('sites-src')) {
      map.addSource('sites-src', {
        type: 'geojson',
        data: (sitesRef.current as any) || { type: 'FeatureCollection', features: [] },
      });
    }

    if (!map.getLayer('sites-points')) {
      map.addLayer({
        id: 'sites-points',
        type: 'circle',
        source: 'sites-src',
        paint: {
          'circle-radius': 11,
          'circle-color': '#10b981',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#064e3b',
          'circle-opacity': 0.95,
        },
      });
    }

    // Interactivity
    map.on('click', 'habitations-points', (e: maplibregl.MapLayerMouseEvent) => {
      if (e.features && e.features[0]) {
        const props = e.features[0].properties as any;
        const habObj: Habitation = {
          ...props,
          vulnerability_breakdown_json: typeof props.vulnerability_breakdown_json === 'string' ? JSON.parse(props.vulnerability_breakdown_json) : props.vulnerability_breakdown_json,
          urgency_breakdown_json: typeof props.urgency_breakdown_json === 'string' ? JSON.parse(props.urgency_breakdown_json) : props.urgency_breakdown_json,
          decision_reasons_json: typeof props.decision_reasons_json === 'string' ? JSON.parse(props.decision_reasons_json) : props.decision_reasons_json,
        };
        onSelectHabitation(habObj);
      }
    });

    map.on('click', 'sites-points', (e: maplibregl.MapLayerMouseEvent) => {
      if (e.features && e.features[0]) {
        const props = e.features[0].properties as any;
        const siteObj: Site = {
          ...props,
          screening_reasons_json: typeof props.screening_reasons_json === 'string' ? JSON.parse(props.screening_reasons_json) : props.screening_reasons_json,
        };
        onSelectSite(siteObj);
      }
    });

    map.on('mouseenter', 'habitations-points', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'habitations-points', () => { map.getCanvas().style.cursor = ''; });
    map.on('mouseenter', 'sites-points', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'sites-points', () => { map.getCanvas().style.cursor = ''; });
  }, [onSelectHabitation, onSelectSite]);

  // Initialize Map instance
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const baseCfg = BASEMAP_OPTIONS[activeBasemap];

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'base-raster': {
            type: 'raster',
            tiles: baseCfg.tiles,
            tileSize: 256,
            attribution: baseCfg.attribution,
          },
        },
        layers: [
          {
            id: 'base-raster-layer',
            type: 'raster',
            source: 'base-raster',
            minzoom: 0,
            maxzoom: 20,
          },
        ],
      },
      center: [76.132, 11.685], // Wayanad district center
      zoom: 10.2,
      pitch: 30,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 100, unit: 'metric' }), 'bottom-left');

    map.on('load', () => {
      setupLayers(map);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [setupLayers, activeBasemap]);

  // Switch basemap raster tile URL without destroying entire map
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const baseCfg = BASEMAP_OPTIONS[activeBasemap];
    if (map.getSource('base-raster')) {
      // Re-set style to switch cleanly while preserving domain layers
      map.setStyle({
        version: 8,
        sources: {
          'base-raster': {
            type: 'raster',
            tiles: baseCfg.tiles,
            tileSize: 256,
            attribution: baseCfg.attribution,
          },
        },
        layers: [
          {
            id: 'base-raster-layer',
            type: 'raster',
            source: 'base-raster',
            minzoom: 0,
            maxzoom: 20,
          },
        ],
      });
      map.once('style.load', () => {
        setupLayers(map);
      });
    }
  }, [activeBasemap, setupLayers]);

  // Live update GeoJSON layers when props arrive
  useEffect(() => {
    updateSource('cells-src', cellsGeoJSON);
  }, [cellsGeoJSON, updateSource]);

  useEffect(() => {
    updateSource('habitations-src', habitationsGeoJSON);
  }, [habitationsGeoJSON, updateSource]);

  useEffect(() => {
    updateSource('sites-src', sitesGeoJSON);
  }, [sitesGeoJSON, updateSource]);

  useEffect(() => {
    updateSource('flows-src', flowGeoJSON);
  }, [flowGeoJSON, updateSource]);

  // Update Layer Visibilities
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('cells-fill')) {
      map.setLayoutProperty('cells-fill', 'visibility', showCells ? 'visible' : 'none');
    }
    if (map.getLayer('habitations-points')) {
      map.setLayoutProperty('habitations-points', 'visibility', showHabitations ? 'visible' : 'none');
    }
    if (map.getLayer('sites-points')) {
      map.setLayoutProperty('sites-points', 'visibility', showSites ? 'visible' : 'none');
    }
    if (map.getLayer('flows-lines')) {
      map.setLayoutProperty('flows-lines', 'visibility', showFlows ? 'visible' : 'none');
    }
  }, [showCells, showHabitations, showSites, showFlows]);

  // Highlight selected habitation
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !map.getLayer('habitations-points')) return;

    if (selectedHabitationId) {
      map.setPaintProperty('habitations-points', 'circle-stroke-color', [
        'case',
        ['==', ['get', 'id'], selectedHabitationId],
        '#38bdf8',
        '#ffffff',
      ]);
      map.setPaintProperty('habitations-points', 'circle-stroke-width', [
        'case',
        ['==', ['get', 'id'], selectedHabitationId],
        4.5,
        2.5,
      ]);
    } else {
      map.setPaintProperty('habitations-points', 'circle-stroke-color', '#ffffff');
      map.setPaintProperty('habitations-points', 'circle-stroke-width', 2.5);
    }
  }, [selectedHabitationId]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '600px', borderRadius: '16px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
      {/* Map Container */}
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

      {/* Floating Layer & Basemap Controls */}
      <div className="glass-panel" style={{ position: 'absolute', top: '16px', left: '16px', padding: '12px 16px', zIndex: 10, display: 'flex', flexDirection: 'column', gap: '10px', minWidth: '220px' }}>
        {/* Basemap Switcher */}
        <div>
          <h4 style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
            Basemap
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px' }}>
            {(['dark', 'osm', 'satellite'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setActiveBasemap(mode)}
                style={{
                  padding: '4px 6px',
                  borderRadius: '6px',
                  border: activeBasemap === mode ? '1px solid #38bdf8' : '1px solid rgba(255,255,255,0.1)',
                  background: activeBasemap === mode ? 'rgba(56, 189, 248, 0.2)' : 'rgba(0,0,0,0.3)',
                  color: activeBasemap === mode ? '#ffffff' : '#94a3b8',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                }}
              >
                {mode === 'dark' ? 'Dark' : mode === 'osm' ? 'OSM' : 'Satellite'}
              </button>
            ))}
          </div>
        </div>

        {/* GIS Layers */}
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '8px' }}>
          <h4 style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
            GIS Overlay Layers
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={showCells} onChange={(e) => setShowCells(e.target.checked)} />
              <span>Multi-Hazard Grid (Red/Amber/Green)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={showHabitations} onChange={(e) => setShowHabitations(e.target.checked)} />
              <span>Habitations (Urgency Priority)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={showSites} onChange={(e) => setShowSites(e.target.checked)} />
              <span>Candidate Relocation Sites</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={showFlows} onChange={(e) => setShowFlows(e.target.checked)} />
              <span>Relocation Assignment Flows</span>
            </label>
          </div>
        </div>
      </div>

      {/* Map Legend */}
      <div className="glass-panel" style={{ position: 'absolute', bottom: '24px', right: '16px', padding: '12px 18px', zIndex: 10, display: 'flex', gap: '16px', fontSize: '0.78rem' }}>
        <div>
          <div style={{ fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>Hazard Zones</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: 10, height: 10, background: '#ef4444', borderRadius: 2 }} /> Red (High Risk)</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: 10, height: 10, background: '#f59e0b', borderRadius: 2 }} /> Amber (Moderate)</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: 10, height: 10, background: '#10b981', borderRadius: 2 }} /> Green (Low Risk)</div>
        </div>
        <div style={{ borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: '14px' }}>
          <div style={{ fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>Relocation Priority</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: 10, height: 10, background: '#ef4444', borderRadius: '50%' }} /> Immediate Bucket</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: 10, height: 10, background: '#f59e0b', borderRadius: '50%' }} /> Short-term Bucket</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: 10, height: 10, background: '#10b981', borderRadius: '50%' }} /> Safe Candidate Site</div>
        </div>
      </div>
    </div>
  );
};
