/**
 * Veterinary Doctors Service
 * API integration for the livestock doctor directory: add a doctor, find one
 * nearby, and connect with them by call / WhatsApp / email.
 */

import apiClient from '../lib/api-client';

export interface VeterinaryDoctor {
  id: number;
  name: string;
  clinic_name?: string;
  specialization?: string;
  species_supported?: string[];
  phone: string;
  whatsapp?: string;
  email?: string;
  location_state?: string;
  location_district?: string;
  address?: string;
  available_now: boolean;
  verified: boolean;
  rating: number;
  total_ratings: number;
  notes?: string;
  call_link?: string;
  whatsapp_link?: string;
  email_link?: string;
  created_at: string;
  updated_at: string;
}

export interface DoctorFilters {
  species?: string;
  state?: string;
  district?: string;
  available_only?: boolean;
  verified_only?: boolean;
}

export interface DoctorCreateInput {
  name: string;
  clinic_name?: string;
  specialization?: string;
  species_supported?: string[];
  phone: string;
  whatsapp?: string;
  email?: string;
  location_state?: string;
  location_district?: string;
  address?: string;
  available_now?: boolean;
  notes?: string;
}

export class VeterinaryDoctorsService {
  /**
   * Find livestock doctors, optionally filtered by species/location
   */
  static async list(filters: DoctorFilters = {}): Promise<VeterinaryDoctor[]> {
    const params: Record<string, string | number | boolean> = {};
    if (filters.species) params.species = filters.species;
    if (filters.state) params.state = filters.state;
    if (filters.district) params.district = filters.district;
    if (filters.available_only) params.available_only = filters.available_only;
    if (filters.verified_only) params.verified_only = filters.verified_only;

    const response = await apiClient.get<{ success: boolean; data: VeterinaryDoctor[]; total: number }>(
      '/veterinary/doctors',
      { params, requiresAuth: false }
    );

    return response.data.data;
  }

  /**
   * Get a single doctor's profile and connect links
   */
  static async get(doctorId: number): Promise<VeterinaryDoctor> {
    const response = await apiClient.get<{ success: boolean; data: VeterinaryDoctor }>(
      `/veterinary/doctors/${doctorId}`,
      { requiresAuth: false }
    );

    return response.data.data;
  }

  /**
   * Add a doctor to the directory
   */
  static async create(doctor: DoctorCreateInput): Promise<VeterinaryDoctor> {
    const response = await apiClient.post<{ success: boolean; data: VeterinaryDoctor }>(
      '/veterinary/doctors',
      doctor
    );
    apiClient.clearCacheByPattern(new RegExp('/veterinary/doctors'));
    return response.data.data;
  }

  /**
   * Update a doctor's directory entry
   */
  static async update(doctorId: number, doctor: Partial<DoctorCreateInput>): Promise<VeterinaryDoctor> {
    const response = await apiClient.put<{ success: boolean; data: VeterinaryDoctor }>(
      `/veterinary/doctors/${doctorId}`,
      doctor
    );
    apiClient.clearCacheByPattern(new RegExp('/veterinary/doctors'));
    return response.data.data;
  }

  /**
   * Remove a doctor from the directory
   */
  static async remove(doctorId: number): Promise<void> {
    await apiClient.delete(`/veterinary/doctors/${doctorId}`);
    apiClient.clearCacheByPattern(new RegExp('/veterinary/doctors'));
  }
}
