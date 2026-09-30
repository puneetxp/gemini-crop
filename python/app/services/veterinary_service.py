"""
Veterinary Services Integration
Task 28.2: Build veterinary services integration

Provides:
- Symptom checker for livestock ailments
- AI triage system for health issues (low/medium/high severity)
- Remote diagnosis and treatment recommendations
- Telemedicine integration framework (placeholder for partnerships)
"""

import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.orm.livestock import Livestock
from app.orm.livestock_health_record import LivestockHealthRecord
from app.services.bedrock_service import bedrock_service
from app.services.veterinarian_directory_service import get_veterinarian_directory_service

logger = logging.getLogger(__name__)


class VeterinaryService:
    """Service for veterinary services and health diagnostics"""

    # Common livestock diseases database
    DISEASE_DATABASE = {
        "cattle": [
            {
                "name": "Foot and Mouth Disease (FMD)",
                "symptoms": [
                    "fever",
                    "blisters_mouth",
                    "blisters_feet",
                    "drooling",
                    "lameness",
                    "reduced_appetite",
                ],
                "severity": "high",
                "contagious": True,
                "treatment": "Immediate veterinary care, isolation, supportive treatment",
            },
            {
                "name": "Mastitis",
                "symptoms": [
                    "swollen_udder",
                    "hot_udder",
                    "reduced_milk",
                    "abnormal_milk",
                    "fever",
                ],
                "severity": "medium",
                "contagious": False,
                "treatment": "Antibiotics, anti-inflammatory drugs, proper milking hygiene",
            },
            {
                "name": "Bloat",
                "symptoms": [
                    "distended_abdomen",
                    "difficulty_breathing",
                    "restlessness",
                    "reduced_appetite",
                ],
                "severity": "high",
                "contagious": False,
                "treatment": "Emergency treatment, stomach tube, trocar and cannula if severe",
            },
            {
                "name": "Diarrhea",
                "symptoms": ["loose_stool", "dehydration", "weakness", "reduced_appetite"],
                "severity": "medium",
                "contagious": True,
                "treatment": "Oral rehydration, antibiotics if bacterial, dietary management",
            },
            {
                "name": "Pneumonia",
                "symptoms": [
                    "coughing",
                    "nasal_discharge",
                    "fever",
                    "difficulty_breathing",
                    "reduced_appetite",
                ],
                "severity": "high",
                "contagious": True,
                "treatment": "Antibiotics, anti-inflammatory drugs, supportive care",
            },
        ],
        "buffalo": [
            {
                "name": "Hemorrhagic Septicemia (HS)",
                "symptoms": [
                    "high_fever",
                    "swelling_throat",
                    "difficulty_breathing",
                    "sudden_death",
                ],
                "severity": "high",
                "contagious": True,
                "treatment": "Emergency antibiotics, supportive treatment, vaccination prevention",
            },
            {
                "name": "Mastitis",
                "symptoms": ["swollen_udder", "hot_udder", "reduced_milk", "abnormal_milk"],
                "severity": "medium",
                "contagious": False,
                "treatment": "Antibiotics, proper milking hygiene",
            },
        ],
        "goat": [
            {
                "name": "PPR (Peste des Petits Ruminants)",
                "symptoms": ["fever", "nasal_discharge", "diarrhea", "mouth_sores", "coughing"],
                "severity": "high",
                "contagious": True,
                "treatment": "Supportive care, antibiotics for secondary infections, vaccination",
            },
            {
                "name": "Enterotoxaemia",
                "symptoms": ["sudden_death", "diarrhea", "abdominal_pain", "convulsions"],
                "severity": "high",
                "contagious": False,
                "treatment": "Emergency antitoxin, antibiotics, vaccination prevention",
            },
            {
                "name": "Pneumonia",
                "symptoms": ["coughing", "nasal_discharge", "fever", "difficulty_breathing"],
                "severity": "medium",
                "contagious": True,
                "treatment": "Antibiotics, supportive care",
            },
        ],
        "poultry": [
            {
                "name": "Newcastle Disease",
                "symptoms": [
                    "respiratory_distress",
                    "diarrhea",
                    "nervous_signs",
                    "reduced_egg_production",
                    "sudden_death",
                ],
                "severity": "high",
                "contagious": True,
                "treatment": "No specific treatment, vaccination prevention, supportive care",
            },
            {
                "name": "Fowl Pox",
                "symptoms": ["skin_lesions", "reduced_appetite", "reduced_egg_production"],
                "severity": "medium",
                "contagious": True,
                "treatment": "Supportive care, vaccination prevention",
            },
        ],
    }

    def __init__(self):
        """Initialize veterinary service"""
        self.bedrock = bedrock_service
        self.livestock_model = Livestock()
        self.health_record_model = LivestockHealthRecord()

    def check_symptoms(
        self,
        livestock_id: int,
        symptoms: List[str],
        duration_days: int,
        additional_info: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check symptoms against disease database and provide AI-powered diagnosis

        Args:
            livestock_id: Livestock ID
            symptoms: List of observed symptoms
            duration_days: How long symptoms have been present
            additional_info: Additional observations or context

        Returns:
            Symptom check results with possible diseases and recommendations
        """
        try:
            # Get livestock details
            livestock = self.livestock_model.find(livestock_id)
            if not livestock:
                raise ValueError(f"Livestock with ID {livestock_id} not found")

            species = livestock["species"].lower()
            breed = livestock["breed"]
            age_months = self._calculate_age_months(livestock["purchase_date"])

            # Match symptoms against disease database
            possible_diseases = self._match_symptoms_to_diseases(species, symptoms)

            # Get AI-powered diagnosis from Bedrock
            ai_diagnosis = self._get_ai_diagnosis(
                species=species,
                breed=breed,
                age_months=age_months,
                symptoms=symptoms,
                duration_days=duration_days,
                additional_info=additional_info,
                possible_diseases=possible_diseases,
            )

            # Perform triage assessment
            triage_result = self._perform_triage(
                symptoms=symptoms,
                duration_days=duration_days,
                possible_diseases=possible_diseases,
                ai_diagnosis=ai_diagnosis,
            )

            logger.info(
                f"Symptom check completed for livestock {livestock_id}, severity: {triage_result['severity']}"
            )

            return {
                "livestock_id": livestock_id,
                "species": species,
                "breed": breed,
                "symptoms_reported": symptoms,
                "duration_days": duration_days,
                "possible_diseases": possible_diseases,
                "ai_diagnosis": ai_diagnosis,
                "triage": triage_result,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error checking symptoms for livestock {livestock_id}: {str(e)}")
            raise

    def _match_symptoms_to_diseases(
        self, species: str, symptoms: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Match reported symptoms to diseases in database

        Args:
            species: Livestock species
            symptoms: List of symptoms

        Returns:
            List of possible diseases with match scores
        """
        diseases = self.DISEASE_DATABASE.get(species, [])
        matches = []

        for disease in diseases:
            disease_symptoms = set(disease["symptoms"])
            reported_symptoms = set(symptoms)

            # Calculate match score
            matching_symptoms = disease_symptoms.intersection(reported_symptoms)
            match_score = len(matching_symptoms) / len(disease_symptoms) if disease_symptoms else 0

            if match_score > 0:
                matches.append(
                    {
                        "disease_name": disease["name"],
                        "match_score": round(match_score, 2),
                        "matching_symptoms": list(matching_symptoms),
                        "severity": disease["severity"],
                        "contagious": disease["contagious"],
                        "treatment": disease["treatment"],
                    }
                )

        # Sort by match score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches

    def _get_ai_diagnosis(
        self,
        species: str,
        breed: str,
        age_months: int,
        symptoms: List[str],
        duration_days: int,
        additional_info: Optional[str],
        possible_diseases: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Get AI-powered diagnosis from Bedrock

        Args:
            species: Livestock species
            breed: Breed
            age_months: Age in months
            symptoms: List of symptoms
            duration_days: Duration of symptoms
            additional_info: Additional information
            possible_diseases: Possible diseases from database matching

        Returns:
            AI diagnosis with recommendations
        """
        # Build disease context from database matches
        disease_context = ""
        if possible_diseases:
            disease_context = "\n\nPossible diseases from symptom matching:\n"
            for disease in possible_diseases[:3]:  # Top 3 matches
                disease_context += f"- {disease['disease_name']} (match: {disease['match_score']*100}%, severity: {disease['severity']})\n"

        prompt = f"""You are an expert veterinarian specializing in livestock health. Analyze the following case:

Animal Details:
- Species: {species}
- Breed: {breed}
- Age: {age_months} months

Symptoms Reported:
{', '.join(symptoms)}

Duration: {duration_days} days
{f"Additional Information: {additional_info}" if additional_info else ""}
{disease_context}

Provide a comprehensive veterinary assessment in JSON format:
{{
  "primary_diagnosis": "most likely condition",
  "confidence_level": 0.85,
  "differential_diagnoses": [
    {{
      "condition": "alternative diagnosis",
      "probability": 0.15,
      "distinguishing_factors": "what would confirm this"
    }}
  ],
  "severity_assessment": "low/medium/high",
  "urgency": "routine/urgent/emergency",
  "recommended_actions": [
    {{
      "action": "specific action to take",
      "priority": "immediate/within_24h/within_week",
      "reason": "why this action is needed"
    }}
  ],
  "treatment_recommendations": {{
    "immediate_care": ["action1", "action2"],
    "medications": [
      {{
        "medication": "drug name",
        "dosage": "dosage info",
        "duration": "treatment duration",
        "purpose": "what it treats"
      }}
    ],
    "supportive_care": ["care1", "care2"]
  }},
  "prognosis": {{
    "expected_outcome": "description",
    "recovery_time_days": 7,
    "complications_to_watch": ["complication1", "complication2"]
  }},
  "prevention_advice": ["advice1", "advice2"],
  "veterinary_consultation_needed": true/false,
  "telemedicine_suitable": true/false
}}

Focus on:
- Practical advice for rural farmers
- Cost-effective treatments
- When professional veterinary care is essential
- Prevention strategies

Provide ONLY the JSON response."""

        try:
            response_text = self.bedrock._invoke_claude(prompt, max_tokens=2000, temperature=0.1)

            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                diagnosis = json.loads(json_text)
                return diagnosis
            else:
                logger.warning("Could not parse JSON from Bedrock diagnosis response")
                return self._create_fallback_diagnosis(symptoms, possible_diseases)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in AI diagnosis: {e}")
            return self._create_fallback_diagnosis(symptoms, possible_diseases)
        except Exception as e:
            logger.error(f"Error getting AI diagnosis: {e}")
            return self._create_fallback_diagnosis(symptoms, possible_diseases)

    def _perform_triage(
        self,
        symptoms: List[str],
        duration_days: int,
        possible_diseases: List[Dict[str, Any]],
        ai_diagnosis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Perform AI triage to assess severity and urgency

        Args:
            symptoms: List of symptoms
            duration_days: Duration of symptoms
            possible_diseases: Possible diseases from database
            ai_diagnosis: AI diagnosis from Bedrock

        Returns:
            Triage assessment with severity level and recommendations
        """
        # Emergency symptoms that require immediate attention
        emergency_symptoms = {
            "sudden_death",
            "difficulty_breathing",
            "convulsions",
            "severe_bleeding",
            "bloat",
            "unable_to_stand",
            "high_fever",
            "severe_dehydration",
        }

        # High severity symptoms
        high_severity_symptoms = {
            "fever",
            "diarrhea",
            "coughing",
            "nasal_discharge",
            "swelling_throat",
            "reduced_appetite",
            "lameness",
            "abnormal_milk",
        }

        # Check for emergency symptoms
        has_emergency = any(symptom in emergency_symptoms for symptom in symptoms)

        # Check for high severity diseases
        has_high_severity_disease = any(
            disease["severity"] == "high" and disease["match_score"] > 0.5
            for disease in possible_diseases
        )

        # Get AI assessment
        ai_severity = ai_diagnosis.get("severity_assessment", "medium")
        ai_urgency = ai_diagnosis.get("urgency", "routine")

        # Determine overall severity
        if has_emergency or ai_urgency == "emergency":
            severity = "high"
            urgency = "emergency"
            action = "Seek immediate veterinary care - this is an emergency"
            timeframe = "Immediate (within 1-2 hours)"
        elif has_high_severity_disease or ai_severity == "high" or ai_urgency == "urgent":
            severity = "high"
            urgency = "urgent"
            action = "Contact veterinarian urgently"
            timeframe = "Within 24 hours"
        elif duration_days > 7 or len(symptoms) > 3:
            severity = "medium"
            urgency = "prompt"
            action = "Schedule veterinary consultation"
            timeframe = "Within 2-3 days"
        else:
            severity = "low"
            urgency = "routine"
            action = "Monitor closely and consult if symptoms worsen"
            timeframe = "Within 1 week if no improvement"

        # Check if contagious
        is_contagious = any(disease["contagious"] for disease in possible_diseases)

        triage_result = {
            "severity": severity,
            "urgency": urgency,
            "action_required": action,
            "timeframe": timeframe,
            "veterinary_consultation_needed": ai_diagnosis.get(
                "veterinary_consultation_needed", severity in ["high", "medium"]
            ),
            "isolation_recommended": is_contagious,
            "telemedicine_suitable": ai_diagnosis.get("telemedicine_suitable", severity == "low"),
            "emergency_indicators": [s for s in symptoms if s in emergency_symptoms],
        }

        return triage_result

    def get_remote_diagnosis(
        self,
        livestock_id: int,
        symptoms: List[str],
        duration_days: int,
        temperature_celsius: Optional[float] = None,
        photos: Optional[List[str]] = None,
        additional_info: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive remote diagnosis with treatment recommendations

        Args:
            livestock_id: Livestock ID
            symptoms: List of symptoms
            duration_days: Duration of symptoms
            temperature_celsius: Body temperature if measured
            photos: List of photo URLs (for future image analysis)
            additional_info: Additional observations

        Returns:
            Comprehensive remote diagnosis with treatment plan
        """
        try:
            # Get symptom check results
            symptom_check = self.check_symptoms(
                livestock_id=livestock_id,
                symptoms=symptoms,
                duration_days=duration_days,
                additional_info=additional_info,
            )

            # Get livestock details
            livestock = self.livestock_model.find(livestock_id)

            # Get health history
            health_records = self.health_record_model.where({"livestock_id": livestock_id}).get()
            recent_records = health_records.to_dict() if health_records else []

            # Build comprehensive diagnosis
            diagnosis = {
                "livestock_id": livestock_id,
                "species": livestock["species"],
                "breed": livestock["breed"],
                "symptom_check": symptom_check,
                "vital_signs": {
                    "temperature_celsius": temperature_celsius,
                    "temperature_status": (
                        self._assess_temperature(livestock["species"], temperature_celsius)
                        if temperature_celsius
                        else None
                    ),
                },
                "health_history_summary": self._summarize_health_history(recent_records),
                "treatment_plan": self._create_treatment_plan(symptom_check),
                "follow_up_schedule": self._create_follow_up_schedule(symptom_check["triage"]),
                "cost_estimate": self._estimate_treatment_cost(symptom_check),
                "telemedicine_options": self._get_telemedicine_options(
                    symptom_check["triage"], species=livestock["species"]
                ),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Remote diagnosis completed for livestock {livestock_id}")

            return diagnosis

        except Exception as e:
            logger.error(f"Error getting remote diagnosis for livestock {livestock_id}: {str(e)}")
            raise

    def _assess_temperature(self, species: str, temperature: float) -> str:
        """Assess if temperature is normal, low, or high"""
        normal_ranges = {
            "cattle": (38.0, 39.5),
            "buffalo": (37.5, 39.0),
            "goat": (38.5, 40.0),
            "poultry": (40.5, 42.0),
        }

        range_min, range_max = normal_ranges.get(species, (38.0, 39.5))

        if temperature < range_min:
            return "low (hypothermia)"
        elif temperature > range_max:
            return "high (fever)"
        else:
            return "normal"

    def _summarize_health_history(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize recent health history"""
        if not records:
            return {
                "recent_treatments": 0,
                "recent_vaccinations": 0,
                "last_checkup": None,
                "chronic_conditions": [],
            }

        # Sort by date
        sorted_records = sorted(records, key=lambda x: x["record_date"], reverse=True)
        recent_records = sorted_records[:10]  # Last 10 records

        treatments = [r for r in recent_records if r["record_type"] == "treatment"]
        vaccinations = [r for r in recent_records if r["record_type"] == "vaccination"]
        checkups = [r for r in recent_records if r["record_type"] == "checkup"]

        return {
            "recent_treatments": len(treatments),
            "recent_vaccinations": len(vaccinations),
            "last_checkup": checkups[0]["record_date"] if checkups else None,
            "chronic_conditions": [],  # Could be extracted from notes
        }

    def _create_treatment_plan(self, symptom_check: Dict[str, Any]) -> Dict[str, Any]:
        """Create treatment plan from symptom check results"""
        ai_diagnosis = symptom_check["ai_diagnosis"]
        triage = symptom_check["triage"]

        treatment_recommendations = ai_diagnosis.get("treatment_recommendations", {})

        return {
            "primary_diagnosis": ai_diagnosis.get("primary_diagnosis", "Unknown"),
            "confidence_level": ai_diagnosis.get("confidence_level", 0.5),
            "immediate_actions": treatment_recommendations.get("immediate_care", []),
            "medications": treatment_recommendations.get("medications", []),
            "supportive_care": treatment_recommendations.get("supportive_care", []),
            "dietary_recommendations": self._get_dietary_recommendations(symptom_check),
            "isolation_required": triage["isolation_recommended"],
            "monitoring_instructions": self._create_monitoring_instructions(symptom_check),
            "warning_signs": ai_diagnosis.get("prognosis", {}).get("complications_to_watch", []),
        }

    def _get_dietary_recommendations(self, symptom_check: Dict[str, Any]) -> List[str]:
        """Get dietary recommendations based on condition"""
        symptoms = symptom_check["symptoms_reported"]

        recommendations = []

        if "diarrhea" in symptoms or "loose_stool" in symptoms:
            recommendations.append("Provide easily digestible feed")
            recommendations.append("Ensure constant access to clean water")
            recommendations.append("Consider oral rehydration solution")

        if "reduced_appetite" in symptoms:
            recommendations.append("Offer palatable, high-quality feed")
            recommendations.append("Provide small, frequent meals")
            recommendations.append("Ensure feed is fresh and not moldy")

        if "fever" in symptoms or "high_fever" in symptoms:
            recommendations.append("Increase water intake")
            recommendations.append("Provide cooling environment")

        if not recommendations:
            recommendations.append("Continue normal feeding schedule")
            recommendations.append("Monitor feed intake closely")

        return recommendations

    def _create_monitoring_instructions(self, symptom_check: Dict[str, Any]) -> List[str]:
        """Create monitoring instructions"""
        triage = symptom_check["triage"]

        instructions = [
            "Monitor temperature twice daily",
            "Check appetite and water intake",
            "Observe behavior and activity level",
            "Note any changes in symptoms",
        ]

        if triage["severity"] == "high":
            instructions.extend(
                [
                    "Check vital signs every 4-6 hours",
                    "Keep detailed log of all observations",
                    "Contact veterinarian immediately if condition worsens",
                ]
            )

        return instructions

    def _create_follow_up_schedule(self, triage: Dict[str, Any]) -> Dict[str, Any]:
        """Create follow-up schedule based on triage"""
        severity = triage["severity"]

        if severity == "high":
            return {
                "first_follow_up": "24 hours",
                "subsequent_follow_ups": "Daily until improvement",
                "veterinary_recheck": "Within 3-5 days",
                "expected_improvement_timeline": "3-7 days",
            }
        elif severity == "medium":
            return {
                "first_follow_up": "2-3 days",
                "subsequent_follow_ups": "Every 3-5 days",
                "veterinary_recheck": "Within 1 week if no improvement",
                "expected_improvement_timeline": "5-10 days",
            }
        else:
            return {
                "first_follow_up": "1 week",
                "subsequent_follow_ups": "As needed",
                "veterinary_recheck": "Only if symptoms worsen",
                "expected_improvement_timeline": "7-14 days",
            }

    def _estimate_treatment_cost(self, symptom_check: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate treatment costs"""
        ai_diagnosis = symptom_check["ai_diagnosis"]
        triage = symptom_check["triage"]

        # Base costs (in INR)
        consultation_cost = 500 if triage["veterinary_consultation_needed"] else 0
        medication_cost = 0

        medications = ai_diagnosis.get("treatment_recommendations", {}).get("medications", [])
        medication_cost = len(medications) * 200  # Rough estimate per medication

        supportive_care_cost = 100  # Basic supportive care supplies

        total_estimated_cost = consultation_cost + medication_cost + supportive_care_cost

        return {
            "consultation_fee": consultation_cost,
            "medications": medication_cost,
            "supportive_care": supportive_care_cost,
            "total_estimated": total_estimated_cost,
            "currency": "INR",
            "note": "Costs are estimates and may vary by location and veterinarian",
        }

    def _get_telemedicine_options(
        self, triage: Dict[str, Any], species: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get nearby/available doctors from the veterinarian directory who can be called or messaged"""
        doctors = []
        if triage["telemedicine_suitable"]:
            doctors = get_veterinarian_directory_service().search(
                species=species, available_only=True, limit=5
            )

        return {
            "available": triage["telemedicine_suitable"] and len(doctors) > 0,
            "recommended": triage["severity"] == "low",
            "doctors": doctors,
            "note": "Doctors are added by farmers or admins to the directory. Add one if none are listed for your area.",
        }

    def _create_fallback_diagnosis(
        self, symptoms: List[str], possible_diseases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create fallback diagnosis when AI fails"""
        primary_disease = possible_diseases[0] if possible_diseases else None

        return {
            "primary_diagnosis": (
                primary_disease["disease_name"] if primary_disease else "Unknown condition"
            ),
            "confidence_level": 0.5,
            "differential_diagnoses": [],
            "severity_assessment": primary_disease["severity"] if primary_disease else "medium",
            "urgency": (
                "urgent" if primary_disease and primary_disease["severity"] == "high" else "routine"
            ),
            "recommended_actions": [
                {
                    "action": "Consult veterinarian for proper diagnosis",
                    "priority": "within_24h",
                    "reason": "Professional assessment needed",
                }
            ],
            "treatment_recommendations": {
                "immediate_care": ["Keep animal comfortable", "Ensure access to water"],
                "medications": [],
                "supportive_care": ["Monitor closely", "Isolate if contagious"],
            },
            "prognosis": {
                "expected_outcome": "Depends on proper diagnosis and treatment",
                "recovery_time_days": 7,
                "complications_to_watch": ["Worsening symptoms", "Spread to other animals"],
            },
            "prevention_advice": ["Maintain vaccination schedule", "Practice good hygiene"],
            "veterinary_consultation_needed": True,
            "telemedicine_suitable": False,
        }

    def _calculate_age_months(self, purchase_date: Any) -> int:
        """Calculate age in months from purchase date"""
        if isinstance(purchase_date, str):
            purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d").date()

        age_days = (date.today() - purchase_date).days
        return age_days // 30

    def save_diagnosis_record(
        self, livestock_id: int, diagnosis: Dict[str, Any], veterinarian_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save diagnosis as health record

        Args:
            livestock_id: Livestock ID
            diagnosis: Diagnosis results
            veterinarian_name: Veterinarian name if consulted

        Returns:
            Created health record
        """
        try:
            # Create health record
            record_data = {
                "livestock_id": livestock_id,
                "record_type": "checkup",
                "record_date": date.today(),
                "description": f"Remote diagnosis: {diagnosis['treatment_plan']['primary_diagnosis']}",
                "veterinarian_name": veterinarian_name,
                "notes": json.dumps(
                    {
                        "symptoms": diagnosis["symptom_check"]["symptoms_reported"],
                        "severity": diagnosis["symptom_check"]["triage"]["severity"],
                        "treatment_plan": diagnosis["treatment_plan"],
                    }
                ),
            }

            result = self.health_record_model.create(record_data)

            logger.info(f"Saved diagnosis record {result['id']} for livestock {livestock_id}")

            return result

        except Exception as e:
            logger.error(f"Error saving diagnosis record: {str(e)}")
            raise


# Singleton instance
_veterinary_service_instance = None


def get_veterinary_service() -> VeterinaryService:
    """Get singleton instance of veterinary service"""
    global _veterinary_service_instance
    if _veterinary_service_instance is None:
        _veterinary_service_instance = VeterinaryService()
    return _veterinary_service_instance


# Export singleton
veterinary_service = get_veterinary_service()
