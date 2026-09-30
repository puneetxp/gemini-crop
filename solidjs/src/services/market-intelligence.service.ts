/**
 * Market Intelligence Service
 * Handles API calls for market intelligence and predictive analytics
 */

import apiClient from '../lib/api-client';
import { buildUrl } from '~/config/api-registry';

// ── Backend → UI shape adapters ──────────────────────────────────────────────
// The API wraps payloads as { success, data } and uses different field names than these
// interfaces (e.g. opportunity_score / score_components). Missing numbers become 0 so the
// pages' .toFixed() calls never hit undefined.
const num = (v: any): number => (typeof v === 'number' && isFinite(v) ? v : Number(v) || 0);
const unwrap = (body: any): any => (body && typeof body === 'object' && 'success' in body && 'data' in body ? body.data : body);

function toTrend(d: any): TrendAnalysis {
  const series = (d?.time_series || []).map((p: any) => ({
    date: p.date || p.month,
    avg_price: num(p.avg_price),
    min_price: num(p.min_price ?? p.avg_price),
    max_price: num(p.max_price ?? p.avg_price),
    transaction_count: num(p.transaction_count ?? p.transactions),
  }));
  const first = series[0]?.avg_price, last = series[series.length - 1]?.avg_price;
  const avg = num(d?.current_avg_price ?? d?.avg_price);
  const t = String(d?.trend_direction || d?.trend || '');
  return {
    item_type: d?.item_type, item_name: d?.item_name, state: d?.state ?? null, district: d?.district ?? null,
    period_days: num(d?.period_days),
    current_avg_price: avg,
    price_change_percent: num(d?.price_change_percent ?? (first ? ((last - first) / first) * 100 : 0)),
    trend_direction: /rising|increas|up/.test(t) ? 'rising' : /falling|decreas|down/.test(t) ? 'falling' : 'stable',
    volatility: num(d?.volatility ?? (avg ? (num(d?.max_price) - num(d?.min_price)) / avg : 0)),
    time_series: series,
  };
}

function toOpportunity(d: any): OpportunityScore {
  const c = d?.score_components || {};
  // each component is { score, max }; the page shows it out of 100
  const pct = (x: any) => (x && num(x.max) ? (num(x.score) / num(x.max)) * 100 : num(x?.score ?? x));
  return {
    item_type: d?.item_type, item_name: d?.item_name, state: d?.state, district: d?.district ?? null,
    overall_score: num(d?.overall_score ?? d?.opportunity_score),
    breakdown: d?.breakdown ? {
      price_trend_score: num(d.breakdown.price_trend_score), demand_score: num(d.breakdown.demand_score),
      supply_gap_score: num(d.breakdown.supply_gap_score), profitability_score: num(d.breakdown.profitability_score),
    } : {
      price_trend_score: pct(c.price_trend), demand_score: pct(c.demand_level),
      supply_gap_score: pct(c.supply_demand_gap), profitability_score: pct(c.profitability),
    },
    recommendation: d?.recommendation || '',
    confidence: num(d?.confidence ?? d?.confidence_score),
  };
}

function toGap(g: any): SupplyDemandGap {
  const supply = num(g.supply_quantity ?? g.supply), demand = num(g.demand_quantity ?? g.demand);
  return {
    item_name: g.item_name, item_type: g.item_type,
    gap_type: g.gap_type === 'surplus' ? 'surplus' : 'shortage',
    severity: g.severity || 'low',
    supply_quantity: supply, demand_quantity: demand,
    gap_quantity: num(g.gap_quantity ?? g.gap ?? demand - supply),
    opportunity_description: g.opportunity_description ||
      `${g.gap_type === 'surplus' ? 'Surplus' : 'Shortage'} of ${Math.abs(num(g.gap_percent)).toFixed(0)}% (${num(g.listing_count)} listings, ${num(g.interest_count)} buyers interested)`,
  };
}

function toPrediction(d: any): PricePrediction {
  return {
    ...d,
    predicted_price: num(d?.predicted_price),
    confidence_score: num(d?.confidence_score),
    price_range: d?.price_range || { min: num(d?.price_range_min), max: num(d?.price_range_max) },
    trend: d?.trend || 'stable',
    factors: d?.factors || [],
  };
}

function toMonth(m: any): MonthlySupply {
  return {
    ...m,
    month: m.month,
    expected_quantity: num(m.expected_quantity ?? m.total_quantity),
    expected_avg_price: num(m.expected_avg_price ?? m.avg_price),
    quality_distribution: m.quality_distribution || {},
    supplier_count: num(m.supplier_count ?? m.listing_count),
  };
}

function toSummary(d: any): MarketSummary {
  const crops: any = {}, livestock: any = {};
  Object.entries(d?.crops || {}).forEach(([k, v]: any) => crops[k] = { ...v, transactions: num(v.transactions), total_volume: num(v.total_volume), avg_price: num(v.avg_price) });
  Object.entries(d?.livestock || {}).forEach(([k, v]: any) => livestock[k] = { ...v, transactions: num(v.transactions), total_animals: num(v.total_animals ?? v.total_volume), avg_price: num(v.avg_price) });
  return { ...d, total_transactions: num(d?.total_transactions), total_value: num(d?.total_value), crops, livestock };
}

export interface PriceTrend {
  date: string;
  avg_price: number;
  min_price: number;
  max_price: number;
  transaction_count: number;
}

export interface TrendAnalysis {
  item_type: string;
  item_name: string;
  state: string | null;
  district: string | null;
  period_days: number;
  current_avg_price: number;
  price_change_percent: number;
  trend_direction: 'rising' | 'falling' | 'stable';
  volatility: number;
  time_series: PriceTrend[];
}

export interface QualityPremium {
  grade: string;
  avg_price: number;
  premium_percent: number;
  transaction_count: number;
}

export interface DemandForecast {
  item_type: string;
  item_name: string;
  forecast_days: number;
  predicted_demand: number;
  confidence_score: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface PricePrediction {
  item_type: string;
  item_name: string;
  state: string;
  district: string | null;
  forecast_days: number;
  predicted_price: number;
  confidence_score: number;
  price_range: {
    min: number;
    max: number;
  };
  trend: 'rising' | 'falling' | 'stable';
  factors: string[];
}

export interface SupplyDemandGap {
  item_name: string;
  item_type: string;
  gap_type: 'surplus' | 'shortage';
  severity: 'low' | 'medium' | 'high';
  supply_quantity: number;
  demand_quantity: number;
  gap_quantity: number;
  opportunity_description: string;
}

export interface OpportunityScore {
  item_type: string;
  item_name: string;
  state: string;
  district: string | null;
  overall_score: number;
  breakdown: {
    price_trend_score: number;
    demand_score: number;
    supply_gap_score: number;
    profitability_score: number;
  };
  recommendation: string;
  confidence: number;
}

export interface MonthlySupply {
  month: string;
  expected_quantity: number;
  expected_avg_price: number;
  quality_distribution: {
    [grade: string]: number;
  };
  supplier_count: number;
}

export interface MarketSummary {
  total_transactions: number;
  total_value: number;
  crops: {
    [cropName: string]: {
      transactions: number;
      total_volume: number;
      avg_price: number;
    };
  };
  livestock: {
    [livestockName: string]: {
      transactions: number;
      total_animals: number;
      avg_price: number;
    };
  };
}

class MarketIntelligenceService {
  /**
   * Get price trends for an item
   */
  async getPriceTrends(
    itemType: string,
    itemName: string,
    state?: string,
    district?: string,
    days: number = 90
  ): Promise<TrendAnalysis> {
    const params = new URLSearchParams({
      days: days.toString(),
    });
    if (state) params.append('state', state);
    if (district) params.append('district', district);

    const url = buildUrl('marketIntelligence', 'trends', { item_type: itemType, item_name: itemName });
    const response = await apiClient.get(
      `${url}?${params}`
    );
    return toTrend(unwrap(response.data));
  }

  /**
   * Get quality premiums by grade
   */
  async getQualityPremiums(
    itemType: string,
    itemName: string,
    state?: string,
    days: number = 90
  ): Promise<QualityPremium[]> {
    const params = new URLSearchParams({
      days: days.toString(),
    });
    if (state) params.append('state', state);

    const url = buildUrl('marketIntelligence', 'qualityPremiums', { item_type: itemType, item_name: itemName });
    const response = await apiClient.get(
      `${url}?${params}`
    );
    const d = unwrap(response.data);
    return Array.isArray(d) ? d : (d?.premiums || d?.quality_premiums || []);
  }

  /**
   * Get demand forecast
   */
  async getDemandForecast(
    itemType: string,
    itemName: string,
    state?: string,
    daysAhead: number = 30
  ): Promise<DemandForecast> {
    const params = new URLSearchParams({
      days_ahead: daysAhead.toString(),
    });
    if (state) params.append('state', state);

    const url = buildUrl('marketIntelligence', 'demandForecast', { item_type: itemType, item_name: itemName });
    const response = await apiClient.get(
      `${url}?${params}`
    );
    return unwrap(response.data);
  }

  /**
   * Get market summary statistics
   */
  async getMarketSummary(state?: string): Promise<MarketSummary> {
    const params = state ? `?state=${state}` : '';
    const url = buildUrl('marketIntelligence', 'summary');
    const response = await apiClient.get(`${url}${params}`);
    return toSummary(unwrap(response.data));
  }

  /**
   * Predict future prices using AI
   */
  async predictPrice(
    itemType: string,
    itemName: string,
    state: string,
    district?: string,
    variety?: string,
    forecastDays: number = 30
  ): Promise<PricePrediction> {
    const params = new URLSearchParams({
      item_type: itemType,
      item_name: itemName,
      state: state,
      forecast_days: forecastDays.toString(),
    });
    if (district) params.append('district', district);
    if (variety) params.append('variety', variety);

    const url = buildUrl('predictiveAnalytics', 'predictPrice');
    const response = await apiClient.post(`${url}?${params}`);
    return toPrediction(unwrap(response.data));
  }

  /**
   * Predict future demand
   */
  async predictDemand(
    itemType: string,
    itemName: string,
    state: string,
    district?: string,
    forecastDays: number = 30
  ): Promise<any> {
    const params = new URLSearchParams({
      item_type: itemType,
      item_name: itemName,
      state: state,
      forecast_days: forecastDays.toString(),
    });
    if (district) params.append('district', district);

    const url = buildUrl('predictiveAnalytics', 'predictDemand');
    const response = await apiClient.get(`${url}?${params}`);
    return unwrap(response.data);
  }

  /**
   * Get supply-demand gaps
   */
  async getSupplyDemandGaps(
    state: string,
    district?: string,
    itemType?: string
  ): Promise<SupplyDemandGap[]> {
    const params = new URLSearchParams({ state });
    if (district) params.append('district', district);
    if (itemType) params.append('item_type', itemType);

    const url = buildUrl('predictiveAnalytics', 'supplyDemandGaps');
    const response = await apiClient.get(`${url}?${params}`);
    return (unwrap(response.data)?.gaps || []).map(toGap);
  }

  /**
   * Get opportunity score for farmers
   */
  async getOpportunityScore(
    itemType: string,
    itemName: string,
    state: string,
    district?: string,
    variety?: string
  ): Promise<OpportunityScore> {
    const params = new URLSearchParams({
      item_type: itemType,
      item_name: itemName,
      state: state,
    });
    if (district) params.append('district', district);
    if (variety) params.append('variety', variety);

    const url = buildUrl('predictiveAnalytics', 'opportunityScore');
    const response = await apiClient.get(`${url}?${params}`);
    return toOpportunity(unwrap(response.data));
  }

  /**
   * Get buyer supply planning data
   */
  async getBuyerSupplyPlanning(
    itemType: string,
    itemName: string,
    state: string,
    district?: string,
    monthsAhead: number = 3
  ): Promise<{ monthly_supply: MonthlySupply[] }> {
    const params = new URLSearchParams({
      item_type: itemType,
      item_name: itemName,
      state: state,
      months_ahead: monthsAhead.toString(),
    });
    if (district) params.append('district', district);

    const url = buildUrl('predictiveAnalytics', 'buyerSupplyPlanning');
    const response = await apiClient.get(`${url}?${params}`);
    const d = unwrap(response.data);
    return { ...d, monthly_supply: (d?.monthly_supply || d?.supply_by_month || []).map(toMonth) };
  }

  /**
   * Get Minimum Support Price (MSP) rates for crops
   */
  async getMspRates(
    cropName?: string,
    year?: number,
    season?: string
  ): Promise<any[]> {
    const params = new URLSearchParams();
    if (cropName) params.append('crop_name', cropName);
    if (year) params.append('year', year.toString());
    if (season) params.append('season', season);

    const url = buildUrl('marketIntelligence', 'msp');
    const response = await apiClient.get(`${url}?${params}`);
    return response.data.data || [];
  }
}

export const marketIntelligenceService = new MarketIntelligenceService();
