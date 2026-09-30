#!/bin/bash

# Fix users table schema to match generated structure.sql
# This script drops and recreates the users table with BIGINT IDs

set -e  # Exit on error

echo "========================================="
echo "Fixing Users Table Schema"
echo "========================================="
echo ""

# Database connection details
DB_NAME="cropsense_dev"
DB_USER="puneetsharma"

echo "Step 1: Backing up current users table..."
psql -U $DB_USER -d $DB_NAME -c "CREATE TABLE IF NOT EXISTS users_backup_$(date +%Y%m%d_%H%M%S) AS SELECT * FROM users;" || echo "No existing users table to backup"

echo ""
echo "Step 2: Dropping and recreating users table with correct schema..."
psql -U $DB_USER -d $DB_NAME -f fix_users_table_schema.sql

echo ""
echo "========================================="
echo "Users Table Fix Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "- Users table recreated with BIGINT ID"
echo "- Test user created: puneetxp / Pa\$w0rd!"
echo "- Email: puneet@example.com"
echo ""
echo "Next steps:"
echo "1. Run E2E tests to verify authentication works"
echo "2. If tests pass, proceed with sequential test execution"
echo ""
