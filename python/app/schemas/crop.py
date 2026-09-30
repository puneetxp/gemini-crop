"""
Crop recommendation and prediction schemas
"""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnnualStrategyRequest(BaseModel):
    """Request for annual crop strategy"""

    farm_id: int = Field(..., description="Farm ID")
    previous_crops: Optional[str] = Field(None, description="Previous crops grown")
    budget_per_acre: Optional[float] = Field(None, gt=0, description="Budget per acre in INR")
    use_gps: bool = Field(False, description="Use GPS-enhanced recommendations (subject to quota)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude (optional)")
    longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="GPS longitude (optional)"
    )


class SeasonalRecommendation(BaseModel):
    """Seasonal crop recommendation"""

    recommended_crop: str
    variety: str
    expected_yield_per_acre: str
    expected_profit_per_acre: float
    investment_per_acre: float
    planting_window: str
    harvest_window: str
    key_success_factors: List[str]
    confidence_score: float


class AnnualSummary(BaseModel):
    """Annual strategy summary"""

    total_expected_profit_per_acre: float
    total_investment_per_acre: float
    roi_percentage: float
    risk_level: str
    sustainability_score: float


class AlternativeOption(BaseModel):
    """Alternative crop option"""

    season: str
    crop: str
    profit_difference: float
    risk_comparison: str


class MonthlyAction(BaseModel):
    """Monthly action item"""

    month: str
    actions: List[str]


class QuotaStatus(BaseModel):
    """AI quota status information"""

    remaining_quota: Optional[int] = Field(
        None, description="Remaining GPS-enhanced requests today"
    )
    gps_enhanced: bool = Field(False, description="Whether GPS-enhanced recommendation was used")
    quota_exceeded: bool = Field(False, description="Whether quota was exceeded")
    fallback_message: Optional[str] = Field(None, description="Message if fallback occurred")


class AnnualStrategyResponse(BaseModel):
    """Complete annual crop strategy response"""

    farm_id: int
    farm_name: str
    location: str
    kharif: SeasonalRecommendation
    rabi: SeasonalRecommendation
    zaid: Optional[Dict[str, Any]] = None
    annual_summary: AnnualSummary
    alternative_options: List[AlternativeOption] = []
    monthly_action_plan: List[MonthlyAction] = []
    generated_at: str
    quota_status: Optional[QuotaStatus] = None


class CropRecommendationRequest(BaseModel):
    """Request for crop recommendations"""

    farm_id: int = Field(..., description="Farm ID")
    season: str = Field(..., description="Season: kharif, rabi, zaid")
    use_gps: bool = Field(False, description="Use GPS-enhanced recommendations (subject to quota)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude (optional)")
    longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="GPS longitude (optional)"
    )


class CropRecommendation(BaseModel):
    """Single crop recommendation"""

    rank: int
    crop_name: str
    variety: str
    suitability_reason: str
    expected_yield_per_acre: str
    expected_profit_per_acre: float
    investment_per_acre: float
    key_requirements: List[str]
    challenges: List[str]
    market_demand: str
    confidence_score: float


class CropRecommendationsResponse(BaseModel):
    """Crop recommendations response"""

    farm_id: int
    season: str
    recommendations: List[CropRecommendation]
    generated_at: str
    quota_status: Optional[QuotaStatus] = None


class YieldPredictionRequest(BaseModel):
    """Request for yield prediction"""

    crop_name: str = Field(..., description="Crop name")
    variety: str = Field(..., description="Crop variety")
    farm_id: int = Field(..., description="Farm ID")
    plot_id: int = Field(..., description="Plot ID")
    planting_date: date = Field(..., description="Planting date")
    area_acres: float = Field(..., gt=0, description="Area in acres")


class YieldPredictionResponse(BaseModel):
    """Yield prediction response"""

    crop_name: str
    variety: str
    harvest_date: str
    harvest_date_range: Dict[str, str]
    expected_yield_per_acre: float
    yield_range: Dict[str, float]
    total_expected_yield: float
    quality_grade: str
    confidence_score: float
    key_factors: List[str]
    recommendations: List[str]
    generated_at: str


class SaveStrategyRequest(BaseModel):
    """Request to save an annual strategy"""

    farm_id: int
    strategy_year: int = Field(..., description="Year for the strategy")
    strategy_data: Dict[str, Any] = Field(..., description="Complete strategy data")
    kharif_crop: Optional[str] = None
    rabi_crop: Optional[str] = None
    zaid_crop: Optional[str] = None


class SaveStrategyResponse(BaseModel):
    """Response after saving strategy"""

    strategy_id: str
    farm_id: int
    strategy_year: int
    message: str
    reminders_created: int


class GetStrategyRequest(BaseModel):
    """Request to retrieve a strategy"""

    farm_id: int
    strategy_year: Optional[int] = None  # If None, get latest


class StrategyListItem(BaseModel):
    """Strategy list item for farmer's strategies"""

    strategy_id: str
    farm_id: int
    farm_name: str
    strategy_year: int
    kharif_crop: Optional[str]
    rabi_crop: Optional[str]
    zaid_crop: Optional[str]
    total_expected_profit: float
    is_active: bool
    generated_at: str


class UpdateStrategyStatusRequest(BaseModel):
    """Request to update strategy implementation status"""

    strategy_id: str
    season: str = Field(..., description="kharif, rabi, or zaid")
    implemented: bool
    actual_results: Optional[Dict[str, Any]] = None


class StrategyFeedbackRequest(BaseModel):
    """Request to provide feedback on strategy"""

    strategy_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback: Optional[str] = None
    actual_results: Optional[Dict[str, Any]] = None


class SupportingCropInput(BaseModel):
    """A supporting (inter/companion) crop grown alongside the main crop"""

    crop_name: str = Field(..., description="Supporting crop name")
    variety: Optional[str] = Field(None, description="Supporting crop variety")
    area: Optional[float] = Field(
        None, gt=0, description="Area in acres (defaults to the main crop's area)"
    )


class QuickPlantRequest(BaseModel):
    """Request to quickly plant a crop"""

    farm_id: int = Field(..., description="Farm ID")
    plot_id: Optional[int] = Field(None, description="Plot ID (if None, plant in all active plots)")
    crop_name: str = Field(..., description="Crop name")
    variety: Optional[str] = Field(None, description="Crop variety")
    season: str = Field(..., description="Season: kharif, rabi, zaid")
    area: float = Field(..., gt=0, description="Area in acres")
    planting_date: date = Field(..., description="Planned planting date")
    expected_harvest_date: Optional[date] = Field(
        None, description="Planned harvest date (defaults to ~4 months after planting)"
    )
    expected_yield: Optional[float] = Field(None, description="Expected yield in quintals")
    market_price: Optional[float] = Field(
        None, description="Expected market price per quintal in INR"
    )
    supporting_crops: List[SupportingCropInput] = Field(
        default_factory=list, description="Supporting crops planted with the main crop"
    )


class QuickPlantResponse(BaseModel):
    """Response after quick planting"""

    success: bool
    message: str
    crop_ids: List[int]
    total_area_planted: float
    supporting_crop_ids: List[int] = Field(default_factory=list)


class CropExpenseRequest(BaseModel):
    """Request to add a crop expense"""

    category: str = Field(..., description="Seeds, Labor, Fertilizer, Pesticide, Equipment, Other")
    amount: float = Field(..., gt=0, description="Expense amount in INR")
    description: Optional[str] = Field(None, description="Detailed description")
    expense_date: date = Field(..., description="Date of expense")


class CropExpenseResponse(BaseModel):
    """Response after adding an expense"""

    id: int
    crop_id: int
    category: str
    amount: float
    description: Optional[str]
    expense_date: date
    created_at: str
