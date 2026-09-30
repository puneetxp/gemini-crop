"""
Database initialization script with sample data
Run this script to populate the database with initial data for development/testing
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.models import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize database with tables"""
    logger.info("Creating database tables...")
    # NOTE (2026-09-26): don't use this to create tables. The schema is owned by database/Model/*.json
    # + `php setup.php` (see skills/SKILL.md); SQLAlchemy here is only a connection pool / the users model.
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def create_sample_users(db: Session) -> dict:
    """Create sample users"""
    logger.info("Creating sample users...")

    users = {}

    # Sample Farmer 1
    farmer1 = User(
        id=uuid.uuid4(),
        cognito_user_id="cognito_farmer_001",
        cognito_username="farmer001",
        email="farmer1@example.com",
        phone_number="+919876543210",
        full_name="Rajesh Kumar",
        language="en",
        user_type="farmer",
        is_active=True,
        is_verified=True,
        email_verified=True,
        phone_verified=True,
        location_state="Punjab",
        location_district="Ludhiana",
    )
    db.add(farmer1)
    users["farmer1"] = farmer1

    # Sample Farmer 2
    farmer2 = User(
        id=uuid.uuid4(),
        cognito_user_id="cognito_farmer_002",
        cognito_username="farmer002",
        email="farmer2@example.com",
        phone_number="+919876543211",
        full_name="Suresh Patel",
        language="hi",
        user_type="farmer",
        is_active=True,
        is_verified=True,
        email_verified=True,
        phone_verified=True,
        location_state="Gujarat",
        location_district="Ahmedabad",
    )
    db.add(farmer2)
    users["farmer2"] = farmer2

    # Sample Buyer
    buyer1 = User(
        id=uuid.uuid4(),
        cognito_user_id="cognito_buyer_001",
        cognito_username="buyer001",
        email="buyer1@example.com",
        phone_number="+919876543212",
        full_name="Amit Sharma",
        language="en",
        user_type="buyer",
        is_active=True,
        is_verified=True,
        email_verified=True,
        phone_verified=True,
        location_state="Maharashtra",
        location_district="Mumbai",
    )
    db.add(buyer1)
    users["buyer1"] = buyer1

    db.commit()
    logger.info(f"Created {len(users)} sample users")
    return users


def create_sample_farms(db: Session, users: dict) -> dict:
    """Create sample farms"""
    logger.info("Creating sample farms...")

    farms = {}

    # Farm 1 - Punjab
    farm1 = Farm(
        id=uuid.uuid4(),
        owner_id=users["farmer1"].id,
        name="Green Valley Farm",
        description="Family-owned farm specializing in wheat and cotton",
        location_state="Punjab",
        location_district="Ludhiana",
        location_village="Khanna",
        latitude=Decimal("30.7046"),
        longitude=Decimal("76.2263"),
        total_area=Decimal("10.5"),
        cultivable_area=Decimal("10.0"),
        primary_soil_type="loamy",
        soil_ph=Decimal("7.2"),
        irrigation_type="canal",
        water_availability="abundant",
        previous_crops=["wheat", "cotton", "rice"],
        farming_experience_years=15,
        investment_capacity_per_acre=Decimal("25000"),
        is_active=True,
        is_verified=True,
    )
    db.add(farm1)
    farms["farm1"] = farm1

    # Farm 2 - Gujarat
    farm2 = Farm(
        id=uuid.uuid4(),
        owner_id=users["farmer2"].id,
        name="Sunrise Agriculture",
        description="Modern farm with drip irrigation",
        location_state="Gujarat",
        location_district="Ahmedabad",
        location_village="Sanand",
        latitude=Decimal("22.9676"),
        longitude=Decimal("72.3805"),
        total_area=Decimal("5.0"),
        cultivable_area=Decimal("4.8"),
        primary_soil_type="clay",
        soil_ph=Decimal("6.8"),
        irrigation_type="borewell",
        water_availability="moderate",
        previous_crops=["cotton", "groundnut"],
        farming_experience_years=8,
        investment_capacity_per_acre=Decimal("30000"),
        is_active=True,
        is_verified=True,
    )
    db.add(farm2)
    farms["farm2"] = farm2

    db.commit()
    logger.info(f"Created {len(farms)} sample farms")
    return farms


def create_sample_plots(db: Session, farms: dict) -> dict:
    """Create sample farm plots"""
    logger.info("Creating sample farm plots...")

    plots = {}

    # Plot 1 for Farm 1
    plot1 = FarmPlot(
        id=uuid.uuid4(),
        farm_id=farms["farm1"].id,
        plot_name="North Field",
        plot_number="P1",
        area=Decimal("5.0"),
        soil_type="loamy",
        soil_ph=Decimal("7.2"),
        drainage_quality="good",
        nitrogen_level="medium",
        phosphorus_level="high",
        potassium_level="medium",
        irrigation_type="canal",
        irrigation_access=True,
        slope="flat",
        is_active=True,
        current_status="planted",
    )
    db.add(plot1)
    plots["plot1"] = plot1

    # Plot 2 for Farm 1
    plot2 = FarmPlot(
        id=uuid.uuid4(),
        farm_id=farms["farm1"].id,
        plot_name="South Field",
        plot_number="P2",
        area=Decimal("5.0"),
        soil_type="loamy",
        soil_ph=Decimal("7.0"),
        drainage_quality="excellent",
        nitrogen_level="high",
        phosphorus_level="medium",
        potassium_level="high",
        irrigation_type="canal",
        irrigation_access=True,
        slope="gentle",
        is_active=True,
        current_status="fallow",
    )
    db.add(plot2)
    plots["plot2"] = plot2

    # Plot 1 for Farm 2
    plot3 = FarmPlot(
        id=uuid.uuid4(),
        farm_id=farms["farm2"].id,
        plot_name="Main Plot",
        plot_number="P1",
        area=Decimal("4.8"),
        soil_type="clay",
        soil_ph=Decimal("6.8"),
        drainage_quality="moderate",
        nitrogen_level="medium",
        phosphorus_level="medium",
        potassium_level="low",
        irrigation_type="drip",
        irrigation_access=True,
        slope="flat",
        is_active=True,
        current_status="planted",
    )
    db.add(plot3)
    plots["plot3"] = plot3

    db.commit()
    logger.info(f"Created {len(plots)} sample plots")
    return plots


def create_sample_crop_varieties(db: Session) -> dict:
    """Create sample crop varieties"""
    logger.info("Creating sample crop varieties...")

    varieties = {}

    # Wheat variety
    wheat_hd2967 = CropVariety(
        id=uuid.uuid4(),
        crop_type="wheat",
        variety_name="HD-2967",
        scientific_name="Triticum aestivum",
        growth_duration=130,
        water_requirement="medium",
        soil_preference={"ph_range": [6.5, 7.5], "types": ["loamy", "clay"]},
        climate_zones=["temperate", "subtropical"],
        market_demand_score=Decimal("0.85"),
    )
    db.add(wheat_hd2967)
    varieties["wheat_hd2967"] = wheat_hd2967

    # Cotton variety
    cotton_bt = CropVariety(
        id=uuid.uuid4(),
        crop_type="cotton",
        variety_name="Bt Cotton",
        scientific_name="Gossypium hirsutum",
        growth_duration=180,
        water_requirement="high",
        soil_preference={"ph_range": [6.0, 7.5], "types": ["clay", "loamy"]},
        climate_zones=["tropical", "subtropical"],
        market_demand_score=Decimal("0.90"),
    )
    db.add(cotton_bt)
    varieties["cotton_bt"] = cotton_bt

    db.commit()
    logger.info(f"Created {len(varieties)} sample crop varieties")
    return varieties


def create_sample_market_data(db: Session) -> None:
    """Create sample market intelligence data"""
    logger.info("Creating sample market data...")

    # Sample crop market data for wheat in Punjab
    market_data = []
    for year in [2023, 2024, 2025]:
        for month in range(1, 13):
            data = CropMarketData(
                id=uuid.uuid4(),
                crop_type="wheat",
                variety="HD-2967",
                state="Punjab",
                district="Ludhiana",
                year=year,
                month=month,
                season="rabi" if month in [11, 12, 1, 2, 3, 4] else "kharif",
                avg_price_per_quintal=Decimal(str(1800 + (year - 2023) * 100 + month * 10)),
                min_price=Decimal(str(1700 + (year - 2023) * 100)),
                max_price=Decimal(str(1900 + (year - 2023) * 100)),
                market_demand_score=Decimal("0.85"),
                price_trend="increasing",
                yoy_price_change=Decimal("5.5"),
                data_source="AGMARKNET",
            )
            market_data.append(data)

    db.add_all(market_data)
    db.commit()
    logger.info(f"Created {len(market_data)} market data records")


def create_sample_crops(db: Session, plots: dict, varieties: dict) -> dict:
    """Create sample crops"""
    logger.info("Creating sample crops...")

    crops = {}

    # Wheat crop on plot 1
    crop1 = Crop(
        id=uuid.uuid4(),
        plot_id=plots["plot1"].id,
        crop_variety_id=varieties["wheat_hd2967"].id,
        planting_date=date.today() - timedelta(days=60),
        expected_harvest_date=date.today() + timedelta(days=70),
        area_planted=Decimal("5.0"),
        planting_method="direct_seeding",
        seed_cost=Decimal("5000"),
        status="growing",
        growth_stage="flowering",
        health_score=Decimal("0.85"),
        current_yield_estimate=Decimal("12.5"),
        total_investment=Decimal("25000"),
    )
    db.add(crop1)
    crops["crop1"] = crop1

    # Cotton crop on plot 3
    crop2 = Crop(
        id=uuid.uuid4(),
        plot_id=plots["plot3"].id,
        crop_variety_id=varieties["cotton_bt"].id,
        planting_date=date.today() - timedelta(days=90),
        expected_harvest_date=date.today() + timedelta(days=90),
        area_planted=Decimal("4.8"),
        planting_method="transplanting",
        seed_cost=Decimal("8000"),
        status="growing",
        growth_stage="vegetative",
        health_score=Decimal("0.90"),
        current_yield_estimate=Decimal("20.0"),
        total_investment=Decimal("40000"),
    )
    db.add(crop2)
    crops["crop2"] = crop2

    db.commit()
    logger.info(f"Created {len(crops)} sample crops")
    return crops


def create_sample_listings(db: Session, crops: dict, users: dict) -> None:
    """Create sample marketplace listings"""
    logger.info("Creating sample marketplace listings...")

    # Listing for wheat crop
    listing1 = Listing(
        id=uuid.uuid4(),
        crop_id=crops["crop1"].id,
        farmer_id=users["farmer1"].id,
        title="Premium Wheat HD-2967 - May 2026 Harvest",
        description="High-quality wheat from Punjab, canal-irrigated farm",
        crop_type="wheat",
        crop_variety="HD-2967",
        estimated_quantity=Decimal("12.5"),
        quantity_unit="quintals",
        quality_grade="A",
        quality_confidence=Decimal("0.85"),
        expected_harvest_date=date.today() + timedelta(days=70),
        harvest_date_confidence=Decimal("0.90"),
        asking_price_per_quintal=Decimal("2000"),
        price_negotiable=True,
        location_state="Punjab",
        location_district="Ludhiana",
        contact_enabled=True,
        farmer_phone="+919876543210",
        status="active",
        advance_booking_allowed=True,
    )
    db.add(listing1)

    # Listing for cotton crop
    listing2 = Listing(
        id=uuid.uuid4(),
        crop_id=crops["crop2"].id,
        farmer_id=users["farmer2"].id,
        title="Bt Cotton - Premium Quality - June 2026",
        description="Bt Cotton from Gujarat, drip irrigation, excellent quality",
        crop_type="cotton",
        crop_variety="Bt Cotton",
        estimated_quantity=Decimal("20.0"),
        quantity_unit="quintals",
        quality_grade="A",
        quality_confidence=Decimal("0.90"),
        expected_harvest_date=date.today() + timedelta(days=90),
        harvest_date_confidence=Decimal("0.85"),
        asking_price_per_quintal=Decimal("5500"),
        price_negotiable=True,
        location_state="Gujarat",
        location_district="Ahmedabad",
        contact_enabled=True,
        farmer_phone="+919876543211",
        status="active",
        advance_booking_allowed=True,
    )
    db.add(listing2)

    db.commit()
    logger.info("Created 2 sample marketplace listings")


def populate_sample_data(db: Session) -> None:
    """Populate database with all sample data"""
    logger.info("Starting sample data population...")

    try:
        # Create data in order of dependencies
        users = create_sample_users(db)
        farms = create_sample_farms(db, users)
        plots = create_sample_plots(db, farms)
        varieties = create_sample_crop_varieties(db)
        create_sample_market_data(db)
        crops = create_sample_crops(db, plots, varieties)
        create_sample_listings(db, crops, users)

        logger.info("Sample data population completed successfully!")

    except Exception as e:
        logger.error(f"Error populating sample data: {e}")
        db.rollback()
        raise


def main():
    """Main function to initialize database and populate sample data"""
    logger.info("=== Database Initialization Started ===")

    # Initialize database tables
    init_db()

    # Create a database session
    db = SessionLocal()

    try:
        # Populate sample data
        populate_sample_data(db)
        logger.info("=== Database Initialization Completed Successfully ===")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
