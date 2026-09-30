/**
 * Assistant Service
 * Sends a voice recording or typed text to /voice/assist and gets back what
 * to do: open a menu option, a short reply, a question ("which animal?"), or
 * a record proposal the user approves before anything is saved.
 */

import apiClient from '../lib/api-client';

export interface AssistMatch {
    id: string;
    score: number;
}

export type AssistEntity = 'livestock' | 'livestock_health_record' | 'farm' | 'crop' | 'crop_expense' | 'marketplace_listing';

export interface AssistProposal {
    entity: AssistEntity;
    fields: Record<string, string | number>;
    summary: string;
}

export interface AssistResult {
    transcript: string;
    language: string;
    intent: 'navigate' | 'create' | 'answer' | 'clarify';
    confidence: number;
    auto_open: boolean;
    reply: string;
    matches: AssistMatch[];
    proposal: AssistProposal | null;
    animal_options: number[];
    vet_help: boolean;
    /** Required fields still empty in the proposal */
    missing?: string[];
    /** Guided form: the field asked about next, quick replies for it, and progress */
    step?: string | null;
    step_options?: string[];
    steps?: string[];
    steps_done?: number;
    fallback?: boolean;
    /** Small data table when answering about the farmer's own data */
    table?: AssistTable | null;
}

export interface AssistTable {
    title: string;
    columns: string[];
    rows: string[][];
}

export interface AssistRequest {
    audio_base64?: string;
    mime_type?: string;
    /** Recording length in ms (goes to the voice log) */
    duration_ms?: number;
    text?: string;
    lang: string;
    menu: { id: string; label: string }[];
    animals: { id: number; label: string }[];
    /** The farmer's farms and crops, so a new crop / expense / listing can target one */
    farms?: { id: number; label: string }[];
    crops?: { id: number; label: string }[];
    history: { role: 'user' | 'assistant'; text: string }[];
    focus_animal_id?: number | null;
    /** Guided form filling: the AI updates `draft` from the conversation */
    task?: 'add_livestock';
    draft?: Record<string, unknown>;
    /** Plain-text summary of the farmer's farms, crops, livestock and figures */
    context?: string;
}

export type Option = { id: number; label: string };

export class AssistantService {
    /** The farmer's crops as picker options, e.g. "Wheat (Lok-1) · Green Valley / Plot B #42" */
    static async cropOptions(): Promise<Option[]> {
        try {
            const res = await apiClient.get<any>('/api/v1/crops/my-crops', { cache: true, cacheTTL: 60000 });
            const list: any[] = res.data?.crops || (Array.isArray(res.data) ? res.data : []);
            return list
                .filter((c) => c.status !== 'harvested' && c.crop_role !== 'supporting')
                .map((c) => ({
                    id: Number(c.id),
                    label: `${c.crop_name}${c.crop_variety ? ` (${c.crop_variety})` : ''} · ${[c.farm_name, c.plot_name].filter(Boolean).join(' / ')} #${c.id}`,
                }));
        } catch {
            return [];
        }
    }

    static async assist(body: AssistRequest): Promise<AssistResult> {
        const response = await apiClient.post<{ success: boolean; data: AssistResult }>('/voice/assist', body);
        return response.data.data;
    }

    /** Recording blob -> base64 (no data: prefix) */
    /** Request fields for a recorded clip */
    static async audioFields(clip: { blob: Blob; durationMs: number }) {
        return {
            audio_base64: await AssistantService.blobToBase64(clip.blob),
            mime_type: clip.blob.type || 'audio/webm',
            duration_ms: Math.round(clip.durationMs),
        };
    }

    /** The server's reason for a failed call, for showing under the generic error */
    static errorReason(err: any): string {
        const detail = err?.response?.data?.detail ?? err?.data?.detail ?? err?.detail;
        const text = typeof detail === 'string' ? detail : err?.message;
        return typeof text === 'string' ? text.slice(0, 200) : '';
    }

    static blobToBase64(blob: Blob): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(String(reader.result).split(',')[1] || '');
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
}
