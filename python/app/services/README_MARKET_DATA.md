# Market Data Ingestion Service

## Overview

The Market Data Ingestion Service provides a comprehensive solution for ingesting, validating, and managing historical crop market data for RAG-based market intelligence. This service is a core component of the Rural Farming Platform's market intelligence system.

## Features

### 1. Crop Market Data Ingestion
- Historical crop price data (average, min, max, modal prices)
- Market metrics (demand score, supply volume, price volatility)
- Trend analysis (YoY and MoM price changes)
- Location-based data (state, district, market)
- Seasonal data (kharif, rabi, zaid)

### 2. Historical Yield Data
- Yield performance by crop and location
- Success rates and farmer statistics
- Growing conditions (soil, irrigation, weather)
- Quality metrics and distributions

### 3. Crop Profitability Data
- Profit margins and ROI calculations
- Detailed cost breakdowns
- Revenue and investment metrics
- Risk assessments

### 4. Data Validation
- Required field validation
- Data type and range validation
- Business logic validation
- Error handling and reporting

### 5. Bulk Import Support
- Efficient batch processing
- Error handling with skip_errors option
- Detailed error reporting
- Transaction management

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   API Layer                             │
│  /market-data/crop-prices                       │
│  /market-data/crop-prices/bulk                  │
│  /market-data/historical-yields                 │
│  /market-data/crop-profitability                │
│  /market-data/summary                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              MarketDataService                          │
│  - ingest_crop_market_data()                           │
│  - bulk_ingest_crop_market_data()                      │
│  - ingest_historical_yield()                           │
│  - ingest_crop_profitability()                         │
│  - get_market_data_summary()                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              Database Models                            │
│  - CropMarketData                                       │
│  - HistoricalYield                                      │
│  - CropProfitability                                    │
│  - SeasonalTrend                                        │
│  - OpportunityCost                                      │
└─────────────────────────────────────────────────────────┘
```

## Usage

### 1. Single Record Ingestion

```python
from app.services.market_data_service import MarketDataService
from app.core.database import SessionLocal

db = SessionLocal()
service = MarketDataService(db)

# Ingest single crop market data
data = {
    "crop_type": "Wheat",
    "variety": "HD-2967",
    "state": "Punjab",
    "district": "Ludhiana",
    "year": 2023,
    "month": 4,
    "season": "rabi",
    "avg_price_per_quintal": 2150.50,
    "min_price": 2000.00,
    "max_price": 2300.00,
    "market_demand_score": 0.85,
    "price_trend": "increasing",
    "yoy_price_change": 8.5,
    "data_source": "AGMARKNET"
}

market_data = service.ingest_crop_market_data(data, validate=True)
print(f"Ingested: {market_data.id}")
```

### 2. Bulk Ingestion

```python
# Bulk ingest multiple records
data_list = [
    {
        "crop_type": "Wheat",
        "state": "Punjab",
        "year": 2023,
        "avg_price_per_quintal": 2150.50
    },
    {
        "crop_type": "Rice",
        "state": "Punjab",
        "year": 2023,
        "avg_price_per_quintal": 3500.00
    }
]

result = service.bulk_ingest_crop_market_data(
    data_list,
    validate=True,
    skip_errors=False
)

print(f"Success: {result['success_count']}")
print(f"Errors: {result['error_count']}")
```

### 3. API Usage

#### Ingest Single Record
```bash
curl -X POST "http://localhost:8000/market-data/crop-prices" \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Wheat",
    "state": "Punjab",
    "year": 2023,
    "avg_price_per_quintal": 2150.50
  }'
```

#### Bulk Ingestion
```bash
curl -X POST "http://localhost:8000/market-data/crop-prices/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "crop_type": "Wheat",
        "state": "Punjab",
        "year": 2023,
        "avg_price_per_quintal": 2150.50
      },
      {
        "crop_type": "Rice",
        "state": "Punjab",
        "year": 2023,
        "avg_price_per_quintal": 3500.00
      }
    ],
    "skip_errors": false
  }'
```

#### Get Summary
```bash
curl -X GET "http://localhost:8000/market-data/summary?state=Punjab&year=2023"
```

### 4. Sample Data Ingestion Script

Run the sample data ingestion script to populate the database with test data:

```bash
cd crop-intelligence-platform/backend
python scripts/ingest_sample_market_data.py
```

## Data Models

### CropMarketData
- **Purpose**: Store historical crop price and market data
- **Key Fields**: crop_type, state, year, avg_price_per_quintal, market_demand_score
- **Indexes**: Optimized for location and time-based queries

### HistoricalYield
- **Purpose**: Store crop yield performance data
- **Key Fields**: crop_type, state, year, avg_yield_per_acre, success_rate
- **Use Cases**: Yield prediction, performance analysis

### CropProfitability
- **Purpose**: Store profitability and cost analysis
- **Key Fields**: crop_type, state, year, avg_profit_per_acre, roi_percentage
- **Use Cases**: ROI calculations, opportunity cost analysis

## Validation Rules

### Required Fields
- **CropMarketData**: crop_type, state, year, avg_price_per_quintal
- **HistoricalYield**: crop_type, state, year, avg_yield_per_acre
- **CropProfitability**: crop_type, state, year, avg_profit_per_acre

### Data Constraints
- Year: 1900 to current year
- Month: 1-12 (if provided)
- Season: kharif, rabi, or zaid
- Prices: Must be positive values
- Market demand score: 0.0 to 1.0
- Min/Max validation: min ≤ max

## Error Handling

### Validation Errors
```python
try:
    service.ingest_crop_market_data(data)
except ValueError as e:
    print(f"Validation error: {e}")
```

### Database Errors
```python
from sqlalchemy.exc import IntegrityError

try:
    service.ingest_crop_market_data(data)
except IntegrityError as e:
    print(f"Database constraint violated: {e}")
```

### Bulk Ingestion with Error Handling
```python
result = service.bulk_ingest_crop_market_data(
    data_list,
    skip_errors=True  # Continue processing on errors
)

# Check for errors
if result['error_count'] > 0:
    for error in result['errors']:
        print(f"Record {error['index']}: {error['error']}")
```

## Integration with RAG System

The market data ingestion service feeds data into the RAG-based market intelligence system:

1. **Data Collection**: Ingest historical data from various sources
2. **Storage**: Store in PostgreSQL with optimized indexes
3. **Retrieval**: Query data for crop recommendations
4. **Analysis**: Calculate YoY trends, opportunity costs, profitability
5. **Recommendations**: Generate AI-powered crop suggestions

## Performance Considerations

### Bulk Ingestion
- Use bulk_ingest for large datasets (100+ records)
- Set skip_errors=True for resilient imports
- Process in batches of 1000-5000 records

### Database Optimization
- Indexes on crop_type, state, year for fast queries
- Composite indexes for common query patterns
- Regular VACUUM and ANALYZE for PostgreSQL

### Caching
- Cache frequently accessed summary statistics
- Use Redis for market data queries
- Implement TTL-based cache invalidation

## Data Sources

### Supported Sources
1. **AGMARKNET**: Government agricultural market data
2. **Manual Entry**: Farmer-reported data
3. **API Integration**: External market data APIs
4. **CSV/Excel Import**: Bulk data files
5. **Agricultural Surveys**: Research data

### Data Quality
- Track data_source for each record
- Maintain data_quality_score (0.0-1.0)
- Validate against known patterns
- Flag anomalies for review

## Future Enhancements

1. **Real-time Data Integration**: Live market price feeds
2. **Data Validation ML**: Anomaly detection using ML
3. **Automated Data Collection**: Scheduled scraping/API calls
4. **Data Enrichment**: Combine multiple sources
5. **Historical Analysis**: Time-series forecasting
6. **Data Visualization**: Charts and trends dashboard

## Testing

### Unit Tests
```bash
pytest tests/services/test_market_data_service.py
```

### Integration Tests
```bash
pytest tests/api/test_market_data_api.py
```

### Sample Data
```bash
python scripts/ingest_sample_market_data.py
```

## Troubleshooting

### Common Issues

1. **Validation Errors**: Check required fields and data types
2. **Database Errors**: Verify database connection and schema
3. **Duplicate Data**: Check for existing records before insert
4. **Performance Issues**: Use bulk ingestion for large datasets

### Logging

Enable debug logging to troubleshoot issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues or questions:
- Check API documentation: `/docs` endpoint
- Review error messages in logs
- Consult database schema documentation
- Contact development team

## License

Part of the Rural Farming & Livestock Management Platform
