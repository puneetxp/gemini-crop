-- Create msp_rates table
CREATE TABLE IF NOT EXISTS msp_rates (
    "id"                       BIGSERIAL PRIMARY KEY,
    "created_at"               TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at"               TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable"                   SMALLINT NOT NULL DEFAULT 1,
    "crop_name"                VARCHAR(255) NOT NULL,
    "year"                     INTEGER NOT NULL,
    "season"                   VARCHAR(50) NOT NULL,
    "msp_per_quintal"          DECIMAL(10,2) NOT NULL,
    "msp_per_kg"               DECIMAL(10,2) NULL,
    "increase_over_previous"   DECIMAL(5,2) NULL,
    "cost_of_production"       DECIMAL(10,2) NULL,
    "return_over_cost_percent" DECIMAL(5,2) NULL,
    "source"                   VARCHAR(100) NULL,
    CONSTRAINT uq_crop_year_season UNIQUE ("crop_name", "year", "season")
);

-- Index for fast lookup by crop name and year
CREATE INDEX IF NOT EXISTS idx_msp_rates_lookup ON msp_rates ("crop_name", "year");
