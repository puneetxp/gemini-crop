import { Component } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { isAuthenticated, signInDemo } from "../stores/auth.store";
import { showToast } from "../components/ui/Toast";
import { t } from "../stores/i18n.store";

export const Home: Component = () => {
  const navigate = useNavigate();

  return (
    <div class="space-y-8 max-w-6xl mx-auto pb-20">
      {/* 1. Master Hero Section with Real Photo */}
      <section class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-forest via-emerald-800 to-emerald-950 text-white p-6 sm:p-10 shadow-xl shadow-forest/15">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          <div class="lg:col-span-7 space-y-4">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs font-semibold text-amber-300">
              <span class="material-symbols-outlined text-sm">auto_awesome</span>
              <span>{t("home.badge")}</span>
            </div>
            <h1 class="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
              {t("home.hero.title1")} <br />
              <span class="text-amber-400">{t("home.hero.title2")}</span> {t("home.hero.title3")}
            </h1>
            <p class="text-emerald-100 text-sm md:text-base leading-relaxed max-w-xl">
              {t("home.hero.desc")}
            </p>
            <div class="flex flex-wrap items-center gap-3 pt-3">
              <A
                href="/dashboard"
                class="px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-sm shadow-lg shadow-amber-500/25 transition-all flex items-center gap-2"
              >
                <span>{t("home.launch")}</span>
                <span class="material-symbols-outlined text-lg">arrow_forward</span>
              </A>
              {!isAuthenticated() && (
                <button
                  onClick={async () => {
                    const res = await signInDemo();
                    if (res.success) navigate("/dashboard");
                    else showToast("error", res.error || "Could not start a demo session");
                  }}
                  class="px-5 py-3 bg-white/10 hover:bg-white/20 border border-white/30 text-white font-semibold rounded-xl text-sm transition-all"
                >
                  {t("home.instantDemo")}
                </button>
              )}
            </div>
          </div>

          {/* Hero Visual Card (Farmer with Cow & Goat) */}
          <div class="lg:col-span-5 relative">
            <div class="relative rounded-2xl overflow-hidden shadow-2xl border-2 border-white/20 aspect-[4/3] bg-emerald-900 group">
              <img
                src="https://lh3.googleusercontent.com/aida/AEtjO1XCpypR4-aqatPr_yZgeZb5YcAtLWB9qgNnL-dmWNKq83PI7Ogmld4I2mfxdMH7fgmB8B5KDXt4cA41PfxQIxgYmtKZqKsQe1frZH_p8w-NhBTDtskbksaVNjHZuM_un25quQJq3aLr1Oq9ne4qYW2n4EQNhutXS2VCtRPBrd-CKCzyErvcugucZ0lSMdmg3Mq4tcqMbjpb_cQqr00VeX6fns-wd8p3fXrURpz1hEFM4aRH4_PPKN7JLA"
                alt="Smiling Indian farmer with Desi cow and dairy goat"
                class="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
              />
              <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
              <div class="absolute bottom-3 left-3 right-3 flex items-center justify-between text-xs">
                <span class="bg-emerald-600/90 backdrop-blur-md px-2.5 py-1 rounded-full font-bold text-white flex items-center gap-1 shadow">
                  <span class="material-symbols-outlined text-sm">verified</span>
                  <span>100% सत्यापित पशु</span>
                </span>
                <span class="bg-amber-500/90 text-slate-950 font-bold px-2 py-0.5 rounded-full text-[11px] shadow">
                  INAHIS RFID
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Animall-Style Emerald Cattle Trading Card */}
      <section class="rounded-3xl bg-[#004532] text-white p-6 sm:p-8 shadow-lg relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="space-y-3 max-w-lg z-10">
          <span class="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-amber-300 bg-white/10 px-3 py-1 rounded-full">
            <span class="material-symbols-outlined text-sm">pets</span>
            CropSense Pashu Dhan
          </span>
          <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
            बेचना आसान है CropSense के साथ
          </h2>
          <p class="text-emerald-100 text-sm">
            गाय, भैंस, बकरी — बिना बिचौलिये सीधे घर बैठे सही दाम पर बेचें व खरीदें। थन जांच और 7 दिन दूध गारंटी।
          </p>
          <div class="pt-2 flex items-center gap-3">
            <A
              href="/livestock-marketplace"
              class="px-5 py-2.5 bg-white text-[#004532] hover:bg-slate-100 font-black rounded-xl text-sm shadow-md transition-all inline-flex items-center gap-2"
            >
              <span>पशु दर्ज करें</span>
              <span class="material-symbols-outlined text-base">add_circle</span>
            </A>
            <A
              href="/livestock"
              class="px-4 py-2 bg-emerald-700/80 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition-all inline-flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-sm">storefront</span>
              <span>मंडी भाव देखें</span>
            </A>
          </div>
        </div>

        <div class="w-full md:w-80 h-44 rounded-2xl overflow-hidden shadow-md relative z-10 shrink-0">
          <img
            src="https://lh3.googleusercontent.com/aida/AEtjO1WBngYvX6VITfnXZEtcX4Jv5VNg6R4FO9eG0PtNOUnxbk02IyP6mEro_KcbmmJvL98OSfVJwxEbKYs2W-tloYXcoLKkd2TmHG1lIuKARnPSl9XnzWiCdpqtZk3yrpd3q_DjIY87IryUNAUhEKbKs45Eior4ubsf8CMdzpYEcK5f4e-G3e8ShcIi8-yOQhVbACrePLmLw6fp19KAWW5NhkUokwcgs4VxAPlp0_uk7Ab4MptfjuBA-5oT5tw"
            alt="Indigenous Gir Cow"
            class="w-full h-full object-cover"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
          <span class="absolute bottom-2.5 left-3 text-xs font-bold text-white bg-black/40 backdrop-blur-sm px-2 py-0.5 rounded">
            देसी गिर गाय • ₹85,000
          </span>
        </div>
      </section>

      {/* 3. Video Tutorials Carousel ("समझें हर प्रक्रिया, आसान तरीके से!") */}
      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span class="material-symbols-outlined text-emerald-600">play_circle</span>
              <span>समझें हर प्रक्रिया, आसान तरीके से!</span>
            </h3>
            <p class="text-xs text-slate-500">किसान भाइयों के लिए वीडियो गाइड व सहायता</p>
          </div>
          <A href="/livestock" class="text-xs font-bold text-forest hover:underline">
            सब देखें &rarr;
          </A>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Video 1 */}
          <div class="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-sm hover:shadow-md transition-all group">
            <div class="relative h-36 bg-slate-100 overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1595974482597-4b8da8879bc5?auto=format&fit=crop&w=600&q=80"
                alt="पशु कैसे खरीदें"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div class="absolute inset-0 bg-black/30 flex items-center justify-center">
                <div class="w-11 h-11 rounded-full bg-emerald-600/90 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-2xl">play_arrow</span>
                </div>
              </div>
              <span class="absolute bottom-2 right-2 bg-black/70 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                2:15 Min
              </span>
            </div>
            <div class="p-4">
              <h4 class="font-bold text-sm text-slate-900 group-hover:text-forest transition-colors">
                कैसे खरीदें CropSense AI से पशु?
              </h4>
              <p class="text-xs text-slate-500 mt-1">थनों की जांच, दूध रिकॉर्ड और एस्क्रो भुगतान का सुरक्षित तरीका।</p>
            </div>
          </div>

          {/* Video 2 */}
          <div class="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-sm hover:shadow-md transition-all group">
            <div class="relative h-36 bg-slate-100 overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1500595046743-cd271d694d30?auto=format&fit=crop&w=600&q=80"
                alt="पशु बेचने का सही तरीका"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div class="absolute inset-0 bg-black/30 flex items-center justify-center">
                <div class="w-11 h-11 rounded-full bg-emerald-600/90 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-2xl">play_arrow</span>
                </div>
              </div>
              <span class="absolute bottom-2 right-2 bg-black/70 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                3:40 Min
              </span>
            </div>
            <div class="p-4">
              <h4 class="font-bold text-sm text-slate-900 group-hover:text-forest transition-colors">
                पशु बेचने का सही तरीका जानें
              </h4>
              <p class="text-xs text-slate-500 mt-1">फ़ोटो और दूध दोहने का वीडियो अपलोड कर के सीधे ग्राहक पाएं।</p>
            </div>
          </div>

          {/* Video 3 */}
          <div class="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-sm hover:shadow-md transition-all group">
            <div class="relative h-36 bg-slate-100 overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?auto=format&fit=crop&w=600&q=80"
                alt="1 दिन में कैसे बिकेगा पशु"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div class="absolute inset-0 bg-black/30 flex items-center justify-center">
                <div class="w-11 h-11 rounded-full bg-emerald-600/90 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-2xl">play_arrow</span>
                </div>
              </div>
              <span class="absolute bottom-2 right-2 bg-black/70 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                1:50 Min
              </span>
            </div>
            <div class="p-4">
              <h4 class="font-bold text-sm text-slate-900 group-hover:text-forest transition-colors">
                1 दिन में कैसे बिकेगा पशु?
              </h4>
              <p class="text-xs text-slate-500 mt-1">सही रेट निर्धारण और प्रीमियम खरीदारों तक सीधी पहुंच।</p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. 2x2 Utility Grid ("अन्य सुविधाएं") */}
      <section class="space-y-4">
        <h3 class="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <span class="material-symbols-outlined text-amber-600">widgets</span>
          <span>अन्य सुविधाएं</span>
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <A
            href="/services"
            class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div class="flex items-center gap-3.5">
              <div class="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-2xl">payments</span>
              </div>
              <div>
                <h4 class="font-bold text-slate-900 group-hover:text-forest text-sm">पशु लोन</h4>
                <p class="text-xs text-slate-500">घर बैठे आसान लोन</p>
              </div>
            </div>
            <span class="material-symbols-outlined text-slate-400 group-hover:text-forest transition-colors">
              chevron_right
            </span>
          </A>

          <A
            href="/services"
            class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div class="flex items-center gap-3.5">
              <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-2xl">verified_user</span>
              </div>
              <div>
                <h4 class="font-bold text-slate-900 group-hover:text-blue-700 text-sm">पशु बीमा</h4>
                <p class="text-xs text-slate-500">सस्ता व सुरक्षित बीमा</p>
              </div>
            </div>
            <span class="material-symbols-outlined text-slate-400 group-hover:text-blue-700 transition-colors">
              chevron_right
            </span>
          </A>

          <A
            href="/assistant"
            class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div class="flex items-center gap-3.5">
              <div class="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-2xl">forum</span>
              </div>
              <div>
                <h4 class="font-bold text-slate-900 group-hover:text-amber-700 text-sm">पशु चर्चा</h4>
                <p class="text-xs text-slate-500">जानकारी व अनुभव बांटें</p>
              </div>
            </div>
            <span class="material-symbols-outlined text-slate-400 group-hover:text-amber-700 transition-colors">
              chevron_right
            </span>
          </A>

          <A
            href="/marketplace"
            class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div class="flex items-center gap-3.5">
              <div class="w-12 h-12 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-2xl">emoji_events</span>
              </div>
              <div>
                <h4 class="font-bold text-slate-900 group-hover:text-purple-700 text-sm">अखाड़ा</h4>
                <p class="text-xs text-slate-500">कॉइन व इनाम जीतें</p>
              </div>
            </div>
            <span class="material-symbols-outlined text-slate-400 group-hover:text-purple-700 transition-colors">
              chevron_right
            </span>
          </A>
        </div>
      </section>

      {/* 5. "आपके क्षेत्र के टॉप पशु" (4-Photo Multi-Angle Cattle Showcase) */}
      <section class="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm space-y-5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div class="inline-flex items-center gap-1.5 text-xs font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full mb-1">
              <span class="material-symbols-outlined text-sm">hotel_class</span>
              <span>क्षेत्र में भारी मांग</span>
            </div>
            <h3 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              आपके क्षेत्र के टॉप पशु
            </h3>
            <p class="text-xs text-slate-500">सत्यापित ब्यात, उच्च दूध क्षमता व थन परीक्षण पास</p>
          </div>
          <A
            href="/livestock-marketplace"
            class="px-4 py-2 bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-xs rounded-xl transition-all self-start sm:self-auto inline-flex items-center gap-1"
          >
            <span>और देखें</span>
            <span class="material-symbols-outlined text-sm">arrow_forward</span>
          </A>
        </div>

        {/* 4 Photos Row */}
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="rounded-xl overflow-hidden aspect-square relative bg-slate-100 group border border-slate-200">
            <img
              src="https://lh3.googleusercontent.com/aida/AEtjO1WwaDmBphlHnVg1Pqo8DOVCYo0FrPe2ygx4IgyO__oq3fcB6DhBNq5rcy-gEp-SMEhiV6PY4UKmesknzBi4Ob4s-GAQ6awDAQ-5ZnwRMbdmeiQE5PUaUjRcFB8dyfSnyk0MOp87-LUq3crvhdRmt4L9x74SQL4WHC9VEGC1xq0y-yqQYzNPRBkafPAYo4r1X23M4iO_lzUjNAmw-uYL1vOVUQNWCHmLk29NOAY5fyMB8K7JTXkp3ej0Oz4"
              alt="Murrah Buffalo"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform"
            />
            <span class="absolute bottom-2 left-2 bg-black/60 text-white text-[10px] font-bold px-2 py-0.5 rounded backdrop-blur-sm">
              मुर्रा भैंस
            </span>
          </div>

          <div class="rounded-xl overflow-hidden aspect-square relative bg-slate-100 group border border-slate-200">
            <img
              src="https://lh3.googleusercontent.com/aida/AEtjO1WBngYvX6VITfnXZEtcX4Jv5VNg6R4FO9eG0PtNOUnxbk02IyP6mEro_KcbmmJvL98OSfVJwxEbKYs2W-tloYXcoLKkd2TmHG1lIuKARnPSl9XnzWiCdpqtZk3yrpd3q_DjIY87IryUNAUhEKbKs45Eior4ubsf8CMdzpYEcK5f4e-G3e8ShcIi8-yOQhVbACrePLmLw6fp19KAWW5NhkUokwcgs4VxAPlp0_uk7Ab4MptfjuBA-5oT5tw"
              alt="Gir Cow"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform"
            />
            <span class="absolute bottom-2 left-2 bg-black/60 text-white text-[10px] font-bold px-2 py-0.5 rounded backdrop-blur-sm">
              गीर गाय
            </span>
          </div>

          <div class="rounded-xl overflow-hidden aspect-square relative bg-slate-100 group border border-slate-200">
            <img
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBABO7nxSKmgm0aU80yG74_kIDLPOdlMOXCnXu-A0yFe94e_qfFM5BYZMhxW3X5CJWb4G7ATVffIaaFl2vVBEkriuSp1C-wXl-jNvh7s32dVtRuPWbqxdnJrH01-R2UXv1GEu4wlxM34Ua_bKi857aMBezdGQl1I7rBvKWbAxmHCkB2-Je_Dc2CoFJ5boIKrvv6W80K9Y3zFLiDP2kjtDjZ8oLdswBUR4Z-rVx7mxJewMrQ3UmF1aoGOkzaJ1UJ90etxLVZ2FKVW4c"
              alt="Udder health check"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform"
            />
            <span class="absolute bottom-2 left-2 bg-emerald-800/80 text-white text-[10px] font-bold px-2 py-0.5 rounded backdrop-blur-sm flex items-center gap-0.5">
              <span class="material-symbols-outlined text-[12px]">check</span> थन जांच OK
            </span>
          </div>

          <div class="rounded-xl overflow-hidden aspect-square relative bg-slate-100 group border border-slate-200">
            <img
              src="https://images.unsplash.com/photo-1546445317-29f4545e9d53?auto=format&fit=crop&w=600&q=80"
              alt="Sahiwal Cow"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform"
            />
            <span class="absolute bottom-2 left-2 bg-black/60 text-white text-[10px] font-bold px-2 py-0.5 rounded backdrop-blur-sm">
              साहीवाल गाय
            </span>
          </div>
        </div>

        {/* Price & Details Bar */}
        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div class="text-2xl font-black text-slate-900 tracking-tight">
              ₹1,70,000 - ₹2,25,000
            </div>
            <p class="text-xs text-slate-500 font-semibold mt-0.5">
              8L - 17L दैनिक दूध क्षमता • दूसरा ब्यात
            </p>
          </div>
          <div class="flex items-center gap-2 text-xs font-bold text-slate-600">
            <span class="material-symbols-outlined text-forest text-base">location_on</span>
            <span>Jaipur • Nashik Valley • Junnar</span>
          </div>
        </div>
      </section>

      {/* 6. Photo-Rich Crop Telemetry Showcase */}
      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span class="material-symbols-outlined text-forest">agriculture</span>
              <span>प्रमुख फसल पोर्टफोलियो</span>
            </h3>
            <p class="text-xs text-slate-500">उपग्रह से लाइव फसल स्वास्थ्य व मंडी अनुबंध</p>
          </div>
          <A href="/crops/my-crops" class="text-xs font-bold text-forest hover:underline">
            मेरी फसलें &rarr;
          </A>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Crop 1: Wheat */}
          <div class="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-sm flex flex-col sm:flex-row group">
            <div class="sm:w-44 h-40 sm:h-auto relative overflow-hidden bg-slate-100 shrink-0">
              <img
                src="https://lh3.googleusercontent.com/aida/AEtjO1UH4pQ9KI3pN7k3AQCFJPFSsslmfSRqI4UiA610qbjehZzVvSX8bLu_rtVO5913eF-aXHvGINybxUv0S_7Nv1a7ouRVQb86_Jx3YDRWwyjxBozzuj0ISXN50t8HBhXcWEJhAKBi4SijlSLRQwsuOXTYSOct_9NWHd9CnTXcfWCMlMuPyVmVZocQ-lSFdTYsQHNabIEVJVW4_uLANVbh3j9RBeTI0ojsItM0c3T3QNbWMsY5absxLXSyESc"
                alt="Golden Sharbati Wheat"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <span class="absolute top-2 left-2 bg-emerald-800 text-white text-[10px] font-bold px-2 py-0.5 rounded">
                Plot A • 4.5 Ac
              </span>
            </div>
            <div class="p-4 flex-1 flex flex-col justify-between">
              <div>
                <h4 class="font-black text-slate-900 text-base">शरबती गोल्डन गेहूं</h4>
                <p class="text-xs text-slate-500 mt-0.5">बालियां निकलने की अवस्था • NDVI 0.81 (उत्तम)</p>
                <div class="mt-2 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg inline-block">
                  मंडी भाव: ₹2,450 / क्विंटल
                </div>
              </div>
              <A href="/dashboard" class="text-xs font-bold text-forest mt-3 inline-flex items-center gap-1">
                <span>विस्तार से देखें</span>
                <span class="material-symbols-outlined text-sm">arrow_forward</span>
              </A>
            </div>
          </div>

          {/* Crop 2: Sweet Corn */}
          <div class="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-sm flex flex-col sm:flex-row group">
            <div class="sm:w-44 h-40 sm:h-auto relative overflow-hidden bg-slate-100 shrink-0">
              <img
                src="https://lh3.googleusercontent.com/aida/AEtjO1XQPHJBsetogv6RoQ-cPg70CSfKt9WKPcv0-YhQ4AjdNq0APaJafaE2Hymj-9SHR7H2u7qcoODEvDbeQNHgW4kF9OgBptpkGy8Y9VqB1VR_HAe4xqG64hzs83XIZegFTV9tFC7d2TMqEnTTSkLcfoSdLqcaQ8rz14_CqoC110qs2aONuX1hKcoEND-bMVxNj_SJcaxh7Zz2RJ7ADhBVIywBgsogM_Xf8gTY4gh0Fi2VbwHVskyXBTIDX3I"
                alt="Sweet Corn Maize"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <span class="absolute top-2 left-2 bg-amber-700 text-white text-[10px] font-bold px-2 py-0.5 rounded">
                Plot C • 2.0 Ac
              </span>
            </div>
            <div class="p-4 flex-1 flex flex-col justify-between">
              <div>
                <h4 class="font-black text-slate-900 text-base">स्वीट कॉर्न मक्का</h4>
                <p class="text-xs text-slate-500 mt-0.5">सिल्किंग अवस्था • अनुमानित उपज: 38 क्विंटल</p>
                <div class="mt-2 text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-1 rounded-lg inline-block">
                  मंडी भाव: ₹2,100 / क्विंटल
                </div>
              </div>
              <A href="/dashboard" class="text-xs font-bold text-forest mt-3 inline-flex items-center gap-1">
                <span>विस्तार से देखें</span>
                <span class="material-symbols-outlined text-sm">arrow_forward</span>
              </A>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

