/**
 * Pest & Disease Service
 * Handles identification, treatment lookup, and risk alerts
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

export interface PestDiseaseRisk {
    type: 'pest' | 'disease';
    name: string;
    scientific_name?: string;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    confidence: number;
    description: string;
    symptoms: string[];
}

export interface Treatment {
    pest_disease_name: string;
    treatment_type: 'organic' | 'chemical' | 'preventive';
    description: string;
    instructions: string;
    safety_precautions: string;
}

export class PestDiseaseService {
    /**
     * Identify pest/disease from image or description
     */
    static async identify(data: { description?: string; image_url?: string }): Promise<PestDiseaseRisk[]> {
        const url = buildUrl('pestDisease', 'identify');
        const response = await apiClient.post<PestDiseaseRisk[]>(url, data);
        return response.data;
    }

    /**
     * Get treatments for a specific pest/disease
     */
    static async getTreatments(name: string): Promise<Treatment[]> {
        const url = buildUrl('pestDisease', 'treatments');
        const response = await apiClient.get<Treatment[]>(url, { params: { name } });
        return response.data;
    }

    /**
     * Get regional alerts for pests and diseases
     */
    static async getAlerts(lat: number, lon: number): Promise<any[]> {
        const url = buildUrl('pestDisease', 'alerts');
        const response = await apiClient.get<any[]>(url, { params: { latitude: lat, longitude: lon } });
        return response.data;
    }
}
