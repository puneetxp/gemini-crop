import { Component, createSignal, For } from "solid-js";
import { user } from "../../stores/auth.store";

interface SessionItem {
  id: string;
  device: string;
  client: string;
  location: string;
  ip: string;
  lastActive: string;
  isCurrent: boolean;
  type: "mobile" | "desktop" | "iot";
}

export const Security: Component = () => {
  // Password State
  const [currentPassword, setCurrentPassword] = createSignal("");
  const [newPassword, setNewPassword] = createSignal("");
  const [confirmPassword, setConfirmPassword] = createSignal("");
  const [showPassword, setShowPassword] = createSignal(false);
  const [passwordStatus, setPasswordStatus] = createSignal<{ type: "idle" | "success" | "error"; message?: string }>({
    type: "idle"
  });

  // 2FA Toggles
  const [smsOtpEnabled, setSmsOtpEnabled] = createSignal(true);
  const [authenticatorEnabled, setAuthenticatorEnabled] = createSignal(true);
  const [biometricEnabled, setBiometricEnabled] = createSignal(true);
  const [voiceOtpEnabled, setVoiceOtpEnabled] = createSignal(false);
  const [showQrModal, setShowQrModal] = createSignal(false);
  const [lockdownActive, setLockdownActive] = createSignal(false);

  // Active Sessions
  const [sessions, setSessions] = createSignal<SessionItem[]>([
    {
      id: "s1",
      device: "Android 14 (OnePlus 11R)",
      client: "Chrome Mobile 128",
      location: "Nashik, Maharashtra",
      ip: "103.211.24.118",
      lastActive: "Active now",
      isCurrent: true,
      type: "mobile"
    },
    {
      id: "s2",
      device: "Mac OS (Apple Silicon)",
      client: "Chrome Desktop 128",
      location: "Pune Office, Maharashtra",
      ip: "115.114.88.92",
      lastActive: "2 hours ago",
      isCurrent: false,
      type: "desktop"
    },
    {
      id: "s3",
      device: "LoRaWAN Station #GW-NSK-02",
      client: "Field Telemetry Node",
      location: "Krishna Valley Farm Shed",
      ip: "192.168.1.45",
      lastActive: "Telemetry sync 4m ago",
      isCurrent: false,
      type: "iot"
    }
  ]);

  const passwordStrength = () => {
    const p = newPassword();
    if (!p) return 0;
    let score = 0;
    if (p.length >= 8) score += 25;
    if (/[A-Z]/.test(p)) score += 25;
    if (/[0-9]/.test(p)) score += 25;
    if (/[^A-Za-z0-9]/.test(p)) score += 25;
    return score;
  };

  const handlePasswordUpdate = (e: Event) => {
    e.preventDefault();
    if (!currentPassword()) {
      setPasswordStatus({ type: "error", message: "Please enter your current password" });
      return;
    }
    if (newPassword().length < 8) {
      setPasswordStatus({ type: "error", message: "New password must be at least 8 characters long" });
      return;
    }
    if (newPassword() !== confirmPassword()) {
      setPasswordStatus({ type: "error", message: "New passwords do not match" });
      return;
    }

    setPasswordStatus({ type: "success", message: "Password updated successfully" });
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setTimeout(() => setPasswordStatus({ type: "idle" }), 4000);
  };

  const revokeSession = (id: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
  };

  const logoutAllOther = () => {
    setSessions((prev) => prev.filter((s) => s.isCurrent));
  };

  return (
    <div class="space-y-6">
      {/* Header */}
      <div class="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 text-xs font-semibold text-emerald-800 uppercase tracking-wider mb-1">
            <span class="material-symbols-outlined text-base">shield_person</span>
            <span>Security Center</span>
          </div>
          <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight">
            Account Security &amp; Authentication
          </h1>
          <p class="text-xs text-slate-500 mt-1 max-w-xl">
            Manage multi-factor authentication, biometric passkeys, active telemetry sessions, and agricultural data privacy controls.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span class="px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-50 text-forest border border-emerald-200 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>ICAR &amp; MeitY Agri-Stack Compliant</span>
          </span>
        </div>
      </div>

      {/* Security Health Posture Banner */}
      <section class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        <div class="p-4 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-500">Security Health</span>
            <span class="w-8 h-8 rounded-xl bg-emerald-50 text-forest flex items-center justify-center">
              <span class="material-symbols-outlined text-base">verified_user</span>
            </span>
          </div>
          <div>
            <span class="text-xl font-extrabold text-forest">88% Strong</span>
            <p class="text-[11px] text-slate-400 mt-0.5">2FA active on 2 methods</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-500">Two-Factor Auth</span>
            <span class="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">lock</span>
            </span>
          </div>
          <div>
            <span class="text-xl font-extrabold text-emerald-900">Enforced</span>
            <p class="text-[11px] text-slate-400 mt-0.5">SMS OTP + Authenticator</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-500">Active Gateways</span>
            <span class="w-8 h-8 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">devices</span>
            </span>
          </div>
          <div>
            <span class="text-xl font-extrabold text-sky-900">{sessions().length} Connected</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Nashik &amp; Pune Farm nodes</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-500">Telemetry Encryption</span>
            <span class="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">key</span>
            </span>
          </div>
          <div>
            <span class="text-xl font-extrabold text-indigo-900">AES-256 GCM</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Escrow &amp; Soil telemetry</p>
          </div>
        </div>
      </section>

      {/* Main Grid: 2 Columns */}
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Multi-Factor Authentication & Change Password */}
        <div class="space-y-6">
          {/* Multi-Factor Authentication (MFA) */}
          <div class="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 rounded-xl bg-emerald-50 text-forest flex items-center justify-center">
                  <span class="material-symbols-outlined text-xl">security</span>
                </div>
                <div>
                  <h3 class="text-base font-bold text-slate-900">Multi-Factor Authentication</h3>
                  <p class="text-xs text-slate-500">Protect mandi escrow payouts and farm telemetry</p>
                </div>
              </div>
            </div>

            <div class="divide-y divide-slate-100 text-xs">
              {/* Method 1: SMS OTP */}
              <div class="py-3 flex items-center justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-slate-800">SMS OTP Verification</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-forest border border-emerald-200">
                      Primary
                    </span>
                  </div>
                  <p class="text-slate-400 mt-0.5">+91 98230 ••••• (Registered Mobile)</p>
                </div>
                <button
                  onClick={() => setSmsOtpEnabled(!smsOtpEnabled())}
                  class={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                    smsOtpEnabled() ? "bg-forest" : "bg-slate-300"
                  }`}
                >
                  <div
                    class={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      smsOtpEnabled() ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Method 2: Authenticator App */}
              <div class="py-3 flex items-center justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-slate-800">Authenticator App (TOTP)</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                      Google / Aegis
                    </span>
                  </div>
                  <p class="text-slate-400 mt-0.5">8 backup codes available</p>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    onClick={() => setShowQrModal(true)}
                    class="px-2.5 py-1 text-[11px] font-bold text-forest bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors"
                  >
                    View QR
                  </button>
                  <button
                    onClick={() => setAuthenticatorEnabled(!authenticatorEnabled())}
                    class={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                      authenticatorEnabled() ? "bg-forest" : "bg-slate-300"
                    }`}
                  >
                    <div
                      class={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                        authenticatorEnabled() ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Method 3: Passkeys / Biometric */}
              <div class="py-3 flex items-center justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-slate-800">Biometric Passkey (WebAuthn)</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                      Fingerprint
                    </span>
                  </div>
                  <p class="text-slate-400 mt-0.5">OnePlus 11R &amp; MacBook Touch ID</p>
                </div>
                <button
                  onClick={() => setBiometricEnabled(!biometricEnabled())}
                  class={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                    biometricEnabled() ? "bg-forest" : "bg-slate-300"
                  }`}
                >
                  <div
                    class={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      biometricEnabled() ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Method 4: Voice OTP */}
              <div class="py-3 flex items-center justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-slate-800">Voice OTP / Kisan Audio Call</span>
                  </div>
                  <p class="text-slate-400 mt-0.5">Automated IVR call in Marathi/Hindi for rural dead-zones</p>
                </div>
                <button
                  onClick={() => setVoiceOtpEnabled(!voiceOtpEnabled())}
                  class={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                    voiceOtpEnabled() ? "bg-forest" : "bg-slate-300"
                  }`}
                >
                  <div
                    class={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      voiceOtpEnabled() ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Change Password Card */}
          <div class="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <div class="flex items-center gap-2.5">
              <div class="w-9 h-9 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
                <span class="material-symbols-outlined text-xl">password</span>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-900">Change Password</h3>
                <p class="text-xs text-slate-500">Updated 42 days ago from Nashik IP</p>
              </div>
            </div>

            <form onSubmit={handlePasswordUpdate} class="space-y-3 text-xs">
              <div>
                <label class="block font-bold text-slate-700 mb-1">Current Password</label>
                <div class="relative">
                  <input
                    type={showPassword() ? "text" : "password"}
                    value={currentPassword()}
                    onInput={(e) => setCurrentPassword(e.currentTarget.value)}
                    placeholder="Enter current password"
                    class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-mono text-slate-800 focus:outline-none focus:border-forest"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword())}
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <span class="material-symbols-outlined text-base">
                      {showPassword() ? "visibility_off" : "visibility"}
                    </span>
                  </button>
                </div>
              </div>

              <div>
                <label class="block font-bold text-slate-700 mb-1">New Password</label>
                <input
                  type={showPassword() ? "text" : "password"}
                  value={newPassword()}
                  onInput={(e) => setNewPassword(e.currentTarget.value)}
                  placeholder="Minimum 8 characters"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-mono text-slate-800 focus:outline-none focus:border-forest"
                />
                {newPassword() && (
                  <div class="mt-1.5 space-y-1">
                    <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                      <div
                        class={`h-full transition-all ${
                          passwordStrength() <= 25
                            ? "bg-red-500 w-1/4"
                            : passwordStrength() <= 50
                            ? "bg-amber-500 w-2/4"
                            : passwordStrength() <= 75
                            ? "bg-blue-500 w-3/4"
                            : "bg-emerald-500 w-full"
                        }`}
                      />
                    </div>
                    <span class="text-[10px] text-slate-400">
                      {passwordStrength() === 100 ? "Strong password" : "Include capital letter, number, and symbol"}
                    </span>
                  </div>
                )}
              </div>

              <div>
                <label class="block font-bold text-slate-700 mb-1">Confirm New Password</label>
                <input
                  type={showPassword() ? "text" : "password"}
                  value={confirmPassword()}
                  onInput={(e) => setConfirmPassword(e.currentTarget.value)}
                  placeholder="Re-enter new password"
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-mono text-slate-800 focus:outline-none focus:border-forest"
                />
              </div>

              {passwordStatus().message && (
                <div
                  class={`p-2.5 rounded-xl text-xs font-semibold ${
                    passwordStatus().type === "success"
                      ? "bg-emerald-50 text-forest border border-emerald-200"
                      : "bg-red-50 text-red-700 border border-red-200"
                  }`}
                >
                  {passwordStatus().message}
                </div>
              )}

              <button
                type="submit"
                class="w-full py-2.5 px-4 bg-forest hover:bg-emerald-800 text-white font-bold rounded-xl shadow-sm transition-all text-xs flex items-center justify-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">lock_reset</span>
                <span>Update Password</span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Active Sessions & Data Privacy */}
        <div class="space-y-6">
          {/* Active Sessions */}
          <div class="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center">
                  <span class="material-symbols-outlined text-xl">devices</span>
                </div>
                <div>
                  <h3 class="text-base font-bold text-slate-900">Active Login Sessions</h3>
                  <p class="text-xs text-slate-500">Connected farm terminals and mobile gateways</p>
                </div>
              </div>
              <button
                onClick={logoutAllOther}
                class="text-xs font-bold text-red-700 hover:text-red-800 hover:underline"
              >
                Log Out Others
              </button>
            </div>

            <div class="space-y-3">
              <For each={sessions()}>
                {(s) => (
                  <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center justify-between text-xs">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-600">
                        <span class="material-symbols-outlined text-base">
                          {s.type === "mobile"
                            ? "smartphone"
                            : s.type === "desktop"
                            ? "laptop"
                            : "router"}
                        </span>
                      </div>
                      <div>
                        <div class="flex items-center gap-2">
                          <span class="font-bold text-slate-800">{s.device}</span>
                          {s.isCurrent && (
                            <span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-100 text-forest">
                              Current
                            </span>
                          )}
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">
                          {s.location} &bull; {s.ip} &bull; {s.lastActive}
                        </p>
                      </div>
                    </div>

                    {!s.isCurrent && (
                      <button
                        onClick={() => revokeSession(s.id)}
                        class="px-2 py-1 text-red-700 hover:bg-red-50 rounded-lg font-bold text-[11px] transition-colors"
                      >
                        Revoke
                      </button>
                    )}
                  </div>
                )}
              </For>
            </div>
          </div>

          {/* Agronomic Data Governance & Kill Switch */}
          <div class="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
            <div class="flex items-center gap-2.5">
              <div class="w-9 h-9 rounded-xl bg-amber-50 text-amber-900 flex items-center justify-center">
                <span class="material-symbols-outlined text-xl">policy</span>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-900">Agronomic Data Privacy</h3>
                <p class="text-xs text-slate-500">ICAR Agri-Stack data sharing and escrow thresholds</p>
              </div>
            </div>

            <div class="space-y-3 text-xs">
              <div class="p-3 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                <div>
                  <span class="font-bold text-slate-800">Govt PM-KISAN &amp; DBT Linkage</span>
                  <p class="text-[11px] text-slate-400 mt-0.5">Read-only verified telemetry sync</p>
                </div>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-forest border border-emerald-200">
                  Verified
                </span>
              </div>

              <div class="p-3 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                <div>
                  <span class="font-bold text-slate-800">Escrow Biometric Payout Signing</span>
                  <p class="text-[11px] text-slate-400 mt-0.5">Mandatory confirmation for amounts &gt; ₹25,000</p>
                </div>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                  Enforced
                </span>
              </div>

              <div class="pt-2 flex gap-3">
                <button
                  onClick={() => alert("Downloading Farm Telemetry & Soil Archive (ZIP/GeoJSON)...")}
                  class="flex-1 py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
                >
                  <span class="material-symbols-outlined text-sm">download</span>
                  <span>Export Farm Data</span>
                </button>

                <button
                  onClick={() => setLockdownActive(!lockdownActive())}
                  class={`flex-1 py-2 px-3 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition-colors ${
                    lockdownActive()
                      ? "bg-red-700 text-white animate-pulse"
                      : "bg-red-50 hover:bg-red-100 text-red-700 border border-red-200"
                  }`}
                >
                  <span class="material-symbols-outlined text-sm">emergency_home</span>
                  <span>{lockdownActive() ? "Lockdown Active" : "Emergency Freeze"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* TOTP Authenticator QR Modal */}
      {showQrModal() && (
        <div class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-bold text-slate-900">Authenticator Setup</h3>
              <button
                onClick={() => setShowQrModal(false)}
                class="text-slate-400 hover:text-slate-600"
              >
                <span class="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div class="text-center p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div class="w-36 h-36 bg-white mx-auto p-2 rounded-lg border border-slate-300 flex items-center justify-center">
                <span class="material-symbols-outlined text-7xl text-slate-700">qr_code_2</span>
              </div>
              <p class="text-xs font-mono font-bold text-slate-700 mt-2 select-all">
                CROPSENSE-TOTP-MH409-7721
              </p>
              <p class="text-[11px] text-slate-400 mt-1">
                Scan with Google Authenticator or Microsoft Authenticator
              </p>
            </div>

            <button
              onClick={() => setShowQrModal(false)}
              class="w-full py-2 bg-forest text-white rounded-xl text-xs font-bold"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
