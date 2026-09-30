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
import { speakFluent, stopFluentSpeech } from '../lib/fluent-tts';

type Message = { role: 'user' | 'assistant'; text: string; result?: AssistResult; proposalDone?: boolean; audioUrl?: string; audioMs?: number };

const STORAGE_KEY = 'assistant_chat';
const MAX_SAVED = 60;

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
        stopFluentSpeech();
        setSpeaking(false);
    };
    onCleanup(stopSpeaking);

    const speak = (text: string, language: string, then?: () => void) => {
        if (!text) return then?.();
        speakFluent(
            text,
            language || lang(),
            () => {
                setSpeaking(false);
                then?.();
            },
            () => setSpeaking(true),
        );
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
        <div class="fixed inset-x-0 top-0 bottom-16 z-30 flex flex-col bg-[#faf9f5] md:bottom-0 font-sans">
            {/* Stitch Header */}
            <header class="border-b border-emerald-900/10 bg-gradient-to-r from-[#004532] to-[#065f46] text-white shadow-sm">
                <div class="mx-auto flex max-w-6xl items-center justify-between gap-2 px-3 py-2.5 sm:px-4 sm:py-3">
                    <div class="flex min-w-0 items-center gap-2 sm:gap-3">
                        <A href="/dashboard" class="rounded-xl p-1.5 text-emerald-100 hover:text-white hover:bg-white/10 transition-colors" aria-label={t('chat.back')}>
                            <span class="material-symbols-outlined text-xl">arrow_back</span>
                        </A>
                        <div class="min-w-0">
                            <h1 class="flex items-center gap-2 font-bold text-white text-base">
                                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-white/10 text-emerald-200">
                                    <span class="material-symbols-outlined text-sm">auto_awesome</span>
                                </span>
                                <span class="truncate">{t('ai.title')}</span>
                                <span class="text-[10px] bg-emerald-400/25 text-emerald-100 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider hidden sm:inline-block">Pashu &amp; Farm Voice</span>
                            </h1>
                            <p class="hidden truncate text-xs text-emerald-100/80 sm:block">{t('chat.subtitle')}</p>
                        </div>
                    </div>
                    <div class="flex shrink-0 items-center gap-1.5">
                        <div class="hidden sm:block">
                            <LanguageSwitcher />
                        </div>
                        <button
                            type="button"
                            onClick={toggleTalk}
                            aria-pressed={talkMode()}
                            class={`rounded-xl px-3 py-1.5 text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${talkMode() ? 'bg-amber-400 text-amber-950 shadow-sm' : 'border border-emerald-300/30 text-white hover:bg-white/10'}`}
                            title={t('chat.talkHint')}
                        >
                            <span class="material-symbols-outlined text-base">record_voice_over</span>
                            <span class="hidden sm:inline"> {t('chat.talk')}</span>
                        </button>
                        <Show when={messages().length > 0}>
                            <button type="button" onClick={newChat} class="rounded-xl p-2 text-emerald-100 hover:text-white hover:bg-white/10 transition-colors" title={t('ai.newChat')}>
                                <span class="material-symbols-outlined text-base">refresh</span>
                            </button>
                        </Show>
                    </div>
                </div>
            </header>

            {/* Audio Waveform Visualizer Banner (Stitch) */}
            <Show when={recording() || speaking()}>
                <div class="bg-white border-b border-emerald-900/10 px-4 py-2.5 shadow-xs">
                    <div class="mx-auto max-w-6xl flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5">
                            <div class="w-8 h-8 rounded-full bg-[#004532] text-white flex items-center justify-center animate-pulse">
                                <span class="material-symbols-outlined text-base">{recording() ? 'mic' : 'volume_up'}</span>
                            </div>
                            <div>
                                <div class="flex items-center gap-1.5">
                                    <span class="text-xs font-bold text-slate-800">{recording() ? 'Listening to Farmer…' : 'Speaking…'}</span>
                                    <span class="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded font-bold">54 dB Stream</span>
                                </div>
                                <span class="text-[11px] text-[#004532] font-semibold block">"बोलिए, हम सुन रहे हैं..."</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-1 h-7 px-3 bg-emerald-50 rounded-xl border border-emerald-200">
                            <div class="w-1.5 bg-[#004532] rounded-full animate-bounce h-2"></div>
                            <div class="w-1.5 bg-emerald-600 rounded-full animate-bounce h-5" style="animation-delay: 0.15s"></div>
                            <div class="w-1.5 bg-emerald-500 rounded-full animate-bounce h-6" style="animation-delay: 0.3s"></div>
                            <div class="w-1.5 bg-[#004532] rounded-full animate-bounce h-4" style="animation-delay: 0.2s"></div>
                            <div class="w-1.5 bg-emerald-400 rounded-full animate-bounce h-3" style="animation-delay: 0.4s"></div>
                        </div>
                    </div>
                </div>
            </Show>

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
                                                <div class="max-w-[80%] rounded-2xl rounded-br-xs bg-[#004532] px-4 py-2.5 text-xs text-white shadow-sm">
                                                    <p class="leading-relaxed">{msg.text}</p>
                                                    <Show when={msg.audioUrl}>
                                                        <ClipPlayer url={msg.audioUrl!} durationMs={msg.audioMs} />
                                                    </Show>
                                                </div>
                                            </div>
                                        }
                                    >
                                        <div class="flex gap-2.5">
                                            <span class="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-xs text-[#004532] font-bold shadow-2xs">
                                                <span class="material-symbols-outlined text-sm">smart_toy</span>
                                            </span>
                                            <div class="min-w-0 max-w-[88%] space-y-2">
                                                <Show when={msg.text}>
                                                    <div class="rounded-2xl rounded-tl-xs bg-white border border-emerald-900/10 px-4 py-3 text-xs text-slate-800 shadow-sm leading-relaxed">
                                                        <p class="whitespace-pre-line">{msg.text}</p>
                                                        <button
                                                            type="button"
                                                            onClick={() => speak(msg.text, msg.result?.language || lang())}
                                                            class="mt-1.5 inline-flex items-center gap-1 text-[11px] font-bold text-[#004532] hover:text-emerald-700 cursor-pointer"
                                                        >
                                                            <span class="material-symbols-outlined text-xs">volume_up</span> {t('ai.listen')}
                                                        </button>
                                                    </div>
                                                </Show>

                                                {/* Stitch Quick-Reply Pill Options (1-by-1 Questions) */}
                                                <Show when={msg.result?.options && msg.result.options.length > 0}>
                                                    <div class="pt-1">
                                                        <p class="text-[11px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1">
                                                            <span class="material-symbols-outlined text-xs text-[#004532]">touch_app</span> Tap an option or speak:
                                                        </p>
                                                        <div class="flex flex-wrap gap-1.5">
                                                            <For each={msg.result!.options}>
                                                                {(opt) => (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => send({ text: opt })}
                                                                        class="px-3.5 py-1.5 rounded-full border border-emerald-900/15 bg-white hover:bg-emerald-50 hover:border-[#004532] text-slate-800 hover:text-[#004532] text-xs font-semibold shadow-2xs transition-all active:scale-[0.98] flex items-center gap-1.5 cursor-pointer"
                                                                    >
                                                                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                                                                        <span>{opt}</span>
                                                                    </button>
                                                                )}
                                                            </For>
                                                        </div>
                                                    </div>
                                                </Show>

                                                {/* Data preview */}
                                                <Show when={msg.result?.table}>
                                                    <DataTableCard table={msg.result!.table!} />
                                                </Show>

                                                {/* Which animal? */}
                                                <Show when={msg.result?.animal_options?.length}>
                                                    <div class="flex flex-wrap gap-1.5">
                                                        <For each={msg.result!.animal_options}>
                                                            {(id) => (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => {
                                                                        setFocusAnimalId(id);
                                                                        send({ text: animalLabel(id) });
                                                                    }}
                                                                    class="rounded-full border border-emerald-600 bg-white px-3 py-1.5 text-xs font-semibold text-emerald-900 hover:bg-emerald-50 shadow-2xs cursor-pointer"
                                                                >
                                                                    🐄 {animalLabel(id)}
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Pages to open */}
                                                <Show when={msg.result?.matches?.length}>
                                                    <div class="flex flex-wrap gap-1.5">
                                                        <For each={msg.result!.matches}>
                                                            {(m) => (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => go(m.id)}
                                                                    class="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:border-emerald-600 shadow-2xs"
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
                                <div class="flex items-center gap-2 text-xs text-slate-500 animate-pulse">
                                    <span class="w-2 h-2 rounded-full bg-emerald-600 animate-ping"></span>
                                    <span>{t('ai.thinking')}</span>
                                </div>
                            </Show>
                        </Show>
                    </div>

                    {/* Composer */}
                    <footer class="border-t border-emerald-900/10 bg-white p-3 space-y-2">
                        <Show when={focusAnimalId()}>
                            <div class="flex items-center justify-between rounded-xl bg-emerald-50 px-2.5 py-1.5 text-xs font-medium text-emerald-900">
                                <span class="truncate">{t('ai.talkingAbout', { name: animalLabel(focusAnimalId()) })}</span>
                                <button type="button" onClick={() => setFocusAnimalId(null)} class="ml-2 shrink-0 font-bold hover:underline">
                                    {t('ai.clearAnimal')}
                                </button>
                            </div>
                        </Show>
                        <Show when={talkMode()}>
                            <p class="text-center text-xs text-[#004532] font-semibold">
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
                                class={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-white transition-all cursor-pointer disabled:opacity-50 ${recording() ? 'animate-pulse bg-red-600 shadow-md shadow-red-500/30' : 'bg-[#004532] hover:bg-[#065f46] shadow-sm'}`}
                                aria-label={recording() ? t('ai.stop') : t('ai.record')}
                                title={recording() ? t('ai.stop') : t('ai.record')}
                            >
                                <span class="material-symbols-outlined text-xl">{recording() ? 'stop' : 'mic'}</span>
                            </button>
                            <input
                                type="text"
                                value={input()}
                                onInput={(e) => setInput(e.currentTarget.value)}
                                placeholder={recording() ? t('ai.listening') : t('chat.placeholder')}
                                disabled={recording()}
                                class="min-w-0 flex-1 rounded-xl border border-slate-200 bg-[#faf9f5] px-4 py-2.5 text-xs outline-none focus:border-[#004532] focus:ring-1 focus:ring-[#004532]"
                            />
                            <button
                                type="submit"
                                disabled={busy() || !input().trim()}
                                class="shrink-0 flex items-center gap-1 rounded-xl bg-[#004532] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#065f46] transition-all cursor-pointer shadow-sm disabled:opacity-50"
                            >
                                <span>{t('ai.send')}</span>
                                <span class="material-symbols-outlined text-sm">send</span>
                            </button>
                        </form>
                    </footer>
                </main>
            </div>
        </div>
    );
};

export default Assistant;
