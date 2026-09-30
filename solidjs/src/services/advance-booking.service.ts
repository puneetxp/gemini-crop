/**
 * Advance Booking Service
 * Handles pre-harvest booking and quality verification operations
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

export interface QualityStandards {
  grade: string;
  size?: string;
  moisture_content?: number;
  organic_certified: boolean;
  defects_tolerance?: number;
  additional_specs?: Record<string, any>;
}

export interface ContractTerms {
  delivery_terms: string;
  penalty_late_delivery?: number;
  penalty_quality_failure?: number;
  cancellation_terms?: string;
  dispute_resolution?: string;
  additional_terms?: string;
}

export interface CreateAdvanceBookingRequest {
  listing_id: number;
  quantity_booked: number;
  price_per_unit: number;
  advance_payment_percent: number;
  expected_delivery_date: string;
  quality_standards: QualityStandards;
  contract_terms: ContractTerms;
}

export interface QualityVerificationRequest {
  verifier_type: 'platform' | 'third_party' | 'buyer';
  quality_grade: string;
  quality_metrics: Record<string, any>;
  photos?: string[];
  passed: boolean;
  notes?: string;
}

export interface PaymentMilestoneRequest {
  milestone_type: 'advance' | 'quality_check' | 'delivery' | 'final';
  payment_method?: string;
  transaction_id?: string;
}

export interface AdvanceBooking {
  id: number;
  listing_id: number;
  buyer_id: number;
  farmer_id: number;
  quantity_booked: number;
  price_per_unit: number;
  total_amount: number;
  advance_payment_percent: number;
  advance_payment_amount: number;
  booking_date: string;
  expected_delivery_date: string;
  status: string;
  quality_standards: QualityStandards;
  contract_terms: ContractTerms;
  created_at: string;
  updated_at: string;
}

export interface QualityVerification {
  id: number;
  booking_id: number;
  verification_date: string;
  verifier_type: string;
  quality_grade: string;
  quality_metrics: Record<string, any>;
  photos: string[];
  passed: boolean;
  notes?: string;
}

export interface PaymentMilestone {
  id: number;
  milestone_type: string;
  amount: number;
  due_date: string;
  paid_date?: string;
  status: string;
  payment_method?: string;
  transaction_id?: string;
}

export class AdvanceBookingService {
  /**
   * Create a new advance booking
   */
  static async createBooking(request: CreateAdvanceBookingRequest): Promise<any> {
    const url = buildUrl('advanceBooking', 'create');
    const response = await apiClient.post(url, request);
    return response;
  }

  /**
   * Get booking details
   */
  /** Raise a quality/delivery dispute; the booking moves to "disputed". */
  static async raiseDispute(
    bookingId: number,
    dispute: { dispute_reason: string; details?: string; photos?: string[] }
  ): Promise<{ success: boolean; message: string; booking: AdvanceBooking }> {
    const url = buildUrl('advanceBooking', 'dispute', { id: bookingId });
    const response = await apiClient.post(url, dispute);
    return response.data;
  }

  static async getBookingDetails(bookingId: number): Promise<{
    booking: AdvanceBooking;
    listing: any;
    payment_milestones: PaymentMilestone[];
    quality_verifications: QualityVerification[];
  }> {
    const url = buildUrl('advanceBooking', 'get', { id: bookingId });
    const response = await apiClient.get(url);
    return response.data;
  }

  /**
   * Update booking status
   */
  static async updateBookingStatus(
    bookingId: number,
    status: string,
    notes?: string
  ): Promise<any> {
    const url = buildUrl('advanceBooking', 'update', { id: bookingId });
    const response = await apiClient.put(url, {
      status,
      notes,
    });
    return response.data;
  }

  /**
   * Submit quality verification
   */
  static async submitQualityVerification(
    bookingId: number,
    verification: QualityVerificationRequest
  ): Promise<any> {
    const url = buildUrl('advanceBooking', 'qualityVerify', { id: bookingId });
    const response = await apiClient.post(
      url,
      verification
    );
    return response;
  }

  /**
   * Record payment milestone
   */
  static async recordPayment(
    bookingId: number,
    payment: PaymentMilestoneRequest
  ): Promise<any> {
    // Payment milestone endpoint not in registry, use direct URL
    const response = await apiClient.post(
      `/api/v1/marketplace/advance-bookings/${bookingId}/payments`,
      payment
    );
    return response.data;
  }

  /**
   * List bookings for current user
   */
  static async listBookings(role: 'buyer' | 'farmer', status?: string): Promise<{
    bookings: AdvanceBooking[];
    count: number;
  }> {
    const params = new URLSearchParams({ role });
    if (status) params.append('status', status);
    
    const url = buildUrl('advanceBooking', 'list');
    const response = await apiClient.get(`${url}?${params.toString()}`);
    return response.data;
  }

  /**
   * Upload quality verification photo
   */
  static async uploadPhoto(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    
    // TODO: Implement actual photo upload to S3 or local storage
    // For now, return a placeholder URL
    const url = buildUrl('upload', 'image');
    // No manual Content-Type: the browser must set multipart/form-data with its boundary.
    const response = await apiClient.post(url, formData);
    
    return response.data.url;
  }
}
