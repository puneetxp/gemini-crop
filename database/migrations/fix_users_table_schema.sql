-- Fix users table schema to match generated structure.sql
-- This script drops and recreates the users table with the correct BIGINT schema

-- Drop the users table (this will also drop dependent foreign keys)
DROP TABLE IF EXISTS users CASCADE;

-- Recreate users table with correct schema from structure.sql
CREATE TABLE IF NOT EXISTS users (
    "id" BIGSERIAL PRIMARY KEY,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable" SMALLINT NOT NULL DEFAULT 1,
    "cognito_user_id" VARCHAR(255) UNIQUE NOT NULL COMMENT 'Amazon Cognito User Pool ID',
    "username" VARCHAR(100) NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) UNIQUE NULL,
    "phone" VARCHAR(255) UNIQUE NULL,
    "google_id" VARCHAR(255) NULL COMMENT 'Google OAuth ID for social login',
    "facebook_id" VARCHAR(255) NULL COMMENT 'Facebook OAuth ID for social login',
    "password" VARCHAR(255) NULL COMMENT 'Hashed password for traditional login',
    "user_type" VARCHAR(255) DEFAULT 'farmer' COMMENT 'farmer, buyer, admin',
    "preferred_language" VARCHAR(255) DEFAULT 'en' COMMENT 'en, hi, ta, te, mr, bn',
    "mfa_enabled" SMALLINT DEFAULT 0,
    "latitude" DECIMAL(10,8) NULL COMMENT 'Personal address GPS latitude (optional)',
    "longitude" DECIMAL(11,8) NULL COMMENT 'Personal address GPS longitude (optional)',
    "pincode" VARCHAR(10) NULL COMMENT 'Postal code for address',
    "state" VARCHAR(100) NULL COMMENT 'State name',
    "district" VARCHAR(100) NULL COMMENT 'District name',
    "village" VARCHAR(100) NULL COMMENT 'Village/VPO name',
    "address_line" VARCHAR(255) NULL COMMENT 'Full address (house/building, street, landmark)'
);

-- Create test user for E2E tests
INSERT INTO users (
    cognito_user_id,
    username,
    name,
    email,
    phone,
    user_type,
    password,
    enable
) VALUES (
    'test-user-cognito-id',
    'puneetxp',
    'Puneet Sharma',
    'puneet@example.com',
    '+919876543210',
    'farmer',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIr.oXkQKu',  -- hashed 'Pa$w0rd!'
    1
);

-- Verify the table structure
\d users;

-- Show the test user
SELECT id, cognito_user_id, username, name, email FROM users;
