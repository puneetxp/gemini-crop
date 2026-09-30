"""
Livestock Health Record Service
Handles health record management, vaccination schedules, and health reports
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.orm.livestock import Livestock
from app.orm.livestock_health_record import LivestockHealthRecord

logger = logging.getLogger(__name__)


class LivestockHealthService:
    """Service for managing livestock health records"""

    # Standard vaccination schedules by species (in months)
    VACCINATION_SCHEDULES = {
        "cattle": [
            {
                "name": "FMD (Foot and Mouth Disease)",
                "age_months": [2, 6, 12],
                "frequency_months": 6,
            },
            {"name": "HS (Hemorrhagic Septicemia)", "age_months": [4, 10], "frequency_months": 6},
            {"name": "BQ (Black Quarter)", "age_months": [4, 10], "frequency_months": 6},
            {"name": "Brucellosis", "age_months": [4], "frequency_months": None},
            {"name": "Anthrax", "age_months": [6], "frequency_months": 12},
        ],
        "buffalo": [
            {
                "name": "FMD (Foot and Mouth Disease)",
                "age_months": [2, 6, 12],
                "frequency_months": 6,
            },
            {"name": "HS (Hemorrhagic Septicemia)", "age_months": [4, 10], "frequency_months": 6},
            {"name": "BQ (Black Quarter)", "age_months": [4, 10], "frequency_months": 6},
            {"name": "Brucellosis", "age_months": [4], "frequency_months": None},
        ],
        "goat": [
            {
                "name": "PPR (Peste des Petits Ruminants)",
                "age_months": [3, 9],
                "frequency_months": 12,
            },
            {"name": "FMD (Foot and Mouth Disease)", "age_months": [3, 9], "frequency_months": 6},
            {"name": "HS (Hemorrhagic Septicemia)", "age_months": [4], "frequency_months": 6},
            {"name": "Enterotoxaemia", "age_months": [2, 6], "frequency_months": 6},
        ],
        "poultry": [
            {"name": "Marek's Disease", "age_months": [0], "frequency_months": None},
            {"name": "Newcastle Disease", "age_months": [0.5, 2, 4], "frequency_months": 4},
            {
                "name": "Infectious Bursal Disease (IBD)",
                "age_months": [0.5, 1],
                "frequency_months": None,
            },
            {"name": "Fowl Pox", "age_months": [2], "frequency_months": 12},
        ],
    }

    def __init__(self):
        """Initialize the health service"""
        self.health_record_model = LivestockHealthRecord()
        self.livestock_model = Livestock()

    def create_health_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new health record

        Args:
            record_data: Health record data

        Returns:
            Created health record
        """
        try:
            # Verify livestock exists
            livestock = self.livestock_model.find(record_data["livestock_id"])
            if not livestock:
                raise ValueError(f"Livestock with ID {record_data['livestock_id']} not found")

            # Create health record
            result = self.health_record_model.create(record_data).get_inserted()

            logger.info(
                f"Created health record {result['id']} for livestock {record_data['livestock_id']}"
            )

            return result

        except Exception as e:
            logger.error(f"Error creating health record: {str(e)}")
            raise

    def get_health_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get health record by ID

        Args:
            record_id: Health record ID

        Returns:
            Health record or None
        """
        try:
            return self.health_record_model.find(record_id)
        except Exception as e:
            logger.error(f"Error fetching health record {record_id}: {str(e)}")
            raise

    def update_health_record(
        self, record_id: int, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update health record

        Args:
            record_id: Health record ID
            update_data: Fields to update

        Returns:
            Updated health record or None
        """
        try:
            # Check if record exists
            existing = self.health_record_model.find(record_id)
            if not existing:
                return None

            # Update record
            self.health_record_model.update(record_id, update_data)

            # Fetch updated record
            result = self.health_record_model.find(record_id)

            logger.info(f"Updated health record {record_id}")

            return result

        except Exception as e:
            logger.error(f"Error updating health record {record_id}: {str(e)}")
            raise

    def delete_health_record(self, record_id: int) -> bool:
        """
        Delete health record (soft delete)

        Args:
            record_id: Health record ID

        Returns:
            True if deleted, False if not found
        """
        try:
            existing = self.health_record_model.find(record_id)
            if not existing:
                return False

            self.health_record_model.delete(record_id)

            logger.info(f"Deleted health record {record_id}")

            return True

        except Exception as e:
            logger.error(f"Error deleting health record {record_id}: {str(e)}")
            raise

    def list_health_records(
        self,
        livestock_id: Optional[int] = None,
        record_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List health records with filters

        Args:
            livestock_id: Filter by livestock ID
            record_type: Filter by record type
            start_date: Filter by start date
            end_date: Filter by end date
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of health records
        """
        try:
            # Build query
            query = self.health_record_model

            if livestock_id:
                query = query.where({"livestock_id": livestock_id})

            if record_type:
                query = query.and_where({"record_type": record_type.lower()})

            # Execute query
            result = query.get()
            all_records = result.to_dict() if result else []

            # Apply date filters
            if start_date or end_date:
                filtered_records = []
                for record in all_records:
                    record_date = record["record_date"]
                    if isinstance(record_date, str):
                        record_date = datetime.strptime(record_date, "%Y-%m-%d").date()

                    if start_date and record_date < start_date:
                        continue
                    if end_date and record_date > end_date:
                        continue

                    filtered_records.append(record)

                all_records = filtered_records

            # Sort by record_date descending (most recent first)
            all_records.sort(key=lambda x: x["record_date"], reverse=True)

            # Apply pagination
            return all_records[skip : skip + limit]

        except Exception as e:
            logger.error(f"Error listing health records: {str(e)}")
            raise

    def get_vaccination_schedule(self, livestock_id: int) -> Dict[str, Any]:
        """
        Get vaccination schedule for livestock

        Args:
            livestock_id: Livestock ID

        Returns:
            Vaccination schedule with upcoming, completed, and overdue vaccinations
        """
        try:
            # Get livestock details
            livestock = self.livestock_model.find(livestock_id)
            if not livestock:
                raise ValueError(f"Livestock with ID {livestock_id} not found")

            species = livestock["species"].lower()
            purchase_date = livestock["purchase_date"]
            if isinstance(purchase_date, str):
                purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d").date()

            # Calculate current age in months
            current_age_months = (date.today() - purchase_date).days // 30

            # Get vaccination schedule for species
            schedule = self.VACCINATION_SCHEDULES.get(species, [])

            # Get completed vaccinations
            completed_records = self.list_health_records(
                livestock_id=livestock_id, record_type="vaccination", limit=1000
            )

            completed_vaccinations = []
            for record in completed_records:
                completed_vaccinations.append(
                    {
                        "id": record["id"],
                        "name": record["description"],
                        "date": record["record_date"],
                        "veterinarian": record.get("veterinarian_name"),
                        "cost": float(record["cost"]) if record.get("cost") else None,
                        "next_due_date": record.get("next_due_date"),
                    }
                )

            # Calculate upcoming and overdue vaccinations
            upcoming_vaccinations = []
            overdue_vaccinations = []

            for vaccine in schedule:
                vaccine_name = vaccine["name"]
                age_months_list = vaccine["age_months"]
                frequency_months = vaccine["frequency_months"]

                # Check if this vaccination has been completed
                completed = any(
                    vaccine_name.lower() in rec["name"].lower() for rec in completed_vaccinations
                )

                # Find the next due age
                next_due_age = None
                for age in age_months_list:
                    if age > current_age_months:
                        next_due_age = age
                        break

                # If no specific age found and has frequency, calculate based on last vaccination
                if next_due_age is None and frequency_months and completed:
                    # Find last vaccination of this type
                    last_vaccination = None
                    for rec in completed_vaccinations:
                        if vaccine_name.lower() in rec["name"].lower():
                            if last_vaccination is None or rec["date"] > last_vaccination["date"]:
                                last_vaccination = rec

                    if last_vaccination:
                        last_date = last_vaccination["date"]
                        if isinstance(last_date, str):
                            last_date = datetime.strptime(last_date, "%Y-%m-%d").date()

                        next_due_date = last_date + timedelta(days=frequency_months * 30)

                        vaccination_info = {
                            "name": vaccine_name,
                            "due_date": next_due_date,
                            "days_until_due": (next_due_date - date.today()).days,
                            "frequency_months": frequency_months,
                        }

                        if next_due_date < date.today():
                            overdue_vaccinations.append(vaccination_info)
                        else:
                            upcoming_vaccinations.append(vaccination_info)

                # If not completed and has a due age
                elif next_due_age is not None:
                    due_date = purchase_date + timedelta(days=next_due_age * 30)

                    vaccination_info = {
                        "name": vaccine_name,
                        "due_date": due_date,
                        "due_age_months": next_due_age,
                        "days_until_due": (due_date - date.today()).days,
                    }

                    if due_date < date.today():
                        overdue_vaccinations.append(vaccination_info)
                    else:
                        upcoming_vaccinations.append(vaccination_info)

            # Sort by due date
            upcoming_vaccinations.sort(key=lambda x: x["due_date"])
            overdue_vaccinations.sort(key=lambda x: x["due_date"])

            return {
                "livestock_id": livestock_id,
                "species": species,
                "age_months": current_age_months,
                "upcoming_vaccinations": upcoming_vaccinations,
                "completed_vaccinations": completed_vaccinations,
                "overdue_vaccinations": overdue_vaccinations,
            }

        except Exception as e:
            logger.error(
                f"Error getting vaccination schedule for livestock {livestock_id}: {str(e)}"
            )
            raise

    def generate_health_report(self, livestock_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive health report for livestock

        Args:
            livestock_id: Livestock ID

        Returns:
            Comprehensive health report
        """
        try:
            # Get livestock details
            livestock = self.livestock_model.find(livestock_id)
            if not livestock:
                raise ValueError(f"Livestock with ID {livestock_id} not found")

            # Get all health records
            all_records = self.list_health_records(livestock_id=livestock_id, limit=1000)

            # Categorize records by type
            vaccinations = []
            treatments = []
            checkups = []
            observations = []

            total_cost = Decimal("0")
            last_checkup_date = None

            for record in all_records:
                record_type = record["record_type"].lower()

                if record_type == "vaccination":
                    vaccinations.append(record)
                elif record_type == "treatment":
                    treatments.append(record)
                elif record_type == "checkup":
                    checkups.append(record)
                    # Track last checkup date
                    checkup_date = record["record_date"]
                    if isinstance(checkup_date, str):
                        checkup_date = datetime.strptime(checkup_date, "%Y-%m-%d").date()
                    if last_checkup_date is None or checkup_date > last_checkup_date:
                        last_checkup_date = checkup_date
                elif record_type == "observation":
                    observations.append(record)

                # Add to total cost
                if record.get("cost"):
                    total_cost += Decimal(str(record["cost"]))

            # Get vaccination schedule
            vaccination_schedule = self.get_vaccination_schedule(livestock_id)

            # Generate health summary
            health_summary = self._generate_health_summary(
                livestock, vaccinations, treatments, checkups, vaccination_schedule
            )

            return {
                "livestock_id": livestock_id,
                "species": livestock["species"],
                "breed": livestock["breed"],
                "total_records": len(all_records),
                "vaccinations": vaccinations,
                "treatments": treatments,
                "checkups": checkups,
                "observations": observations,
                "total_health_cost": total_cost,
                "last_checkup_date": last_checkup_date,
                "upcoming_vaccinations": vaccination_schedule["upcoming_vaccinations"],
                "health_summary": health_summary,
            }

        except Exception as e:
            logger.error(f"Error generating health report for livestock {livestock_id}: {str(e)}")
            raise

    def _generate_health_summary(
        self,
        livestock: Dict[str, Any],
        vaccinations: List[Dict[str, Any]],
        treatments: List[Dict[str, Any]],
        checkups: List[Dict[str, Any]],
        vaccination_schedule: Dict[str, Any],
    ) -> str:
        """
        Generate health summary text

        Args:
            livestock: Livestock data
            vaccinations: List of vaccination records
            treatments: List of treatment records
            checkups: List of checkup records
            vaccination_schedule: Vaccination schedule data

        Returns:
            Health summary text
        """
        summary_parts = []

        # Basic info
        species = livestock["species"].capitalize()
        breed = livestock["breed"]
        summary_parts.append(f"{species} ({breed})")

        # Vaccination status
        overdue_count = len(vaccination_schedule["overdue_vaccinations"])
        upcoming_count = len(vaccination_schedule["upcoming_vaccinations"])
        completed_count = len(vaccination_schedule["completed_vaccinations"])

        if overdue_count > 0:
            summary_parts.append(f"⚠️ {overdue_count} overdue vaccination(s)")
        elif upcoming_count > 0:
            summary_parts.append(
                f"✓ {completed_count} vaccination(s) completed, {upcoming_count} upcoming"
            )
        else:
            summary_parts.append(f"✓ All vaccinations up to date ({completed_count} completed)")

        # Recent treatments
        if treatments:
            recent_treatments = [
                t for t in treatments if self._is_recent(t["record_date"], days=30)
            ]
            if recent_treatments:
                summary_parts.append(f"⚕️ {len(recent_treatments)} treatment(s) in last 30 days")

        # Last checkup
        if checkups:
            last_checkup = max(checkups, key=lambda x: x["record_date"])
            days_since = (date.today() - self._parse_date(last_checkup["record_date"])).days
            if days_since > 180:
                summary_parts.append(f"⚠️ Last checkup {days_since} days ago - checkup recommended")
            else:
                summary_parts.append(f"✓ Last checkup {days_since} days ago")
        else:
            summary_parts.append("⚠️ No checkup records - checkup recommended")

        return " | ".join(summary_parts)

    def _is_recent(self, record_date: Any, days: int = 30) -> bool:
        """Check if a date is within the last N days"""
        if isinstance(record_date, str):
            record_date = datetime.strptime(record_date, "%Y-%m-%d").date()
        return (date.today() - record_date).days <= days

    def _parse_date(self, date_value: Any) -> date:
        """Parse date from various formats"""
        if isinstance(date_value, str):
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        return date_value


# Singleton instance
_health_service_instance = None


def get_health_service() -> LivestockHealthService:
    """Get singleton instance of health service"""
    global _health_service_instance
    if _health_service_instance is None:
        _health_service_instance = LivestockHealthService()
    return _health_service_instance
