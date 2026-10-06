import { Component, createSignal, createEffect } from "solid-js";
import { A, useNavigate, useSearchParams } from "@solidjs/router";
import { signInWithEmail, signInDemo, authLoading, isAuthenticated } from "../../stores/auth.store";

export const SignIn: Component = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const targetUrl = (): string => {
    const raw = Array.isArray(searchParams.redirect) ? searchParams.redirect[0] : searchParams.redirect;
    if (!raw || typeof raw !== "string") return "/dashboard";
    // Only allow safe internal relative paths, avoid auth loop
    if (
      raw.startsWith("/") &&
      !raw.startsWith("//") &&
      !raw.startsWith("/auth/signin") &&
      !raw.startsWith("/auth/signup")
    ) {
      return raw;
    }
    return "/dashboard";
  };

  // If already logged in, redirect immediately to intended target
  createEffect(() => {
    if (!authLoading() && isAuthenticated()) {
      navigate(targetUrl(), { replace: true });
    }
  });

  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [errorMsg, setErrorMsg] = createSignal("");

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setErrorMsg("");
    const res = await signInWithEmail(email(), password());
    if (res.success) {
      navigate(targetUrl(), { replace: true });
    } else {
      setErrorMsg(res.error || "Failed to sign in");
    }
  };

  const handleDemoLogin = async () => {
    setErrorMsg("");
    const res = await signInDemo();
    if (res.success) {
      navigate(targetUrl(), { replace: true });
    } else {
      setErrorMsg(res.error || "Demo sign-in failed");
    }
  };

  return (
    <div class="min-h-[80vh] flex items-center justify-center p-4">
      <div class="w-full max-w-md bg-white rounded-3xl p-8 border border-slate-200/80 shadow-xl shadow-slate-200/50 space-y-6">
        <div class="text-center space-y-2">
          <div class="w-12 h-12 rounded-2xl bg-forest mx-auto flex items-center justify-center text-white shadow-md shadow-forest/20">
            <span class="material-symbols-outlined text-2xl">eco</span>
          </div>
          <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Sign In to CropSense</h2>
          <p class="text-xs text-slate-500">Access your Krishi Command Center & satellite telemetry</p>
        </div>

        {errorMsg() && (
          <div class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center gap-2">
            <span class="material-symbols-outlined text-base">error</span>
            <span>{errorMsg()}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email()}
              onInput={(e) => setEmail(e.currentTarget.value)}
              placeholder="farmer@cropsense.ai"
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-forest text-slate-900 placeholder:text-slate-400"
            />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Password</label>
            <input
              type="password"
              required
              value={password()}
              onInput={(e) => setPassword(e.currentTarget.value)}
              placeholder="••••••••"
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-forest text-slate-900 placeholder:text-slate-400"
            />
          </div>

          <button
            type="submit"
            disabled={authLoading()}
            class="w-full py-3 bg-forest hover:bg-forest-light text-white font-bold rounded-xl text-sm shadow-md shadow-forest/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {authLoading() ? (
              <span class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        <div class="relative flex items-center justify-center my-4">
          <div class="border-t border-slate-200 w-full"></div>
          <span class="bg-white px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider absolute">
            or instant preview
          </span>
        </div>

        <button
          type="button"
          onClick={handleDemoLogin}
          class="w-full py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs shadow transition-all flex items-center justify-center gap-2"
        >
          <span class="material-symbols-outlined text-base">flash_on</span>
          <span>Try the demo farmer account</span>
        </button>
        <p class="text-[11px] text-slate-500 text-center">
          Your own demo account with a sample farm. It and its data are deleted automatically after 24 hours.
        </p>

        <div class="text-center pt-2">
          <span class="text-xs text-slate-500">Don't have an account yet? </span>
          <A href="/auth/signup" class="text-xs font-bold text-forest hover:underline">
            Register Farm
          </A>
        </div>
      </div>
    </div>
  );
};
