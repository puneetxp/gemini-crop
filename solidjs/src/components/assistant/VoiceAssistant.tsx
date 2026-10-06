/**
 * Voice Assistant
 * Floating 🎤 button → chat panel. The farmer speaks (any language) or types.
 * Before anything is said, the panel shows their animals and a searchable
 * index of every menu option. The assistant then:
 *  - opens a page on its own only when it is sure (auto_open), else offers options
 *  - asks "which animal? does it have a name?" when unclear, with the
 *    farmer's animals as tap-to-answer chips
 *  - for health problems, shows vets to call and proposes a health record
 *  - proposes records as an editable preview; saved only on Approve
 * Replies can be read aloud (🔊) in the user's language.
 */

import { Component, For, Show, createMemo, createSignal, onCleanup } from 'solid-js';
import { useLocation, useNavigate } from '@solidjs/router';
import { isAuthenticated } from '../../stores/auth.store';
import { lang, t, tValue } from '../../stores/i18n.store';
import { en, type TKey } from '../../i18n/en';
import { SERVICE_GROUPS } from '../ui/ServicesMenu';
import LanguageSwitcher from '../ui/LanguageSwitcher';
import ProposalCard, { proposalTitle } from './ProposalCard';
import { useRecorder, type VoiceClip } from './useRecorder';
import ClipPlayer from './ClipPlayer';
import { AssistantService, type AssistResult, type Option } from '../../services/assistant.service';
import { AssistantArchiveService } from '../../services/assistant-archive.service';
import { FarmService, LivestockService } from '../../shared/Service/Services';
import { VeterinaryDoctorsService, type VeterinaryDoctor } from '../../services/veterinary-doctors.service';
import { showToast } from '../ui/Toast';
import { speakFluent, stopFluentSpeech, voiceReplies, setVoiceReplies } from '../../lib/fluent-tts';

type Message = { role: 'user' | 'assistant'; text: string; result?: AssistResult; proposalDone?: boolean; audioUrl?: string; audioMs?: number };

const AUTO_OPEN_DELAY_MS = 1500;

// Flat menu index: id -> path/emoji, labelled in the current language + English
const MENU = SERVICE_GROUPS.flatMap((g) => g.items);
const menuLabel = (id: string) => t(`svc.${id}` as TKey);
const menuItem = (id: string) => MENU.find((m) => m.id === id);

const VoiceAssistant: Component = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const [open, setOpen] = createSignal(false);
    const [messages, setMessages] = createSignal<Message[]>([]);
    const [input, setInput] = createSignal('');
    const [busy, setBusy] = createSignal(false);
    const [speaking, setSpeaking] = createSignal(false);
    const [focusAnimalId, setFocusAnimalId] = createSignal<number | null>(null);
    const [autoOpen, setAutoOpen] = createSignal<{ id: string; timer: number } | null>(null);
    const [vets, setVets] = createSignal<VeterinaryDoctor[]>([]);

    let scrollEl: HTMLDivElement | undefined;

    // Hidden on /assistant, which is the same chat full-screen
    const visible = () => isAuthenticated() && !location.pathname.startsWith('/auth') && location.pathname !== '/assistant';

    // The farmer's own animals (livestock records), labelled by name when they have one
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

    // Typed text filters the menu index before anything is sent
    const menuMatches = createMemo(() => {
        const q = input().trim().toLowerCase();
        if (!q) return MENU;
        return MENU.filter((m) =>
            [menuLabel(m.id), t(`svc.${m.id}.sub` as TKey), en[`svc.${m.id}` as TKey]].some((s) => s?.toLowerCase().includes(q)),
        );
    });

    const openPanel = () => {
        setOpen(true);
        LivestockService.all();
        FarmService.all();
        loadCrops();
    };

    const closePanel = () => {
        cancelAutoOpen();
        recorder.stop(true);
        stopFluentSpeech();
        setSpeaking(false);
        setOpen(false);
    };

    const scrollDown = () => queueMicrotask(() => scrollEl?.scrollTo({ top: scrollEl.scrollHeight, behavior: 'smooth' }));

    const speak = (text: string, language: string) => {
        if (!text) return;
        speakFluent(
            text,
            language || lang(),
            () => setSpeaking(false),
            () => setSpeaking(true),
        );
    };

    const go = (id: string) => {
        const item = menuItem(id);
        if (!item) return;
        closePanel();
        navigate(item.path);
    };

    const cancelAutoOpen = () => {
        const a = autoOpen();
        if (a) clearTimeout(a.timer);
        setAutoOpen(null);
    };
    onCleanup(cancelAutoOpen);

    const loadVets = async () => {
        if (vets().length) return;
        try {
            setVets((await VeterinaryDoctorsService.list({})).slice(0, 3));
        } catch {
            // directory unavailable — the "Vet Doctors" option still links to the page
        }
    };

    const send = async (payload: { text?: string; clip?: VoiceClip }) => {
        const text = payload.text?.trim();
        if (!text && !payload.clip) return;
        cancelAutoOpen();

        const history = messages()
            .filter((m) => m.text)
            .slice(-10)
            .map((m) => ({ role: m.role, text: m.text }));
        setMessages([...messages(), { role: 'user', text: text || '🎤 …', audioUrl: payload.clip?.url, audioMs: payload.clip?.durationMs }]);
        setInput('');
        setBusy(true);
        scrollDown();

        try {
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
            });

            // Show what was heard in place of the 🎤 placeholder
            if (payload.clip && result.transcript) {
                const list = [...messages()];
                list[list.length - 1] = { ...list[list.length - 1], text: result.transcript };
                setMessages(list);
            }
            setMessages([...messages(), { role: 'assistant', text: result.reply, result }]);
            // Always answer aloud (unless the farmer muted replies)
            if (voiceReplies() && result.reply) speak(result.reply, result.language || lang());

            if (result.proposal?.fields?.livestock_id) setFocusAnimalId(Number(result.proposal.fields.livestock_id));
            if (result.vet_help) loadVets();
            if (result.auto_open && result.matches[0]) {
                const id = result.matches[0].id;
                setAutoOpen({ id, timer: window.setTimeout(() => go(id), AUTO_OPEN_DELAY_MS) });
            }
        } catch (err: any) {
            const unavailable = err?.status === 503 || /unavailable/i.test(err?.message || '');
            const reason = AssistantService.errorReason(err);
            const base = unavailable ? t('ai.unavailable') : t('ai.error');
            setMessages([...messages(), { role: 'assistant', text: reason && reason !== base ? `${base}\n(${reason})` : base }]);
        } finally {
            setBusy(false);
            scrollDown();
        }
    };

    const recorder = useRecorder((clip) => send({ clip }));
    const recording = recorder.recording;

    const pickAnimal = (id: number) => {
        setFocusAnimalId(id);
        send({ text: animalLabel(id) });
    };

    const newChat = () => {
        cancelAutoOpen();
        if (messages().length > 0) {
            const archived = AssistantArchiveService.archiveSession(messages());
            if (archived) {
                showToast('success', `Conversation archived as "${archived.title}"`);
            }
        }
        setMessages([]);
        setFocusAnimalId(null);
        setVets([]);
    };

    const markProposalDone = (index: number) => {
        const list = [...messages()];
        list[index] = { ...list[index], proposalDone: true };
        setMessages(list);
    };

    return (
        <Show when={visible()}>
            {/* Floating button — sits above BottomNav on mobile and above the Services button on desktop */}
            <Show when={!open()}>
                <button
                    type="button"
                    onClick={openPanel}
                    class="fixed z-40 right-4 bottom-20 sm:right-6 sm:bottom-24 w-14 h-14 rounded-full bg-[#004532] hover:bg-[#065f46] text-white shadow-xl shadow-emerald-950/20 flex items-center justify-center cursor-pointer transition-all active:scale-95 group"
                    aria-label={t('ai.open')}
                    title={t('ai.open')}
                >
                    <span class="material-symbols-outlined text-2xl group-hover:scale-110 transition-transform">mic</span>
                    <span class="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-3.5 w-3.5 bg-emerald-500"></span>
                    </span>
                </button>
            </Show>

            <Show when={open()}>
                <div class="fixed inset-0 z-[70] flex items-end sm:items-end sm:justify-end sm:p-6 font-sans">
                    <div class="absolute inset-0 bg-black/40 backdrop-blur-xs sm:bg-transparent" onClick={closePanel} />
                    <section
                        role="dialog"
                        aria-label={t('ai.title')}
                        class="relative w-full sm:w-[460px] h-[88vh] sm:h-[680px] bg-[#faf9f5] rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-emerald-900/10"
                    >
                        {/* Stitch Header */}
                        <header class="bg-gradient-to-r from-[#004532] to-[#065f46] text-white px-4 py-3 flex items-center justify-between gap-2 shadow-sm">
                            <div class="flex items-center gap-2.5 min-w-0">
                                <div class="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center shrink-0">
                                    <span class="material-symbols-outlined text-lg text-emerald-200">auto_awesome</span>
                                </div>
                                <div class="min-w-0">
                                    <h2 class="font-bold text-sm tracking-tight text-white flex items-center gap-1.5 truncate">
                                        <span>CropSense AI</span>
                                        <span class="text-[9px] bg-emerald-400/25 text-emerald-200 px-1.5 py-0.2 rounded font-bold uppercase tracking-wider">Pashu Voice</span>
                                    </h2>
                                    <p class="text-[11px] text-emerald-100/80 truncate">1-by-1 Conversational Wizard</p>
                                </div>
                            </div>
                            <div class="flex items-center gap-1 shrink-0">
                                <LanguageSwitcher />
                                <button
                                    onClick={() => {
                                        setVoiceReplies(!voiceReplies());
                                        if (!voiceReplies()) setSpeaking(false);
                                    }}
                                    class="p-1.5 text-emerald-100 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                    aria-pressed={voiceReplies()}
                                    title={voiceReplies() ? t('chat.voiceOn') : t('chat.voiceOff')}
                                    aria-label={voiceReplies() ? t('chat.voiceOn') : t('chat.voiceOff')}
                                >
                                    <span class="material-symbols-outlined text-sm">{voiceReplies() ? 'volume_up' : 'volume_off'}</span>
                                </button>
                                <button
                                    onClick={() => {
                                        closePanel();
                                        navigate('/assistant');
                                    }}
                                    class="p-1.5 text-emerald-100 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                    title={t('svc.assistant')}
                                    aria-label={t('svc.assistant')}
                                >
                                    <span class="material-symbols-outlined text-sm">open_in_full</span>
                                </button>
                                <Show when={messages().length > 0}>
                                    <button onClick={newChat} class="p-1.5 text-emerald-100 hover:text-white hover:bg-white/10 rounded-lg transition-colors" title={t('ai.newChat')}>
                                        <span class="material-symbols-outlined text-sm">refresh</span>
                                    </button>
                                </Show>
                                <button onClick={closePanel} class="p-1.5 text-emerald-100 hover:text-white hover:bg-white/10 rounded-lg transition-colors" aria-label={t('drawer.close')}>
                                    <span class="material-symbols-outlined text-base">close</span>
                                </button>
                            </div>
                        </header>

                        {/* Animated Waveform Visualizer Banner (Stitch) */}
                        <Show when={recording() || speaking()}>
                            <div class="bg-white border-b border-emerald-900/10 px-4 py-2.5 flex items-center justify-between gap-3 shadow-xs">
                                <div class="flex items-center gap-2.5">
                                    <div class="w-8 h-8 rounded-full bg-[#004532] text-white flex items-center justify-center animate-pulse">
                                        <span class="material-symbols-outlined text-base">{recording() ? 'mic' : 'volume_up'}</span>
                                    </div>
                                    <div>
                                        <div class="flex items-center gap-1.5">
                                            <span class="text-xs font-bold text-slate-800">{recording() ? 'Listening…' : 'Speaking…'}</span>
                                            <span class="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded font-bold">Clear Audio</span>
                                        </div>
                                        <span class="text-[11px] text-[#004532] font-semibold block">"बोलिए, हम सुन रहे हैं..."</span>
                                    </div>
                                </div>
                                <div class="flex items-center gap-1 h-7 px-2.5 bg-emerald-50 rounded-xl border border-emerald-200">
                                    <div class="w-1 bg-[#004532] rounded-full animate-bounce h-2"></div>
                                    <div class="w-1 bg-emerald-600 rounded-full animate-bounce h-5" style="animation-delay: 0.15s"></div>
                                    <div class="w-1 bg-emerald-500 rounded-full animate-bounce h-6" style="animation-delay: 0.3s"></div>
                                    <div class="w-1 bg-[#004532] rounded-full animate-bounce h-4" style="animation-delay: 0.2s"></div>
                                    <div class="w-1 bg-emerald-400 rounded-full animate-bounce h-3" style="animation-delay: 0.4s"></div>
                                </div>
                            </div>
                        </Show>

                        {/* My animals — tap one to talk about it */}
                        <Show when={animals().length > 0}>
                            <div class="bg-white/70 border-b border-emerald-900/5 px-4 py-2">
                                <p class="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">{t('ai.myAnimals')}</p>
                                <div class="flex gap-1.5 overflow-x-auto pb-0.5 scrollbar-thin">
                                    <For each={animals()}>
                                        {(a) => (
                                            <button
                                                onClick={() => setFocusAnimalId(focusAnimalId() === a.id ? null : a.id)}
                                                class={`shrink-0 text-xs px-2.5 py-1 rounded-full border transition-all ${focusAnimalId() === a.id ? 'bg-[#004532] border-[#004532] text-white font-bold' : 'bg-white border-slate-200 text-slate-700 hover:border-emerald-500'}`}
                                            >
                                                🐄 {a.label}
                                            </button>
                                        )}
                                    </For>
                                </div>
                            </div>
                        </Show>

                        {/* Chat / menu index */}
                        <div ref={scrollEl} class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
                            <Show
                                when={messages().length > 0}
                                fallback={
                                    <div class="space-y-3 py-2">
                                        <div class="bg-white rounded-2xl p-4 text-slate-800 shadow-sm border border-emerald-900/10 leading-relaxed text-xs">
                                            {t('ai.greeting')}
                                        </div>
                                        <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">{t('ai.allMenu')}</p>
                                        <Show when={menuMatches().length > 0} fallback={<p class="text-xs text-slate-400">{t('ai.noMatch')}</p>}>
                                            <div class="grid grid-cols-2 gap-2">
                                                <For each={menuMatches()}>
                                                    {(m) => (
                                                        <button
                                                            onClick={() => go(m.id)}
                                                            class="flex items-center gap-2 bg-white border border-slate-200 hover:border-emerald-600 rounded-xl px-3 py-2 text-left text-xs font-semibold text-slate-800 transition-colors shadow-2xs"
                                                        >
                                                            <span class="text-lg">{m.emoji}</span>
                                                            <span class="truncate">{menuLabel(m.id)}</span>
                                                        </button>
                                                    )}
                                                </For>
                                            </div>
                                        </Show>
                                    </div>
                                }
                            >
                                <For each={messages()}>
                                    {(msg, i) => (
                                        <Show
                                            when={msg.role === 'assistant'}
                                            fallback={
                                                <div class="flex justify-end">
                                                    <div class="max-w-[85%] bg-[#004532] text-white rounded-2xl rounded-br-xs px-3.5 py-2.5 text-xs shadow-sm">
                                                        <p class="leading-relaxed">{msg.text}</p>
                                                        <Show when={msg.audioUrl}>
                                                            <ClipPlayer url={msg.audioUrl!} durationMs={msg.audioMs} />
                                                        </Show>
                                                    </div>
                                                </div>
                                            }
                                        >
                                            <div class="space-y-2">
                                                <Show when={msg.text}>
                                                    <div class="max-w-[92%] bg-white rounded-2xl rounded-tl-xs px-3.5 py-2.5 shadow-sm border border-emerald-900/10 text-slate-800 text-xs leading-relaxed">
                                                        <p class="whitespace-pre-line">{msg.text}</p>
                                                        <button
                                                            onClick={() => speak(msg.text, msg.result?.language || lang())}
                                                            class="mt-1.5 inline-flex items-center gap-1 text-[11px] text-[#004532] hover:text-emerald-700 font-bold"
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
                                                                        class="px-3 py-1.5 rounded-full border border-emerald-900/15 bg-white hover:bg-emerald-50 hover:border-[#004532] text-slate-800 hover:text-[#004532] text-xs font-semibold shadow-2xs transition-all active:scale-[0.98] flex items-center gap-1.5 cursor-pointer"
                                                                    >
                                                                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                                                                        <span>{opt}</span>
                                                                    </button>
                                                                )}
                                                            </For>
                                                        </div>
                                                    </div>
                                                </Show>

                                                {/* Which animal? */}
                                                <Show when={msg.result?.animal_options?.length}>
                                                    <div class="flex flex-wrap gap-1.5">
                                                        <For each={msg.result!.animal_options}>
                                                            {(id) => (
                                                                <button
                                                                    onClick={() => pickAnimal(id)}
                                                                    class="text-xs px-3 py-1.5 rounded-full bg-white border border-emerald-600 text-emerald-900 hover:bg-emerald-50 font-semibold shadow-2xs cursor-pointer"
                                                                >
                                                                    🐄 {animalLabel(id)}
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Auto-open countdown */}
                                                <Show when={autoOpen() && i() === messages().length - 1}>
                                                    <div class="flex items-center justify-between bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2 text-xs">
                                                        <span class="text-emerald-900 font-semibold">{t('ai.opening', { name: menuLabel(autoOpen()!.id) })}</span>
                                                        <button onClick={cancelAutoOpen} class="text-slate-600 hover:text-slate-900 font-bold">
                                                            {t('ai.cancel')}
                                                        </button>
                                                    </div>
                                                </Show>

                                                {/* Options when not sure */}
                                                <Show when={!msg.result?.auto_open && msg.result?.matches?.length}>
                                                    <div class="flex flex-wrap gap-1.5">
                                                        <For each={msg.result!.matches}>
                                                            {(m) => (
                                                                <button
                                                                    onClick={() => go(m.id)}
                                                                    class="text-xs px-2.5 py-1.5 rounded-xl bg-white border border-slate-200 hover:border-emerald-600 text-slate-800 font-semibold shadow-2xs"
                                                                >
                                                                    {menuItem(m.id)?.emoji} {menuLabel(m.id)} →
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Vets to call */}
                                                <Show when={msg.result?.vet_help && vets().length > 0}>
                                                    <div class="bg-white rounded-2xl border border-emerald-900/10 divide-y divide-slate-100 overflow-hidden shadow-xs">
                                                        <p class="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">{t('ai.nearbyVets')}</p>
                                                        <For each={vets()}>
                                                            {(doc) => (
                                                                <div class="px-3 py-2 flex items-center justify-between gap-2">
                                                                    <div class="min-w-0">
                                                                        <p class="text-xs font-bold text-slate-900 truncate">{t('vet.dr', { name: doc.name })}</p>
                                                                        <p class="text-[11px] text-slate-500 truncate">
                                                                            {doc.location_district || doc.location_state || doc.clinic_name || ''}
                                                                        </p>
                                                                    </div>
                                                                    <a
                                                                        href={doc.call_link || `tel:${doc.phone}`}
                                                                        class="shrink-0 px-3 py-1.5 bg-[#004532] hover:bg-[#065f46] text-white text-xs font-bold rounded-xl"
                                                                    >
                                                                        📞 {t('vet.call')}
                                                                    </a>
                                                                </div>
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
                                                            LivestockService.all();
                                                            FarmService.all();
                                                            loadCrops();
                                                            setMessages([...messages(), { role: 'assistant', text: `✓ ${t('ai.saved')}: ${proposalTitle(msg.result!.proposal!.entity)}` }]);
                                                            showToast('success', t('ai.saved'));
                                                            scrollDown();
                                                        }}
                                                        onCancel={() => markProposalDone(i())}
                                                    />
                                                </Show>
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

                        {/* Composer (Stitch design) */}
                        <footer class="bg-white border-t border-emerald-900/10 p-3 space-y-2">
                            <Show when={focusAnimalId()}>
                                <div class="flex items-center justify-between text-xs bg-emerald-50 text-emerald-900 rounded-xl px-2.5 py-1.5 font-medium">
                                    <span class="truncate">{t('ai.talkingAbout', { name: animalLabel(focusAnimalId()) })}</span>
                                    <button onClick={() => setFocusAnimalId(null)} class="font-bold hover:underline shrink-0 ml-2">
                                        {t('ai.clearAnimal')}
                                    </button>
                                </div>
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
                                    onClick={recorder.toggle}
                                    disabled={busy()}
                                    class={`shrink-0 w-11 h-11 rounded-2xl flex items-center justify-center text-white disabled:opacity-50 transition-all cursor-pointer ${recording() ? 'bg-red-600 animate-pulse shadow-md shadow-red-500/30' : 'bg-[#004532] hover:bg-[#065f46] shadow-sm'}`}
                                    aria-label={recording() ? t('ai.stop') : t('ai.record')}
                                    title={recording() ? t('ai.stop') : t('ai.record')}
                                >
                                    <span class="material-symbols-outlined text-xl">{recording() ? 'stop' : 'mic'}</span>
                                </button>
                                <input
                                    type="text"
                                    value={input()}
                                    onInput={(e) => setInput(e.currentTarget.value)}
                                    placeholder={recording() ? t('ai.listening') : t('ai.search')}
                                    disabled={recording()}
                                    class="flex-1 min-w-0 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs outline-none focus:border-[#004532] focus:ring-1 focus:ring-[#004532] bg-[#faf9f5]"
                                />
                                <button
                                    type="submit"
                                    disabled={busy() || !input().trim()}
                                    class="shrink-0 px-4 py-2.5 bg-[#004532] hover:bg-[#065f46] disabled:opacity-50 text-white font-bold text-xs rounded-xl transition-all cursor-pointer flex items-center gap-1 shadow-sm"
                                >
                                    <span>{t('ai.send')}</span>
                                    <span class="material-symbols-outlined text-sm">send</span>
                                </button>
                            </form>
                        </footer>
                    </section>
                </div>
            </Show>
        </Show>
    );
};

export default VoiceAssistant;
