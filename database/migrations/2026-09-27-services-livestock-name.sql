-- CropSense: additive Cloud SQL migration (2026-09-27) for the services directory and livestock name.
-- Generated from database/structure.sql + insert.sql (php setup.php). Safe to re-run:
-- only CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS and an insert skipped when the row exists. Nothing is dropped.
BEGIN;

CREATE TABLE IF NOT EXISTS services ("id" BIGSERIAL PRIMARY KEY, "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "enable" SMALLINT NOT NULL DEFAULT 1, "category" VARCHAR(50) NOT NULL, "name" VARCHAR(255) NOT NULL, "organisation" VARCHAR(255) NULL, "description" TEXT NULL, "phone" VARCHAR(20) NOT NULL, "whatsapp" VARCHAR(20) NULL, "email" VARCHAR(255) NULL, "location_state" VARCHAR(100) NULL, "location_district" VARCHAR(100) NULL, "address" TEXT NULL, "languages" VARCHAR(100) NULL, "available_now" SMALLINT NOT NULL DEFAULT 1, "verified" SMALLINT NOT NULL DEFAULT 0, "is_active" SMALLINT NOT NULL DEFAULT 1, "added_by_user_id" BIGINT NULL, "user_id" BIGINT NULL);

ALTER TABLE livestock ADD COLUMN IF NOT EXISTS "name" VARCHAR(100) NULL;

-- roles.name has no unique constraint, so guard the insert instead of ON CONFLICT
INSERT INTO roles (name) SELECT 'service_provider' WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'service_provider');

COMMIT;
