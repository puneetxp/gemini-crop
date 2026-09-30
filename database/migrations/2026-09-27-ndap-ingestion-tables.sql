-- CropSense: additive Cloud SQL migration (2026-09-27) for NDAP price-file ingestion tracking.
-- Generated from database/structure.sql (php setup.php). Safe to re-run: only CREATE TABLE IF NOT EXISTS. Nothing is dropped.
BEGIN;

CREATE TABLE IF NOT EXISTS ndap_downloaded_files ("id" BIGSERIAL PRIMARY KEY, "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "enable" SMALLINT NOT NULL DEFAULT 1, "file_name" VARCHAR(255) NOT NULL, "file_hash" VARCHAR(64) NOT NULL UNIQUE, "file_content" BYTEA NOT NULL);
CREATE TABLE IF NOT EXISTS ndap_ingestion_runs ("id" BIGSERIAL PRIMARY KEY, "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "enable" SMALLINT NOT NULL DEFAULT 1, "file_name" VARCHAR(255) NOT NULL, "file_hash" VARCHAR(64) NOT NULL UNIQUE, "started_at" TIMESTAMP NOT NULL, "completed_at" TIMESTAMP NULL, "status" VARCHAR(20) NOT NULL, "records_ingested" INTEGER NULL DEFAULT 0, "error_message" TEXT NULL);

COMMIT;
