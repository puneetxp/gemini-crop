/**
 * Assistant page (/assistant)
 * Full-screen chat with CropSense AI. Type or speak in any language; the AI
 * sees a summary of the farmer's own farms, crops, livestock and board figures,
 * so it can answer about their data (with small tables), open pages, and fill
 * records as a preview that is saved only on Approve.
 * Talk mode reads each reply aloud and then listens again, hands-free.
 */

import { Component, For, Show, createMemo, createSignal, onCleanup, onMount } from 'solid-js';
import { A, useNavigate, useSearchParams } from '@solidjs/router';
import { user } from '../stores/auth.store';
import { lang, t, tValue } from '../stores/i18n.store';
import { en, type TKey } from '../i18n/en';
import { SERVICE_GROUPS } from '../components/ui/ServicesMenu';
import LanguageSwitcher from '../components/ui/LanguageSwitcher';
import ProposalCard, { proposalTitle } from '../components/assistant/ProposalCard';
import { useRecorder, type VoiceClip } from '../components/assistant/useRecorder';
import ClipPlayer from '../components/assistant/ClipPlayer';
import { AssistantService, type AssistResult, type AssistTable, type Option } from '../services/assistant.service';
import { buildAssistantContext, clearAssistantContext } from '../services/assistant-context';
import { FarmService, LivestockService } from '../shared/Service/Services';
import { showToast } from '../components/ui/Toast';
import { useDeviceInfo } from '../utils/useResponsive';

type Message = { role: 'user' | 'assistant'; text: string; result?: AssistResult; proposalDone?: boolean; audioUrl?: string; audioMs?: number };

const STORAGE_KEY = 'assistant_chat';
const MAX_SAVED = 60;
const speechLang = (code: string) => `${code}-IN`;

const MENU = SERVICE_GROUPS.flatMap((g) => g.items);
const menuLabel = (id: string) => t(`svc.${id}` as TKey);
const menuItem = (id: string) => MENU.find((m) => m.id === id);

const SUGGESTIONS: TKey[] = ['chat.s.summary', 'chat.s.herd', 'chat.s.harvest', 'chat.s.profit', 'chat.s.addAnimal', 'chat.s.plant', 'chat.s.expense', 'chat.s.sell', 'chat.s.sick'];

const loadSaved = (): Message[] => {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? (JSON.parse(raw) as Message[]) : [];
    } catch {
        return [];
    }
};

const DataTableCard: Component<{ table: AssistTable }> = (props) => {
    const copy = async () => {
        const tsv = [props.table.columns, ...props.table.rows].map((r) => r.join('\t')).join('\n');
        try {
            await navigator.clipboard.writeText(tsv);
            showToast('success', t('chat.copied'));
        } catch {
            // clipboard blocked — nothing to do
        }
    };
    return (
        <div class="max-w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
            <div class="flex items-center justify-between gap-2 border-b border-gray-100 px-3 py-2">
                <p class="text-xs font-semibold text-gray-700">▦ {props.table.title || t('chat.data')}</p>
                <button type="button" onClick={copy} class="text-[11px] text-gray-500 hover:text-gray-900">
                    ⧉ {t('chat.copy')}
                </button>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead class="bg-gray-50 text-gray-500">
                        <tr>
                            <For each={props.table.columns}>{(c) => <th class="px-3 py-1.5 font-medium whitespace-nowrap">{c}</th>}</For>
                        </tr>
                    </thead>
                    <tbody>
                        <For each={props.table.rows}>
                            {(r) => (
                                <tr class="border-t border-gray-100">
                                    <For each={r}>{(cell) => <td class="px-3 py-1.5 text-gray-800 whitespace-nowrap">{cell}</td>}</For>
                                </tr>
                            )}
                        </For>
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export const Assistant: Component = () => {
    const navigate = useNavigate();
    const [messages, setMessages] = createSignal<Message[]>(loadSaved());
    const [input, setInput] = createSignal('');
    const [busy, setBusy] = createSignal(false);
    const [talkMode, setTalkMode] = createSignal(false);
    const [speaking, setSpeaking] = createSignal(false);
    const [focusAnimalId, setFocusAnimalId] = createSignal<number | null>(null);
    const [known, setKnown] = createSignal<{ farms: number; crops: number; animals: number } | null>(null);
    const deviceInfo = useDeviceInfo();
    let scrollEl: HTMLDivElement | undefined;

    const animals = createMemo(() => {
        try {
            const list = typeof (LivestockService as any)?.allstate === 'function' ? (LivestockService as any).allstate() : [];
            return ((list || []) as any[]).map((a) => ({
                id: a.id as number,
                label: [a.name, a.breed, tValue('species', a.species)].filter(Boolean).join(' · ') + ` #${a.id}`,
            }));
        } catch {
            return [];
        }
    });
    const animalLabel = (id: number | null) => animals().find((a) => a.id === id)?.label || '';
    const farmOptions = createMemo<Option[]>(() => {
        try {
            const list = typeof (FarmService as any)?.allstate === 'function' ? (FarmService as any).allstate() : [];
            return ((list || []) as any[]).map((f) => ({ id: f.id as number, label: `${f.name || 'Farm'} #${f.id}` }));
        } catch {
            return [];
        }
    });
    const [crops, setCrops] = createSignal<Option[]>([]);
    const loadCrops = async () => setCrops(await AssistantService.cropOptions());

    const persist = (list: Message[]) => {
        setMessages(list);
        try {
            // Proposals already handled are kept only as text
            // Recording URLs only live for this visit, so they aren't saved
            localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(-MAX_SAVED).map(({ audioUrl, ...m }) => m)));
        } catch {
            // storage blocked — chat still works for this visit
        }
    };

    const scrollDown = () => queueMicrotask(() => scrollEl?.scrollTo({ top: scrollEl.scrollHeight, behavior: 'smooth' }));

    const refreshKnown = async (force = false) => {
        const id = user()?.id;
        if (!id) return '';
        const ctx = await buildAssistantContext(id, force);
        const count = (label: string) => Number(ctx.match(new RegExp(`${label} \\((\\d+)`))?.[1] || 0);
        const heads = Number(ctx.match(/records, (\d+) animals/)?.[1] || 0);
        setKnown({ farms: count('FARMS'), crops: count('ACTIVE CROPS'), animals: heads });
        return ctx;
    };

    // The dashboard's "Ask or add anything" card hands over with ?q=<text> or ?mic=1
    const [searchParams, setSearchParams] = useSearchParams();

    onMount(() => {
        LivestockService.all();
        FarmService.all();
        loadCrops();
        refreshKnown();
        scrollDown();
        const q = typeof searchParams.q === 'string' ? searchParams.q.trim() : '';
        const mic = searchParams.mic === '1';
        if (q || mic) {
            // Clear them so a reload doesn't resend
            setSearchParams({ q: undefined, mic: undefined }, { replace: true });
            if (q) send({ text: q.slice(0, 1000) });
            else recorder.start();
        }
    });

    const stopSpeaking = () => {
        window.speechSynthesis?.cancel();
        setSpeaking(false);
    };
    onCleanup(stopSpeaking);

    const speak = (text: string, language: string, then?: () => void) => {
        if (!('speechSynthesis' in window) || !text) return then?.();
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = speechLang(language || lang());
        u.onend = () => {
            setSpeaking(false);
            then?.();
        };
        u.onerror = () => setSpeaking(false);
        setSpeaking(true);
        window.speechSynthesis.speak(u);
    };

    const go = (id: string) => {
        const item = menuItem(id);
        if (item) navigate(item.path);
    };

    const send = async (payload: { text?: string; clip?: VoiceClip }) => {
        const text = payload.text?.trim();
        if (!text && !payload.clip) return;
        stopSpeaking();
        const history = messages()
            .filter((m) => m.text)
            .slice(-10)
            .map((m) => ({ role: m.role, text: m.text.slice(0, 1000) }));
        persist([...messages(), { role: 'user', text: text || '🎤 …', audioUrl: payload.clip?.url, audioMs: payload.clip?.durationMs }]);
        setInput('');
        setBusy(true);
        scrollDown();

        try {
            const context = await refreshKnown().catch(() => '');
            const result = await AssistantService.assist({
                text,
                ...(payload.clip ? await AssistantService.audioFields(payload.clip) : {}),
                lang: lang(),
                menu: MENU.map((m) => ({ id: m.id, label: `${menuLabel(m.id)} / ${en[`svc.${m.id}` as TKey]}` })),
                animals: animals(),
                farms: farmOptions(),
                crops: crops(),
                history,
                focus_animal_id: focusAnimalId(),
                context: context || undefined,
            });
            if (payload.clip && result.transcript) {
                const list = [...messages()];
                list[list.length - 1] = { ...list[list.length - 1], text: result.transcript };
                persist(list);
            }
            persist([...messages(), { role: 'assistant', text: result.reply, result }]);
            if (result.proposal?.fields?.livestock_id) setFocusAnimalId(Number(result.proposal.fields.livestock_id));
            // Talk mode: read the reply, then listen again (unless a form or choice needs a tap)
            if (talkMode()) {
                const needsTap = !!result.proposal || !!result.animal_options?.length;
                speak(result.reply, result.language, () => {
                    if (talkMode() && !needsTap && !busy()) recorder.start();
                });
            } else if (payload.clip && result.reply) {
                // Asked by voice: answer by voice
                speak(result.reply, result.language);
            }
        } catch (err: any) {
            const unavailable = err?.status === 503 || /unavailable/i.test(err?.message || '');
            const reason = AssistantService.errorReason(err);
            const base = unavailable ? t('ai.unavailable') : t('ai.error');
            persist([...messages(), { role: 'assistant', text: reason && reason !== base ? `${base}\n(${reason})` : base }]);
        } finally {
            setBusy(false);
            scrollDown();
        }
    };

    const recorder = useRecorder((clip) => send({ clip }));
    const recording = recorder.recording;

    const toggleTalk = () => {
        const on = !talkMode();
        setTalkMode(on);
        if (!on) {
            stopSpeaking();
            recorder.stop(true);
        } else if (!recording() && !busy()) {
            recorder.start();
        }
    };

    const newChat = () => {
        stopSpeaking();
        recorder.stop(true);
        setFocusAnimalId(null);
        clearAssistantContext();
        refreshKnown(true);
        persist([]);
    };

    const markProposalDone = (index: number) => {
        const list = [...messages()];
        list[index] = { ...list[index], proposalDone: true };
        persist(list);
    };

    return (
        // Fixed to the viewport: bottom-16 leaves room for the mobile bottom nav
        <div class="fixed inset-x-0 top-0 bottom-16 z-30 flex flex-col bg-gray-50 md:bottom-0">
            {/* Header */}
            <header class="border-b border-gray-200 bg-white">
                <div class="mx-auto flex max-w-6xl items-center justify-between gap-2 px-3 py-2.5 sm:px-4 sm:py-3">
                    <div class="flex min-w-0 items-center gap-2 sm:gap-3">
                        <A href="/dashboard" class="rounded-md px-2 py-1 text-gray-500 hover:bg-gray-100" aria-label={t('chat.back')}>
                            ←
                        </A>
                        <div class="min-w-0">
                            <h1 class="flex items-center gap-2 font-bold text-gray-900">
                                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-green-600 text-sm text-white">✦</span>
                                <span class="truncate">{t('ai.title')}</span>
                            </h1>
                            <p class="hidden truncate text-xs text-gray-500 sm:block">{t('chat.subtitle')}</p>
                        </div>
                    </div>
                    <div class="flex shrink-0 items-center gap-1">
                        <div class="hidden sm:block">
                            <LanguageSwitcher />
                        </div>
                        <button
                            type="button"
                            onClick={toggleTalk}
                            aria-pressed={talkMode()}
                            class={`rounded-full px-3 py-1.5 text-xs font-medium ${talkMode() ? 'bg-green-600 text-white' : 'border border-gray-300 text-gray-700 hover:bg-gray-50'}`}
                            title={t('chat.talkHint')}
                        >
                            🗣️<span class="hidden sm:inline"> {t('chat.talk')}</span>
                        </button>
                        <Show when={messages().length > 0}>
                            <button type="button" onClick={newChat} class="rounded-md px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-100">
                                ↺<span class="hidden sm:inline"> {t('ai.newChat')}</span>
                            </button>
                        </Show>
                    </div>
                </div>
            </header>

            <div class="mx-auto flex w-full max-w-6xl flex-1 gap-4 overflow-hidden px-0 py-0 sm:px-4 sm:py-4">
                {/* Side panel: what the assistant knows + suggestions */}
                <aside class="hidden w-64 shrink-0 space-y-4 overflow-y-auto lg:block">
                    <section class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                        <h2 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{t('chat.knows')}</h2>
                        <Show when={known()} fallback={<p class="mt-2 text-sm text-gray-400 animate-pulse">{t('chat.loadingData')}</p>}>
                            <ul class="mt-2 space-y-1.5 text-sm text-gray-700">
                                <li>🏡 {t('chat.nFarms', { n: String(known()!.farms) })}</li>
                                <li>🌱 {t('chat.nCrops', { n: String(known()!.crops) })}</li>
                                <li>🐄 {t('chat.nAnimals', { n: String(known()!.animals) })}</li>
                                <li>📊 {t('chat.boardFigures')}</li>
                            </ul>
                        </Show>
                        <p class="mt-3 text-[11px] text-gray-400">{t('chat.privacy')}</p>
                    </section>
                    <section class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                        <h2 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{t('chat.try')}</h2>
                        <div class="mt-2 space-y-1.5">
                            <For each={SUGGESTIONS}>
                                {(k) => (
                                    <button
                                        type="button"
                                        disabled={busy()}
                                        onClick={() => send({ text: t(k) })}
                                        class="w-full rounded-md px-2 py-1.5 text-left text-sm text-gray-700 hover:bg-green-50 hover:text-green-800 disabled:opacity-50"
                                    >
                                        {t(k)}
                                    </button>
                                )}
                            </For>
                        </div>
                    </section>
                    <Show when={animals().length > 0}>
                        <section class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                            <h2 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{t('ai.myAnimals')}</h2>
                            <div class="mt-2 flex flex-wrap gap-1.5">
                                <For each={animals()}>
                                    {(a) => (
                                        <button
                                            type="button"
                                            onClick={() => setFocusAnimalId(focusAnimalId() === a.id ? null : a.id)}
                                            class={`rounded-full border px-2.5 py-1 text-xs ${focusAnimalId() === a.id ? 'border-green-600 bg-green-600 text-white' : 'border-gray-300 text-gray-700 hover:border-green-400'}`}
                                        >
                                            🐄 {a.label}
                                        </button>
                                    )}
                                </For>
                            </div>
                        </section>
                    </Show>
                </aside>

                {/* Conversation */}
                <main class="flex min-w-0 flex-1 flex-col overflow-hidden bg-white sm:rounded-xl sm:border sm:border-gray-200 sm:shadow-sm">
                    <div ref={scrollEl} class="flex-1 space-y-4 overflow-y-auto px-4 py-4 sm:px-6">
                        <Show
                            when={messages().length > 0}
                            fallback={
                                <div class="mx-auto max-w-xl py-10 text-center">
                                    <div class="text-5xl">🌾</div>
                                    <h2 class="mt-3 text-xl font-semibold text-gray-900">{t('chat.hello', { name: user()?.full_name || '' })}</h2>
                                    <p class="mt-1 text-sm text-gray-600">{t('chat.intro')}</p>
                                    <div class="mt-3 flex justify-center sm:hidden">
                                        <LanguageSwitcher />
                                    </div>
                                    <div class="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
                                        <For each={SUGGESTIONS}>
                                            {(k) => (
                                                <button
                                                    type="button"
                                                    onClick={() => send({ text: t(k) })}
                                                    class="rounded-lg border border-gray-200 px-3 py-2.5 text-left text-sm text-gray-700 hover:border-green-400 hover:bg-green-50"
                                                >
                                                    {t(k)}
                                                </button>
                                            )}
                                        </For>
                                    </div>
                                </div>
                            }
                        >
                            <For each={messages()}>
                                {(msg, i) => (
                                    <Show
                                        when={msg.role === 'assistant'}
                                        fallback={
                                            <div class="flex justify-end">
                                                <div class="max-w-[80%] rounded-2xl rounded-br-sm bg-green-600 px-4 py-2 text-sm text-white">
                                                    {msg.text}
                                                    <Show when={msg.audioUrl}>
                                                        <ClipPlayer url={msg.audioUrl!} durationMs={msg.audioMs} />
                                                    </Show>
                                                </div>
                                            </div>
                                        }
                                    >
                                        <div class="flex gap-2">
                                            <span class="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-green-100 text-xs text-green-700">✦</span>
                                            <div class="min-w-0 max-w-[88%] space-y-2">
                                                <Show when={msg.text}>
                                                    <div class="rounded-2xl rounded-tl-sm bg-gray-100 px-4 py-2 text-sm text-gray-800">
                                                        <p class="whitespace-pre-line">{msg.text}</p>
                                                        <button
                                                            type="button"
                                                            onClick={() => speak(msg.text, msg.result?.language || lang())}
                                                            class="mt-1 text-xs font-medium text-green-700 hover:text-green-900"
                                                        >
                                                            🔊 {t('ai.listen')}
                                                        </button>
                                                    </div>
                                                </Show>

                                                {/* Data preview */}
                                                <Show when={msg.result?.table}>
                                                    <DataTableCard table={msg.result!.table!} />
                                                </Show>

                                                {/* Which animal? */}
                                                <Show when={msg.result?.animal_options?.length}>
                                                    <div class="flex flex-wrap gap-2">
                                                        <For each={msg.result!.animal_options}>
                                                            {(id) => (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => {
                                                                        setFocusAnimalId(id);
                                                                        send({ text: animalLabel(id) });
                                                                    }}
                                                                    class="rounded-full border border-green-500 bg-white px-3 py-1.5 text-sm text-green-800 hover:bg-green-50"
                                                                >
                                                                    🐄 {animalLabel(id)}
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Pages to open */}
                                                <Show when={msg.result?.matches?.length}>
                                                    <div class="flex flex-wrap gap-2">
                                                        <For each={msg.result!.matches}>
                                                            {(m) => (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => go(m.id)}
                                                                    class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-800 hover:border-green-500"
                                                                >
                                                                    {menuItem(m.id)?.emoji} {menuLabel(m.id)} →
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Record preview → approve */}
                                                <Show when={msg.result?.proposal && !msg.proposalDone}>
                                                    <ProposalCard
                                                        proposal={msg.result!.proposal!}
                                                        animals={animals()}
                                                        crops={crops()}
                                                        onSaved={() => {
                                                            markProposalDone(i());
                                                            // Refresh whatever the new record may have changed
                                                            LivestockService.all();
                                                            FarmService.all();
                                                            loadCrops();
                                                            clearAssistantContext();
                                                            refreshKnown(true);
                                                            persist([...messages(), { role: 'assistant', text: `✓ ${t('ai.saved')}: ${proposalTitle(msg.result!.proposal!.entity)}` }]);
                                                            showToast('success', t('ai.saved'));
                                                            scrollDown();
                                                        }}
                                                        onCancel={() => markProposalDone(i())}
                                                    />
                                                </Show>
                                            </div>
                                        </div>
                                    </Show>
                                )}
                            </For>
                            <Show when={busy()}>
                                <div class="flex items-center gap-2 text-sm text-gray-500">
                                    <span class="flex h-7 w-7 items-center justify-center rounded-full bg-green-100 text-xs text-green-700">✦</span>
                                    <span class="animate-pulse">{t('ai.thinking')}</span>
                                </div>
                            </Show>
                        </Show>
                    </div>

                    {/* Composer */}
                    <footer class="border-t border-gray-200 p-3">
                        <Show when={focusAnimalId()}>
                            <div class="mb-2 flex items-center justify-between rounded bg-green-50 px-2 py-1 text-xs text-green-800">
                                <span class="truncate">{t('ai.talkingAbout', { name: animalLabel(focusAnimalId()) })}</span>
                                <button type="button" onClick={() => setFocusAnimalId(null)} class="ml-2 shrink-0 font-medium hover:underline">
                                    {t('ai.clearAnimal')}
                                </button>
                            </div>
                        </Show>
                        <Show when={talkMode()}>
                            <p class="mb-2 text-center text-xs text-green-700">
                                {speaking() ? `🔊 ${t('chat.speaking')}` : recording() ? `🎤 ${t('chat.listeningTap')}` : busy() ? t('ai.thinking') : t('chat.talkHint')}
                            </p>
                        </Show>
                        <form
                            class="flex items-center gap-2"
                            onSubmit={(e) => {
                                e.preventDefault();
                                send({ text: input() });
                            }}
                        >
                            <button
                                type="button"
                                onClick={() => {
                                    stopSpeaking();
                                    recorder.toggle();
                                }}
                                disabled={busy()}
                                class={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-xl text-white disabled:opacity-50 ${recording() ? 'animate-pulse bg-red-600' : 'bg-green-600 hover:bg-green-700'}`}
                                aria-label={recording() ? t('ai.stop') : t('ai.record')}
                                title={recording() ? t('ai.stop') : t('ai.record')}
                            >
                                {recording() ? '■' : '🎤'}
                            </button>
                            <input
                                type="text"
                                value={input()}
                                onInput={(e) => setInput(e.currentTarget.value)}
                                placeholder={recording() ? t('ai.listening') : t('chat.placeholder')}
                                disabled={recording()}
                                class="min-w-0 flex-1 rounded-full border border-gray-300 px-4 py-3 text-sm outline-none focus:border-green-500"
                            />
                            <button
                                type="submit"
                                disabled={busy() || !input().trim()}
                                class="shrink-0 rounded-full bg-green-600 px-5 py-3 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                            >
                                {t('ai.send')}
                            </button>
                        </form>
                    </footer>
                </main>
            </div>
        </div>
    );
};

export default Assistant;
