/**
 * Play back the farmer's own recording inside their chat bubble, so they can
 * hear what the assistant received (a clipped start or a noisy room is obvious).
 */

import { Component } from 'solid-js';
import { t } from '../../stores/i18n.store';

const ClipPlayer: Component<{ url: string; durationMs?: number }> = (props) => (
    <div class="mt-1 flex items-center gap-2">
        <audio controls preload="metadata" src={props.url} class="h-8 max-w-[220px]" aria-label={t('ai.playRecording')} />
        {props.durationMs ? <span class="text-xs opacity-80">{(props.durationMs / 1000).toFixed(1)}s</span> : null}
    </div>
);

export default ClipPlayer;
