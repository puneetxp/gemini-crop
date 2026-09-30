"""
Livestock ROI Calculator Service
Calculates return on investment, break-even point, and profit projections for livestock

Features:
- ROI calculation based on purchase price, feed costs, healthcare, and revenue
- Break-even point analysis
- Projected annual profit calculations
- Species-specific cost and revenue models
- Integration with Amazon Bedrock for AI-powered insights
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LivestockROICalculator:
    """
    Calculate ROI, break-even point, and profit projections for livestock
    """

    # Average monthly costs per animal (in INR)
    MONTHLY_COSTS = {
        "cattle": {"feed": 3000, "healthcare": 500, "maintenance": 300},
        "buffalo": {"feed": 3500, "healthcare": 600, "maintenance": 350},
        "goat": {"feed": 800, "healthcare": 200, "maintenance": 100},
        "poultry": {"feed": 50, "healthcare": 20, "maintenance": 10},
    }

    # Average revenue per animal per month (in INR)
    MONTHLY_REVENUE = {
        "cattle": {
            "dairy": 6000,  # Milk production
            "meat": 0,  # One-time sale
            "breeding": 2000,  # Breeding fees
        },
        "buffalo": {"dairy": 8000, "meat": 0, "breeding": 2500},  # Higher milk production
        "goat": {"dairy": 1500, "meat": 0, "breeding": 800},
        "poultry": {"eggs": 150, "meat": 0, "breeding": 0},  # Egg production
    }

    def __init__(self):
        """Initialize ROI calculator"""
        pass

    def calculate_roi(
        self,
        species: str,
        purpose: str,
        purchase_price: float,
        current_age_months: int,
        total_investment: float,
        total_revenue: float,
        milk_production_liters_per_day: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive ROI metrics

        Args:
            species: Animal species (cattle, buffalo, goat, poultry)
            purpose: Purpose (dairy, meat, breeding, eggs)
            purchase_price: Initial purchase price
            current_age_months: Current age in months
            total_investment: Total investment including feed, healthcare
            total_revenue: Total revenue generated so far
            milk_production_liters_per_day: Daily milk production (for dairy)

        Returns:
            Dictionary with ROI metrics
        """
        species_lower = species.lower()
        purpose_lower = purpose.lower()

        # Calculate current ROI
        if total_investment > 0:
            current_roi_percentage = ((total_revenue - total_investment) / total_investment) * 100
        else:
            current_roi_percentage = 0

        # Calculate net profit/loss
        net_profit = total_revenue - total_investment

        # Check if break-even achieved
        break_even_achieved = total_revenue >= total_investment

        # Calculate break-even date (estimated)
        break_even_date = self._calculate_break_even_date(
            species_lower,
            purpose_lower,
            purchase_price,
            current_age_months,
            total_investment,
            total_revenue,
            milk_production_liters_per_day,
        )

        # Calculate projected annual profit
        projected_annual_profit = self._calculate_projected_annual_profit(
            species_lower, purpose_lower, current_age_months, milk_production_liters_per_day
        )

        # Calculate monthly cash flow
        monthly_costs = self._get_monthly_costs(species_lower)
        monthly_revenue = self._get_monthly_revenue(
            species_lower, purpose_lower, milk_production_liters_per_day
        )
        monthly_cash_flow = monthly_revenue - monthly_costs

        return {
            "current_roi_percentage": round(current_roi_percentage, 2),
            "net_profit": round(net_profit, 2),
            "break_even_achieved": break_even_achieved,
            "break_even_date": break_even_date,
            "projected_annual_profit": round(projected_annual_profit, 2),
            "monthly_costs": round(monthly_costs, 2),
            "monthly_revenue": round(monthly_revenue, 2),
            "monthly_cash_flow": round(monthly_cash_flow, 2),
            "payback_period_months": self._calculate_payback_period(
                total_investment, monthly_cash_flow
            ),
            "investment_summary": {
                "total_investment": round(total_investment, 2),
                "total_revenue": round(total_revenue, 2),
                "purchase_price": round(purchase_price, 2),
                "operating_costs": round(total_investment - purchase_price, 2),
            },
        }

    def _get_monthly_costs(self, species: str) -> float:
        """Get total monthly costs for species"""
        costs = self.MONTHLY_COSTS.get(species, self.MONTHLY_COSTS["cattle"])
        return sum(costs.values())

    def _get_monthly_revenue(
        self, species: str, purpose: str, milk_production_liters_per_day: Optional[float] = None
    ) -> float:
        """Get estimated monthly revenue"""
        revenue_data = self.MONTHLY_REVENUE.get(species, self.MONTHLY_REVENUE["cattle"])

        # For dairy animals, calculate based on actual milk production
        if purpose == "dairy" and milk_production_liters_per_day:
            # Average milk price: ₹40-50 per liter
            milk_price_per_liter = 45
            monthly_revenue = milk_production_liters_per_day * 30 * milk_price_per_liter
            return monthly_revenue

        # For eggs (poultry)
        if purpose == "eggs":
            return revenue_data.get("eggs", 0)

        # For breeding
        if purpose == "breeding":
            return revenue_data.get("breeding", 0)

        # Default to purpose-based revenue
        return revenue_data.get(purpose, 0)

    def _calculate_break_even_date(
        self,
        species: str,
        purpose: str,
        purchase_price: float,
        current_age_months: int,
        total_investment: float,
        total_revenue: float,
        milk_production_liters_per_day: Optional[float] = None,
    ) -> Optional[str]:
        """Calculate estimated break-even date"""
        # If already break-even, return current date
        if total_revenue >= total_investment:
            return datetime.now().strftime("%Y-%m-%d")

        # Calculate remaining amount to break even
        remaining_amount = total_investment - total_revenue

        # Calculate monthly cash flow
        monthly_costs = self._get_monthly_costs(species)
        monthly_revenue = self._get_monthly_revenue(
            species, purpose, milk_production_liters_per_day
        )
        monthly_cash_flow = monthly_revenue - monthly_costs

        # If negative cash flow, break-even not achievable
        if monthly_cash_flow <= 0:
            return None

        # Calculate months to break even
        months_to_break_even = remaining_amount / monthly_cash_flow

        # Calculate break-even date
        break_even_date = datetime.now() + timedelta(days=int(months_to_break_even * 30))

        return break_even_date.strftime("%Y-%m-%d")

    def _calculate_projected_annual_profit(
        self,
        species: str,
        purpose: str,
        current_age_months: int,
        milk_production_liters_per_day: Optional[float] = None,
    ) -> float:
        """Calculate projected annual profit"""
        monthly_costs = self._get_monthly_costs(species)
        monthly_revenue = self._get_monthly_revenue(
            species, purpose, milk_production_liters_per_day
        )

        monthly_profit = monthly_revenue - monthly_costs
        annual_profit = monthly_profit * 12

        # Adjust for age (younger animals may have lower productivity)
        if current_age_months < 24:  # Less than 2 years
            age_factor = 0.7  # 70% productivity
        elif current_age_months < 36:  # 2-3 years
            age_factor = 0.9  # 90% productivity
        else:
            age_factor = 1.0  # Full productivity

        return annual_profit * age_factor

    def _calculate_payback_period(
        self, total_investment: float, monthly_cash_flow: float
    ) -> Optional[int]:
        """Calculate payback period in months"""
        if monthly_cash_flow <= 0:
            return None

        payback_months = total_investment / monthly_cash_flow
        return int(payback_months)

    def calculate_projected_returns(
        self,
        species: str,
        purpose: str,
        purchase_price: float,
        current_age_months: int,
        milk_production_liters_per_day: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate projected returns over 1, 2, and 5 year periods

        Args:
            species: Animal species
            purpose: Purpose (dairy, meat, breeding, eggs)
            purchase_price: Initial purchase price
            current_age_months: Current age in months
            milk_production_liters_per_day: Daily milk production (for dairy)

        Returns:
            Dictionary with projected returns for different time periods
        """
        species_lower = species.lower()
        purpose_lower = purpose.lower()

        # Calculate monthly cash flow
        monthly_costs = self._get_monthly_costs(species_lower)
        monthly_revenue = self._get_monthly_revenue(
            species_lower, purpose_lower, milk_production_liters_per_day
        )
        monthly_profit = monthly_revenue - monthly_costs

        # Calculate age factors for different periods
        def get_age_factor(months_from_now: int) -> float:
            """Calculate productivity factor based on age"""
            future_age = current_age_months + months_from_now
            if future_age < 24:  # Less than 2 years
                return 0.7  # 70% productivity
            elif future_age < 36:  # 2-3 years
                return 0.9  # 90% productivity
            elif future_age < 96:  # 3-8 years (prime productive years)
                return 1.0  # Full productivity
            else:  # Older than 8 years
                return 0.8  # 80% productivity (declining)

        # Calculate 1-year projection
        one_year_profit = 0
        for month in range(12):
            age_factor = get_age_factor(month)
            one_year_profit += monthly_profit * age_factor

        # Calculate 2-year projection
        two_year_profit = 0
        for month in range(24):
            age_factor = get_age_factor(month)
            two_year_profit += monthly_profit * age_factor

        # Calculate 5-year projection
        five_year_profit = 0
        for month in range(60):
            age_factor = get_age_factor(month)
            five_year_profit += monthly_profit * age_factor

        # Calculate ROI percentages
        total_investment = purchase_price
        one_year_roi = (one_year_profit / total_investment) * 100 if total_investment > 0 else 0
        two_year_roi = (two_year_profit / total_investment) * 100 if total_investment > 0 else 0
        five_year_roi = (five_year_profit / total_investment) * 100 if total_investment > 0 else 0

        return {
            "one_year": {
                "profit": round(one_year_profit, 2),
                "roi_percentage": round(one_year_roi, 2),
                "total_revenue": round(one_year_profit + total_investment, 2),
                "confidence_interval": {
                    "lower": round(one_year_profit * 0.8, 2),  # ±20% confidence
                    "upper": round(one_year_profit * 1.2, 2),
                },
            },
            "two_year": {
                "profit": round(two_year_profit, 2),
                "roi_percentage": round(two_year_roi, 2),
                "total_revenue": round(two_year_profit + total_investment, 2),
                "confidence_interval": {
                    "lower": round(two_year_profit * 0.7, 2),  # ±30% confidence
                    "upper": round(two_year_profit * 1.3, 2),
                },
            },
            "five_year": {
                "profit": round(five_year_profit, 2),
                "roi_percentage": round(five_year_roi, 2),
                "total_revenue": round(five_year_profit + total_investment, 2),
                "confidence_interval": {
                    "lower": round(five_year_profit * 0.7, 2),  # ±30% confidence
                    "upper": round(five_year_profit * 1.3, 2),
                },
            },
        }

    def compare_livestock_options(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare ROI across different livestock options

        Args:
            options: List of livestock options with species, purpose, purchase_price, age

        Returns:
            Comparison analysis with rankings
        """
        comparisons = []

        for option in options:
            species = option.get("species", "cattle")
            purpose = option.get("purpose", "dairy")
            purchase_price = option.get("purchase_price", 50000)
            age_months = option.get("age_months", 24)
            milk_production = option.get("milk_production_liters_per_day")

            # Calculate projected returns
            projections = self.calculate_projected_returns(
                species=species,
                purpose=purpose,
                purchase_price=purchase_price,
                current_age_months=age_months,
                milk_production_liters_per_day=milk_production,
            )

            # Calculate break-even timeline
            monthly_costs = self._get_monthly_costs(species.lower())
            monthly_revenue = self._get_monthly_revenue(
                species.lower(), purpose.lower(), milk_production
            )
            monthly_cash_flow = monthly_revenue - monthly_costs

            break_even_months = None
            if monthly_cash_flow > 0:
                break_even_months = int(purchase_price / monthly_cash_flow)

            comparisons.append(
                {
                    "species": species,
                    "breed": option.get("breed", "Unknown"),
                    "purpose": purpose,
                    "purchase_price": purchase_price,
                    "age_months": age_months,
                    "break_even_months": break_even_months,
                    "one_year_roi": projections["one_year"]["roi_percentage"],
                    "two_year_roi": projections["two_year"]["roi_percentage"],
                    "five_year_roi": projections["five_year"]["roi_percentage"],
                    "one_year_profit": projections["one_year"]["profit"],
                    "five_year_profit": projections["five_year"]["profit"],
                    "monthly_cash_flow": round(monthly_cash_flow, 2),
                    "monthly_costs": round(monthly_costs, 2),
                    "monthly_revenue": round(monthly_revenue, 2),
                }
            )

        # Sort by 5-year ROI (best to worst)
        comparisons.sort(key=lambda x: x["five_year_roi"], reverse=True)

        # Add rankings
        for i, comparison in enumerate(comparisons):
            comparison["rank"] = i + 1

        # Generate recommendation
        best_option = comparisons[0] if comparisons else None
        recommendation = None
        if best_option:
            recommendation = (
                f"Best option: {best_option['species']} ({best_option['breed']}) for {best_option['purpose']} "
                f"with {best_option['five_year_roi']:.1f}% 5-year ROI and "
                f"₹{best_option['five_year_profit']:,.0f} projected profit over 5 years."
            )

        return {
            "comparisons": comparisons,
            "best_option": best_option,
            "recommendation": recommendation,
            "total_options_compared": len(comparisons),
        }

    def generate_roi_report(
        self, livestock_data: Dict[str, Any], roi_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive ROI report

        Args:
            livestock_data: Livestock information
            roi_metrics: Calculated ROI metrics

        Returns:
            Formatted ROI report
        """
        species = livestock_data.get("species", "Unknown")
        breed = livestock_data.get("breed", "Unknown")
        purpose = livestock_data.get("purpose", "Unknown")
        purchase_price = livestock_data.get("purchase_price", 0)
        current_age_months = livestock_data.get("current_age_months", 0)
        milk_production = livestock_data.get("milk_production_liters_per_day")

        # Calculate projected returns for 1, 2, and 5 years
        projected_returns = self.calculate_projected_returns(
            species=species,
            purpose=purpose,
            purchase_price=purchase_price,
            current_age_months=current_age_months,
            milk_production_liters_per_day=milk_production,
        )

        report = {
            "livestock_info": {
                "species": species,
                "breed": breed,
                "purpose": purpose,
                "age_months": current_age_months,
            },
            "financial_summary": {
                "total_investment": roi_metrics["investment_summary"]["total_investment"],
                "total_revenue": roi_metrics["investment_summary"]["total_revenue"],
                "net_profit": roi_metrics["net_profit"],
                "roi_percentage": roi_metrics["current_roi_percentage"],
            },
            "break_even_analysis": {
                "achieved": roi_metrics["break_even_achieved"],
                "date": roi_metrics["break_even_date"],
                "payback_period_months": roi_metrics["payback_period_months"],
                "days_to_break_even": (
                    roi_metrics["payback_period_months"] * 30
                    if roi_metrics["payback_period_months"]
                    else None
                ),
            },
            "cash_flow": {
                "monthly_costs": roi_metrics["monthly_costs"],
                "monthly_revenue": roi_metrics["monthly_revenue"],
                "monthly_profit": roi_metrics["monthly_cash_flow"],
            },
            "projected_returns": projected_returns,
            "investment_vs_return": {
                "initial_investment": purchase_price,
                "one_year_return": projected_returns["one_year"]["total_revenue"],
                "two_year_return": projected_returns["two_year"]["total_revenue"],
                "five_year_return": projected_returns["five_year"]["total_revenue"],
                "one_year_roi_percentage": projected_returns["one_year"]["roi_percentage"],
                "two_year_roi_percentage": projected_returns["two_year"]["roi_percentage"],
                "five_year_roi_percentage": projected_returns["five_year"]["roi_percentage"],
            },
            "recommendations": self._generate_recommendations(roi_metrics, livestock_data),
        }

        return report

    def _generate_recommendations(
        self, roi_metrics: Dict[str, Any], livestock_data: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on ROI analysis"""
        recommendations = []

        # ROI-based recommendations
        if roi_metrics["current_roi_percentage"] < 0:
            recommendations.append(
                "Current ROI is negative. Consider optimizing feed costs and improving productivity."
            )
        elif roi_metrics["current_roi_percentage"] < 20:
            recommendations.append(
                "ROI is below target. Focus on increasing revenue through better breeding or milk production."
            )
        else:
            recommendations.append("Excellent ROI! Consider expanding your livestock portfolio.")

        # Break-even recommendations
        if not roi_metrics["break_even_achieved"]:
            if roi_metrics["payback_period_months"]:
                recommendations.append(
                    f"Expected to break even in {roi_metrics['payback_period_months']} months. "
                    "Maintain consistent care and feeding schedule."
                )
            else:
                recommendations.append(
                    "Break-even not achievable with current revenue. Consider changing purpose or improving productivity."
                )

        # Cash flow recommendations
        if roi_metrics["monthly_cash_flow"] < 0:
            recommendations.append("Negative monthly cash flow. Review and reduce operating costs.")

        # Age-based recommendations
        age_months = livestock_data.get("current_age_months", 0)
        if age_months < 12:
            recommendations.append(
                "Young animal with growth potential. Invest in proper nutrition for better future returns."
            )
        elif age_months > 60:
            recommendations.append(
                "Mature animal. Consider breeding or sale timing for optimal returns."
            )

        return recommendations


# Singleton instance
_roi_calculator = None


def get_roi_calculator() -> LivestockROICalculator:
    """Get ROI calculator singleton instance"""
    global _roi_calculator
    if _roi_calculator is None:
        _roi_calculator = LivestockROICalculator()
    return _roi_calculator
