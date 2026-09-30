/**
 * Weather Service
 * Handles weather forecasts, severe alerts, and weather-based recommendations
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

export interface WeatherForecast {
    date: string;
    temp_min: number;
    temp_max: number;
    condition: string;
    icon: string;
    rainfall_prob: number;
}

export interface SevereAlert {
    alert_type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    date: string;
    message: string;
    recommendation: string;
}

export class WeatherService {
    /**
     * Get 7-day weather forecast for coordinates
     */
    static async getForecast(lat: number, lon: number): Promise<WeatherForecast[]> {
        const url = buildUrl('weather', 'forecast');
        const response = await apiClient.get<WeatherForecast[]>(url, {
            params: { latitude: lat, longitude: lon, days: 7 }
        });
        return response.data;
    }

    /**
     * Get active severe weather alerts
     */
    static async getSevereAlerts(lat: number, lon: number): Promise<SevereAlert[]> {
        const url = buildUrl('weather', 'severe');
        const response = await apiClient.get<SevereAlert[]>(url, {
            params: { latitude: lat, longitude: lon }
        });
        return response.data;
    }

    /**
     * Get planting recommendations based on weather
     */
    static async getPlantingRecommendations(lat: number, lon: number, cropType: string, season: string) {
        const url = buildUrl('weather', 'recommendations');
        const response = await apiClient.get<any>(`${url}/planting`, {
            params: { latitude: lat, longitude: lon, crop_type: cropType, season }
        });
        return response.data;
    }

    /**
     * Get irrigation schedule
     */
    static async getIrrigationSchedule(lat: number, lon: number, cropType: string, soilType: string) {
        const url = buildUrl('weather', 'recommendations');
        const response = await apiClient.get<any>(`${url}/irrigation-schedule`, {
            params: { latitude: lat, longitude: lon, crop_type: cropType, soil_type: soilType }
        });
        return response.data;
    }
}
