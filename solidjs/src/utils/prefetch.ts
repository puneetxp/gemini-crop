/**
 * Prefetch utility for loading data before user navigates
 * Improves perceived performance by loading likely next actions
 */

interface PrefetchOptions {
  priority?: 'high' | 'low';
  timeout?: number;
}

interface PrefetchCache {
  data: any;
  timestamp: number;
  expiresAt: number;
}

const prefetchCache = new Map<string, PrefetchCache>();
const DEFAULT_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Prefetch data and cache it for quick access
 * 
 * @param key - Unique cache key
 * @param fetchFn - Function to fetch data
 * @param options - Prefetch options
 */
export async function prefetch<T>(
  key: string,
  fetchFn: () => Promise<T>,
  options: PrefetchOptions = {}
): Promise<void> {
  // Check if already cached and not expired
  const cached = prefetchCache.get(key);
  if (cached && Date.now() < cached.expiresAt) {
    return;
  }

  try {
    const data = await fetchFn();
    const now = Date.now();
    
    prefetchCache.set(key, {
      data,
      timestamp: now,
      expiresAt: now + DEFAULT_CACHE_TTL,
    });
  } catch (error) {
    console.error(`Prefetch failed for key: ${key}`, error);
  }
}

/**
 * Get prefetched data from cache
 * 
 * @param key - Cache key
 * @returns Cached data or null if not found/expired
 */
export function getPrefetched<T>(key: string): T | null {
  const cached = prefetchCache.get(key);
  
  if (!cached) {
    return null;
  }

  // Check if expired
  if (Date.now() >= cached.expiresAt) {
    prefetchCache.delete(key);
    return null;
  }

  return cached.data as T;
}

/**
 * Clear prefetch cache for a specific key or all keys
 * 
 * @param key - Optional key to clear, clears all if not provided
 */
export function clearPrefetchCache(key?: string): void {
  if (key) {
    prefetchCache.delete(key);
  } else {
    prefetchCache.clear();
  }
}

/**
 * Prefetch on hover - start loading data when user hovers over element
 * 
 * @param element - Element to attach hover listener
 * @param key - Cache key
 * @param fetchFn - Function to fetch data
 */
export function prefetchOnHover<T>(
  element: HTMLElement,
  key: string,
  fetchFn: () => Promise<T>
): () => void {
  let timeoutId: number | null = null;

  const handleMouseEnter = () => {
    // Delay prefetch slightly to avoid prefetching on quick hovers
    timeoutId = window.setTimeout(() => {
      prefetch(key, fetchFn);
    }, 100);
  };

  const handleMouseLeave = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  element.addEventListener('mouseenter', handleMouseEnter);
  element.addEventListener('mouseleave', handleMouseLeave);

  // Return cleanup function
  return () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    element.removeEventListener('mouseenter', handleMouseEnter);
    element.removeEventListener('mouseleave', handleMouseLeave);
  };
}

/**
 * Prefetch on viewport - start loading data when element enters viewport
 * 
 * @param element - Element to observe
 * @param key - Cache key
 * @param fetchFn - Function to fetch data
 * @param options - IntersectionObserver options
 */
export function prefetchOnViewport<T>(
  element: HTMLElement,
  key: string,
  fetchFn: () => Promise<T>,
  options: IntersectionObserverInit = {}
): () => void {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          prefetch(key, fetchFn);
          observer.disconnect(); // Only prefetch once
        }
      });
    },
    {
      root: null,
      rootMargin: '50px', // Start loading 50px before element enters viewport
      threshold: 0,
      ...options,
    }
  );

  observer.observe(element);

  // Return cleanup function
  return () => {
    observer.disconnect();
  };
}

/**
 * Prefetch next page in pagination
 * 
 * @param currentPage - Current page number
 * @param fetchFn - Function to fetch page data
 */
export function prefetchNextPage<T>(
  currentPage: number,
  fetchFn: (page: number) => Promise<T>
): void {
  const nextPage = currentPage + 1;
  const key = `page-${nextPage}`;
  
  prefetch(key, () => fetchFn(nextPage));
}

/**
 * Prefetch related listings
 * 
 * @param listingId - Current listing ID
 * @param fetchFn - Function to fetch related listings
 */
export function prefetchRelatedListings(
  listingId: number,
  fetchFn: (id: number) => Promise<any>
): void {
  const key = `related-${listingId}`;
  
  prefetch(key, () => fetchFn(listingId));
}

/**
 * Batch prefetch multiple items
 * 
 * @param items - Array of prefetch items with keys and fetch functions
 */
export async function batchPrefetch(
  items: Array<{ key: string; fetchFn: () => Promise<any> }>
): Promise<void> {
  const promises = items.map(({ key, fetchFn }) => prefetch(key, fetchFn));
  await Promise.allSettled(promises);
}

/**
 * Clean up expired cache entries
 */
export function cleanupExpiredCache(): void {
  const now = Date.now();
  
  for (const [key, cached] of prefetchCache.entries()) {
    if (now >= cached.expiresAt) {
      prefetchCache.delete(key);
    }
  }
}

// Auto cleanup every 5 minutes
if (typeof window !== 'undefined') {
  setInterval(cleanupExpiredCache, 5 * 60 * 1000);
}
