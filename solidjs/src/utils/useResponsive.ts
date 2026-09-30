import { createSignal, onMount, onCleanup } from 'solid-js';
import { debounce } from './touchGestures';

export interface ResponsiveBreakpoints {
  xs: boolean; // < 640px
  sm: boolean; // >= 640px
  md: boolean; // >= 768px
  lg: boolean; // >= 1024px
  xl: boolean; // >= 1280px
}

export interface DeviceInfo {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isTouch: boolean;
  isPortrait: boolean;
  width: number;
  height: number;
}

/**
 * Hook to detect responsive breakpoints
 */
export function useResponsive() {
  const [breakpoints, setBreakpoints] = createSignal<ResponsiveBreakpoints>({
    xs: false,
    sm: false,
    md: false,
    lg: false,
    xl: false,
  });

  const updateBreakpoints = () => {
    const width = window.innerWidth;
    setBreakpoints({
      xs: width < 640,
      sm: width >= 640,
      md: width >= 768,
      lg: width >= 1024,
      xl: width >= 1280,
    });
  };

  onMount(() => {
    updateBreakpoints();
    const debouncedUpdate = debounce(updateBreakpoints, 150);
    window.addEventListener('resize', debouncedUpdate);

    onCleanup(() => {
      window.removeEventListener('resize', debouncedUpdate);
    });
  });

  return breakpoints;
}

/**
 * Hook to detect device type and capabilities
 */
export function useDeviceInfo() {
  const [deviceInfo, setDeviceInfo] = createSignal<DeviceInfo>({
    isMobile: false,
    isTablet: false,
    isDesktop: false,
    isTouch: false,
    isPortrait: false,
    width: 0,
    height: 0,
  });

  const updateDeviceInfo = () => {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const isTouch =
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0;

    setDeviceInfo({
      isMobile: width < 768,
      isTablet: width >= 768 && width < 1024,
      isDesktop: width >= 1024,
      isTouch,
      isPortrait: height > width,
      width,
      height,
    });
  };

  onMount(() => {
    updateDeviceInfo();
    const debouncedUpdate = debounce(updateDeviceInfo, 150);
    window.addEventListener('resize', debouncedUpdate);
    window.addEventListener('orientationchange', debouncedUpdate);

    onCleanup(() => {
      window.removeEventListener('resize', debouncedUpdate);
      window.removeEventListener('orientationchange', debouncedUpdate);
    });
  });

  return deviceInfo;
}

/**
 * Hook to detect if viewport is at a specific breakpoint
 */
export function useMediaQuery(query: string) {
  const [matches, setMatches] = createSignal(false);

  onMount(() => {
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => {
      setMatches(e.matches);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
      onCleanup(() => mediaQuery.removeEventListener('change', handler));
    } else {
      // Fallback for older browsers
      // @ts-ignore
      mediaQuery.addListener(handler);
      // @ts-ignore
      onCleanup(() => mediaQuery.removeListener(handler));
    }
  });

  return matches;
}

/**
 * Hook to detect network connection quality
 */
export function useNetworkInfo() {
  const [networkInfo, setNetworkInfo] = createSignal({
    online: true,
    effectiveType: '4g' as '4g' | '3g' | '2g' | 'slow-2g',
    downlink: 10,
    saveData: false,
  });

  onMount(() => {
    const updateNetworkInfo = () => {
      // @ts-ignore - NetworkInformation API
      const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      
      setNetworkInfo({
        online: navigator.onLine,
        effectiveType: connection?.effectiveType || '4g',
        downlink: connection?.downlink || 10,
        saveData: connection?.saveData || false,
      });
    };

    updateNetworkInfo();

    window.addEventListener('online', updateNetworkInfo);
    window.addEventListener('offline', updateNetworkInfo);

    // @ts-ignore
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (connection) {
      connection.addEventListener('change', updateNetworkInfo);
    }

    onCleanup(() => {
      window.removeEventListener('online', updateNetworkInfo);
      window.removeEventListener('offline', updateNetworkInfo);
      if (connection) {
        connection.removeEventListener('change', updateNetworkInfo);
      }
    });
  });

  return networkInfo;
}
