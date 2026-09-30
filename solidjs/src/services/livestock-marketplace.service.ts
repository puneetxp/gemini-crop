/**
 * Livestock Marketplace Service
 * API integration for livestock marketplace listings and ROI calculations
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

// Types
export interface LivestockMarketplaceListing {
  id: number;
  livestock_id: number;
  farmer_id: number;
  listing_type: string; // sale, breeding_service, milk_production
  asking_price: number;
  current_age_months: number;
  current_weight_kg?: number;
  milk_production_liters_per_day?: number;
  breeding_history?: string;
  health_status: string;
  vaccination_status: string;
  total_investment: number;
  total_revenue: number;
  current_roi_percentage?: number;
  break_even_achieved: boolean;
  break_even_date?: string;
  projected_annual_profit?: number;
  location_state: string;
  location_district: string;
  farmer_contact_phone: string;
  farmer_contact_email?: string;
  listing_status: string;
  views_count: number;
  bedrock_analysis?: string;
  created_at: string;
  updated_at: string;
}

export interface LivestockListingFilters {
  species?: string;
  listing_type?: string;
  state?: string;
  district?: string;
  min_price?: number;
  max_price?: number;
  min_roi?: number;
  health_status?: string;
}

export interface LivestockListingsResponse {
  listings: LivestockMarketplaceListing[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ROICalculationRequest {
  species: string;
  purpose: string;
  purchase_price: number;
  current_age_months: number;
  total_investment: number;
  total_revenue: number;
  milk_production_liters_per_day?: number;
}

export interface ROICalculationResponse {
  current_roi_percentage: number;
  net_profit: number;
  break_even_achieved: boolean;
  break_even_date?: string;
  projected_annual_profit: number;
  monthly_costs: number;
  monthly_revenue: number;
  monthly_cash_flow: number;
  payback_period_months?: number;
  investment_summary: {
    total_investment: number;
    total_revenue: number;
    purchase_price: number;
    operating_costs: number;
  };
  recommendations?: string[];
}

export interface ROIReport {
  livestock_info: {
    species: string;
    breed: string;
    purpose: string;
    age_months: number;
  };
  financial_summary: {
    total_investment: number;
    total_revenue: number;
    net_profit: number;
    roi_percentage: number;
  };
  break_even_analysis: {
    achieved: boolean;
    date?: string;
    payback_period_months?: number;
  };
  cash_flow: {
    monthly_costs: number;
    monthly_revenue: number;
    monthly_profit: number;
  };
  projections: {
    annual_profit: number;
    five_year_profit: number;
  };
  recommendations: string[];
}

export class LivestockMarketplaceService {
  /**
   * Get livestock marketplace listings with filters and pagination
   */
  static async getListings(
    filters: LivestockListingFilters = {},
    page: number = 1,
    pageSize: number = 20
  ): Promise<LivestockListingsResponse> {
    const params: Record<string, string | number> = {
      page,
      page_size: pageSize,
    };

    // Add filters
    if (filters.species) params.species = filters.species;
    if (filters.listing_type) params.listing_type = filters.listing_type;
    if (filters.state) params.state = filters.state;
    if (filters.district) params.district = filters.district;
    if (filters.min_price) params.min_price = filters.min_price;
    if (filters.max_price) params.max_price = filters.max_price;
    if (filters.min_roi) params.min_roi = filters.min_roi;
    if (filters.health_status) params.health_status = filters.health_status;

    // Livestock marketplace listings endpoint not in registry, use direct URL
    const response = await apiClient.get<LivestockListingsResponse>(
      '/api/v1/livestock-marketplace/listings',
      {
        params,
        requiresAuth: false, // Public listings
        cache: true,
        cacheTTL: 60000, // 1 minute cache
      }
    );

    return response.data;
  }

  /**
   * Get listing detail
   */
  static async getListingDetail(listingId: number): Promise<LivestockMarketplaceListing> {
    // Livestock listing detail endpoint not in registry, use direct URL
    const response = await apiClient.get<LivestockMarketplaceListing>(
      `/api/v1/livestock-marketplace/listings/${listingId}`,
      {
        requiresAuth: false,
        cache: true,
        cacheTTL: 120000, // 2 minutes cache
      }
    );

    return response.data;
  }

  /**
   * Create livestock marketplace listing
   */
  static async createListing(listingData: Partial<LivestockMarketplaceListing>): Promise<LivestockMarketplaceListing> {
    // Livestock marketplace create endpoint not in registry, use direct URL
    const response = await apiClient.post<LivestockMarketplaceListing>(
      '/api/v1/livestock-marketplace/listings',
      listingData
    );
    // Clear listings cache after create
    apiClient.clearCacheByPattern(new RegExp('/livestock-marketplace/listings'));
    return response.data;
  }

  /**
   * Update livestock marketplace listing
   */
  static async updateListing(
    listingId: number,
    listingData: Partial<LivestockMarketplaceListing>
  ): Promise<LivestockMarketplaceListing> {
    // Livestock marketplace update endpoint not in registry, use direct URL
    const response = await apiClient.put<LivestockMarketplaceListing>(
      `/api/v1/livestock-marketplace/listings/${listingId}`,
      listingData
    );
    // Clear cache after update
    apiClient.clearCacheByPattern(new RegExp(`/livestock-marketplace/listings/${listingId}`));
    return response.data;
  }

  /**
   * Delete livestock marketplace listing
   */
  static async deleteListing(listingId: number): Promise<void> {
    // Livestock marketplace delete endpoint not in registry, use direct URL
    await apiClient.delete(`/api/v1/livestock-marketplace/listings/${listingId}`);
    // Clear cache after delete
    apiClient.clearCacheByPattern(new RegExp('/livestock-marketplace/listings'));
  }

  /**
   * Calculate ROI for livestock
   */
  static async calculateROI(request: ROICalculationRequest): Promise<ROICalculationResponse> {
    // Livestock ROI calculation endpoint not in registry, use direct URL
    const response = await apiClient.post<ROICalculationResponse>(
      '/api/v1/livestock-marketplace/calculate-roi',
      request
    );
    return response.data;
  }

  /**
   * Get comprehensive ROI report
   */
  static async getROIReport(listingId: number): Promise<ROIReport> {
    // Livestock ROI report endpoint not in registry, use direct URL
    const response = await apiClient.get<ROIReport>(
      `/api/v1/livestock-marketplace/listings/${listingId}/roi-report`,
      {
        requiresAuth: false,
        cache: true,
        cacheTTL: 300000, // 5 minutes cache
      }
    );
    return response.data;
  }
}
