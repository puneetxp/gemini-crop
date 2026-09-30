/**
 * Assistant context
 * A compact plain-text summary of the farmer's own farms, crops, livestock,
 * tasks, listings and board figures, sent with each chat turn so the AI can
 * answer questions about their data ("how many goats?", "which crop earns most?").
 */

import { DashboardService } from "./dashboard.service";
import { BoardService } from "./board.service";

const CACHE_MS = 2 * 60 * 1000;
let cached: { at: number; userId: number; text: string } | null = null;

const money = (n: unknown) => `Rs ${Math.round(Number(n) || 0).toLocaleString("en-IN")}`;
const day = (s?: string | null) => (s ? String(s).slice(0, 10) : "-");

export async function buildAssistantContext(userId: number, force = false): Promise<string> {
  if (!force && cached && cached.userId === userId && Date.now() - cached.at < CACHE_MS) return cached.text;

  const [status, livestock] = await Promise.all([
    DashboardService.getProfileStatus().catch(() => null),
    BoardService.getLivestock(userId),
  ]);
  const farms: any[] = status?.farms || [];
  const d = status?.dashboard_data;
  const crops = d?.active_crops || [];
  const lines: string[] = [];

  lines.push(`FARMS (${farms.length}):`);
  for (const f of farms) {
    lines.push(
      `- #${f.id} ${f.name}: ${f.total_area ?? "?"} ${f.area_unit || ""}, ${[f.village, f.district, f.state].filter(Boolean).join(", ") || f.location || "location not set"}` +
        `${f.soil_type ? `, soil ${f.soil_type}` : ""}${f.ph_level ? `, pH ${f.ph_level}` : ""}${f.is_active === false ? ", inactive" : ""}`,
    );
  }

  lines.push(`\nACTIVE CROPS (${crops.length}):`);
  for (const c of crops) {
    lines.push(
      `- ${c.crop_type}${c.crop_variety ? ` (${c.crop_variety})` : ""}${c.plot_name ? ` on ${c.plot_name}` : ""}: ${c.growth_stage}, sown ${day(c.planting_date)}, harvest ${day(c.expected_harvest_date)} (${c.days_until_harvest} days), ` +
        `yield ${c.estimated_quantity ?? "?"} ${c.quantity_unit || ""}, expenses ${money(c.total_expenses)}, projected profit ${money(c.projected_profit ?? c.expected_profit)}`,
    );
  }

  const heads = livestock.reduce((s, l) => s + l.quantity, 0);
  lines.push(`\nLIVESTOCK (${livestock.length} records, ${heads} animals):`);
  for (const l of livestock) {
    const farm = farms.find((f) => f.id === l.farm_id)?.name || `farm #${l.farm_id}`;
    lines.push(
      `- #${l.id} ${l.quantity} x ${l.species} ${l.breed} (${l.purpose}) at ${farm}, bought ${day(l.purchase_date)} for ${money(l.purchase_price)} each` +
        `${l.expected_roi ? `, expected returns ${money(l.expected_roi)} each` : ""}${l.break_even_date ? `, break-even ${day(l.break_even_date)}` : ""}`,
    );
  }

  if (d?.upcoming_tasks?.length) {
    lines.push(`\nUPCOMING TASKS:`);
    for (const t of d.upcoming_tasks.slice(0, 10)) lines.push(`- ${day(t.due_date)} ${t.title} (${t.priority}, ${t.status})`);
  }
  if (d?.active_listings?.length) {
    lines.push(`\nMARKETPLACE LISTINGS: ${d.active_listings.length}`);
    for (const x of d.active_listings.slice(0, 10)) lines.push(`- ${x.crop_type || x.title || "listing"} ${x.quantity ?? ""} ${x.unit || x.quantity_unit || ""} @ ${money(x.price_per_unit ?? x.price)}`);
  }
  if (d?.buyer_interests?.length) lines.push(`\nBUYER INTERESTS: ${d.buyer_interests.length} (${d.buyer_interests.map((b) => b.crop_type).join(", ")})`);
  if (d?.weather_alerts?.length) lines.push(`\nWEATHER ALERTS: ${d.weather_alerts.map((w) => `${w.severity} ${w.title}`).join("; ")}`);

  const projection = BoardService.buildIncomeProjection(crops, livestock, []);
  const next6 = projection.filter((p) => p.projected).reduce((s, p) => s + p.value, 0);
  const last6 = projection.filter((p) => !p.projected).reduce((s, p) => s + p.value, 0);
  lines.push(
    `\nBOARD FIGURES: total profit potential ${money(d?.stats?.total_profit_potential)}, livestock invested ${money(livestock.reduce((s, l) => s + l.purchase_price * l.quantity, 0))}, ` +
      `income last 6 months ${money(last6)}, projected next 6 months ${money(next6)} (by month: ${projection.map((p) => `${p.label} ${money(p.value)}`).join(", ")})`,
  );

  const text = lines.join("\n").slice(0, 11500);
  cached = { at: Date.now(), userId, text };
  return text;
}

export const clearAssistantContext = () => {
  cached = null;
};
