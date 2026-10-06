/**
 * Fluent Text-to-Speech Engine for CropSense AI
 * Selects highest-fidelity neural/natural Indian English and Hindi voices,
 * strips technical markdown, normalizes numbers & currency, and speaks fluently.
 */

import { createSignal } from "solid-js";

let cachedVoices: SpeechSynthesisVoice[] = [];

function loadVoices(): SpeechSynthesisVoice[] {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return [];
  const voices = window.speechSynthesis.getVoices();
  if (voices.length > 0) cachedVoices = voices;
  return cachedVoices;
}

if (typeof window !== "undefined" && "speechSynthesis" in window) {
  loadVoices();
  window.speechSynthesis.onvoiceschanged = () => {
    loadVoices();
  };
}

/** Pre-process text for natural, fluid reading by stripping markdown & converting symbols */
export function cleanTextForSpeech(raw: string): string {
  if (!raw) return "";
  return raw
    // Remove markdown code blocks and inline code
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`([^`]+)`/g, "$1")
    // Remove markdown bold / italics
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/_([^_]+)_/g, "$1")
    // Remove markdown headers
    .replace(/^#+\s+/gm, "")
    // Remove bullet point markers
    .replace(/^[-*•]\s+/gm, "")
    // Convert ₹ symbol to spoken word "rupees" / "रुपये"
    .replace(/₹\s*([0-9,]+)/g, "$1 rupees")
    // Replace ac -> acres, kg -> kilograms
    .replace(/\b([0-9.]+)\s*ac\b/gi, "$1 acres")
    .replace(/\b([0-9.]+)\s*kg\b/gi, "$1 kilograms")
    // Clean extra whitespace
    .replace(/\s+/g, " ")
    .trim();
}

/** Find the most natural/fluent voice matching the language */
export function pickFluentVoice(langCode: string): SpeechSynthesisVoice | null {
  const voices = loadVoices();
  if (!voices.length) return null;

  const targetLang = (langCode || "en").toLowerCase();
  const base = targetLang.split("-")[0];

  const scoreVoice = (v: SpeechSynthesisVoice): number => {
    const name = v.name.toLowerCase();
    const vlang = v.lang.toLowerCase().replace("_", "-");
    let score = 0;

    // Prefer a voice for the target language (en prefers the Indian accent)
    if (vlang === targetLang) score += 70;
    else if (vlang.split("-")[0] === base) score += 60;
    if (base === "en" && vlang === "en-in") score += 50;

    // High fidelity natural voice indicators
    if (name.includes("natural") || name.includes("online (natural)")) score += 40;
    if (name.includes("neural")) score += 35;
    if (name.includes("google")) score += 30;
    if (name.includes("enhanced") || name.includes("premium")) score += 25;
    // Known premium Indian English voices on Chrome / Windows / Mac
    if (
      name.includes("swara") ||
      name.includes("rishi") ||
      name.includes("veena") ||
      name.includes("neerja") ||
      name.includes("lekha") ||
      name.includes("sangeeta") ||
      name.includes("karan")
    ) {
      score += 40;
    }

    return score;
  };

  const sorted = [...voices].sort((a, b) => scoreVoice(b) - scoreVoice(a));
  return sorted[0] || null;
}

export function speakFluent(
  rawText: string,
  langCode: string = "en",
  onEnd?: () => void,
  onStart?: () => void
): void {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    onEnd?.();
    return;
  }

  window.speechSynthesis.cancel();
  const cleaned = cleanTextForSpeech(rawText);
  if (!cleaned) {
    onEnd?.();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(cleaned);
  const voice = pickFluentVoice(langCode);
  if (voice) {
    utterance.voice = voice;
    utterance.lang = voice.lang;
  } else {
    utterance.lang = langCode === "en" ? "en-IN" : `${langCode}-IN`;
  }

  // Fluent, warm natural pacing
  utterance.rate = 0.98;
  utterance.pitch = 1.05;

  let finished = false;
  const finish = () => {
    if (!finished) {
      finished = true;
      onEnd?.();
    }
  };

  utterance.onstart = () => onStart?.();
  utterance.onend = finish;
  utterance.onerror = finish;

  window.speechSynthesis.speak(utterance);
}

export function stopFluentSpeech(): void {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}


// Spoken replies: on by default, the farmer can mute them (saved on this device)
const SPEAK_KEY = "app_voice_replies";
const readSpeak = (): boolean => {
  try {
    return localStorage.getItem(SPEAK_KEY) !== "off";
  } catch {
    return true;
  }
};
const [voiceReplies, setVoiceRepliesSignal] = createSignal(readSpeak());
export { voiceReplies };
export function setVoiceReplies(on: boolean): void {
  setVoiceRepliesSignal(on);
  if (!on) stopFluentSpeech();
  try {
    localStorage.setItem(SPEAK_KEY, on ? "on" : "off");
  } catch {
    // storage blocked — applies for this session only
  }
}
