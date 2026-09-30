/**
 * useAsync Hook
 * Manages async operations with loading, error, and data states
 */

import { createSignal, createEffect, onCleanup } from 'solid-js';
import type { ApiError } from '../lib/api-client';
import { showToast } from '../components/ui/Toast';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | Error | null;
}

export interface UseAsyncOptions {
  showSuccessToast?: boolean;
  successMessage?: string;
  showErrorToast?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: ApiError | Error) => void;
}

/**
 * Hook for managing async operations
 */
export function useAsync<T>(
  asyncFunction: (...args: any[]) => Promise<T>,
  options: UseAsyncOptions = {}
) {
  const [data, setData] = createSignal<T | null>(null);
  const [loading, setLoading] = createSignal(false);
  const [error, setError] = createSignal<ApiError | Error | null>(null);

  const execute = async (...args: any[]) => {
    setLoading(true);
    setError(null);

    try {
      const result = await asyncFunction(...args);
      setData(() => result);

      // Show success toast if enabled
      if (options.showSuccessToast) {
        showToast('success', options.successMessage || 'Operation completed successfully');
      }

      // Call success callback
      if (options.onSuccess) {
        options.onSuccess(result);
      }

      return result;
    } catch (err: any) {
      const errorObj = err as ApiError | Error;
      setError(errorObj);

      // Show error toast if enabled (default: true)
      if (options.showErrorToast !== false) {
        const message = 'message' in errorObj ? errorObj.message : 'An error occurred';
        showToast('error', message);
      }

      // Call error callback
      if (options.onError) {
        options.onError(errorObj);
      }

      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setData(null);
    setError(null);
    setLoading(false);
  };

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
}

/**
 * Hook for auto-executing async operations on mount
 */
export function useAsyncEffect<T>(
  asyncFunction: () => Promise<T>,
  options: UseAsyncOptions = {}
) {
  const asyncState = useAsync(asyncFunction, options);

  createEffect(() => {
    asyncState.execute();
  });

  return asyncState;
}

/**
 * Hook for managing form submissions
 */
export function useAsyncSubmit<T>(
  submitFunction: (data: any) => Promise<T>,
  options: UseAsyncOptions = {}
) {
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<ApiError | Error | null>(null);
  const [success, setSuccess] = createSignal(false);

  const submit = async (data: any) => {
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const result = await submitFunction(data);

      setSuccess(true);

      // Show success toast if enabled
      if (options.showSuccessToast !== false) {
        showToast('success', options.successMessage || 'Saved successfully');
      }

      // Call success callback
      if (options.onSuccess) {
        options.onSuccess(result);
      }

      return result;
    } catch (err: any) {
      const errorObj = err as ApiError | Error;
      setError(errorObj);

      // Show error toast if enabled (default: true)
      if (options.showErrorToast !== false) {
        const message = 'message' in errorObj ? errorObj.message : 'Failed to save';
        showToast('error', message);
      }

      // Call error callback
      if (options.onError) {
        options.onError(errorObj);
      }

      throw err;
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setError(null);
    setSuccess(false);
    setSubmitting(false);
  };

  return {
    submitting,
    error,
    success,
    submit,
    reset,
  };
}

export default useAsync;
