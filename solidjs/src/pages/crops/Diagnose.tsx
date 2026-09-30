import { Component, createSignal } from "solid-js";
import { apiClient } from "../../lib/api-client";
import { lang } from "../../stores/i18n.store";

export const Diagnose: Component = () => {
  const [selectedFile, setSelectedFile] = createSignal<File | null>(null);
  const [previewUrl, setPreviewUrl] = createSignal<string | null>(null);
  const [isDiagnosing, setIsDiagnosing] = createSignal(false);
  const [result, setResult] = createSignal<any>(null);
  const [errorMessage, setErrorMessage] = createSignal("");

  const toBase64 = (file: File) =>
    new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(file);
    });

  const handleFileChange = (e: Event) => {
    const input = e.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleDiagnose = async () => {
    const file = selectedFile();
    if (!file) return;
    setIsDiagnosing(true);
    setErrorMessage("");
    setResult(null);

    try {
      // POST /vision/diagnose-crop expects JSON { image_base64, mime_type, crop_name?, lang }
      const res = await apiClient.post<any>(
        "/vision/diagnose-crop",
        {
          image_base64: await toBase64(file),
          mime_type: file.type || "image/jpeg",
          lang: lang(),
        },
        { timeoutMs: 90000 }
      );

      const d = res.data?.diagnosis;
      if (res.ok && d) {
        const t = d.treatment || {};
        setResult({
          disease_name: d.disease_name,
          confidence_score: Number(d.confidence) || 0,
          severity: d.severity,
          recommended_treatment: [...(t.cultural || []), ...(t.organic || []), ...(t.chemical || [])],
          // Banned pesticides the safety check removed, the CIBRC label note, and any photo tip
          safety_warning: [
            ...((d.safety?.removed || []) as { reason: string }[]).map((r) => `Removed: ${r.reason}.`),
            d.safety?.label_note,
            d.better_photo_tip,
          ]
            .filter(Boolean)
            .join(" "),
        });
      } else {
        const detail = res.data?.detail;
        setErrorMessage(
          `Diagnosis failed (${res.status}): ${typeof detail === "string" ? detail : "the AI service did not return a result"}`
        );
      }
    } catch (err: any) {
      setErrorMessage(`Diagnosis failed: ${err?.message || "network error"}`);
    } finally {
      setIsDiagnosing(false);
    }
  };

  return (
    <div class="space-y-6 max-w-5xl mx-auto pb-20">
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
            <span class="material-symbols-outlined text-2xl">psychology</span>
          </div>
          <div>
            <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">AI Crop Pathology Doctor</h1>
            <p class="text-xs text-slate-500">
              Powered by Multimodal Gemini Vision & agronomic safety guidelines
            </p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Upload Column */}
        <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
          <h3 class="font-bold text-slate-900 text-sm">Upload or Capture Leaf Specimen</h3>

          <div class="border-2 border-dashed border-slate-200 hover:border-forest/50 rounded-2xl p-6 text-center transition-all bg-slate-50/50">
            {previewUrl() ? (
              <div class="space-y-3">
                <img
                  src={previewUrl()!}
                  alt="Leaf Specimen"
                  class="max-h-60 mx-auto rounded-xl object-contain shadow"
                />
                <button
                  onClick={() => {
                    setSelectedFile(null);
                    setPreviewUrl(null);
                    setResult(null);
                  }}
                  class="text-xs font-semibold text-rose-600 hover:underline"
                >
                  Remove & Choose Another
                </button>
              </div>
            ) : (
              <label class="cursor-pointer block space-y-2">
                <span class="material-symbols-outlined text-4xl text-slate-400">add_a_photo</span>
                <div class="text-xs font-bold text-slate-700">Click to upload photo or take a picture</div>
                <div class="text-[11px] text-slate-400">Supports JPG, PNG up to 10MB</div>
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handleFileChange}
                  class="hidden"
                />
              </label>
            )}
          </div>

          <button
            onClick={handleDiagnose}
            disabled={!selectedFile() || isDiagnosing()}
            class="w-full py-3 bg-forest hover:bg-forest-light text-white font-bold rounded-xl text-sm shadow-md shadow-forest/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isDiagnosing() ? (
              <>
                <span class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>Analyzing Pathology via Gemini Vision…</span>
              </>
            ) : (
              <>
                <span class="material-symbols-outlined text-base">auto_fix_high</span>
                <span>Run Instant AI Pathology Scan</span>
              </>
            )}
          </button>
        </div>

        {/* Diagnosis Results Column */}
        <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
          <h3 class="font-bold text-slate-900 text-sm">Pathology & Treatment Report</h3>

          {result() ? (
            <div class="space-y-4">
              <div class="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-emerald-800 uppercase tracking-wide">Diagnosis Result</span>
                  <span class="text-xs font-bold text-emerald-700 bg-white px-2 py-0.5 rounded-full border border-emerald-200">
                    {Math.round(result().confidence_score * 100)}% Confidence
                  </span>
                </div>
                <h4 class="text-lg font-black text-slate-900 mt-1">{result().disease_name}</h4>
                <div class="text-xs text-slate-600 mt-0.5">Severity: {result().severity}</div>
              </div>

              <div>
                <h5 class="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Recommended Agro-Chemical Treatment
                </h5>
                <ul class="space-y-2">
                  {result().recommended_treatment?.map((treatment: string) => (
                    <li class="text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-200/60 flex items-start gap-2">
                      <span class="material-symbols-outlined text-base text-forest mt-0.5">check_circle</span>
                      <span>{treatment}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {result().safety_warning && (
                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 font-medium flex items-start gap-2">
                  <span class="material-symbols-outlined text-base text-amber-600">security</span>
                  <span>{result().safety_warning}</span>
                </div>
              )}
            </div>
          ) : errorMessage() ? (
            <div role="alert" class="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 font-semibold flex items-start gap-2">
              <span class="material-symbols-outlined text-base text-red-600">error</span>
              <span>{errorMessage()}</span>
            </div>
          ) : (
            <div class="min-h-[220px] flex flex-col items-center justify-center text-center p-6 text-slate-400">
              <span class="material-symbols-outlined text-5xl mb-2 text-slate-300">microbiology</span>
              <p class="text-xs max-w-xs">
                Upload or snap a leaf photo on the left and click "Run Instant AI Pathology Scan" to view diagnosis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
