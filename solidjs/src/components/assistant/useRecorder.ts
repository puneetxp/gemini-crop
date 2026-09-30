/**
 * Microphone recording for the assistant: tap to start, tap to stop,
 * the finished clip is handed to onDone. Shared by the floating assistant,
 * the full-page chat and the inline Add Livestock card.
 *
 * The clip keeps a local URL so the farmer can play back what was recorded,
 * and its length so the voice log shows whether the recording was cut short.
 */

import { createSignal, onCleanup } from 'solid-js';
import { showToast } from '../ui/Toast';
import { t } from '../../stores/i18n.store';

export type VoiceClip = { blob: Blob; url: string; durationMs: number };

// Anything shorter is almost always a tap-and-release before speaking
const MIN_CLIP_MS = 700;

// Speech-friendly capture: one channel, the browser's echo/noise cleanup and
// level control on (phones in a field or a shed pick up a lot of background)
const SPEECH_AUDIO: MediaTrackConstraints = {
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
};

export function useRecorder(onDone: (clip: VoiceClip) => void) {
    const [recording, setRecording] = createSignal(false);
    let recorder: MediaRecorder | null = null;
    let chunks: Blob[] = [];
    let startedAt = 0;
    let discarded = false;

    const start = async () => {
        if (recorder) return;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: SPEECH_AUDIO });
            // Opus in WebM/Ogg first; Safari only records MP4/AAC
            const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/ogg', 'audio/mp4'].find(
                (m) => MediaRecorder.isTypeSupported?.(m),
            ) || '';
            recorder = new MediaRecorder(stream, {
                ...(mime ? { mimeType: mime } : {}),
                audioBitsPerSecond: 32000,
            });
            chunks = [];
            discarded = false;
            recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
            recorder.onstop = () => {
                stream.getTracks().forEach((tr) => tr.stop());
                const durationMs = Date.now() - startedAt;
                const blob = new Blob(chunks, { type: (recorder?.mimeType || 'audio/webm').split(';')[0] });
                recorder = null;
                if (discarded || !chunks.length) return;
                if (durationMs < MIN_CLIP_MS || blob.size <= 500) {
                    showToast('warning', t('ai.tooShort'));
                    return;
                }
                onDone({ blob, url: URL.createObjectURL(blob), durationMs });
            };
            // Recording starts only now: the button turns red when the mic is really listening
            recorder.start();
            startedAt = Date.now();
            setRecording(true);
        } catch {
            recorder = null;
            showToast('warning', t('ai.micDenied'));
        }
    };

    /** Stop; with discard=true the clip is thrown away (e.g. panel closed) */
    const stop = (discard = false) => {
        if (!recorder) return;
        // The last chunk still arrives after stop(), so a flag (not clearing chunks) drops it
        discarded = discard;
        if (recorder.state !== 'inactive') recorder.stop();
        setRecording(false);
    };

    const toggle = () => (recording() ? stop() : start());

    onCleanup(() => stop(true));

    return { recording, start, stop, toggle };
}
