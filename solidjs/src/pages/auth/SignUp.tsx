import { Component, createSignal } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { apiClient } from "../../lib/api-client";
import { signInWithMock } from "../../stores/auth.store";

export const SignUp: Component = () => {
  const navigate = useNavigate();
  const [name, setName] = createSignal("");
  const [email, setEmail] = createSignal("");
  const [phone, setPhone] = createSignal("");
  const [pincode, setPincode] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [district, setDistrict] = createSignal("");
  const [loading, setLoading] = createSignal(false);
  const [errorMsg, setErrorMsg] = createSignal("");

  const handlePincodeLookup = async (pin: string) => {
    setPincode(pin);
    if (pin.length === 6) {
      try {
        const res = await apiClient.get(`/address/pincode/${pin}`, { requiresAuth: false });
        if (res.ok && res.data?.district) {
          setDistrict(`${res.data.district}, ${res.data.state}`);
        }
      } catch {
        // ignore
      }
    }
  };

  const handleSignUp = async (e: Event) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    try {
      const res = await apiClient.post(
        "/auth/signup",
        {
          name: name(),
          email: email(),
          phone: phone(),
          pincode: pincode(),
          password: password(),
        },
        { requiresAuth: false }
      );

      if (res.ok) {
        await signInWithMock(email());
        navigate("/dashboard");
      } else {
        // Fallback for demo
        await signInWithMock(email());
        navigate("/dashboard");
      }
    } catch {
      await signInWithMock(email());
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div class="min-h-[85vh] flex items-center justify-center p-4">
      <div class="w-full max-w-lg bg-white rounded-3xl p-8 border border-slate-200/80 shadow-xl shadow-slate-200/50 space-y-6">
        <div class="text-center space-y-2">
          <div class="w-12 h-12 rounded-2xl bg-forest mx-auto flex items-center justify-center text-white shadow-md shadow-forest/20">
            <span class="material-symbols-outlined text-2xl">agriculture</span>
          </div>
          <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Register as CropSense Farmer</h2>
          <p class="text-xs text-slate-500">Connect your land parcels to satellite telemetry & forward buyers</p>
        </div>

        {errorMsg() && (
          <div class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold">
            {errorMsg()}
          </div>
        )}

        <form onSubmit={handleSignUp} class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Full Name</label>
            <input
              type="text"
              required
              value={name()}
              onInput={(e) => setName(e.currentTarget.value)}
              placeholder="e.g. Gurpreet Singh"
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-forest text-slate-900"
            />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Email</label>
              <input
                type="email"
                required
                value={email()}
                onInput={(e) => setEmail(e.currentTarget.value)}
                placeholder="gurpreet@farm.in"
                class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-forest text-slate-900"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Mobile Number</label>
              <input
                type="tel"
                value={phone()}
                onInput={(e) => setPhone(e.currentTarget.value)}
                placeholder="+91 98765 43210"
                class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-forest text-slate-900"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Pincode</label>
              <input
                type="text"
                maxLength={6}
                value={pincode()}
                onInput={(e) => handlePincodeLookup(e.currentTarget.value)}
                placeholder="141001"
                class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-forest text-slate-900"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Detected District</label>
              <input
                type="text"
                readOnly
                value={district() || "Enter 6-digit pin"}
                class="w-full px-4 py-2.5 bg-slate-100 border border-slate-200 rounded-xl text-sm text-slate-600 cursor-not-allowed"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Create Password</label>
            <input
              type="password"
              required
              value={password()}
              onInput={(e) => setPassword(e.currentTarget.value)}
              placeholder="••••••••"
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-forest text-slate-900"
            />
          </div>

          <button
            type="submit"
            disabled={loading()}
            class="w-full py-3 bg-forest hover:bg-forest-light text-white font-bold rounded-xl text-sm shadow-md shadow-forest/20 transition-all flex items-center justify-center gap-2"
          >
            <span>Complete Registration</span>
            <span class="material-symbols-outlined text-base">arrow_forward</span>
          </button>
        </form>

        <div class="text-center pt-2">
          <span class="text-xs text-slate-500">Already registered? </span>
          <A href="/auth/signin" class="text-xs font-bold text-forest hover:underline">
            Sign In here
          </A>
        </div>
      </div>
    </div>
  );
};
