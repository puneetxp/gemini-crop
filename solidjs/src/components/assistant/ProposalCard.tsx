/**
 * Proposal Card
 * Preview of a record the assistant wants to add. Every field is editable;
 * nothing is saved until the user taps Approve. Saving uses the same service
 * each normal form uses (islogin CRUD, farm registration, quick-plant, crop
 * expenses, marketplace listing), so the same ownership rules apply.
 */

import { Component, For, Show, createEffect, createResource, createSignal, on } from 'solid-js';
import type { AssistEntity, AssistProposal } from '../../services/assistant.service';
import { FarmService, LivestockService, Livestock_health_recordService } from '../../shared/Service/Services';
import { FarmService as FarmApi } from '../../services/farm.service';
import { CropService as CropApi } from '../../services/crop.service';
import { DashboardService } from '../../services/dashboard.service';
import { MarketplaceService } from '../../services/marketplace.service';
import { user } from '../../stores/auth.store';
import { t } from '../../stores/i18n.store';
import type { TKey } from '../../i18n/en';

type FieldDef = {
    name: string;
    type: 'text' | 'number' | 'date' | 'select';
    options?: string[];
    required?: boolean;
    /** Label key when field.<name> means something else (e.g. field.name = animal name) */
    label?: TKey;
    wide?: boolean;
};

// Which of the farmer's records the new one hangs off — chosen in the preview, never trusted from the AI
type Owner = 'farm' | 'animal' | 'crop' | null;

const OWNER: Record<AssistEntity, Owner> = {
    livestock: 'farm',
    livestock_health_record: 'animal',
    farm: null,
    crop: 'farm',
    crop_expense: 'crop',
    marketplace_listing: 'crop',
};
const OWNER_FIELD: Record<Exclude<Owner, null>, string> = { farm: 'farm_id', animal: 'livestock_id', crop: 'crop_id' };

const TITLE: Record<AssistEntity, TKey> = {
    livestock: 'ai.newAnimal',
    livestock_health_record: 'ai.newHealth',
    farm: 'ai.newFarm',
    crop: 'ai.newCrop',
    crop_expense: 'ai.newExpense',
    marketplace_listing: 'ai.newListing',
};

/** "New farm", "Plant a crop"… for messages after saving */
export const proposalTitle = (entity: AssistEntity) => t(TITLE[entity]);

const FIELDS: Record<AssistEntity, FieldDef[]> = {
    livestock: [
        { name: 'species', type: 'select', options: ['cattle', 'buffalo', 'goat', 'sheep', 'poultry'], required: true },
        { name: 'breed', type: 'text', required: true },
        { name: 'name', type: 'text' },
        { name: 'quantity', type: 'number', required: true },
        { name: 'purchase_price', type: 'number', required: true },
        { name: 'purchase_date', type: 'date', required: true },
        { name: 'purpose', type: 'select', options: ['dairy', 'meat', 'breeding', 'eggs', 'draught', 'mixed'], required: true },
        { name: 'village', type: 'text' },
        { name: 'district', type: 'text' },
        { name: 'state', type: 'text' },
    ],
    livestock_health_record: [
        { name: 'record_type', type: 'select', options: ['vaccination', 'checkup', 'treatment', 'breeding'], required: true },
        { name: 'record_date', type: 'date', required: true },
        { name: 'description', type: 'text', required: true, wide: true },
        { name: 'veterinarian_name', type: 'text' },
        { name: 'cost', type: 'number' },
        { name: 'next_due_date', type: 'date' },
        { name: 'notes', type: 'text', wide: true },
    ],
    farm: [
        { name: 'name', type: 'text', required: true, label: 'field.farm_name', wide: true },
        { name: 'state', type: 'text', required: true },
        { name: 'district', type: 'text', required: true },
        { name: 'village', type: 'text', required: true },
        { name: 'pincode', type: 'text', required: true },
        { name: 'total_area_acres', type: 'number', required: true },
        // Values accepted by both the registration form and the backend validator
        { name: 'primary_soil_type', type: 'select', options: ['Clay', 'Sandy', 'Loamy', 'Silt', 'Black', 'Red', 'Mixed'] },
        { name: 'irrigation_type', type: 'select', options: ['Rain-fed', 'Canal', 'Borewell', 'Drip', 'Sprinkler', 'Mixed'] },
    ],
    crop: [
        { name: 'crop_name', type: 'text', required: true },
        { name: 'variety', type: 'text' },
        { name: 'season', type: 'select', options: ['Kharif', 'Rabi', 'Zaid', 'Summer', 'Winter', 'Year-Round'], required: true },
        { name: 'area', type: 'number', required: true },
        { name: 'planting_date', type: 'date', required: true },
        { name: 'expected_harvest_date', type: 'date' },
        { name: 'expected_yield', type: 'number' },
        { name: 'market_price', type: 'number' },
    ],
    crop_expense: [
        { name: 'category', type: 'select', options: ['Seeds', 'Labor', 'Fertilizer', 'Pesticide', 'Equipment', 'Irrigation', 'Transport', 'Other'], required: true },
        { name: 'amount', type: 'number', required: true },
        { name: 'expense_date', type: 'date', required: true },
        { name: 'description', type: 'text', wide: true },
    ],
    marketplace_listing: [
        { name: 'estimated_yield', type: 'number' },
        { name: 'quality_grade', type: 'select', options: ['A', 'B', 'C'] },
    ],
};

const NUMERIC = new Set(['quantity', 'purchase_price', 'cost', 'total_area_acres', 'area', 'expected_yield', 'market_price', 'amount', 'estimated_yield']);
const today = () => new Date().toISOString().slice(0, 10);

/** Sensible starting values the farmer can still change */
const defaults = (entity: AssistEntity): Record<string, any> => {
    switch (entity) {
        case 'livestock':
            return { quantity: 1, purchase_date: today() };
        case 'livestock_health_record':
            return { record_date: today() };
        case 'crop': {
            const m = new Date().getMonth() + 1; // Jun-Oct Kharif, Nov-Feb Rabi, else Zaid
            return { planting_date: today(), season: m >= 6 && m <= 10 ? 'Kharif' : m >= 11 || m <= 2 ? 'Rabi' : 'Zaid' };
        }
        case 'crop_expense':
            return { expense_date: today() };
        default:
            return {};
    }
};

const clean = (o: Record<string, any>) => Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== ''));

interface ProposalCardProps {
    proposal: AssistProposal;
    animals: { id: number; label: string }[];
    /** The farmer's crops, for expenses and listings */
    crops?: { id: number; label: string }[];
    onSaved: () => void;
    onCancel: () => void;
    /** Called whenever the user edits a field, so the chat keeps the latest draft */
    onChange?: (values: Record<string, any>) => void;
}

const ProposalCard: Component<ProposalCardProps> = (props) => {
    const entity = props.proposal.entity;
    const owner = OWNER[entity];
    const ownerField = owner ? OWNER_FIELD[owner] : null;
    const farms = () => {
        try {
            return (typeof (FarmService as any)?.allstate === 'function' ? (FarmService as any).allstate() : []) as any[];
        } catch {
            return [] as any[];
        }
    };
    const ownerOptions = () =>
        owner === 'farm'
            ? farms().map((f) => ({ id: f.id as number, label: f.name || `#${f.id}` }))
            : owner === 'animal'
              ? props.animals
              : owner === 'crop'
                ? props.crops || []
                : [];

    const [values, setValues] = createSignal<Record<string, any>>({ ...defaults(entity), ...props.proposal.fields });

    // Crop: optional plot of the chosen farm ("" = whole farm, spread across its plots)
    const [plots] = createResource(
        () => (entity === 'crop' && values().farm_id ? Number(values().farm_id) : null),
        (farmId) => FarmApi.getFarmPlots(farmId).catch(() => []),
    );
    const [saving, setSaving] = createSignal(false);
    const [error, setError] = createSignal<string | null>(null);

    const set = (k: string, v: any) => {
        setValues({ ...values(), [k]: v, ...(k === 'farm_id' ? { plot_id: '' } : {}) });
        setError(null);
        props.onChange?.(values());
    };

    // The AI filled more fields in a later turn — merge them in, keeping the user's own edits to other fields
    createEffect(
        on(
            () => props.proposal.fields,
            (fields) => setValues({ ...values(), ...fields }),
            { defer: true },
        ),
    );

    // Farms may still be loading when the card opens. Livestock keeps its old default (first farm);
    // a crop defaults only when there is a single farm, so the farmer picks when the AI asked "which farm?"
    createEffect(() => {
        if (owner === 'farm' && values().farm_id == null && farms()[0] && (entity === 'livestock' || farms().length === 1))
            set('farm_id', farms()[0].id);
        if (owner === 'crop' && values().crop_id == null && props.crops?.length === 1) set('crop_id', props.crops[0].id);
    });

    const missing = () => {
        const v = values();
        const req = FIELDS[entity].filter((f) => f.required).map((f) => f.name);
        if (ownerField) req.push(ownerField);
        return req.filter((k) => v[k] === undefined || v[k] === null || v[k] === '');
    };

    const save = async (body: Record<string, any>) => {
        switch (entity) {
            // ModelService.create resolves to undefined on failure instead of throwing
            case 'livestock': {
                if (user()?.id) body.farmer_id = user()!.id;
                const saved = await LivestockService.create(body);
                if (!saved) throw new Error('save failed');
                return saved;
            }
            case 'livestock_health_record': {
                const saved = await Livestock_health_recordService.create(body);
                if (!saved) throw new Error('save failed');
                return saved;
            }
            case 'farm':
                return FarmApi.createFarm(clean({
                    name: body.name,
                    state: body.state,
                    district: body.district,
                    village: body.village,
                    pincode: String(body.pincode || '').trim(),
                    total_area_acres: body.total_area_acres,
                    primary_soil_type: body.primary_soil_type,
                    irrigation_type: body.irrigation_type,
                }) as any);
            case 'crop': {
                // plot_id null: quick-plant spreads across the farm's plots (or makes a main plot)
                const { plot_id, ...crop } = clean(body);
                return CropApi.quickPlant({ ...(crop as any), plot_id: plot_id ? Number(plot_id) : null, supporting_crops: [] });
            }
            case 'crop_expense':
                return DashboardService.addCropExpense(String(body.crop_id), clean({
                    category: body.category,
                    amount: body.amount,
                    description: body.description,
                    expense_date: body.expense_date,
                }) as any);
            case 'marketplace_listing':
                return MarketplaceService.createListing(
                    String(body.crop_id),
                    body.estimated_yield || body.quality_grade ? clean({ estimated_yield: body.estimated_yield, quality_grade: body.quality_grade }) : undefined,
                );
        }
    };

    const approve = async () => {
        if (missing().length) {
            setError(t('ai.required'));
            return;
        }
        setSaving(true);
        setError(null);
        const body: Record<string, any> = { ...values() };
        for (const k of Object.keys(body)) if (NUMERIC.has(k) && body[k] !== '' && body[k] != null) body[k] = Number(body[k]);
        for (const k of ['farm_id', 'livestock_id', 'crop_id']) if (body[k] !== undefined) body[k] = Number(body[k]);
        try {
            await save(body);
            props.onSaved();
        } catch (err: any) {
            // Show the server's reason when it gives one (e.g. "pincode must be 6 digits")
            const detail = err?.data?.detail ?? err?.response?.data?.detail ?? err?.detail;
            const msg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: any) => d?.msg).filter(Boolean).join('; ') : '';
            setError(msg ? `${t('ai.saveFailed')} (${msg})` : t('ai.saveFailed'));
        } finally {
            setSaving(false);
        }
    };

    const optionLabel = (field: string, opt: string) =>
        field === 'species' || field === 'purpose'
            ? t(`${field}.${opt}` as TKey)
            : opt.charAt(0).toUpperCase() + opt.slice(1);

    const ownerLabel = (): TKey => (owner === 'farm' ? 'ai.chooseFarm' : owner === 'animal' ? 'ai.chooseAnimal' : 'ai.chooseCrop');
    const ownerEmpty = (): TKey => (owner === 'farm' ? 'ai.noFarm' : owner === 'animal' ? 'ai.noAnimal' : 'ai.noCrop');

    return (
        <div class="bg-white border-2 border-green-200 rounded-lg p-3 space-y-3">
            <div>
                <p class="text-xs font-semibold text-green-700 uppercase tracking-wide">{t('ai.preview')}</p>
                <p class="font-bold text-gray-900">{t(TITLE[entity])}</p>
                <Show when={props.proposal.summary}>
                    <p class="text-sm text-gray-600">{props.proposal.summary}</p>
                </Show>
            </div>

            {/* Owner: which farm / animal / crop — chosen by the user, never by the AI */}
            <Show when={ownerField}>
                <Show when={ownerOptions().length > 0} fallback={<p class="text-sm text-red-600">{t(ownerEmpty())}</p>}>
                    <label class="block text-sm">
                        <span class="text-gray-700">{t(ownerLabel())} *</span>
                        <select
                            value={values()[ownerField!] ?? ''}
                            onChange={(e) => set(ownerField!, e.currentTarget.value)}
                            class={`mt-1 w-full border rounded-md px-2 py-2 focus:border-green-500 outline-none ${values()[ownerField!] ? 'border-gray-300' : 'border-amber-400 bg-amber-50'}`}
                        >
                            <Show when={entity !== 'livestock'}>
                                <option value="">—</option>
                            </Show>
                            <For each={ownerOptions()}>{(o) => <option value={o.id}>{o.label}</option>}</For>
                        </select>
                    </label>
                </Show>
            </Show>

            <Show when={entity === 'crop' && (plots() || []).length > 0}>
                <label class="block text-sm">
                    <span class="text-gray-700">{t('ai.choosePlot')}</span>
                    <select
                        value={values().plot_id ?? ''}
                        onChange={(e) => set('plot_id', e.currentTarget.value)}
                        class="mt-1 w-full border border-gray-300 rounded-md px-2 py-2 focus:border-green-500 outline-none"
                    >
                        <option value="">{t('ai.wholeFarm')}</option>
                        <For each={plots()}>{(pl) => <option value={pl.id}>{`${pl.plot_name} · ${pl.area} ac`}</option>}</For>
                    </select>
                </label>
            </Show>

            <div class="grid grid-cols-2 gap-2">
                <For each={FIELDS[entity]}>
                    {(f) => (
                        <label class={`block text-sm ${f.wide ? 'col-span-2' : ''}`}>
                            <span class="text-gray-700">
                                {t(f.label || (`field.${f.name}` as TKey))}
                                {f.required ? ' *' : ''}
                            </span>
                            <Show
                                when={f.type === 'select'}
                                fallback={
                                    <input
                                        type={f.type}
                                        inputmode={f.type === 'number' ? 'decimal' : undefined}
                                        value={values()[f.name] ?? ''}
                                        onInput={(e) => set(f.name, e.currentTarget.value)}
                                        class={`mt-1 w-full border rounded-md px-2 py-2 outline-none focus:border-green-500 ${f.required && !values()[f.name] ? 'border-amber-400 bg-amber-50' : 'border-gray-300'}`}
                                    />
                                }
                            >
                                <select
                                    value={values()[f.name] ?? ''}
                                    onChange={(e) => set(f.name, e.currentTarget.value)}
                                    class={`mt-1 w-full border rounded-md px-2 py-2 outline-none focus:border-green-500 ${f.required && !values()[f.name] ? 'border-amber-400 bg-amber-50' : 'border-gray-300'}`}
                                >
                                    <option value="">—</option>
                                    <For each={f.options}>{(o) => <option value={o}>{optionLabel(f.name, o)}</option>}</For>
                                </select>
                            </Show>
                        </label>
                    )}
                </For>
            </div>

            <Show when={error()}>
                <p class="text-sm text-red-600">{error()}</p>
            </Show>

            <div class="flex gap-2">
                <button
                    type="button"
                    onClick={approve}
                    disabled={saving()}
                    class="flex-1 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-medium rounded-md"
                >
                    {saving() ? '…' : `✓ ${t('ai.approve')}`}
                </button>
                <button
                    type="button"
                    onClick={props.onCancel}
                    class="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md"
                >
                    {t('ai.cancel')}
                </button>
            </div>
        </div>
    );
};

export default ProposalCard;
