/**
 * Crop photo diagnosis (Gemini multimodal) — /api/v1/vision/diagnose-crop
 */

import apiClient from '../lib/api-client';

export interface Diagnosis {
    disease_detected: boolean;
    category?: 'disease' | 'pest' | 'nutrient' | 'abiotic' | 'healthy' | 'unclear';
    crop_identified?: string;
    disease_name?: string;
    local_name?: string;
    scientific_name?: string;
    confidence?: number;
    severity?: string;
    affected_part?: string;
    symptoms_observed?: string[];
    possible_causes?: string[];
    look_alikes?: string[];
    treatment?: { cultural?: string[]; organic?: string[]; chemical?: string[] };
    prevention?: string[];
    urgency?: string;
    spread_risk?: string;
    better_photo_tip?: string;
    additional_notes?: string;
    safety?: { checked: boolean; removed: { suggestion: string; reason: string }[]; label_note: string };
    error?: string;
    model_used?: string;
    language?: string;
}

export interface DiagnosisRow {
    id: number;
    created_at: string;
    crop_name?: string;
    disease_name?: string;
    category?: string;
    severity?: string;
    urgency?: string;
    confidence?: number;
}

// Big phone photos are shrunk before upload: faster on rural networks, and plenty for the model
const MAX_SIDE = 1600;

export class DiagnosisService {
    static async diagnose(body: {
        image_base64: string;
        mime_type: string;
        crop_id?: number;
        crop_name?: string;
        lang: string;
    }): Promise<{ diagnosis: Diagnosis; id: number | null }> {
        const res = await apiClient.post<{ success: boolean; diagnosis: Diagnosis; id: number | null }>(
            '/vision/diagnose-crop',
            body,
            { timeout: 90000, retry: false },
        );
        return { diagnosis: res.data.diagnosis, id: res.data.id };
    }

    static async history(limit = 10): Promise<DiagnosisRow[]> {
        try {
            const res = await apiClient.get<{ success: boolean; data: DiagnosisRow[] }>(`/vision/diagnoses?limit=${limit}`, { cache: false });
            return res.data?.data || [];
        } catch {
            return [];
        }
    }

    /** Photo -> JPEG base64 (longest side <= 1600px) */
    static async prepareImage(file: File): Promise<{ base64: string; mime: string; previewUrl: string }> {
        const previewUrl = URL.createObjectURL(file);
        try {
            const bitmap = await createImageBitmap(file);
            const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
            const canvas = document.createElement('canvas');
            canvas.width = Math.round(bitmap.width * scale);
            canvas.height = Math.round(bitmap.height * scale);
            canvas.getContext('2d')!.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
            return { base64: dataUrl.split(',')[1] || '', mime: 'image/jpeg', previewUrl };
        } catch {
            // Browser can't decode it (e.g. some HEIC): send the original
            const dataUrl: string = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(String(reader.result));
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
            return { base64: dataUrl.split(',')[1] || '', mime: file.type || 'image/jpeg', previewUrl };
        }
    }
}
