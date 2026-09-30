import { Component, createSignal } from "solid-js";
import { currentLanguage, setLanguage, SupportedLanguage } from "../stores/i18n.store";

export const Configuration: Component = () => {
  const [offlineSync, setOfflineSync] = createSignal(true);
  const [pushAlerts, setPushAlerts] = createSignal(true);
  const [saved, setSaved] = createSignal(false);

  const saveSettings = () => {
    localStorage.setItem(
      "app_config",
      JSON.stringify({
        offlineSync: offlineSync(),
        pushAlerts: pushAlerts(),
      })
    );
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div class="space-y-6 max-w-3xl mx-auto pb-20">
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Platform Configuration</h1>
        <p class="text-xs text-slate-500 mt-0.5">Application preferences, localization & telemetry cache controls</p>
      </div>

      <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-6">
        {saved() && (
          <div class="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold rounded-xl flex items-center gap-2">
            <span class="material-symbols-outlined text-base">check_circle</span>
            <span>Settings saved successfully!</span>
          </div>
        )}

        <div class="space-y-4">
          <div class="flex items-center justify-between py-3 border-b border-slate-100">
            <div>
              <div class="text-sm font-bold text-slate-900">Application Language</div>
              <div class="text-xs text-slate-500">Select language for interface & AI recommendations</div>
            </div>
            <select
              value={currentLanguage()}
              onChange={(e) => setLanguage(e.currentTarget.value as SupportedLanguage)}
              class="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700"
            >
              <option value="en">English (EN)</option>
              <option value="hi">हिंदी (HI)</option>
              <option value="mr">मराठी (MR)</option>
              <option value="pa">ਪੰਜਾਬੀ (PA)</option>
            </select>
          </div>

          <div class="flex items-center justify-between py-3 border-b border-slate-100">
            <div>
              <div class="text-sm font-bold text-slate-900">Offline Background Sync</div>
              <div class="text-xs text-slate-500">Cache plot logs and submit automatically upon internet reconnect</div>
            </div>
            <input
              type="checkbox"
              checked={offlineSync()}
              onChange={(e) => setOfflineSync(e.currentTarget.checked)}
              class="w-5 h-5 accent-forest rounded cursor-pointer"
            />
          </div>

          <div class="flex items-center justify-between py-3">
            <div>
              <div class="text-sm font-bold text-slate-900">Critical Weather & Disease Push Alerts</div>
              <div class="text-xs text-slate-500">Receive Web Push notifications for pest outbreaks and extreme weather</div>
            </div>
            <input
              type="checkbox"
              checked={pushAlerts()}
              onChange={(e) => setPushAlerts(e.currentTarget.checked)}
              class="w-5 h-5 accent-forest rounded cursor-pointer"
            />
          </div>
        </div>

        <button
          onClick={saveSettings}
          class="w-full py-2.5 bg-forest hover:bg-forest-light text-white font-bold text-xs rounded-xl shadow transition-all"
        >
          Save Preferences
        </button>
      </div>
    </div>
  );
};
