/**
 * Dashboard Service
 * API integration for dashboard data aggregation
 */

import apiClient from "../lib/api-client";
import { buildUrl } from "~/config/api-registry";

// Types
export interface DashboardStats {
  total_profit_potential: number;
  active_listings: number;
  buyer_interests: number;
  active_crops: number;
  pending_tasks: number;
}

export interface ActiveCrop {
  id: string;
  crop_type: string;
  crop_variety: string;
  planting_date: string;
  expected_harvest_date: string;
  estimated_quantity: number;
  quantity_unit: string;
  growth_stage: "planted" | "growing" | "maturing" | "ready" | "overdue";
  days_until_harvest: number;
  plot_name?: string;
  expected_profit?: number;
  total_expenses?: number;
  projected_profit?: number;
  status?: string;
}

export interface UpcomingTask {
  id: string;
  title: string;
  description: string;
  due_date: string;
  priority: string;
  category: string;
  status: string;
}

export interface BuyerInterest {
  id: string;
  listing_id: string;
  crop_type: string;
  buyer_name?: string;
  buyer_company?: string;
  quantity_interested: number;
  preferred_price?: number;
  status: string;
  created_at: string;
}

export interface WeatherAlert {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  affected_area: string;
  valid_from: string;
  valid_until: string;
  recommendations: string[];
}

export interface DashboardData {
  stats: DashboardStats;
  active_crops: ActiveCrop[];
  active_listings: any[];
  upcoming_tasks: UpcomingTask[];
  buyer_interests: BuyerInterest[];
  weather_alerts: WeatherAlert[];
  strategy_timeline?: SeasonProgress[];
}

export interface SeasonProgress {
  season: "Kharif" | "Rabi" | "Zaid";
  crop: string;
  startMonth: number;
  endMonth: number;
  tasks: {
    month: string;
    actions: string[];
    completed: boolean;
  }[];
  status: "upcoming" | "active" | "completed";
}

export class DashboardService {
  /**
   * Check if user has any data (lightweight check before loading dashboard)
   */
  static async getProfileStatus(): Promise<{
    has_farms: boolean;
    has_crops: boolean;
    has_strategies: boolean;
    has_listings: boolean;
    is_onboarding_complete: boolean;
    farms: any[];
    plots: any[];
    dashboard_data: DashboardData;
  }> {
    try {
      const url = buildUrl("analytics", "profileStatus");
      const response = await apiClient.get(url, {
        cache: false, // Don't cache this check
      });
      return response.data;
    } catch (error) {
      console.error("Failed to fetch profile status:", error);
      // If error, assume no data to show onboarding
      return {
        has_farms: false,
        has_crops: false,
        has_strategies: false,
        has_listings: false,
        is_onboarding_complete: false,
        farms: [],
        plots: [],
        dashboard_data: {
          stats: {
            total_profit_potential: 0,
            active_listings: 0,
            buyer_interests: 0,
            active_crops: 0,
            pending_tasks: 0,
          },
          active_crops: [],
          active_listings: [],
          upcoming_tasks: [],
          buyer_interests: [],
          weather_alerts: [],
          strategy_timeline: [],
        },
      };
    }
  }

  /**
   * Get comprehensive dashboard data
   */
  static async getDashboardData(): Promise<DashboardData> {
    try {
      const url = buildUrl("analytics", "dashboard");
      const response = await apiClient.get<DashboardData>(
        url,
        {
          cache: true,
          cacheTTL: 60000, // 1 minute cache
        },
      );
      return response.data;
    } catch (error) {
      // If dashboard endpoint doesn't exist, aggregate data from multiple endpoints
      return this.aggregateDashboardData();
    }
  }

  /**
   * Aggregate dashboard data from multiple endpoints
   */
  private static async aggregateDashboardData(): Promise<DashboardData> {
    // Fetch data from multiple endpoints in parallel
    // These endpoints don't exist in registry, use direct URLs
    const [cropsRes, listingsRes, strategiesRes] = await Promise.allSettled([
      apiClient.get("/api/v1/crops/my-crops", { cache: true, cacheTTL: 60000 }),
      apiClient.get("/marketplace/my-listings", {
        cache: true,
        cacheTTL: 60000,
      }),
      apiClient.get(buildUrl("crops", "listStrategies"), {
        cache: true,
        cacheTTL: 120000,
      }),
    ]);

    // Parse successful responses
    const crops = cropsRes.status === "fulfilled" ? cropsRes.value.data : [];
    const listings = listingsRes.status === "fulfilled"
      ? listingsRes.value.data
      : [];
    const strategies = strategiesRes.status === "fulfilled"
      ? strategiesRes.value.data
      : [];

    // Calculate stats
    const stats: DashboardStats = {
      total_profit_potential: this.calculateTotalProfit(strategies),
      active_listings: Array.isArray(listings) ? listings.length : 0,
      buyer_interests: this.countBuyerInterests(listings),
      active_crops: Array.isArray(crops) ? crops.length : 0,
      pending_tasks: this.countPendingTasks(strategies),
    };

    // Transform crops data
    const active_crops: ActiveCrop[] = Array.isArray(crops)
      ? crops.map((crop: any) => this.transformCropData(crop))
      : [];

    // Extract upcoming tasks from strategies
    const upcoming_tasks: UpcomingTask[] = this.extractUpcomingTasks(
      strategies,
    );

    // Extract buyer interests from listings
    const buyer_interests: BuyerInterest[] = this.extractBuyerInterests(
      listings,
    );

    // Extract strategy timeline
    const strategy_timeline: SeasonProgress[] = this.extractStrategyTimeline(
      strategies,
    );

    return {
      stats,
      active_crops,
      active_listings: Array.isArray(listings) ? listings : [],
      upcoming_tasks,
      buyer_interests,
      weather_alerts: [], // Will be populated when weather API is available
      strategy_timeline,
    };
  }

  /**
   * Calculate total profit potential from strategies
   */
  private static calculateTotalProfit(strategies: any[]): number {
    if (!Array.isArray(strategies)) return 0;

    return strategies.reduce((total, strategy) => {
      const kharifProfit = strategy.kharif_profit_estimate || 0;
      const rabiProfit = strategy.rabi_profit_estimate || 0;
      const zaidProfit = strategy.zaid_profit_estimate || 0;
      return total + kharifProfit + rabiProfit + zaidProfit;
    }, 0);
  }

  /**
   * Count buyer interests from listings
   */
  private static countBuyerInterests(listings: any[]): number {
    if (!Array.isArray(listings)) return 0;

    return listings.reduce((total, listing) => {
      return total + (listing.interest_count || 0);
    }, 0);
  }

  /**
   * Count pending tasks from strategies
   */
  private static countPendingTasks(strategies: any[]): number {
    if (!Array.isArray(strategies)) return 0;

    // Extract monthly action plans and count pending tasks
    let taskCount = 0;
    strategies.forEach((strategy: any) => {
      if (strategy.monthly_action_plan) {
        taskCount += strategy.monthly_action_plan.length;
      }
    });
    return taskCount;
  }

  /**
   * Transform crop data to ActiveCrop format
   */
  private static transformCropData(crop: any): ActiveCrop {
    const plantingDate = new Date(crop.planting_date || crop.created_at);
    const harvestDate = new Date(
      crop.expected_harvest_date || Date.now() + 90 * 24 * 60 * 60 * 1000,
    );
    const daysUntilHarvest = Math.ceil(
      (harvestDate.getTime() - Date.now()) / (24 * 60 * 60 * 1000),
    );

    return {
      id: crop.id,
      crop_type: crop.crop_type || "Unknown",
      crop_variety: crop.crop_variety || "",
      planting_date: plantingDate.toISOString(),
      expected_harvest_date: harvestDate.toISOString(),
      estimated_quantity: crop.estimated_quantity || 0,
      quantity_unit: crop.quantity_unit || "quintals",
      growth_stage: this.determineGrowthStage(daysUntilHarvest),
      days_until_harvest: daysUntilHarvest,
    };
  }

  /**
   * Determine growth stage based on days until harvest
   */
  private static determineGrowthStage(
    daysUntilHarvest: number,
  ): "planted" | "growing" | "maturing" | "ready" | "overdue" {
    if (daysUntilHarvest < 0) return "overdue";
    if (daysUntilHarvest <= 7) return "ready";
    if (daysUntilHarvest <= 30) return "maturing";
    if (daysUntilHarvest <= 60) return "growing";
    return "planted";
  }

  /**
   * Extract upcoming tasks from strategies
   */
  private static extractUpcomingTasks(strategies: any[]): UpcomingTask[] {
    if (!Array.isArray(strategies)) return [];

    const tasks: UpcomingTask[] = [];
    const currentMonth = new Date().getMonth();

    strategies.forEach((strategy: any) => {
      if (
        strategy.monthly_action_plan &&
        Array.isArray(strategy.monthly_action_plan)
      ) {
        strategy.monthly_action_plan.forEach(
          (monthPlan: any, index: number) => {
            if (monthPlan.actions && Array.isArray(monthPlan.actions)) {
              monthPlan.actions.forEach(
                (action: string, actionIndex: number) => {
                  // Only include upcoming tasks (current month and next 2 months)
                  if (index >= currentMonth && index <= currentMonth + 2) {
                    tasks.push({
                      id: `${strategy.id}-${index}-${actionIndex}`,
                      title: action,
                      description: `${monthPlan.month} - ${
                        strategy.kharif_crop || strategy.rabi_crop
                      }`,
                      due_date: this.getMonthDate(index),
                      priority: index === currentMonth ? "high" : "medium",
                      category: "farming",
                      status: "pending",
                    });
                  }
                },
              );
            }
          },
        );
      }
    });

    return tasks.slice(0, 10); // Limit to 10 upcoming tasks
  }

  /**
   * Get date for a specific month index
   */
  private static getMonthDate(monthIndex: number): string {
    const date = new Date();
    date.setMonth(monthIndex);
    date.setDate(15); // Mid-month
    return date.toISOString();
  }

  /**
   * Extract buyer interests from listings
   */
  private static extractBuyerInterests(listings: any[]): BuyerInterest[] {
    if (!Array.isArray(listings)) return [];

    const interests: BuyerInterest[] = [];

    listings.forEach((listing: any) => {
      if (listing.buyer_interests && Array.isArray(listing.buyer_interests)) {
        listing.buyer_interests.forEach((interest: any) => {
          interests.push({
            id: interest.id,
            listing_id: listing.id,
            crop_type: listing.crop_type,
            buyer_name: interest.buyer_name,
            buyer_company: interest.buyer_company,
            quantity_interested: interest.quantity_interested || 0,
            preferred_price: interest.preferred_price,
            status: interest.status || "pending",
            created_at: interest.created_at,
          });
        });
      }
    });

    return interests.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    ).slice(0, 10); // Limit to 10 most recent
  }

  /**
   * Get analytics for a specific farm
   */
  static async getFarmAnalytics(farmId: number): Promise<any> {
    const url = buildUrl("analytics", "farmAnalytics", { farm_id: farmId });
    const response = await apiClient.get(url);
    return response.data;
  }

  /**
   * Add a new expense for a crop
   */
  static async addCropExpense(cropId: string, expense: {
    category: string;
    amount: number;
    description?: string;
    expense_date: string;
  }): Promise<any> {
    const url = `/api/v1/crops/${cropId}/expenses`;
    const response = await apiClient.post(url, expense);
    return response.data;
  }

  /**
   * Delete a crop record
   */
  static async deleteCrop(cropId: number | string): Promise<void> {
    await apiClient.delete(`/islogin/crop/${cropId}`);
  }

  /**
   * Get weather alerts
   */
  static async getWeatherAlerts(): Promise<WeatherAlert[]> {
    try {
      const url = buildUrl("weather", "alerts");
      const response = await apiClient.get<WeatherAlert[]>(
        url,
        {
          cache: true,
          cacheTTL: 300000, // 5 minutes cache
        },
      );
      return response.data;
    } catch (error) {
      console.error("Failed to fetch weather alerts:", error);
      return [];
    }
  }

  /**
   * Extract strategy timeline from strategies
   */
  private static extractStrategyTimeline(strategies: any[]): SeasonProgress[] {
    if (!Array.isArray(strategies) || strategies.length === 0) return [];

    const currentMonth = new Date().getMonth();
    const timeline: SeasonProgress[] = [];

    strategies.forEach((strategy: any) => {
      // Kharif Season (June-October)
      if (strategy.kharif_crop) {
        const kharifTasks = this.extractSeasonTasks(strategy, "kharif", 5, 9); // June (5) to October (9)
        timeline.push({
          season: "Kharif",
          crop: strategy.kharif_crop,
          startMonth: 5,
          endMonth: 9,
          tasks: kharifTasks,
          status: this.determineSeasonStatus(5, 9, currentMonth),
        });
      }

      // Rabi Season (November-March)
      if (strategy.rabi_crop) {
        const rabiTasks = this.extractSeasonTasks(strategy, "rabi", 10, 2); // November (10) to March (2)
        timeline.push({
          season: "Rabi",
          crop: strategy.rabi_crop,
          startMonth: 10,
          endMonth: 2,
          tasks: rabiTasks,
          status: this.determineSeasonStatus(10, 2, currentMonth),
        });
      }

      // Zaid Season (April-June)
      if (strategy.zaid_crop) {
        const zaidTasks = this.extractSeasonTasks(strategy, "zaid", 3, 5); // April (3) to June (5)
        timeline.push({
          season: "Zaid",
          crop: strategy.zaid_crop,
          startMonth: 3,
          endMonth: 5,
          tasks: zaidTasks,
          status: this.determineSeasonStatus(3, 5, currentMonth),
        });
      }
    });

    return timeline;
  }

  /**
   * Extract tasks for a specific season
   */
  private static extractSeasonTasks(
    strategy: any,
    season: string,
    startMonth: number,
    endMonth: number,
  ): { month: string; actions: string[]; completed: boolean }[] {
    const tasks: { month: string; actions: string[]; completed: boolean }[] =
      [];
    const monthNames = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];

    if (
      strategy.monthly_action_plan &&
      Array.isArray(strategy.monthly_action_plan)
    ) {
      // Handle wrap-around for seasons that cross year boundary (e.g., Rabi: Nov-Mar)
      const months = endMonth >= startMonth
        ? Array.from(
          { length: endMonth - startMonth + 1 },
          (_, i) => startMonth + i,
        )
        : [
          ...Array.from({ length: 12 - startMonth }, (_, i) => startMonth + i),
          ...Array.from({ length: endMonth + 1 }, (_, i) => i),
        ];

      months.forEach((monthIndex) => {
        const monthPlan = strategy.monthly_action_plan[monthIndex];
        if (
          monthPlan && monthPlan.actions && Array.isArray(monthPlan.actions)
        ) {
          tasks.push({
            month: monthNames[monthIndex],
            actions: monthPlan.actions,
            completed: monthPlan.completed || false,
          });
        }
      });
    }

    return tasks;
  }

  /**
   * Determine season status based on current month
   */
  private static determineSeasonStatus(
    startMonth: number,
    endMonth: number,
    currentMonth: number,
  ): "upcoming" | "active" | "completed" {
    // Handle wrap-around for seasons that cross year boundary
    if (endMonth >= startMonth) {
      // Normal season (doesn't cross year)
      if (currentMonth >= startMonth && currentMonth <= endMonth) {
        return "active";
      }
      if (currentMonth < startMonth) {
        return "upcoming";
      }
      return "completed";
    } else {
      // Season crosses year boundary (e.g., Rabi: Nov-Mar)
      if (currentMonth >= startMonth || currentMonth <= endMonth) {
        return "active";
      }
      if (currentMonth < startMonth && currentMonth > endMonth) {
        return currentMonth < 6 ? "completed" : "upcoming";
      }
      return "upcoming";
    }
  }
}
