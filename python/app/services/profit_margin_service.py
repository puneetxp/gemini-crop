"""
Profit Margin Calculation Service
Calculates profit margins for crop recommendations based on costs, revenue, and market data
"""

import logging
from decimal import Decimal
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as Session
from typing import Dict, List, Optional

from app.services.farm_access import fetch_all, fetch_one
from app.services.market_data_service import _CMD_VIEW, _where

logger = logging.getLogger(__name__)


class ProfitMarginService:
    """Service for calculating profit margins for crop recommendations"""

    def __init__(self, db: Session):
        """
        Initialize profit margin service

        Args:
            db: Database session
        """
        self.db = db

    def calculate_profit_margin(
        self,
        crop_type: str,
        state: str,
        district: Optional[str] = None,
        season: Optional[str] = None,
        area_acres: float = 1.0,
        custom_costs: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive profit margin for a crop

        Profit Margin = (Revenue - Total Costs) / Revenue * 100

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)
            season: Season (kharif, rabi, zaid) (optional)
            area_acres: Farm area in acres (default: 1.0)
            custom_costs: Custom cost overrides (optional)

        Returns:
            Dictionary with profit margin analysis
        """
        try:
            logger.info(f"Calculating profit margin for {crop_type} in {state}, {district}")

            # Get historical profitability data
            profitability_data = self._get_profitability_data(
                crop_type=crop_type, state=state, district=district, season=season
            )

            # Get market price data
            market_data = self._get_market_price_data(
                crop_type=crop_type, state=state, district=district, season=season
            )

            # Get yield data
            yield_data = self._get_yield_data(
                crop_type=crop_type, state=state, district=district, season=season
            )

            # Calculate costs
            costs = self._calculate_total_costs(
                profitability_data=profitability_data,
                custom_costs=custom_costs,
                area_acres=area_acres,
            )

            # Calculate revenue
            revenue = self._calculate_revenue(
                market_data=market_data, yield_data=yield_data, area_acres=area_acres
            )

            # Calculate profit margin
            profit_margin_result = self._calculate_margin_metrics(
                revenue=revenue, costs=costs, area_acres=area_acres
            )

            # Compile comprehensive result
            result = {
                "crop_type": crop_type,
                "location": {"state": state, "district": district, "season": season},
                "area_acres": area_acres,
                "costs": costs,
                "revenue": revenue,
                "profit_margin": profit_margin_result,
                "data_sources": {
                    "has_profitability_data": profitability_data is not None,
                    "has_market_data": market_data is not None,
                    "has_yield_data": yield_data is not None,
                },
                "recommendations": self._generate_margin_recommendations(
                    profit_margin_result=profit_margin_result, costs=costs, revenue=revenue
                ),
            }

            logger.info(
                f"Profit margin calculated: {profit_margin_result['profit_margin_percentage']:.2f}%"
            )
            return result

        except Exception as e:
            logger.error(f"Error calculating profit margin: {e}")
            raise

    def calculate_comparative_margins(
        self,
        crops: List[str],
        state: str,
        district: Optional[str] = None,
        season: Optional[str] = None,
        area_acres: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Calculate and compare profit margins for multiple crops

        Args:
            crops: List of crop types to compare
            state: State name
            district: District name (optional)
            season: Season (optional)
            area_acres: Farm area in acres

        Returns:
            Comparative profit margin analysis
        """
        try:
            logger.info(f"Calculating comparative margins for {len(crops)} crops in {state}")

            crop_margins = []

            for crop_type in crops:
                try:
                    margin_data = self.calculate_profit_margin(
                        crop_type=crop_type,
                        state=state,
                        district=district,
                        season=season,
                        area_acres=area_acres,
                    )
                    crop_margins.append(margin_data)
                except Exception as e:
                    logger.warning(f"Could not calculate margin for {crop_type}: {e}")
                    continue

            if not crop_margins:
                return {
                    "error": "No profit margin data available for specified crops",
                    "crops": crops,
                    "location": {"state": state, "district": district},
                }

            # Sort by profit margin percentage
            crop_margins.sort(
                key=lambda x: x["profit_margin"]["profit_margin_percentage"], reverse=True
            )

            # Generate comparison insights
            comparison = {
                "location": {"state": state, "district": district, "season": season},
                "area_acres": area_acres,
                "crops_analyzed": len(crop_margins),
                "crop_margins": crop_margins,
                "best_margin": {
                    "crop": crop_margins[0]["crop_type"],
                    "margin_percentage": crop_margins[0]["profit_margin"][
                        "profit_margin_percentage"
                    ],
                    "net_profit": crop_margins[0]["profit_margin"]["net_profit"],
                },
                "worst_margin": {
                    "crop": crop_margins[-1]["crop_type"],
                    "margin_percentage": crop_margins[-1]["profit_margin"][
                        "profit_margin_percentage"
                    ],
                    "net_profit": crop_margins[-1]["profit_margin"]["net_profit"],
                },
                "average_margin": sum(
                    c["profit_margin"]["profit_margin_percentage"] for c in crop_margins
                )
                / len(crop_margins),
                "comparison_insights": self._generate_comparison_insights(crop_margins),
            }

            return comparison

        except Exception as e:
            logger.error(f"Error calculating comparative margins: {e}")
            raise

    def _get_profitability_data(
        self, crop_type: str, state: str, district: Optional[str], season: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get historical profitability data for a crop"""
        try:
            where, bind = _where(
                {"crop_type": crop_type, "state": state, "district": district, "season": season}
            )
            # Get most recent data
            result = fetch_one(
                f"SELECT * FROM crop_profitability{where} ORDER BY year DESC NULLS LAST, id DESC LIMIT 1",
                bind,
            )

            if not result:
                return None

            return {
                "avg_profit_per_acre": (
                    float(result.avg_profit_per_acre) if result.avg_profit_per_acre else 0
                ),
                "seed_cost": float(result.seed_cost) if result.seed_cost else 0,
                "fertilizer_cost": float(result.fertilizer_cost) if result.fertilizer_cost else 0,
                "pesticide_cost": float(result.pesticide_cost) if result.pesticide_cost else 0,
                "labor_cost": float(result.labor_cost) if result.labor_cost else 0,
                "irrigation_cost": float(result.irrigation_cost) if result.irrigation_cost else 0,
                "equipment_cost": float(result.equipment_cost) if result.equipment_cost else 0,
                "other_costs": float(result.other_costs) if result.other_costs else 0,
                "total_investment_cost": (
                    float(result.total_investment_cost) if result.total_investment_cost else 0
                ),
                "avg_revenue_per_acre": (
                    float(result.avg_revenue_per_acre) if result.avg_revenue_per_acre else 0
                ),
                "profit_margin": float(result.profit_margin) if result.profit_margin else 0,
                "roi_percentage": float(result.roi_percentage) if result.roi_percentage else 0,
            }

        except Exception as e:
            logger.error(f"Error getting profitability data: {e}")
            return None

    def _get_market_price_data(
        self, crop_type: str, state: str, district: Optional[str], season: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get market price data for a crop"""
        try:
            where, bind = _where(
                {"crop_type": crop_type, "state": state, "district": district, "season": season}
            )
            # Get average price from recent data
            result = fetch_all(f"SELECT * FROM {_CMD_VIEW}{where} ORDER BY date DESC LIMIT 5", bind)

            if not result:
                return None

            avg_price = sum(float(r.avg_price_per_quintal) for r in result) / len(result)

            return {"avg_price_per_quintal": avg_price, "data_points": len(result)}

        except Exception as e:
            logger.error(f"Error getting market price data: {e}")
            return None

    def _get_yield_data(
        self, crop_type: str, state: str, district: Optional[str], season: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get yield data for a crop"""
        try:
            where, bind = _where(
                {"crop_type": crop_type, "state": state, "district": district, "season": season}
            )
            # Get average yield from recent data
            result = fetch_all(
                f"SELECT * FROM historical_yields{where} ORDER BY year DESC NULLS LAST, id DESC LIMIT 5",
                bind,
            )

            if not result:
                return None

            avg_yield = sum(float(r.avg_yield_per_acre) for r in result) / len(result)

            return {"avg_yield_per_acre": avg_yield, "data_points": len(result)}

        except Exception as e:
            logger.error(f"Error getting yield data: {e}")
            return None

    def _calculate_total_costs(
        self,
        profitability_data: Optional[Dict[str, Any]],
        custom_costs: Optional[Dict[str, float]],
        area_acres: float,
    ) -> Dict[str, Any]:
        """Calculate total costs with custom overrides"""

        # Default costs if no data available
        default_costs = {
            "seed_cost": 0,
            "fertilizer_cost": 0,
            "pesticide_cost": 0,
            "labor_cost": 0,
            "irrigation_cost": 0,
            "equipment_cost": 0,
            "other_costs": 0,
        }

        # Use profitability data if available
        if profitability_data:
            costs = {
                "seed_cost": profitability_data.get("seed_cost", 0),
                "fertilizer_cost": profitability_data.get("fertilizer_cost", 0),
                "pesticide_cost": profitability_data.get("pesticide_cost", 0),
                "labor_cost": profitability_data.get("labor_cost", 0),
                "irrigation_cost": profitability_data.get("irrigation_cost", 0),
                "equipment_cost": profitability_data.get("equipment_cost", 0),
                "other_costs": profitability_data.get("other_costs", 0),
            }
        else:
            costs = default_costs.copy()

        # Apply custom cost overrides
        if custom_costs:
            for key, value in custom_costs.items():
                if key in costs:
                    costs[key] = value

        # Calculate per acre costs
        cost_per_acre = sum(costs.values())

        # Calculate total costs for area
        total_costs = cost_per_acre * area_acres

        return {
            "per_acre": {**costs, "total_cost_per_acre": cost_per_acre},
            "total_area": {
                "seed_cost": costs["seed_cost"] * area_acres,
                "fertilizer_cost": costs["fertilizer_cost"] * area_acres,
                "pesticide_cost": costs["pesticide_cost"] * area_acres,
                "labor_cost": costs["labor_cost"] * area_acres,
                "irrigation_cost": costs["irrigation_cost"] * area_acres,
                "equipment_cost": costs["equipment_cost"] * area_acres,
                "other_costs": costs["other_costs"] * area_acres,
                "total_costs": total_costs,
            },
        }

    def _calculate_revenue(
        self,
        market_data: Optional[Dict[str, Any]],
        yield_data: Optional[Dict[str, Any]],
        area_acres: float,
    ) -> Dict[str, Any]:
        """Calculate revenue based on yield and market price"""

        # Default values if no data
        avg_yield_per_acre = 20.0  # quintals per acre (conservative estimate)
        avg_price_per_quintal = 2000.0  # rupees per quintal (conservative)

        if yield_data:
            avg_yield_per_acre = yield_data.get("avg_yield_per_acre", avg_yield_per_acre)

        if market_data:
            avg_price_per_quintal = market_data.get("avg_price_per_quintal", avg_price_per_quintal)

        # Calculate revenue
        revenue_per_acre = avg_yield_per_acre * avg_price_per_quintal
        total_revenue = revenue_per_acre * area_acres
        total_yield = avg_yield_per_acre * area_acres

        return {
            "per_acre": {
                "yield_quintals": avg_yield_per_acre,
                "price_per_quintal": avg_price_per_quintal,
                "revenue_per_acre": revenue_per_acre,
            },
            "total_area": {"total_yield_quintals": total_yield, "total_revenue": total_revenue},
        }

    def _calculate_margin_metrics(
        self, revenue: Dict[str, Any], costs: Dict[str, Any], area_acres: float
    ) -> Dict[str, Any]:
        """Calculate profit margin and related metrics"""

        total_revenue = revenue["total_area"]["total_revenue"]
        total_costs = costs["total_area"]["total_costs"]

        # Calculate net profit
        net_profit = total_revenue - total_costs
        net_profit_per_acre = net_profit / area_acres if area_acres > 0 else 0

        # Calculate profit margin percentage
        # Profit Margin = (Net Profit / Revenue) * 100
        profit_margin_percentage = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Calculate ROI
        # ROI = (Net Profit / Total Investment) * 100
        roi_percentage = (net_profit / total_costs * 100) if total_costs > 0 else 0

        # Calculate break-even yield
        # Break-even yield = Total Costs / Price per quintal
        price_per_quintal = revenue["per_acre"]["price_per_quintal"]
        break_even_yield_total = total_costs / price_per_quintal if price_per_quintal > 0 else 0
        break_even_yield_per_acre = break_even_yield_total / area_acres if area_acres > 0 else 0

        # Determine profitability status
        if profit_margin_percentage > 50:
            status = "highly_profitable"
        elif profit_margin_percentage > 30:
            status = "profitable"
        elif profit_margin_percentage > 10:
            status = "moderately_profitable"
        elif profit_margin_percentage > 0:
            status = "marginally_profitable"
        else:
            status = "unprofitable"

        return {
            "net_profit": round(net_profit, 2),
            "net_profit_per_acre": round(net_profit_per_acre, 2),
            "profit_margin_percentage": round(profit_margin_percentage, 2),
            "roi_percentage": round(roi_percentage, 2),
            "break_even_yield_quintals": round(break_even_yield_total, 2),
            "break_even_yield_per_acre": round(break_even_yield_per_acre, 2),
            "profitability_status": status,
            "metrics_explanation": {
                "profit_margin": "Percentage of revenue that becomes profit",
                "roi": "Return on investment - profit as percentage of costs",
                "break_even_yield": "Minimum yield needed to cover all costs",
            },
        }

    def _generate_margin_recommendations(
        self, profit_margin_result: Dict[str, Any], costs: Dict[str, Any], revenue: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on profit margin analysis"""

        recommendations = []

        margin_pct = profit_margin_result["profit_margin_percentage"]
        status = profit_margin_result["profitability_status"]

        # Status-based recommendations
        if status == "highly_profitable":
            recommendations.append(
                f"Excellent profit margin of {margin_pct:.1f}%. "
                "This crop is highly recommended for your location."
            )
        elif status == "profitable":
            recommendations.append(
                f"Good profit margin of {margin_pct:.1f}%. "
                "This crop should provide solid returns."
            )
        elif status == "moderately_profitable":
            recommendations.append(
                f"Moderate profit margin of {margin_pct:.1f}%. "
                "Consider cost optimization strategies to improve profitability."
            )
        elif status == "marginally_profitable":
            recommendations.append(
                f"Low profit margin of {margin_pct:.1f}%. "
                "Carefully evaluate if this crop is worth the investment."
            )
        else:
            recommendations.append(
                f"Negative profit margin of {margin_pct:.1f}%. "
                "This crop may result in losses. Consider alternatives."
            )

        # Cost optimization recommendations
        cost_per_acre = costs["per_acre"]["total_cost_per_acre"]
        revenue_per_acre = revenue["per_acre"]["revenue_per_acre"]

        if cost_per_acre > revenue_per_acre * 0.7:
            recommendations.append(
                "High cost-to-revenue ratio. Focus on reducing input costs, "
                "especially fertilizer and labor expenses."
            )

        # ROI recommendations
        roi = profit_margin_result["roi_percentage"]
        if roi < 50:
            recommendations.append(
                f"ROI of {roi:.1f}% is below optimal. "
                "Consider crops with higher return potential or reduce investment costs."
            )
        elif roi > 100:
            recommendations.append(
                f"Excellent ROI of {roi:.1f}%. "
                "This crop offers strong returns on your investment."
            )

        return recommendations

    def _generate_comparison_insights(self, crop_margins: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from comparative margin analysis"""

        insights = []

        if len(crop_margins) < 2:
            return insights

        best = crop_margins[0]
        worst = crop_margins[-1]

        margin_diff = (
            best["profit_margin"]["profit_margin_percentage"]
            - worst["profit_margin"]["profit_margin_percentage"]
        )

        insights.append(
            f"{best['crop_type']} has the highest profit margin at "
            f"{best['profit_margin']['profit_margin_percentage']:.1f}%, "
            f"which is {margin_diff:.1f}% higher than {worst['crop_type']}."
        )

        profit_diff = best["profit_margin"]["net_profit"] - worst["profit_margin"]["net_profit"]

        insights.append(
            f"Choosing {best['crop_type']} over {worst['crop_type']} could result in "
            f"₹{abs(profit_diff):,.0f} additional profit."
        )

        # Find crops with best ROI
        best_roi_crop = max(crop_margins, key=lambda x: x["profit_margin"]["roi_percentage"])

        if best_roi_crop["crop_type"] != best["crop_type"]:
            insights.append(
                f"{best_roi_crop['crop_type']} offers the best ROI at "
                f"{best_roi_crop['profit_margin']['roi_percentage']:.1f}%, "
                "making it ideal for farmers with limited capital."
            )

        return insights
