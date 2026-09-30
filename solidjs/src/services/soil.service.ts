/**
 * Soil & Fertilizer Service
 * Handles soil health, maps, testing, and fertilizer tracking
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

export interface SoilHealth {
    plot_id: number;
    last_test_date: string;
    ph_level?: number;
    nitrogen?: number;
    phosphorus?: number;
    potassium?: number;
    organic_carbon?: number;
    health_score: number;
}

export interface SoilMap {
    id: number;
    plot_id: number;
    layer_type: string;
    map_url: string;
    legend_data: any;
}

export interface FertilizerRecommendation {
    crop_type: string;
    growth_stage: string;
    recommended_fertilizers: Array<{
        name: string;
        dosage: string;
        timing: string;
        application_method: string;
    }>;
}

export class SoilService {
    /**
     * Get soil health for a plot
     */
    static async getSoilHealth(plotId: number): Promise<SoilHealth> {
        const url = buildUrl('soil', 'getHealth');
        const response = await apiClient.get<SoilHealth>(url.replace('{plot_id}', String(plotId)));
        return response.data;
    }

    /**
     * Get soil maps for a plot
     */
    static async getSoilMaps(plotId: number): Promise<SoilMap[]> {
        const url = buildUrl('soil', 'getMaps');
        const response = await apiClient.get<SoilMap[]>(url, { params: { plot_id: plotId } });
        return response.data;
    }

    /**
     * Get fertilizer recommendations
     */
    static async getFertilizerRecommendations(plotId: number): Promise<FertilizerRecommendation> {
        const url = buildUrl('soil', 'getRecommendations');
        const response = await apiClient.get<FertilizerRecommendation>(url, { params: { plot_id: plotId } });
        return response.data;
    }

    /**
     * Get fertilizer application history
     */
    static async getFertilizerHistory(plotId: number): Promise<any[]> {
        const url = buildUrl('fertilizer', 'getHistory');
        const response = await apiClient.get<any[]>(url.replace('{plot_id}', String(plotId)));
        return response.data;
    }

    /**
     * Upload soil test report (PDF)
     */
    static async uploadSoilReport(plotId: number, file: File): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('plot_id', String(plotId));

        // Direct URL as it might need specific multipart handling if not in client
        const response = await apiClient.post('/api/v1/soil/testing/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    }

    /**
     * Get soil moisture data
     */
    static async getSoilMoisture(state: string, district: string, limit: number = 10): Promise<any> {
        const url = buildUrl('soil', 'moisture');
        const response = await apiClient.get<any>(url, { params: { state, district, limit } });
        return response.data;
    }
}
