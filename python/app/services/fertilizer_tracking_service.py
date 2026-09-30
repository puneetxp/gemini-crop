"""
Fertilizer Tracking Service

This service handles:
- Recording fertilizer applications over time
- Monitoring soil response to fertilizer applications
- Analyzing fertilizer effectiveness with ROI calculations
- Generating usage reports with cost analysis and recommendations

Validates: Requirements AC9 (Phase 6 - Required)
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.core.db import DB
from app.services.farm_access import (
    Row,
    crop_for_user,
    farm_for_user,
    fetch_all,
    fetch_one,
    plot_for_user,
    soil_test_for_user,
)

# Data access is raw SQL through app.core.db.DB (app/orm classes are not SQLAlchemy models).
# Rows come back as farm_access.Row (dict with attribute access), so `FertilizerApplication` is an alias.
FertilizerApplication = Row
AsyncSession = Any  # kept for the constructor signature; queries don't use it

APP_COLUMNS = (
    "farm_id",
    "plot_id",
    "crop_id",
    "application_date",
    "fertilizer_type",
    "category",
    "quantity_kg",
    "quantity_per_hectare",
    "area_applied_hectares",
    "nitrogen_kg",
    "phosphorus_kg",
    "potassium_kg",
    "cost_total",
    "cost_per_kg",
    "cost_per_hectare",
    "application_method",
    "growth_stage",
    "days_after_planting",
    "soil_test_before_id",
    "weather_conditions",
    "temperature_celsius",
    "rainfall_mm_24h",
    "recommended_by",
    "recommendation_id",
    "notes",
)


class FertilizerTrackingService:
    """Service for tracking fertilizer applications and analyzing effectiveness"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_application(
        self,
        farm_id: int,
        application_date: datetime,
        fertilizer_type: str,
        category: str,
        quantity_kg: float,
        cost_total: float,
        plot_id: Optional[int] = None,
        crop_id: Optional[int] = None,
        area_applied_hectares: Optional[float] = None,
        nitrogen_kg: Optional[float] = None,
        phosphorus_kg: Optional[float] = None,
        potassium_kg: Optional[float] = None,
        application_method: Optional[str] = None,
        growth_stage: Optional[str] = None,
        days_after_planting: Optional[int] = None,
        soil_test_before_id: Optional[int] = None,
        weather_conditions: Optional[str] = None,
        temperature_celsius: Optional[float] = None,
        rainfall_mm_24h: Optional[float] = None,
        recommended_by: Optional[str] = None,
        recommendation_id: Optional[str] = None,
        notes: Optional[str] = None,
        user=None,
    ) -> FertilizerApplication:
        """
        Record a fertilizer application with all details

        Args:
            farm_id: Farm where fertilizer was applied
            application_date: Date of application
            fertilizer_type: Type of fertilizer (urea, dap, vermicompost, etc.)
            category: organic or chemical
            quantity_kg: Total quantity applied in kg
            cost_total: Total cost in ₹
            plot_id: Optional specific plot
            crop_id: Optional associated crop
            area_applied_hectares: Area where applied
            nitrogen_kg: Nitrogen content provided
            phosphorus_kg: Phosphorus content provided
            potassium_kg: Potassium content provided
            application_method: broadcast, banding, foliar, etc.
            growth_stage: basal, vegetative, flowering, etc.
            days_after_planting: Days after crop planting
            soil_test_before_id: Soil test before application
            weather_conditions: Weather during application
            temperature_celsius: Temperature during application
            rainfall_mm_24h: Rainfall within 24h after application
            recommended_by: system, agronomist, farmer
            recommendation_id: Reference to recommendation
            notes: Additional notes

        Returns:
            Created FertilizerApplication record
        """
        # Calculate derived metrics
        cost_per_kg = cost_total / quantity_kg if quantity_kg > 0 else 0

        quantity_per_hectare = None
        cost_per_hectare = None
        if area_applied_hectares and area_applied_hectares > 0:
            quantity_per_hectare = quantity_kg / area_applied_hectares
            cost_per_hectare = cost_total / area_applied_hectares

        # Owner checks: the farm must belong to the user; plot / crop / soil test must be on that farm.
        farm_for_user(farm_id, user)
        if plot_id is not None and plot_for_user(plot_id, user)["farm_id"] != farm_id:
            raise ValueError(f"Plot {plot_id} is not on farm {farm_id}")
        if crop_id is not None and crop_for_user(crop_id, user)["farm_id"] != farm_id:
            raise ValueError(f"Crop {crop_id} is not on farm {farm_id}")
        if (
            soil_test_before_id is not None
            and soil_test_for_user(soil_test_before_id, user)["farm_id"] != farm_id
        ):
            raise ValueError(f"Soil test {soil_test_before_id} is not for farm {farm_id}")

        values = {
            "farm_id": farm_id,
            "plot_id": plot_id,
            "crop_id": crop_id,
            "application_date": application_date,
            "fertilizer_type": fertilizer_type,
            "category": category,
            "quantity_kg": quantity_kg,
            "quantity_per_hectare": quantity_per_hectare,
            "area_applied_hectares": area_applied_hectares,
            "nitrogen_kg": nitrogen_kg,
            "phosphorus_kg": phosphorus_kg,
            "potassium_kg": potassium_kg,
            "cost_total": cost_total,
            "cost_per_kg": cost_per_kg,
            "cost_per_hectare": cost_per_hectare,
            "application_method": application_method,
            "growth_stage": growth_stage,
            "days_after_planting": days_after_planting,
            "soil_test_before_id": soil_test_before_id,
            "weather_conditions": weather_conditions,
            "temperature_celsius": temperature_celsius,
            "rainfall_mm_24h": rainfall_mm_24h,
            "recommended_by": recommended_by,
            "recommendation_id": recommendation_id,
            "notes": notes,
        }
        application = fetch_one(
            f"INSERT INTO fertilizer_applications ({', '.join(APP_COLUMNS)}) "
            f"VALUES ({', '.join('?' for _ in APP_COLUMNS)}) RETURNING *",
            [values[c] for c in APP_COLUMNS],
        )
        return application

    async def update_soil_response(
        self,
        application_id: int,
        soil_test_after_id: int,
        soil_response_notes: Optional[str] = None,
        user=None,
    ) -> FertilizerApplication:
        """
        Update fertilizer application with soil test results after application
        and calculate effectiveness score

        Args:
            application_id: Fertilizer application ID
            soil_test_after_id: Soil test conducted after application
            soil_response_notes: Observed soil response and crop performance

        Returns:
            Updated FertilizerApplication with effectiveness score
        """
        # Get application
        application = fetch_one(
            "SELECT * FROM fertilizer_applications WHERE id = ?", [application_id]
        )
        if not application:
            raise ValueError(f"Fertilizer application {application_id} not found")
        try:
            farm_for_user(application.farm_id, user)
            after_test = soil_test_for_user(soil_test_after_id, user)
        except LookupError as e:
            # Router maps ValueError -> 404; don't reveal other users' applications / tests.
            raise ValueError(str(e))
        if after_test["farm_id"] != application.farm_id:
            raise ValueError(f"Soil test {soil_test_after_id} not found for this farm")

        # Update with after soil test
        application.soil_test_after_id = soil_test_after_id
        application.soil_response_notes = soil_response_notes

        # Calculate effectiveness score if we have before and after tests
        if application.soil_test_before_id:
            effectiveness_score = await self._calculate_effectiveness_score(
                application.soil_test_before_id, soil_test_after_id, application
            )
            application.effectiveness_score = Decimal(str(effectiveness_score))

        application = fetch_one(
            """UPDATE fertilizer_applications SET soil_test_after_id = ?, soil_response_notes = ?,
               effectiveness_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? RETURNING *""",
            [
                soil_test_after_id,
                soil_response_notes,
                application.get("effectiveness_score"),
                application_id,
            ],
        )

        return application

    async def _calculate_effectiveness_score(
        self, before_test_id: int, after_test_id: int, application: FertilizerApplication
    ) -> float:
        """
        Calculate effectiveness score (0-100) based on soil nutrient improvements

        Scoring factors:
        - Nitrogen improvement: 30%
        - Phosphorus improvement: 30%
        - Potassium improvement: 30%
        - Soil health score improvement: 10%

        Args:
            before_test_id: Soil test before application
            after_test_id: Soil test after application
            application: Fertilizer application record

        Returns:
            Effectiveness score (0-100)
        """
        # Get before and after soil tests
        before = fetch_one("SELECT * FROM soil_test_results WHERE id = ?", [before_test_id])
        after = fetch_one("SELECT * FROM soil_test_results WHERE id = ?", [after_test_id])

        if not before or not after:
            return 0.0

        score = 0.0

        # Nitrogen improvement (30 points)
        if before.nitrogen_kg_per_ha and after.nitrogen_kg_per_ha:
            n_improvement = float(after.nitrogen_kg_per_ha - before.nitrogen_kg_per_ha)
            n_applied = float(application.nitrogen_kg) if application.nitrogen_kg else 0
            if n_applied > 0:
                # Score based on nutrient retention (ideal: 70-80% retained)
                retention_rate = (n_improvement / n_applied) * 100
                if 70 <= retention_rate <= 80:
                    score += 30
                elif 50 <= retention_rate < 70 or 80 < retention_rate <= 90:
                    score += 20
                elif retention_rate >= 40:
                    score += 10

        # Phosphorus improvement (30 points)
        if before.phosphorus_kg_per_ha and after.phosphorus_kg_per_ha:
            p_improvement = float(after.phosphorus_kg_per_ha - before.phosphorus_kg_per_ha)
            p_applied = float(application.phosphorus_kg) if application.phosphorus_kg else 0
            if p_applied > 0:
                retention_rate = (p_improvement / p_applied) * 100
                if 70 <= retention_rate <= 80:
                    score += 30
                elif 50 <= retention_rate < 70 or 80 < retention_rate <= 90:
                    score += 20
                elif retention_rate >= 40:
                    score += 10

        # Potassium improvement (30 points)
        if before.potassium_kg_per_ha and after.potassium_kg_per_ha:
            k_improvement = float(after.potassium_kg_per_ha - before.potassium_kg_per_ha)
            k_applied = float(application.potassium_kg) if application.potassium_kg else 0
            if k_applied > 0:
                retention_rate = (k_improvement / k_applied) * 100
                if 70 <= retention_rate <= 80:
                    score += 30
                elif 50 <= retention_rate < 70 or 80 < retention_rate <= 90:
                    score += 20
                elif retention_rate >= 40:
                    score += 10

        # Soil health score improvement (10 points)
        if before.soil_health_score and after.soil_health_score:
            health_improvement = float(after.soil_health_score - before.soil_health_score)
            if health_improvement >= 5:
                score += 10
            elif health_improvement >= 3:
                score += 7
            elif health_improvement >= 1:
                score += 5

        return min(score, 100.0)

    async def get_application_history(
        self,
        farm_id: int,
        plot_id: Optional[int] = None,
        crop_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        fertilizer_type: Optional[str] = None,
        category: Optional[str] = None,
        user=None,
    ) -> List[FertilizerApplication]:
        """
        Get fertilizer application history with filters

        Args:
            farm_id: Farm ID
            plot_id: Optional plot filter
            crop_id: Optional crop filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            fertilizer_type: Optional fertilizer type filter
            category: Optional category filter (organic/chemical)

        Returns:
            List of fertilizer applications
        """
        farm_for_user(farm_id, user)
        where, bind = ["farm_id = ?"], [farm_id]
        for col, op, val in (
            ("plot_id", "=", plot_id),
            ("crop_id", "=", crop_id),
            ("application_date", ">=", start_date),
            ("application_date", "<=", end_date),
            ("fertilizer_type", "=", fertilizer_type),
            ("category", "=", category),
        ):
            if val:
                where.append(f"{col} {op} ?")
                bind.append(val)
        return fetch_all(
            f"SELECT * FROM fertilizer_applications WHERE {' AND '.join(where)} ORDER BY application_date DESC",
            bind,
        )

    async def analyze_fertilizer_effectiveness(
        self,
        farm_id: int,
        plot_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user=None,
    ) -> Dict[str, Any]:
        """
        Analyze fertilizer effectiveness with ROI calculations

        Args:
            farm_id: Farm ID
            plot_id: Optional plot filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Effectiveness analysis with ROI metrics
        """
        applications = await self.get_application_history(
            farm_id=farm_id,
            plot_id=plot_id,
            start_date=start_date,
            end_date=end_date,
            user=user,
        )

        if not applications:
            return {
                "total_applications": 0,
                "total_cost": 0,
                "average_effectiveness": 0,
                "roi_analysis": {},
                "recommendations": [],
            }

        # Calculate aggregate metrics
        total_cost = sum(float(app.cost_total) for app in applications)
        total_quantity = sum(float(app.quantity_kg) for app in applications)

        # Calculate average effectiveness for applications with scores
        apps_with_scores = [app for app in applications if app.effectiveness_score]
        avg_effectiveness = (
            sum(float(app.effectiveness_score) for app in apps_with_scores) / len(apps_with_scores)
            if apps_with_scores
            else 0
        )

        # Analyze by fertilizer type
        type_analysis = {}
        for app in applications:
            ftype = app.fertilizer_type
            if ftype not in type_analysis:
                type_analysis[ftype] = {
                    "count": 0,
                    "total_cost": 0,
                    "total_quantity": 0,
                    "effectiveness_scores": [],
                }

            type_analysis[ftype]["count"] += 1
            type_analysis[ftype]["total_cost"] += float(app.cost_total)
            type_analysis[ftype]["total_quantity"] += float(app.quantity_kg)
            if app.effectiveness_score:
                type_analysis[ftype]["effectiveness_scores"].append(float(app.effectiveness_score))

        # Calculate averages and ROI for each type
        for ftype, data in type_analysis.items():
            data["avg_cost_per_kg"] = (
                data["total_cost"] / data["total_quantity"] if data["total_quantity"] > 0 else 0
            )
            data["avg_effectiveness"] = (
                sum(data["effectiveness_scores"]) / len(data["effectiveness_scores"])
                if data["effectiveness_scores"]
                else 0
            )
            # ROI = (effectiveness / cost) * 100 - simplified metric
            data["roi_score"] = (
                (data["avg_effectiveness"] / data["avg_cost_per_kg"])
                if data["avg_cost_per_kg"] > 0
                else 0
            )

        # Analyze by category (organic vs chemical)
        category_analysis = {}
        for app in applications:
            cat = app.category
            if cat not in category_analysis:
                category_analysis[cat] = {"count": 0, "total_cost": 0, "effectiveness_scores": []}

            category_analysis[cat]["count"] += 1
            category_analysis[cat]["total_cost"] += float(app.cost_total)
            if app.effectiveness_score:
                category_analysis[cat]["effectiveness_scores"].append(
                    float(app.effectiveness_score)
                )

        for cat, data in category_analysis.items():
            data["avg_effectiveness"] = (
                sum(data["effectiveness_scores"]) / len(data["effectiveness_scores"])
                if data["effectiveness_scores"]
                else 0
            )

        # Generate recommendations
        recommendations = self._generate_effectiveness_recommendations(
            type_analysis, category_analysis, avg_effectiveness
        )

        return {
            "total_applications": len(applications),
            "total_cost": round(total_cost, 2),
            "total_quantity_kg": round(total_quantity, 2),
            "average_effectiveness": round(avg_effectiveness, 2),
            "by_fertilizer_type": {
                ftype: {
                    "count": data["count"],
                    "total_cost": round(data["total_cost"], 2),
                    "total_quantity_kg": round(data["total_quantity"], 2),
                    "avg_cost_per_kg": round(data["avg_cost_per_kg"], 2),
                    "avg_effectiveness": round(data["avg_effectiveness"], 2),
                    "roi_score": round(data["roi_score"], 2),
                }
                for ftype, data in type_analysis.items()
            },
            "by_category": {
                cat: {
                    "count": data["count"],
                    "total_cost": round(data["total_cost"], 2),
                    "avg_effectiveness": round(data["avg_effectiveness"], 2),
                }
                for cat, data in category_analysis.items()
            },
            "recommendations": recommendations,
        }

    def _generate_effectiveness_recommendations(
        self,
        type_analysis: Dict[str, Any],
        category_analysis: Dict[str, Any],
        avg_effectiveness: float,
    ) -> List[str]:
        """Generate recommendations based on effectiveness analysis"""
        recommendations = []

        # Find best performing fertilizer type
        if type_analysis:
            best_type = max(type_analysis.items(), key=lambda x: x[1].get("roi_score", 0))
            if best_type[1].get("roi_score", 0) > 0:
                recommendations.append(
                    f"Best ROI: {best_type[0]} with ROI score {best_type[1]['roi_score']:.2f}. "
                    f"Consider using more of this fertilizer type."
                )

        # Check overall effectiveness
        if avg_effectiveness < 50:
            recommendations.append(
                "Overall effectiveness is low (<50). Consider soil testing before applications "
                "and following recommended timing and quantities."
            )
        elif avg_effectiveness >= 70:
            recommendations.append(
                "Excellent effectiveness (≥70). Continue current fertilizer management practices."
            )

        # Compare organic vs chemical
        if "organic" in category_analysis and "chemical" in category_analysis:
            org_eff = category_analysis["organic"].get("avg_effectiveness", 0)
            chem_eff = category_analysis["chemical"].get("avg_effectiveness", 0)

            if org_eff > chem_eff + 10:
                recommendations.append(
                    f"Organic fertilizers show better effectiveness ({org_eff:.1f}% vs {chem_eff:.1f}%). "
                    "Consider increasing organic fertilizer ratio for better soil health."
                )
            elif chem_eff > org_eff + 10:
                recommendations.append(
                    f"Chemical fertilizers show better effectiveness ({chem_eff:.1f}% vs {org_eff:.1f}%). "
                    "However, consider balancing with organic fertilizers for long-term soil health."
                )

        if not recommendations:
            recommendations.append(
                "Continue monitoring fertilizer applications and conduct soil tests to track effectiveness."
            )

        return recommendations

    async def generate_usage_report(
        self,
        farm_id: int,
        plot_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user=None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive fertilizer usage report with cost analysis

        Args:
            farm_id: Farm ID
            plot_id: Optional plot filter
            start_date: Optional start date filter (defaults to 1 year ago)
            end_date: Optional end date filter (defaults to today)

        Returns:
            Comprehensive usage report with cost analysis and recommendations
        """
        # Default to last year if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get applications
        applications = await self.get_application_history(
            farm_id=farm_id,
            plot_id=plot_id,
            start_date=start_date,
            end_date=end_date,
            user=user,
        )

        # Get effectiveness analysis
        effectiveness = await self.analyze_fertilizer_effectiveness(
            farm_id=farm_id,
            plot_id=plot_id,
            start_date=start_date,
            end_date=end_date,
            user=user,
        )

        # Calculate monthly breakdown
        monthly_breakdown = {}
        for app in applications:
            month_key = app.application_date.strftime("%Y-%m")
            if month_key not in monthly_breakdown:
                monthly_breakdown[month_key] = {
                    "applications": 0,
                    "total_cost": 0,
                    "total_quantity": 0,
                    "by_type": {},
                }

            monthly_breakdown[month_key]["applications"] += 1
            monthly_breakdown[month_key]["total_cost"] += float(app.cost_total)
            monthly_breakdown[month_key]["total_quantity"] += float(app.quantity_kg)

            ftype = app.fertilizer_type
            if ftype not in monthly_breakdown[month_key]["by_type"]:
                monthly_breakdown[month_key]["by_type"][ftype] = {"quantity": 0, "cost": 0}
            monthly_breakdown[month_key]["by_type"][ftype]["quantity"] += float(app.quantity_kg)
            monthly_breakdown[month_key]["by_type"][ftype]["cost"] += float(app.cost_total)

        # Calculate nutrient totals
        total_nitrogen = sum(float(app.nitrogen_kg) for app in applications if app.nitrogen_kg)
        total_phosphorus = sum(
            float(app.phosphorus_kg) for app in applications if app.phosphorus_kg
        )
        total_potassium = sum(float(app.potassium_kg) for app in applications if app.potassium_kg)

        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days,
            },
            "summary": {
                "total_applications": len(applications),
                "total_cost": round(effectiveness["total_cost"], 2),
                "total_quantity_kg": round(effectiveness["total_quantity_kg"], 2),
                "avg_cost_per_application": round(
                    effectiveness["total_cost"] / len(applications) if applications else 0, 2
                ),
            },
            "nutrients_applied": {
                "nitrogen_kg": round(total_nitrogen, 2),
                "phosphorus_kg": round(total_phosphorus, 2),
                "potassium_kg": round(total_potassium, 2),
            },
            "monthly_breakdown": {
                month: {
                    "applications": data["applications"],
                    "total_cost": round(data["total_cost"], 2),
                    "total_quantity_kg": round(data["total_quantity"], 2),
                    "by_type": {
                        ftype: {
                            "quantity_kg": round(tdata["quantity"], 2),
                            "cost": round(tdata["cost"], 2),
                        }
                        for ftype, tdata in data["by_type"].items()
                    },
                }
                for month, data in sorted(monthly_breakdown.items())
            },
            "effectiveness_analysis": effectiveness,
            "cost_optimization_tips": self._generate_cost_optimization_tips(
                effectiveness, applications
            ),
        }

    def _generate_cost_optimization_tips(
        self, effectiveness: Dict[str, Any], applications: List[FertilizerApplication]
    ) -> List[str]:
        """Generate cost optimization tips based on usage patterns"""
        tips = []

        # Check for high-cost, low-effectiveness fertilizers
        for ftype, data in effectiveness.get("by_fertilizer_type", {}).items():
            if data["avg_effectiveness"] < 50 and data["total_cost"] > 5000:
                tips.append(
                    f"Consider alternatives to {ftype}: Low effectiveness ({data['avg_effectiveness']:.1f}%) "
                    f"with high cost (₹{data['total_cost']:.2f})"
                )

        # Check organic vs chemical balance
        category_data = effectiveness.get("by_category", {})
        if "organic" in category_data and "chemical" in category_data:
            org_cost = category_data["organic"]["total_cost"]
            chem_cost = category_data["chemical"]["total_cost"]
            total_cost = org_cost + chem_cost

            org_ratio = org_cost / total_cost if total_cost > 0 else 0

            if org_ratio < 0.2:
                tips.append(
                    "Consider increasing organic fertilizer usage (currently <20% of cost). "
                    "Organic fertilizers improve long-term soil health and reduce chemical dependency."
                )

        # Check for seasonal patterns
        if len(applications) >= 4:
            # Group by season
            seasonal_costs = {"kharif": 0, "rabi": 0, "zaid": 0}
            for app in applications:
                month = app.application_date.month
                if 6 <= month <= 10:  # Kharif
                    seasonal_costs["kharif"] += float(app.cost_total)
                elif 11 <= month or month <= 3:  # Rabi
                    seasonal_costs["rabi"] += float(app.cost_total)
                else:  # Zaid
                    seasonal_costs["zaid"] += float(app.cost_total)

            max_season = max(seasonal_costs.items(), key=lambda x: x[1])
            if max_season[1] > sum(seasonal_costs.values()) * 0.5:
                tips.append(
                    f"High fertilizer cost in {max_season[0]} season (₹{max_season[1]:.2f}). "
                    "Consider soil testing and split applications to optimize usage."
                )

        if not tips:
            tips.append(
                "Fertilizer usage appears well-balanced. Continue monitoring and conducting "
                "soil tests to maintain optimal application rates."
            )

        return tips
