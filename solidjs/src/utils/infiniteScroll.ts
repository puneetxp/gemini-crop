import { createSignal, onCleanup, onMount } from 'solid-js';

export interface InfiniteScrollOptions {
  threshold?: number; // Distance from bottom to trigger load (in pixels)
  initialPage?: number;
  pageSize?: number;
}

export interface InfiniteScrollResult<T> {
  items: () => T[];
  loading: () => boolean;
  hasMore: () => boolean;
  error: () => string | null;
  loadMore: () => Promise<void>;
  reset: () => void;
}

/**
 * Hook for implementing infinite scroll functionality
 * Automatically loads more data when user scrolls near the bottom
 * 
 * @param fetchFn - Function to fetch data for a given page
 * @param options - Configuration options
 * @returns Infinite scroll state and controls
 */
export function createInfiniteScroll<T>(
  fetchFn: (page: number, pageSize: number) => Promise<T[]>,
  options: InfiniteScrollOptions = {}
): InfiniteScrollResult<T> {
  const threshold = options.threshold || 200;
  const pageSize = options.pageSize || 20;
  const initialPage = options.initialPage || 1;

  const [items, setItems] = createSignal<T[]>([]);
  const [loading, setLoading] = createSignal(false);
  const [hasMore, setHasMore] = createSignal(true);
  const [error, setError] = createSignal<string | null>(null);
  const [currentPage, setCurrentPage] = createSignal(initialPage);

  const loadMore = async () => {
    if (loading() || !hasMore()) return;

    setLoading(true);
    setError(null);

    try {
      const newItems = await fetchFn(currentPage(), pageSize);
      
      if (newItems.length === 0) {
        setHasMore(false);
      } else {
        setItems([...items(), ...newItems]);
        setCurrentPage(currentPage() + 1);
        
        // If we got fewer items than requested, we've reached the end
        if (newItems.length < pageSize) {
          setHasMore(false);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load more items');
      console.error('Infinite scroll error:', err);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setItems([]);
    setCurrentPage(initialPage);
    setHasMore(true);
    setError(null);
    setLoading(false);
  };

  // Auto-load first page on mount
  onMount(() => {
    loadMore();
  });

  return {
    items,
    loading,
    hasMore,
    error,
    loadMore,
    reset,
  };
}

/**
 * Hook to detect when user scrolls near bottom of container
 * Triggers callback when threshold is reached
 * 
 * @param containerRef - Reference to scrollable container (null for window)
 * @param onScrollNearBottom - Callback to trigger when near bottom
 * @param threshold - Distance from bottom to trigger (in pixels)
 */
export function createScrollObserver(
  containerRef: () => HTMLElement | null,
  onScrollNearBottom: () => void,
  threshold: number = 200
) {
  const handleScroll = () => {
    const container = containerRef();
    
    if (!container) {
      // Use window scroll
      const scrollTop = window.scrollY;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      
      if (scrollTop + windowHeight >= documentHeight - threshold) {
        onScrollNearBottom();
      }
    } else {
      // Use container scroll
      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;
      
      if (scrollTop + clientHeight >= scrollHeight - threshold) {
        onScrollNearBottom();
      }
    }
  };

  onMount(() => {
    const container = containerRef();
    const target = container || window;
    
    target.addEventListener('scroll', handleScroll);
    
    onCleanup(() => {
      target.removeEventListener('scroll', handleScroll);
    });
  });
}

/**
 * Intersection Observer based infinite scroll
 * More efficient than scroll event listeners
 * 
 * @param targetRef - Reference to sentinel element at bottom of list
 * @param onIntersect - Callback when sentinel becomes visible
 * @param options - IntersectionObserver options
 */
export function createIntersectionObserver(
  targetRef: () => HTMLElement | null,
  onIntersect: () => void,
  options: IntersectionObserverInit = {}
) {
  onMount(() => {
    const target = targetRef();
    if (!target) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            onIntersect();
          }
        });
      },
      {
        root: null,
        rootMargin: '0px',
        threshold: 0.1,
        ...options,
      }
    );

    observer.observe(target);

    onCleanup(() => {
      observer.disconnect();
    });
  });
}
