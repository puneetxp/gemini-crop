/**
 * Crop Service
 * Handles crop management operations including planting and updates
 */

import apiClient from '../lib/api-client';

export interface SupportingCropInput {
  crop_name: string;
  variety?: string;
  area?: number;
}

export interface QuickPlantRequest {
  farm_id: number;
  plot_id: number | null;
  crop_name: string;
  variety?: string;
  season: string;
  area: number;
  planting_date: string;
  expected_harvest_date?: string;
  expected_yield?: number;
  market_price?: number;
  supporting_crops?: SupportingCropInput[];
}

export interface QuickPlantResponse {
  success: boolean;
  message: string;
  crop_ids: number[];
  supporting_crop_ids?: number[];
  total_area_planted: number;
}

export class CropService {
  /**
   * Quickly plant a crop to a specific plot or across the farm
   */
  static async quickPlant(data: QuickPlantRequest): Promise<QuickPlantResponse> {
    try {
      const response = await apiClient.post<QuickPlantResponse>('crops/quick-plant', data);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get all crops for the current user
   */
  static async getMyCrops(): Promise<any> {
    const response = await apiClient.get('/api/v1/crops/my-crops');
    return response.data;
  }
}

export default CropService;
