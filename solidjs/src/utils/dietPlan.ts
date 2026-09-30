/**
 * Daily diet plan for dairy animals, from the NDDB / ICAR feeding thumb rules
 * used in Indian dairy extension:
 *  - Cow: 1.5 kg concentrate for maintenance + 1 kg per 2.5 L milk
 *  - Buffalo: 2 kg concentrate for maintenance + 1 kg per 2 L milk
 *  - Last 3 months of pregnancy: +1.5 kg concentrate (cow/buffalo)
 *  - Goat: 250 g concentrate + 400 g per litre milk
 *  - Dry matter intake ~2.5% (cow/buffalo) / ~3.5% (goat) of body weight,
 *    split roughly 2/3 green : 1/3 dry fodder on a dry-matter basis
 * Values are a starting point, not a prescription — the page tells farmers
 * to confirm with a vet.
 */

export type DietSpecies = 'cow' | 'buffalo' | 'goat';

export interface DietInput {
    species: DietSpecies;
    weightKg: number;
    milkLitresPerDay: number;
    pregnantLastTrimester: boolean;
}

export type DietTipKey = 'diet.tip.mix' | 'diet.tip.split' | 'diet.tip.water' | 'diet.tip.pregnancy' | 'diet.tip.highYield';

export interface DietPlan {
    greenFodderKg: number;
    dryFodderKg: number;
    concentrateKg: number;
    mineralMixtureG: number;
    saltG: number;
    waterLitres: number;
    /** i18n keys (diet.tip.*) — the page translates them */
    tips: DietTipKey[];
}

const round1 = (n: number) => Math.round(n * 10) / 10;

// Dry-matter fractions of typical fodder: green ~20%, dry (straw/bhusa) ~90%
const GREEN_DM = 0.2;
const DRY_DM = 0.9;

export function calculateDietPlan(input: DietInput): DietPlan {
    const weight = Math.max(0, input.weightKg || 0);
    const milk = Math.max(0, input.milkLitresPerDay || 0);
    const isGoat = input.species === 'goat';

    let concentrate: number;
    if (input.species === 'cow') concentrate = 1.5 + milk / 2.5;
    else if (input.species === 'buffalo') concentrate = 2 + milk / 2;
    else concentrate = 0.25 + milk * 0.4;

    if (input.pregnantLastTrimester) concentrate += isGoat ? 0.2 : 1.5;

    const dmIntake = weight * (isGoat ? 0.035 : 0.025);
    // Concentrate is ~90% DM; roughage covers the rest of the dry matter
    const roughageDm = Math.max(0, dmIntake - concentrate * 0.9);
    const greenFodder = (roughageDm * 2) / 3 / GREEN_DM;
    const dryFodder = roughageDm / 3 / DRY_DM;

    const mineral = isGoat ? 10 + milk * 5 : 50 + milk * 2;
    const salt = isGoat ? 10 : 30;
    const water = isGoat ? 4 + milk * 1.5 : weight * 0.08 + milk * 4;

    const tips: DietTipKey[] = ['diet.tip.mix', 'diet.tip.split', 'diet.tip.water'];
    if (input.pregnantLastTrimester) tips.push('diet.tip.pregnancy');
    if (!isGoat && milk >= 15) tips.push('diet.tip.highYield');

    return {
        greenFodderKg: round1(greenFodder),
        dryFodderKg: round1(dryFodder),
        concentrateKg: round1(concentrate),
        mineralMixtureG: Math.round(mineral),
        saltG: salt,
        waterLitres: Math.round(water),
        tips,
    };
}
