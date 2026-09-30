-- Comprehensive Migration: Convert ALL UUID columns to BIGINT
-- This handles all foreign key dependencies

-- BACKUP FIRST! Run: pg_dump -U puneetsharma cropsense_dev > backup_before_migration.sql

BEGIN;

-- Drop all foreign key constraints first
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT conname, conrelid::regclass AS table_name
        FROM pg_constraint
        WHERE contype = 'f'
    ) LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT IF EXISTS %I CASCADE', r.table_name, r.conname);
    END LOOP;
END $$;

-- Create sequences
CREATE SEQUENCE IF NOT EXISTS users_id_seq;
CREATE SEQUENCE IF NOT EXISTS farms_id_seq;
CREATE SEQUENCE IF NOT EXISTS farm_plots_id_seq;

-- Migrate users table
ALTER TABLE users ADD COLUMN id_new BIGSERIAL;
UPDATE users SET id_new = (SELECT ROW_NUMBER() OVER (ORDER BY created_at) FROM users u2 WHERE u2.id = users.id);
ALTER TABLE users DROP COLUMN id CASCADE;
ALTER TABLE users RENAME COLUMN id_new TO id;
ALTER TABLE users ADD PRIMARY KEY (id);

-- Migrate farms table  
ALTER TABLE farms ADD COLUMN id_new BIGSERIAL;
ALTER TABLE farms ADD COLUMN owner_id_new BIGINT;
UPDATE farms f SET id_new = (SELECT ROW_NUMBER() OVER (ORDER BY created_at) FROM farms f2 WHERE f2.id = f.id);
UPDATE farms f SET owner_id_new = u.id FROM users u WHERE f.owner_id::text = u.id::text;
ALTER TABLE farms DROP COLUMN id CASCADE;
ALTER TABLE farms DROP COLUMN owner_id CASCADE;
ALTER TABLE farms RENAME COLUMN id_new TO id;
ALTER TABLE farms RENAME COLUMN owner_id_new TO owner_id;
ALTER TABLE farms ADD PRIMARY 