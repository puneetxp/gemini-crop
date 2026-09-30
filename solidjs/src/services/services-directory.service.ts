/**
 * Services Directory
 * Reads come from the generated islogin controller (every signed-in user sees
 * all services). Writes go to the role controller the user is allowed to use:
 *   admin            -> /isuper/service/            (any service)
 *   service_provider -> /service_provider/service/  (only services linked to them)
 */

import apiClient from '../lib/api-client';
import type { Service } from '../shared/Interface/Model/Service';
import { user } from '../stores/auth.store';

export type { Service };

export const SERVICE_CATEGORIES = ['vet', 'insurance', 'loan', 'shop', 'transport'] as const;
export type ServiceCategory = (typeof SERVICE_CATEGORIES)[number];

type WriteScope = 'isuper' | 'service_provider';

/** Which write controller this user may use, if any */
export function serviceWriteScope(): WriteScope | null {
    const type = user()?.user_type;
    if (type === 'admin') return 'isuper';
    if (type === 'service_provider') return 'service_provider';
    return null;
}

/** Can the signed-in user edit/delete this service? */
export function canManageService(s: Service): boolean {
    const scope = serviceWriteScope();
    if (scope === 'isuper') return true;
    return scope === 'service_provider' && s.user_id != null && s.user_id === user()?.id;
}

const clearCache = () => apiClient.clearCacheByPattern(new RegExp('/service/'));

export class ServicesDirectory {
    static async list(): Promise<Service[]> {
        const res = await apiClient.get<Service[]>('/islogin/service/', { cache: false });
        return res.data || [];
    }

    static async create(body: Partial<Service>): Promise<Service> {
        const scope = serviceWriteScope();
        if (!scope) throw new Error('Not allowed');
        const res = await apiClient.post<Service>(`/${scope}/service/`, body);
        clearCache();
        return res.data;
    }

    static async update(id: number, body: Partial<Service>): Promise<Service> {
        const scope = serviceWriteScope();
        if (!scope) throw new Error('Not allowed');
        const res = await apiClient.put<Service>(`/${scope}/service/${id}`, body);
        clearCache();
        return res.data;
    }

    static async remove(id: number): Promise<void> {
        const scope = serviceWriteScope();
        if (!scope) throw new Error('Not allowed');
        await apiClient.delete(`/${scope}/service/${id}`);
        clearCache();
    }
}
