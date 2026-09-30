/**
 * Lightweight IndexedDB client for offline storage and cache clearing.
 */

export const indexdb = {
  async The_clearData(): Promise<void> {
    if (typeof window === "undefined" || !window.indexedDB) return;
    try {
      window.indexedDB.deleteDatabase("rural_farming_db");
    } catch {
      // ignore
    }
  },
};
