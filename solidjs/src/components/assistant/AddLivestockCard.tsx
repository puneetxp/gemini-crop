/**
 * Add Livestock card (Dashboard + Livestock home)
 * The farmer types or speaks about the animal; the AI fills the livestock
 * form over the conversation, one step at a time: purpose first (it decides
 * the species and breeds that make sense), then species, breed, how many,
 * when and the price. Each step offers tap-to-answer choices. The form
 * preview stays visible and editable; nothing is saved until Approve.
 * "Fill form myself" opens the same preview empty.
 */

import { Component, For, Show, createSignal } from 'solid-js';
import { t, lang } from '../../stores/i18n.store';
import type { TKey } from '../../i18n/en';
import { AssistantService, type AssistProposal } from '../../services/assistant.service';
import { FarmService, LivestockService } from '../../shared/Service/Services';
import { showToast } from '../ui/Toast';
import ProposalCard from './ProposalCard';
import { useRecorder, type VoiceClip } from './useRecorder';
import ClipPlayer from './ClipPlayer';

type Msg = { role: 'user' | 'assistant'; text: string; audioUrl?: string; audioMs?: number };

// Browser voice for read-aloud: Indian variant of the language code (en-IN, hi-IN, gu-IN, ...)
const speechLang = (code: string) => `${code}-IN`;
const emptyProposal = (): AssistProposal => ({ entity: 'livestock', fields: {}, summary: '' });

const AddLivestockCard: Component<{ id?: string }> = (props) => {
    const [expanded, setExpanded] = createSignal(false);
    const [messages, setMessages] = createSignal<Msg[]>([]);
    const [input, setInput] = createSignal('');
    const [busy, setBusy] = createSignal(false);
    const [proposal, setProposal] = createSignal<AssistProposal | null>(null);
    const [draft, setDraft] = createSignal<Record<string, any>>({});
    const [missing, setMissing] = createSignal<string[]>([]);
    // Guided steps from the server: what is asked next, quick replies, progress
    const [step, setStep] = createSignal<string | null>(null);
    const [stepOptions, setStepOptions] = createSignal<string[]>([]);
    const [progress, setProgress] = createSignal<{ done: number; total: number } | null>(null);

    const expand = () => {
        if (!expanded()) {
            setExpanded(true);
            FarmService.all();
        }
    };

    const reset = () => {
        recorder.stop(true);
        setMessages([]);
        setProposal(null);
        setDraft({});
        setMissing([]);
        setStep(null);
        setStepOptions([]);
        setProgress(null);
        setInput('');
        setExpanded(false);
    };

    const openManual = () => {
        expand();
        if (!proposal()) setProposal(emptyProposal());
    };

    const speak = (text: string) => {
        if (!('speechSynthesis' in window) || !text) return;
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = speechLang(lang());
        window.speechSynthesis.speak(u);
    };

    const send = async (payload: { text?: string; clip?: VoiceClip }) => {
        const text = payload.text?.trim();
        if (!text && !payload.clip) return;
        expand();
        const history = messages().slice(-10).map(({ role, text }) => ({ role, text }));
        setMessages([...messages().slice(-10), { role: 'user', text: text || '🎤 …', audioUrl: payload.clip?.url, audioMs: payload.clip?.durationMs }]);
        setInput('');
        setBusy(true);
        try {
            const result = await AssistantService.assist({
                text,
                ...(payload.clip ? await AssistantService.audioFields(payload.clip) : {}),
                lang: lang(),
                menu: [],
                animals: [],
                history,
                task: 'add_livestock',
                draft: draft(),
            });
            if (payload.clip && result.transcript) {
                const list = [...messages()];
                list[list.length - 1] = { ...list[list.length - 1], text: result.transcript };
                setMessages(list);
            }
            if (result.reply) {
                setMessages([...messages(), { role: 'assistant', text: result.reply }]);
                // Asked by voice: answer by voice
                if (payload.clip) speak(result.reply);
            }
            if (result.proposal) {
                setProposal(result.proposal);
                setDraft({ ...draft(), ...result.proposal.fields });
            }
            setMissing(result.missing || []);
            setStep(result.step ?? null);
            setStepOptions(result.step_options || []);
            if (result.steps?.length) setProgress({ done: result.steps_done || 0, total: result.steps.length });
        } catch (err: any) {
            const unavailable = err?.status === 503 || /unavailable/i.test(err?.message || '');
            const reason = AssistantService.errorReason(err);
            const base = unavailable ? t('ai.unavailable') : t('ai.error');
            setMessages([...messages(), { role: 'assistant', text: reason && reason !== base ? `${base} (${reason})` : base }]);
            if (!proposal()) setProposal(emptyProposal()); // let them finish by hand
        } finally {
            setBusy(false);
        }
    };

    const recorder = useRecorder((clip) => send({ clip }));

    // Purpose is asked first, before any server reply, so its choices show from the start
    const currentStep = () => step() ?? (messages().length === 0 ? 'purpose' : null);
    const currentOptions = () =>
        stepOptions().length ? stepOptions() : currentStep() === 'purpose' ? ['dairy', 'meat', 'breeding', 'eggs', 'draught', 'mixed'] : [];
    const optionText = (opt: string) =>
        currentStep() === 'purpose' || currentStep() === 'species' ? t(`${currentStep()}.${opt}` as TKey) : opt;
    // A tap fills the field straight away and tells the AI, which moves to the next step
    const pickOption = (opt: string) => {
        const field = currentStep();
        if (!field || busy()) return;
        setDraft({ ...draft(), [field]: field === 'quantity' ? Number(opt) : opt });
        send({ text: optionText(opt) });
    };

    return (
        <section id={props.id} class="bg-white rounded-lg shadow-md p-4 sm:p-6 border border-green-100">
            <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                <div>
                    <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
                        <span>🐄</span> {t('addLs.title')}
                    </h2>
                    <p class="text-sm text-gray-600 mt-1">{t('addLs.subtitle')}</p>
                </div>
                <div class="flex gap-2 shrink-0">
                    <Show when={expanded()}>
                        <button type="button" onClick={reset} class="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md">
                            ↺ {t('addLs.reset')}
                        </button>
                    </Show>
                    <button
                        type="button"
                        onClick={openManual}
                        class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-md shadow-sm"
                    >
                        ➕ {t('addLs.title')}
                    </button>
                </div>
            </div>

            {/* Message input — always visible */}
            <form
                class="mt-4 flex items-center gap-2"
                onSubmit={(e) => {
                    e.preventDefault();
                    send({ text: input() });
                }}
            >
                <button
                    type="button"
                    onClick={recorder.toggle}
                    disabled={busy()}
                    class={`shrink-0 w-11 h-11 rounded-full text-lg flex items-center justify-center text-white disabled:opacity-50 ${recorder.recording() ? 'bg-red-600 animate-pulse' : 'bg-green-600 hover:bg-green-700'}`}
                    aria-label={recorder.recording() ? t('ai.stop') : t('ai.record')}
                    title={recorder.recording() ? t('ai.stop') : t('ai.record')}
                >
                    {recorder.recording() ? '■' : '🎤'}
                </button>
                <input
                    type="text"
                    value={input()}
                    onInput={(e) => setInput(e.currentTarget.value)}
                    onFocus={expand}
                    placeholder={recorder.recording() ? t('ai.listening') : t('addLs.placeholder')}
                    disabled={recorder.recording()}
                    class="flex-1 min-w-0 border border-gray-300 rounded-md px-3 py-2.5 outline-none focus:border-green-500"
                />
                <button
                    type="submit"
                    disabled={busy() || !input().trim()}
                    class="shrink-0 px-4 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium rounded-md"
                >
                    {t('ai.send')}
                </button>
            </form>

            <Show when={expanded()}>
                <div class="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Conversation */}
                    <div class="bg-gray-50 rounded-lg p-3 space-y-2 max-h-96 overflow-y-auto">
                        <Show when={progress()}>
                            {(p) => (
                                <div class="flex items-center gap-2 text-xs text-gray-500">
                                    <span>{t('addLs.step', { n: String(Math.min(p().done + 1, p().total)), total: String(p().total) })}</span>
                                    <div class="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                        <div class="h-full bg-green-600 transition-all" style={{ width: `${(p().done / p().total) * 100}%` }} />
                                    </div>
                                </div>
                            )}
                        </Show>
                        <div class="bg-white rounded-lg px-3 py-2 text-sm text-gray-800 shadow-sm">{t('addLs.greeting')}</div>
                        <For each={messages()}>
                            {(m) => (
                                <Show
                                    when={m.role === 'assistant'}
                                    fallback={
                                        <div class="flex justify-end">
                                            <div class="max-w-[85%] bg-green-600 text-white rounded-lg rounded-br-none px-3 py-2 text-sm">
                                                {m.text}
                                                <Show when={m.audioUrl}>
                                                    <ClipPlayer url={m.audioUrl!} durationMs={m.audioMs} />
                                                </Show>
                                            </div>
                                        </div>
                                    }
                                >
                                    <div class="max-w-[90%] bg-white rounded-lg rounded-bl-none px-3 py-2 text-sm text-gray-800 shadow-sm">
                                        <p>{m.text}</p>
                                        <button onClick={() => speak(m.text)} class="mt-1 text-xs text-green-700 hover:text-green-900 font-medium">
                                            🔊 {t('ai.listen')}
                                        </button>
                                    </div>
                                </Show>
                            )}
                        </For>
                        <Show when={busy()}>
                            <p class="text-sm text-gray-500 animate-pulse">{t('ai.thinking')}</p>
                        </Show>
                        {/* Tap-to-answer choices for the current step */}
                        <Show when={!busy() && currentOptions().length > 0}>
                            <div class="flex flex-wrap gap-2 pt-1">
                                <For each={currentOptions()}>
                                    {(opt) => (
                                        <button
                                            type="button"
                                            onClick={() => pickOption(opt)}
                                            class="px-3 py-1.5 rounded-full border border-green-600 text-green-800 bg-white hover:bg-green-50 text-sm"
                                        >
                                            {optionText(opt)}
                                        </button>
                                    )}
                                </For>
                            </div>
                        </Show>
                        <Show when={proposal() && messages().length > 0 && !busy()}>
                            <p class={`text-xs font-medium ${missing().length ? 'text-amber-700' : 'text-green-700'}`}>
                                {missing().length
                                    ? t('addLs.missing', { fields: missing().map((f) => t(`field.${f}` as TKey)).join(', ') })
                                    : `✓ ${t('addLs.ready')}`}
                            </p>
                        </Show>
                    </div>

                    {/* Live form preview */}
                    <Show
                        when={proposal()}
                        fallback={
                            <div class="hidden lg:flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg text-sm text-gray-400 p-6 text-center">
                                {t('ai.preview')}
                            </div>
                        }
                    >
                        <ProposalCard
                            proposal={proposal()!}
                            animals={[]}
                            onChange={(values) => setDraft(values)}
                            onSaved={() => {
                                showToast('success', t('ai.saved'));
                                LivestockService.all();
                                reset();
                            }}
                            onCancel={reset}
                        />
                    </Show>
                </div>
            </Show>
        </section>
    );
};

export default AddLivestockCard;
