import axios from 'axios';
import type {
  CellProperties,
  Habitation,
  Site,
  Scenario,
  Assignment,
  GeoJSONFeatureCollection,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

export const api = {
  // Cells
  getCells: async (districtId = 'wayanad', hazardClass?: string, limit = 4000): Promise<GeoJSONFeatureCollection<CellProperties>> => {
    const res = await apiClient.get<GeoJSONFeatureCollection<CellProperties>>('/cells', {
      params: { district_id: districtId, hazard_class: hazardClass, limit },
    });
    return res.data;
  },

  // Habitations
  getHabitationsGeoJSON: async (districtId = 'wayanad'): Promise<GeoJSONFeatureCollection<Habitation>> => {
    const res = await apiClient.get<GeoJSONFeatureCollection<Habitation>>('/habitations', {
      params: { district_id: districtId },
    });
    return res.data;
  },

  getPriorityTable: async (districtId = 'wayanad'): Promise<Habitation[]> => {
    const res = await apiClient.get<Habitation[]>('/habitations/priority-table', {
      params: { district_id: districtId },
    });
    return res.data;
  },

  getHabitationDetail: async (id: string): Promise<Habitation> => {
    const res = await apiClient.get<Habitation>(`/habitations/${id}`);
    return res.data;
  },

  // Sites
  getSitesGeoJSON: async (districtId = 'wayanad'): Promise<GeoJSONFeatureCollection<Site>> => {
    const res = await apiClient.get<GeoJSONFeatureCollection<Site>>('/sites', {
      params: { district_id: districtId },
    });
    return res.data;
  },

  getSiteDetail: async (id: string): Promise<Site> => {
    const res = await apiClient.get<Site>(`/sites/${id}`);
    return res.data;
  },

  // Scenarios
  getScenarios: async (districtId = 'wayanad'): Promise<Scenario[]> => {
    const res = await apiClient.get<Scenario[]>('/scenarios', {
      params: { district_id: districtId },
    });
    return res.data;
  },

  runScenario: async (params: {
    district_id: string;
    name: string;
    rainfall_multiplier: number;
    solver_method: 'greedy' | 'ilp_ortools';
    weight_overrides?: Record<string, number>;
    site_adjustments?: Record<string, number>;
  }): Promise<any> => {
    const res = await apiClient.post('/scenarios/run', params);
    return res.data;
  },

  compareScenarios: async (scen1: string, scen2: string): Promise<any> => {
    const res = await apiClient.get(`/scenarios/${scen1}/compare/${scen2}`);
    return res.data;
  },

  // Assignments
  getAssignments: async (scenarioId: string): Promise<Assignment[]> => {
    const res = await apiClient.get<Assignment[]>('/assignments', {
      params: { scenario_id: scenarioId },
    });
    return res.data;
  },

  getAssignmentFlows: async (scenarioId: string): Promise<GeoJSONFeatureCollection> => {
    const res = await apiClient.get<GeoJSONFeatureCollection>('/assignments/export/geojson', {
      params: { scenario_id: scenarioId },
    });
    return res.data;
  },

  getExportCsvUrl: (scenarioId: string): string => {
    return `${API_BASE}/assignments/export/csv?scenario_id=${scenarioId}`;
  },

  // Seed
  seedDemoData: async (districtId = 'wayanad'): Promise<any> => {
    const res = await apiClient.post('/seed/demo', null, {
      params: { district_id: districtId },
    });
    return res.data;
  },
};
