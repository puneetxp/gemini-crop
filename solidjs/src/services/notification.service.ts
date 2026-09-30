/**
 * Notification Service
 * Handles web push notifications, service worker registration, and permission management
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

export interface NotificationPermissionState {
  granted: boolean;
  denied: boolean;
  prompt: boolean;
  supported: boolean;
}

export interface PushSubscriptionData {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

export interface NotificationPayload {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  tag?: string;
  url?: string;
  type?: 'buyer_interest' | 'strategy_reminder' | 'weather_alert' | 'harvest_reminder' | 'general';
  id?: string;
  requireInteraction?: boolean;
  actions?: Array<{
    action: string;
    title: string;
    icon?: string;
  }>;
}

class NotificationService {
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null;
  private pushSubscription: PushSubscription | null = null;

  /**
   * Check if push notifications are supported
   */
  isSupported(): boolean {
    return (
      'serviceWorker' in navigator &&
      'PushManager' in window &&
      'Notification' in window
    );
  }

  /**
   * Get current notification permission state
   */
  getPermissionState(): NotificationPermissionState {
    if (!this.isSupported()) {
      return {
        granted: false,
        denied: false,
        prompt: false,
        supported: false,
      };
    }

    const permission = Notification.permission;
    return {
      granted: permission === 'granted',
      denied: permission === 'denied',
      prompt: permission === 'default',
      supported: true,
    };
  }

  /**
   * Register service worker
   */
  async registerServiceWorker(): Promise<ServiceWorkerRegistration> {
    if (!this.isSupported()) {
      throw new Error('Service workers are not supported in this browser');
    }

    try {
      // Register the service worker
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });

      console.log('[Notification Service] Service worker registered:', registration);

      // Wait for the service worker to be ready
      await navigator.serviceWorker.ready;

      this.serviceWorkerRegistration = registration;

      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              console.log('[Notification Service] New service worker available');
              // Could show update notification here
            }
          });
        }
      });

      return registration;
    } catch (error) {
      console.error('[Notification Service] Service worker registration failed:', error);
      throw error;
    }
  }

  /**
   * Request notification permission from user
   */
  async requestPermission(): Promise<NotificationPermission> {
    if (!this.isSupported()) {
      throw new Error('Notifications are not supported in this browser');
    }

    try {
      const permission = await Notification.requestPermission();
      console.log('[Notification Service] Permission result:', permission);
      return permission;
    } catch (error) {
      console.error('[Notification Service] Permission request failed:', error);
      throw error;
    }
  }

  /**
   * Subscribe to push notifications
   */
  async subscribeToPush(vapidPublicKey: string): Promise<PushSubscription> {
    if (!this.serviceWorkerRegistration) {
      await this.registerServiceWorker();
    }

    if (!this.serviceWorkerRegistration) {
      throw new Error('Service worker not registered');
    }

    try {
      // Check if already subscribed
      let subscription = await this.serviceWorkerRegistration.pushManager.getSubscription();

      if (!subscription) {
        // Create new subscription
        subscription = await this.serviceWorkerRegistration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey),
        });

        console.log('[Notification Service] Push subscription created:', subscription);
      } else {
        console.log('[Notification Service] Already subscribed to push:', subscription);
      }

      this.pushSubscription = subscription;
      return subscription;
    } catch (error) {
      console.error('[Notification Service] Push subscription failed:', error);
      throw error;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribeFromPush(): Promise<boolean> {
    if (!this.pushSubscription) {
      const registration = await navigator.serviceWorker.ready;
      this.pushSubscription = await registration.pushManager.getSubscription();
    }

    if (this.pushSubscription) {
      try {
        const result = await this.pushSubscription.unsubscribe();
        console.log('[Notification Service] Unsubscribed from push:', result);
        this.pushSubscription = null;
        return result;
      } catch (error) {
        console.error('[Notification Service] Unsubscribe failed:', error);
        throw error;
      }
    }

    return false;
  }

  /**
   * Get current push subscription
   */
  async getPushSubscription(): Promise<PushSubscription | null> {
    if (!this.serviceWorkerRegistration) {
      const registration = await navigator.serviceWorker.ready;
      this.serviceWorkerRegistration = registration;
    }

    return await this.serviceWorkerRegistration.pushManager.getSubscription();
  }

  /**
   * Send subscription to backend
   */
  async sendSubscriptionToBackend(subscription: PushSubscription): Promise<void> {
    const subscriptionData = this.subscriptionToJSON(subscription);

    try {
      const url = buildUrl('notifications', 'subscribe');
      await apiClient.post(url, subscriptionData);
      console.log('[Notification Service] Subscription sent to backend');
    } catch (error) {
      console.error('[Notification Service] Failed to send subscription:', error);
      throw error;
    }
  }

  /**
   * Remove subscription from backend
   */
  async removeSubscriptionFromBackend(subscription: PushSubscription): Promise<void> {
    const subscriptionData = this.subscriptionToJSON(subscription);

    try {
      const url = buildUrl('notifications', 'unsubscribe');
      await apiClient.post(url, subscriptionData);
      console.log('[Notification Service] Subscription removed from backend');
    } catch (error) {
      console.error('[Notification Service] Failed to remove subscription:', error);
      throw error;
    }
  }

  /**
   * Ask the backend to push a test notification to this user's subscribed browsers
   */
  async sendServerTestNotification(): Promise<{ sent: number; removed: number; failed: number }> {
    const url = buildUrl('notifications', 'test');
    const response = await apiClient.post(url, {});
    return response.data;
  }

  /**
   * Show local notification (for testing or immediate feedback)
   */
  async showLocalNotification(payload: NotificationPayload): Promise<void> {
    if (!this.serviceWorkerRegistration) {
      await this.registerServiceWorker();
    }

    if (!this.serviceWorkerRegistration) {
      throw new Error('Service worker not registered');
    }

    const permission = this.getPermissionState();
    if (!permission.granted) {
      throw new Error('Notification permission not granted');
    }

    try {
      await this.serviceWorkerRegistration.showNotification(payload.title, {
        body: payload.body,
        icon: payload.icon || '/icon-192.png',
        badge: payload.badge || '/badge-72.png',
        tag: payload.tag || 'local-notification',
        requireInteraction: payload.requireInteraction || false,
        data: {
          url: payload.url || '/',
          type: payload.type || 'general',
          id: payload.id,
          timestamp: Date.now(),
        },
        ...(payload.actions && { actions: payload.actions }),
        vibrate: [200, 100, 200],
      } as NotificationOptions);

      console.log('[Notification Service] Local notification shown');
    } catch (error) {
      console.error('[Notification Service] Failed to show notification:', error);
      throw error;
    }
  }

  /**
   * Initialize notification system
   * Registers service worker and requests permission if needed
   */
  async initialize(vapidPublicKey?: string): Promise<boolean> {
    try {
      // Check support
      if (!this.isSupported()) {
        console.warn('[Notification Service] Push notifications not supported');
        return false;
      }

      // Register service worker
      await this.registerServiceWorker();

      // Check current permission
      const permissionState = this.getPermissionState();

      if (permissionState.granted && vapidPublicKey) {
        // Already granted, subscribe to push
        const subscription = await this.subscribeToPush(vapidPublicKey);
        await this.sendSubscriptionToBackend(subscription);
        return true;
      }

      return permissionState.granted;
    } catch (error) {
      console.error('[Notification Service] Initialization failed:', error);
      return false;
    }
  }

  /**
   * Complete notification setup flow
   * Requests permission, subscribes to push, and sends to backend
   */
  async setupNotifications(vapidPublicKey: string): Promise<boolean> {
    if (!vapidPublicKey) {
      throw new Error('Push notifications are not configured (VITE_VAPID_PUBLIC_KEY is missing)');
    }

    try {
      // Request permission
      const permission = await this.requestPermission();

      if (permission !== 'granted') {
        console.log('[Notification Service] Permission denied');
        return false;
      }

      // Subscribe to push
      const subscription = await this.subscribeToPush(vapidPublicKey);

      // Send to backend
      await this.sendSubscriptionToBackend(subscription);

      console.log('[Notification Service] Notifications setup complete');
      return true;
    } catch (error) {
      console.error('[Notification Service] Setup failed:', error);
      throw error;
    }
  }

  /**
   * Disable notifications
   * Unsubscribes from push and removes from backend
   */
  async disableNotifications(): Promise<boolean> {
    try {
      const subscription = await this.getPushSubscription();

      if (subscription) {
        await this.removeSubscriptionFromBackend(subscription);
        await this.unsubscribeFromPush();
      }

      console.log('[Notification Service] Notifications disabled');
      return true;
    } catch (error) {
      console.error('[Notification Service] Failed to disable notifications:', error);
      return false;
    }
  }

  /**
   * Helper: Convert VAPID key to Uint8Array
   */
  private urlBase64ToUint8Array(base64String: string): BufferSource {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
  }

  /**
   * Helper: Convert subscription to JSON
   */
  private subscriptionToJSON(subscription: PushSubscription): PushSubscriptionData {
    const keys = subscription.getKey('p256dh');
    const auth = subscription.getKey('auth');

    return {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: keys ? this.arrayBufferToBase64(keys) : '',
        auth: auth ? this.arrayBufferToBase64(auth) : '',
      },
    };
  }

  /**
   * Helper: Convert ArrayBuffer to Base64
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }
}

// Export singleton instance
export const notificationService = new NotificationService();
