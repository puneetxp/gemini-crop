#!/bin/bash

# Script to recreate database with BIGSERIAL (correct schema)
# This drops all tables and recreates them with the generated schema

echo "⚠️  WARNING: This will DROP ALL TABLES and recreate them!"
echo "Make sure you have a backup if you need the data."
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

DB_NAME="cropsense_dev"
DB_USER="puneetsharma"

echo ""
echo "🗑️  Dropping all tables..."

# Drop all tables in correct order (respecting foreign keys)
psql -U $DB_USER -d $DB_NAME << 'EOF'
DROP TABLE IF EXISTS payment_milestones CASCADE;
DROP TABLE IF EXISTS quality_verifications CASCADE;
DROP TABLE IF EXISTS advance_bookings CASCADE;
DROP TABLE IF EXISTS buyer_interests CASCADE;
DROP TABLE IF EXISTS direct_contacts CASCADE;
DROP TABLE IF EXISTS livestock_transactions CASCADE;
DROP TABLE IF EXISTS livestock_listings CASCADE;
DROP TABLE IF EXISTS livestock_marketplace_listings CASCADE;
DROP TABLE IF EXISTS livestock_health_records CASCADE;
DROP TABLE IF EXISTS livestock CASCADE;
DROP TABLE IF EXISTS market_prices CASCADE;
DROP TABLE IF EXISTS price_predictions CASCADE;
DROP TABLE IF EXISTS marketplace_listings CASCADE;
DROP TABLE IF EXISTS listings CASCADE;
DROP TABLE IF EXISTS pest_disease_alerts CASCADE;
DROP TABLE IF EXISTS pest_disease_data CASCADE;
DROP TABLE IF EXISTS fertilizer_applications CASCADE;
DROP TABLE IF EXISTS soil_test_results CASCADE;
DROP TABLE IF EXISTS crop_milestones CASCADE;
DROP TABLE IF EXISTS crops CASCADE;
DROP TABLE IF EXISTS annual_crop_strategies CASCADE;
DROP TABLE IF EXISTS annual_strategies CASCADE;
DROP TABLE IF EXISTS farm_plots CASCADE;
DROP TABLE IF EXISTS farms CASCADE;
DROP TABLE IF EXISTS crop_market_data CASCADE;
DROP TABLE IF EXISTS ai_usage_quota CASCADE;
DROP TABLE IF EXISTS user_activities CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS active_roles CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop sequences
DROP SEQUENCE IF EXISTS users_id_seq CASCADE;
DROP SEQUENCE IF EXISTS farms_id_seq CASCADE;
DROP SEQUENCE IF EXISTS farm_plots_id_seq CASCADE;

\echo '✅ All tables dropped'
EOF

echo ""
echo "📦 Creating tables with BIGSERIAL schema..."

# Apply the generated schema
psql -U $DB_USER -d $DB_NAME -f database/structure.sql

echo ""
echo "✅ Database recreated with BIGSERIAL!"
echo ""
echo "🔍 Verifying schema..."

psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    table_name, 
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns 
WHERE table_name IN ('users', 'farms', 'farm_plots') 
  AND column_name = 'id'
ORDER BY table_name;
"

echo ""
echo "✅ Done! Database now uses BIGSERIAL for IDs."
