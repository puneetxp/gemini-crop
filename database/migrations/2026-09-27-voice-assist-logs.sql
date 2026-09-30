-- CropSense: additive Cloud SQL migration (2026-09-27) for the voice/assistant log.
-- Generated from database/structure.sql + relation.sql (php setup.php). Safe to re-run; nothing is dropped.
BEGIN;

CREATE TABLE IF NOT EXISTS voice_assist_logs ("id" BIGSERIAL PRIMARY KEY, "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "enable" SMALLINT NOT NULL DEFAULT 1, "user_id" BIGINT NOT NULL, "source" VARCHAR(20) NOT NULL DEFAULT 'text', "task" VARCHAR(50) NULL, "ui_lang" VARCHAR(10) NULL, "language_detected" VARCHAR(10) NULL, "mime_type" VARCHAR(50) NULL, "audio_bytes" INTEGER NULL, "duration_ms" INTEGER NULL, "transcript" TEXT NULL, "intent" VARCHAR(20) NULL, "model_used" VARCHAR(100) NULL, "status" VARCHAR(20) NOT NULL DEFAULT 'ok', "error" TEXT NULL, "latency_ms" INTEGER NULL);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'voice_assist_log_user_id_foreign') THEN
    ALTER TABLE voice_assist_logs ADD CONSTRAINT voice_assist_log_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS voice_assist_logs_user_created_idx ON voice_assist_logs (user_id, created_at DESC);

COMMIT;
