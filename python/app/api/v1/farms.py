"""
Farm Management API endpoints
Handles farm registration, plot management, and farm profile updates with address support
"""

import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import DB, AddressSvc, BedrockSvc, CurrentFarmer, CurrentUser, FarmSvc
from app.orm.active_role import ActiveRole
from app.orm.farm import Farm
from app.orm.farm_plot import FarmPlot
from app.orm.user import User
from app.schemas.address import AddressBase
from app.schemas.auth import MessageResponse
from app.schemas.farm import (
    FarmCreate,
    FarmDetailResponse,
    FarmListResponse,
    FarmResponse,
    FarmUpdate,
    PlotCreate,
    PlotListResponse,
    PlotResponse,
    PlotUpdate,
)
from app.services.address_service import AddressService
from app.services.farm_service import FarmService
from app.services.soil_mapping import SoilMappingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/farms", tags=["Farms"])


@router.get("/location-lookup", status_code=status.HTTP_200_OK)
async def lookup_farm_location(
    current_user: CurrentUser,
    db: DB,
    bedrock: BedrockSvc,
    latitude: Optional[float] = Query(None, description="GPS Latitude"),
    longitude: Optional[float] = Query(None, description="GPS Longitude"),
    pincode: Optional[str] = Query(None, description="6-digit Pincode"),
    village: Optional[str] = Query(None, description="Village/VPO name"),
):
    """
    Predict farm location details (State, District, Village, Pincode, Soil Type) using AI
    Can be triggered via GPS coordinates OR Pincode.
    """
    if not (latitude and longitude) and not pincode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either latitude/longitude OR pincode",
        )

    try:
        result = None

        if latitude and longitude:
            logger.info(
                f"Looking up location via GPS for user {current_user.id}: {latitude}, {longitude}"
            )
            result = await bedrock.predict_location_from_gps(latitude, longitude)

        elif pincode and village:
            logger.info(
                f"Looking up location via Precise VPO for user {current_user.id}: {pincode}, {village}"
            )
            result = await bedrock.predict_location_from_village(pincode, village)

        elif pincode:
            logger.info(f"Looking up location via Pincode for user {current_user.id}: {pincode}")
            result = await bedrock.predict_location_from_pincode(pincode)

        if not result:
            # Return empty structure instead of 404 to allow manual entry in UI
            return {
                "state": None,
                "district": None,
                "pincode": pincode,
                "villages": [],
                "primary_soil_type": None,
            }

        return result

    except Exception as e:
        logger.error(f"AI Location lookup failed: {e}")
        # Return empty structure on error to prevent UI breakage
        return {
            "state": None,
            "district": None,
            "pincode": pincode,
            "village": None,
            "primary_soil_type": None,
            "error": str(e),
        }


@router.post("", response_model=FarmDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate, current_user: CurrentFarmer, db: DB, address_service: AddressSvc
):
    """
    Register a new farm for the current farmer with address support

    - **name**: Farm name
    - **state**: State where farm is located (required)
    - **district**: District (required)
    - **village**: Village/VPO (required)
    - **pincode**: 6-digit postal code (required)
    - **address_line**: Address line (optional)
    - **primary_soil_type**: Primary soil type for the farm (optional)
    - **irrigation_type**: Primary irrigation type for the farm (optional)
    - **total_area_acres**: Total farm area in acres
    - **latitude**: GPS latitude (optional)
    - **longitude**: GPS longitude (optional)
    - **plots**: Initial plots to create (optional)

    Validates: AC1 - Farmer can register farm with address and manage multiple plots
    Validates: AC8 - Smart Farm Registration with pincode lookup
    """

    try:
        # Validate address using address service
        address_data = AddressBase(
            latitude=farm_data.latitude,
            longitude=farm_data.longitude,
            pincode=farm_data.pincode,
            state=farm_data.state,
            district=farm_data.district,
            village=farm_data.village,
            address_line=farm_data.address_line,
        )

        is_valid, error_message = await address_service.validate_address(address_data)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

        # Create farm using custom ORM with PostgreSQL column names
        # Note: ID is auto-generated by database (BIGSERIAL)
        # Both user_id and owner_id must be set (both are NOT NULL in database)
        farm_dict = {
            "user_id": current_user.id,  # References users table
            "owner_id": current_user.id,  # References active_roles table (same as user_id for farmers)
            "name": farm_data.name,
            "location_state": farm_data.state,  # Map to location_state
            "location_district": farm_data.district,  # Map to location_district
            "location_village": farm_data.village,  # Map to location_village
            "latitude": farm_data.latitude,
            "longitude": farm_data.longitude,
            "total_area": farm_data.total_area_acres,
            "area_unit": "acres",
        }

        # Get soil defaults based on state if not provided
        soil_defaults = SoilMappingService.get_likely_soil_profile(
            farm_data.state, farm_data.district
        )

        farm_dict.update(
            {
                "primary_soil_type": farm_data.primary_soil_type
                or soil_defaults.get("primary_soil_type"),
                "irrigation_type": farm_data.irrigation_type,
                "nitrogen": (
                    farm_data.nitrogen
                    if farm_data.nitrogen is not None
                    else soil_defaults.get("nitrogen")
                ),
                "phosphorus": (
                    farm_data.phosphorus
                    if farm_data.phosphorus is not None
                    else soil_defaults.get("phosphorus")
                ),
                "potassium": (
                    farm_data.potassium
                    if farm_data.potassium is not None
                    else soil_defaults.get("potassium")
                ),
                "ph_level": (
                    farm_data.ph_level
                    if farm_data.ph_level is not None
                    else soil_defaults.get("ph_level")
                ),
                "organic_carbon": (
                    farm_data.organic_carbon
                    if farm_data.organic_carbon is not None
                    else soil_defaults.get("organic_carbon")
                ),
                "electrical_conductivity": (
                    farm_data.electrical_conductivity
                    if farm_data.electrical_conductivity is not None
                    else soil_defaults.get("electrical_conductivity")
                ),
                "sulfur": (
                    farm_data.sulfur
                    if farm_data.sulfur is not None
                    else soil_defaults.get("sulfur")
                ),
                "zinc": farm_data.zinc if farm_data.zinc is not None else soil_defaults.get("zinc"),
                "iron": farm_data.iron if farm_data.iron is not None else soil_defaults.get("iron"),
                "boron": (
                    farm_data.boron if farm_data.boron is not None else soil_defaults.get("boron")
                ),
                "is_active": True,  # PostgreSQL uses is_active
            }
        )

        # Insert farm and get the created record with auto-generated ID
        insert_result = Farm.create(farm_dict).get_inserted()

        # The ORM returns the class instance itself with data in the 'items' attribute
        if isinstance(insert_result, Farm):
            # Convert ORM instance to dict and extract the items
            result_dict = insert_result.__dict__ if hasattr(insert_result, "__dict__") else {}
            created_farm = result_dict.get("items", {})
            logger.info(f"Created farm: {created_farm}")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected insert result type: {type(insert_result)}",
            )

        if not created_farm or "id" not in created_farm:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create farm - no ID returned",
            )

        farm_id = created_farm["id"]

        # Get or create active role for the user
        active_role_id = None
        # In a real system, role_id would be looked up from a roles table. Assuming 1 for farmer here for simplicity/hackathon
        farmer_role_id = 1

        active_role_query = ActiveRole.where(
            {"user_id": [current_user.id], "role_id": [farmer_role_id]}
        ).get()
        if active_role_query and active_role_query.items:
            active_role_id = active_role_query.items[0]["id"]
        else:
            # Create a fallback active role
            new_role = ActiveRole.create(
                {"user_id": current_user.id, "role_id": farmer_role_id, "enable": 1}
            ).get_inserted()

            if isinstance(new_role, ActiveRole) and hasattr(new_role, "__dict__"):
                active_role_data = new_role.__dict__.get("items", {})
                active_role_id = active_role_data.get("id")
            else:
                # If we still can't get it, we'll try to just pass current_user.id and hope
                active_role_id = current_user.id

        # Create initial plots if provided
        plot_dicts = []
        if farm_data.plots:
            for plot_data in farm_data.plots:
                plot_dict = {
                    "farm_id": farm_id,
                    "plot_name": plot_data.name,
                    "area": plot_data.area_acres,
                    "soil_type": plot_data.soil_type or farm_data.primary_soil_type or "mixed",
                    "irrigation_type": plot_data.irrigation_type
                    or farm_data.irrigation_type
                    or "mixed",
                    "state": farm_data.state,
                    "district": farm_data.district,
                    "active_role_id": active_role_id,
                    "nitrogen": (
                        plot_data.nitrogen
                        if plot_data.nitrogen is not None
                        else (
                            farm_data.nitrogen
                            if farm_data.nitrogen is not None
                            else soil_defaults.get("nitrogen")
                        )
                    ),
                    "phosphorus": (
                        plot_data.phosphorus
                        if plot_data.phosphorus is not None
                        else (
                            farm_data.phosphorus
                            if farm_data.phosphorus is not None
                            else soil_defaults.get("phosphorus")
                        )
                    ),
                    "potassium": (
                        plot_data.potassium
                        if plot_data.potassium is not None
                        else (
                            farm_data.potassium
                            if farm_data.potassium is not None
                            else soil_defaults.get("potassium")
                        )
                    ),
                    "ph_level": (
                        plot_data.ph_level
                        if plot_data.ph_level is not None
                        else (
                            farm_data.ph_level
                            if farm_data.ph_level is not None
                            else soil_defaults.get("ph_level")
                        )
                    ),
                    "organic_carbon": (
                        plot_data.organic_carbon
                        if plot_data.organic_carbon is not None
                        else (
                            farm_data.organic_carbon
                            if farm_data.organic_carbon is not None
                            else soil_defaults.get("organic_carbon")
                        )
                    ),
                    "electrical_conductivity": (
                        plot_data.electrical_conductivity
                        if plot_data.electrical_conductivity is not None
                        else (
                            farm_data.electrical_conductivity
                            if farm_data.electrical_conductivity is not None
                            else soil_defaults.get("electrical_conductivity")
                        )
                    ),
                    "sulfur": (
                        plot_data.sulfur
                        if plot_data.sulfur is not None
                        else (
                            farm_data.sulfur
                            if farm_data.sulfur is not None
                            else soil_defaults.get("sulfur")
                        )
                    ),
                    "zinc": (
                        plot_data.zinc
                        if plot_data.zinc is not None
                        else (
                            farm_data.zinc
                            if farm_data.zinc is not None
                            else soil_defaults.get("zinc")
                        )
                    ),
                    "iron": (
                        plot_data.iron
                        if plot_data.iron is not None
                        else (
                            farm_data.iron
                            if farm_data.iron is not None
                            else soil_defaults.get("iron")
                        )
                    ),
                    "boron": (
                        plot_data.boron
                        if plot_data.boron is not None
                        else (
                            farm_data.boron
                            if farm_data.boron is not None
                            else soil_defaults.get("boron")
                        )
                    ),
                    "enable": 1,
                }
                plot_dicts.append(plot_dict)

        # Insert all plots at once if any
        created_plots = []
        if plot_dicts:
            FarmPlot.insert(plot_dicts).get_all_inserted()
            plots_result = FarmPlot.where({"farm_id": [farm_id]}).get()
            if plots_result and plots_result.items:
                created_plots = plots_result.items

        logger.info(
            f"Farm {created_farm['name']} created by user {current_user.id} with address at pincode {farm_data.pincode}"
        )

        # Build response - convert dict to response model
        response_data = {
            "id": created_farm["id"],  # bigint ID
            "farmer_id": created_farm["owner_id"],  # Map back to farmer_id for API
            "name": created_farm["name"],
            "state": created_farm.get("location_state", ""),  # Map back to state
            "district": created_farm.get("location_district", ""),  # Map back to district
            "village": created_farm.get("location_village", ""),  # Map back to village
            "pincode": farm_data.pincode,  # Not stored in DB, use from request
            "total_area_acres": created_farm.get("total_area", 0),
            "latitude": created_farm.get("latitude"),
            "longitude": created_farm.get("longitude"),
            "address_line": farm_data.address_line or "",
            "primary_soil_type": created_farm.get("primary_soil_type"),
            "irrigation_type": created_farm.get("irrigation_type"),
            "nitrogen": created_farm.get("nitrogen"),
            "phosphorus": created_farm.get("phosphorus"),
            "potassium": created_farm.get("potassium"),
            "ph_level": created_farm.get("ph_level"),
            "organic_carbon": created_farm.get("organic_carbon"),
            "electrical_conductivity": created_farm.get("electrical_conductivity"),
            "sulfur": created_farm.get("sulfur"),
            "zinc": created_farm.get("zinc"),
            "iron": created_farm.get("iron"),
            "boron": created_farm.get("boron"),
            "is_active": created_farm.get("is_active", True),
            "created_at": created_farm.get("created_at"),
            "updated_at": created_farm.get("updated_at"),
            "plots": [],
        }

        # Add plots to response
        for plot in created_plots:
            plot_response = {
                "id": plot["id"],  # bigint ID
                "farm_id": plot["farm_id"],  # bigint ID
                "name": plot.get("plot_name"),
                "area_acres": plot.get("area"),
                "soil_type": plot.get("soil_type"),
                "irrigation_type": plot.get("irrigation_type"),
                "is_active": plot.get("is_active", True),
                "created_at": plot.get("created_at"),
                "updated_at": plot.get("updated_at"),
            }
            response_data["plots"].append(PlotResponse(**plot_response))

        return FarmDetailResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create farm error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=FarmListResponse)
async def get_my_farms(
    current_user: CurrentFarmer,
    db: DB,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records"),
):
    """
    Get all farms for the current farmer

    Returns list of farms owned by the authenticated farmer.
    """
    try:
        # Get farms using custom ORM
        farms_result = Farm.where({"owner_id": [current_user.id], "is_active": [True]}).get()
        farms_data = farms_result.items if farms_result and farms_result.items else []

        # Apply pagination manually
        total = len(farms_data)
        paginated_farms = farms_data[skip : skip + limit]

        # Build farm responses
        farm_responses = []
        for farm in paginated_farms:
            farm_response = FarmResponse(
                id=farm["id"],
                farmer_id=farm.get("owner_id"),
                name=farm["name"],
                state=farm.get("location_state", ""),
                district=farm.get("location_district", ""),
                village=farm.get("location_village", ""),
                pincode=None,
                total_area_acres=farm.get("total_area", 0),
                latitude=farm.get("latitude"),
                longitude=farm.get("longitude"),
                address_line=None,
                primary_soil_type=farm.get("primary_soil_type"),
                irrigation_type=farm.get("irrigation_type"),
                nitrogen=farm.get("nitrogen"),
                phosphorus=farm.get("phosphorus"),
                potassium=farm.get("potassium"),
                ph_level=farm.get("ph_level"),
                organic_carbon=farm.get("organic_carbon"),
                electrical_conductivity=farm.get("electrical_conductivity"),
                sulfur=farm.get("sulfur"),
                zinc=farm.get("zinc"),
                iron=farm.get("iron"),
                boron=farm.get("boron"),
                is_active=farm.get("is_active", True),
                created_at=farm.get("created_at"),
                updated_at=farm.get("updated_at"),
            )
            farm_responses.append(farm_response)

        return FarmListResponse(farms=farm_responses, total=total)

    except Exception as e:
        logger.error(f"Get farms error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve farms"
        )


@router.get("/{id:int}", response_model=FarmDetailResponse)
async def get_farm(id: int, current_user: CurrentUser, db: DB):
    """
    Get farm details by ID

    Returns detailed farm information including all plots.
    Farmers can only access their own farms.
    """
    try:
        # Get farm using custom ORM
        farm_result = Farm.where({"id": [id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        # Check ownership (farmers can only see their own farms)
        if current_user.user_type == "farmer" and farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Get plots using custom ORM
        plots_result = FarmPlot.where({"farm_id": [id], "enable": [1]}).get()
        plots_data = plots_result.items if plots_result and plots_result.items else []

        # Build response
        response_data = {
            "id": farm_data["id"],
            "farmer_id": farm_data.get("owner_id"),
            "name": farm_data["name"],
            "state": farm_data.get("location_state", ""),
            "district": farm_data.get("location_district", ""),
            "village": farm_data.get("location_village", ""),
            "pincode": None,  # Not stored in DB
            "total_area_acres": farm_data.get("total_area", 0),
            "latitude": farm_data.get("latitude"),
            "longitude": farm_data.get("longitude"),
            "address_line": None,  # Not stored in DB
            "primary_soil_type": farm_data.get("primary_soil_type"),
            "irrigation_type": farm_data.get("irrigation_type"),
            "nitrogen": farm_data.get("nitrogen"),
            "phosphorus": farm_data.get("phosphorus"),
            "potassium": farm_data.get("potassium"),
            "ph_level": farm_data.get("ph_level"),
            "organic_carbon": farm_data.get("organic_carbon"),
            "electrical_conductivity": farm_data.get("electrical_conductivity"),
            "sulfur": farm_data.get("sulfur"),
            "zinc": farm_data.get("zinc"),
            "iron": farm_data.get("iron"),
            "boron": farm_data.get("boron"),
            "is_active": farm_data.get("is_active", True),
            "created_at": farm_data.get("created_at"),
            "updated_at": farm_data.get("updated_at"),
            "plots": [],
        }

        # Add plots to response
        for plot in plots_data:
            plot_response = {
                "id": plot["id"],
                "farm_id": plot["farm_id"],
                "name": plot.get("plot_name"),
                "area_acres": plot.get("area"),
                "soil_type": plot.get("soil_type"),
                "irrigation_type": plot.get("irrigation_type"),
                "nitrogen": plot.get("nitrogen"),
                "phosphorus": plot.get("phosphorus"),
                "potassium": plot.get("potassium"),
                "ph_level": plot.get("ph_level"),
                "organic_carbon": plot.get("organic_carbon"),
                "electrical_conductivity": plot.get("electrical_conductivity"),
                "sulfur": plot.get("sulfur"),
                "zinc": plot.get("zinc"),
                "iron": plot.get("iron"),
                "boron": plot.get("boron"),
                "is_active": plot.get("is_active", True),
                "created_at": plot.get("created_at"),
                "updated_at": plot.get("updated_at"),
            }
            response_data["plots"].append(PlotResponse(**plot_response))

        return FarmDetailResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get farm error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve farm"
        )


@router.put("/{id:int}", response_model=FarmResponse)
async def update_farm(id: int, farm_update: FarmUpdate, current_user: CurrentFarmer, db: DB):
    """
    Update farm profile

    Updates farm information. Only the farm owner can update.
    """
    try:
        # Get farm using custom ORM
        farm_result = Farm.where({"id": [id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        # Check ownership
        if farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Build update dict with PostgreSQL column names
        update_dict = {}
        update_data = farm_update.dict(exclude_unset=True)

        # Map API field names to database column names
        field_mapping = {
            "name": "name",
            "state": "location_state",
            "district": "location_district",
            "village": "location_village",
            "total_area_acres": "total_area",
            "latitude": "latitude",
            "longitude": "longitude",
            "primary_soil_type": "primary_soil_type",
            "irrigation_type": "irrigation_type",
            "nitrogen": "nitrogen",
            "phosphorus": "phosphorus",
            "potassium": "potassium",
            "ph_level": "ph_level",
            "organic_carbon": "organic_carbon",
            "electrical_conductivity": "electrical_conductivity",
            "sulfur": "sulfur",
            "zinc": "zinc",
            "iron": "iron",
            "boron": "boron",
        }

        for api_field, db_field in field_mapping.items():
            if api_field in update_data:
                update_dict[db_field] = update_data[api_field]

        # Update using custom ORM
        if update_dict:
            Farm.where({"id": [id]}).update(update_dict)

        # Get updated farm
        updated_farm_result = Farm.where({"id": [id]}).get()
        updated_farm = (
            updated_farm_result.items[0]
            if updated_farm_result and updated_farm_result.items
            else farm_data
        )

        logger.info(f"Farm {id} updated by user {current_user.id}")

        # Build response
        return FarmResponse(
            id=updated_farm["id"],
            farmer_id=updated_farm.get("owner_id"),
            name=updated_farm["name"],
            state=updated_farm.get("location_state", ""),
            district=updated_farm.get("location_district", ""),
            village=updated_farm.get("location_village", ""),
            pincode=None,
            total_area_acres=updated_farm.get("total_area", 0),
            latitude=updated_farm.get("latitude"),
            longitude=updated_farm.get("longitude"),
            address_line=None,
            primary_soil_type=updated_farm.get("primary_soil_type"),
            irrigation_type=updated_farm.get("irrigation_type"),
            nitrogen=updated_farm.get("nitrogen"),
            phosphorus=updated_farm.get("phosphorus"),
            potassium=updated_farm.get("potassium"),
            ph_level=updated_farm.get("ph_level"),
            organic_carbon=updated_farm.get("organic_carbon"),
            electrical_conductivity=updated_farm.get("electrical_conductivity"),
            sulfur=updated_farm.get("sulfur"),
            zinc=updated_farm.get("zinc"),
            iron=updated_farm.get("iron"),
            boron=updated_farm.get("boron"),
            is_active=updated_farm.get("is_active", True),
            created_at=updated_farm.get("created_at"),
            updated_at=updated_farm.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update farm error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{id:int}", response_model=MessageResponse)
async def delete_farm(id: int, current_user: CurrentFarmer, db: DB):
    """
    Delete farm (soft delete)

    Marks farm as inactive. Only the farm owner can delete.
    """
    try:
        # Get farm using custom ORM
        farm_result = Farm.where({"id": [id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        # Check ownership
        if farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Soft delete farm
        Farm.where({"id": [id]}).update({"is_active": False})

        # Also deactivate all plots
        FarmPlot.where({"farm_id": [id]}).update({"is_active": False})

        logger.info(f"Farm {id} deleted by user {current_user.id}")

        return MessageResponse(message="Farm deleted successfully", success=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete farm error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Plot Management Endpoints


@router.post("/{id}/plots", response_model=PlotResponse, status_code=status.HTTP_201_CREATED)
async def create_plot(id: int, plot_data: PlotCreate, current_user: CurrentFarmer, db: DB):
    """
    Add a new plot to a farm

    - **name**: Plot name
    - **area_acres**: Plot area in acres
    - **soil_type**: Soil type (clay, sandy, loamy, silt, peat)
    - **irrigation_type**: Irrigation type (rain-fed, canal, borewell, drip, sprinkler)
    """
    farm_id = id  # route parameter is {id}; the body below refers to farm_id
    try:
        # Get farm and verify ownership using custom ORM
        farm_result = Farm.where({"id": [farm_id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        if farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Get or create active role for the user
        active_role_id = None
        farmer_role_id = 1

        active_role_query = ActiveRole.where(
            {"user_id": [current_user.id], "role_id": [farmer_role_id]}
        ).get()
        if active_role_query and active_role_query.items:
            active_role_id = active_role_query.items[0]["id"]
        else:
            # Create a fallback active role
            new_role = ActiveRole.create(
                {"user_id": current_user.id, "role_id": farmer_role_id, "enable": 1}
            ).get_inserted()

            if isinstance(new_role, ActiveRole) and hasattr(new_role, "__dict__"):
                active_role_data = new_role.__dict__.get("items", {})
                active_role_id = active_role_data.get("id")
            else:
                active_role_id = current_user.id

        # Create plot using custom ORM
        plot_dict = {
            "farm_id": farm_id,
            "plot_name": plot_data.name,
            "area": plot_data.area_acres,
            "soil_type": plot_data.soil_type or farm_data.get("primary_soil_type") or "mixed",
            "irrigation_type": plot_data.irrigation_type
            or farm_data.get("irrigation_type")
            or "mixed",
            "state": farm_data.get("location_state", ""),
            "district": farm_data.get("location_district", ""),
            "active_role_id": active_role_id,
            "enable": 1,
        }

        # Insert and get created plot
        insert_result = FarmPlot.create(plot_dict).get_inserted()

        if isinstance(insert_result, FarmPlot):
            result_dict = insert_result.__dict__ if hasattr(insert_result, "__dict__") else {}
            created_plot = result_dict.get("items", {})
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected insert result type: {type(insert_result)}",
            )

        logger.info(f"Plot {created_plot.get('plot_name')} created for farm {farm_id}")

        return PlotResponse(
            id=created_plot["id"],
            farm_id=created_plot["farm_id"],
            name=created_plot["plot_name"],
            area_acres=created_plot["area"],
            soil_type=created_plot["soil_type"],
            irrigation_type=created_plot["irrigation_type"],
            is_active=bool(created_plot.get("enable", 1)),
            created_at=created_plot.get("created_at"),
            updated_at=created_plot.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create plot error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{id}/plots", response_model=PlotListResponse)
async def get_farm_plots(id: int, current_user: CurrentUser, db: DB):
    """
    Get all plots for a farm

    Returns list of plots for the specified farm.
    """
    try:
        # Get farm using custom ORM and verify access
        farm_result = Farm.where({"id": [id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        # Check access (farmers can only see their own farms)
        if current_user.user_type == "farmer" and farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Get plots using custom ORM
        plots_result = FarmPlot.where({"farm_id": [id], "enable": [1]}).get()
        plots_data = plots_result.items if plots_result and plots_result.items else []

        # Build plot responses
        plot_responses = []
        for plot in plots_data:
            plot_response = PlotResponse(
                id=plot["id"],
                farm_id=plot["farm_id"],
                name=plot.get("plot_name"),
                area_acres=plot.get("area"),
                soil_type=plot.get("soil_type"),
                irrigation_type=plot.get("irrigation_type"),
                nitrogen=plot.get("nitrogen"),
                phosphorus=plot.get("phosphorus"),
                potassium=plot.get("potassium"),
                ph_level=plot.get("ph_level"),
                organic_carbon=plot.get("organic_carbon"),
                electrical_conductivity=plot.get("electrical_conductivity"),
                sulfur=plot.get("sulfur"),
                zinc=plot.get("zinc"),
                iron=plot.get("iron"),
                boron=plot.get("boron"),
                is_active=plot.get("is_active", True),
                created_at=plot.get("created_at"),
                updated_at=plot.get("updated_at"),
            )
            plot_responses.append(plot_response)

        return PlotListResponse(plots=plot_responses, total=len(plot_responses))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get plots error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve plots"
        )


@router.put("/{farm_id}/plots/{id}", response_model=PlotResponse)
async def update_plot(
    farm_id: int, id: int, plot_update: PlotUpdate, current_user: CurrentFarmer, db: DB
):
    """
    Update plot information

    Updates plot details. Only the farm owner can update.
    """
    try:
        # Get farm and verify ownership using custom ORM
        farm_result = Farm.where({"id": [farm_id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        if farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Get plot using custom ORM
        plot_result = FarmPlot.where({"id": [id], "farm_id": [farm_id]}).get()

        if not plot_result or not plot_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")

        # Update fields
        update_dict = plot_update.dict(exclude_unset=True)
        if update_dict:
            FarmPlot.where({"id": [id]}).update(update_dict)

        # Get updated plot
        updated_plot_result = FarmPlot.where({"id": [id]}).get()
        updated_plot = (
            updated_plot_result.items[0]
            if updated_plot_result and updated_plot_result.items
            else plot_result.items[0]
        )

        logger.info(f"Plot {id} updated by user {current_user.id}")

        return PlotResponse(
            id=updated_plot["id"],
            farm_id=updated_plot["farm_id"],
            name=updated_plot.get("plot_name"),
            area_acres=updated_plot.get("area"),
            soil_type=updated_plot.get("soil_type"),
            irrigation_type=updated_plot.get("irrigation_type"),
            nitrogen=updated_plot.get("nitrogen"),
            phosphorus=updated_plot.get("phosphorus"),
            potassium=updated_plot.get("potassium"),
            ph_level=updated_plot.get("ph_level"),
            organic_carbon=updated_plot.get("organic_carbon"),
            electrical_conductivity=updated_plot.get("electrical_conductivity"),
            sulfur=updated_plot.get("sulfur"),
            zinc=updated_plot.get("zinc"),
            iron=updated_plot.get("iron"),
            boron=updated_plot.get("boron"),
            is_active=updated_plot.get("is_active", True),
            created_at=updated_plot.get("created_at"),
            updated_at=updated_plot.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update plot error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{farm_id}/plots/{id}", response_model=MessageResponse)
async def delete_plot(farm_id: int, id: int, current_user: CurrentFarmer, db: DB):
    """
    Delete plot (soft delete)

    Marks plot as inactive. Only the farm owner can delete.
    """
    try:
        # Get farm and verify ownership using custom ORM
        farm_result = Farm.where({"id": [farm_id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        if farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Get plot using custom ORM
        plot_result = FarmPlot.where({"id": [id], "farm_id": [farm_id]}).get()

        if not plot_result or not plot_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")

        # Soft delete (farm_plots uses enable; there is no is_active column)
        FarmPlot.where({"id": [id]}).update({"enable": 0})

        logger.info(f"Plot {id} deleted by user {current_user.id}")

        return MessageResponse(message="Plot deleted successfully", success=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete plot error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
