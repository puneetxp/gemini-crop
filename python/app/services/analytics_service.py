"""
Analytics Service for comprehensive dashboard metrics
Provides farmer analytics, platform analytics, and market analytics using raw SQL queries
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsService:
    """Service for generating analytics and insights"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_farmer_analytics(
        self,
        farmer_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive farmer analytics with crop performance, profit trends, and ROI tracking"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        crop_performance = await self._get_crop_performance(farmer_id, start_date, end_date)
        profit_trends = await self._get_profit_trends(farmer_id, start_date, end_date)
        roi_tracking = await self._get_roi_tracking(farmer_id, start_date, end_date)
        regional_comparison = await self._get_regional_comparison(farmer_id)

        return {
            "farmer_id": farmer_id,
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "crop_performance": crop_performance,
            "profit_trends": profit_trends,
            "roi_tracking": roi_tracking,
            "regional_comparison": regional_comparison,
        }

    async def get_farm_analytics(
        self,
        farm_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get analytics for a specific farm"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        # Get farm details
        farm_query = text(
            "SELECT id, name, location_state, location_district, primary_soil_type, total_area, irrigation_type FROM farms WHERE id = :farm_id"
        )
        farm_result = await self.db.execute(farm_query, {"farm_id": farm_id})
        farm = farm_result.first()

        if not farm:
            return {"error": "Farm not found"}

        # Get plot performance for this farm
        plot_performance = await self._get_plot_performance(farm_id, start_date, end_date)

        # Get profit trends for this specific farm
        profit_trends = await self._get_farm_profit_trends(farm_id, start_date, end_date)

        # Get latest strategy
        strategy_query = text("""
            SELECT id, created_at, kharif_crop, rabi_crop, total_annual_profit 
            FROM annual_strategies 
            WHERE farm_id = :farm_id 
            ORDER BY created_at DESC LIMIT 1
        """)
        strategy_result = await self.db.execute(strategy_query, {"farm_id": farm_id})
        latest_strategy = strategy_result.first()

        # Always provide contextual crop recommendations using Bedrock AI
        recommended_crops = []
        current_season = "rabi"  # default
        try:
            import logging as _logging

            from app.services.bedrock_service import BedrockService

            bedrock = BedrockService()

            current_month = datetime.now().month
            current_date_str = datetime.now().strftime("%B %d")

            if 3 <= current_month <= 5:
                current_season = "zaid"
                season_display = "Zaid (Summer: March - June)"
            elif 6 <= current_month <= 10:
                current_season = "kharif"
                season_display = "Kharif (Monsoon: June - Oct)"
            else:
                current_season = "rabi"
                season_display = "Rabi (Winter: Nov - Feb)"

            state = farm.location_state or "Haryana"
            district = farm.location_district or "Gurgaon"
            soil_type = farm.primary_soil_type or "loamy"
            total_area = float(farm.total_area or 1.0)
            irrigation_type = farm.irrigation_type or "rainfed"

            rec_result = await bedrock.get_crop_recommendations(
                state=state,
                district=district,
                season=season_display,
                soil_type=soil_type,
                area_acres=total_area,
                irrigation_type=irrigation_type,
                current_date=current_date_str,
            )

            if rec_result and "recommendations" in rec_result:
                recommended_crops = rec_result["recommendations"][:4]
                today = datetime.now()
                today_str = today.strftime("%Y-%m-%d")
                for crop in recommended_crops:
                    crop["season_display"] = season_display
                    # Normalize planting window to ISO date if it's a text description
                    planting_raw = crop.get("optimal_planting_window", "")
                    if planting_raw and not self._is_iso_date(planting_raw):
                        crop["optimal_planting_window"] = today_str
                    elif not planting_raw:
                        crop["optimal_planting_window"] = today_str
                    # Normalize harvest window to ISO date from days_to_harvest
                    harvest_raw = crop.get("optimal_harvest_window", "")
                    days = int(crop.get("days_to_harvest", 90))
                    if harvest_raw and not self._is_iso_date(harvest_raw):
                        harvest_dt = today + timedelta(days=days)
                        crop["optimal_harvest_window"] = harvest_dt.strftime("%Y-%m-%d")
                    elif not harvest_raw:
                        harvest_dt = today + timedelta(days=days)
                        crop["optimal_harvest_window"] = harvest_dt.strftime("%Y-%m-%d")
        except Exception as e:
            import logging as _logging

            _logging.getLogger(__name__).error(f"Failed to get AI recommendations: {e}")
            # Compute season dates
            current_month = datetime.now().month
            if 3 <= current_month <= 5:
                current_season = "zaid"
                season_display = "Zaid (Summer: March - June)"
            elif 6 <= current_month <= 10:
                current_season = "kharif"
                season_display = "Kharif (Monsoon: June - Oct)"
            else:
                current_season = "rabi"
                season_display = "Rabi (Winter: Nov - Feb)"

            now = datetime.now()
            # Rich fallback data per season with pre-computed ISO dates and days_to_harvest
            fallback_data = {
                "kharif": [
                    {
                        "crop_name": "Rice",
                        "variety": "Basmati 1718",
                        "suitability_reason": "Ideal for monsoon season with good water availability",
                        "expected_yield_per_acre": "18-22 qtl",
                        "days_to_harvest": 120,
                        "market_demand": "High",
                    },
                    {
                        "crop_name": "Maize",
                        "variety": "DKC 9144",
                        "suitability_reason": "High-yield hybrid, low water requirement",
                        "expected_yield_per_acre": "20-25 qtl",
                        "days_to_harvest": 90,
                        "market_demand": "High",
                    },
                    {
                        "crop_name": "Cotton",
                        "variety": "RCH 650 BG II",
                        "suitability_reason": "Premium market crop suited to your soil type",
                        "expected_yield_per_acre": "10-12 qtl",
                        "days_to_harvest": 160,
                        "market_demand": "High",
                    },
                    {
                        "crop_name": "Soybean",
                        "variety": "JS 335",
                        "suitability_reason": "Nitrogen-fixing, improves soil health",
                        "expected_yield_per_acre": "12-15 qtl",
                        "days_to_harvest": 100,
                        "market_demand": "Medium",
                    },
                ],
                "rabi": [
                    {
                        "crop_name": "Wheat",
                        "variety": "HD 3086",
                        "suitability_reason": "Top-yielding variety suited to North India winters",
                        "expected_yield_per_acre": "18-22 qtl",
                        "days_to_harvest": 120,
                        "market_demand": "High",
                    },
                    {
                        "crop_name": "Mustard",
                        "variety": "RH 725",
                        "suitability_reason": "Drought-tolerant, high oil content, strong market demand",
                        "expected_yield_per_acre": "8-10 qtl",
                        "days_to_harvest": 100,
                        "market_demand": "High",
                    },
                    {
                        "crop_name": "Chickpea",
                        "variety": "HC 1",
                        "suitability_reason": "High protein, low water requirement",
                        "expected_yield_per_acre": "6-8 qtl",
                        "days_to_harvest": 110,
                        "market_demand": "Medium",
                    },
                    {
                        "crop_name": "Barley",
                        "variety": "RD 2552",
                        "suitability_reason": "Hardy winter crop, good for animal feed and malt",
                        "expected_yield_per_acre": "15-18 qtl",
                        "days_to_harvest": 95,
                        "market_demand": "Medium",
                    },
                ],
                "zaid": [
                    {
                        "crop_name": "Watermelon",
                        "variety": "Arka Jyoti",
                        "suitability_reason": "High summer demand, quick income crop",
                        "expected_yield_per_acre": "80-100 qtl",
                        "days_to_harvest": 75,
                        "market_demand": "High",
                    },
                    {
                        "crop_name": "Cucumber",
                        "variety": "Poinsett 76",
                        "suitability_reason": "Fast growing, high water content crop",
                        "expected_yield_per_acre": "50-60 qtl",
                        "days_to_harvest": 55,
                        "market_demand": "Medium",
                    },
                    {
                        "crop_name": "Moong Dal",
                        "variety": "Pusa Vishal",
                        "suitability_reason": "Short duration, nitrogen-fixing legume",
                        "expected_yield_per_acre": "5-6 qtl",
                        "days_to_harvest": 65,
                        "market_demand": "High",
                    },
                    {
                        "crop_name": "Sunflower",
                        "variety": "KBSH 44",
                        "suitability_reason": "Drought-tolerant oilseed crop with strong demand",
                        "expected_yield_per_acre": "8-10 qtl",
                        "days_to_harvest": 90,
                        "market_demand": "High",
                    },
                ],
            }
            planting_date = now.strftime("%Y-%m-%d")
            recommended_crops = []
            for crop_info in fallback_data.get(current_season, []):
                harvest_dt = now + timedelta(days=crop_info["days_to_harvest"])
                recommended_crops.append(
                    {
                        **crop_info,
                        "season": current_season,
                        "season_display": season_display,
                        "confidence_score": 0.70,
                        "optimal_planting_window": planting_date,
                        "optimal_harvest_window": harvest_dt.strftime("%Y-%m-%d"),
                    }
                )

        # Get active crops for this farm
        active_crops_query = text("""
            SELECT 
                c.id, c.crop_name, c.crop_variety, c.planting_date, c.expected_harvest_date, 
                c.expected_yield, c.expected_profit, c.status,
                fp.id as plot_id, fp.plot_name, fp.area as plot_area, fp.soil_type,
                COALESCE((SELECT SUM(amount) FROM crop_expenses WHERE crop_id = c.id), 0) as total_expenses
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            WHERE fp.farm_id = :farm_id AND c.status IN ('planted', 'growing', 'harvested')
            ORDER BY c.planting_date DESC
        """)
        active_crops_result = await self.db.execute(active_crops_query, {"farm_id": farm_id})
        active_crops = [
            {
                "id": row.id,
                "crop_type": row.crop_name,  # Match frontend expectation
                "crop_name": row.crop_name,
                "crop_variety": row.crop_variety,
                "plot_id": row.plot_id,
                "plot_name": row.plot_name,
                "plot_area": float(row.plot_area) if row.plot_area else 0,
                "soil_type": row.soil_type,
                "planting_date": row.planting_date.isoformat() if row.planting_date else None,
                "expected_harvest_date": (
                    row.expected_harvest_date.isoformat() if row.expected_harvest_date else None
                ),
                "expected_yield": float(row.expected_yield) if row.expected_yield else 0,
                "expected_profit": float(row.expected_profit) if row.expected_profit else 0,
                "total_expenses": float(row.total_expenses),
                "projected_profit": float(row.expected_profit or 0) - float(row.total_expenses),
                "status": row.status,
            }
            for row in active_crops_result.fetchall()
        ]

        # Get all plots for this farm with their current crop if any
        plots_query = text("""
            SELECT 
                fp.id, fp.plot_name, fp.area, fp.soil_type, fp.irrigation_type,
                c.crop_name as current_crop, c.status as crop_status
            FROM farm_plots fp
            LEFT JOIN crops c ON c.farm_plot_id = fp.id AND c.status IN ('planted', 'growing')
            WHERE fp.farm_id = :farm_id AND fp.enable = 1
            ORDER BY fp.plot_name
        """)
        plots_result = await self.db.execute(plots_query, {"farm_id": farm_id})
        farm_plots = [
            {
                "id": row.id,
                "plot_name": row.plot_name,
                "area": float(row.area) if row.area else 0,
                "soil_type": row.soil_type,
                "irrigation_type": row.irrigation_type,
                "current_crop": row.current_crop,
                "crop_status": row.crop_status,
            }
            for row in plots_result.fetchall()
        ]

        return {
            "farm_id": farm_id,
            "farm_name": farm.name,
            "farm_total_area": float(farm.total_area) if farm.total_area else 0.0,
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "plot_performance": plot_performance,
            "profit_trends": profit_trends,
            "active_crops": active_crops,
            "farm_plots": farm_plots,
            "latest_strategy": (
                {
                    "id": latest_strategy.id,
                    "generated_at": latest_strategy.created_at.isoformat(),
                    "crops": [latest_strategy.kharif_crop, latest_strategy.rabi_crop],
                    "expected_profit": float(latest_strategy.total_annual_profit),
                }
                if latest_strategy
                else None
            ),
            "recommended_crops": recommended_crops,
            "current_season": current_season,
        }

    async def _get_plot_performance(
        self, farm_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get per-plot performance metrics for a farm"""
        query = text("""
            SELECT 
                fp.id as plot_id,
                fp.plot_name,
                COUNT(c.id) as crop_count,
                COALESCE(SUM(c.actual_yield), 0) as actual_yield,
                COALESCE(SUM(c.expected_yield), 0) as expected_yield,
                COALESCE(SUM(c.actual_profit), 0) as actual_profit,
                COALESCE(SUM(c.expected_profit), 0) as expected_profit
            FROM farm_plots fp
            LEFT JOIN crops c ON fp.id = c.farm_plot_id
            WHERE fp.farm_id = :farm_id
                AND (c.created_at IS NULL OR (c.created_at >= :start_date AND c.created_at <= :end_date))
            GROUP BY fp.id, fp.plot_name
        """)

        result = await self.db.execute(
            query, {"farm_id": farm_id, "start_date": start_date, "end_date": end_date}
        )
        rows = result.fetchall()
        plot_data = [
            {
                "plot_id": row.plot_id,
                "plot_name": row.plot_name,
                "crop_count": row.crop_count,
                "yield_accuracy": (
                    (float(row.actual_yield) / float(row.expected_yield) * 100)
                    if row.expected_yield > 0
                    else 0
                ),
                "profit_accuracy": (
                    (float(row.actual_profit) / float(row.expected_profit) * 100)
                    if row.expected_profit > 0
                    else 0
                ),
                "actual_profit": float(row.actual_profit),
            }
            for row in rows
        ]

        if not plot_data or all(item["crop_count"] == 0 for item in plot_data):
            fallback_rows = await self._get_plot_performance_all_time(farm_id)
            if fallback_rows:
                plot_data = fallback_rows

        return plot_data

    async def _get_farm_profit_trends(
        self, farm_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get profit trends for a specific farm"""
        query = text("""
            SELECT 
                TO_CHAR(c.planting_date, 'YYYY-MM') as month,
                COALESCE(SUM(c.actual_profit), 0) as profit
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            WHERE fp.farm_id = :farm_id
                AND c.planting_date >= :start_date
                AND c.planting_date <= :end_date
            GROUP BY TO_CHAR(c.planting_date, 'YYYY-MM')
            ORDER BY month
        """)

        result = await self.db.execute(
            query, {"farm_id": farm_id, "start_date": start_date, "end_date": end_date}
        )
        rows = result.fetchall()
        trends = [{"month": row.month, "profit": float(row.profit)} for row in rows]

        if not trends:
            fallback_rows = await self._get_farm_profit_trends_all_time(farm_id)
            if fallback_rows:
                trends = fallback_rows

        return trends

    async def _get_farm_profit_trends_all_time(self, farm_id: int) -> List[Dict[str, Any]]:
        """Fallback: get all-time profit trends for a farm (no date filter)"""
        query = text("""
            SELECT 
                TO_CHAR(c.planting_date, 'YYYY-MM') as month,
                COALESCE(SUM(c.actual_profit), 0) as profit
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            WHERE fp.farm_id = :farm_id
                AND c.planting_date IS NOT NULL
            GROUP BY TO_CHAR(c.planting_date, 'YYYY-MM')
            ORDER BY month
        """)
        result = await self.db.execute(query, {"farm_id": farm_id})
        rows = result.fetchall()
        return [{"month": row.month, "profit": float(row.profit)} for row in rows]

    async def _get_plot_performance_all_time(self, farm_id: int) -> List[Dict[str, Any]]:
        """Fallback: get all-time plot performance for a farm (no date filter)"""
        query = text("""
            SELECT 
                fp.id as plot_id,
                fp.plot_name,
                COUNT(c.id) as crop_count,
                COALESCE(SUM(c.actual_yield), 0) as actual_yield,
                COALESCE(SUM(c.expected_yield), 0) as expected_yield,
                COALESCE(SUM(c.actual_profit), 0) as actual_profit,
                COALESCE(SUM(c.expected_profit), 0) as expected_profit
            FROM farm_plots fp
            LEFT JOIN crops c ON fp.id = c.farm_plot_id
            WHERE fp.farm_id = :farm_id
            GROUP BY fp.id, fp.plot_name
        """)
        result = await self.db.execute(query, {"farm_id": farm_id})
        rows = result.fetchall()
        return [
            {
                "plot_id": row.plot_id,
                "plot_name": row.plot_name,
                "crop_count": row.crop_count,
                "yield_accuracy": (
                    (float(row.actual_yield) / float(row.expected_yield) * 100)
                    if row.expected_yield > 0
                    else 0
                ),
                "profit_accuracy": (
                    (float(row.actual_profit) / float(row.expected_profit) * 100)
                    if row.expected_profit > 0
                    else 0
                ),
                "actual_profit": float(row.actual_profit),
            }
            for row in rows
        ]

    def _determine_current_season(self) -> tuple:
        """Determine the current Indian agricultural season based on the current month."""
        month = datetime.now().month
        if month in (6, 7, 8, 9, 10):
            return ("kharif", "Kharif (Jun-Oct)")
        elif month in (11, 12, 1, 2, 3):
            return ("rabi", "Rabi (Nov-Mar)")
        else:
            return ("zaid", "Zaid / Summer (Apr-May)")

    def _is_strategy_stale(self, created_at) -> bool:
        """Return True if the strategy is more than 6 months old."""
        if not created_at:
            return True
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                return True
        return (datetime.now() - created_at).days > 180

    async def _get_quick_crop_recommendations(
        self, farm, season_display: str, current_date_str: str
    ) -> List[Dict[str, Any]]:
        """Generate simple crop recommendations based on regional historical data."""
        try:
            query = text("""
                SELECT c.crop_name, COUNT(*) as frequency,
                    AVG(c.expected_profit) as avg_expected_profit
                FROM crops c
                JOIN farm_plots fp ON c.farm_plot_id = fp.id
                JOIN farms f ON fp.farm_id = f.id
                WHERE f.location_state = :state
                    AND f.location_district = :district
                GROUP BY c.crop_name
                ORDER BY frequency DESC, avg_expected_profit DESC
                LIMIT 5
            """)
            result = await self.db.execute(
                query,
                {"state": farm.location_state or "", "district": farm.location_district or ""},
            )
            rows = result.fetchall()
            if rows:
                return [
                    {
                        "crop_name": row.crop_name,
                        "season": season_display,
                        "reason": f"Popular in {farm.location_district} with avg profit Rs{int(row.avg_expected_profit or 0)}/acre",
                        "confidence": min(0.6 + row.frequency * 0.05, 0.95),
                    }
                    for row in rows
                ]
        except Exception:
            pass
        # Static fallback
        season_crops = {
            "kharif": ["Rice", "Maize", "Cotton", "Soybean", "Groundnut"],
            "rabi": ["Wheat", "Mustard", "Chickpea", "Peas", "Barley"],
            "zaid": ["Watermelon", "Muskmelon", "Cucumber", "Moong Dal", "Sunflower"],
        }
        season_key = (
            "kharif"
            if "Kharif" in season_display
            else ("rabi" if "Rabi" in season_display else "zaid")
        )
        return [
            {
                "crop_name": crop,
                "season": season_display,
                "reason": f"Recommended for {season_display} season",
                "confidence": 0.6,
            }
            for crop in season_crops.get(season_key, [])
        ]

    async def _get_crop_performance(
        self, farmer_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get crop performance metrics: yield vs predicted, profit vs expected"""
        query = text("""
            SELECT 
                COUNT(*) as total_crops,
                COALESCE(SUM(actual_yield), 0) as total_actual_yield,
                COALESCE(SUM(expected_yield), 0) as total_expected_yield,
                COALESCE(SUM(actual_profit), 0) as total_actual_profit,
                COALESCE(SUM(expected_profit), 0) as total_expected_profit
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            JOIN farms f ON fp.farm_id = f.id
            WHERE f.farmer_id = :farmer_id
                AND c.created_at >= :start_date
                AND c.created_at <= :end_date
        """)

        result = await self.db.execute(
            query, {"farmer_id": farmer_id, "start_date": start_date, "end_date": end_date}
        )
        row = result.first()

        if not row or row.total_crops == 0:
            return {
                "total_crops": 0,
                "total_actual_yield": 0.0,
                "total_expected_yield": 0.0,
                "total_actual_profit": 0.0,
                "total_expected_profit": 0.0,
                "yield_accuracy_percentage": 0.0,
                "profit_accuracy_percentage": 0.0,
            }

        yield_accuracy = (
            (row.total_actual_yield / row.total_expected_yield * 100)
            if row.total_expected_yield > 0
            else 0
        )
        profit_accuracy = (
            (row.total_actual_profit / row.total_expected_profit * 100)
            if row.total_expected_profit > 0
            else 0
        )

        return {
            "total_crops": row.total_crops,
            "total_actual_yield": round(float(row.total_actual_yield), 2),
            "total_expected_yield": round(float(row.total_expected_yield), 2),
            "total_actual_profit": round(float(row.total_actual_profit), 2),
            "total_expected_profit": round(float(row.total_expected_profit), 2),
            "yield_accuracy_percentage": round(yield_accuracy, 2),
            "profit_accuracy_percentage": round(profit_accuracy, 2),
        }

    async def _get_profit_trends(
        self, farmer_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get profit trends over time"""
        query = text("""
            SELECT 
                TO_CHAR(c.planting_date, 'YYYY-MM') as month,
                COALESCE(SUM(c.expected_profit), 0) as expected,
                COALESCE(SUM(c.actual_profit), 0) as actual,
                COUNT(*) as count
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            JOIN farms f ON fp.farm_id = f.id
            WHERE f.farmer_id = :farmer_id
                AND c.created_at >= :start_date
                AND c.created_at <= :end_date
                AND c.planting_date IS NOT NULL
            GROUP BY TO_CHAR(c.planting_date, 'YYYY-MM')
            ORDER BY month
        """)

        result = await self.db.execute(
            query, {"farmer_id": farmer_id, "start_date": start_date, "end_date": end_date}
        )
        rows = result.fetchall()

        trends = [
            {
                "month": row.month,
                "expected": float(row.expected),
                "actual": float(row.actual),
                "count": row.count,
            }
            for row in rows
        ]
        total_actual_profit = sum(t["actual"] for t in trends)

        return {"monthly_trends": trends, "total_actual_profit": round(total_actual_profit, 2)}

    async def _get_roi_tracking(
        self, farmer_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get ROI tracking: investment vs returns, profit margins"""
        # Get expected profit from strategies
        strategy_query = text("""
            SELECT COALESCE(SUM(total_annual_profit), 0) as total_expected
            FROM annual_strategies
            WHERE farmer_id = :farmer_id
                AND created_at >= :start_date
                AND created_at <= :end_date
        """)

        strategy_result = await self.db.execute(
            strategy_query, {"farmer_id": farmer_id, "start_date": start_date, "end_date": end_date}
        )
        strategy_row = strategy_result.first()
        total_expected_profit = float(strategy_row.total_expected) if strategy_row else 0

        # Get actual profit from crops
        crop_query = text("""
            SELECT COALESCE(SUM(c.actual_profit), 0) as total_actual
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            JOIN farms f ON fp.farm_id = f.id
            WHERE f.farmer_id = :farmer_id
                AND c.created_at >= :start_date
                AND c.created_at <= :end_date
        """)

        crop_result = await self.db.execute(
            crop_query, {"farmer_id": farmer_id, "start_date": start_date, "end_date": end_date}
        )
        crop_row = crop_result.first()
        total_actual_profit = float(crop_row.total_actual) if crop_row else 0

        roi_percentage = (
            (total_actual_profit / total_expected_profit * 100) if total_expected_profit > 0 else 0
        )
        investment_estimate = total_expected_profit * 0.4  # Assume 40% investment
        profit_margin = (
            (total_actual_profit / (total_actual_profit + investment_estimate) * 100)
            if (total_actual_profit + investment_estimate) > 0
            else 0
        )

        return {
            "total_investment_estimate": round(investment_estimate, 2),
            "total_expected_returns": round(total_expected_profit, 2),
            "total_actual_returns": round(total_actual_profit, 2),
            "roi_percentage": round(roi_percentage, 2),
            "profit_margin": round(profit_margin, 2),
        }

    async def _get_regional_comparison(self, farmer_id: int) -> Dict[str, Any]:
        """Get comparison with regional averages"""
        # Get farmer's location
        farm_query = text("""
            SELECT location_state, location_district
            FROM farms
            WHERE farmer_id = :farmer_id
            LIMIT 1
        """)

        farm_result = await self.db.execute(farm_query, {"farmer_id": farmer_id})
        farm_row = farm_result.first()

        if not farm_row:
            return {
                "regional_average_profit": 0.0,
                "farmer_average_profit": 0.0,
                "performance": "N/A",
            }

        # Get regional average
        regional_query = text("""
            SELECT AVG(c.actual_profit) as avg_profit
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            JOIN farms f ON fp.farm_id = f.id
            WHERE f.location_state = :state
                AND f.location_district = :district
                AND c.actual_profit IS NOT NULL
                AND c.actual_profit > 0
        """)

        regional_result = await self.db.execute(
            regional_query,
            {"state": farm_row.location_state, "district": farm_row.location_district},
        )
        regional_row = regional_result.first()
        avg_regional_profit = (
            float(regional_row.avg_profit) if regional_row and regional_row.avg_profit else 0
        )

        # Get farmer average
        farmer_query = text("""
            SELECT AVG(c.actual_profit) as avg_profit
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            JOIN farms f ON fp.farm_id = f.id
            WHERE f.farmer_id = :farmer_id
                AND c.actual_profit IS NOT NULL
                AND c.actual_profit > 0
        """)

        farmer_result = await self.db.execute(farmer_query, {"farmer_id": farmer_id})
        farmer_row = farmer_result.first()
        avg_farmer_profit = (
            float(farmer_row.avg_profit) if farmer_row and farmer_row.avg_profit else 0
        )

        performance = (
            "Above Average" if avg_farmer_profit > avg_regional_profit else "Below Average"
        )

        return {
            "regional_average_profit": round(avg_regional_profit, 2),
            "farmer_average_profit": round(avg_farmer_profit, 2),
            "performance": performance,
        }

    async def get_platform_analytics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get platform analytics: user adoption, feature usage, prediction accuracy"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        user_adoption = await self._get_user_adoption(start_date, end_date)
        feature_usage = await self._get_feature_usage(start_date, end_date)
        prediction_accuracy = await self._get_prediction_accuracy(start_date, end_date)

        return {
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "user_adoption": user_adoption,
            "feature_usage": feature_usage,
            "prediction_accuracy": prediction_accuracy,
        }

    async def _get_user_adoption(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user adoption trends: registrations, active users, retention"""
        total_query = text("SELECT COUNT(*) as total FROM users WHERE created_at <= :end_date")
        total_result = await self.db.execute(total_query, {"end_date": end_date})
        total_users = total_result.scalar() or 0

        new_query = text(
            "SELECT COUNT(*) as new_users FROM users WHERE created_at >= :start_date AND created_at <= :end_date"
        )
        new_result = await self.db.execute(
            new_query, {"start_date": start_date, "end_date": end_date}
        )
        new_users = new_result.scalar() or 0

        active_query = text("""
            SELECT COUNT(DISTINCT f.farmer_id) as active
            FROM crops c
            JOIN farm_plots fp ON c.farm_plot_id = fp.id
            JOIN farms f ON fp.farm_id = f.id
            WHERE c.created_at >= :start_date AND c.created_at <= :end_date
        """)
        active_result = await self.db.execute(
            active_query, {"start_date": start_date, "end_date": end_date}
        )
        active_users = active_result.scalar() or 0

        retention_rate = (active_users / total_users * 100) if total_users > 0 else 0

        return {
            "total_users": total_users,
            "new_users_period": new_users,
            "active_users_period": active_users,
            "retention_rate_percentage": round(retention_rate, 2),
        }

    async def _get_feature_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get feature usage statistics"""
        strategies_query = text(
            "SELECT COUNT(*) FROM annual_strategies WHERE created_at >= :start_date AND created_at <= :end_date"
        )
        strategies_result = await self.db.execute(
            strategies_query, {"start_date": start_date, "end_date": end_date}
        )
        strategies_created = strategies_result.scalar() or 0

        listings_query = text(
            "SELECT COUNT(*) FROM marketplace_listings WHERE created_at >= :start_date AND created_at <= :end_date"
        )
        listings_result = await self.db.execute(
            listings_query, {"start_date": start_date, "end_date": end_date}
        )
        listings_created = listings_result.scalar() or 0

        interests_query = text(
            "SELECT COUNT(*) FROM buyer_interests WHERE created_at >= :start_date AND created_at <= :end_date"
        )
        interests_result = await self.db.execute(
            interests_query, {"start_date": start_date, "end_date": end_date}
        )
        buyer_interests = interests_result.scalar() or 0

        most_used = "annual_strategy" if strategies_created > listings_created else "marketplace"

        return {
            "annual_strategies_created": strategies_created,
            "marketplace_listings_created": listings_created,
            "buyer_interests_registered": buyer_interests,
            "most_used_feature": most_used,
        }

    async def _get_prediction_accuracy(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get prediction accuracy over time"""
        query = text("""
            SELECT 
                expected_yield,
                actual_yield,
                expected_profit,
                actual_profit
            FROM crops
            WHERE created_at >= :start_date
                AND created_at <= :end_date
                AND status = 'harvested'
                AND expected_yield > 0
                AND actual_yield > 0
        """)

        result = await self.db.execute(query, {"start_date": start_date, "end_date": end_date})
        rows = result.fetchall()

        if not rows:
            return {
                "overall_accuracy_percentage": 0.0,
                "yield_accuracy_percentage": 0.0,
                "profit_accuracy_percentage": 0.0,
                "samples_analyzed": 0,
            }

        yield_accuracies = []
        profit_accuracies = []

        for row in rows:
            if row.expected_yield and row.expected_yield > 0:
                yield_acc = min((float(row.actual_yield) / float(row.expected_yield)) * 100, 100)
                yield_accuracies.append(yield_acc)

            if row.expected_profit and row.expected_profit > 0:
                profit_acc = min((float(row.actual_profit) / float(row.expected_profit)) * 100, 100)
                profit_accuracies.append(profit_acc)

        avg_yield_accuracy = (
            sum(yield_accuracies) / len(yield_accuracies) if yield_accuracies else 0
        )
        avg_profit_accuracy = (
            sum(profit_accuracies) / len(profit_accuracies) if profit_accuracies else 0
        )
        overall_accuracy = (avg_yield_accuracy + avg_profit_accuracy) / 2

        return {
            "overall_accuracy_percentage": round(overall_accuracy, 2),
            "yield_accuracy_percentage": round(avg_yield_accuracy, 2),
            "profit_accuracy_percentage": round(avg_profit_accuracy, 2),
            "samples_analyzed": len(rows),
        }

    async def get_market_analytics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get market analytics: price trends, demand patterns, supply forecasting"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        price_trends = await self._get_price_trends(start_date, end_date)
        demand_patterns = await self._get_demand_patterns(start_date, end_date)
        supply_forecast = await self._get_supply_forecast()

        return {
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "price_trends": price_trends,
            "demand_patterns": demand_patterns,
            "supply_forecast": supply_forecast,
        }

    async def _get_price_trends(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get price trends for major crops"""
        query = text("""
            SELECT 
                crop_name,
                AVG(actual_profit / NULLIF(actual_yield, 0)) as avg_price,
                MIN(actual_profit / NULLIF(actual_yield, 0)) as min_price,
                MAX(actual_profit / NULLIF(actual_yield, 0)) as max_price,
                COUNT(*) as samples
            FROM crops
            WHERE created_at >= :start_date
                AND created_at <= :end_date
                AND actual_profit > 0
                AND actual_yield > 0
            GROUP BY crop_name
            ORDER BY avg_price DESC
        """)

        result = await self.db.execute(query, {"start_date": start_date, "end_date": end_date})
        rows = result.fetchall()

        trends = [
            {
                "crop": row.crop_name,
                "average_price": round(float(row.avg_price), 2),
                "min_price": round(float(row.min_price), 2),
                "max_price": round(float(row.max_price), 2),
                "samples": row.samples,
            }
            for row in rows
        ]

        return {"crop_price_trends": trends}

    async def _get_demand_patterns(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get demand patterns by crop and region"""
        crop_query = text("""
            SELECT 
                ml.crop_type,
                COUNT(bi.id) as interest_count
            FROM buyer_interests bi
            JOIN marketplace_listings ml ON bi.listing_id = ml.id
            WHERE bi.created_at >= :start_date
                AND bi.created_at <= :end_date
            GROUP BY ml.crop_type
            ORDER BY interest_count DESC
            LIMIT 10
        """)

        crop_result = await self.db.execute(
            crop_query, {"start_date": start_date, "end_date": end_date}
        )
        crop_rows = crop_result.fetchall()

        top_crops = [
            {"crop": row.crop_type, "interest_count": row.interest_count} for row in crop_rows
        ]

        region_query = text("""
            SELECT 
                ml.location_state || '-' || ml.location_district as region,
                COUNT(bi.id) as interest_count
            FROM buyer_interests bi
            JOIN marketplace_listings ml ON bi.listing_id = ml.id
            WHERE bi.created_at >= :start_date
                AND bi.created_at <= :end_date
            GROUP BY ml.location_state, ml.location_district
            ORDER BY interest_count DESC
            LIMIT 10
        """)

        region_result = await self.db.execute(
            region_query, {"start_date": start_date, "end_date": end_date}
        )
        region_rows = region_result.fetchall()

        top_regions = [
            {"region": row.region, "interest_count": row.interest_count} for row in region_rows
        ]

        total_query = text(
            "SELECT COUNT(*) FROM buyer_interests WHERE created_at >= :start_date AND created_at <= :end_date"
        )
        total_result = await self.db.execute(
            total_query, {"start_date": start_date, "end_date": end_date}
        )
        total_interests = total_result.scalar() or 0

        return {
            "top_demanded_crops": top_crops,
            "top_demand_regions": top_regions,
            "total_buyer_interests": total_interests,
        }

    async def _get_supply_forecast(self) -> Dict[str, Any]:
        """Get supply forecasting for upcoming harvests"""
        future_date = datetime.now() + timedelta(days=90)

        query = text("""
            SELECT 
                crop_name,
                SUM(expected_yield) as expected_supply,
                COUNT(*) as farm_count
            FROM crops
            WHERE expected_harvest_date >= :now
                AND expected_harvest_date <= :future_date
                AND status = 'planted'
            GROUP BY crop_name
            ORDER BY expected_supply DESC
        """)

        result = await self.db.execute(query, {"now": datetime.now(), "future_date": future_date})
        rows = result.fetchall()

        forecasts = [
            {
                "crop": row.crop_name,
                "expected_supply": round(float(row.expected_supply), 2),
                "farm_count": row.farm_count,
            }
            for row in rows
        ]

        total_query = text("""
            SELECT COUNT(*) FROM crops
            WHERE expected_harvest_date >= :now
                AND expected_harvest_date <= :future_date
                AND status = 'planted'
        """)

        total_result = await self.db.execute(
            total_query, {"now": datetime.now(), "future_date": future_date}
        )
        total_upcoming = total_result.scalar() or 0

        return {"upcoming_harvests_90_days": forecasts, "total_upcoming_crops": total_upcoming}

    async def generate_executive_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate executive report with key insights and recommendations"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        platform_analytics = await self.get_platform_analytics(start_date, end_date)
        market_analytics = await self.get_market_analytics(start_date, end_date)

        insights = self._generate_insights(platform_analytics, market_analytics)
        recommendations = self._generate_recommendations(platform_analytics, market_analytics)

        return {
            "report_generated_at": datetime.now().isoformat(),
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "key_metrics": {
                "total_users": platform_analytics["user_adoption"]["total_users"],
                "active_users": platform_analytics["user_adoption"]["active_users_period"],
                "prediction_accuracy": platform_analytics["prediction_accuracy"][
                    "overall_accuracy_percentage"
                ],
                "total_buyer_interests": market_analytics["demand_patterns"][
                    "total_buyer_interests"
                ],
            },
            "insights": insights,
            "recommendations": recommendations,
        }

    def _generate_insights(
        self, platform_analytics: Dict[str, Any], market_analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate key insights from analytics data"""
        insights = []

        retention_rate = platform_analytics["user_adoption"]["retention_rate_percentage"]
        if retention_rate > 70:
            insights.append(
                f"Strong user retention at {retention_rate}% indicates high platform value"
            )
        elif retention_rate < 50:
            insights.append(
                f"Low retention rate of {retention_rate}% requires attention to user engagement"
            )

        accuracy = platform_analytics["prediction_accuracy"]["overall_accuracy_percentage"]
        if accuracy > 85:
            insights.append(
                f"Prediction accuracy of {accuracy}% exceeds target, building farmer trust"
            )
        elif accuracy < 80:
            insights.append(
                f"Prediction accuracy of {accuracy}% below target, model improvements needed"
            )

        top_crops = market_analytics["demand_patterns"]["top_demanded_crops"]
        if top_crops:
            top_crop = top_crops[0]["crop"]
            insights.append(
                f"Highest demand for {top_crop}, opportunity for targeted farmer recommendations"
            )

        most_used = platform_analytics["feature_usage"]["most_used_feature"]
        insights.append(f"Most used feature is {most_used}, indicating primary user value driver")

        return insights

    def _generate_recommendations(
        self, platform_analytics: Dict[str, Any], market_analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        retention_rate = platform_analytics["user_adoption"]["retention_rate_percentage"]
        if retention_rate < 60:
            recommendations.append(
                "Implement user engagement campaigns and feature tutorials to improve retention"
            )

        accuracy = platform_analytics["prediction_accuracy"]["overall_accuracy_percentage"]
        if accuracy < 85:
            recommendations.append(
                "Invest in model training with more regional data to improve prediction accuracy"
            )

        top_crops = market_analytics["demand_patterns"]["top_demanded_crops"]
        if top_crops and len(top_crops) > 0:
            high_demand_crops = [c["crop"] for c in top_crops[:3]]
            recommendations.append(
                f"Promote cultivation of high-demand crops: {', '.join(high_demand_crops)}"
            )

        buyer_interests = market_analytics["demand_patterns"]["total_buyer_interests"]
        strategies = platform_analytics["feature_usage"]["annual_strategies_created"]
        if buyer_interests < strategies * 0.5:
            recommendations.append(
                "Increase buyer outreach to match farmer supply with market demand"
            )

        recommendations.append(
            "Continue monitoring regional performance to identify best practices for replication"
        )

        return recommendations
