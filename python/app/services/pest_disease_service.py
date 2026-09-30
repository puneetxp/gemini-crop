"""
Pest and Disease Early Warning Service
Monitors weather conditions and crop stages to provide early warnings

Validates: Requirements AC10 (Phase 6 - Required)
Task 25.2: Build pest and disease early warning system
"""

import logging
from datetime import datetime, timedelta
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as AsyncSession
from typing import Dict, List, Optional

from app.services.farm_access import Row, crop_for_user, fetch_all, fetch_one
from app.services.notification_service import get_notification_service

logger = logging.getLogger(__name__)


# Pest and disease risk thresholds based on weather conditions
PEST_DISEASE_THRESHOLDS = {
    "aphids": {
        "temp_min": 20,
        "temp_max": 30,
        "humidity_min": 60,
        "risk_stages": ["vegetative", "flowering"],
        "severity": "medium",
        "description": "Aphid infestation risk",
    },
    "fungal_diseases": {
        "temp_min": 15,
        "temp_max": 28,
        "humidity_min": 80,
        "rainfall_min": 5,  # mm per day
        "risk_stages": ["vegetative", "flowering", "maturation"],
        "severity": "high",
        "description": "Fungal disease risk (leaf spot, blight, rust)",
    },
    "stem_borer": {
        "temp_min": 25,
        "temp_max": 35,
        "humidity_min": 70,
        "risk_stages": ["vegetative", "flowering"],
        "severity": "high",
        "description": "Stem borer infestation risk",
    },
    "whitefly": {
        "temp_min": 22,
        "temp_max": 32,
        "humidity_min": 50,
        "risk_stages": ["vegetative", "flowering"],
        "severity": "medium",
        "description": "Whitefly infestation risk",
    },
    "bacterial_wilt": {
        "temp_min": 28,
        "temp_max": 35,
        "humidity_min": 85,
        "risk_stages": ["vegetative", "flowering"],
        "severity": "high",
        "description": "Bacterial wilt risk",
    },
    "powdery_mildew": {
        "temp_min": 18,
        "temp_max": 28,
        "humidity_min": 50,
        "humidity_max": 70,
        "risk_stages": ["vegetative", "flowering"],
        "severity": "medium",
        "description": "Powdery mildew risk",
    },
    "fruit_borer": {
        "temp_min": 20,
        "temp_max": 30,
        "humidity_min": 60,
        "risk_stages": ["flowering", "maturation"],
        "severity": "high",
        "description": "Fruit borer infestation risk",
    },
    "leaf_miner": {
        "temp_min": 22,
        "temp_max": 32,
        "humidity_min": 55,
        "risk_stages": ["vegetative", "flowering"],
        "severity": "low",
        "description": "Leaf miner infestation risk",
    },
}


# Pest and disease management recommendations
PEST_DISEASE_MANAGEMENT = {
    "aphids": {
        "organic": [
            "Spray neem oil solution (5ml per liter water)",
            "Release ladybugs as natural predators",
            "Use yellow sticky traps to monitor population",
            "Spray garlic-chili solution (100g garlic + 50g chili per 10L water)",
        ],
        "chemical": [
            "Apply Imidacloprid 17.8% SL @ 0.3ml per liter",
            "Use Thiamethoxam 25% WG @ 0.2g per liter",
            "Spray Acetamiprid 20% SP @ 0.2g per liter",
        ],
        "timing": "Apply at first sign of infestation, repeat after 7-10 days if needed",
        "prevention": [
            "Monitor plants weekly for early detection",
            "Remove and destroy heavily infested plants",
            "Maintain proper plant spacing for air circulation",
            "Avoid excessive nitrogen fertilization",
        ],
    },
    "fungal_diseases": {
        "organic": [
            "Apply Trichoderma viride @ 5g per liter water",
            "Spray Pseudomonas fluorescens @ 10g per liter",
            "Use copper oxychloride @ 3g per liter water",
            "Apply neem cake to soil @ 100kg per acre",
        ],
        "chemical": [
            "Spray Mancozeb 75% WP @ 2.5g per liter",
            "Apply Carbendazim 50% WP @ 1g per liter",
            "Use Propiconazole 25% EC @ 1ml per liter",
            "Spray Azoxystrobin 23% SC @ 1ml per liter",
        ],
        "timing": "Apply preventively before monsoon, repeat every 10-15 days during humid conditions",
        "prevention": [
            "Ensure good drainage to prevent waterlogging",
            "Remove infected plant debris immediately",
            "Avoid overhead irrigation during humid weather",
            "Maintain proper plant spacing",
            "Use disease-resistant varieties when available",
        ],
    },
    "stem_borer": {
        "organic": [
            "Release Trichogramma wasps @ 50,000 per acre",
            "Apply neem seed kernel extract @ 5% solution",
            "Use pheromone traps @ 5 traps per acre",
            "Spray Bacillus thuringiensis @ 1g per liter",
        ],
        "chemical": [
            "Apply Chlorantraniliprole 18.5% SC @ 0.3ml per liter",
            "Use Cartap hydrochloride 50% SP @ 1g per liter",
            "Spray Fipronil 5% SC @ 2ml per liter",
        ],
        "timing": "Apply at early vegetative stage, repeat at 15-day intervals",
        "prevention": [
            "Remove and destroy crop residues after harvest",
            "Use light traps to monitor adult moth population",
            "Avoid staggered planting to break pest cycle",
            "Maintain field sanitation",
        ],
    },
    "whitefly": {
        "organic": [
            "Spray neem oil @ 5ml per liter water",
            "Use yellow sticky traps @ 10 traps per acre",
            "Apply insecticidal soap solution",
            "Release parasitic wasps (Encarsia formosa)",
        ],
        "chemical": [
            "Apply Buprofezin 25% SC @ 1.5ml per liter",
            "Use Diafenthiuron 50% WP @ 1g per liter",
            "Spray Spiromesifen 22.9% SC @ 1ml per liter",
        ],
        "timing": "Apply at first appearance, repeat after 7 days",
        "prevention": [
            "Use reflective mulch to repel whiteflies",
            "Remove weeds that harbor whiteflies",
            "Monitor with yellow sticky traps",
            "Avoid water stress which attracts whiteflies",
        ],
    },
    "bacterial_wilt": {
        "organic": [
            "Apply Pseudomonas fluorescens @ 10g per liter as soil drench",
            "Use Trichoderma harzianum @ 5g per liter",
            "Remove and destroy infected plants immediately",
            "Avoid planting in infected soil for 2 years",
        ],
        "chemical": [
            "Apply Streptocycline @ 0.5g per liter as soil drench",
            "Use Copper oxychloride @ 3g per liter",
            "Drench with Bordeaux mixture (1%)",
        ],
        "timing": "Apply at first sign of wilting, no cure once established",
        "prevention": [
            "Use disease-free seeds and seedlings",
            "Practice crop rotation with non-host crops",
            "Ensure good drainage",
            "Avoid wounding plants during cultivation",
            "Disinfect tools between plants",
        ],
    },
    "powdery_mildew": {
        "organic": [
            "Spray milk solution (1:9 milk to water ratio)",
            "Apply sulfur dust @ 20kg per acre",
            "Use baking soda solution (1 tablespoon per liter)",
            "Spray neem oil @ 5ml per liter",
        ],
        "chemical": [
            "Apply Sulfex 80% WP @ 2g per liter",
            "Use Hexaconazole 5% EC @ 2ml per liter",
            "Spray Penconazole 10% EC @ 0.5ml per liter",
        ],
        "timing": "Apply at first sign of white powdery spots, repeat every 7-10 days",
        "prevention": [
            "Ensure good air circulation between plants",
            "Avoid overhead watering",
            "Remove infected leaves promptly",
            "Plant in full sun locations",
        ],
    },
    "fruit_borer": {
        "organic": [
            "Install pheromone traps @ 5 traps per acre",
            "Spray Bacillus thuringiensis @ 1g per liter",
            "Release Trichogramma wasps @ 50,000 per acre",
            "Apply neem seed kernel extract @ 5%",
        ],
        "chemical": [
            "Spray Emamectin benzoate 5% SG @ 0.5g per liter",
            "Apply Spinosad 45% SC @ 0.3ml per liter",
            "Use Indoxacarb 14.5% SC @ 1ml per liter",
        ],
        "timing": "Apply at flowering stage, repeat at 10-day intervals",
        "prevention": [
            "Remove and destroy infested fruits",
            "Use light traps to monitor adult moths",
            "Practice deep plowing after harvest",
            "Maintain field sanitation",
        ],
    },
    "leaf_miner": {
        "organic": [
            "Spray neem oil @ 5ml per liter water",
            "Remove and destroy affected leaves",
            "Use yellow sticky traps",
            "Apply neem cake to soil @ 100kg per acre",
        ],
        "chemical": [
            "Apply Abamectin 1.9% EC @ 1ml per liter",
            "Use Cyromazine 75% WP @ 0.5g per liter",
            "Spray Diafenthiuron 50% WP @ 1g per liter",
        ],
        "timing": "Apply at first sign of leaf mining, repeat after 10 days",
        "prevention": [
            "Remove weeds that harbor leaf miners",
            "Use reflective mulch",
            "Monitor with yellow sticky traps",
            "Maintain plant health with proper nutrition",
        ],
    },
}


class PestDiseaseService:
    """
    Service for pest and disease early warning and management

    Validates: Requirements AC10.3 (Phase 6 - Required)
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session"""
        self.db = db
        self.notification_service = get_notification_service()

    async def check_pest_disease_risk(
        self,
        crop_id: int,
        weather_data: Dict[str, Any],
        current_stage: str,
        save_to_db: bool = True,
        user=None,
    ) -> List[Dict[str, Any]]:
        """
        Check for pest and disease risks based on weather and crop stage

        Args:
            crop_id: Crop ID
            weather_data: Current weather data (temp, humidity, rainfall)
            current_stage: Current crop growth stage
            save_to_db: Whether to save alerts to database

        Returns:
            List of detected risks with severity and recommendations

        Validates: AC10.3 - Early warning alerts based on weather and crop stage
        """
        try:
            import json

            risks = []

            temp = weather_data.get("temperature", 0)
            humidity = weather_data.get("humidity", 0)
            rainfall = weather_data.get("rainfall", 0)

            # Get crop details for farm_id (crops link to farms through farm_plots).
            # With a user, someone else's crop raises LookupError (router -> 404).
            if user is not None:
                crop = crop_for_user(crop_id, user)
            else:
                try:
                    crop = crop_for_user(crop_id, None)
                except LookupError:
                    crop = None

            if not crop:
                logger.warning(f"Crop {crop_id} not found")
                return risks

            # Check each pest/disease threshold
            for pest_disease, thresholds in PEST_DISEASE_THRESHOLDS.items():
                # Check if current stage is at risk
                if current_stage not in thresholds.get("risk_stages", []):
                    continue

                # Check temperature range
                temp_min = thresholds.get("temp_min", 0)
                temp_max = thresholds.get("temp_max", 100)
                if not (temp_min <= temp <= temp_max):
                    continue

                # Check humidity
                humidity_min = thresholds.get("humidity_min", 0)
                humidity_max = thresholds.get("humidity_max", 100)
                if not (humidity_min <= humidity <= humidity_max):
                    continue

                # Check rainfall if specified
                rainfall_min = thresholds.get("rainfall_min")
                if rainfall_min is not None and rainfall < rainfall_min:
                    continue

                # Get management recommendations
                management = PEST_DISEASE_MANAGEMENT.get(pest_disease, {})

                # Risk detected
                risk = {
                    "pest_disease": pest_disease,
                    "severity": thresholds["severity"],
                    "description": thresholds["description"],
                    "current_conditions": {
                        "temperature": temp,
                        "humidity": humidity,
                        "rainfall": rainfall,
                        "crop_stage": current_stage,
                    },
                    "management": management,
                    "detected_at": datetime.now().isoformat(),
                }

                risks.append(risk)
                logger.info(f"Detected {pest_disease} risk for crop {crop_id}")

                # Save alert to database
                if save_to_db:
                    try:
                        alert_type = (
                            "pest"
                            if "borer" in pest_disease
                            or "fly" in pest_disease
                            or "aphid" in pest_disease
                            or "miner" in pest_disease
                            else "disease"
                        )
                        alert = fetch_one(
                            """INSERT INTO pest_disease_alerts
                               (crop_id, farm_id, pest_disease_name, alert_type, severity, description, crop_stage,
                                weather_conditions, organic_recommendations, chemical_recommendations,
                                prevention_measures, timing_instructions, notification_sent, is_resolved)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0) RETURNING *""",
                            [
                                crop_id,
                                crop.farm_id,
                                pest_disease,
                                alert_type,
                                thresholds["severity"],
                                thresholds["description"],
                                current_stage,
                                json.dumps(
                                    {
                                        "temperature": temp,
                                        "humidity": humidity,
                                        "rainfall": rainfall,
                                    }
                                ),
                                json.dumps(management.get("organic", [])),
                                json.dumps(management.get("chemical", [])),
                                json.dumps(management.get("prevention", [])),
                                management.get("timing", ""),
                            ],
                        )
                        logger.info(f"Saved pest/disease alert {alert.id} for crop {crop_id}")
                    except Exception as e:
                        logger.error(f"Error saving alert to database: {e}")

            return risks

        except Exception as e:
            logger.error(f"Error checking pest/disease risk for crop {crop_id}: {e}")
            raise

    async def get_management_recommendations(
        self, pest_disease: str, preference: str = "both"
    ) -> Dict[str, Any]:
        """
        Get pest/disease management recommendations

        Args:
            pest_disease: Name of pest or disease
            preference: 'organic', 'chemical', or 'both'

        Returns:
            Management recommendations with timing and prevention

        Validates: AC10.3 - Pest management recommendations with organic and chemical options
        """
        try:
            management = PEST_DISEASE_MANAGEMENT.get(pest_disease, {})

            if not management:
                return {
                    "error": f"No management data available for {pest_disease}",
                    "pest_disease": pest_disease,
                }

            result = {
                "pest_disease": pest_disease,
                "timing": management.get("timing", ""),
                "prevention": management.get("prevention", []),
            }

            if preference in ["organic", "both"]:
                result["organic_options"] = management.get("organic", [])

            if preference in ["chemical", "both"]:
                result["chemical_options"] = management.get("chemical", [])

            return result

        except Exception as e:
            logger.error(f"Error getting management recommendations for {pest_disease}: {e}")
            raise

    async def monitor_crops_for_risks(
        self,
        weather_service,  # Type hint removed to avoid circular import
        milestone_service,  # Type hint removed to avoid circular import
    ) -> Dict[str, Any]:
        """
        Background job to monitor all active crops for pest/disease risks

        Args:
            weather_service: Weather service instance
            milestone_service: Crop milestone service instance

        Returns:
            Summary of monitoring results

        Validates: AC10.3 - Automated pest/disease monitoring
        """
        try:
            summary = {"crops_checked": 0, "risks_detected": 0, "alerts_sent": 0, "errors": 0}

            # Get all active crops (not harvested). crops.status values are planned/planted/growing/harvested,
            # so "active" means planted or growing. Farm location and farmer contact come from joins.
            active_crops = fetch_all(
                """SELECT c.*, p.farm_id AS farm_id, f.latitude AS farm_latitude, f.longitude AS farm_longitude,
                          u.phone AS farmer_phone, u.email AS farmer_email, u.name AS farmer_name
                   FROM crops c
                   JOIN farm_plots p ON p.id = c.farm_plot_id
                   JOIN farms f ON f.id = p.farm_id
                   LEFT JOIN users u ON u.id = f.user_id
                   WHERE c.status IN ('active', 'planted', 'growing')
                     AND (c.expected_harvest_date IS NULL OR c.expected_harvest_date >= ?)""",
                [datetime.now().date()],
            )
            for crop in active_crops:
                crop.farm = Row(
                    latitude=crop.farm_latitude or 0.0, longitude=crop.farm_longitude or 0.0
                )
                crop.farmer = Row(
                    phone=crop.farmer_phone or "",
                    email=crop.farmer_email,
                    name=crop.farmer_name or "Farmer",
                )

            for crop in active_crops:
                try:
                    summary["crops_checked"] += 1

                    # Get current weather for crop location
                    weather_data = await weather_service.get_current_weather(
                        latitude=crop.farm.latitude if hasattr(crop, "farm") else 0.0,
                        longitude=crop.farm.longitude if hasattr(crop, "farm") else 0.0,
                    )

                    if not weather_data:
                        logger.warning(f"No weather data for crop {crop.id}")
                        continue

                    # Get current growth stage
                    current_stage_data = await milestone_service.get_current_stage(crop.id)
                    if not current_stage_data:
                        logger.warning(f"No growth stage data for crop {crop.id}")
                        continue

                    current_stage = current_stage_data.get("stage", "vegetative")

                    # Check for risks
                    risks = await self.check_pest_disease_risk(
                        crop_id=crop.id, weather_data=weather_data, current_stage=current_stage
                    )

                    if risks:
                        summary["risks_detected"] += len(risks)

                        # Send alerts for high severity risks
                        for risk in risks:
                            if risk["severity"] in ["high", "medium"]:
                                await self.send_pest_disease_alert(
                                    crop_id=crop.id,
                                    farmer_phone=(
                                        crop.farmer.phone if hasattr(crop, "farmer") else ""
                                    ),
                                    farmer_email=(
                                        crop.farmer.email if hasattr(crop, "farmer") else None
                                    ),
                                    farmer_name=(
                                        crop.farmer.name if hasattr(crop, "farmer") else "Farmer"
                                    ),
                                    crop_name=crop.crop_name,
                                    risk=risk,
                                )
                                summary["alerts_sent"] += 1

                except Exception as e:
                    logger.error(f"Error monitoring crop {crop.id}: {e}")
                    summary["errors"] += 1

            logger.info(f"Pest/disease monitoring completed: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error in pest/disease monitoring job: {e}")
            return {"error": str(e)}

    async def send_pest_disease_alert(
        self,
        crop_id: int,
        farmer_phone: str,
        farmer_email: Optional[str],
        farmer_name: str,
        crop_name: str,
        risk: Dict[str, Any],
        alert_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Send pest/disease alert to farmer

        Args:
            crop_id: Crop ID
            farmer_phone: Farmer's phone number
            farmer_email: Farmer's email (optional)
            farmer_name: Farmer's name
            crop_name: Name of the crop
            risk: Risk details
            alert_id: Alert ID to mark as notified (optional)

        Returns:
            Notification result

        Validates: AC10.3 - Early warning alerts via SNS
        """
        try:
            pest_disease = risk["pest_disease"].replace("_", " ").title()
            severity = risk["severity"].upper()

            # Format action items from management recommendations
            management = risk.get("management", {})
            action_items = []

            # Add organic options first
            organic = management.get("organic", [])
            if organic:
                action_items.append(f"Organic: {organic[0]}")

            # Add chemical option
            chemical = management.get("chemical", [])
            if chemical:
                action_items.append(f"Chemical: {chemical[0]}")

            # Add timing
            timing = management.get("timing", "")
            if timing:
                action_items.append(f"Timing: {timing}")

            # Add prevention tip
            prevention = management.get("prevention", [])
            if prevention:
                action_items.append(f"Prevention: {prevention[0]}")

            # Send notification
            result = self.notification_service.send_strategy_reminder(
                farmer_phone=farmer_phone,
                farmer_email=farmer_email,
                farmer_name=farmer_name,
                strategy_id=f"crop_{crop_id}_pest_alert",
                reminder_type=f"{severity}_RISK_{pest_disease}",
                action_items=action_items[:5],  # Limit to 5 items
                due_date=None,
            )

            # Mark alert as notified in database
            if alert_id:
                try:
                    alert = fetch_one(
                        """UPDATE pest_disease_alerts SET notification_sent = 1, notification_sent_at = ?,
                           updated_at = CURRENT_TIMESTAMP WHERE id = ? RETURNING id""",
                        [datetime.now(), alert_id],
                    )
                    if alert:
                        logger.info(f"Marked alert {alert_id} as notified")
                except Exception as e:
                    logger.error(f"Error marking alert as notified: {e}")

            logger.info(f"Pest/disease alert sent for crop {crop_id} - {pest_disease}")
            return result

        except Exception as e:
            logger.error(f"Error sending pest/disease alert: {e}")
            return {"success": False, "error": str(e)}

    async def get_crop_specific_risks(
        self, crop_name: str, current_stage: str
    ) -> List[Dict[str, Any]]:
        """
        Get common pest/disease risks for specific crop and stage

        Args:
            crop_name: Name of the crop
            current_stage: Current growth stage

        Returns:
            List of common risks for this crop and stage

        Validates: AC10.3 - Crop-specific pest/disease information
        """
        try:
            # Filter risks by stage
            relevant_risks = []

            for pest_disease, thresholds in PEST_DISEASE_THRESHOLDS.items():
                if current_stage in thresholds.get("risk_stages", []):
                    risk_info = {
                        "pest_disease": pest_disease,
                        "severity": thresholds["severity"],
                        "description": thresholds["description"],
                        "risk_stages": thresholds["risk_stages"],
                        "management": PEST_DISEASE_MANAGEMENT.get(pest_disease, {}),
                    }
                    relevant_risks.append(risk_info)

            return relevant_risks

        except Exception as e:
            logger.error(f"Error getting crop-specific risks: {e}")
            raise

    async def get_prevention_guidance(self, crop_id: int, current_stage: str) -> Dict[str, Any]:
        """
        Get disease prevention guidance for current crop stage

        Args:
            crop_id: Crop ID
            current_stage: Current growth stage

        Returns:
            Prevention guidance with timing and application instructions

        Validates: AC10.3 - Disease prevention guidance
        """
        try:
            # Get relevant risks for this stage
            relevant_risks = []

            for pest_disease, thresholds in PEST_DISEASE_THRESHOLDS.items():
                if current_stage in thresholds.get("risk_stages", []):
                    relevant_risks.append(pest_disease)

            # Compile prevention measures
            prevention_measures = []
            timing_instructions = []

            for pest_disease in relevant_risks:
                management = PEST_DISEASE_MANAGEMENT.get(pest_disease, {})

                # Add prevention measures
                prevention = management.get("prevention", [])
                for measure in prevention:
                    if measure not in prevention_measures:
                        prevention_measures.append(measure)

                # Add timing
                timing = management.get("timing", "")
                if timing and timing not in timing_instructions:
                    timing_instructions.append(
                        f"{pest_disease.replace('_', ' ').title()}: {timing}"
                    )

            return {
                "crop_id": crop_id,
                "current_stage": current_stage,
                "relevant_risks": relevant_risks,
                "prevention_measures": prevention_measures,
                "timing_instructions": timing_instructions,
                "general_guidance": [
                    "Monitor crops regularly for early detection",
                    "Maintain field sanitation and remove crop debris",
                    "Ensure proper plant spacing for air circulation",
                    "Use disease-resistant varieties when available",
                    "Practice crop rotation to break pest cycles",
                    "Maintain optimal soil health and plant nutrition",
                ],
            }

        except Exception as e:
            logger.error(f"Error getting prevention guidance for crop {crop_id}: {e}")
            raise


def get_pest_disease_service(db: AsyncSession) -> PestDiseaseService:
    """Get pest disease service instance"""
    return PestDiseaseService(db)
