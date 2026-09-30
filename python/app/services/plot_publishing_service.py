"""
Plot Publishing Service
Handles publishing analyzed plots to marketplace for advance reservations

Task 27.1: Plot publishing API implementation
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as AsyncSession
from typing import Dict, Optional

from app.services.farm_access import Row, fetch_one, is_admin
from app.services.plot_analysis_service import PlotAnalysisService

# Rows are farm_access.Row (dict with attribute access); aliases keep the type hints readable.
FarmPlot = Row
User = Row

logger = logging.getLogger(__name__)


class PlotPublishingService:
    """Service for publishing plots to marketplace"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.plot_analysis_service = PlotAnalysisService(db)

    async def publish_plot(
        self,
        plot_id: int,
        crop_name: str,
        crop_variety: str,
        expected_harvest_date: str,
        quantity_quintals: float,
        quality_grade: str,
        price_per_quintal: float,
        farmer_id: int,
        user=None,
    ) -> Dict[str, Any]:
        """
        Publish a plot to marketplace with AI predictions

        Args:
            plot_id: Plot ID to publish
            crop_name: Selected crop name
            crop_variety: Crop variety
            expected_harvest_date: Expected harvest date (ISO format)
            quantity_quintals: Estimated quantity in quintals
            quality_grade: Quality grade (A/B/C)
            price_per_quintal: Asking price per quintal
            farmer_id: Farmer user ID

        Returns:
            Published listing details with AI predictions
        """

        # Get plot details
        plot = await self._get_plot(plot_id)
        if not plot:
            raise ValueError(f"Plot {plot_id} not found")

        # Verify plot belongs to farmer (farm_plots -> farms.user_id); admins may publish any plot.
        # A plot owned by someone else is reported as "not found".
        plot_data = plot
        if not (user is not None and is_admin(user)) and plot_data.farm_user_id != farmer_id:
            raise ValueError(f"Plot {plot_id} not found")

        # Get farmer details
        farmer = await self._get_farmer(farmer_id)
        if not farmer:
            raise ValueError(f"Farmer {farmer_id} not found")

        # Generate AI predictions for the listing
        ai_predictions = await self._generate_ai_predictions(
            plot=plot_data,
            crop_name=crop_name,
            expected_harvest_date=expected_harvest_date,
            quantity_quintals=quantity_quintals,
            quality_grade=quality_grade,
        )

        # Create marketplace listing
        listing = await self._create_marketplace_listing(
            plot=plot_data,
            crop_name=crop_name,
            crop_variety=crop_variety,
            expected_harvest_date=expected_harvest_date,
            quantity_quintals=quantity_quintals,
            quality_grade=quality_grade,
            price_per_quintal=price_per_quintal,
            farmer=farmer,
            ai_predictions=ai_predictions,
        )

        logger.info(f"Published plot {plot_id} to marketplace as listing {listing['listing_id']}")

        return listing

    async def _get_plot(self, plot_id: int) -> Optional[FarmPlot]:
        """Get plot details from database"""
        return fetch_one(
            """SELECT p.*, f.user_id AS farm_user_id FROM farm_plots p
               JOIN farms f ON f.id = p.farm_id WHERE p.id = ?""",
            [plot_id],
        )

    async def _get_farmer(self, farmer_id: int) -> Optional[User]:
        """Get farmer details from database"""
        return fetch_one("SELECT id, name, email, phone FROM users WHERE id = ?", [farmer_id])

    async def _generate_ai_predictions(
        self,
        plot: FarmPlot,
        crop_name: str,
        expected_harvest_date: str,
        quantity_quintals: float,
        quality_grade: str,
    ) -> Dict[str, Any]:
        """
        Generate AI predictions for marketplace listing

        Returns:
            - yield_confidence: Confidence in yield prediction (0-1)
            - quality_confidence: Confidence in quality grade (0-1)
            - harvest_date_range: Predicted harvest window (start, end dates)
        """

        try:
            # Get plot analysis to extract AI predictions
            # Use the season based on harvest date
            harvest_date = datetime.fromisoformat(expected_harvest_date.replace("Z", "+00:00"))
            month = harvest_date.month

            # Determine season from harvest month
            if month in [10, 11, 12]:  # Kharif harvest
                season = "kharif"
            elif month in [3, 4, 5]:  # Rabi harvest
                season = "rabi"
            else:  # Zaid harvest
                season = "zaid"

            # Get AI analysis for this plot and crop
            analysis = await self.plot_analysis_service.analyze_plot(
                plot_id=plot.id,
                season=season,
                budget_per_acre=(
                    float(plot.investment_capacity) if plot.investment_capacity else 20000
                ),
                preferences={},
            )

            # Find the matching crop in recommendations
            crop_data = None
            for crop in analysis.get("recommended_crops", []):
                if crop["crop_name"].lower() == crop_name.lower():
                    crop_data = crop
                    break

            if crop_data:
                # Extract AI predictions from analysis
                yield_confidence = crop_data.get("confidence_score", 0.75)
                quality_confidence = crop_data.get("quality_confidence", 0.80)

                # Calculate harvest date range (±7 days from expected date)
                harvest_start = harvest_date - timedelta(days=7)
                harvest_end = harvest_date + timedelta(days=7)

                return {
                    "yield_confidence": float(yield_confidence),
                    "quality_confidence": float(quality_confidence),
                    "harvest_date_range": {
                        "start": harvest_start.date().isoformat(),
                        "end": harvest_end.date().isoformat(),
                    },
                    "ai_analysis_available": True,
                    "suitability_score": crop_data.get("suitability_score", 7.0),
                    "risk_level": crop_data.get("risk_probability", "medium"),
                }
            else:
                # Fallback predictions if crop not in analysis
                harvest_start = harvest_date - timedelta(days=10)
                harvest_end = harvest_date + timedelta(days=10)

                return {
                    "yield_confidence": 0.70,
                    "quality_confidence": 0.75,
                    "harvest_date_range": {
                        "start": harvest_start.date().isoformat(),
                        "end": harvest_end.date().isoformat(),
                    },
                    "ai_analysis_available": False,
                    "suitability_score": 7.0,
                    "risk_level": "medium",
                }

        except Exception as e:
            logger.warning(f"Could not generate AI predictions: {e}")
            # Fallback predictions
            harvest_date = datetime.fromisoformat(expected_harvest_date.replace("Z", "+00:00"))
            harvest_start = harvest_date - timedelta(days=10)
            harvest_end = harvest_date + timedelta(days=10)

            return {
                "yield_confidence": 0.70,
                "quality_confidence": 0.75,
                "harvest_date_range": {
                    "start": harvest_start.date().isoformat(),
                    "end": harvest_end.date().isoformat(),
                },
                "ai_analysis_available": False,
                "suitability_score": 7.0,
                "risk_level": "medium",
            }

    async def _create_marketplace_listing(
        self,
        plot: FarmPlot,
        crop_name: str,
        crop_variety: str,
        expected_harvest_date: str,
        quantity_quintals: float,
        quality_grade: str,
        price_per_quintal: float,
        farmer: User,
        ai_predictions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create marketplace listing with all details"""

        # Convert quantity from quintals to kg (1 quintal = 100 kg)
        quantity_kg = int(quantity_quintals * 100)

        # Parse harvest date
        harvest_date = datetime.fromisoformat(expected_harvest_date.replace("Z", "+00:00")).date()

        # Create listing record
        listing_data = {
            "farm_id": plot.farm_id,
            "farmer_id": farmer.id,
            "crop_type": crop_name,
            "crop_variety": crop_variety,
            "expected_harvest_date": harvest_date,
            "estimated_quantity": quantity_kg,
            "quality_grade": quality_grade.upper(),
            "location_state": plot.state,
            "location_district": plot.district,
            "farmer_contact_phone": farmer.get(
                "phone"
            ),  # users.phone (there is no phone_number column)
            "farmer_contact_email": farmer.get("email"),
            "status": "published",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "enable": 1,
        }

        # Insert into database
        cols = list(listing_data.keys())
        listing = fetch_one(
            f"INSERT INTO marketplace_listings ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)}) RETURNING *",
            [listing_data[c] for c in cols],
        )

        # Build response with all details
        response = {
            "listing_id": listing.id,
            "plot_id": plot.id,
            "plot_name": plot.plot_name,
            "status": "published",
            "created_at": datetime.now().isoformat(),
            # Crop details
            "crop_details": {
                "crop_name": crop_name,
                "crop_variety": crop_variety,
                "expected_harvest_date": expected_harvest_date,
                "quantity_quintals": quantity_quintals,
                "quantity_kg": quantity_kg,
                "quality_grade": quality_grade.upper(),
                "price_per_quintal": price_per_quintal,
            },
            # Plot characteristics
            "plot_characteristics": {
                "location": {"state": plot.state, "district": plot.district},
                "area_acres": float(plot.area or 0),
                "soil_type": plot.soil_type,
                "irrigation_type": plot.irrigation_type,
                "soil_health_score": None,  # Can be enhanced with soil test data
            },
            # AI predictions
            "ai_predictions": {
                "yield_confidence": ai_predictions["yield_confidence"],
                "quality_confidence": ai_predictions["quality_confidence"],
                "harvest_date_range": ai_predictions["harvest_date_range"],
                "suitability_score": ai_predictions["suitability_score"],
                "risk_level": ai_predictions["risk_level"],
            },
            # Farmer contact
            "farmer_contact": {
                "phone": listing_data["farmer_contact_phone"],
                "email": listing_data["farmer_contact_email"],
            },
            # Offering terms
            "offering_terms": {
                "price_per_quintal": price_per_quintal,
                "total_value": price_per_quintal * quantity_quintals,
                "advance_booking_available": True,
                "minimum_booking_quantity": max(1.0, quantity_quintals * 0.1),  # 10% minimum
            },
        }

        return response
