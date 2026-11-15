/**
 * CropSense AI — Pure Kotlin Native Android Bridge Client
 * Interoperates directly with window.AndroidNative @JavascriptInterface
 */

declare global {
  interface Window {
    AndroidNative?: {
      isNativeAndroid: () => boolean;
      showToast: (message: string) => void;
      vibrate: (durationMs: number) => void;
      takePhoto: () => void;
      requestLocation: () => void;
    };
    onNativePhotoCaptured?: (dataUrl: string) => void;
    onNativeLocationReceived?: (lat: number, lng: number) => void;
  }
}

export const isAndroidNative = (): boolean => {
  return typeof window !== "undefined" && Boolean(window.AndroidNative?.isNativeAndroid?.());
};

export const showNativeToast = (message: string): void => {
  if (isAndroidNative()) {
    window.AndroidNative?.showToast(message);
  }
};

export const vibrateNative = (durationMs = 50): void => {
  if (isAndroidNative()) {
    window.AndroidNative?.vibrate(durationMs);
  }
};

export const takeNativePhoto = (onCaptured: (dataUrl: string) => void): void => {
  if (isAndroidNative()) {
    window.onNativePhotoCaptured = (dataUrl: string) => {
      onCaptured(dataUrl);
    };
    window.AndroidNative?.takePhoto();
  }
};

export const requestNativeLocation = (onLocation: (lat: number, lng: number) => void): void => {
  if (isAndroidNative()) {
    window.onNativeLocationReceived = (lat: number, lng: number) => {
      onLocation(lat, lng);
    };
    window.AndroidNative?.requestLocation();
  }
};
