"""
Market Data API endpoints
Handles ingestion and retrieval of historical crop market data
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.market_data import (
    BulkIngestionResponse,
    BulkMarketDataCreate,
    CropMarketDataCreate,
    CropMarketDataResponse,
    CropProfitabilityCreate,
    HistoricalYieldCreate,
    MarketDataSummary,
)
from app.services.market_data_service import MarketDataService, get_market_data_service

router = APIRouter(prefix="/market-data", tags=["Market Data"])


@router.post(
    "/crop-prices",
    response_model=CropMarketDataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest single crop market data record",
)
def ingest_crop_market_data(data: CropMarketDataCreate, db: Session = Depends(get_db)):
    """
    Ingest a single crop market data record.

    This endpoint allows ingestion of historical crop price data including:
    - Crop type and variety
    - Location (state, district, market)
    - Time period (year, month, season)
    - Price data (average, min, max, modal)
    - Market metrics (demand score, supply volume, volatility)
    - Trends (YoY, MoM price changes)

    **Required fields:**
    - crop_type: Name of the crop
    - state: State name
    - year: Year of data
    - avg_price_per_quintal: Average price per quintal

    **Validation:**
    - Year must be between 1900 and current year
    - Month must be between 1-12 if provided
    - Season must be one of: kharif, rabi, zaid
    - Prices must be positive values
    - Market demand score must be between 0.0 and 1.0
    """
    try:
        service = get_market_data_service(db)
        market_data = service.ingest_crop_market_data(data.dict(), validate=True)
        return market_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest market data: {str(e)}",
        )


@router.post(
    "/crop-prices/bulk",
    response_model=BulkIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk ingest crop market data",
)
def bulk_ingest_crop_market_data(bulk_data: BulkMarketDataCreate, db: Session = Depends(get_db)):
    """
    Bulk ingest multiple crop market data records.

    This endpoint allows efficient ingestion of large datasets with:
    - Batch processing of multiple records
    - Error handling with skip_errors option
    - Detailed error reporting for failed records
    - Transaction management for data integrity

    **Parameters:**
    - data: List of market data records
    - skip_errors: If true, continues processing even if some records fail

    **Response:**
    - success_count: Number of successfully ingested records
    - error_count: Number of failed records
    - total_records: Total records processed
    - errors: Detailed error information for failed records

    **Use cases:**
    - Import historical data from CSV/Excel files
    - Sync data from external APIs (AGMARKNET, etc.)
    - Batch updates of market prices
    """
    try:
        service = get_market_data_service(db)
        data_list = [item.dict() for item in bulk_data.data]
        result = service.bulk_ingest_crop_market_data(
            data_list, validate=True, skip_errors=bulk_data.skip_errors
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk ingestion failed: {str(e)}",
        )


@router.post(
    "/historical-yields",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest historical yield data",
)
def ingest_historical_yield(data: HistoricalYieldCreate, db: Session = Depends(get_db)):
    """
    Ingest historical crop yield data.

    This endpoint stores yield performance data including:
    - Average, min, max yields per acre
    - Success rates and farmer counts
    - Growing conditions (soil, irrigation, weather)
    - Quality metrics and distributions

    **Required fields:**
    - crop_type: Name of the crop
    - state: State name
    - year: Year of data
    - avg_yield_per_acre: Average yield in quintals per acre

    **Use cases:**
    - Build yield prediction models
    - Analyze crop performance by region
    - Identify optimal growing conditions
    """
    try:
        service = get_market_data_service(db)
        yield_data = service.ingest_historical_yield(data.dict(), validate=True)
        return {"message": "Historical yield data ingested successfully", "id": str(yield_data.id)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest yield data: {str(e)}",
        )


@router.post(
    "/crop-profitability",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest crop profitability data",
)
def ingest_crop_profitability(data: CropProfitabilityCreate, db: Session = Depends(get_db)):
    """
    Ingest crop profitability analysis data.

    This endpoint stores comprehensive profitability data including:
    - Profit margins and ROI calculations
    - Detailed cost breakdowns (seed, fertilizer, labor, etc.)
    - Revenue and investment metrics
    - Risk assessments and market factors

    **Required fields:**
    - crop_type: Name of the crop
    - state: State name
    - year: Year of data
    - avg_profit_per_acre: Average profit per acre

    **Use cases:**
    - Calculate opportunity costs
    - Compare crop profitability
    - Generate ROI recommendations
    - Risk-adjusted crop selection
    """
    try:
        service = get_market_data_service(db)
        profitability_data = service.ingest_crop_profitability(data.dict(), validate=True)
        return {
            "message": "Crop profitability data ingested successfully",
            "id": str(profitability_data.id),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest profitability data: {str(e)}",
        )


@router.get("/prices")
async def get_market_prices_alias(db: Session = Depends(get_db)):
    """Registry alias for market prices"""
    return get_market_data_summary(db=db)


@router.get(
    "/summary", response_model=MarketDataSummary, summary="Get market data summary statistics"
)
def get_market_data_summary(
    crop_type: Optional[str] = None,
    state: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Get summary statistics of ingested market data.

    This endpoint provides overview statistics including:
    - Total number of records
    - Unique crops and states
    - Year range of available data

    **Query parameters (all optional):**
    - crop_type: Filter by specific crop
    - state: Filter by specific state
    - year: Filter by specific year

    **Use cases:**
    - Data quality assessment
    - Coverage analysis
    - Identify data gaps
    - Monitor ingestion progress
    """
    try:
        service = get_market_data_service(db)
        summary = service.get_market_data_summary(crop_type=crop_type, state=state, year=year)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summary: {str(e)}",
        )


@router.get("/health", summary="Health check for market data service")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for market data service.

    Returns service status and basic connectivity information.
    """
    try:
        # Test database connectivity
        service = get_market_data_service(db)
        summary = service.get_market_data_summary()

        return {
            "status": "healthy",
            "service": "market_data_ingestion",
            "database": "connected",
            "total_records": summary["total_records"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Service unhealthy: {str(e)}"
        )


@router.get("/trends")
async def get_market_trends_alias(crop_type: str, state: str, db: Session = Depends(get_db)):
    """Registry alias for market trends"""
    return analyze_seasonal_trends(crop_type, state, db=db)


@router.get("/forecast")
async def get_market_forecast_alias(crop_type: str, state: str, db: Session = Depends(get_db)):
    """Registry alias for market forecast"""
    return analyze_seasonal_trends(crop_type, state, db=db)


# Seasonal Trend Analysis Endpoints


@router.get("/seasonal-trends/{crop_type}", summary="Analyze seasonal trends for a crop")
def analyze_seasonal_trends(
    crop_type: str,
    state: str,
    district: Optional[str] = None,
    years: int = 5,
    db: Session = Depends(get_db),
):
    """
    Analyze seasonal trends (Kharif, Rabi, Zaid) for a crop.

    This endpoint provides comprehensive seasonal analysis including:
    - Price trends by season (YoY growth, volatility)
    - Yield trends by season (performance, success rates)
    - Seasonal patterns and optimal planting windows
    - Best season recommendation with scoring
    - Actionable recommendations for farmers

    **Path parameters:**
    - crop_type: Name of the crop (e.g., Wheat, Rice, Cotton)

    **Query parameters:**
    - state: State name (required)
    - district: District name (optional, for more specific analysis)
    - years: Number of years to analyze (default: 5)

    **Response includes:**
    - Seasonal breakdown for Kharif, Rabi, and Zaid seasons
    - Price and yield trends with YoY growth rates
    - Optimal planting and harvest windows
    - Best performing season with confidence score
    - Practical recommendations for crop planning

    **Use cases:**
    - Annual crop strategy planning
    - Season selection for maximum profitability
    - Risk assessment by season
    - Planting calendar optimization
    """
    try:
        from app.services.seasonal_trend_analysis import get_seasonal_trend_service

        service = get_seasonal_trend_service(db)
        analysis = service.analyze_seasonal_trends(
            crop_type=crop_type, state=state, district=district, years=years
        )
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze seasonal trends: {str(e)}",
        )


@router.get(
    "/seasonal-trends/{crop_type}/{season}", summary="Analyze specific season trend for a crop"
)
def analyze_season_trend(
    crop_type: str,
    season: str,
    state: str,
    district: Optional[str] = None,
    years: int = 5,
    db: Session = Depends(get_db),
):
    """
    Analyze trends for a specific season (Kharif, Rabi, or Zaid).

    This endpoint provides detailed analysis for a single season including:
    - Price trends with YoY growth and volatility
    - Yield trends with success rates
    - Seasonal patterns and performance scores
    - Optimal planting and harvest windows
    - Specific recommendations for the season

    **Path parameters:**
    - crop_type: Name of the crop
    - season: Season name (kharif, rabi, or zaid)

    **Query parameters:**
    - state: State name (required)
    - district: District name (optional)
    - years: Number of years to analyze (default: 5)

    **Seasons:**
    - Kharif: Monsoon season (June-October planting, September-November harvest)
    - Rabi: Winter season (October-November planting, March-May harvest)
    - Zaid: Summer season (March-April planting, June-July harvest)

    **Use cases:**
    - Detailed season-specific planning
    - Compare performance across years
    - Identify optimal planting dates
    - Assess season-specific risks
    """
    try:
        from app.services.seasonal_trend_analysis import get_seasonal_trend_service

        # Validate season
        if season.lower() not in ["kharif", "rabi", "zaid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Season must be one of: kharif, rabi, zaid",
            )

        service = get_seasonal_trend_service(db)
        analysis = service.analyze_season_trend(
            crop_type=crop_type, state=state, district=district, season=season.lower(), years=years
        )

        if "error" in analysis:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=analysis["error"])

        return analysis
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze season trend: {str(e)}",
        )


@router.post(
    "/seasonal-trends/store",
    status_code=status.HTTP_201_CREATED,
    summary="Store seasonal trend analysis",
)
def store_seasonal_trend(
    crop_type: str,
    state: str,
    season: str,
    district: Optional[str] = None,
    years: int = 5,
    db: Session = Depends(get_db),
):
    """
    Analyze and store seasonal trend data in the database.

    This endpoint:
    1. Analyzes seasonal trends for the specified crop and location
    2. Stores the analysis results in the seasonal_trends table
    3. Returns the stored trend data

    **Query parameters:**
    - crop_type: Name of the crop (required)
    - state: State name (required)
    - season: Season name - kharif, rabi, or zaid (required)
    - district: District name (optional)
    - years: Number of years to analyze (default: 5)

    **Use cases:**
    - Pre-compute seasonal trends for faster retrieval
    - Build historical trend database
    - Cache analysis results for recommendations
    - Support offline trend access
    """
    try:
        from app.services.seasonal_trend_analysis import get_seasonal_trend_service

        # Validate season
        if season.lower() not in ["kharif", "rabi", "zaid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Season must be one of: kharif, rabi, zaid",
            )

        service = get_seasonal_trend_service(db)

        # Analyze the season
        analysis = service.analyze_season_trend(
            crop_type=crop_type, state=state, district=district, season=season.lower(), years=years
        )

        if "error" in analysis:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=analysis["error"])

        # Store the analysis
        stored_trend = service.store_seasonal_trend(
            crop_type=crop_type,
            state=state,
            district=district,
            season=season.lower(),
            trend_data=analysis,
        )

        return {
            "message": "Seasonal trend stored successfully",
            "id": str(stored_trend.id),
            "crop_type": stored_trend.crop_type,
            "state": stored_trend.state,
            "season": stored_trend.planting_season,
            "analysis_summary": {
                "price_trend_yoy": (
                    float(stored_trend.price_trend_yoy) if stored_trend.price_trend_yoy else None
                ),
                "yield_trend_yoy": (
                    float(stored_trend.yield_trend_yoy) if stored_trend.yield_trend_yoy else None
                ),
                "performance_score": (
                    float(stored_trend.weather_suitability_score)
                    if stored_trend.weather_suitability_score
                    else None
                ),
            },
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store seasonal trend: {str(e)}",
        )


@router.get("/yoy-growth/{crop_type}", summary="Calculate Year-over-Year growth for crop prices")
def calculate_yoy_growth(
    crop_type: str,
    state: str,
    district: Optional[str] = None,
    current_year: Optional[int] = None,
    season: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Calculate Year-over-Year (YoY) growth for crop prices.

    This endpoint provides YoY price analysis including:
    - Current and previous year average prices
    - YoY growth percentage
    - Absolute price change
    - Price trend classification (increasing/stable/decreasing)
    - Price volatility metrics

    **Path parameters:**
    - crop_type: Name of the crop

    **Query parameters:**
    - state: State name (required)
    - district: District name (optional)
    - current_year: Year to calculate growth for (defaults to latest available)
    - season: Season filter (optional) - kharif, rabi, or zaid

    **Use cases:**
    - Quick price trend assessment
    - Market intelligence for crop selection
    - Historical price comparison
    - Opportunity cost calculations
    """
    try:
        service = get_market_data_service(db)
        result = service.calculate_yoy_growth(
            crop_type=crop_type,
            state=state,
            district=district,
            current_year=current_year,
            season=season,
        )

        if "error" in result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate YoY growth: {str(e)}",
        )


@router.get("/multi-year-growth/{crop_type}", summary="Calculate multi-year growth trends")
def calculate_multi_year_growth(
    crop_type: str,
    state: str,
    district: Optional[str] = None,
    years: int = 5,
    season: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Calculate multi-year growth trends for crop prices.

    This endpoint provides comprehensive multi-year analysis including:
    - Compound Annual Growth Rate (CAGR)
    - Average YoY growth across years
    - Year-by-year price breakdown
    - Overall trend classification
    - Price range and volatility

    **Path parameters:**
    - crop_type: Name of the crop

    **Query parameters:**
    - state: State name (required)
    - district: District name (optional)
    - years: Number of years to analyze (default: 5)
    - season: Season filter (optional)

    **Use cases:**
    - Long-term market trend analysis
    - Investment decision support
    - Crop profitability forecasting
    - Risk assessment over time
    """
    try:
        service = get_market_data_service(db)
        result = service.calculate_multi_year_growth(
            crop_type=crop_type, state=state, district=district, years=years, season=season
        )

        if "error" in result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate multi-year growth: {str(e)}",
        )


# Opportunity Cost Analysis Endpoints


@router.get("/opportunity-cost", summary="Calculate opportunity cost between two crops")
def calculate_opportunity_cost(
    primary_crop: str,
    alternative_crop: str,
    state: str,
    district: Optional[str] = None,
    season: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Calculate opportunity cost of choosing primary crop over alternative crop.

    **Opportunity Cost Definition:**
    The opportunity cost represents the profit that could have been earned by choosing
    the alternative crop instead of the primary crop. This helps farmers understand
    trade-offs in crop selection.

    **Query parameters:**
    - primary_crop: The crop being considered (required)
    - alternative_crop: The alternative crop to compare against (required)
    - state: State name (required)
    - district: District name (optional, for more specific analysis)
    - season: Season filter (optional) - kharif, rabi, or zaid
    - year: Year for comparison (defaults to latest available year)

    **Response includes:**
    - Profit comparison (per acre)
    - Investment comparison
    - ROI comparison
    - Risk assessment for both crops
    - Opportunity cost calculation (profit difference)
    - Risk-adjusted opportunity cost
    - Recommendation with confidence score
    - Detailed reasoning for the recommendation

    **Example:**
    If choosing Wheat (primary) over Cotton (alternative):
    - Positive opportunity cost: Cotton would have been more profitable
    - Negative opportunity cost: Wheat is more profitable than Cotton

    **Use cases:**
    - Compare two specific crops for the same land
    - Understand trade-offs in crop selection
    - Make informed planting decisions
    - Validate AC4: RAG system suggests crops with opportunity cost analysis
    """
    try:
        service = get_market_data_service(db)
        result = service.calculate_opportunity_cost(
            primary_crop=primary_crop,
            alternative_crop=alternative_crop,
            state=state,
            district=district,
            season=season,
            year=year,
        )

        if "error" in result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate opportunity cost: {str(e)}",
        )


@router.get(
    "/opportunity-cost/multi-crop",
    summary="Calculate opportunity costs for multiple alternative crops",
)
def calculate_multi_crop_opportunity_costs(
    primary_crop: str,
    alternative_crops: str,  # Comma-separated list
    state: str,
    district: Optional[str] = None,
    season: Optional[str] = None,
    year: Optional[int] = None,
    top_n: int = 3,
    db: Session = Depends(get_db),
):
    """
    Calculate opportunity costs for multiple alternative crops.

    This endpoint helps farmers see all their options and understand the trade-offs
    of choosing one crop over multiple alternatives.

    **Query parameters:**
    - primary_crop: The crop being considered (required)
    - alternative_crops: Comma-separated list of alternative crops (required)
      Example: "Cotton,Rice,Sugarcane"
    - state: State name (required)
    - district: District name (optional)
    - season: Season filter (optional)
    - year: Year for comparison (defaults to latest year)
    - top_n: Number of top alternatives to highlight (default: 3)

    **Response includes:**
    - Top N alternatives ranked by profit difference
    - Best alternative with highest profit potential
    - Total opportunity cost across all alternatives
    - Detailed comparisons for each alternative
    - Insights and recommendations
    - Risk analysis across alternatives

    **Use cases:**
    - Compare multiple crop options simultaneously
    - Identify the most profitable alternative
    - Understand full range of opportunities
    - Support comprehensive crop planning
    """
    try:
        # Parse comma-separated alternative crops
        alt_crops_list = [crop.strip() for crop in alternative_crops.split(",")]

        if not alt_crops_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one alternative crop must be provided",
            )

        service = get_market_data_service(db)
        result = service.calculate_multi_crop_opportunity_costs(
            primary_crop=primary_crop,
            alternative_crops=alt_crops_list,
            state=state,
            district=district,
            season=season,
            year=year,
            top_n=top_n,
        )

        if "error" in result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])

        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate multi-crop opportunity costs: {str(e)}",
        )


@router.post(
    "/opportunity-cost/save",
    status_code=status.HTTP_201_CREATED,
    summary="Calculate and save opportunity cost analysis",
)
def save_opportunity_cost_analysis(
    primary_crop: str,
    alternative_crop: str,
    state: str,
    district: Optional[str] = None,
    season: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Calculate and save opportunity cost analysis to database.

    This endpoint:
    1. Calculates opportunity cost between two crops
    2. Stores the analysis in the opportunity_costs table
    3. Returns the stored analysis data

    **Query parameters:**
    - primary_crop: The crop being considered (required)
    - alternative_crop: The alternative crop to compare (required)
    - state: State name (required)
    - district: District name (optional)
    - season: Season filter (optional)
    - year: Year for comparison (defaults to latest year)

    **Use cases:**
    - Pre-compute opportunity costs for faster retrieval
    - Build historical opportunity cost database
    - Cache analysis results for recommendations
    - Support RAG-based crop recommendations
    """
    try:
        service = get_market_data_service(db)
        opportunity_cost = service.save_opportunity_cost_analysis(
            primary_crop=primary_crop,
            alternative_crop=alternative_crop,
            state=state,
            district=district,
            season=season,
            year=year,
        )

        return {
            "message": "Opportunity cost analysis saved successfully",
            "id": str(opportunity_cost.id),
            "primary_crop": opportunity_cost.primary_crop,
            "alternative_crop": opportunity_cost.alternative_crop,
            "profit_difference": float(opportunity_cost.profit_difference),
            "recommended_choice": opportunity_cost.recommended_choice,
            "confidence": float(opportunity_cost.recommendation_confidence),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save opportunity cost analysis: {str(e)}",
        )


@router.get(
    "/top-profitable-crops",
    summary="Get top profitable crops with opportunity cost analysis - Validates AC4",
)
def get_top_profitable_crops(
    state: str,
    district: Optional[str] = None,
    season: Optional[str] = None,
    year: Optional[int] = None,
    top_n: int = 3,
    include_opportunity_costs: bool = True,
    db: Session = Depends(get_db),
):
    """
    Get top N most profitable crops for a location with opportunity cost analysis.

    **This endpoint validates Acceptance Criteria 4 (AC4):**
    "RAG system suggests top 3 profitable crops with opportunity cost analysis"

    **Query parameters:**
    - state: State name (required)
    - district: District name (optional, for more specific recommendations)
    - season: Season filter (optional) - kharif, rabi, or zaid
    - year: Year for analysis (defaults to latest available year)
    - top_n: Number of top crops to return (default: 3)
    - include_opportunity_costs: Include opportunity cost analysis (default: true)

    **Response includes:**
    - Top N most profitable crops ranked by profit per acre
    - Average profit, investment, and ROI for each crop
    - Risk level assessment for each crop
    - Opportunity cost analysis comparing top crops
    - Recommendation with confidence score
    - Total crops analyzed in the location

    **Opportunity Cost Analysis:**
    When enabled, shows what farmers forgo by choosing lower-ranked crops
    instead of the top-ranked crop. This helps farmers understand the
    financial impact of their crop selection decisions.

    **Use cases:**
    - RAG-based crop recommendations for farmers
    - Annual crop strategy planning
    - Profit maximization decisions
    - Market intelligence for crop selection
    - Validate AC4 requirement

    **Example Response:**
    ```json
    {
      "location": {"state": "Punjab", "district": "Ludhiana", "year": 2023},
      "top_profitable_crops": [
        {
          "crop_type": "Cotton",
          "avg_profit_per_acre": 75000,
          "avg_roi_percentage": 85,
          "risk_level": "medium"
        },
        {
          "crop_type": "Wheat",
          "avg_profit_per_acre": 65000,
          "avg_roi_percentage": 75,
          "risk_level": "low"
        },
        {
          "crop_type": "Rice",
          "avg_profit_per_acre": 55000,
          "avg_roi_percentage": 70,
          "risk_level": "medium"
        }
      ],
      "opportunity_cost_analysis": {
        "comparisons": [
          {
            "choosing": "Wheat",
            "forgoing": "Cotton",
            "opportunity_cost": 10000,
            "reasoning": "Choosing Wheat over Cotton means forgoing ₹10,000 per acre"
          }
        ],
        "recommendation": "Cotton offers the highest profit potential in this location",
        "confidence": 0.85
      }
    }
    ```
    """
    try:
        service = get_market_data_service(db)
        result = service.get_top_profitable_crops(
            state=state,
            district=district,
            season=season,
            year=year,
            top_n=top_n,
            include_opportunity_costs=include_opportunity_costs,
        )

        if "error" in result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top profitable crops: {str(e)}",
        )
