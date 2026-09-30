/**
 * Toast Notification Component
 * Displays success, error, warning, and info messages
 */

import { createSignal, For, Show, onCleanup } from 'solid-js';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

// Global toast state
const [toasts, setToasts] = createSignal<Toast[]>([]);

/**
 * Add a toast notification
 */
export function showToast(type: ToastType, message: string, duration: number = 5000): void {
  const id = `toast-${Date.now()}-${Math.random()}`;
  const toast: Toast = { id, type, message, duration };
  
  setToasts(prev => [...prev, toast]);

  // Auto-remove after duration
  if (duration > 0) {
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }
}

/**
 * Remove a toast notification
 */
export function removeToast(id: string): void {
  setToasts(prev => prev.filter(t => t.id !== id));
}

/**
 * Toast Container Component
 */
export function ToastContainer() {
  return (
    <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      <For each={toasts()}>
        {(toast) => <ToastItem toast={toast} />}
      </For>
    </div>
  );
}

/**
 * Individual Toast Item
 */
function ToastItem(props: { toast: Toast }) {
  const [isVisible, setIsVisible] = createSignal(true);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => removeToast(props.toast.id), 300);
  };

  const getToastStyles = () => {
    const baseStyles = 'flex items-start gap-3 p-4 rounded-lg shadow-lg transition-all duration-300 transform';
    const visibilityStyles = isVisible() 
      ? 'translate-x-0 opacity-100' 
      : 'translate-x-full opacity-0';

    const typeStyles = {
      success: 'bg-green-50 border border-green-200 text-green-800',
      error: 'bg-red-50 border border-red-200 text-red-800',
      warning: 'bg-yellow-50 border border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border border-blue-200 text-blue-800',
    };

    return `${baseStyles} ${visibilityStyles} ${typeStyles[props.toast.type]}`;
  };

  const getIcon = () => {
    switch (props.toast.type) {
      case 'success':
        return (
          <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        );
      case 'info':
        return (
          <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
        );
    }
  };

  return (
    <div class={getToastStyles()} role="alert">
      {getIcon()}
      <div class="flex-1 text-sm font-medium">
        {props.toast.message}
      </div>
      <button
        onClick={handleClose}
        class="flex-shrink-0 ml-2 text-gray-400 hover:text-gray-600 transition-colors"
        aria-label="Close"
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  );
}

export default ToastContainer;
