/**
 * Services Menu
 * One catalog of every service in the app, grouped the way farmers think
 * about them (livestock, farming, market, account). Used by the profile
 * drawer, the Profile page, the Dashboard and the /menu page so the list
 * stays in one place. Labels come from the i18n dictionaries (svc.<id>).
 */

import { Component, For, Show, createMemo, createSignal } from 'solid-js';
import { useNavigate, useLocation } from '@solidjs/router';
import { t } from '../../stores/i18n.store';
import { en, type TKey } from '../../i18n/en';

export interface ServiceItem {
    id: string;
    emoji: string;
    path: string;
}

export interface ServiceGroup {
    id: 'livestock' | 'farming' | 'market' | 'account';
    items: ServiceItem[];
}

export const SERVICE_GROUPS: ServiceGroup[] = [
    {
        id: 'livestock',
        items: [
            { id: 'livestockHome', emoji: '🐄', path: '/livestock' },
            { id: 'assistant', emoji: '✦', path: '/assistant' },
            { id: 'services', emoji: '🧰', path: '/services' },
            { id: 'vets', emoji: '🩺', path: '/livestock/doctors' },
            { id: 'buy', emoji: '🐃', path: '/livestock-marketplace' },
            { id: 'sell', emoji: '🤝', path: '/marketplace/my-listings' },
            { id: 'health', emoji: '💉', path: '/livestock/hub' },
            { id: 'diet', emoji: '🥛', path: '/livestock/diet-plan' },
        ],
    },
    {
        id: 'farming',
        items: [
            { id: 'myFarm', emoji: '🏡', path: '/farm' },
            { id: 'addFarm', emoji: '🚜', path: '/farm/register' },
            { id: 'myCrops', emoji: '🌱', path: '/crops/my-crops' },
            { id: 'plantCrop', emoji: '🌾', path: '/crops/plant' },
            { id: 'strategy', emoji: '📋', path: '/strategy/request' },
            { id: 'soil', emoji: '🧪', path: '/soil/hub' },
            { id: 'diagnose', emoji: '🔬', path: '/diagnose' },
            { id: 'pests', emoji: '🐛', path: '/pest-disease/hub' },
            { id: 'weather', emoji: '🌦️', path: '/climate/hub' },
            { id: 'plots', emoji: '🗺️', path: '/plots/analyze' },
        ],
    },
    {
        id: 'market',
        items: [
            { id: 'marketplace', emoji: '🛒', path: '/marketplace' },
            { id: 'rates', emoji: '🧮', path: '/marketplace/intelligence' },
            { id: 'bookings', emoji: '📦', path: '/marketplace/bookings' },
            { id: 'buyers', emoji: '🧑‍💼', path: '/marketplace/buyer-dashboard' },
            { id: 'supply', emoji: '📈', path: '/marketplace/supply-planning' },
            { id: 'transport', emoji: '🚚', path: '/transport/tracking' },
        ],
    },
    {
        id: 'account',
        items: [
            { id: 'profile', emoji: '👤', path: '/users/profile' },
            { id: 'notifications', emoji: '🔔', path: '/notifications' },
            { id: 'security', emoji: '🔒', path: '/users/security' },
            { id: 'dashboard', emoji: '📊', path: '/dashboard' },
            { id: 'aiUsage', emoji: '🤖', path: '/quota/history' },
            { id: 'config', emoji: '⚙️', path: '/settings' },
        ],
    },
];

const label = (id: string) => t(`svc.${id}` as TKey);
const sub = (id: string) => t(`svc.${id}.sub` as TKey);

interface ServicesMenuProps {
    /** 'grid' = icon tiles (pages), 'list' = compact rows (drawer) */
    variant?: 'grid' | 'list';
    /** Called after navigating, e.g. to close a drawer */
    onNavigate?: () => void;
    /** Show a search box above the groups */
    searchable?: boolean;
}

const ServicesMenu: Component<ServicesMenuProps> = (props) => {
    const navigate = useNavigate();
    const location = useLocation();
    const [query, setQuery] = createSignal('');

    const go = (path: string) => {
        navigate(path);
        props.onNavigate?.();
    };

    const isCurrent = (path: string) => location.pathname === path;

    // Match the current language and English, so "doctor" works in any language
    const groups = createMemo(() => {
        const q = query().trim().toLowerCase();
        if (!q) return SERVICE_GROUPS;
        const matches = (id: string) =>
            [label(id), sub(id), en[`svc.${id}` as TKey], en[`svc.${id}.sub` as TKey]].some((s) =>
                s?.toLowerCase().includes(q),
            );
        return SERVICE_GROUPS
            .map((g) => ({ ...g, items: g.items.filter((i) => matches(i.id)) }))
            .filter((g) => g.items.length > 0);
    });

    return (
        <div class="space-y-5">
            <Show when={props.searchable}>
                <div class="relative">
                    <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-lg">search</span>
                    <input
                        type="search"
                        value={query()}
                        onInput={(e) => setQuery(e.currentTarget.value)}
                        placeholder={t('menu.search')}
                        class="w-full pl-10 pr-10 py-3 rounded-lg bg-white border border-gray-200 outline-none focus:border-green-500 text-gray-800"
                    />
                    <Show when={query()}>
                        <button
                            onClick={() => setQuery('')}
                            class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                            aria-label={t('menu.clear')}
                        >
                            <span class="material-symbols-outlined text-lg">close</span>
                        </button>
                    </Show>
                </div>
            </Show>
            <Show when={groups().length === 0}>
                <p class="text-center text-gray-500 py-6">{t('menu.none')}</p>
            </Show>
            <For each={groups()}>
                {(group) => (
                    <section>
                        <h3 class="text-sm font-bold text-green-800 uppercase tracking-wide mb-2">{t(`grp.${group.id}` as TKey)}</h3>
                        <Show
                            when={props.variant === 'list'}
                            fallback={
                                <div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2">
                                    <For each={group.items}>
                                        {(item) => (
                                            <button
                                                onClick={() => go(item.path)}
                                                class={`bg-white rounded-lg p-3 text-center shadow-sm border transition-colors ${isCurrent(item.path) ? 'border-green-600 ring-2 ring-green-600/20' : 'border-gray-100 hover:border-green-300'}`}
                                            >
                                                <span class="block text-3xl">{item.emoji}</span>
                                                <span class="block font-bold text-sm text-gray-800 mt-1">{label(item.id)}</span>
                                                <span class="block text-[11px] text-gray-500">{sub(item.id)}</span>
                                            </button>
                                        )}
                                    </For>
                                </div>
                            }
                        >
                            <div class="bg-white rounded-lg divide-y divide-gray-100 overflow-hidden">
                                <For each={group.items}>
                                    {(item) => (
                                        <button
                                            onClick={() => go(item.path)}
                                            class={`w-full flex items-center gap-3 px-3 py-3 text-left transition-colors min-h-touch-android ${isCurrent(item.path) ? 'bg-green-50' : 'hover:bg-green-50'}`}
                                        >
                                            <span class="text-2xl w-8 text-center">{item.emoji}</span>
                                            <span class="flex-1 min-w-0">
                                                <span class="block font-semibold text-gray-800">{label(item.id)}</span>
                                                <span class="block text-xs text-gray-500">{sub(item.id)}</span>
                                            </span>
                                            <span class="material-symbols-outlined text-green-700 text-lg">chevron_right</span>
                                        </button>
                                    )}
                                </For>
                            </div>
                        </Show>
                    </section>
                )}
            </For>
        </div>
    );
};

export default ServicesMenu;
