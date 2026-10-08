export interface FactorContributions {
  slope?: number;
  aspect?: number;
  hand_elevation?: number;
  drainage_proximity?: number;
  road_proximity?: number;
  wetness_flow?: number;
  land_cover?: number;
  historical_events?: number;
  rainfall_trigger?: number;
  [key: string]: number | undefined;
}

export interface CellProperties {
  id: string;
  district_id: string;
  slope_deg?: number;
  aspect_deg?: number;
  curvature?: number;
  flow_accum?: number;
  wetness_index?: number;
  hand_m?: number;
  dist_drainage_m?: number;
  dist_road_m?: number;
  lulc_class?: string;
  landslide_score: number;
  flood_score: number;
  flash_flood_score: number;
  coastal_score: number;
  structural_hazard: number;
  combined_hazard: number;
  hazard_class: "Red" | "Amber" | "Green" | string;
  factor_contributions_json: FactorContributions;
  data_origin: string;
}

export interface Habitation {
  id: string;
  district_id: string;
  name: string;
  population: number;
  households: number;
  vuln_children_u6: number;
  vuln_elderly_60p: number;
  vuln_disabled: number;
  vuln_female_head: number;
  vuln_kutcha: number;
  vuln_dist_health_m: number;
  vulnerability_index: number;
  hazard_score: number;
  structural_hazard: number;
  time_factor: number;
  raw_urgency_score: number;
  urgency_score: number;
  bucket: "Immediate" | "Short-term" | "Medium-term" | "NONE" | string;
  vulnerability_breakdown_json: Record<string, any>;
  urgency_breakdown_json: Record<string, any>;
  assigned_site_id: string | null;
  unassigned_reason: string | null;
  decision_reasons_json: Record<string, any>;
  data_origin: string;
}

export interface Site {
  id: string;
  district_id: string;
  name: string;
  tier: "temporary_shelter" | "permanent_site" | string;
  area_sqm: number;
  slope_deg: number;
  dist_road_m: number;
  dist_water_m: number;
  cap_land: number;
  cap_water: number;
  cap_sanitation: number;
  cap_road: number;
  cap_services: number;
  final_capacity: number;
  limiting_factor: "land" | "water" | "sanitation" | "road" | "services" | string;
  allocated_population: number;
  remaining_capacity: number;
  confidence_level: "high" | "medium" | "low" | string;
  screening_reasons_json: string[];
  data_origin: string;
}

export interface Scenario {
  id: string;
  district_id: string;
  name: string;
  description?: string;
  rainfall_multiplier: number;
  weight_overrides_json: Record<string, any>;
  site_adjustments_json: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Assignment {
  id: string;
  scenario_id: string;
  habitation_id: string;
  site_id: string | null;
  assigned_population: number;
  distance_km: number;
  routing_method: string;
  decision_rank: number;
  reasons_json: string[];
  unassigned_reason: string | null;
  solver_method: string;
  created_at: string;
}

export interface GeoJSONFeature<P = Record<string, any>> {
  type: "Feature";
  id: string;
  geometry: {
    type: "Point" | "Polygon" | "LineString";
    coordinates: any;
  };
  properties: P;
}

export interface GeoJSONFeatureCollection<P = Record<string, any>> {
  type: "FeatureCollection";
  features: GeoJSONFeature<P>[];
  total_count?: number;
  returned_count?: number;
  district_id?: string;
}
