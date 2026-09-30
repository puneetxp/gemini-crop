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

-- API keys are not seeded here. Set DATAGOV_API_KEY / DATAGOV_MOISTURE_API_KEY as environment
-- variables (Secret Manager on Cloud Run), or insert them into this table per deployment:
--   INSERT INTO system_settings ("key", "value", "description")
--   VALUES ('DATAGOV_API_KEY', '<your data.gov.in key>', 'API Key for data.gov.in mandi price tracking')
--   ON CONFLICT ("key") DO UPDATE SET "value" = EXCLUDED.value;
