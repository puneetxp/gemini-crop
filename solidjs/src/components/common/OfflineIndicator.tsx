import { Component, createSignal, onCleanup, onMount } from "solid-js";
import { t } from "../../stores/i18n.store";

export const OfflineIndicator: Component = () => {
  const [isOnline, setIsOnline] = createSignal(typeof navigator !== "undefined" ? navigator.onLine : true);

  onMount(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    onCleanup(() => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    });
  });

  return (
    <>
      {!isOnline() && (
        <div class="fixed top-0 left-0 right-0 z-50 bg-amber-500 text-white px-4 py-2 text-center text-xs font-semibold shadow-md flex items-center justify-center gap-2">
          <span class="material-symbols-outlined text-base">cloud_off</span>
          <span>{t("status.offline")}</span>
        </div>
      )}
    </>
  );
};
