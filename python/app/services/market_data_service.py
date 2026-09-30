"""
Market Data Ingestion Service
Handles ingestion of historical crop price data for RAG-based market intelligence
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as Session
from typing import Dict, List, Optional

from app.services.farm_access import Row, fetch_all, fetch_one

logger = logging.getLogger(__name__)

# Data access is raw SQL through app.core.db.DB (app/orm classes are not SQLAlchemy models).
# Rows are farm_access.Row (dict + attribute access); these aliases keep the type hints readable.
CropMarketData = HistoricalYield = CropProfitability = SeasonalTrend = OpportunityCost = Row


class IntegrityError(Exception):
    """Kept so `except IntegrityError` callers still work (DB errors now surface as psycopg errors)."""


# crop_market_data stores crop_name / price_per_kg / date / yoy_growth / demand_level. This view exposes
# the names this service (and CropMarketDataResponse) use. Fields with no column are NULL.
_CMD_VIEW = """(SELECT id::text AS id, created_at, updated_at, crop_name AS crop_type, NULL::varchar AS variety,
        state, district, NULL::varchar AS market_name,
        EXTRACT(YEAR FROM date)::int AS year, EXTRACT(MONTH FROM date)::int AS month, season,
        price_per_kg * 100 AS avg_price_per_quintal,
        NULL::numeric AS min_price, NULL::numeric AS max_price, NULL::numeric AS modal_price,
        NULL::numeric AS market_demand_score, NULL::numeric AS supply_volume, NULL::numeric AS price_volatility,
        NULL::varchar AS price_trend, yoy_growth AS yoy_price_change, NULL::numeric AS mom_price_change,
        NULL::varchar AS data_source, NULL::numeric AS data_quality_score,
        demand_level, date, price_per_kg
    FROM crop_market_data WHERE COALESCE(enable, 1) = 1) cmd"""


def _where(filters: Dict[str, Any], extra: tuple = ()) -> tuple:
    """Build ' WHERE a = ? AND ...' from fixed column names; None / '' values are skipped."""
    parts, bind = [], []
    for col, val in filters.items():
        if val is None or val == "":
            continue
        parts.append(f"{col} = ?")
        bind.append(val)
    for clause, *vals in extra:
        parts.append(clause)
        bind.extend(vals)
    return ((" WHERE " + " AND ".join(parts)) if parts else ""), bind


def _market_rows(order: str = "year, month, id", extra: tuple = (), **filters) -> List[Row]:
    where, bind = _where(filters, extra)
    return fetch_all(f"SELECT * FROM {_CMD_VIEW}{where} ORDER BY {order}", bind)


def _profit_rows(extra: tuple = (), **filters) -> List[Row]:
    where, bind = _where(filters, extra)
    return fetch_all(f"SELECT * FROM crop_profitability{where} ORDER BY id", bind)


def _max_profit_year(state: str) -> Optional[int]:
    row = fetch_one("SELECT MAX(year) AS y FROM crop_profitability WHERE state = ?", [state])
    return row.y if row else None


def _insert(table: str, values: Dict[str, Any]) -> Row:
    cols = list(values.keys())
    return fetch_one(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)}) RETURNING *",
        [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values.values()],
    )


def _num(v):
    return float(v) if v not in (None, "") else None


class MarketDataService:
    """Service for ingesting and managing historical crop market data"""

    def __init__(self, db: Session):
        """
        Initialize market data service

        Args:
            db: Database session
        """
        self.db = db

    def ingest_crop_market_data(
        self, data: Dict[str, Any], validate: bool = True
    ) -> CropMarketData:
        """
        Ingest single crop market data record

        Args:
            data: Market data dictionary with required fields
            validate: Whether to validate data before insertion

        Returns:
            Created CropMarketData instance

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraint violated
        """
        try:
            if validate:
                self._validate_market_data(data)

            # Create market data record. Real columns: crop_name, state, district, price_per_kg, date,
            # season, yoy_growth, demand_level. variety / market_name / min / max / modal price, demand score,
            # supply volume, volatility, trend, MoM change, data source and quality have no column and are not stored.
            price_per_kg = float(data["avg_price_per_quintal"]) / 100  # 1 quintal = 100 kg
            record_date = datetime(int(data["year"]), int(data.get("month") or 1), 1).date()
            created = _insert(
                "crop_market_data",
                {
                    "crop_name": data["crop_type"],
                    "state": data["state"],
                    "district": data.get("district"),
                    "price_per_kg": round(price_per_kg, 2),
                    "date": record_date,
                    "season": data.get("season"),
                    "yoy_growth": _num(data.get("yoy_price_change")),
                    "demand_level": data.get("demand_level"),
                },
            )
            market_data = fetch_one(f"SELECT * FROM {_CMD_VIEW} WHERE id = ?", [str(created.id)])

            logger.info(
                f"Ingested market data: {market_data.crop_type} - {market_data.state} - {market_data.year}"
            )
            return market_data

        except IntegrityError as e:
            logger.error(f"Database integrity error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error ingesting market data: {e}")
            raise

    def bulk_ingest_crop_market_data(
        self, data_list: List[Dict[str, Any]], validate: bool = True, skip_errors: bool = False
    ) -> Dict[str, Any]:
        """
        Bulk ingest multiple crop market data records

        Args:
            data_list: List of market data dictionaries
            validate: Whether to validate data before insertion
            skip_errors: Whether to skip records with errors and continue

        Returns:
            Dictionary with success count, error count, and error details
        """
        success_count = 0
        error_count = 0
        errors = []

        for idx, data in enumerate(data_list):
            try:
                self.ingest_crop_market_data(data, validate=validate)
                success_count += 1

            except Exception as e:
                error_count += 1
                error_detail = {"index": idx, "data": data, "error": str(e)}
                errors.append(error_detail)
                logger.error(f"Error ingesting record {idx}: {e}")

                if not skip_errors:
                    raise

        result = {
            "success_count": success_count,
            "error_count": error_count,
            "total_records": len(data_list),
            "errors": errors,
        }

        logger.info(f"Bulk ingestion completed: {success_count} success, {error_count} errors")
        return result

    def ingest_historical_yield(
        self, data: Dict[str, Any], validate: bool = True
    ) -> HistoricalYield:
        """
        Ingest historical yield data record

        Args:
            data: Yield data dictionary
            validate: Whether to validate data

        Returns:
            Created HistoricalYield instance
        """
        try:
            if validate:
                self._validate_yield_data(data)

            yield_data = _insert(
                "historical_yields",
                {
                    "crop_type": data["crop_type"],
                    "variety": data.get("variety"),
                    "state": data["state"],
                    "district": data.get("district"),
                    "block": data.get("block"),
                    "year": data["year"],
                    "season": data.get("season"),
                    "avg_yield_per_acre": _num(data["avg_yield_per_acre"]),
                    "min_yield": _num(data.get("min_yield")),
                    "max_yield": _num(data.get("max_yield")),
                    "success_rate": _num(data.get("success_rate")),
                    "farmer_count": data.get("farmer_count"),
                    "total_area_cultivated": _num(data.get("total_area_cultivated")),
                    "soil_types": data.get("soil_types"),
                    "irrigation_methods": data.get("irrigation_methods"),
                    "avg_rainfall": _num(data.get("avg_rainfall")),
                    "avg_temperature": _num(data.get("avg_temperature")),
                    "quality_distribution": data.get("quality_distribution"),
                    "avg_quality_grade": data.get("avg_quality_grade"),
                    "data_source": data.get("data_source", "manual"),
                    "data_quality_score": _num(data.get("data_quality_score")) or 0.8,
                },
            )

            logger.info(
                f"Ingested yield data: {yield_data.crop_type} - {yield_data.state} - {yield_data.year}"
            )
            return yield_data

        except Exception as e:
            logger.error(f"Error ingesting yield data: {e}")
            raise

    def ingest_crop_profitability(
        self, data: Dict[str, Any], validate: bool = True
    ) -> CropProfitability:
        """
        Ingest crop profitability data record

        Args:
            data: Profitability data dictionary
            validate: Whether to validate data

        Returns:
            Created CropProfitability instance
        """
        try:
            if validate:
                self._validate_profitability_data(data)

            numeric = (
                "avg_profit_per_acre",
                "min_profit_per_acre",
                "max_profit_per_acre",
                "seed_cost",
                "fertilizer_cost",
                "pesticide_cost",
                "labor_cost",
                "irrigation_cost",
                "equipment_cost",
                "other_costs",
                "total_investment_cost",
                "avg_revenue_per_acre",
                "roi_percentage",
                "break_even_yield",
                "profit_margin",
                "price_risk_score",
                "yield_risk_score",
            )
            values = {
                "crop_type": data["crop_type"],
                "variety": data.get("variety"),
                "state": data["state"],
                "district": data.get("district"),
                "year": data["year"],
                "season": data.get("season"),
            }
            values.update({k: _num(data.get(k)) for k in numeric})
            values.update(
                {
                    "risk_level": data.get("risk_level"),
                    "market_demand": data.get("market_demand"),
                    "competition_level": data.get("competition_level"),
                    "data_source": data.get("data_source", "manual"),
                    "sample_size": data.get("sample_size"),
                }
            )
            profitability_data = _insert("crop_profitability", values)

            logger.info(
                f"Ingested profitability data: {profitability_data.crop_type} - {profitability_data.state} - {profitability_data.year}"
            )
            return profitability_data

        except Exception as e:
            logger.error(f"Error ingesting profitability data: {e}")
            raise

    def _validate_market_data(self, data: Dict[str, Any]) -> None:
        """
        Validate crop market data

        Args:
            data: Market data dictionary

        Raises:
            ValueError: If validation fails
        """
        required_fields = ["crop_type", "state", "year", "avg_price_per_quintal"]

        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Missing required field: {field}")

        # Validate year
        current_year = datetime.now().year
        if not (1900 <= data["year"] <= current_year):
            raise ValueError(f"Invalid year: {data['year']}")

        # Validate month if provided
        if data.get("month") and not (1 <= data["month"] <= 12):
            raise ValueError(f"Invalid month: {data['month']}")

        # Validate season if provided
        valid_seasons = ["kharif", "rabi", "zaid"]
        if data.get("season") and data["season"].lower() not in valid_seasons:
            raise ValueError(f"Invalid season: {data['season']}. Must be one of {valid_seasons}")

        # Validate price values
        if data["avg_price_per_quintal"] <= 0:
            raise ValueError("Average price must be positive")

        if data.get("min_price") and data.get("max_price"):
            if data["min_price"] > data["max_price"]:
                raise ValueError("Min price cannot be greater than max price")

        # Validate market demand score if provided
        if data.get("market_demand_score"):
            score = float(data["market_demand_score"])
            if not (0.0 <= score <= 1.0):
                raise ValueError("Market demand score must be between 0.0 and 1.0")

    def _validate_yield_data(self, data: Dict[str, Any]) -> None:
        """
        Validate historical yield data

        Args:
            data: Yield data dictionary

        Raises:
            ValueError: If validation fails
        """
        required_fields = ["crop_type", "state", "year", "avg_yield_per_acre"]

        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Missing required field: {field}")

        # Validate year
        current_year = datetime.now().year
        if not (1900 <= data["year"] <= current_year):
            raise ValueError(f"Invalid year: {data['year']}")

        # Validate yield values
        if data["avg_yield_per_acre"] <= 0:
            raise ValueError("Average yield must be positive")

        if data.get("min_yield") and data.get("max_yield"):
            if data["min_yield"] > data["max_yield"]:
                raise ValueError("Min yield cannot be greater than max yield")

    def _validate_profitability_data(self, data: Dict[str, Any]) -> None:
        """
        Validate crop profitability data

        Args:
            data: Profitability data dictionary

        Raises:
            ValueError: If validation fails
        """
        required_fields = ["crop_type", "state", "year", "avg_profit_per_acre"]

        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Missing required field: {field}")

        # Validate year
        current_year = datetime.now().year
        if not (1900 <= data["year"] <= current_year):
            raise ValueError(f"Invalid year: {data['year']}")

        # Validate risk level if provided
        valid_risk_levels = ["low", "medium", "high"]
        if data.get("risk_level") and data["risk_level"].lower() not in valid_risk_levels:
            raise ValueError(
                f"Invalid risk level: {data['risk_level']}. Must be one of {valid_risk_levels}"
            )

    def get_market_data_summary(
        self,
        crop_type: Optional[str] = None,
        state: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get summary statistics of ingested market data

        Args:
            crop_type: Filter by crop type (optional)
            state: Filter by state (optional)
            year: Filter by year (optional)

        Returns:
            Summary statistics dictionary
        """
        where, bind = _where({"crop_type": crop_type, "state": state, "year": year})
        stats = fetch_one(
            f"""SELECT COUNT(*) AS total_records, COUNT(DISTINCT crop_type) AS unique_crops,
                       COUNT(DISTINCT state) AS unique_states, MIN(year) AS min_year, MAX(year) AS max_year
                FROM {_CMD_VIEW}{where}""",
            bind,
        )
        total_records = stats.total_records if stats else 0

        if total_records == 0:
            return {"total_records": 0, "unique_crops": 0, "unique_states": 0, "year_range": None}

        unique_crops = stats.unique_crops
        unique_states = stats.unique_states
        year_stats = (stats.min_year, stats.max_year)

        return {
            "total_records": total_records,
            "unique_crops": unique_crops,
            "unique_states": unique_states,
            "year_range": {"min": year_stats[0], "max": year_stats[1]} if year_stats else None,
        }

    def calculate_yoy_growth(
        self,
        crop_type: str,
        state: str,
        district: Optional[str] = None,
        current_year: Optional[int] = None,
        season: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate Year-over-Year (YoY) growth for crop prices

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)
            current_year: Year to calculate growth for (defaults to latest year)
            season: Season filter (optional)

        Returns:
            Dictionary with YoY growth metrics
        """
        try:
            # Base filters (raw SQL over the crop_market_data view)
            base = {"crop_type": crop_type, "state": state, "district": district, "season": season}

            # Get current year if not provided
            if not current_year:
                where, bind = _where(base)
                row = fetch_one(f"SELECT MAX(year) AS y FROM {_CMD_VIEW}{where}", bind)
                max_year_result = row.y if row else None

                if not max_year_result:
                    return {
                        "error": "No data found for specified criteria",
                        "crop_type": crop_type,
                        "state": state,
                        "district": district,
                    }

                current_year = max_year_result

            # Get current year data
            current_data = _market_rows(year=current_year, **base)

            if not current_data:
                return {
                    "error": f"No data found for year {current_year}",
                    "crop_type": crop_type,
                    "state": state,
                    "year": current_year,
                }

            # Get previous year data
            previous_year = current_year - 1
            previous_data = _market_rows(year=previous_year, **base)

            if not previous_data:
                return {
                    "error": f"No data found for previous year {previous_year}",
                    "crop_type": crop_type,
                    "state": state,
                    "current_year": current_year,
                    "previous_year": previous_year,
                }

            # Calculate average prices
            current_avg_price = sum(d.avg_price_per_quintal for d in current_data) / len(
                current_data
            )
            previous_avg_price = sum(d.avg_price_per_quintal for d in previous_data) / len(
                previous_data
            )

            # Calculate YoY growth percentage
            yoy_growth_percentage = (
                (current_avg_price - previous_avg_price) / previous_avg_price
            ) * 100

            # Calculate absolute change
            absolute_change = current_avg_price - previous_avg_price

            # Determine trend
            if yoy_growth_percentage > 5:
                trend = "increasing"
            elif yoy_growth_percentage < -5:
                trend = "decreasing"
            else:
                trend = "stable"

            # Calculate volatility (standard deviation of prices)
            current_prices = [float(d.avg_price_per_quintal) for d in current_data]
            previous_prices = [float(d.avg_price_per_quintal) for d in previous_data]

            import statistics

            current_volatility = statistics.stdev(current_prices) if len(current_prices) > 1 else 0
            previous_volatility = (
                statistics.stdev(previous_prices) if len(previous_prices) > 1 else 0
            )

            result = {
                "crop_type": crop_type,
                "state": state,
                "district": district,
                "season": season,
                "current_year": current_year,
                "previous_year": previous_year,
                "current_avg_price": float(current_avg_price),
                "previous_avg_price": float(previous_avg_price),
                "yoy_growth_percentage": float(yoy_growth_percentage),
                "absolute_change": float(absolute_change),
                "trend": trend,
                "current_volatility": float(current_volatility),
                "previous_volatility": float(previous_volatility),
                "data_points_current": len(current_data),
                "data_points_previous": len(previous_data),
            }

            logger.info(
                f"Calculated YoY growth for {crop_type} in {state}: {yoy_growth_percentage:.2f}%"
            )
            return result

        except Exception as e:
            logger.error(f"Error calculating YoY growth: {e}")
            raise

    def calculate_multi_year_growth(
        self,
        crop_type: str,
        state: str,
        district: Optional[str] = None,
        years: int = 5,
        season: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate multi-year growth trends for crop prices

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)
            years: Number of years to analyze (default 5)
            season: Season filter (optional)

        Returns:
            Dictionary with multi-year growth analysis
        """
        try:
            # Get available years (average price per year)
            where, bind = _where(
                {"crop_type": crop_type, "state": state, "district": district, "season": season}
            )
            year_data = fetch_all(
                f"""SELECT year, AVG(avg_price_per_quintal) AS avg_price FROM {_CMD_VIEW}{where}
                    GROUP BY year ORDER BY year DESC LIMIT ?""",
                bind + [int(years)],
            )

            if len(year_data) < 2:
                return {
                    "error": "Insufficient data for multi-year analysis",
                    "crop_type": crop_type,
                    "state": state,
                    "available_years": len(year_data),
                }

            # Reverse to get chronological order
            year_data = list(reversed(year_data))

            # Calculate year-over-year changes
            yoy_changes = []
            for i in range(1, len(year_data)):
                previous_price = float(year_data[i - 1].avg_price)
                current_price = float(year_data[i].avg_price)
                yoy_change = ((current_price - previous_price) / previous_price) * 100

                yoy_changes.append(
                    {
                        "from_year": year_data[i - 1].year,
                        "to_year": year_data[i].year,
                        "previous_price": previous_price,
                        "current_price": current_price,
                        "yoy_growth_percentage": float(yoy_change),
                        "absolute_change": float(current_price - previous_price),
                    }
                )

            # Calculate compound annual growth rate (CAGR)
            first_price = float(year_data[0].avg_price)
            last_price = float(year_data[-1].avg_price)
            num_years = len(year_data) - 1

            cagr = (((last_price / first_price) ** (1 / num_years)) - 1) * 100

            # Calculate average YoY growth
            avg_yoy_growth = sum(change["yoy_growth_percentage"] for change in yoy_changes) / len(
                yoy_changes
            )

            # Determine overall trend
            if cagr > 5:
                overall_trend = "strong_growth"
            elif cagr > 0:
                overall_trend = "moderate_growth"
            elif cagr > -5:
                overall_trend = "slight_decline"
            else:
                overall_trend = "significant_decline"

            # Calculate price range
            all_prices = [float(yd.avg_price) for yd in year_data]
            min_price = min(all_prices)
            max_price = max(all_prices)
            price_range = max_price - min_price

            result = {
                "crop_type": crop_type,
                "state": state,
                "district": district,
                "season": season,
                "analysis_period": {
                    "start_year": year_data[0].year,
                    "end_year": year_data[-1].year,
                    "years_analyzed": len(year_data),
                },
                "price_summary": {
                    "first_year_price": first_price,
                    "last_year_price": last_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "price_range": price_range,
                },
                "growth_metrics": {
                    "cagr": float(cagr),
                    "avg_yoy_growth": float(avg_yoy_growth),
                    "overall_trend": overall_trend,
                    "total_growth_percentage": float(
                        ((last_price - first_price) / first_price) * 100
                    ),
                },
                "yearly_breakdown": yoy_changes,
                "year_prices": [
                    {"year": yd.year, "avg_price": float(yd.avg_price)} for yd in year_data
                ],
            }

            logger.info(
                f"Calculated multi-year growth for {crop_type} in {state}: CAGR={cagr:.2f}%"
            )
            return result

        except Exception as e:
            logger.error(f"Error calculating multi-year growth: {e}")
            raise

    def calculate_seasonal_yoy_growth(
        self, crop_type: str, state: str, district: Optional[str] = None, years: int = 3
    ) -> Dict[str, Any]:
        """
        Calculate YoY growth by season (Kharif, Rabi, Zaid)

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)
            years: Number of years to analyze (default 3)

        Returns:
            Dictionary with seasonal YoY growth analysis
        """
        try:
            seasons = ["kharif", "rabi", "zaid"]
            seasonal_analysis = {}

            for season in seasons:
                # Calculate multi-year growth for this season
                season_growth = self.calculate_multi_year_growth(
                    crop_type=crop_type, state=state, district=district, years=years, season=season
                )

                # Skip if insufficient data
                if "error" in season_growth:
                    seasonal_analysis[season] = {
                        "status": "insufficient_data",
                        "message": season_growth["error"],
                    }
                else:
                    seasonal_analysis[season] = season_growth

            # Compare seasons
            valid_seasons = {
                k: v for k, v in seasonal_analysis.items() if "error" not in v and "status" not in v
            }

            if valid_seasons:
                # Find best performing season
                best_season = max(
                    valid_seasons.items(), key=lambda x: x[1]["growth_metrics"]["cagr"]
                )

                result = {
                    "crop_type": crop_type,
                    "state": state,
                    "district": district,
                    "years_analyzed": years,
                    "seasonal_breakdown": seasonal_analysis,
                    "best_performing_season": {
                        "season": best_season[0],
                        "cagr": best_season[1]["growth_metrics"]["cagr"],
                        "trend": best_season[1]["growth_metrics"]["overall_trend"],
                    },
                    "comparison": {
                        season: {
                            "cagr": data["growth_metrics"]["cagr"],
                            "avg_yoy_growth": data["growth_metrics"]["avg_yoy_growth"],
                            "trend": data["growth_metrics"]["overall_trend"],
                        }
                        for season, data in valid_seasons.items()
                    },
                }
            else:
                result = {
                    "crop_type": crop_type,
                    "state": state,
                    "district": district,
                    "error": "Insufficient data for seasonal analysis",
                    "seasonal_breakdown": seasonal_analysis,
                }

            logger.info(f"Calculated seasonal YoY growth for {crop_type} in {state}")
            return result

        except Exception as e:
            logger.error(f"Error calculating seasonal YoY growth: {e}")
            raise

    def update_yoy_price_changes(
        self,
        crop_type: Optional[str] = None,
        state: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update yoy_price_change field in existing market data records

        Args:
            crop_type: Filter by crop type (optional)
            state: Filter by state (optional)
            year: Filter by year (optional)

        Returns:
            Dictionary with update statistics
        """
        try:
            # Build query for records to update
            records = _market_rows(crop_type=crop_type, state=state, year=year)

            updated_count = 0
            skipped_count = 0
            error_count = 0

            for record in records:
                try:
                    # Find previous year data for same crop, location, season (and month)
                    previous_records = _market_rows(
                        crop_type=record.crop_type,
                        state=record.state,
                        year=record.year - 1,
                        district=record.district,
                        season=record.season,
                        month=record.month,
                    )

                    if not previous_records:
                        skipped_count += 1
                        continue

                    # Calculate average price from previous year
                    previous_avg_price = sum(
                        r.avg_price_per_quintal for r in previous_records
                    ) / len(previous_records)

                    # Calculate YoY change
                    yoy_change = (
                        (record.avg_price_per_quintal - previous_avg_price) / previous_avg_price
                    ) * 100

                    # Update record (yoy_growth column; there is no price_trend column to store the trend)
                    fetch_one(
                        "UPDATE crop_market_data SET yoy_growth = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? RETURNING id",
                        [round(yoy_change, 2), int(record.id)],
                    )

                    updated_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error updating record {record.id}: {e}")

            # Each UPDATE is committed by DB.raw

            result = {
                "total_records": len(records),
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
            }

            logger.info(
                f"Updated YoY price changes: {updated_count} records updated, {skipped_count} skipped"
            )
            return result

        except Exception as e:
            logger.error(f"Error updating YoY price changes: {e}")
            raise

    def analyze_seasonal_trends(
        self, crop_type: str, state: str, district: Optional[str] = None, years: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze seasonal trends for Kharif, Rabi, and Zaid seasons

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)
            years: Number of years to analyze (default 5)

        Returns:
            Dictionary with seasonal trend analysis
        """
        try:
            seasons = ["kharif", "rabi", "zaid"]
            seasonal_analysis = {}

            for season in seasons:
                # Data for recent years for this season
                season_data = _market_rows(
                    extra=(("year >= ?", datetime.now().year - years),),
                    crop_type=crop_type,
                    state=state,
                    season=season,
                    district=district,
                )

                if not season_data:
                    seasonal_analysis[season] = {
                        "status": "no_data",
                        "message": f"No data available for {season} season",
                    }
                    continue

                # Calculate seasonal metrics
                prices = [float(d.avg_price_per_quintal) for d in season_data]
                years_list = [d.year for d in season_data]

                # Price trend analysis
                if len(prices) >= 2:
                    first_price = prices[0]
                    last_price = prices[-1]
                    price_change_pct = ((last_price - first_price) / first_price) * 100

                    # Calculate average annual growth
                    num_years = years_list[-1] - years_list[0]
                    if num_years > 0:
                        cagr = (((last_price / first_price) ** (1 / num_years)) - 1) * 100
                    else:
                        cagr = 0
                else:
                    price_change_pct = 0
                    cagr = 0

                # Calculate volatility
                import statistics

                price_volatility = statistics.stdev(prices) if len(prices) > 1 else 0
                avg_price = statistics.mean(prices)
                volatility_coefficient = (
                    (price_volatility / avg_price * 100) if avg_price > 0 else 0
                )

                # Determine trend direction
                if cagr > 5:
                    trend_direction = "strong_upward"
                elif cagr > 0:
                    trend_direction = "moderate_upward"
                elif cagr > -5:
                    trend_direction = "stable"
                else:
                    trend_direction = "downward"

                # Calculate demand indicators
                demand_scores = [
                    float(d.market_demand_score) for d in season_data if d.market_demand_score
                ]
                avg_demand = statistics.mean(demand_scores) if demand_scores else None

                seasonal_analysis[season] = {
                    "status": "success",
                    "data_points": len(season_data),
                    "year_range": {"start": years_list[0], "end": years_list[-1]},
                    "price_metrics": {
                        "avg_price": float(avg_price),
                        "min_price": float(min(prices)),
                        "max_price": float(max(prices)),
                        "first_year_price": float(prices[0]),
                        "last_year_price": float(prices[-1]),
                        "price_change_percentage": float(price_change_pct),
                        "cagr": float(cagr),
                        "volatility": float(price_volatility),
                        "volatility_coefficient": float(volatility_coefficient),
                    },
                    "trend_analysis": {
                        "direction": trend_direction,
                        "stability": "stable" if volatility_coefficient < 15 else "volatile",
                        "avg_demand_score": float(avg_demand) if avg_demand else None,
                    },
                    "yearly_data": [
                        {
                            "year": d.year,
                            "price": float(d.avg_price_per_quintal),
                            "demand_score": (
                                float(d.market_demand_score) if d.market_demand_score else None
                            ),
                        }
                        for d in season_data
                    ],
                }

            # Compare seasons
            valid_seasons = {
                k: v for k, v in seasonal_analysis.items() if v.get("status") == "success"
            }

            comparison = {}
            if len(valid_seasons) >= 2:
                # Find best performing season
                best_season = max(
                    valid_seasons.items(), key=lambda x: x[1]["price_metrics"]["cagr"]
                )

                # Find most stable season
                most_stable = min(
                    valid_seasons.items(),
                    key=lambda x: x[1]["price_metrics"]["volatility_coefficient"],
                )

                comparison = {
                    "best_price_growth": {
                        "season": best_season[0],
                        "cagr": best_season[1]["price_metrics"]["cagr"],
                    },
                    "most_stable": {
                        "season": most_stable[0],
                        "volatility": most_stable[1]["price_metrics"]["volatility_coefficient"],
                    },
                    "season_rankings": sorted(
                        [
                            {
                                "season": season,
                                "cagr": data["price_metrics"]["cagr"],
                                "avg_price": data["price_metrics"]["avg_price"],
                                "volatility": data["price_metrics"]["volatility_coefficient"],
                            }
                            for season, data in valid_seasons.items()
                        ],
                        key=lambda x: x["cagr"],
                        reverse=True,
                    ),
                }

            result = {
                "crop_type": crop_type,
                "state": state,
                "district": district,
                "analysis_period": years,
                "seasonal_breakdown": seasonal_analysis,
                "comparison": comparison,
            }

            logger.info(f"Analyzed seasonal trends for {crop_type} in {state}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing seasonal trends: {e}")
            raise

    def forecast_seasonal_prices(
        self,
        crop_type: str,
        state: str,
        season: str,
        district: Optional[str] = None,
        forecast_years: int = 2,
    ) -> Dict[str, Any]:
        """
        Forecast future seasonal prices based on historical trends

        Args:
            crop_type: Type of crop
            state: State name
            season: Season (kharif, rabi, zaid)
            district: District name (optional)
            forecast_years: Number of years to forecast (default 2)

        Returns:
            Dictionary with price forecasts
        """
        import statistics

        try:
            # Get historical data for the season (at least 3 years of data for forecasting)
            historical_data = _market_rows(
                crop_type=crop_type, state=state, season=season, district=district
            )

            if len(historical_data) < 3:
                return {
                    "error": "Insufficient historical data for forecasting",
                    "message": "At least 3 years of data required",
                    "available_years": len(historical_data),
                }

            # Extract prices and years
            years = [d.year for d in historical_data]
            prices = [float(d.avg_price_per_quintal) for d in historical_data]

            # Simple linear regression for trend
            n = len(years)
            sum_x = sum(years)
            sum_y = sum(prices)
            sum_xy = sum(x * y for x, y in zip(years, prices))
            sum_x2 = sum(x * x for x in years)

            # Calculate slope and intercept (all points in one year -> no trend can be fitted)
            if n * sum_x2 - sum_x * sum_x == 0:
                return {
                    "error": "Insufficient historical data for forecasting",
                    "message": "At least 3 years of data required",
                    "available_years": len(set(years)),
                }
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n

            # Calculate R-squared for forecast confidence
            mean_y = statistics.mean(prices)
            ss_tot = sum((y - mean_y) ** 2 for y in prices)
            ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(years, prices))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Generate forecasts
            last_year = years[-1]
            forecasts = []

            for i in range(1, forecast_years + 1):
                forecast_year = last_year + i
                forecast_price = slope * forecast_year + intercept

                # Calculate confidence interval (simple approach)
                std_error = statistics.stdev(prices) if len(prices) > 1 else 0
                confidence_margin = 1.96 * std_error  # 95% confidence

                forecasts.append(
                    {
                        "year": forecast_year,
                        "season": season,
                        "forecast_price": float(max(0, forecast_price)),  # Ensure non-negative
                        "lower_bound": float(max(0, forecast_price - confidence_margin)),
                        "upper_bound": float(forecast_price + confidence_margin),
                        "confidence_score": float(r_squared),
                    }
                )

            # Determine forecast reliability
            if r_squared > 0.7:
                reliability = "high"
            elif r_squared > 0.4:
                reliability = "moderate"
            else:
                reliability = "low"

            result = {
                "crop_type": crop_type,
                "state": state,
                "district": district,
                "season": season,
                "historical_summary": {
                    "years_analyzed": len(historical_data),
                    "year_range": {"start": years[0], "end": years[-1]},
                    "avg_historical_price": float(statistics.mean(prices)),
                    "price_trend": "increasing" if slope > 0 else "decreasing",
                    "annual_change_rate": float(slope),
                },
                "forecast": {
                    "method": "linear_regression",
                    "reliability": reliability,
                    "r_squared": float(r_squared),
                    "predictions": forecasts,
                },
                "recommendations": self._generate_forecast_recommendations(
                    slope, r_squared, forecasts
                ),
            }

            logger.info(f"Generated price forecast for {crop_type} ({season}) in {state}")
            return result

        except Exception as e:
            logger.error(f"Error forecasting seasonal prices: {e}")
            raise

    def _generate_forecast_recommendations(
        self, slope: float, r_squared: float, forecasts: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations based on forecast results

        Args:
            slope: Trend slope
            r_squared: Forecast confidence
            forecasts: List of forecast data

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Trend-based recommendations
        if slope > 0:
            recommendations.append(
                f"Prices are forecasted to increase by approximately ₹{abs(slope):.2f} per quintal annually"
            )
            if r_squared > 0.7:
                recommendations.append("Strong upward trend suggests good profit potential")
        else:
            recommendations.append(
                f"Prices are forecasted to decrease by approximately ₹{abs(slope):.2f} per quintal annually"
            )
            recommendations.append("Consider alternative crops with better price trends")

        # Confidence-based recommendations
        if r_squared < 0.4:
            recommendations.append(
                "Low forecast confidence - market is volatile, consider risk mitigation strategies"
            )
        elif r_squared > 0.7:
            recommendations.append("High forecast confidence - historical patterns are consistent")

        # Price level recommendations
        if forecasts:
            first_forecast = forecasts[0]
            if (
                first_forecast["upper_bound"] - first_forecast["lower_bound"]
                > first_forecast["forecast_price"] * 0.3
            ):
                recommendations.append(
                    "Wide price range indicates uncertainty - monitor market conditions closely"
                )

        return recommendations

    def identify_seasonal_patterns(
        self, crop_type: str, state: str, district: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify patterns in crop prices and yields across seasons

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)

        Returns:
            Dictionary with identified patterns
        """
        try:
            # Get seasonal trend analysis
            trends = self.analyze_seasonal_trends(
                crop_type=crop_type, state=state, district=district, years=5
            )

            patterns = {
                "crop_type": crop_type,
                "state": state,
                "district": district,
                "identified_patterns": [],
            }

            seasonal_data = trends.get("seasonal_breakdown", {})
            valid_seasons = {k: v for k, v in seasonal_data.items() if v.get("status") == "success"}

            if not valid_seasons:
                patterns["identified_patterns"].append(
                    {
                        "pattern": "insufficient_data",
                        "description": "Not enough data to identify patterns",
                    }
                )
                return patterns

            # Pattern 1: Consistent growth across seasons
            all_growing = all(v["price_metrics"]["cagr"] > 0 for v in valid_seasons.values())

            if all_growing:
                patterns["identified_patterns"].append(
                    {
                        "pattern": "consistent_growth",
                        "description": "Prices are growing consistently across all seasons",
                        "recommendation": "Favorable market conditions for this crop",
                        "confidence": "high",
                    }
                )

            # Pattern 2: Seasonal preference
            if len(valid_seasons) >= 2:
                best_season = max(
                    valid_seasons.items(), key=lambda x: x[1]["price_metrics"]["cagr"]
                )
                worst_season = min(
                    valid_seasons.items(), key=lambda x: x[1]["price_metrics"]["cagr"]
                )

                cagr_diff = (
                    best_season[1]["price_metrics"]["cagr"]
                    - worst_season[1]["price_metrics"]["cagr"]
                )

                if cagr_diff > 10:
                    patterns["identified_patterns"].append(
                        {
                            "pattern": "strong_seasonal_preference",
                            "description": f"{best_season[0].capitalize()} season shows significantly better price growth",
                            "best_season": best_season[0],
                            "worst_season": worst_season[0],
                            "growth_difference": float(cagr_diff),
                            "recommendation": f"Prioritize {best_season[0]} season planting for better returns",
                            "confidence": "high",
                        }
                    )

            # Pattern 3: Volatility patterns
            volatile_seasons = [
                season
                for season, data in valid_seasons.items()
                if data["price_metrics"]["volatility_coefficient"] > 20
            ]

            if volatile_seasons:
                patterns["identified_patterns"].append(
                    {
                        "pattern": "high_volatility",
                        "description": f'High price volatility detected in {", ".join(volatile_seasons)} season(s)',
                        "affected_seasons": volatile_seasons,
                        "recommendation": "Consider price hedging or advance contracts to mitigate risk",
                        "confidence": "medium",
                    }
                )

            # Pattern 4: Stable pricing
            stable_seasons = [
                season
                for season, data in valid_seasons.items()
                if data["price_metrics"]["volatility_coefficient"] < 10
            ]

            if stable_seasons:
                patterns["identified_patterns"].append(
                    {
                        "pattern": "stable_pricing",
                        "description": f'Stable prices in {", ".join(stable_seasons)} season(s)',
                        "affected_seasons": stable_seasons,
                        "recommendation": "Predictable returns make planning easier",
                        "confidence": "high",
                    }
                )

            # Pattern 5: Declining market
            all_declining = all(v["price_metrics"]["cagr"] < -5 for v in valid_seasons.values())

            if all_declining:
                patterns["identified_patterns"].append(
                    {
                        "pattern": "market_decline",
                        "description": "Prices are declining across all seasons",
                        "recommendation": "Consider switching to alternative crops with better market outlook",
                        "confidence": "high",
                        "severity": "high",
                    }
                )

            logger.info(
                f"Identified {len(patterns['identified_patterns'])} patterns for {crop_type} in {state}"
            )
            return patterns

        except Exception as e:
            logger.error(f"Error identifying seasonal patterns: {e}")
            raise

    def calculate_opportunity_cost(
        self,
        primary_crop: str,
        alternative_crop: str,
        state: str,
        district: Optional[str] = None,
        season: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate opportunity cost of choosing primary crop over alternative crop

        The opportunity cost represents the profit that could have been earned by choosing
        the alternative crop instead of the primary crop. This helps farmers understand
        trade-offs in crop selection.

        Args:
            primary_crop: The crop being considered
            alternative_crop: The alternative crop to compare against
            state: State name
            district: District name (optional)
            season: Season filter (optional)
            year: Year for comparison (defaults to latest year)

        Returns:
            Dictionary with opportunity cost analysis
        """
        try:
            # Get current year if not provided
            if not year:
                max_year_result = _max_profit_year(state)

                if not max_year_result:
                    return {
                        "error": "No profitability data found for specified location",
                        "state": state,
                        "district": district,
                    }

                year = max_year_result

            # Get profitability data for primary crop
            primary_data = _profit_rows(
                crop_type=primary_crop, state=state, year=year, district=district, season=season
            )

            if not primary_data:
                return {
                    "error": f"No profitability data found for {primary_crop}",
                    "crop": primary_crop,
                    "state": state,
                    "year": year,
                }

            # Get profitability data for alternative crop
            alternative_data = _profit_rows(
                crop_type=alternative_crop, state=state, year=year, district=district, season=season
            )

            if not alternative_data:
                return {
                    "error": f"No profitability data found for {alternative_crop}",
                    "crop": alternative_crop,
                    "state": state,
                    "year": year,
                }

            # Calculate average metrics for primary crop
            primary_avg_profit = sum(d.avg_profit_per_acre for d in primary_data) / len(
                primary_data
            )
            primary_avg_investment = (
                sum(d.total_investment_cost for d in primary_data if d.total_investment_cost)
                / len([d for d in primary_data if d.total_investment_cost])
                if any(d.total_investment_cost for d in primary_data)
                else None
            )
            primary_avg_roi = (
                sum(d.roi_percentage for d in primary_data if d.roi_percentage)
                / len([d for d in primary_data if d.roi_percentage])
                if any(d.roi_percentage for d in primary_data)
                else None
            )

            # Calculate average metrics for alternative crop
            alternative_avg_profit = sum(d.avg_profit_per_acre for d in alternative_data) / len(
                alternative_data
            )
            alternative_avg_investment = (
                sum(d.total_investment_cost for d in alternative_data if d.total_investment_cost)
                / len([d for d in alternative_data if d.total_investment_cost])
                if any(d.total_investment_cost for d in alternative_data)
                else None
            )
            alternative_avg_roi = (
                sum(d.roi_percentage for d in alternative_data if d.roi_percentage)
                / len([d for d in alternative_data if d.roi_percentage])
                if any(d.roi_percentage for d in alternative_data)
                else None
            )

            # Calculate opportunity cost (profit difference)
            profit_difference = float(alternative_avg_profit - primary_avg_profit)

            # Calculate investment difference
            investment_difference = None
            if primary_avg_investment and alternative_avg_investment:
                investment_difference = float(alternative_avg_investment - primary_avg_investment)

            # Calculate ROI difference
            roi_difference = None
            if primary_avg_roi and alternative_avg_roi:
                roi_difference = float(alternative_avg_roi - primary_avg_roi)

            # Determine risk levels
            primary_risk = self._aggregate_risk_level(
                [d.risk_level for d in primary_data if d.risk_level]
            )
            alternative_risk = self._aggregate_risk_level(
                [d.risk_level for d in alternative_data if d.risk_level]
            )

            # Calculate risk-adjusted opportunity cost
            risk_factor = self._calculate_risk_factor(primary_risk, alternative_risk)
            risk_adjusted_opportunity_cost = profit_difference * risk_factor

            # Determine recommendation
            if profit_difference > 0:
                if profit_difference > 10000:  # Significant difference
                    recommendation = f"Consider switching to {alternative_crop} for ₹{abs(profit_difference):.2f} higher profit per acre"
                    recommendation_confidence = 0.85
                else:
                    recommendation = f"{alternative_crop} offers slightly better returns (₹{abs(profit_difference):.2f} per acre)"
                    recommendation_confidence = 0.65
            elif profit_difference < -5000:  # Primary is significantly better
                recommendation = f"Continue with {primary_crop} - it offers ₹{abs(profit_difference):.2f} more profit per acre"
                recommendation_confidence = 0.85
            else:
                recommendation = (
                    f"Both crops offer similar profitability - choose based on other factors"
                )
                recommendation_confidence = 0.50

            # Adjust confidence based on risk
            if alternative_risk == "high" and primary_risk == "low":
                recommendation_confidence *= 0.8

            # Generate detailed reasoning
            reasoning_points = []

            if profit_difference > 0:
                reasoning_points.append(
                    f"By choosing {primary_crop} over {alternative_crop}, you forgo ₹{abs(profit_difference):.2f} profit per acre"
                )
            else:
                reasoning_points.append(
                    f"Choosing {primary_crop} provides ₹{abs(profit_difference):.2f} more profit per acre than {alternative_crop}"
                )

            if investment_difference:
                if investment_difference > 0:
                    reasoning_points.append(
                        f"{alternative_crop} requires ₹{abs(investment_difference):.2f} more investment per acre"
                    )
                else:
                    reasoning_points.append(
                        f"{alternative_crop} requires ₹{abs(investment_difference):.2f} less investment per acre"
                    )

            if roi_difference:
                if roi_difference > 0:
                    reasoning_points.append(
                        f"{alternative_crop} offers {abs(roi_difference):.2f}% better ROI"
                    )
                else:
                    reasoning_points.append(
                        f"{primary_crop} offers {abs(roi_difference):.2f}% better ROI"
                    )

            if primary_risk != alternative_risk:
                reasoning_points.append(
                    f"Risk comparison: {primary_crop} ({primary_risk}) vs {alternative_crop} ({alternative_risk})"
                )

            result = {
                "analysis_type": "opportunity_cost",
                "location": {"state": state, "district": district, "season": season, "year": year},
                "primary_crop": {
                    "name": primary_crop,
                    "avg_profit_per_acre": float(primary_avg_profit),
                    "avg_investment": (
                        float(primary_avg_investment) if primary_avg_investment else None
                    ),
                    "avg_roi_percentage": float(primary_avg_roi) if primary_avg_roi else None,
                    "risk_level": primary_risk,
                    "data_points": len(primary_data),
                },
                "alternative_crop": {
                    "name": alternative_crop,
                    "avg_profit_per_acre": float(alternative_avg_profit),
                    "avg_investment": (
                        float(alternative_avg_investment) if alternative_avg_investment else None
                    ),
                    "avg_roi_percentage": (
                        float(alternative_avg_roi) if alternative_avg_roi else None
                    ),
                    "risk_level": alternative_risk,
                    "data_points": len(alternative_data),
                },
                "opportunity_cost": {
                    "profit_difference": profit_difference,
                    "investment_difference": investment_difference,
                    "roi_difference": roi_difference,
                    "risk_factor": float(risk_factor),
                    "risk_adjusted_cost": float(risk_adjusted_opportunity_cost),
                    "interpretation": "positive" if profit_difference > 0 else "negative",
                },
                "recommendation": {
                    "choice": alternative_crop if profit_difference > 5000 else primary_crop,
                    "message": recommendation,
                    "confidence": float(recommendation_confidence),
                    "reasoning": reasoning_points,
                },
            }

            logger.info(
                f"Calculated opportunity cost: {primary_crop} vs {alternative_crop} in {state}"
            )
            return result

        except Exception as e:
            logger.error(f"Error calculating opportunity cost: {e}")
            raise

    def calculate_multi_crop_opportunity_costs(
        self,
        primary_crop: str,
        alternative_crops: List[str],
        state: str,
        district: Optional[str] = None,
        season: Optional[str] = None,
        year: Optional[int] = None,
        top_n: int = 3,
    ) -> Dict[str, Any]:
        """
        Calculate opportunity costs for multiple alternative crops

        This helps farmers see all their options and understand the trade-offs
        of choosing one crop over multiple alternatives.

        Args:
            primary_crop: The crop being considered
            alternative_crops: List of alternative crops to compare
            state: State name
            district: District name (optional)
            season: Season filter (optional)
            year: Year for comparison (defaults to latest year)
            top_n: Number of top alternatives to highlight (default 3)

        Returns:
            Dictionary with multi-crop opportunity cost analysis
        """
        try:
            comparisons = []

            for alt_crop in alternative_crops:
                if alt_crop == primary_crop:
                    continue

                comparison = self.calculate_opportunity_cost(
                    primary_crop=primary_crop,
                    alternative_crop=alt_crop,
                    state=state,
                    district=district,
                    season=season,
                    year=year,
                )

                if "error" not in comparison:
                    comparisons.append(comparison)

            if not comparisons:
                return {
                    "error": "No valid comparisons could be made",
                    "primary_crop": primary_crop,
                    "alternative_crops": alternative_crops,
                }

            # Sort by opportunity cost (highest profit difference first)
            comparisons.sort(key=lambda x: x["opportunity_cost"]["profit_difference"], reverse=True)

            # Get top alternatives
            top_alternatives = comparisons[:top_n]

            # Calculate total opportunity cost (sum of all positive differences)
            total_opportunity_cost = sum(
                c["opportunity_cost"]["profit_difference"]
                for c in comparisons
                if c["opportunity_cost"]["profit_difference"] > 0
            )

            # Find best alternative
            best_alternative = comparisons[0] if comparisons else None

            # Generate summary
            summary = {
                "primary_crop": primary_crop,
                "location": {
                    "state": state,
                    "district": district,
                    "season": season,
                    "year": year if year else comparisons[0]["location"]["year"],
                },
                "alternatives_analyzed": len(comparisons),
                "top_alternatives": [
                    {
                        "crop": c["alternative_crop"]["name"],
                        "profit_difference": c["opportunity_cost"]["profit_difference"],
                        "roi_difference": c["opportunity_cost"]["roi_difference"],
                        "risk_level": c["alternative_crop"]["risk_level"],
                        "recommendation": c["recommendation"]["message"],
                    }
                    for c in top_alternatives
                ],
                "best_alternative": (
                    {
                        "crop": best_alternative["alternative_crop"]["name"],
                        "additional_profit": best_alternative["opportunity_cost"][
                            "profit_difference"
                        ],
                        "confidence": best_alternative["recommendation"]["confidence"],
                    }
                    if best_alternative
                    and best_alternative["opportunity_cost"]["profit_difference"] > 0
                    else None
                ),
                "total_opportunity_cost": float(total_opportunity_cost),
                "detailed_comparisons": comparisons,
                "insights": self._generate_multi_crop_insights(comparisons, primary_crop),
            }

            logger.info(
                f"Calculated multi-crop opportunity costs for {primary_crop} vs {len(alternative_crops)} alternatives"
            )
            return summary

        except Exception as e:
            logger.error(f"Error calculating multi-crop opportunity costs: {e}")
            raise

    def save_opportunity_cost_analysis(
        self,
        primary_crop: str,
        alternative_crop: str,
        state: str,
        district: Optional[str] = None,
        season: Optional[str] = None,
        year: Optional[int] = None,
    ) -> OpportunityCost:
        """
        Calculate and save opportunity cost analysis to database

        Args:
            primary_crop: The crop being considered
            alternative_crop: The alternative crop to compare
            state: State name
            district: District name (optional)
            season: Season filter (optional)
            year: Year for comparison (defaults to latest year)

        Returns:
            Created OpportunityCost instance
        """
        try:
            # Calculate opportunity cost
            analysis = self.calculate_opportunity_cost(
                primary_crop=primary_crop,
                alternative_crop=alternative_crop,
                state=state,
                district=district,
                season=season,
                year=year,
            )

            if "error" in analysis:
                raise ValueError(f"Cannot save analysis: {analysis['error']}")

            # Create opportunity cost record
            oc = analysis["opportunity_cost"]
            pc, ac = analysis["primary_crop"], analysis["alternative_crop"]
            opportunity_cost = _insert(
                "opportunity_costs",
                {
                    "location_state": state,
                    "location_district": district,
                    "primary_crop": primary_crop,
                    "alternative_crop": alternative_crop,
                    "season": season,
                    "year": analysis["location"]["year"],
                    "primary_crop_profit": _num(pc["avg_profit_per_acre"]),
                    "alternative_crop_profit": _num(ac["avg_profit_per_acre"]),
                    "profit_difference": _num(oc["profit_difference"]),
                    "primary_crop_investment": _num(pc["avg_investment"]),
                    "alternative_crop_investment": _num(ac["avg_investment"]),
                    "investment_difference": _num(oc["investment_difference"]),
                    "primary_crop_roi": _num(pc["avg_roi_percentage"]),
                    "alternative_crop_roi": _num(ac["avg_roi_percentage"]),
                    "roi_difference": _num(oc["roi_difference"]),
                    "primary_crop_risk": pc["risk_level"],
                    "alternative_crop_risk": ac["risk_level"],
                    "risk_factor": _num(oc["risk_factor"]),
                    "recommended_choice": analysis["recommendation"]["choice"],
                    "recommendation_confidence": _num(analysis["recommendation"]["confidence"]),
                    "recommendation_reasoning": "\n".join(analysis["recommendation"]["reasoning"]),
                },
            )

            logger.info(f"Saved opportunity cost analysis: {primary_crop} vs {alternative_crop}")
            return opportunity_cost

        except Exception as e:
            logger.error(f"Error saving opportunity cost analysis: {e}")
            raise

    def get_top_profitable_crops(
        self,
        state: str,
        district: Optional[str] = None,
        season: Optional[str] = None,
        year: Optional[int] = None,
        top_n: int = 3,
        include_opportunity_costs: bool = True,
    ) -> Dict[str, Any]:
        """
        Get top N most profitable crops for a location with opportunity cost analysis

        This is the core function for RAG-based crop recommendations that validates AC4:
        "RAG system suggests top 3 profitable crops with opportunity cost analysis"

        Args:
            state: State name
            district: District name (optional)
            season: Season filter (optional)
            year: Year for analysis (defaults to latest year)
            top_n: Number of top crops to return (default 3)
            include_opportunity_costs: Whether to include opportunity cost analysis

        Returns:
            Dictionary with top profitable crops and opportunity cost analysis
        """
        try:
            # Get current year if not provided
            if not year:
                max_year_result = _max_profit_year(state)

                if not max_year_result:
                    return {
                        "error": "No profitability data found for specified location",
                        "state": state,
                        "district": district,
                    }

                year = max_year_result

            # Build query for profitable crops
            all_crops_data = _profit_rows(state=state, year=year, district=district, season=season)

            if not all_crops_data:
                return {
                    "error": "No crop profitability data found",
                    "state": state,
                    "district": district,
                    "year": year,
                }

            # Group by crop type and calculate averages
            from collections import defaultdict

            crop_metrics = defaultdict(list)

            for data in all_crops_data:
                crop_metrics[data.crop_type].append(data)

            # Calculate average metrics for each crop
            crop_summaries = []
            for crop_type, data_list in crop_metrics.items():
                avg_profit = sum(d.avg_profit_per_acre for d in data_list) / len(data_list)
                avg_investment = (
                    sum(d.total_investment_cost for d in data_list if d.total_investment_cost)
                    / len([d for d in data_list if d.total_investment_cost])
                    if any(d.total_investment_cost for d in data_list)
                    else None
                )
                avg_roi = (
                    sum(d.roi_percentage for d in data_list if d.roi_percentage)
                    / len([d for d in data_list if d.roi_percentage])
                    if any(d.roi_percentage for d in data_list)
                    else None
                )
                risk_level = self._aggregate_risk_level(
                    [d.risk_level for d in data_list if d.risk_level]
                )

                crop_summaries.append(
                    {
                        "crop_type": crop_type,
                        "avg_profit_per_acre": float(avg_profit),
                        "avg_investment": float(avg_investment) if avg_investment else None,
                        "avg_roi_percentage": float(avg_roi) if avg_roi else None,
                        "risk_level": risk_level,
                        "data_points": len(data_list),
                    }
                )

            # Sort by profit and get top N
            crop_summaries.sort(key=lambda x: x["avg_profit_per_acre"], reverse=True)
            top_crops = crop_summaries[:top_n]

            result = {
                "location": {"state": state, "district": district, "season": season, "year": year},
                "top_profitable_crops": top_crops,
                "total_crops_analyzed": len(crop_summaries),
            }

            # Add opportunity cost analysis if requested
            if include_opportunity_costs and len(top_crops) >= 2:
                # Calculate opportunity costs between top crops
                opportunity_costs = []

                # Compare top crop with others
                top_crop = top_crops[0]["crop_type"]

                for i in range(1, len(top_crops)):
                    alt_crop = top_crops[i]["crop_type"]

                    opp_cost = self.calculate_opportunity_cost(
                        primary_crop=alt_crop,  # If farmer chooses this instead of top
                        alternative_crop=top_crop,  # They forgo the top crop
                        state=state,
                        district=district,
                        season=season,
                        year=year,
                    )

                    if "error" not in opp_cost:
                        opportunity_costs.append(
                            {
                                "choosing": alt_crop,
                                "forgoing": top_crop,
                                "opportunity_cost": opp_cost["opportunity_cost"][
                                    "profit_difference"
                                ],
                                "reasoning": f"Choosing {alt_crop} over {top_crop} means forgoing ₹{abs(opp_cost['opportunity_cost']['profit_difference']):.2f} per acre",
                            }
                        )

                result["opportunity_cost_analysis"] = {
                    "comparisons": opportunity_costs,
                    "recommendation": f"{top_crop} offers the highest profit potential in this location",
                    "confidence": 0.85,
                }

            logger.info(f"Retrieved top {top_n} profitable crops for {state}")
            return result

        except Exception as e:
            logger.error(f"Error getting top profitable crops: {e}")
            raise

    def _aggregate_risk_level(self, risk_levels: List[str]) -> str:
        """
        Aggregate multiple risk levels into a single risk assessment

        Args:
            risk_levels: List of risk level strings

        Returns:
            Aggregated risk level
        """
        if not risk_levels:
            return "medium"

        risk_counts = {"low": 0, "medium": 0, "high": 0}
        for level in risk_levels:
            if level and level.lower() in risk_counts:
                risk_counts[level.lower()] += 1

        # Return most common risk level
        if risk_counts["high"] > len(risk_levels) / 2:
            return "high"
        elif risk_counts["low"] > len(risk_levels) / 2:
            return "low"
        else:
            return "medium"

    def _calculate_risk_factor(self, primary_risk: str, alternative_risk: str) -> float:
        """
        Calculate risk adjustment factor for opportunity cost

        Args:
            primary_risk: Risk level of primary crop
            alternative_risk: Risk level of alternative crop

        Returns:
            Risk adjustment factor (0.5 to 1.5)
        """
        risk_values = {"low": 0.8, "medium": 1.0, "high": 1.2}

        primary_value = risk_values.get(primary_risk, 1.0)
        alternative_value = risk_values.get(alternative_risk, 1.0)

        # If alternative is riskier, reduce the opportunity cost value
        # If alternative is safer, increase the opportunity cost value
        return alternative_value / primary_value

    def _generate_multi_crop_insights(
        self, comparisons: List[Dict[str, Any]], primary_crop: str
    ) -> List[str]:
        """
        Generate insights from multi-crop opportunity cost analysis

        Args:
            comparisons: List of comparison results
            primary_crop: The primary crop being analyzed

        Returns:
            List of insight strings
        """
        insights = []

        if not comparisons:
            return insights

        # Count better alternatives
        better_alternatives = [
            c for c in comparisons if c["opportunity_cost"]["profit_difference"] > 0
        ]

        if better_alternatives:
            insights.append(
                f"Found {len(better_alternatives)} crops that offer better profitability than {primary_crop}"
            )

            # Highlight best alternative
            best = better_alternatives[0]
            insights.append(
                f"Best alternative: {best['alternative_crop']['name']} offers ₹{best['opportunity_cost']['profit_difference']:.2f} more profit per acre"
            )
        else:
            insights.append(
                f"{primary_crop} is the most profitable option among the crops analyzed"
            )

        # Risk analysis
        high_risk_better = [
            c for c in better_alternatives if c["alternative_crop"]["risk_level"] == "high"
        ]

        if high_risk_better:
            insights.append(
                f"Note: {len(high_risk_better)} higher-profit alternatives have high risk - consider risk tolerance"
            )

        # Investment analysis
        lower_investment_better = [
            c
            for c in better_alternatives
            if c["opportunity_cost"]["investment_difference"]
            and c["opportunity_cost"]["investment_difference"] < 0
        ]

        if lower_investment_better:
            insights.append(
                f"{len(lower_investment_better)} alternatives offer better profit with lower investment"
            )

        return insights


def get_market_data_service(db: Session) -> MarketDataService:
    """
    Factory function to create MarketDataService instance

    Args:
        db: Database session

    Returns:
        MarketDataService instance
    """
    return MarketDataService(db)
