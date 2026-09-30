/**
 * Language Switcher
 * Compact 🌐 select that changes the UI language app-wide.
 */

import { Component, For } from 'solid-js';
import { LANGUAGES, lang, setLang, t, type Lang } from '../../stores/i18n.store';

const LanguageSwitcher: Component<{ class?: string }> = (props) => (
    <label class={`inline-flex items-center gap-1 text-gray-600 ${props.class || ''}`} title={t('lang.label')}>
        <span aria-hidden="true">🌐</span>
        <select
            value={lang()}
            onChange={(e) => setLang(e.currentTarget.value as Lang)}
            aria-label={t('lang.label')}
            class="bg-transparent border border-gray-200 hover:border-green-400 rounded-md px-2 py-1.5 text-sm outline-none focus:border-green-500 cursor-pointer"
        >
            <For each={LANGUAGES}>{(l) => <option value={l.code}>{l.label}</option>}</For>
        </select>
    </label>
);

export default LanguageSwitcher;
