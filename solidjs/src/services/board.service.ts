/**
 * Board Service
 * Livestock data and AI projections for the dashboard Analytics Board.
 * Farm and crop data already arrive with profile-status (DashboardService).
 */

import apiClient from "../lib/api-client";
import type { ActiveCrop } from "./dashboard.service";

export interface LivestockRow {
  id: number;
  farm_id: number;
  species: string;
  breed: string;
  quantity: number;
  purchase_price: number;
  purchase_date: string;
  purpose: string;
  status: string;
  expected_roi?: number | null;
  break_even_date?: string | null;
  state?: string | null;
  district?: string | null;
}

export interface LivestockPortfolio {
  total_livestock: number;
  total_investment: number;
  total_expected_returns: number;
  total_current_value: number;
  overall_roi_percentage: number;
  livestock_by_species: Record<string, { count: number; investment: number; expected_returns: number }>;
  livestock_by_purpose: Record<string, { count: number; investment: number; expected_returns: number }>;
  active_livestock: number;
  break_even_summary: { achieved: number; pending: number };
}

export interface DemandSignal {
  item_type: "crop" | "livestock";
  item_name: string;
  state: string;
  demand_level: "high" | "medium" | "low";
  growth_rate: number; // fraction, e.g. 0.25 = +25%
  confidence: number; // 0..1
  data_points: number;
}

export interface ProjectionPoint {
  label: string;
  value: number;
  projected?: boolean;
  low?: number;
  high?: number;
}

const n = (v: unknown) => Number(v) || 0;

export class BoardService {
  static async getLivestock(farmerId: number): Promise<LivestockRow[]> {
    try {
      const res = await apiClient.get<LivestockRow[]>(`/livestock/?farmer_id=${farmerId}&limit=1000`, { cache: true, cacheTTL: 60000 });
      return (res.data || []).map((l) => ({
        ...l,
        quantity: n(l.quantity) || 1,
        purchase_price: n(l.purchase_price),
        expected_roi: l.expected_roi == null ? null : n(l.expected_roi),
      }));
    } catch (e) {
      console.error("Failed to load livestock for board:", e);
      return [];
    }
  }

  static async getPortfolio(farmerId: number): Promise<LivestockPortfolio | null> {
    try {
      const res = await apiClient.get<LivestockPortfolio>(`/livestock/farmer/${farmerId}/portfolio`, { cache: true, cacheTTL: 60000 });
      const p = res.data;
      return {
        ...p,
        total_investment: n(p.total_investment),
        total_expected_returns: n(p.total_expected_returns),
        total_current_value: n(p.total_current_value),
        overall_roi_percentage: n(p.overall_roi_percentage),
      };
    } catch (e) {
      console.error("Failed to load livestock portfolio:", e);
      return null;
    }
  }

  /**
   * AI demand signals from the predictive-analytics service, one per distinct
   * crop / species (capped so the board stays fast). Items that fail are skipped.
   */
  static async getDemandSignals(items: { item_type: "crop" | "livestock"; item_name: string; state: string }[]): Promise<DemandSignal[]> {
    const unique = items
      .filter((i) => i.item_name && i.state)
      .filter((i, k, a) => a.findIndex((j) => j.item_type === i.item_type && j.item_name.toLowerCase() === i.item_name.toLowerCase()) === k)
      .slice(0, 8);
    const results = await Promise.allSettled(
      unique.map((i) =>
        apiClient.get<any>(
          `/predictive-analytics/predict-demand?item_type=${i.item_type}&item_name=${encodeURIComponent(i.item_name)}&state=${encodeURIComponent(i.state)}&forecast_days=90`,
          { cache: true, cacheTTL: 10 * 60000 },
        ),
      ),
    );
    return results.flatMap((r, k) => {
      if (r.status !== "fulfilled" || !r.value.data?.success) return [];
      const d = r.value.data.data;
      return [{
        item_type: unique[k].item_type,
        item_name: unique[k].item_name,
        state: unique[k].state,
        demand_level: d.demand_level,
        growth_rate: n(d.growth_rate),
        confidence: n(d.confidence) || 0.6,
        data_points: n(d.data_points),
      }];
    });
  }

  /**
   * Monthly income: 6 months back (realised) + 6 months ahead (projected).
   * Crop income lands in its harvest month; livestock expected returns are
   * treated as annual and spread evenly across months the animal is owned.
   * Projected months are scaled by the AI demand growth for that item and
   * carry a range that widens with lower confidence and distance.
   */
  static buildIncomeProjection(crops: ActiveCrop[], livestock: LivestockRow[], signals: DemandSignal[]): ProjectionPoint[] {
    const now = new Date();
    const months = Array.from({ length: 12 }, (_, k) => new Date(now.getFullYear(), now.getMonth() - 5 + k, 1));
    const key = (d: Date) => d.getFullYear() * 12 + d.getMonth();
    const nowKey = key(now);
    const signalFor = (type: string, name: string) =>
      signals.find((s) => s.item_type === type && s.item_name.toLowerCase() === (name || "").toLowerCase());
    // Growth is noisy with few buyer-interest data points, so it is clamped.
    const growth = (s?: DemandSignal) => Math.max(-0.3, Math.min(0.5, s?.growth_rate ?? 0));

    return months.map((m) => {
      const mk = key(m);
      const projected = mk > nowKey;
      const ahead = Math.max(0, mk - nowKey);
      let value = 0, spread = 0;

      for (const c of crops) {
        const h = c.expected_harvest_date ? new Date(c.expected_harvest_date) : null;
        if (!h || key(h) !== mk) continue;
        const base = n(c.projected_profit ?? c.expected_profit);
        const s = signalFor("crop", c.crop_type);
        const v = projected ? base * (1 + growth(s) * Math.min(ahead / 6, 1)) : base;
        value += v;
        spread += Math.abs(v) * (1 - (s?.confidence ?? 0.6));
      }

      for (const l of livestock) {
        if (!l.expected_roi) continue;
        if (l.purchase_date && key(new Date(l.purchase_date)) > mk) continue;
        const base = (n(l.expected_roi) * l.quantity) / 12;
        const s = signalFor("livestock", l.species);
        const v = projected ? base * (1 + growth(s) * Math.min(ahead / 6, 1)) : base;
        value += v;
        spread += Math.abs(v) * (1 - (s?.confidence ?? 0.6)) * 0.5;
      }

      const label = m.toLocaleString("en-IN", { month: "short" }) + (m.getMonth() === 0 ? ` ${String(m.getFullYear()).slice(2)}` : "");
      if (!projected) return { label, value };
      const widen = 1 + ahead * 0.15;
      return { label, value, projected, low: Math.max(0, value - spread * widen), high: value + spread * widen };
    });
  }
}
