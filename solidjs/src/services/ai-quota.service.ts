/**
 * AI Quota Service
 * Handles AI usage quota tracking and management
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

export interface QuotaStatus {
  user_id: number; // Integer user ID from users.id
  date: string;
  gps_enhanced_requests: number;
  pincode_requests: number;
  quota_limit: number;
  remaining_quota: number;
  quota_exceeded: boolean;
  next_reset: string;
}

export interface QuotaCheck {
  can_use_gps: boolean;
  remaining_quota: number;
  fallback_to_pincode: boolean;
  message: string;
}

export interface QuotaStatistics {
  total_users: number;
  total_gps_requests: number;
  total_pincode_requests: number;
  average_requests_per_user: number;
  date_range: {
    start_date: string;
    end_date: string;
  };
}

export class AIQuotaService {
  /**
   * Get current quota status for user
   */
  static async getQuotaStatus(userId: number): Promise<QuotaStatus> {
    const url = buildUrl('aiQuota', 'getStatus', { user_id: userId });
    const response = await apiClient.get<QuotaStatus>(url);
    return response.data;
  }

  /**
   * Check if user can make AI request
   */
  static async checkQuota(userId: number, hasGps: boolean = false): Promise<QuotaCheck> {
    const url = buildUrl('aiQuota', 'check');
    const response = await apiClient.post<QuotaCheck>(url, null, {
      params: { user_id: userId, has_gps: hasGps }
    });
    return response.data;
  }

  /**
   * Get usage statistics (admin only)
   */
  static async getStatistics(startDate: string, endDate: string): Promise<QuotaStatistics> {
    const url = buildUrl('aiQuota', 'statistics');
    const response = await apiClient.get<QuotaStatistics>(url, {
      params: { start_date: startDate, end_date: endDate }
    });
    return response.data;
  }

  /**
   * Reset daily quota (admin only)
   */
  static async resetDailyQuota(): Promise<{ users_reset: number; reset_time: string; message: string }> {
    const url = buildUrl('aiQuota', 'reset');
    const response = await apiClient.post<{ users_reset: number; reset_time: string; message: string }>(
      url
    );
    return response.data;
  }

  /**
   * Update quota limit for user (admin only)
   */
  static async updateQuotaLimit(userId: number, newLimit: number): Promise<QuotaStatus> {
    const url = buildUrl('aiQuota', 'updateLimit', { user_id: userId });
    const response = await apiClient.put<QuotaStatus>(url, null, {
      params: { new_limit: newLimit }
    });
    return response.data;
  }
}
