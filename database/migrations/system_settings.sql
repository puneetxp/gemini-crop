-- Create system_settings table
CREATE TABLE IF NOT EXISTS system_settings (
    "id"          BIGSERIAL PRIMARY KEY,
    "created_at"  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at"  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable"      SMALLINT NOT NULL DEFAULT 1,
    "key"         VARCHAR(255) NOT NULL UNIQUE,
    "value"       TEXT NOT NULL,
    "description" TEXT NULL
);

-- Seed initial API keys
INSERT INTO system_settings ("key", "value", "description")
VALUES 
    ('DATAGOV_API_KEY', '579b464db66ec23bdd0000012cdbe49ab3c940207a454cd85898720b', 'API Key for data.gov.in mandi price tracking'),
    ('DATAGOV_MOISTURE_API_KEY', '579b464db66ec23bdd0000012cdbe49ab3c940207a454cd85898720b', 'API Key for data.gov.in soil moisture tracking')
ON CONFLICT ("key") DO UPDATE 
SET "value" = EXCLUDED.value;
