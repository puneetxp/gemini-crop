/**
 * Assistant Conversation Archive Service
 * Manages persistent storage of reset & historical assistant conversations in localStorage.
 * Enables farmers to restart sessions without losing their historical records,
 * and seamlessly restore past dialogues and proposals.
 */

import type { AssistProposal } from './assistant.service';

export interface ArchivedSession {
    id: string;
    title: string;
    createdAt: string;
    messageCount: number;
    preview: string;
    messages: any[];
    proposal?: AssistProposal | null;
    focusAnimalId?: number | null;
}

const ARCHIVE_STORAGE_KEY = 'cropsense_assistant_archives';
const MAX_ARCHIVES = 50;

export class AssistantArchiveService {
    /**
     * Retrieve all saved archived conversations in reverse chronological order
     */
    static getArchives(): ArchivedSession[] {
        try {
            const raw = localStorage.getItem(ARCHIVE_STORAGE_KEY);
            if (!raw) return [];
            const list: ArchivedSession[] = JSON.parse(raw);
            return Array.isArray(list) ? list.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()) : [];
        } catch {
            return [];
        }
    }

    /**
     * Generate an intelligent readable title for the session
     */
    static generateTitle(messages: any[], proposal?: AssistProposal | null): string {
        if (proposal) {
            const breed = proposal.fields?.breed ? String(proposal.fields.breed) : '';
            const species = proposal.fields?.species ? String(proposal.fields.species) : '';
            const price = proposal.fields?.purchase_price || proposal.fields?.price ? ` · ₹${Number(proposal.fields.purchase_price || proposal.fields.price).toLocaleString('en-IN')}` : '';
            const crop = proposal.fields?.crop_name ? String(proposal.fields.crop_name) : '';
            const farm = proposal.fields?.name ? String(proposal.fields.name) : '';

            if (breed || species) return `${breed || species} Registration${price}`;
            if (crop) return `Crop Plan: ${crop}`;
            if (farm) return `Farm Registration: ${farm}`;
            return `${proposal.entity.replace(/_/g, ' ').toUpperCase()} Proposal`;
        }

        // Use the first user message
        const firstUserMsg = messages.find((m) => m.role === 'user' && m.text && !m.text.startsWith('🎤'));
        if (firstUserMsg && firstUserMsg.text) {
            const clean = firstUserMsg.text.replace(/\s+/g, ' ').trim();
            return clean.length > 36 ? `${clean.slice(0, 36)}…` : clean;
        }

        const now = new Date();
        return `AgriSense Session · ${now.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`;
    }

    /**
     * Archive the current session
     */
    static archiveSession(messages: any[], proposal?: AssistProposal | null, focusAnimalId?: number | null): ArchivedSession | null {
        if (!messages || messages.length === 0) return null;

        const archives = this.getArchives();
        const id = `session_${Date.now()}`;
        const title = this.generateTitle(messages, proposal);
        
        // Find last message preview
        const lastMsg = messages[messages.length - 1];
        const preview = lastMsg?.text ? (lastMsg.text.length > 80 ? `${lastMsg.text.slice(0, 80)}…` : lastMsg.text) : 'Conversation turn completed.';

        const session: ArchivedSession = {
            id,
            title,
            createdAt: new Date().toISOString(),
            messageCount: messages.length,
            preview,
            // Strip out ephemeral blob URLs before persisting
            messages: messages.map(({ audioUrl, ...m }) => m),
            proposal: proposal || null,
            focusAnimalId: focusAnimalId || null,
        };

        const updated = [session, ...archives].slice(0, MAX_ARCHIVES);
        try {
            localStorage.setItem(ARCHIVE_STORAGE_KEY, JSON.stringify(updated));
        } catch {
            // Storage quota or restriction fallback
        }

        return session;
    }

    /**
     * Restore an archived session by ID
     */
    static restoreSession(id: string): ArchivedSession | null {
        const archives = this.getArchives();
        return archives.find((a) => a.id === id) || null;
    }

    /**
     * Delete an archived session
     */
    static deleteArchive(id: string): boolean {
        try {
            const archives = this.getArchives().filter((a) => a.id !== id);
            localStorage.setItem(ARCHIVE_STORAGE_KEY, JSON.stringify(archives));
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Clear all archives
     */
    static clearAll(): void {
        try {
            localStorage.removeItem(ARCHIVE_STORAGE_KEY);
        } catch {
            // ignore
        }
    }
}
