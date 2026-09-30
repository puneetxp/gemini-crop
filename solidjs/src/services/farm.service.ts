/**
 * Farm Service
 * Handles all farm management operations
 */

import apiClient from "../lib/api-client";
import { buildUrl } from "~/config/api-registry";

export interface Farm {
  id: number;
  farmer_id: number;
  name: string;
  state: string;
  district: string;
  village: string;
  pincode: string;
  address_line?: string;
  total_area_acres: number;
  latitude?: number;
  longitude?: number;
  primary_soil_type?: string;
  irrigation_type?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph_level?: number;
  organic_carbon?: number;
  electrical_conductivity?: number;
  sulfur?: number;
  zinc?: number;
  iron?: number;
  boron?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FarmCreate {
  name: string;
  state: string;
  district: string;
  village: string;
  pincode: string;
  address_line?: string;
  total_area_acres: number;
  latitude?: number;
  longitude?: number;
  primary_soil_type?: string;
  irrigation_type?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph_level?: number;
  organic_carbon?: number;
  electrical_conductivity?: number;
  sulfur?: number;
  zinc?: number;
  iron?: number;
  boron?: number;
  plots?: PlotCreate[];
}

export interface FarmUpdate {
  name?: string;
  state?: string;
  district?: string;
  village?: string;
  pincode?: string;
  address_line?: string;
  total_area_acres?: number;
  latitude?: number;
  longitude?: number;
  primary_soil_type?: string;
  irrigation_type?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph_level?: number;
  organic_carbon?: number;
  electrical_conductivity?: number;
  sulfur?: number;
  zinc?: number;
  iron?: number;
  boron?: number;
}

export interface PlotCreate {
  name: string;
  area_acres: number;
  soil_type?: string;
  irrigation_type?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph_level?: number;
  organic_carbon?: number;
  electrical_conductivity?: number;
  sulfur?: number;
  zinc?: number;
  iron?: number;
  boron?: number;
}

export interface FarmPlot {
  id: number;
  farm_id: number;
  plot_name: string;
  area: number;
  soil_type?: string;
  current_crop?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph_level?: number;
  organic_carbon?: number;
  electrical_conductivity?: number;
  sulfur?: number;
  zinc?: number;
  iron?: number;
  boron?: number;
  created_at: string;
  updated_at: string;
}

export interface FarmPlotCreate {
  farm_id: number;
  plot_name: string;
  area: number;
  soil_type?: string;
  current_crop?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph_level?: number;
  organic_carbon?: number;
  electrical_conductivity?: number;
  sulfur?: number;
  zinc?: number;
  iron?: number;
  boron?: number;
}

// Indian states and their districts
export const INDIAN_STATES = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
];

// Sample districts (in production, this would be a complete mapping)
export const DISTRICTS_BY_STATE: Record<string, string[]> = {
  "Punjab": [
    "Amritsar",
    "Bathinda",
    "Faridkot",
    "Fatehgarh Sahib",
    "Ferozepur",
    "Gurdaspur",
    "Hoshiarpur",
    "Jalandhar",
    "Kapurthala",
    "Ludhiana",
    "Mansa",
    "Moga",
    "Muktsar",
    "Pathankot",
    "Patiala",
    "Rupnagar",
    "Sangrur",
    "SAS Nagar",
    "SBS Nagar",
    "Tarn Taran",
  ],
  "Haryana": [
    "Ambala",
    "Bhiwani",
    "Charkhi Dadri",
    "Faridabad",
    "Fatehabad",
    "Gurugram",
    "Hisar",
    "Jhajjar",
    "Jind",
    "Kaithal",
    "Karnal",
    "Kurukshetra",
    "Mahendragarh",
    "Nuh",
    "Palwal",
    "Panchkula",
    "Panipat",
    "Rewari",
    "Rohtak",
    "Sirsa",
    "Sonipat",
    "Yamunanagar",
  ],
  "Maharashtra": [
    "Mumbai",
    "Pune",
    "Nagpur",
    "Nashik",
    "Aurangabad",
    "Solapur",
    "Kolhapur",
    "Ahmednagar",
    "Satara",
    "Sangli",
  ],
  "Karnataka": [
    "Bangalore",
    "Mysore",
    "Hubli",
    "Mangalore",
    "Belgaum",
    "Gulbarga",
    "Davangere",
    "Bellary",
    "Bijapur",
    "Shimoga",
  ],
  "Tamil Nadu": [
    "Chennai",
    "Coimbatore",
    "Madurai",
    "Tiruchirappalli",
    "Salem",
    "Tirunelveli",
    "Tiruppur",
    "Erode",
    "Vellore",
    "Thoothukudi",
  ],
  "Uttar Pradesh": [
    "Lucknow",
    "Kanpur",
    "Ghaziabad",
    "Agra",
    "Varanasi",
    "Meerut",
    "Allahabad",
    "Bareilly",
    "Aligarh",
    "Moradabad",
  ],
  "Rajasthan": [
    "Jaipur",
    "Jodhpur",
    "Kota",
    "Bikaner",
    "Ajmer",
    "Udaipur",
    "Bhilwara",
    "Alwar",
    "Bharatpur",
    "Sikar",
  ],
  "Gujarat": [
    "Ahmedabad",
    "Surat",
    "Vadodara",
    "Rajkot",
    "Bhavnagar",
    "Jamnagar",
    "Junagadh",
    "Gandhinagar",
    "Anand",
    "Mehsana",
  ],
};

export const SOIL_TYPES = [
  "Clay",
  "Sandy",
  "Loamy",
  "Black",
  "Red",
  "Alluvial",
  "Laterite",
];

export const IRRIGATION_TYPES = [
  "Rain-fed",
  "Canal",
  "Borewell",
  "Drip",
  "Sprinkler",
  "Mixed",
];

/** API plot (name / area_acres) -> app plot (plot_name / area); keeps the API names too */
const fromApiPlot = (p: any): FarmPlot => ({
  ...p,
  plot_name: p.plot_name ?? p.name,
  area: p.area ?? p.area_acres,
});

export class FarmService {
  /**
   * Create a new farm
   */
  static async createFarm(data: FarmCreate): Promise<Farm> {
    const url = buildUrl("farms", "create");
    
    // Ensure we don't send empty strings for optional enums
    const payload: any = { ...data };
    if (payload.primary_soil_type === "") delete payload.primary_soil_type;
    if (payload.irrigation_type === "") delete payload.irrigation_type;
    
    if (payload.plots && Array.isArray(payload.plots)) {
      payload.plots = payload.plots.map((p: any) => {
        const plot = { ...p };
        if (plot.soil_type === "") delete plot.soil_type;
        if (plot.irrigation_type === "") delete plot.irrigation_type;
        return plot;
      });
    }
    
    const response = await apiClient.post<Farm>(url, payload);
    return response.data;
  }

  /**
   * Get all farms for current user
   */
  static async getFarms(): Promise<Farm[]> {
    const url = buildUrl("farms", "list");
    const response = await apiClient.get<Farm[] | { farms: Farm[]; total: number }>(
      url,
      {
        cache: true,
        cacheTTL: 60000, // 1 minute cache
      },
    );
    // GET /farms returns a plain list; older responses wrapped it as { farms, total }.
    const data: any = response.data;
    return Array.isArray(data) ? data : (data?.farms ?? []);
  }

  /**
   * Get farm by ID
   */
  static async getFarm(id: number): Promise<Farm> {
    const url = buildUrl("farms", "get", { id });
    const response = await apiClient.get<Farm>(url, {
      cache: true,
      cacheTTL: 60000,
    });
    return response.data;
  }

  /**
   * Update farm
   */
  static async updateFarm(id: number, data: FarmUpdate): Promise<Farm> {
    const url = buildUrl("farms", "update", { id });
    const payload: any = { ...data };
    if (payload.primary_soil_type === "") delete payload.primary_soil_type;
    if (payload.irrigation_type === "") delete payload.irrigation_type;
    
    const response = await apiClient.put<Farm>(url, payload);
    // Clear farm cache after update
    apiClient.clearCacheByPattern(new RegExp(`/farms`));
    return response.data;
  }

  /**
   * Delete farm
   */
  static async deleteFarm(id: number): Promise<void> {
    const url = buildUrl("farms", "delete", { id });
    await apiClient.delete(url);
    // Clear farm cache after delete
    apiClient.clearCacheByPattern(new RegExp(`/farms`));
  }

  /**
   * Get plots for a farm
   */
  static async getFarmPlots(farmId: number): Promise<FarmPlot[]> {
    const url = buildUrl("farms", "plots", { id: farmId });
    const response = await apiClient.get<{ plots: any[]; total: number }>(url, {
      cache: true,
      cacheTTL: 60000,
    });
    // The API returns name / area_acres; the app reads plot_name / area
    return (response.data.plots || []).map(fromApiPlot);
  }

  /**
   * Create a new plot
   */
  static async createPlot(data: FarmPlotCreate): Promise<FarmPlot> {
    const url = buildUrl("farms", "plots", { id: data.farm_id });
    // The API's PlotCreate uses name / area_acres
    const { farm_id: _farmId, plot_name, area, current_crop: _crop, ...rest } = data as any;
    const payload: any = { ...rest, name: plot_name, area_acres: Number(area) };
    if (payload.soil_type === "") delete payload.soil_type;
    
    const response = await apiClient.post<any>(url, payload);
    // Clear farm plots cache after create
    apiClient.clearCacheByPattern(new RegExp(`/farms/${data.farm_id}/plots`));
    return fromApiPlot(response.data);
  }

  /**
   * Delete plot
   */
  static async deletePlot(farmId: number, plotId: number): Promise<void> {
    const url = buildUrl("farms", "deletePlot", { farm_id: farmId, id: plotId });
    await apiClient.delete(url);
    // Clear farm plots cache after delete
    apiClient.clearCacheByPattern(new RegExp(`/farms/${farmId}/plots`));
  }
}
export default FarmService;
