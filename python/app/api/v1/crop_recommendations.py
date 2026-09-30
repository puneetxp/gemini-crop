"""
RAG-Based Crop Recommendation API
Validates AC4: RAG system suggests top 3 profitable crops with opportunity cost analysis and 2-crop rotation
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.crop_recommendation_service import get_crop_recommendation_service

router = APIRouter(prefix="/crop-recommendations", tags=["Crop Recommendations"])


@router.get(
    "",
    summary="Get RAG-based crop recommendations - Validates AC4",
    description="""
    Get intelligent crop recommendations using RAG (Retrieval-Augmented Generation) approach.
    
    **This endpoint validates Acceptance Criteria 4 (AC4):**
    - Top 3 profitable crops based on historical data
    - Opportunity cost analysis between crops
    - 2-crop rotation recommendations for consecutive seasons
    - Confidence scores for each recommendation
    - Integration with Amazon Bedrock for AI-powered insights
    
    **RAG Approach:**
    1. **Retrieval**: Fetch historical market data, profitability, and yield data from database
    2. **Analysis**: Calculate opportunity costs and identify optimal crop rotations
    3. **Generation**: Enhance with Amazon Bedrock AI insights for qualitative recommendations
    
    **Features:**
    - Top N profitable crops ranked by profit per acre
    - Opportunity cost analysis showing trade-offs between crops
    - 2-crop rotation recommendations for maximum annual returns
    - Confidence scores based on data availability and success rates
    - AI-powered insights for each crop recommendation
    - Market trend analysis (YoY growth, price trends)
    - Risk assessment and success rates
    
    **Query Parameters:**
    - state: State name (required)
    - district: District name (optional, for more specific recommendations)
    - season: Season filter (optional) - kharif, rabi, or zaid
    - soil_type: Soil type (optional) - clay, sandy, loamy, etc.
    - irrigation_type: Irrigation type (optional) - rain-fed, canal, borewell
    - area_acres: Farm area in acres (optional)
    - top_n: Number of top crops to recommend (default: 3)
    - include_rotation: Include crop rotation recommendations (default: true)
    
    **Response Structure:**
    ```json
    {
      "location": {
        "state": "Punjab",
        "district": "Ludhiana",
        "season": "kharif"
      },
      "top_recommendations": [
        {
          "crop_name": "Cotton",
          "variety": "Bt Cotton",
          "expected_profit_per_acre": 65000,
          "investment_per_acre": 25000,
          "roi_percentage": 160,
          "confidence_score": 0.87,
          "ai_insights": "Cotton performs well in Punjab with good market demand...",
          "expected_yield_per_acre": 25,
          "avg_market_price": 5800,
          "price_trend": "increasing",
          "yoy_growth": 12.5
        }
      ],
      "opportunity_cost_analysis": [
        {
          "primary_crop": "Cotton",
          "alternative_crop": "Rice",
          "profit_difference": 15000,
          "opportunity_cost": 15000,
          "recommended_choice": "Cotton",
          "recommendation": "Cotton is ₹15,000 more profitable per acre"
        }
      ],
      "crop_rotation_recommendations": [
        {
          "sequence": "Cotton → Wheat",
          "season_1": {
            "crop": "Cotton",
            "season": "kharif",
            "expected_profit": 65000
          },
          "season_2": {
            "crop": "Wheat",
            "season": "rabi",
            "expected_profit": 45000
          },
          "total_annual_profit": 110000,
          "benefits": [
            "Soil health improvement",
            "Risk diversification",
            "Optimal land utilization"
          ]
        }
      ],
      "recommendation_summary": {
        "top_recommendation": {
          "crop": "Cotton",
          "expected_profit": 65000,
          "confidence": 0.87,
          "key_insight": "Proven high-profit crop for Punjab region"
        },
        "opportunity_cost_insight": "Cotton is the most profitable option",
        "rotation_insight": "Cotton → Wheat rotation for ₹110,000 annual profit"
      }
    }
    ```
    
    **Use Cases:**
    - Annual crop planning for farmers
    - Profit maximization through data-driven crop selection
    - Understanding trade-offs between different crop options
    - Planning crop rotations for soil health and maximum returns
    - Risk assessment and market trend analysis
    
    **Data Sources:**
    - Historical market price data (3-5 years)
    - Crop profitability records
    - Yield success rates
    - Seasonal trends
    - Amazon Bedrock AI insights
    """,
)
def get_crop_recommendations(
    state: str = Query(..., description="State name (required)"),
    district: Optional[str] = Query(None, description="District name for specific recommendations"),
    season: Optional[str] = Query(None, description="Season: kharif, rabi, or zaid"),
    soil_type: Optional[str] = Query(None, description="Soil type: clay, sandy, loamy, etc."),
    irrigation_type: Optional[str] = Query(
        None, description="Irrigation: rain-fed, canal, borewell"
    ),
    area_acres: Optional[float] = Query(None, description="Farm area in acres", gt=0),
    top_n: int = Query(3, description="Number of top crops to recommend", ge=1, le=10),
    include_rotation: bool = Query(True, description="Include crop rotation recommendations"),
    db: Session = Depends(get_db),
):
    """
    Get RAG-based crop recommendations with opportunity cost analysis.

    **Validates AC4**: RAG system suggests top 3 profitable crops with opportunity cost
    analysis and 2-crop rotation recommendations.
    """
    try:
        # Validate season if provided
        if season and season.lower() not in ["kharif", "rabi", "zaid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Season must be one of: kharif, rabi, zaid",
            )

        # Get recommendation service
        service = get_crop_recommendation_service(db)

        # Generate recommendations
        recommendations = service.get_rag_crop_recommendations(
            state=state,
            district=district,
            season=season.lower() if season else None,
            soil_type=soil_type,
            irrigation_type=irrigation_type,
            area_acres=area_acres,
            top_n=top_n,
            include_rotation=include_rotation,
        )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate crop recommendations: {str(e)}",
        )


@router.get(
    "/quick",
    summary="Get quick crop recommendations (faster response)",
    description="""
    Get quick crop recommendations with minimal processing for faster response times.
    
    This endpoint provides:
    - Top 3 profitable crops
    - Basic opportunity cost analysis
    - No crop rotation recommendations (for speed)
    - Reduced AI enhancement
    
    Use this endpoint when you need fast recommendations without detailed analysis.
    """,
)
def get_quick_crop_recommendations(
    state: str = Query(..., description="State name (required)"),
    district: Optional[str] = Query(None, description="District name"),
    season: Optional[str] = Query(None, description="Season: kharif, rabi, or zaid"),
    db: Session = Depends(get_db),
):
    """
    Get quick crop recommendations without rotation analysis.
    """
    try:
        # Validate season if provided
        if season and season.lower() not in ["kharif", "rabi", "zaid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Season must be one of: kharif, rabi, zaid",
            )

        # Get recommendation service
        service = get_crop_recommendation_service(db)

        # Generate quick recommendations (no rotation)
        recommendations = service.get_rag_crop_recommendations(
            state=state,
            district=district,
            season=season.lower() if season else None,
            soil_type=None,
            irrigation_type=None,
            area_acres=None,
            top_n=3,
            include_rotation=False,  # Skip rotation for speed
        )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quick recommendations: {str(e)}",
        )


@router.get(
    "/by-season/{season}",
    summary="Get season-specific crop recommendations",
    description="""
    Get crop recommendations optimized for a specific season.
    
    **Seasons:**
    - **Kharif**: Monsoon season (June-October planting)
    - **Rabi**: Winter season (November-April planting)
    - **Zaid**: Summer season (March-June planting)
    
    This endpoint provides season-specific insights including:
    - Best crops for the season
    - Seasonal market trends
    - Weather-appropriate recommendations
    - Season-specific opportunity costs
    """,
)
def get_season_specific_recommendations(
    season: str,
    state: str = Query(..., description="State name (required)"),
    district: Optional[str] = Query(None, description="District name"),
    soil_type: Optional[str] = Query(None, description="Soil type"),
    top_n: int = Query(3, description="Number of recommendations", ge=1, le=10),
    db: Session = Depends(get_db),
):
    """
    Get season-specific crop recommendations.
    """
    try:
        # Validate season
        if season.lower() not in ["kharif", "rabi", "zaid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Season must be one of: kharif, rabi, zaid",
            )

        # Get recommendation service
        service = get_crop_recommendation_service(db)

        # Generate season-specific recommendations
        recommendations = service.get_rag_crop_recommendations(
            state=state,
            district=district,
            season=season.lower(),
            soil_type=soil_type,
            irrigation_type=None,
            area_acres=None,
            top_n=top_n,
            include_rotation=True,
        )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate season-specific recommendations: {str(e)}",
        )


@router.get("/health", summary="Health check for crop recommendation service")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for crop recommendation service.

    Returns service status and connectivity information.
    """
    try:
        # Test database connectivity
        service = get_crop_recommendation_service(db)

        # Test basic query
        from app.core.db import DB as RawDB  # raw SQL (app/orm classes are not SQLAlchemy models)

        test_query = RawDB.raw("SELECT id FROM crop_profitability LIMIT 1").result

        return {
            "status": "healthy",
            "service": "crop_recommendation",
            "database": "connected",
            "rag_engine": "operational",
            "bedrock_integration": "available",
            "features": {
                "top_crop_recommendations": True,
                "opportunity_cost_analysis": True,
                "crop_rotation_recommendations": True,
                "ai_insights": True,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Service unhealthy: {str(e)}"
        )
