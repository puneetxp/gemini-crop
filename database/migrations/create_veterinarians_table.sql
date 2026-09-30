-- Veterinarian directory: lets farmers add/find a livestock doctor and connect
-- with them by phone, WhatsApp, or email.

CREATE TABLE IF NOT EXISTS veterinarians (
    "id" BIGSERIAL PRIMARY KEY,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable" SMALLINT NOT NULL DEFAULT 1,
    "added_by_user_id" BIGINT NULL,
    "name" VARCHAR(255) NOT NULL,
    "clinic_name" VARCHAR(255) NULL,
    "specialization" VARCHAR(100) NULL,
    "species_supported" TEXT NULL, -- JSON array: cattle, buffalo, goat, poultry, ...
    "phone" VARCHAR(20) NOT NULL,
    "whatsapp" VARCHAR(20) NULL,
    "email" VARCHAR(255) NULL,
    "location_state" VARCHAR(100) NULL,
    "location_district" VARCHAR(100) NULL,
    "address" TEXT NULL,
    "available_now" SMALLINT NOT NULL DEFAULT 1,
    "verified" SMALLINT NOT NULL DEFAULT 0,
    "rating" DECIMAL(3,2) DEFAULT 0,
    "total_ratings" INTEGER DEFAULT 0,
    "notes" TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_veterinarians_location ON veterinarians (location_state, location_district);
