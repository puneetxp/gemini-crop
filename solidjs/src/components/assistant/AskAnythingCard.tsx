/**
 * Ask or add anything (Dashboard)
 * One box for the whole farm, not just livestock: the farmer types or taps the
 * mic and lands in the full AI chat (/assistant), which knows their farms,
 * crops and animals and can fill any form (farm, crop, expense, sale, animal,
 * health record). Example chips show what it can do.
 */

import { Component, For, createSignal } from 'solid-js';
import { useNavigate } from '@solidjs/router';
import { t } from '../../stores/i18n.store';
import type { TKey } from '../../i18n/en';

const EXAMPLES: TKey[] = ['ask.ex.crop', 'ask.ex.expense', 'ask.ex.pest', 'ask.ex.sell', 'ask.ex.animal'];

const AskAnythingCard: Component = () => {
    const navigate = useNavigate();
    const [input, setInput] = createSignal('');

    const ask = (text: string) => {
        const q = text.trim();
        if (q) navigate(`/assistant?q=${encodeURIComponent(q)}`);
    };

    return (
        <section class="bg-white rounded-lg shadow-md p-4 sm:p-6 border border-green-100" aria-label={t('ask.title')}>
            <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
                <span>✦</span> {t('ask.title')}
            </h2>
            <p class="text-sm text-gray-600 mt-1">{t('ask.subtitle')}</p>

            <form
                class="mt-4 flex items-center gap-2"
                onSubmit={(e) => {
                    e.preventDefault();
                    ask(input());
                }}
            >
                <button
                    type="button"
                    onClick={() => navigate('/assistant?mic=1')}
                    class="shrink-0 w-11 h-11 rounded-full text-lg flex items-center justify-center text-white bg-green-600 hover:bg-green-700"
                    aria-label={t('ai.record')}
                    title={t('ai.record')}
                >
                    🎤
                </button>
                <input
                    type="text"
                    value={input()}
                    onInput={(e) => setInput(e.currentTarget.value)}
                    placeholder={t('ask.placeholder')}
                    class="flex-1 min-w-0 border border-gray-300 rounded-md px-3 py-2.5 outline-none focus:border-green-500"
                />
                <button
                    type="submit"
                    disabled={!input().trim()}
                    class="shrink-0 px-4 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium rounded-md"
                >
                    {t('ai.send')}
                </button>
            </form>

            <div class="mt-3 flex flex-wrap gap-2">
                <button
                    type="button"
                    onClick={() => navigate('/diagnose')}
                    class="px-3 py-1.5 rounded-full border border-green-300 bg-green-50 hover:bg-green-100 text-sm text-green-800 font-medium"
                >
                    🔬 {t('diag.title')}
                </button>
                <For each={EXAMPLES}>
                    {(key) => (
                        <button
                            type="button"
                            onClick={() => ask(t(key))}
                            class="px-3 py-1.5 rounded-full border border-gray-200 bg-gray-50 hover:bg-green-50 hover:border-green-300 text-sm text-gray-700"
                        >
                            {t(key)}
                        </button>
                    )}
                </For>
            </div>
        </section>
    );
};

export default AskAnythingCard;
