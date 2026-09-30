/**
 * Language store
 * Current UI language plus t() for translated strings. The language comes
 * from (in order) the viewer's explicit choice saved on this device, the
 * user's profile language_preference, then English. Missing keys fall back
 * to English, so a partly translated language never shows blanks.
 */

import { createRoot, createSignal, createEffect } from 'solid-js';
import { user } from './auth.store';
import { en, type TKey, type Dictionary } from '../i18n/en';
import LANGUAGE_CONFIG from '../i18n/languages.json';

// Every src/i18n/<code>.ts exports `const <code>: Dictionary` — written by
// `npm run i18n:translate` for each language in i18n/languages.json.
const modules = import.meta.glob('../i18n/*.ts', { eager: true }) as Record<string, Record<string, unknown>>;
const DICTIONARIES: Record<string, Dictionary> = { en };
for (const [path, mod] of Object.entries(modules)) {
    const code = path.match(/\/([a-z]{2,3})\.ts$/)?.[1];
    if (code && code !== 'en' && mod[code]) DICTIONARIES[code] = mod[code] as Dictionary;
}

export type Lang = string;

/** Languages offered in the picker: configured and with a dictionary built */
export const LANGUAGES: { code: Lang; label: string; name: string }[] = LANGUAGE_CONFIG.filter(
    (l) => l.code in DICTIONARIES,
);

const STORAGE_KEY = 'app_lang';

const isLang = (v: unknown): v is Lang => typeof v === 'string' && v in DICTIONARIES;

const readSaved = (): Lang | null => {
    try {
        const v = localStorage.getItem(STORAGE_KEY);
        return isLang(v) ? v : null;
    } catch {
        return null;
    }
};

const [lang, setLangSignal] = createSignal<Lang>(readSaved() || 'en');

// Until the viewer picks a language here, follow their profile setting
createRoot(() => {
    createEffect(() => {
        const pref = user()?.language_preference;
        if (!readSaved() && isLang(pref)) setLangSignal(pref);
    });
});

export function setLang(next: Lang) {
    setLangSignal(next);
    try {
        localStorage.setItem(STORAGE_KEY, next);
    } catch {
        // storage blocked — choice lasts for this session only
    }
    document.documentElement.lang = next;
}

/** Translate a key, filling {placeholders} from vars */
export function t(key: TKey, vars?: Record<string, string | number>): string {
    let s = DICTIONARIES[lang()]?.[key] ?? en[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, String(v));
    return s;
}

/** Translate a value that came from the API (e.g. species), or show it as-is */
export function tValue(prefix: 'species' | 'health', value?: string | null): string {
    if (!value) return '';
    const key = `${prefix}.${value.toLowerCase()}` as TKey;
    return key in en ? t(key) : value;
}

export { lang };
export type SupportedLanguage = Lang;
export const currentLanguage = lang;
export const setLanguage = setLang;
