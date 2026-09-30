-- SLUSI Soil Data Integration Migration
-- Creates new SLUSI/SHC tables and adds SHC fields to farms table
-- Generated for: slusi-soil-data-integration spec, Task 1

-- ============================================================
-- New table: slusi_lcc_reports
-- ============================================================
CREATE TABLE IF NOT EXISTS slusi_lcc_reports (
    "id"                   BIGSERIAL PRIMARY KEY,
    "created_at"           TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at"           TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable"               SMALLINT NOT NULL DEFAULT 1,
    "state"                VARCHAR(100) NOT NULL,
    "district"             VARCHAR(100) NOT NULL,
    "report_no"            VARCHAR(50)  NOT NULL,
    "year"                 INTEGER NULL,
    "total_area_ha"        DECIMAL(14,2) NULL,
    "lcc_class_i"          DECIMAL(14,2) NULL,
    "lcc_class_ii"         DECIMAL(14,2) NULL,
    "lcc_class_iii"        DECIMAL(14,2) NULL,
    "lcc_class_iv"         DECIMAL(14,2) NULL,
    "lcc_class_v"          DECIMAL(14,2) NULL,
    "lcc_class_vi"         DECIMAL(14,2) NULL,
    "lcc_class_vii"        DECIMAL(14,2) NULL,
    "lcc_class_viii"       DECIMAL(14,2) NULL,
    "forest_area"          DECIMAL(14,2) NULL,
    "miscellaneous_area"   DECIMAL(14,2) NULL,
    "spatial_available"    BOOLEAN NULL DEFAULT false,
    "non_spatial_available" BOOLEAN NULL DEFAULT false,
    "ingested_at"          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT slusi_lcc_reports_state_district_report_no_unique
        UNIQUE ("state", "district", "report_no")
);

CREATE INDEX IF NOT EXISTS idx_slusi_lcc_reports_state_district
    ON slusi_lcc_reports ("state", "district");

CREATE INDEX IF NOT EXISTS idx_slusi_lcc_reports_year_desc
    ON slusi_lcc_reports ("year" DESC);

-- ============================================================
-- New table: slusi_microwatershed_maps
-- ============================================================
CREATE TABLE IF NOT EXISTS slusi_microwatershed_maps (
    "id"               BIGSERIAL PRIMARY KEY,
    "created_at"       TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at"       TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable"           SMALLINT NOT NULL DEFAULT 1,
    "state"            VARCHAR(100) NOT NULL UNIQUE,
    "map_data"         BYTEA NOT NULL,
    "file_size_bytes"  INTEGER NULL,
    "ingested_at"      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- New table: slusi_ingestion_runs
-- ============================================================
CREATE TABLE IF NOT EXISTS slusi_ingestion_runs (
    "id"                    BIGSERIAL PRIMARY KEY,
    "created_at"            TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at"            TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable"                SMALLINT NOT NULL DEFAULT 1,
    "started_at"            TIMESTAMP NOT NULL,
    "completed_at"          TIMESTAMP NULL,
    "status"                VARCHAR(20) NOT NULL,
    "lcc_records_ingested"  INTEGER NULL DEFAULT 0,
    "maps_ingested"         INTEGER NULL DEFAULT 0,
    "error_message"         TEXT NULL
);

-- ============================================================
-- New table: shc_state_district_codes
-- ============================================================
CREATE TABLE IF NOT EXISTS shc_state_district_codes (
    "id"             BIGSERIAL PRIMARY KEY,
    "created_at"     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at"     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable"         SMALLINT NOT NULL DEFAULT 1,
    "state_name"     VARCHAR(100) NOT NULL,
    "state_code"     INTEGER NOT NULL,
    "district_name"  VARCHAR(100) NOT NULL,
    "district_code"  INTEGER NOT NULL
);

-- ============================================================
-- ALTER TABLE farms — add new SHC / SLUSI columns
-- (safe: uses ADD COLUMN IF NOT EXISTS)
-- ============================================================
ALTER TABLE farms
    ADD COLUMN IF NOT EXISTS "copper"                DECIMAL(10,2) NULL,
    ADD COLUMN IF NOT EXISTS "manganese"             DECIMAL(10,2) NULL,
    ADD COLUMN IF NOT EXISTS "soil_depth_class"      VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS "slope_class"           VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS "erosion_class"         VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS "soil_texture_class"    VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS "land_capability_class" VARCHAR(10)   NULL,
    ADD COLUMN IF NOT EXISTS "land_irrigability_class" VARCHAR(10) NULL,
    ADD COLUMN IF NOT EXISTS "hydrological_soil_group" VARCHAR(10) NULL,
    ADD COLUMN IF NOT EXISTS "shc_data_source"       VARCHAR(100)  NULL,
    ADD COLUMN IF NOT EXISTS "shc_fetched_at"        TIMESTAMP     NULL,
    ADD COLUMN IF NOT EXISTS "shc_partial_data"      BOOLEAN       NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS "shc_unavailable_styles" TEXT[]       NULL;
