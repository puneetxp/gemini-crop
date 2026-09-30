"""
Analytics API endpoints
Provides farmer analytics, platform analytics, market analytics, and executive reports
Updated: 2026-03-02
"""

from datetime import datetime, timedelta
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    get_current_active_user,
    get_current_admin,
    get_current_user,
    get_optional_current_user,
)
from app.core.database import get_async_db
from app.core.dependencies import AsyncDB, OptionalUser
from app.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_active_user)]
)


def _ensure_farm_access(farm_id: int, current_user) -> None:
    if getattr(current_user, "user_type", None) == "admin":
        return
    from app.core.db import DB
    from app.core.ownership import owner_condition

    if not DB.raw(
        f"SELECT 1 FROM farms t WHERE t.id = ? AND {owner_condition('farms', current_user.id)}",
        [farm_id],
    ).result:
        raise HTTPException(status_code=404, detail="Farm not found")


def _self_or_admin(user_id, current_user) -> int:
    """Default to the signed-in user; only admins may look at someone else."""
    if user_id is None or user_id == current_user.id:
        return current_user.id
    if getattr(current_user, "user_type", None) != "admin":
        raise HTTPException(status_code=403, detail="You can only view your own analytics")
    return user_id


@router.get("/profile-status")
async def get_profile_status(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_async_db)
):
    """
    Get user profile status - lightweight check for onboarding

    Returns whether user has farms, crops, strategies, or listings
    This is called before loading full dashboard to avoid unnecessary API calls
    """
    try:
        from app.orm.annual_strategy import AnnualStrategy
        from app.orm.buyer_interest import BuyerInterest
        from app.orm.crop import Crop
        from app.orm.farm import Farm
        from app.orm.farm_plot import FarmPlot
        from app.orm.marketplace_listing import MarketplaceListing

        # current_user is a User object, not a dict - access id attribute directly
        user_id = current_user.id
        print(f"Profile Status - User ID: {user_id}, User: {current_user}")

        # Check for farms
        farms_result = Farm.where({"owner_id": [user_id], "is_active": [True]}).get()
        has_farms = len(farms_result.items) > 0
        farms_list = farms_result.items[:6] if has_farms else []

        # Check for plots (crops) - need to get farm IDs first
        has_crops = False
        plots_list = []
        if has_farms:
            farm_ids = [farm["id"] for farm in farms_list]
            plots_result = FarmPlot.where({"farm_id": farm_ids}).get()
            has_crops = len(plots_result.items) > 0
            plots_list = plots_result.items if has_crops else []

        # Check for strategies
        strategies_result = AnnualStrategy.where({"farmer_id": [user_id]}).get()
        has_strategies = len(strategies_result.items) > 0

        # Check for marketplace listings
        listings_result = MarketplaceListing.where(
            {"farmer_id": [user_id], "status": ["active"]}
        ).get()
        has_listings = len(listings_result.items) > 0

        # Helper to normalize date/datetime into ISO strings
        def _to_iso(value):
            if not value:
                return None
            if isinstance(value, datetime):
                return value.isoformat()
            try:
                from datetime import date

                if isinstance(value, date):
                    return value.isoformat()
            except ImportError:
                pass
            return str(value)

        # Get active crops (status: 'planted', 'growing', 'flowering', etc.)
        active_crops = []
        total_profit_potential = 0
        next_expected_harvest = None
        if has_crops:
            plot_ids = [plot["id"] for plot in plots_list]
            crops_result = Crop.where(
                {
                    "farm_plot_id": plot_ids,
                    "status": ["planted", "growing", "flowering", "maturing"],
                }
            ).get()
            raw_crops = crops_result.items if len(crops_result.items) > 0 else []
            for crop in raw_crops:
                planting_date = _to_iso(crop.get("planting_date"))
                expected_harvest_date = _to_iso(crop.get("expected_harvest_date"))

                # Calculate days remaining until harvest if possible
                days_until_harvest = None
                if expected_harvest_date:
                    try:
                        harvest_dt = datetime.fromisoformat(expected_harvest_date)
                        days_until_harvest = max(
                            (harvest_dt.date() - datetime.utcnow().date()).days, 0
                        )
                        if not next_expected_harvest or harvest_dt < next_expected_harvest:
                            next_expected_harvest = harvest_dt
                    except ValueError:
                        pass

                normalized_crop = {
                    **crop,
                    "planting_date": planting_date,
                    "expected_harvest_date": expected_harvest_date,
                    "days_until_harvest": days_until_harvest,
                    "estimated_quantity": crop.get("estimated_quantity")
                    or crop.get("expected_yield")
                    or 0,
                    "quantity_unit": crop.get("quantity_unit") or "quintals",
                }
                active_crops.append(normalized_crop)

            # Calculate total profit potential from expected_profit
            for crop in active_crops:
                if crop.get("expected_profit"):
                    try:
                        total_profit_potential += float(crop["expected_profit"])
                    except (ValueError, TypeError):
                        pass

        # Get buyer interests
        buyer_interests = []
        if has_listings:
            listing_ids = [listing["id"] for listing in listings_result.items]
            interests_result = BuyerInterest.where({"listing_id": listing_ids}).get()
            buyer_interests = interests_result.items if len(interests_result.items) > 0 else []

        # User is onboarded if they have at least a farm
        is_onboarding_complete = has_farms

        print(
            f"Profile Status Results - Farms: {has_farms}, Crops: {has_crops}, Strategies: {has_strategies}, Listings: {has_listings}, Active Crops: {len(active_crops)}, Profit Potential: {total_profit_potential}"
        )

        # Return dashboard data structure expected by frontend
        return {
            "debug": {"current_user": str(user_id)},
            "has_farms": has_farms,
            "has_crops": has_crops,
            "has_strategies": has_strategies,
            "has_listings": has_listings,
            "is_onboarding_complete": is_onboarding_complete,
            "farms": farms_list,
            "plots": plots_list,
            "dashboard_data": {
                "stats": {
                    "total_profit_potential": round(total_profit_potential, 2),
                    "active_listings": len(listings_result.items) if has_listings else 0,
                    "buyer_interests": len(buyer_interests),
                    "active_crops": len(active_crops),
                    "pending_tasks": 0,
                    "next_expected_harvest_date": (
                        next_expected_harvest.isoformat() if next_expected_harvest else None
                    ),
                },
                "active_crops": active_crops[:5],  # Top 5 active crops
                "active_listings": (
                    listings_result.items[:5] if has_listings else []
                ),  # Top 5 listings
                "upcoming_tasks": [],
                "buyer_interests": buyer_interests[:5],  # Top 5 buyer interests
                "weather_alerts": [],
                "strategy_timeline": [],
            },
        }
    except Exception as e:
        # If there's an error, assume no data to show onboarding
        print(f"Error in profile-status: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            "debug": {"current_user": "None", "error": str(e)},
            "has_farms": False,
            "has_crops": False,
            "has_strategies": False,
            "has_listings": False,
            "is_onboarding_complete": False,
            "farms": [],
            "plots": [],
            "dashboard_data": {
                "stats": {
                    "total_profit_potential": 0,
                    "active_listings": 0,
                    "buyer_interests": 0,
                    "active_crops": 0,
                    "pending_tasks": 0,
                },
                "active_crops": [],
                "active_listings": [],
                "upcoming_tasks": [],
                "buyer_interests": [],
                "weather_alerts": [],
                "strategy_timeline": [],
            },
        }


@router.get("/dashboard")
async def get_dashboard_analytics(db: AsyncSession = Depends(get_async_db)):
    """
    Get dashboard analytics summary

    Returns quick summary data for the main dashboard
    """
    try:
        # Return dashboard data in the format expected by frontend
        return {
            "stats": {
                "total_profit_potential": 0,
                "active_listings": 0,
                "buyer_interests": 0,
                "active_crops": 0,
                "pending_tasks": 0,
            },
            "active_crops": [],
            "active_listings": [],
            "upcoming_tasks": [],
            "buyer_interests": [],
            "weather_alerts": [],
            "strategy_timeline": [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard analytics: {str(e)}")


@router.get("/farm-performance")
async def get_farm_performance(
    farm_id: int = Query(..., description="Farm ID"), db: AsyncSession = Depends(get_async_db)
):
    """Get per-plot performance for a specific farm"""
    service = AnalyticsService(db)
    try:
        # Using a wide date range to get general performance
        start_date = datetime.now() - timedelta(days=730)
        end_date = datetime.now()
        performance = await service._get_plot_performance(farm_id, start_date, end_date)
        return {"farm_id": farm_id, "performance": performance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crop-performance")
async def get_crop_performance(
    farmer_id: Optional[int] = Query(
        None, description="Farmer ID (defaults to you; admins may pass any)"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get overall crop performance for a farmer"""
    farmer_id = _self_or_admin(farmer_id, current_user)
    service = AnalyticsService(db)
    try:
        start_date = datetime.now() - timedelta(days=730)
        end_date = datetime.now()
        performance = await service._get_crop_performance(farmer_id, start_date, end_date)
        return {"farmer_id": farmer_id, "performance": performance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-trends")
async def get_market_trends_api(db: AsyncSession = Depends(get_async_db)):
    """Get market price trends"""
    service = AnalyticsService(db)
    try:
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        trends = await service._get_price_trends(start_date, end_date)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/farmer/{farmer_id}")
async def get_farmer_analytics(
    farmer_id: int,
    start_date: Optional[datetime] = Query(
        None, description="Start date for analysis (ISO format)"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get comprehensive farmer analytics

    Returns:
        - Crop performance metrics (yield vs predicted, profit vs expected)
        - Profit trends over time
        - ROI tracking (investment vs returns, profit margins)
        - Regional comparison with averages
    """
    farmer_id = _self_or_admin(farmer_id, current_user)
    service = AnalyticsService(db)
    try:
        analytics = await service.get_farmer_analytics(farmer_id, start_date, end_date)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating farmer analytics: {str(e)}")


@router.get("/farm/{farm_id}")
async def get_farm_analytics_api(
    farm_id: int,
    start_date: Optional[datetime] = Query(
        None, description="Start date for analysis (ISO format)"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get analytics for a specific farm

    Returns plot-level performance, profit trends, and latest strategy overview
    """
    _ensure_farm_access(farm_id, current_user)
    service = AnalyticsService(db)
    try:
        analytics = await service.get_farm_analytics(farm_id, start_date, end_date)
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating farm analytics: {str(e)}")


@router.get("/platform")
async def get_platform_analytics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for analysis (ISO format)"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_admin),
):
    """
    Get platform analytics

    Returns:
        - User adoption trends (registrations, active users, retention)
        - Feature usage statistics (most used features, engagement metrics)
        - Prediction accuracy over time (track model performance)
    """
    service = AnalyticsService(db)
    try:
        analytics = await service.get_platform_analytics(start_date, end_date)
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating platform analytics: {str(e)}"
        )


@router.get("/market")
async def get_market_analytics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for analysis (ISO format)"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get market analytics

    Returns:
        - Price trends for major crops (historical prices, current prices)
        - Demand patterns (buyer interest by crop and region)
        - Supply forecasts (upcoming harvests, quantity predictions)
    """
    service = AnalyticsService(db)
    try:
        analytics = await service.get_market_analytics(start_date, end_date)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating market analytics: {str(e)}")


@router.get("/executive-report")
async def get_executive_report(
    start_date: Optional[datetime] = Query(None, description="Start date for report (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for report (ISO format)"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_admin),
):
    """
    Generate executive report with key insights and recommendations

    Returns:
        - Key metrics summary
        - Insights from platform and market data
        - Actionable recommendations for platform improvement
    """
    service = AnalyticsService(db)
    try:
        report = await service.generate_executive_report(start_date, end_date)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating executive report: {str(e)}")
