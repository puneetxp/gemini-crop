/**
 * Assistant Page (/assistant)
 * Conversational Agronomist & Farm Copilot.
 *
 * Implements the complete proven 2-column architecture from the previous design:
 * - Left Sidebar: What CropSense Knows (live farm, crop & herd counts), Try Asking suggestions, and My Animals chips.
 * - Main Conversation Area: Stream with fluent TTS, 1-by-1 quick-reply chips, data tables, and embedded ProposalCards.
 * - Enhanced with Stitch AgriSense Premier tokens, animated voice waveform visualizer, and Conversation Archiving.
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
import { AssistantService, type AssistProposal, type AssistResult, type AssistTable, type Option } from '../services/assistant.service';
import { AssistantArchiveService, type ArchivedSession } from '../services/assistant-archive.service';
import { buildAssistantContext, clearAssistantContext } from '../services/assistant-context';
import { FarmService, LivestockService } from '../shared/Service/Services';
import { showToast } from '../components/ui/Toast';
import { speakFluent, stopFluentSpeech } from '../lib/fluent-tts';

type Message = {
    role: 'user' | 'assistant';
    text: string;
    result?: AssistResult;
    proposalDone?: boolean;
    audioUrl?: string;
    audioMs?: number;
    timestamp?: string;
};

const STORAGE_KEY = 'cropsense_assistant_active_chat';
const MAX_SAVED = 60;

const MENU = SERVICE_GROUPS.flatMap((g) => g.items);
const menuLabel = (id: string) => t(`svc.${id}` as TKey);
const menuItem = (id: string) => MENU.find((m) => m.id === id);

const SUGGESTIONS: TKey[] = [
    'chat.s.summary',
    'chat.s.herd',
    'chat.s.harvest',
    'chat.s.profit',
    'chat.s.addAnimal',
    'chat.s.plant',
    'chat.s.expense',
    'chat.s.sell',
    'chat.s.sick',
];

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
            // clipboard blocked
        }
    };
    return (
        <div class="max-w-full overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm my-2">
            <div class="flex items-center justify-between gap-2 border-b border-outline-variant/60 px-3.5 py-2 bg-surface-container-low">
                <p class="text-label-sm font-label-sm text-primary flex items-center gap-1.5 font-bold">
                    <span class="material-symbols-outlined text-sm">table_chart</span>
                    <span>{props.table.title || t('chat.data')}</span>
                </p>
                <button type="button" onClick={copy} class="text-xs text-outline hover:text-primary transition-colors flex items-center gap-1 cursor-pointer">
                    <span class="material-symbols-outlined text-xs">content_copy</span>
                    <span>{t('chat.copy')}</span>
                </button>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-body-sm">
                    <thead class="bg-surface-container text-outline text-[11px] uppercase tracking-wider font-semibold">
                        <tr>
                            <For each={props.table.columns}>{(c) => <th class="px-3 py-1.5 font-medium whitespace-nowrap">{c}</th>}</For>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-outline-variant/40">
                        <For each={props.table.rows}>
                            {(r) => (
                                <tr class="hover:bg-surface-container-high/40 transition-colors">
                                    <For each={r}>{(cell) => <td class="px-3 py-1.5 text-on-surface whitespace-nowrap text-xs">{cell}</td>}</For>
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
    const [known, setKnown] = createSignal<{ farms: number; crops: number; animals: number; activeFarmName?: string } | null>(null);
    const [archiveDrawerOpen, setArchiveDrawerOpen] = createSignal(false);
    const [archives, setArchives] = createSignal<ArchivedSession[]>(AssistantArchiveService.getArchives());

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
            localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(-MAX_SAVED).map(({ audioUrl, ...m }) => m)));
        } catch {
            // storage restricted fallback
        }
    };

    const scrollDown = () => queueMicrotask(() => scrollEl?.scrollTo({ top: scrollEl.scrollHeight, behavior: 'smooth' }));

    const refreshKnown = async (force = false) => {
        const id = user()?.id;
        if (!id) return '';
        const ctx = await buildAssistantContext(id, force);
        const count = (label: string) => Number(ctx.match(new RegExp(`${label} \\((\\d+)`))?.[1] || 0);
        const heads = Number(ctx.match(/records, (\d+) animals/)?.[1] || 0);
        const firstFarmMatch = ctx.match(/FARMS \(\d+\):\n- #\d+ ([^:]+):/);
        const activeFarmName = firstFarmMatch ? firstFarmMatch[1] : farmOptions()[0]?.label?.split(' #')[0] || 'Krishna Valley Farm';

        setKnown({
            farms: count('FARMS'),
            crops: count('ACTIVE CROPS'),
            animals: heads,
            activeFarmName,
        });
        return ctx;
    };

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

    // Send text or voice recording
    const send = async (payload: { text?: string; clip?: VoiceClip }) => {
        const text = payload.text?.trim();
        if (!text && !payload.clip) return;
        stopSpeaking();

        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const history = messages()
            .filter((m) => m.text)
            .slice(-10)
            .map((m) => ({ role: m.role, text: m.text.slice(0, 1000) }));

        persist([
            ...messages(),
            {
                role: 'user',
                text: text || '🎤 …',
                audioUrl: payload.clip?.url,
                audioMs: payload.clip?.durationMs,
                timestamp: timeStr,
            },
        ]);
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

            const replyTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            persist([...messages(), { role: 'assistant', text: result.reply, result, timestamp: replyTime }]);

            if (result.proposal?.fields?.livestock_id) setFocusAnimalId(Number(result.proposal.fields.livestock_id));

            // Talk mode: read reply, then continue listening if hands-free
            if (talkMode()) {
                const needsTap = !!result.proposal || !!result.animal_options?.length;
                speak(result.reply, result.language, () => {
                    if (talkMode() && !needsTap && !busy()) recorder.start();
                });
            } else if (payload.clip && result.reply) {
                speak(result.reply, result.language);
            }
        } catch (err: any) {
            const unavailable = err?.status === 503 || /unavailable/i.test(err?.message || '');
            const reason = AssistantService.errorReason(err);
            const base = unavailable ? t('ai.unavailable') : t('ai.error');
            const errTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            persist([...messages(), { role: 'assistant', text: reason && reason !== base ? `${base}\n(${reason})` : base, timestamp: errTime }]);
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

    /**
     * Archive active conversation and reset to fresh clean slate
     */
    const resetAndArchive = () => {
        stopSpeaking();
        recorder.stop(true);

        const currentMessages = messages();
        if (currentMessages.length > 0) {
            // Find active proposal if any
            const lastProposal = currentMessages.slice().reverse().find((m) => m.result?.proposal && !m.proposalDone)?.result?.proposal;
            const archived = AssistantArchiveService.archiveSession(currentMessages, lastProposal, focusAnimalId());
            if (archived) {
                setArchives(AssistantArchiveService.getArchives());
                showToast('success', `Conversation archived as "${archived.title}"`);
            }
        }

        setFocusAnimalId(null);
        clearAssistantContext();
        refreshKnown(true);
        persist([]);
        showToast('info', 'Session reset. Ready for new questions.');
    };

    /**
     * Restore an archived conversation
     */
    const restoreArchivedSession = (sessionId: string) => {
        const session = AssistantArchiveService.restoreSession(sessionId);
        if (!session) {
            showToast('error', 'Could not find session in archive');
            return;
        }

        if (messages().length > 0) {
            AssistantArchiveService.archiveSession(messages());
            setArchives(AssistantArchiveService.getArchives());
        }

        persist(session.messages || []);
        if (session.focusAnimalId) setFocusAnimalId(session.focusAnimalId);
        setArchiveDrawerOpen(false);
        showToast('success', `Restored session "${session.title}"`);
        scrollDown();
    };

    /**
     * Delete an archive item
     */
    const deleteArchivedSession = (sessionId: string, e: MouseEvent) => {
        e.stopPropagation();
        AssistantArchiveService.deleteArchive(sessionId);
        setArchives(AssistantArchiveService.getArchives());
        showToast('info', 'Archived conversation deleted');
    };

    const markProposalDone = (index: number) => {
        const list = [...messages()];
        list[index] = { ...list[index], proposalDone: true };
        persist(list);
    };

    return (
        // Fixed to viewport: bottom-16 leaves room for mobile bottom dock; on desktop fits full viewport
        <div class="fixed inset-x-0 top-0 bottom-16 z-30 flex flex-col bg-surface md:bottom-0 font-body-md text-on-surface">
            {/* Header (Stitch AgriSense Premier Header) */}
            <header class="border-b border-outline-variant bg-surface-container-lowest shadow-sm shrink-0">
                <div class="mx-auto flex max-w-6xl items-center justify-between gap-2 px-3 py-2.5 sm:px-4 sm:py-3">
                    <div class="flex min-w-0 items-center gap-2 sm:gap-3">
                        <A
                            href="/dashboard"
                            class="rounded-xl p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-container-high transition-colors"
                            aria-label={t('chat.back')}
                        >
                            <span class="material-symbols-outlined text-xl">arrow_back</span>
                        </A>
                        <div class="min-w-0">
                            <h1 class="flex items-center gap-2 font-bold text-on-surface text-base">
                                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-primary-container text-on-primary-container shadow-xs">
                                    <span class="material-symbols-outlined text-sm">auto_awesome</span>
                                </span>
                                <span class="truncate">{t('ai.title')}</span>
                                <span class="text-[10px] bg-[#d1fae5] text-primary px-2 py-0.5 rounded-full font-bold hidden sm:inline-block border border-primary/20">
                                    AgriSense Premier
                                </span>
                            </h1>
                            <p class="hidden truncate text-xs text-outline sm:block">{t('chat.subtitle')}</p>
                        </div>
                    </div>

                    <div class="flex shrink-0 items-center gap-2">
                        <div class="hidden sm:block">
                            <LanguageSwitcher />
                        </div>

                        {/* Hands-Free Talk Mode Button */}
                        <button
                            type="button"
                            onClick={toggleTalk}
                            aria-pressed={talkMode()}
                            class={`rounded-xl px-3 py-1.5 text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                                talkMode()
                                    ? 'bg-primary text-on-primary shadow-xs'
                                    : 'border border-outline-variant bg-surface-container text-on-surface hover:bg-surface-container-high'
                            }`}
                            title={t('chat.talkHint')}
                        >
                            <span class="material-symbols-outlined text-base">record_voice_over</span>
                            <span class="hidden sm:inline"> {talkMode() ? 'Hands-Free (Active)' : t('chat.talk')}</span>
                        </button>

                        {/* Archive Drawer Button */}
                        <button
                            type="button"
                            onClick={() => setArchiveDrawerOpen(true)}
                            class="rounded-xl px-3 py-1.5 text-xs font-bold border border-outline-variant bg-surface-container text-on-surface hover:bg-surface-container-high transition-colors flex items-center gap-1.5 cursor-pointer"
                            title="View Archived Conversations"
                        >
                            <span class="material-symbols-outlined text-base text-primary">history</span>
                            <span class="hidden sm:inline">Archive ({archives().length})</span>
                        </button>

                        {/* Restart Session / Reset Button */}
                        <button
                            type="button"
                            onClick={resetAndArchive}
                            class="rounded-xl px-3 py-1.5 text-xs font-bold border border-outline-variant bg-surface-container text-outline hover:text-error hover:border-error transition-colors flex items-center gap-1.5 cursor-pointer"
                            title="Reset and Archive Conversation"
                        >
                            <span class="material-symbols-outlined text-base">refresh</span>
                            <span class="hidden sm:inline"> {t('ai.newChat')}</span>
                        </button>
                    </div>
                </div>
            </header>

            {/* Stitch Animated Audio Waveform Visualizer Banner (Appears when recording or speaking) */}
            <Show when={recording() || speaking()}>
                <div class="bg-surface-container-lowest border-b border-outline-variant px-4 py-2.5 shadow-2xs shrink-0">
                    <div class="mx-auto max-w-6xl flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5">
                            <div
                                class={`w-8 h-8 rounded-full flex items-center justify-center animate-pulse ${
                                    recording() ? 'bg-red-600 text-white' : 'bg-primary text-on-primary'
                                }`}
                            >
                                <span class="material-symbols-outlined text-base">{recording() ? 'mic' : 'volume_up'}</span>
                            </div>
                            <div>
                                <div class="flex items-center gap-1.5">
                                    <span class="text-xs font-bold text-on-surface">
                                        {recording() ? 'Listening to Farmer…' : 'AI Speaking…'}
                                    </span>
                                    <span class="text-[10px] bg-[#fef3c7] text-[#92400e] px-1.5 py-0.5 rounded-full font-bold">
                                        {recording() ? '54 dB Stream' : 'Fluent Audio'}
                                    </span>
                                </div>
                                <span class="text-[11px] text-primary font-semibold block">"बोलिए, हम सुन रहे हैं..."</span>
                            </div>
                        </div>

                        {/* 10 Waveform Bars */}
                        <div class="flex items-center gap-1 h-7 px-3 bg-surface-container-low rounded-xl border border-outline-variant/60">
                            <div class="w-1.5 bg-primary rounded-full wave-bar" style="height: 10px"></div>
                            <div class="w-1.5 bg-primary-container rounded-full wave-bar" style="height: 20px"></div>
                            <div class="w-1.5 bg-emerald-600 rounded-full wave-bar" style="height: 28px"></div>
                            <div class="w-1.5 bg-primary rounded-full wave-bar" style="height: 14px"></div>
                            <div class="w-1.5 bg-emerald-500 rounded-full wave-bar" style="height: 30px"></div>
                            <div class="w-1.5 bg-primary-container rounded-full wave-bar" style="height: 22px"></div>
                            <div class="w-1.5 bg-primary rounded-full wave-bar" style="height: 16px"></div>
                            <div class="w-1.5 bg-emerald-600 rounded-full wave-bar" style="height: 26px"></div>
                            <div class="w-1.5 bg-primary rounded-full wave-bar" style="height: 12px"></div>
                            <div class="w-1.5 bg-emerald-400 rounded-full wave-bar" style="height: 8px"></div>
                        </div>
                    </div>
                </div>
            </Show>

            {/* 2-Column Responsive Workspace */}
            <div class="mx-auto flex w-full max-w-6xl flex-1 gap-4 overflow-hidden px-0 py-0 sm:px-4 sm:py-4">
                {/* LEFT ASIDE (Proven Architecture): What assistant knows + Suggestions + My Animals */}
                <aside class="hidden w-72 shrink-0 space-y-4 overflow-y-auto lg:block pr-1">
                    {/* Card 1: What CropSense AI Knows */}
                    <section class="rounded-2xl border border-outline-variant bg-surface-container-lowest p-4 shadow-sm space-y-2">
                        <div class="flex items-center gap-2 border-b border-outline-variant/60 pb-2">
                            <span class="material-symbols-outlined text-primary text-base">database</span>
                            <h2 class="text-xs font-bold uppercase tracking-wider text-outline">{t('chat.knows')}</h2>
                        </div>
                        <Show when={known()} fallback={<p class="mt-2 text-xs text-outline animate-pulse">{t('chat.loadingData')}</p>}>
                            <ul class="space-y-2 text-xs text-on-surface pt-1">
                                <li class="flex items-center gap-2">
                                    <span class="text-base">🏡</span>
                                    <span>{t('chat.nFarms', { n: String(known()!.farms) })}</span>
                                </li>
                                <li class="flex items-center gap-2">
                                    <span class="text-base">🌱</span>
                                    <span>{t('chat.nCrops', { n: String(known()!.crops) })}</span>
                                </li>
                                <li class="flex items-center gap-2">
                                    <span class="text-base">🐄</span>
                                    <span>{t('chat.nAnimals', { n: String(known()!.animals) })}</span>
                                </li>
                                <li class="flex items-center gap-2">
                                    <span class="text-base">📊</span>
                                    <span>{t('chat.boardFigures')}</span>
                                </li>
                            </ul>
                        </Show>
                        <p class="pt-2 border-t border-outline-variant/40 text-[11px] text-outline leading-tight">{t('chat.privacy')}</p>
                    </section>

                    {/* Card 2: Try Asking Suggestions */}
                    <section class="rounded-2xl border border-outline-variant bg-surface-container-lowest p-4 shadow-sm space-y-2">
                        <div class="flex items-center gap-2 border-b border-outline-variant/60 pb-2">
                            <span class="material-symbols-outlined text-primary text-base">lightbulb</span>
                            <h2 class="text-xs font-bold uppercase tracking-wider text-outline">{t('chat.try')}</h2>
                        </div>
                        <div class="space-y-1.5 pt-1">
                            <For each={SUGGESTIONS}>
                                {(k) => (
                                    <button
                                        type="button"
                                        disabled={busy()}
                                        onClick={() => send({ text: t(k) })}
                                        class="w-full rounded-xl px-2.5 py-2 text-left text-xs font-medium text-on-surface hover:bg-[#d1fae5]/40 hover:text-primary border border-transparent hover:border-primary/20 transition-all disabled:opacity-50 flex items-center justify-between cursor-pointer"
                                    >
                                        <span>{t(k)}</span>
                                        <span class="material-symbols-outlined text-xs text-outline">arrow_forward</span>
                                    </button>
                                )}
                            </For>
                        </div>
                    </section>

                    {/* Card 3: My Animals (Focus Filter) */}
                    <Show when={animals().length > 0}>
                        <section class="rounded-2xl border border-outline-variant bg-surface-container-lowest p-4 shadow-sm space-y-2">
                            <div class="flex items-center gap-2 border-b border-outline-variant/60 pb-2">
                                <span class="material-symbols-outlined text-primary text-base">pets</span>
                                <h2 class="text-xs font-bold uppercase tracking-wider text-outline">{t('ai.myAnimals')}</h2>
                            </div>
                            <div class="flex flex-wrap gap-1.5 pt-1">
                                <For each={animals()}>
                                    {(a) => (
                                        <button
                                            type="button"
                                            onClick={() => setFocusAnimalId(focusAnimalId() === a.id ? null : a.id)}
                                            class={`rounded-full border px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer ${
                                                focusAnimalId() === a.id
                                                    ? 'border-primary bg-primary text-on-primary shadow-xs'
                                                    : 'border-outline-variant bg-surface text-on-surface hover:border-primary'
                                            }`}
                                        >
                                            🐄 {a.label}
                                        </button>
                                    )}
                                </For>
                            </div>
                        </section>
                    </Show>
                </aside>

                {/* MAIN CONVERSATION COLUMN */}
                <main class="flex min-w-0 flex-1 flex-col overflow-hidden bg-surface-container-lowest sm:rounded-2xl sm:border sm:border-outline-variant sm:shadow-sm">
                    {/* Chat Messages Scroll Container */}
                    <div ref={scrollEl} class="flex-1 space-y-4 overflow-y-auto px-4 py-4 sm:px-6">
                        <Show
                            when={messages().length > 0}
                            fallback={
                                <div class="mx-auto max-w-xl py-8 text-center space-y-4">
                                    <div class="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto text-3xl shadow-inner">
                                        🌾
                                    </div>
                                    <div>
                                        <h2 class="text-headline-sm font-headline-sm font-bold text-on-surface">
                                            {t('chat.hello', { name: user()?.name || user()?.full_name || 'Kisan' })}
                                        </h2>
                                        <p class="mt-1 text-body-sm font-body-sm text-outline max-w-md mx-auto">{t('chat.intro')}</p>
                                    </div>
                                    <div class="mt-3 flex justify-center sm:hidden">
                                        <LanguageSwitcher />
                                    </div>
                                    <div class="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2 text-left">
                                        <For each={SUGGESTIONS}>
                                            {(k) => (
                                                <button
                                                    type="button"
                                                    onClick={() => send({ text: t(k) })}
                                                    class="rounded-xl border border-outline-variant p-3 text-left text-xs font-semibold text-on-surface hover:border-primary hover:bg-[#d1fae5]/30 transition-all shadow-2xs cursor-pointer flex items-center justify-between"
                                                >
                                                    <span>{t(k)}</span>
                                                    <span class="material-symbols-outlined text-xs text-primary">arrow_forward</span>
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
                                            /* User Turn Message */
                                            <div class="flex justify-end">
                                                <div class="max-w-[80%] rounded-2xl rounded-br-xs bg-primary px-4 py-3 text-body-sm text-on-primary shadow-sm space-y-1">
                                                    <p class="leading-relaxed">{msg.text}</p>
                                                    <Show when={msg.audioUrl}>
                                                        <div class="mt-1.5">
                                                            <ClipPlayer url={msg.audioUrl!} durationMs={msg.audioMs} />
                                                        </div>
                                                    </Show>
                                                    <Show when={msg.timestamp}>
                                                        <span class="text-[10px] text-white/70 block text-right">{msg.timestamp}</span>
                                                    </Show>
                                                </div>
                                            </div>
                                        }
                                    >
                                        /* Assistant Turn Message */
                                        <div class="flex gap-3 items-start">
                                            <div class="w-8 h-8 rounded-xl bg-primary-container text-on-primary-container flex items-center justify-center shrink-0 mt-0.5 shadow-2xs font-bold">
                                                <span class="material-symbols-outlined text-sm">smart_toy</span>
                                            </div>
                                            <div class="min-w-0 max-w-[88%] space-y-2">
                                                <Show when={msg.text}>
                                                    <div class="rounded-2xl rounded-tl-xs bg-surface-container-low border border-outline-variant/60 px-4 py-3 text-body-sm text-on-surface shadow-2xs leading-relaxed">
                                                        <p class="whitespace-pre-line">{msg.text}</p>
                                                        <div class="mt-2 flex items-center justify-between pt-1 border-t border-outline-variant/40">
                                                            <button
                                                                type="button"
                                                                onClick={() => speak(msg.text, msg.result?.language || lang())}
                                                                class="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:underline cursor-pointer"
                                                            >
                                                                <span class="material-symbols-outlined text-xs">volume_up</span> {t('ai.listen')}
                                                            </button>
                                                            <Show when={msg.timestamp}>
                                                                <span class="text-[10px] text-outline">{msg.timestamp}</span>
                                                            </Show>
                                                        </div>
                                                    </div>
                                                </Show>

                                                {/* 1-by-1 Interactive Quick-Reply Pill Options */}
                                                <Show when={msg.result?.options && msg.result.options.length > 0}>
                                                    <div class="pt-1">
                                                        <p class="text-[11px] font-semibold text-outline mb-1.5 flex items-center gap-1">
                                                            <span class="material-symbols-outlined text-xs text-primary">touch_app</span> Tap an option or speak:
                                                        </p>
                                                        <div class="flex flex-wrap gap-1.5">
                                                            <For each={msg.result!.options}>
                                                                {(opt, optIdx) => (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => send({ text: opt })}
                                                                        class={`px-3.5 py-1.5 rounded-full text-xs font-semibold shadow-2xs transition-all active:scale-[0.98] flex items-center gap-1.5 cursor-pointer ${
                                                                            optIdx() === 0
                                                                                ? 'border-2 border-primary bg-[#d1fae5]/50 text-primary font-bold'
                                                                                : 'border border-outline-variant bg-surface hover:bg-[#d1fae5] hover:border-primary text-on-surface hover:text-primary'
                                                                        }`}
                                                                    >
                                                                        <Show when={optIdx() === 0}>
                                                                            <span class="material-symbols-outlined text-xs text-primary">star</span>
                                                                        </Show>
                                                                        <Show when={optIdx() > 0}>
                                                                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                                                                        </Show>
                                                                        <span>{opt}</span>
                                                                    </button>
                                                                )}
                                                            </For>
                                                        </div>
                                                    </div>
                                                </Show>

                                                {/* Small Data Table */}
                                                <Show when={msg.result?.table}>
                                                    <DataTableCard table={msg.result!.table!} />
                                                </Show>

                                                {/* Animal Options Chips */}
                                                <Show when={msg.result?.animal_options?.length}>
                                                    <div class="flex flex-wrap gap-1.5 pt-1">
                                                        <For each={msg.result!.animal_options}>
                                                            {(id) => (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => {
                                                                        setFocusAnimalId(id);
                                                                        send({ text: animalLabel(id) });
                                                                    }}
                                                                    class="rounded-full border border-primary bg-surface-container-lowest px-3 py-1.5 text-xs font-semibold text-primary hover:bg-surface-container-high shadow-2xs cursor-pointer flex items-center gap-1"
                                                                >
                                                                    <span class="material-symbols-outlined text-xs">pets</span>
                                                                    <span>{animalLabel(id)}</span>
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Navigation Action Buttons */}
                                                <Show when={msg.result?.matches?.length}>
                                                    <div class="flex flex-wrap gap-1.5 pt-1">
                                                        <For each={msg.result!.matches}>
                                                            {(m) => (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => go(m.id)}
                                                                    class="rounded-xl border border-outline-variant bg-surface px-3 py-1.5 text-xs font-semibold text-on-surface hover:border-primary hover:bg-[#d1fae5]/30 shadow-2xs cursor-pointer flex items-center gap-1"
                                                                >
                                                                    <span>{menuItem(m.id)?.emoji}</span>
                                                                    <span>{menuLabel(m.id)}</span>
                                                                    <span class="material-symbols-outlined text-xs">arrow_forward</span>
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Proposal Preview & Interactive Approval Card */}
                                                <Show when={msg.result?.proposal && !msg.proposalDone}>
                                                    <div class="pt-2">
                                                        <ProposalCard
                                                            proposal={msg.result!.proposal!}
                                                            animals={animals()}
                                                            crops={crops()}
                                                            onSaved={() => {
                                                                markProposalDone(i());
                                                                LivestockService.all();
                                                                FarmService.all();
                                                                loadCrops();
                                                                clearAssistantContext();
                                                                refreshKnown(true);
                                                                persist([
                                                                    ...messages(),
                                                                    {
                                                                        role: 'assistant',
                                                                        text: `✓ ${t('ai.saved')}: ${proposalTitle(msg.result!.proposal!.entity)}`,
                                                                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                                                                    },
                                                                ]);
                                                                showToast('success', t('ai.saved'));
                                                                scrollDown();
                                                            }}
                                                            onCancel={() => markProposalDone(i())}
                                                        />
                                                    </div>
                                                </Show>
                                            </div>
                                        </div>
                                    </Show>
                                )}
                            </For>

                            <Show when={busy()}>
                                <div class="flex items-center gap-2 text-xs text-primary font-bold p-3 bg-primary/5 rounded-xl border border-primary/20 animate-pulse">
                                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-600 animate-ping"></span>
                                    <span>{t('ai.thinking')}</span>
                                </div>
                            </Show>
                        </Show>
                    </div>

                    {/* Composer Footer */}
                    <footer class="border-t border-outline-variant bg-surface-container-lowest p-3 space-y-2">
                        <Show when={focusAnimalId()}>
                            <div class="flex items-center justify-between rounded-xl bg-primary/10 border border-primary/20 px-3 py-1.5 text-xs font-semibold text-primary">
                                <span class="truncate">{t('ai.talkingAbout', { name: animalLabel(focusAnimalId()) })}</span>
                                <button type="button" onClick={() => setFocusAnimalId(null)} class="ml-2 shrink-0 font-bold hover:underline cursor-pointer">
                                    {t('ai.clearAnimal')}
                                </button>
                            </div>
                        </Show>

                        <Show when={talkMode()}>
                            <p class="text-center text-xs text-primary font-bold">
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
                                class={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-on-primary transition-all cursor-pointer disabled:opacity-50 ${
                                    recording() ? 'animate-pulse bg-red-600 shadow-md shadow-red-500/30' : 'bg-primary hover:bg-primary-container shadow-sm'
                                }`}
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
                                class="min-w-0 flex-1 rounded-xl border border-outline-variant bg-surface px-4 py-2.5 text-xs text-on-surface outline-none focus:border-primary focus:ring-1 focus:ring-primary placeholder:text-outline"
                            />

                            <button
                                type="submit"
                                disabled={busy() || !input().trim()}
                                class="shrink-0 flex items-center gap-1 rounded-xl bg-primary px-4 py-2.5 text-xs font-bold text-on-primary hover:bg-primary-container transition-all cursor-pointer shadow-sm disabled:opacity-50"
                            >
                                <span>{t('ai.send')}</span>
                                <span class="material-symbols-outlined text-sm">send</span>
                            </button>
                        </form>
                    </footer>
                </main>
            </div>

            {/* Archive Drawer Modal */}
            <Show when={archiveDrawerOpen()}>
                <div class="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs transition-opacity animate-in fade-in">
                    <div class="w-full max-w-md bg-surface-container-lowest h-full shadow-2xl flex flex-col border-l border-outline-variant">
                        <div class="p-4 border-b border-outline-variant flex items-center justify-between bg-surface-container-low">
                            <div class="flex items-center gap-2">
                                <span class="material-symbols-outlined text-primary text-xl">history</span>
                                <h3 class="text-title-md font-title-md font-bold text-on-surface">Archived Sessions</h3>
                                <span class="text-xs bg-surface-container-high text-outline px-2 py-0.5 rounded-full font-bold">
                                    {archives().length}
                                </span>
                            </div>
                            <button
                                type="button"
                                onClick={() => setArchiveDrawerOpen(false)}
                                class="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container transition-colors cursor-pointer"
                            >
                                <span class="material-symbols-outlined text-lg">close</span>
                            </button>
                        </div>

                        <div class="flex-1 overflow-y-auto p-4 space-y-3">
                            <Show
                                when={archives().length > 0}
                                fallback={
                                    <div class="py-12 text-center text-outline space-y-2">
                                        <span class="material-symbols-outlined text-4xl text-outline/50">inventory_2</span>
                                        <p class="text-body-sm font-body-sm">No archived sessions yet.</p>
                                        <p class="text-xs">Clicking "Restart Session" automatically moves your active conversation to this archive.</p>
                                    </div>
                                }
                            >
                                <For each={archives()}>
                                    {(item) => (
                                        <div
                                            onClick={() => restoreArchivedSession(item.id)}
                                            class="p-3.5 bg-surface border border-outline-variant hover:border-primary rounded-xl transition-all hover:shadow-sm cursor-pointer space-y-2 group"
                                        >
                                            <div class="flex items-start justify-between gap-2">
                                                <h4 class="font-bold text-sm text-on-surface group-hover:text-primary transition-colors line-clamp-1">
                                                    {item.title}
                                                </h4>
                                                <button
                                                    type="button"
                                                    onClick={(e) => deleteArchivedSession(item.id, e)}
                                                    class="text-outline hover:text-error transition-colors p-0.5"
                                                    title="Delete Archive"
                                                >
                                                    <span class="material-symbols-outlined text-base">delete</span>
                                                </button>
                                            </div>
                                            <p class="text-xs text-outline line-clamp-2 leading-relaxed">{item.preview}</p>
                                            <div class="flex items-center justify-between text-[11px] text-outline/80 pt-1 border-t border-outline-variant/40">
                                                <span>{new Date(item.createdAt).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                                                <span class="font-semibold text-primary flex items-center gap-1">
                                                    <span>{item.messageCount} turns</span>
                                                    <span class="material-symbols-outlined text-xs">restore</span>
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </For>
                            </Show>
                        </div>

                        <Show when={archives().length > 0}>
                            <div class="p-3 border-t border-outline-variant bg-surface-container-low flex items-center justify-between">
                                <button
                                    type="button"
                                    onClick={() => {
                                        AssistantArchiveService.clearAll();
                                        setArchives([]);
                                        showToast('info', 'All archives cleared.');
                                    }}
                                    class="text-xs text-error hover:underline cursor-pointer"
                                >
                                    Clear all archives
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setArchiveDrawerOpen(false)}
                                    class="px-3 py-1.5 bg-surface-container rounded-lg border border-outline-variant text-xs font-semibold text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer"
                                >
                                    Close
                                </button>
                            </div>
                        </Show>
                    </div>
                </div>
            </Show>
        </div>
    );
};

export default Assistant;
