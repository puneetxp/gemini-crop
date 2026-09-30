-- Create soil_moisture_data table
CREATE TABLE IF NOT EXISTS soil_moisture_data (
    "id"             BIGSERIAL PRIMARY KEY,
    "created_at"     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at"     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable"         SMALLINT NOT NULL DEFAULT 1,
    "state"          VARCHAR(100) NOT NULL,
    "district"       VARCHAR(100) NOT NULL,
    "date"           DATE NOT NULL,
    "year"           INTEGER NOT NULL,
    "month"          VARCHAR(2) NOT NULL,
    "moisture_level" DECIMAL(10,4) NOT NULL,
    "agency_name"    VARCHAR(255) NULL,
    CONSTRAINT uq_state_district_date UNIQUE ("state", "district", "date")
);

-- Index for fast lookup by state and district
CREATE INDEX IF NOT EXISTS idx_soil_moisture_lookup ON soil_moisture_data (LOWER(state), LOWER(district));
