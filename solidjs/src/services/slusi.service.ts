/**
 * SLUSI Soil Data Service
 * Fetches government soil data (SHC WMS + SLUSI LCC) for a farm coordinate.
 */

import apiClient from '../lib/api-client';

// ---------------------------------------------------------------------------
// TypeScript interfaces
// ---------------------------------------------------------------------------

export interface SHCSoilProfile {
  // Nutrient values (kg/ha or ppm)
  nitrogen: number | null;
  phosphorus: number | null;
  potassium: number | null;
  sulfur: number | null;
  boron: number | null;
  iron: number | null;
  zinc: number | null;
  copper: number | null;
  manganese: number | null;
  organic_carbon: number | null;
  ph_level: number | null;
  electrical_conductivity: number | null;
  // Physical class values
  soil_depth_class: string | null;
  slope_class: string | null;
  erosion_class: string | null;
  soil_texture_class: string | null;
  land_capability_class: string | null;
  land_irrigability_class: string | null;
  hydrological_soil_group: string | null;
  // Metadata
  partial_data: boolean;
  wms_available: boolean;
  unavailable_styles: string[];
  fetched_at: string | null;
}

export interface LCCReport {
  state: string;
  district: string;
  report_no: string;
  year: number | null;
  total_area_ha: number | null;
  lcc_class_i: number | null;
  lcc_class_ii: number | null;
  lcc_class_iii: number | null;
  lcc_class_iv: number | null;
  lcc_class_v: number | null;
  lcc_class_vi: number | null;
  lcc_class_vii: number | null;
  lcc_class_viii: number | null;
  forest_area: number | null;
  miscellaneous_area: number | null;
  spatial_available: boolean;
  non_spatial_available: boolean;
  ingested_at: string;
}

export interface LCCSummary {
  dominant_class: string | null;
  total_area_ha: number | null;
  data_source: string;
  report_no: string | null;
  year: number | null;
  ingested_at: string | null;
}

export interface SoilLookupResponse {
  shc_profile: SHCSoilProfile;
  lcc_summary: LCCSummary | null;
  lcc_data_available: boolean;
  lcc_limitation_warning: string | null;
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

export class SLUSIService {
  /**
   * Fetch soil data for a GPS coordinate.
   * Calls GET /farms/soil-lookup/v2?lat=&lon=&state=&district=
   */
  static async fetchSoilLookup(
    lat: number,
    lon: number,
    state: string,
    district: string,
  ): Promise<SoilLookupResponse> {
    const response = await apiClient.get<SoilLookupResponse>(
      'farms/soil-lookup/v2',
      { params: { lat, lon, state, district } },
    );
    return response.data;
  }

  /**
   * Fetch LCC reports for a state/district.
   */
  static async getLCCReports(
    state: string,
    district: string,
    year?: number,
  ): Promise<LCCReport[]> {
    const params: Record<string, string | number> = { state, district };
    if (year !== undefined) params.year = year;
    const response = await apiClient.get<LCCReport[]>('slusi/lcc', { params });
    return response.data;
  }

  /**
   * Get microwatershed map URL for a state (returns the endpoint URL for use in <img>).
   */
  static getMicrowatersheddMapUrl(state: string): string {
    return `/api/v1/slusi/maps/${encodeURIComponent(state)}`;
  }
}

export const slusiService = SLUSIService;
export default SLUSIService;
