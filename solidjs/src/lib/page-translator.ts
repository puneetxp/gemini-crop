/**
 * Whole-site translator
 * Pages are written in English with a few t() strings. When the viewer picks
 * another language, this walks the page (and everything that renders later),
 * sends the English text to /voice/translate in batches, and swaps it in.
 * Results are cached on the device per language, so a string is only ever
 * translated once. Switching back to English restores the original text.
 *
 * Text that is already in the chosen language (no Latin letters, e.g. from a
 * t() dictionary) is left alone. Anything inside [data-no-translate] — chat
 * messages, language names — is never touched.
 */

import { createEffect, createRoot } from 'solid-js';
import apiClient from './api-client';
import { lang } from '../stores/i18n.store';

const BATCH = 40;
const DEBOUNCE_MS = 150;
const CACHE_PREFIX = 'app_tr_';
const ATTRS = ['placeholder', 'title', 'aria-label', 'alt'] as const;
const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'CODE', 'PRE', 'TEXTAREA', 'SELECT', 'OPTION', 'SVG', 'IFRAME']);

type Slot = { node: Text; attr?: undefined } | { node: Element; attr: string };

// What each node/attribute originally said and what we replaced it with
const originals = new WeakMap<object, Record<string, { src: string; out: string }>>();
const tracked = new Set<WeakRef<Node>>();

let target = 'en';
let cache: Record<string, string> = {};
let queue = new Map<string, Slot[]>();
let timer = 0;
let observer: MutationObserver | null = null;
let version = 0;

const translatable = (s: string) => /[A-Za-z]{2,}/.test(s);
const blocked = (el: Element | null) => !!el && (SKIP_TAGS.has(el.tagName.toUpperCase()) || !!el.closest('[data-no-translate],[contenteditable="true"]'));

const loadCache = (code: string) => {
    try {
        cache = JSON.parse(localStorage.getItem(CACHE_PREFIX + code) || '{}');
    } catch {
        cache = {};
    }
};
const saveCache = () => {
    try {
        localStorage.setItem(CACHE_PREFIX + target, JSON.stringify(cache));
    } catch {
        // storage full or blocked — cache lasts for this session
    }
};

const keyOf = (attr: string) => attr || '#text';

function apply(slot: Slot, text: string) {
    const key = keyOf(slot.attr || '');
    const rec = originals.get(slot.node)?.[key];
    if (!rec) return;
    rec.out = text;
    if (slot.attr !== undefined) (slot.node as Element).setAttribute(slot.attr, text);
    else (slot.node as Text).data = text;
}

function restoreAll() {
    for (const ref of tracked) {
        const node = ref.deref();
        if (!node) {
            tracked.delete(ref);
            continue;
        }
        const recs = originals.get(node);
        if (!recs) continue;
        for (const [key, rec] of Object.entries(recs)) {
            // Skip nodes the app has since rewritten (e.g. t() text for the new language)
            if (key === '#text') {
                if ((node as Text).data === rec.out) (node as Text).data = rec.src;
            } else if ((node as Element).getAttribute(key) === rec.out) (node as Element).setAttribute(key, rec.src);
        }
        originals.delete(node);
    }
    tracked.clear();
}

function enqueue(slot: Slot, current: string) {
    const src = current.trim();
    if (!translatable(src)) return;
    const key = keyOf(slot.attr || '');
    const recs = originals.get(slot.node) || {};
    const prev = recs[key];
    // Already holds our translation of its original text
    if (prev && prev.out === current) return;
    recs[key] = { src: current, out: current };
    if (!originals.has(slot.node)) {
        originals.set(slot.node, recs);
        tracked.add(new WeakRef(slot.node));
    }
    const hit = cache[src];
    if (hit) {
        apply(slot, current.replace(src, hit));
        return;
    }
    const list = queue.get(src) || [];
    list.push(slot);
    queue.set(src, list);
    schedule();
}

function scan(root: Node) {
    if (target === 'en') return;
    if (root.nodeType === Node.TEXT_NODE) {
        const el = root.parentElement;
        if (!blocked(el)) enqueue({ node: root as Text }, (root as Text).data);
        return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE) return;
    const el = root as Element;
    if (blocked(el)) return;
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
        acceptNode: (n) => (n.nodeType === Node.ELEMENT_NODE && blocked(n as Element) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    const scanAttrs = (e: Element) => {
        for (const a of ATTRS) {
            const v = e.getAttribute(a);
            if (v) enqueue({ node: e, attr: a }, v);
        }
    };
    scanAttrs(el);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        if (n.nodeType === Node.TEXT_NODE) enqueue({ node: n as Text }, (n as Text).data);
        else scanAttrs(n as Element);
    }
}

function schedule() {
    clearTimeout(timer);
    timer = window.setTimeout(flush, DEBOUNCE_MS);
}

async function flush() {
    if (!queue.size) return;
    const pending = queue;
    queue = new Map();
    const code = target;
    const myVersion = version;
    const texts = [...pending.keys()];
    for (let i = 0; i < texts.length; i += BATCH) {
        const chunk = texts.slice(i, i + BATCH);
        try {
            const res = await apiClient.post<{ data?: { translations?: string[] } }>('/voice/translate', { texts: chunk, target: code });
            const out = (res as any)?.data?.data?.translations;
            if (!Array.isArray(out) || out.length !== chunk.length) continue;
            if (myVersion !== version) return; // language changed meanwhile
            chunk.forEach((src, j) => {
                if (out[j] && out[j] !== src) cache[src] = out[j];
                for (const slot of pending.get(src) || []) {
                    const cur = slot.attr ? (slot.node as Element).getAttribute(slot.attr) : (slot.node as Text).data;
                    // Only swap if the node still shows the text we asked about
                    if (cur != null && cur.trim() === src && out[j]) apply(slot, cur.replace(src, out[j]));
                }
            });
            saveCache();
        } catch {
            // translation unavailable — the English text stays
        }
    }
}

function start(code: string) {
    version++;
    target = code;
    queue = new Map();
    restoreAll();
    document.documentElement.lang = code;
    if (code === 'en') {
        observer?.disconnect();
        observer = null;
        return;
    }
    loadCache(code);
    scan(document.body);
    if (!observer) {
        observer = new MutationObserver((muts) => {
            for (const m of muts) {
                if (m.type === 'characterData') scan(m.target);
                else if (m.type === 'attributes') {
                    const v = (m.target as Element).getAttribute(m.attributeName!);
                    if (v && !blocked(m.target as Element)) enqueue({ node: m.target as Element, attr: m.attributeName! }, v);
                } else m.addedNodes.forEach(scan);
            }
        });
    }
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
        attributeFilter: [...ATTRS],
    });
}

/** Call once at startup: follows the language picker for the whole page */
export function initPageTranslator() {
    createRoot(() => {
        createEffect(() => start(lang()));
    });
}
