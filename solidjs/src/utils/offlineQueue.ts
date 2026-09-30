/**
 * Offline Queue Utility
 * Manages queuing and syncing of actions performed while offline
 */

export interface QueuedAction {
  id: string;
  type: 'api-request';
  method: string;
  url: string;
  body?: any;
  headers?: Record<string, string>;
  timestamp: number;
  retries: number;
}

const QUEUE_KEY = 'offline-queue';
const MAX_RETRIES = 3;

/**
 * Add an action to the offline queue
 */
export function queueAction(
  method: string,
  url: string,
  body?: any,
  headers?: Record<string, string>
): void {
  try {
    const queue = getQueue();
    
    const action: QueuedAction = {
      id: generateId(),
      type: 'api-request',
      method,
      url,
      body,
      headers,
      timestamp: Date.now(),
      retries: 0,
    };

    queue.push(action);
    saveQueue(queue);

    console.log('[Offline Queue] Action queued:', action.id);
  } catch (error) {
    console.error('[Offline Queue] Error queuing action:', error);
  }
}

/**
 * Get all queued actions
 */
export function getQueue(): QueuedAction[] {
  try {
    const queueStr = localStorage.getItem(QUEUE_KEY);
    if (!queueStr) {
      return [];
    }
    return JSON.parse(queueStr);
  } catch (error) {
    console.error('[Offline Queue] Error reading queue:', error);
    return [];
  }
}

/**
 * Save queue to localStorage
 */
function saveQueue(queue: QueuedAction[]): void {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
  } catch (error) {
    console.error('[Offline Queue] Error saving queue:', error);
  }
}

/**
 * Process all queued actions
 */
export async function processQueue(): Promise<void> {
  if (!navigator.onLine) {
    console.log('[Offline Queue] Still offline, skipping queue processing');
    return;
  }

  const queue = getQueue();
  
  if (queue.length === 0) {
    console.log('[Offline Queue] Queue is empty');
    return;
  }

  console.log(`[Offline Queue] Processing ${queue.length} queued actions`);

  const remainingQueue: QueuedAction[] = [];

  for (const action of queue) {
    try {
      await processAction(action);
      console.log('[Offline Queue] Action processed successfully:', action.id);
    } catch (error) {
      console.error('[Offline Queue] Error processing action:', action.id, error);
      
      // Increment retry count
      action.retries++;

      // Keep in queue if under max retries
      if (action.retries < MAX_RETRIES) {
        remainingQueue.push(action);
      } else {
        console.warn('[Offline Queue] Max retries reached, discarding action:', action.id);
      }
    }
  }

  // Save remaining queue
  saveQueue(remainingQueue);

  if (remainingQueue.length > 0) {
    console.log(`[Offline Queue] ${remainingQueue.length} actions remaining in queue`);
  } else {
    console.log('[Offline Queue] All actions processed successfully');
  }
}

/**
 * Process a single queued action
 */
async function processAction(action: QueuedAction): Promise<void> {
  if (action.type !== 'api-request') {
    throw new Error(`Unknown action type: ${action.type}`);
  }

  const response = await fetch(action.url, {
    method: action.method,
    headers: {
      'Content-Type': 'application/json',
      ...action.headers,
    },
    body: action.body ? JSON.stringify(action.body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Clear all queued actions
 */
export function clearQueue(): void {
  try {
    localStorage.removeItem(QUEUE_KEY);
    console.log('[Offline Queue] Queue cleared');
  } catch (error) {
    console.error('[Offline Queue] Error clearing queue:', error);
  }
}

/**
 * Get queue size
 */
export function getQueueSize(): number {
  return getQueue().length;
}

/**
 * Generate a unique ID for queued actions
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Initialize offline queue processing
 * Call this when the app starts
 */
export function initOfflineQueue(): void {
  // Process queue when coming back online
  window.addEventListener('online', () => {
    console.log('[Offline Queue] Connection restored, processing queue');
    processQueue().catch((error) => {
      console.error('[Offline Queue] Error processing queue:', error);
    });
  });

  // Process queue on app start if online
  if (navigator.onLine) {
    processQueue().catch((error) => {
      console.error('[Offline Queue] Error processing queue on startup:', error);
    });
  }
}
