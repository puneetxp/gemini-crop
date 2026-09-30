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
import { FarmService, LivestockService } from '../../shared/Service/Services';
import { VeterinaryDoctorsService, type VeterinaryDoctor } from '../../services/veterinary-doctors.service';
import { showToast } from '../ui/Toast';

type Message = { role: 'user' | 'assistant'; text: string; result?: AssistResult; proposalDone?: boolean; audioUrl?: string; audioMs?: number };

// Browser voice for read-aloud: Indian variant of the language code (en-IN, hi-IN, gu-IN, ...)
const speechLang = (code: string) => `${code}-IN`;
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
        window.speechSynthesis?.cancel();
        setOpen(false);
    };

    const scrollDown = () => queueMicrotask(() => scrollEl?.scrollTo({ top: scrollEl.scrollHeight, behavior: 'smooth' }));

    const speak = (text: string, language: string) => {
        if (!('speechSynthesis' in window) || !text) return;
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = speechLang(language || lang());
        window.speechSynthesis.speak(u);
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
            // Asked by voice: answer by voice
            if (payload.clip && result.reply) speak(result.reply, result.language || lang());

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
                    class="fixed z-40 right-4 bottom-20 sm:right-6 sm:bottom-24 w-14 h-14 rounded-full bg-green-600 hover:bg-green-700 text-white text-2xl shadow-lg flex items-center justify-center"
                    aria-label={t('ai.open')}
                    title={t('ai.open')}
                >
                    🎤
                </button>
            </Show>

            <Show when={open()}>
                <div class="fixed inset-0 z-[70] flex items-end sm:items-end sm:justify-end sm:p-6">
                    <div class="absolute inset-0 bg-black/30 sm:bg-transparent" onClick={closePanel} />
                    <section
                        role="dialog"
                        aria-label={t('ai.title')}
                        class="relative w-full sm:w-[420px] h-[88vh] sm:h-[640px] bg-gray-50 rounded-t-2xl sm:rounded-lg shadow-2xl flex flex-col overflow-hidden"
                    >
                        {/* Header */}
                        <header class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between gap-2">
                            <div class="min-w-0">
                                <h2 class="font-bold text-gray-900">{t('ai.title')}</h2>
                                <p class="text-xs text-gray-500 truncate">{t('ai.hint')}</p>
                            </div>
                            <div class="flex items-center gap-1 shrink-0">
                                <LanguageSwitcher />
                                <button
                                    onClick={() => {
                                        closePanel();
                                        navigate('/assistant');
                                    }}
                                    class="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded"
                                    title={t('svc.assistant')}
                                    aria-label={t('svc.assistant')}
                                >
                                    ⤢
                                </button>
                                <Show when={messages().length > 0}>
                                    <button onClick={newChat} class="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded" title={t('ai.newChat')}>
                                        ↺
                                    </button>
                                </Show>
                                <button onClick={closePanel} class="px-2 py-1 text-xl text-gray-500 hover:bg-gray-100 rounded" aria-label={t('drawer.close')}>
                                    ✕
                                </button>
                            </div>
                        </header>

                        {/* My animals — tap one to talk about it */}
                        <Show when={animals().length > 0}>
                            <div class="bg-white border-b border-gray-100 px-4 py-2">
                                <p class="text-xs font-semibold text-gray-500 mb-1">{t('ai.myAnimals')}</p>
                                <div class="flex gap-2 overflow-x-auto pb-1">
                                    <For each={animals()}>
                                        {(a) => (
                                            <button
                                                onClick={() => setFocusAnimalId(focusAnimalId() === a.id ? null : a.id)}
                                                class={`shrink-0 text-sm px-3 py-1 rounded-full border ${focusAnimalId() === a.id ? 'bg-green-600 border-green-600 text-white' : 'bg-white border-gray-300 text-gray-700 hover:border-green-400'}`}
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
                                    <div class="space-y-3">
                                        <div class="bg-white rounded-lg p-3 text-gray-800 shadow-sm">{t('ai.greeting')}</div>
                                        <p class="text-xs font-semibold text-gray-500">{t('ai.allMenu')}</p>
                                        <Show when={menuMatches().length > 0} fallback={<p class="text-sm text-gray-500">{t('ai.noMatch')}</p>}>
                                            <div class="grid grid-cols-2 gap-2">
                                                <For each={menuMatches()}>
                                                    {(m) => (
                                                        <button
                                                            onClick={() => go(m.id)}
                                                            class="flex items-center gap-2 bg-white border border-gray-200 hover:border-green-400 rounded-lg px-3 py-2 text-left text-sm"
                                                        >
                                                            <span class="text-xl">{m.emoji}</span>
                                                            <span class="font-medium text-gray-800">{menuLabel(m.id)}</span>
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
                                                    <div class="max-w-[85%] bg-green-600 text-white rounded-lg rounded-br-none px-3 py-2">
                                                        {msg.text}
                                                        <Show when={msg.audioUrl}>
                                                            <ClipPlayer url={msg.audioUrl!} durationMs={msg.audioMs} />
                                                        </Show>
                                                    </div>
                                                </div>
                                            }
                                        >
                                            <div class="space-y-2">
                                                <Show when={msg.text}>
                                                    <div class="max-w-[90%] bg-white rounded-lg rounded-bl-none px-3 py-2 shadow-sm text-gray-800">
                                                        <p>{msg.text}</p>
                                                        <button
                                                            onClick={() => speak(msg.text, msg.result?.language || lang())}
                                                            class="mt-1 text-xs text-green-700 hover:text-green-900 font-medium"
                                                        >
                                                            🔊 {t('ai.listen')}
                                                        </button>
                                                    </div>
                                                </Show>

                                                {/* Which animal? */}
                                                <Show when={msg.result?.animal_options?.length}>
                                                    <div class="flex flex-wrap gap-2">
                                                        <For each={msg.result!.animal_options}>
                                                            {(id) => (
                                                                <button
                                                                    onClick={() => pickAnimal(id)}
                                                                    class="text-sm px-3 py-1.5 rounded-full bg-white border border-green-500 text-green-800 hover:bg-green-50"
                                                                >
                                                                    🐄 {animalLabel(id)}
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Auto-open countdown */}
                                                <Show when={autoOpen() && i() === messages().length - 1}>
                                                    <div class="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm">
                                                        <span class="text-green-800">{t('ai.opening', { name: menuLabel(autoOpen()!.id) })}</span>
                                                        <button onClick={cancelAutoOpen} class="text-gray-600 hover:text-gray-900 font-medium">
                                                            {t('ai.cancel')}
                                                        </button>
                                                    </div>
                                                </Show>

                                                {/* Options when not sure */}
                                                <Show when={!msg.result?.auto_open && msg.result?.matches?.length}>
                                                    <div class="flex flex-wrap gap-2">
                                                        <For each={msg.result!.matches}>
                                                            {(m) => (
                                                                <button
                                                                    onClick={() => go(m.id)}
                                                                    class="text-sm px-3 py-1.5 rounded-md bg-white border border-gray-300 hover:border-green-500 text-gray-800"
                                                                >
                                                                    {menuItem(m.id)?.emoji} {menuLabel(m.id)} →
                                                                </button>
                                                            )}
                                                        </For>
                                                    </div>
                                                </Show>

                                                {/* Vets to call */}
                                                <Show when={msg.result?.vet_help && vets().length > 0}>
                                                    <div class="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
                                                        <p class="px-3 py-2 text-xs font-semibold text-gray-500">{t('ai.nearbyVets')}</p>
                                                        <For each={vets()}>
                                                            {(doc) => (
                                                                <div class="px-3 py-2 flex items-center justify-between gap-2">
                                                                    <div class="min-w-0">
                                                                        <p class="text-sm font-semibold text-gray-900 truncate">{t('vet.dr', { name: doc.name })}</p>
                                                                        <p class="text-xs text-gray-500 truncate">
                                                                            {doc.location_district || doc.location_state || doc.clinic_name || ''}
                                                                        </p>
                                                                    </div>
                                                                    <a
                                                                        href={doc.call_link || `tel:${doc.phone}`}
                                                                        class="shrink-0 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-md"
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
                                    <div class="text-sm text-gray-500 animate-pulse">{t('ai.thinking')}</div>
                                </Show>
                            </Show>
                        </div>

                        {/* Composer */}
                        <footer class="bg-white border-t border-gray-200 p-3 space-y-2">
                            <Show when={focusAnimalId()}>
                                <div class="flex items-center justify-between text-xs bg-green-50 text-green-800 rounded px-2 py-1">
                                    <span class="truncate">{t('ai.talkingAbout', { name: animalLabel(focusAnimalId()) })}</span>
                                    <button onClick={() => setFocusAnimalId(null)} class="font-medium hover:underline shrink-0 ml-2">
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
                                    class={`shrink-0 w-12 h-12 rounded-full text-xl flex items-center justify-center text-white disabled:opacity-50 ${recording() ? 'bg-red-600 animate-pulse' : 'bg-green-600 hover:bg-green-700'}`}
                                    aria-label={recording() ? t('ai.stop') : t('ai.record')}
                                    title={recording() ? t('ai.stop') : t('ai.record')}
                                >
                                    {recording() ? '■' : '🎤'}
                                </button>
                                <input
                                    type="text"
                                    value={input()}
                                    onInput={(e) => setInput(e.currentTarget.value)}
                                    placeholder={recording() ? t('ai.listening') : t('ai.search')}
                                    disabled={recording()}
                                    class="flex-1 min-w-0 border border-gray-300 rounded-md px-3 py-3 outline-none focus:border-green-500"
                                />
                                <button
                                    type="submit"
                                    disabled={busy() || !input().trim()}
                                    class="shrink-0 px-4 py-3 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium rounded-md"
                                >
                                    {t('ai.send')}
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
