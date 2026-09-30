-- Migration: Convert UUID columns to BIGINT with auto-increment
-- This fixes the mismatch between generated schema (BIGSERIAL) and actual database (UUID)

-- BACKUP FIRST! Run: pg_dump -U puneetsharma cropsense_dev > backup_before_migration.sql

BEGIN;

-- Step 1: Create sequences for auto-increment
CREATE SEQUENCE IF NOT EXISTS users_id_seq;
CREATE SEQUENCE IF NOT EXISTS farms_id_seq;
CREATE SEQUENCE IF NOT EXISTS farm_plots_id_seq;

-- Step 2: Migrate users table (if needed)
-- Check if users.id is UUID
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'id' AND data_type = 'uuid'
    ) THEN
        -- Create temporary bigint column
        ALTER TABLE users ADD COLUMN id_new BIGINT;
        
        -- Generate sequential IDs for existing records
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as new_id
            FROM users
        )
        UPDATE users u
        SET id_new = n.new_id
        FROM numbered n
        WHERE u.id = n.id;
        
        -- Update foreign keys in other tables first
        ALTER TABLE farms ADD COLUMN owner_id_new BIGINT;
        UPDATE farms f
        SET owner_id_new = u.id_new
        FROM users u
        WHERE f.owner_id = u.id;
        
        -- Drop old foreign key constraints
        ALTER TABLE farms DROP CONSTRAINT IF EXISTS farms_owner_id_fkey;
        
        -- Drop old columns
        ALTER TABLE farms DROP COLUMN owner_id;
        ALTER TABLE users DROP COLUMN id;
        
        -- Rename new columns
        ALTER TABLE users RENAME COLUMN id_new TO id;
        ALTER TABLE farms RENAME COLUMN owner_id_new TO owner_id;
        
        -- Set sequence and defaults
        ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq');
        SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 0) + 1);
        
        -- Add primary key
        ALTER TABLE users ADD PRIMARY KEY (id);
        
        RAISE NOTICE 'Users table migrated from UUID to BIGINT';
    ELSE
        RAISE NOTICE 'Users table already uses BIGINT, skipping';
    END IF;
END $$;

-- Step 3: Migrate farms table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'farms' AND column_name = 'id' AND data_type = 'uuid'
    ) THEN
        -- Create temporary bigint column
        ALTER TABLE farms ADD COLUMN id_new BIGINT;
        
        -- Generate sequential IDs for existing records
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as new_id
            FROM farms
        )
        UPDATE farms f
        SET id_new = n.new_id
        FROM numbered n
        WHERE f.id = n.id;
        
        -- Update foreign keys in other tables
        ALTER TABLE farm_plots ADD COLUMN farm_id_new BIGINT;
        UPDATE farm_plots fp
        SET farm_id_new = f.id_new
        FROM farms f
        WHERE fp.farm_id = f.id;
        
        ALTER TABLE crops ADD COLUMN farm_plot_id_new BIGINT;
        UPDATE crops c
        SET farm_plot_id_new = fp.id_new
        FROM farm_plots fp
        WHERE c.farm_plot_id = fp.id;
        
        -- Drop old foreign key constraints
        ALTER TABLE farm_plots DROP CONSTRAINT IF EXISTS farm_plots_farm_id_fkey;
        ALTER TABLE crops DROP CONSTRAINT IF EXISTS crops_farm_plot_id_fkey;
        
        -- Drop old columns
        ALTER TABLE farm_plots DROP COLUMN farm_id;
        ALTER TABLE crops DROP COLUMN farm_plot_id;
        ALTER TABLE farms DROP COLUMN id;
        
        -- Rename new columns
        ALTER TABLE farms RENAME COLUMN id_new TO id;
        ALTER TABLE farm_plots RENAME COLUMN farm_id_new TO farm_id;
        ALTER TABLE crops RENAME COLUMN farm_plot_id_new TO farm_plot_id;
        
        -- Set sequence and defaults
        ALTER TABLE farms ALTER COLUMN id SET DEFAULT nextval('farms_id_seq');
        SELECT setval('farms_id_seq', COALESCE((SELECT MAX(id) FROM farms), 0) + 1);
        
        -- Add primary key
        ALTER TABLE farms ADD PRIMARY KEY (id);
        
        -- Recreate foreign keys
        ALTER TABLE farms ADD CONSTRAINT farms_owner_id_fkey 
            FOREIGN KEY (owner_id) REFERENCES users(id);
        
        RAISE NOTICE 'Farms table migrated from UUID to BIGINT';
    ELSE
        RAISE NOTICE 'Farms table already uses BIGINT, skipping';
    END IF;
END $$;

-- Step 4: Migrate farm_plots table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'farm_plots' AND column_name = 'id' AND data_type = 'uuid'
    ) THEN
        ALTER TABLE farm_plots ADD COLUMN id_new BIGINT;
        
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as new_id
            FROM farm_plots
        )
        UPDATE farm_plots fp
        SET id_new = n.new_id
        FROM numbered n
        WHERE fp.id = n.id;
        
        ALTER TABLE farm_plots DROP COLUMN id;
        ALTER TABLE farm_plots RENAME COLUMN id_new TO id;
        
        ALTER TABLE farm_plots ALTER COLUMN id SET DEFAULT nextval('farm_plots_id_seq');
        SELECT setval('farm_plots_id_seq', COALESCE((SELECT MAX(id) FROM farm_plots), 0) + 1);
        
        ALTER TABLE farm_plots ADD PRIMARY KEY (id);
        
        -- Recreate foreign key
        ALTER TABLE farm_plots ADD CONSTRAINT farm_plots_farm_id_fkey 
            FOREIGN KEY (farm_id) REFERENCES farms(id);
        
        RAISE NOTICE 'Farm_plots table migrated from UUID to BIGINT';
    ELSE
        RAISE NOTICE 'Farm_plots table already uses BIGINT, skipping';
    END IF;
END $$;

COMMIT;

-- Verify migration
SELECT 
    table_name, 
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns 
WHERE table_name IN ('users', 'farms', 'farm_plots') 
  AND column_name = 'id'
ORDER BY table_name;
