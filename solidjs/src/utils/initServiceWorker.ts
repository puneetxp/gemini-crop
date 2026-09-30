/**
 * Service Worker Initialization Utility
 * Registers the service worker and initializes push notifications
 */

import { notificationService } from '../services/notification.service';
import { initOfflineQueue, processQueue } from './offlineQueue';

export async function initServiceWorker(): Promise<void> {
  // Check if service workers are supported
  if (!('serviceWorker' in navigator)) {
    console.warn('[App] Service workers are not supported');
    return;
  }

  try {
    // Register service worker
    const registration = await notificationService.registerServiceWorker();
    console.log('[App] Service worker registered successfully');

    // Initialize offline queue
    initOfflineQueue();

    // Initialize notifications if permission already granted
    const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY;
    if (VAPID_PUBLIC_KEY) {
      await notificationService.initialize(VAPID_PUBLIC_KEY);
    }

    // Listen for service worker updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            console.log('[App] New service worker available');
            showUpdateNotification();
          }
        });
      }
    });

    // Handle controller change (new service worker activated)
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      console.log('[App] Service worker controller changed');
      // Reload the page to use the new service worker
      window.location.reload();
    });

    // Listen for messages from service worker
    navigator.serviceWorker.addEventListener('message', (event) => {
      console.log('[App] Message from service worker:', event.data);
      
      if (event.data && event.data.type === 'SYNC_QUEUE') {
        // Process offline queue when service worker requests sync
        processQueue().catch((error) => {
          console.error('[App] Error processing queue:', error);
        });
      }
    });

    // Register background sync if supported
    if ('sync' in registration) {
      try {
        await (registration as any).sync.register('sync-offline-queue');
        console.log('[App] Background sync registered');
      } catch (error) {
        console.warn('[App] Background sync registration failed:', error);
      }
    }

  } catch (error) {
    console.error('[App] Service worker registration failed:', error);
  }
}

function showUpdateNotification(): void {
  // Show a notification that an update is available
  const updateBanner = document.createElement('div');
  updateBanner.id = 'update-banner';
  updateBanner.className = 'fixed top-4 left-4 right-4 bg-blue-600 text-white p-4 rounded-lg shadow-lg z-50 flex items-center justify-between animate-slide-down';
  updateBanner.innerHTML = `
    <div class="flex items-center gap-3">
      <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      <div>
        <p class="font-medium">Update Available</p>
        <p class="text-sm text-blue-100">A new version of CropSense AI is ready.</p>
      </div>
    </div>
    <div class="flex gap-2 ml-4">
      <button id="update-button" class="px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-medium text-sm whitespace-nowrap">
        Update Now
      </button>
      <button id="dismiss-update" class="px-3 py-2 text-white hover:bg-blue-700 rounded-lg transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  `;

  document.body.appendChild(updateBanner);

  // Handle update button click
  const updateButton = document.getElementById('update-button');
  if (updateButton) {
    updateButton.addEventListener('click', () => {
      // Tell service worker to skip waiting
      if (navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
      }
      // The controllerchange event will trigger a reload
    });
  }

  // Handle dismiss button click
  const dismissButton = document.getElementById('dismiss-update');
  if (dismissButton) {
    dismissButton.addEventListener('click', () => {
      updateBanner.remove();
    });
  }

  // Auto-dismiss after 30 seconds
  setTimeout(() => {
    if (document.getElementById('update-banner')) {
      updateBanner.remove();
    }
  }, 30000);
}

/**
 * Request notification permission at appropriate time
 * Should be called after user interaction (e.g., after login, after first farm registration)
 */
export async function requestNotificationPermission(): Promise<boolean> {
  const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY;
  
  if (!VAPID_PUBLIC_KEY) {
    console.warn('[App] VAPID public key not configured');
    return false;
  }

  try {
    const success = await notificationService.setupNotifications(VAPID_PUBLIC_KEY);
    return success;
  } catch (error) {
    console.error('[App] Failed to request notification permission:', error);
    return false;
  }
}

/**
 * Check if notifications are enabled
 */
export function areNotificationsEnabled(): boolean {
  const state = notificationService.getPermissionState();
  return state.granted && state.supported;
}
