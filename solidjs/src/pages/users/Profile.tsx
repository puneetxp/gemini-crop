import { Component } from "solid-js";
import { user } from "../../stores/auth.store";

export const Profile: Component = () => {
  return (
    <div class="space-y-6 max-w-3xl mx-auto pb-20">
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Farmer Account Profile</h1>
        <p class="text-xs text-slate-500 mt-0.5">Aadhaar verified farmer identity & banking registration</p>
      </div>

      <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
        <div class="flex items-center gap-4 pb-4 border-b border-slate-100">
          <div class="w-16 h-16 rounded-2xl bg-forest/10 text-forest font-black text-2xl flex items-center justify-center">
            {user()?.name?.[0] || "F"}
          </div>
          <div>
            <h3 class="font-bold text-lg text-slate-900">{user()?.name || "Farmer User"}</h3>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              Verified Primary Producer
            </span>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div class="p-3 bg-slate-50 rounded-xl">
            <span class="text-slate-400 block uppercase font-bold text-[10px]">Registered Email</span>
            <span class="font-bold text-slate-800 text-sm mt-0.5 block">{user()?.email || "farmer@cropsense.ai"}</span>
          </div>
          <div class="p-3 bg-slate-50 rounded-xl">
            <span class="text-slate-400 block uppercase font-bold text-[10px]">Assigned Role</span>
            <span class="font-bold text-slate-800 text-sm mt-0.5 block uppercase">{user()?.role || "Farmer"}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
