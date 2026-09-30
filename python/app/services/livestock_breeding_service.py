"""
Livestock Breeding Service
Handles breeding optimization, cycle tracking, offspring management, and breeding program reports
"""

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.orm.breeding_record import BreedingRecord
from app.orm.livestock import Livestock
from app.orm.offspring import Offspring
from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)


class LivestockBreedingService:
    """Service for managing livestock breeding optimization"""

    # Gestation periods by species (in days)
    GESTATION_PERIODS = {
        "cattle": 283,  # ~9 months
        "buffalo": 310,  # ~10 months
        "goat": 150,  # ~5 months
        "poultry": 21,  # ~3 weeks
    }

    # Optimal breeding seasons by species
    BREEDING_SEASONS = {
        "cattle": "October to February (cooler months)",
        "buffalo": "October to March (cooler months)",
        "goat": "September to November (autumn)",
        "poultry": "Year-round with peak in spring",
    }

    def __init__(self):
        """Initialize the breeding service"""
        self.breeding_record_model = BreedingRecord()
        self.offspring_model = Offspring()
        self.livestock_model = Livestock()
        self.bedrock_service = BedrockService()

    # ========================================================================
    # Breeding Record Management
    # ========================================================================

    def create_breeding_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new breeding record

        Args:
            record_data: Breeding record data

        Returns:
            Created breeding record
        """
        try:
            # Verify livestock exists
            livestock = self.livestock_model.find(record_data["livestock_id"])
            if not livestock:
                raise ValueError(f"Livestock with ID {record_data['livestock_id']} not found")

            # Calculate expected delivery date if not provided
            if not record_data.get("expected_delivery_date") and record_data.get("breeding_date"):
                breeding_date = record_data["breeding_date"]
                if isinstance(breeding_date, str):
                    breeding_date = datetime.strptime(breeding_date, "%Y-%m-%d").date()

                species = livestock["species"].lower()
                gestation_days = self.GESTATION_PERIODS.get(species, 283)
                expected_delivery = breeding_date + timedelta(days=gestation_days)
                record_data["expected_delivery_date"] = expected_delivery

            # Create breeding record
            result = self.breeding_record_model.create(record_data)

            logger.info(
                f"Created breeding record {result['id']} for livestock {record_data['livestock_id']}"
            )

            return result

        except Exception as e:
            logger.error(f"Error creating breeding record: {str(e)}")
            raise

    def get_breeding_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Get breeding record by ID"""
        try:
            return self.breeding_record_model.find(record_id)
        except Exception as e:
            logger.error(f"Error fetching breeding record {record_id}: {str(e)}")
            raise

    def update_breeding_record(
        self, record_id: int, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update breeding record"""
        try:
            existing = self.breeding_record_model.find(record_id)
            if not existing:
                return None

            self.breeding_record_model.update(record_id, update_data)
            result = self.breeding_record_model.find(record_id)

            logger.info(f"Updated breeding record {record_id}")

            return result

        except Exception as e:
            logger.error(f"Error updating breeding record {record_id}: {str(e)}")
            raise

    def delete_breeding_record(self, record_id: int) -> bool:
        """Delete breeding record (soft delete)"""
        try:
            existing = self.breeding_record_model.find(record_id)
            if not existing:
                return False

            self.breeding_record_model.delete(record_id)
            logger.info(f"Deleted breeding record {record_id}")

            return True

        except Exception as e:
            logger.error(f"Error deleting breeding record {record_id}: {str(e)}")
            raise

    def list_breeding_records(
        self,
        livestock_id: Optional[int] = None,
        farmer_id: Optional[int] = None,
        pregnancy_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List breeding records with filters"""
        try:
            query = self.breeding_record_model

            if livestock_id:
                query = query.where({"livestock_id": livestock_id})

            if farmer_id:
                if livestock_id:
                    query = query.and_where({"farmer_id": farmer_id})
                else:
                    query = query.where({"farmer_id": farmer_id})

            if pregnancy_status:
                if livestock_id or farmer_id:
                    query = query.and_where({"pregnancy_status": pregnancy_status.lower()})
                else:
                    query = query.where({"pregnancy_status": pregnancy_status.lower()})

            result = query.get()
            all_records = result.to_dict() if result else []

            # Sort by breeding_date descending
            all_records.sort(key=lambda x: x["breeding_date"], reverse=True)

            return all_records[skip : skip + limit]

        except Exception as e:
            logger.error(f"Error listing breeding records: {str(e)}")
            raise

    # ========================================================================
    # Offspring Management
    # ========================================================================

    def create_offspring(self, offspring_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create offspring record"""
        try:
            # Verify breeding record exists
            breeding_record = self.breeding_record_model.find(offspring_data["breeding_record_id"])
            if not breeding_record:
                raise ValueError(
                    f"Breeding record with ID {offspring_data['breeding_record_id']} not found"
                )

            # Create offspring
            result = self.offspring_model.create(offspring_data)

            # Update breeding record with offspring count
            current_count = breeding_record.get("number_of_offspring", 0) or 0
            self.breeding_record_model.update(
                offspring_data["breeding_record_id"], {"number_of_offspring": current_count + 1}
            )

            logger.info(
                f"Created offspring {result['id']} for breeding record {offspring_data['breeding_record_id']}"
            )

            return result

        except Exception as e:
            logger.error(f"Error creating offspring: {str(e)}")
            raise

    def get_offspring(self, offspring_id: int) -> Optional[Dict[str, Any]]:
        """Get offspring by ID"""
        try:
            return self.offspring_model.find(offspring_id)
        except Exception as e:
            logger.error(f"Error fetching offspring {offspring_id}: {str(e)}")
            raise

    def update_offspring(
        self, offspring_id: int, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update offspring record"""
        try:
            existing = self.offspring_model.find(offspring_id)
            if not existing:
                return None

            # Calculate growth rate if current weight is updated
            if "current_weight" in update_data and update_data["current_weight"]:
                birth_weight = existing.get("birth_weight")
                birth_date = existing["birth_date"]
                if isinstance(birth_date, str):
                    birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()

                if birth_weight:
                    days_old = (date.today() - birth_date).days
                    if days_old > 0:
                        weight_gain = float(update_data["current_weight"]) - float(birth_weight)
                        growth_rate = weight_gain / days_old
                        update_data["growth_rate"] = Decimal(str(round(growth_rate, 3)))

            self.offspring_model.update(offspring_id, update_data)
            result = self.offspring_model.find(offspring_id)

            logger.info(f"Updated offspring {offspring_id}")

            return result

        except Exception as e:
            logger.error(f"Error updating offspring {offspring_id}: {str(e)}")
            raise

    def list_offspring(
        self,
        breeding_record_id: Optional[int] = None,
        farmer_id: Optional[int] = None,
        health_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List offspring with filters"""
        try:
            query = self.offspring_model

            if breeding_record_id:
                query = query.where({"breeding_record_id": breeding_record_id})

            if farmer_id:
                if breeding_record_id:
                    query = query.and_where({"farmer_id": farmer_id})
                else:
                    query = query.where({"farmer_id": farmer_id})

            if health_status:
                if breeding_record_id or farmer_id:
                    query = query.and_where({"health_status": health_status.lower()})
                else:
                    query = query.where({"health_status": health_status.lower()})

            result = query.get()
            all_offspring = result.to_dict() if result else []

            # Sort by birth_date descending
            all_offspring.sort(key=lambda x: x["birth_date"], reverse=True)

            return all_offspring[skip : skip + limit]

        except Exception as e:
            logger.error(f"Error listing offspring: {str(e)}")
            raise

    # ========================================================================
    # Breeding Recommendations (AI-Powered)
    # ========================================================================

    def get_breeding_recommendations(self, livestock_id: int) -> Dict[str, Any]:
        """
        Get AI-powered breeding recommendations for livestock

        Args:
            livestock_id: Livestock ID

        Returns:
            Breeding recommendations with optimal pairs and timing
        """
        try:
            # Get livestock details
            livestock = self.livestock_model.find(livestock_id)
            if not livestock:
                raise ValueError(f"Livestock with ID {livestock_id} not found")

            species = livestock["species"].lower()
            breed = livestock["breed"]

            # Get breeding history
            breeding_history = self.list_breeding_records(livestock_id=livestock_id, limit=10)

            # Get offspring performance
            offspring_performance = []
            for breeding in breeding_history:
                offspring_list = self.list_offspring(breeding_record_id=breeding["id"])
                for offspring in offspring_list:
                    offspring_performance.append(
                        {
                            "birth_weight": offspring.get("birth_weight"),
                            "growth_rate": offspring.get("growth_rate"),
                            "health_status": offspring.get("health_status"),
                            "sale_price": offspring.get("sale_price"),
                        }
                    )

            # Build prompt for Bedrock
            prompt = self._build_breeding_recommendation_prompt(
                species, breed, breeding_history, offspring_performance
            )

            # Get AI recommendations
            bedrock_response = self.bedrock_service._invoke_claude(
                prompt=prompt, max_tokens=2000, temperature=0.7
            )

            # Parse response
            recommendations = self._parse_breeding_recommendations(bedrock_response, species, breed)

            logger.info(f"Generated breeding recommendations for livestock {livestock_id}")

            return recommendations

        except Exception as e:
            logger.error(
                f"Error generating breeding recommendations for livestock {livestock_id}: {str(e)}"
            )
            raise

    def _build_breeding_recommendation_prompt(
        self,
        species: str,
        breed: str,
        breeding_history: List[Dict[str, Any]],
        offspring_performance: List[Dict[str, Any]],
    ) -> str:
        """Build prompt for breeding recommendations"""

        prompt = f"""You are an expert livestock breeding advisor. Provide breeding recommendations for a {species} of breed {breed}.

Current Livestock Details:
- Species: {species}
- Breed: {breed}

Breeding History:
- Total breedings: {len(breeding_history)}
- Successful breedings: {sum(1 for b in breeding_history if b.get('pregnancy_status') == 'delivered')}

Offspring Performance:
- Total offspring: {len(offspring_performance)}
- Average birth weight: {self._calculate_average([o.get('birth_weight') for o in offspring_performance if o.get('birth_weight')])} kg
- Average growth rate: {self._calculate_average([o.get('growth_rate') for o in offspring_performance if o.get('growth_rate')])} kg/day
- Healthy offspring: {sum(1 for o in offspring_performance if o.get('health_status') == 'healthy')}

Please provide:
1. Top 3 recommended mate breeds with compatibility scores (0-1)
2. Expected offspring traits for each recommendation
3. Reasoning for each recommendation
4. Optimal breeding season
5. Breeding tips and best practices

Format your response as JSON with this structure:
{{
  "recommendations": [
    {{
      "mate_breed": "breed name",
      "compatibility_score": 0.85,
      "expected_offspring_traits": {{
        "milk_yield": "high/medium/low",
        "growth_rate": "fast/medium/slow",
        "disease_resistance": "high/medium/low"
      }},
      "reasoning": "explanation"
    }}
  ],
  "optimal_breeding_season": "season description",
  "breeding_tips": ["tip1", "tip2", "tip3"]
}}
"""
        return prompt

    def _parse_breeding_recommendations(
        self, bedrock_response: str, species: str, breed: str
    ) -> Dict[str, Any]:
        """Parse Bedrock response into structured recommendations"""
        try:
            # Try to parse JSON from response
            # Look for JSON block in response
            start_idx = bedrock_response.find("{")
            end_idx = bedrock_response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = bedrock_response[start_idx:end_idx]
                parsed = json.loads(json_str)
            else:
                # Fallback to default recommendations
                parsed = self._get_default_recommendations(species, breed)

            # Add gestation period
            gestation_days = self.GESTATION_PERIODS.get(species, 283)

            return {
                "livestock_breed": breed,
                "livestock_species": species,
                "recommendations": parsed.get("recommendations", []),
                "optimal_breeding_season": parsed.get(
                    "optimal_breeding_season",
                    self.BREEDING_SEASONS.get(species, "Consult veterinarian"),
                ),
                "estimated_gestation_days": gestation_days,
                "breeding_tips": parsed.get("breeding_tips", []),
            }

        except Exception as e:
            logger.warning(f"Error parsing breeding recommendations: {str(e)}, using defaults")
            return self._get_default_recommendations(species, breed)

    def _get_default_recommendations(self, species: str, breed: str) -> Dict[str, Any]:
        """Get default breeding recommendations"""
        gestation_days = self.GESTATION_PERIODS.get(species, 283)

        return {
            "livestock_breed": breed,
            "livestock_species": species,
            "recommendations": [
                {
                    "mate_breed": f"High-quality {breed}",
                    "compatibility_score": 0.8,
                    "expected_offspring_traits": {
                        "milk_yield": "medium",
                        "growth_rate": "medium",
                        "disease_resistance": "medium",
                    },
                    "reasoning": "Same breed mating maintains breed characteristics",
                }
            ],
            "optimal_breeding_season": self.BREEDING_SEASONS.get(species, "Consult veterinarian"),
            "estimated_gestation_days": gestation_days,
            "breeding_tips": [
                "Ensure livestock is in good health before breeding",
                "Consult veterinarian for optimal timing",
                "Monitor pregnancy progress regularly",
            ],
        }

    def _calculate_average(self, values: List[Any]) -> float:
        """Calculate average of numeric values"""
        numeric_values = [float(v) for v in values if v is not None]
        if not numeric_values:
            return 0.0
        return round(sum(numeric_values) / len(numeric_values), 2)

    # ========================================================================
    # Breeding Program Reports
    # ========================================================================

    def generate_breeding_program_report(
        self, farmer_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive breeding program report

        Args:
            farmer_id: Farmer ID
            start_date: Report start date (optional)
            end_date: Report end date (optional)

        Returns:
            Breeding program report with metrics and recommendations
        """
        try:
            # Default date range: last 12 months
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=365)

            # Get all breeding records for farmer
            all_breeding_records = self.list_breeding_records(farmer_id=farmer_id, limit=1000)

            # Filter by date range
            breeding_records = []
            for record in all_breeding_records:
                breeding_date = record["breeding_date"]
                if isinstance(breeding_date, str):
                    breeding_date = datetime.strptime(breeding_date, "%Y-%m-%d").date()

                if start_date <= breeding_date <= end_date:
                    breeding_records.append(record)

            # Calculate metrics
            metrics = self._calculate_breeding_metrics(breeding_records, farmer_id)

            # Get offspring summary
            offspring_summary = self._calculate_offspring_summary(breeding_records)

            # Calculate genetic trends
            genetic_trends = self._calculate_genetic_trends(breeding_records, farmer_id)

            # Generate recommendations
            recommendations = self._generate_breeding_program_recommendations(
                metrics, offspring_summary, genetic_trends
            )

            return {
                "farmer_id": farmer_id,
                "report_period": {"start_date": start_date, "end_date": end_date},
                "metrics": metrics,
                "breeding_records": breeding_records,
                "offspring_summary": offspring_summary,
                "genetic_trends": genetic_trends,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(
                f"Error generating breeding program report for farmer {farmer_id}: {str(e)}"
            )
            raise

    def _calculate_breeding_metrics(
        self, breeding_records: List[Dict[str, Any]], farmer_id: int
    ) -> Dict[str, Any]:
        """Calculate breeding program metrics"""

        total_breedings = len(breeding_records)
        successful_breedings = sum(
            1 for r in breeding_records if r.get("pregnancy_status") == "delivered"
        )

        success_rate = (
            Decimal(successful_breedings / total_breedings * 100)
            if total_breedings > 0
            else Decimal("0")
        )

        # Calculate total offspring
        total_offspring = sum(r.get("number_of_offspring", 0) or 0 for r in breeding_records)

        avg_offspring = (
            Decimal(total_offspring / successful_breedings)
            if successful_breedings > 0
            else Decimal("0")
        )

        # Calculate costs
        total_breeding_cost = sum(
            Decimal(str(r.get("breeding_cost", 0) or 0)) for r in breeding_records
        )

        # Calculate revenue from offspring
        all_offspring = self.list_offspring(farmer_id=farmer_id, limit=10000)
        total_offspring_revenue = sum(
            Decimal(str(o.get("sale_price", 0) or 0)) for o in all_offspring if o.get("sale_price")
        )

        # Calculate ROI
        breeding_roi = Decimal("0")
        if total_breeding_cost > 0:
            breeding_roi = (
                (total_offspring_revenue - total_breeding_cost) / total_breeding_cost * 100
            )

        # Calculate genetic improvement score (based on offspring health and growth)
        healthy_offspring = sum(1 for o in all_offspring if o.get("health_status") == "healthy")
        genetic_improvement_score = (
            Decimal(healthy_offspring / len(all_offspring) * 100) if all_offspring else Decimal("0")
        )

        return {
            "total_breedings": total_breedings,
            "successful_breedings": successful_breedings,
            "success_rate": round(success_rate, 2),
            "total_offspring": total_offspring,
            "average_offspring_per_breeding": round(avg_offspring, 2),
            "total_breeding_cost": round(total_breeding_cost, 2),
            "total_offspring_revenue": round(total_offspring_revenue, 2),
            "breeding_roi": round(breeding_roi, 2),
            "genetic_improvement_score": round(genetic_improvement_score, 2),
        }

    def _calculate_offspring_summary(
        self, breeding_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate offspring summary statistics"""

        all_offspring = []
        for record in breeding_records:
            offspring_list = self.list_offspring(breeding_record_id=record["id"])
            all_offspring.extend(offspring_list)

        if not all_offspring:
            return {
                "total_offspring": 0,
                "average_birth_weight": 0,
                "average_growth_rate": 0,
                "healthy_offspring": 0,
                "sold_offspring": 0,
                "average_sale_price": 0,
            }

        birth_weights = [
            float(o.get("birth_weight", 0) or 0) for o in all_offspring if o.get("birth_weight")
        ]
        growth_rates = [
            float(o.get("growth_rate", 0) or 0) for o in all_offspring if o.get("growth_rate")
        ]
        sale_prices = [
            float(o.get("sale_price", 0) or 0) for o in all_offspring if o.get("sale_price")
        ]

        return {
            "total_offspring": len(all_offspring),
            "average_birth_weight": (
                round(sum(birth_weights) / len(birth_weights), 2) if birth_weights else 0
            ),
            "average_growth_rate": (
                round(sum(growth_rates) / len(growth_rates), 3) if growth_rates else 0
            ),
            "healthy_offspring": sum(
                1 for o in all_offspring if o.get("health_status") == "healthy"
            ),
            "sold_offspring": len(sale_prices),
            "average_sale_price": (
                round(sum(sale_prices) / len(sale_prices), 2) if sale_prices else 0
            ),
        }

    def _calculate_genetic_trends(
        self, breeding_records: List[Dict[str, Any]], farmer_id: int
    ) -> Dict[str, Any]:
        """Calculate genetic improvement trends"""

        # Get all offspring sorted by birth date
        all_offspring = self.list_offspring(farmer_id=farmer_id, limit=10000)
        all_offspring.sort(key=lambda x: x["birth_date"])

        if len(all_offspring) < 2:
            return {
                "trend": "insufficient_data",
                "improvement_percentage": 0,
                "description": "Need more breeding cycles to identify trends",
            }

        # Split into first half and second half
        mid_point = len(all_offspring) // 2
        first_half = all_offspring[:mid_point]
        second_half = all_offspring[mid_point:]

        # Calculate average metrics for each half
        first_avg_weight = self._calculate_average([o.get("birth_weight") for o in first_half])
        second_avg_weight = self._calculate_average([o.get("birth_weight") for o in second_half])

        first_avg_growth = self._calculate_average([o.get("growth_rate") for o in first_half])
        second_avg_growth = self._calculate_average([o.get("growth_rate") for o in second_half])

        # Calculate improvement
        weight_improvement = (
            ((second_avg_weight - first_avg_weight) / first_avg_weight * 100)
            if first_avg_weight > 0
            else 0
        )
        growth_improvement = (
            ((second_avg_growth - first_avg_growth) / first_avg_growth * 100)
            if first_avg_growth > 0
            else 0
        )

        overall_improvement = (weight_improvement + growth_improvement) / 2

        if overall_improvement > 5:
            trend = "improving"
            description = "Breeding program showing positive genetic improvement"
        elif overall_improvement < -5:
            trend = "declining"
            description = "Breeding program needs optimization"
        else:
            trend = "stable"
            description = "Breeding program maintaining consistent quality"

        return {
            "trend": trend,
            "improvement_percentage": round(overall_improvement, 2),
            "description": description,
            "weight_trend": round(weight_improvement, 2),
            "growth_trend": round(growth_improvement, 2),
        }

    def _generate_breeding_program_recommendations(
        self,
        metrics: Dict[str, Any],
        offspring_summary: Dict[str, Any],
        genetic_trends: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations for breeding program optimization"""

        recommendations = []

        # Success rate recommendations
        if metrics["success_rate"] < 60:
            recommendations.append(
                "⚠️ Breeding success rate is below 60%. Consider consulting veterinarian for health checks and optimal breeding timing."
            )
        elif metrics["success_rate"] > 80:
            recommendations.append(
                "✓ Excellent breeding success rate! Continue current breeding practices."
            )

        # ROI recommendations
        if metrics["breeding_roi"] < 0:
            recommendations.append(
                "⚠️ Breeding program showing negative ROI. Review breeding costs and consider higher-value breeds or better market timing."
            )
        elif metrics["breeding_roi"] > 50:
            recommendations.append("✓ Strong breeding ROI! Consider expanding breeding program.")

        # Genetic trend recommendations
        if genetic_trends["trend"] == "declining":
            recommendations.append(
                "⚠️ Genetic quality declining. Consider introducing new breeding stock or consulting breeding specialist."
            )
        elif genetic_trends["trend"] == "improving":
            recommendations.append(
                "✓ Genetic improvement detected! Current breeding strategy is effective."
            )

        # Offspring health recommendations
        if offspring_summary["total_offspring"] > 0:
            health_rate = (
                offspring_summary["healthy_offspring"] / offspring_summary["total_offspring"]
            ) * 100
            if health_rate < 80:
                recommendations.append(
                    "⚠️ Offspring health rate below 80%. Review nutrition, housing, and veterinary care practices."
                )

        # General recommendations
        if not recommendations:
            recommendations.append(
                "✓ Breeding program performing well. Continue monitoring and maintain good practices."
            )

        return recommendations


# Singleton instance
_breeding_service_instance = None


def get_breeding_service() -> LivestockBreedingService:
    """Get singleton instance of breeding service"""
    global _breeding_service_instance
    if _breeding_service_instance is None:
        _breeding_service_instance = LivestockBreedingService()
    return _breeding_service_instance
