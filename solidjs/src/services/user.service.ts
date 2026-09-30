/**
 * User Service
 * Handles user profile and security operations
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';
import type { User } from './auth.service';

export interface UserUpdateData {
    full_name?: string;
    email?: string;
    phone_number?: string;
    language_preference?: string;
}

export interface ChangePasswordData {
    previous_password: string;
    proposed_password: string;
}

export class UserService {
    /**
     * Get current user profile (with extra Firebase / Identity Platform attributes)
     */
    static async getProfile(): Promise<{ user: User; cognito_attributes: any }> {
        const url = buildUrl('users', 'getProfile');
        const response = await apiClient.get<{ user: User; cognito_attributes: any }>(url);
        return response.data;
    }

    /**
     * Update user profile
     */
    static async updateProfile(data: UserUpdateData): Promise<User> {
        const url = buildUrl('users', 'updateProfile');
        const response = await apiClient.put<User>(url, data);
        return response.data;
    }

    /**
     * Change user password
     */
    static async changePassword(data: ChangePasswordData): Promise<{ success: boolean; message: string }> {
        const url = buildUrl('users', 'changePassword');
        const response = await apiClient.post<{ success: boolean; message: string }>(url, data);
        return response.data;
    }

    /**
     * Enable MFA
     */
    static async enableMFA(): Promise<{ success: boolean; message: string }> {
        // Endpoints for MFA might need direct URL if not in registry
        const response = await apiClient.post<{ success: boolean; message: string }>('/api/v1/users/me/mfa/enable', {});
        return response.data;
    }

    /**
     * Disable MFA
     */
    static async disableMFA(): Promise<{ success: boolean; message: string }> {
        const response = await apiClient.post<{ success: boolean; message: string }>('/api/v1/users/me/mfa/disable', {});
        return response.data;
    }
}
