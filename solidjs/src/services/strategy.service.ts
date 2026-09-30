/**
 * Annual Crop Strategy Service
 * API integration for crop strategy generation and management
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

// Types
export interface SeasonalRecommendation {
  recommended_crop: string;
  variety: string;
  expected_yield_per_acre: string;
  expected_profit_per_acre: number;
  investment_per_acre: number;
  planting_window: string;
  harvest_window: string;
  key_success_factors: string[];
  confidence_score: number;
}

export interface AnnualSummary {
  total_expected_profit_per_acre: number;
  total_investment_per_acre: number;
  roi_percentage: number;
  risk_level: string;
  sustainability_score: number;
}

export interface AlternativeOption {
  season: string;
  crop: string;
  profit_difference: number;
  risk_comparison: string;
}

export interface MonthlyAction {
  month: string;
  actions: string[];
}

export interface AnnualStrategy {
  farm_id: number;
  farm_name: string;
  location: string;
  kharif: SeasonalRecommendation;
  rabi: SeasonalRecommendation;
  zaid?: {
    recommended_crop: string | null;
    expected_profit_per_acre: number;
  };
  annual_summary: AnnualSummary;
  alternative_options: AlternativeOption[];
  monthly_action_plan: MonthlyAction[];
  generated_at: string;
}

export interface StrategyRequest {
  farm_id: number;
  previous_crops?: string;
  budget_per_acre?: number;
  preferred_crop?: string;
  custom_message?: string;
}

export interface SaveStrategyRequest {
  farm_id: number;
  strategy_data: AnnualStrategy;
  notes?: string;
}

export interface SavedStrategy {
  id: string;
  farm_id: number;
  year: number;
  kharif_crop: string;
  kharif_profit_estimate: number;
  rabi_crop: string;
  rabi_profit_estimate: number;
  zaid_crop?: string;
  zaid_profit_estimate?: number;
  total_annual_profit: number;
  status: string;
  is_active: boolean;
  generated_at: string;
}

export class StrategyService {
  /**
   * Generate annual crop strategy
   */
  static async generateStrategy(request: StrategyRequest): Promise<AnnualStrategy> {
    const url = buildUrl('crops', 'annualStrategy');
    const response = await apiClient.post<AnnualStrategy>(
      url,
      request,
      {
        cache: false,
        timeout: 45000, // 45 seconds for AI generation (Nova can take longer)
      }
    );
    return response.data;
  }

  /**
   * Save generated strategy
   */
  static async saveStrategy(request: SaveStrategyRequest): Promise<SavedStrategy> {
    const url = buildUrl('crops', 'saveStrategy');
    const response = await apiClient.post<SavedStrategy>(
      url,
      request
    );
    // Clear strategy cache after save
    apiClient.clearCacheByPattern(new RegExp(`/annual-strategy`));
    return response.data;
  }

  /**
   * Get saved strategies for a farm
   */
  static async getFarmStrategies(farmId: number): Promise<SavedStrategy[]> {
    const url = buildUrl('crops', 'listStrategies');
    const response = await apiClient.get<SavedStrategy[]>(
      url,
      {
        cache: true,
        cacheTTL: 120000, // 2 minutes cache
      }
    );
    return response.data;
  }

  /**
   * Get a specific saved strategy
   */
  static async getStrategy(strategyId: string): Promise<SavedStrategy> {
    const url = buildUrl('crops', 'getStrategy', { id: strategyId });
    const response = await apiClient.get<SavedStrategy>(
      url,
      {
        cache: true,
        cacheTTL: 300000, // 5 minutes cache
      }
    );
    return response.data;
  }

  /**
   * Update strategy status
   */
  static async updateStrategyStatus(
    strategyId: string,
    status: string
  ): Promise<SavedStrategy> {
    const url = buildUrl('crops', 'updateStatus', { id: strategyId });
    const response = await apiClient.put<SavedStrategy>(
      url,
      { status }
    );
    // Clear strategy cache after update
    apiClient.clearCacheByPattern(new RegExp(`/annual-strategy`));
    return response.data;
  }
}
