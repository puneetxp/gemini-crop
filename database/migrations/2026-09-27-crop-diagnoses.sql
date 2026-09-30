-- CropSense: additive Cloud SQL migration (2026-09-27) for crop photo diagnoses.
-- Generated from database/structure.sql + relation.sql (php setup.php). Safe to re-run; nothing is dropped.
BEGIN;

CREATE TABLE IF NOT EXISTS crop_diagnoses ("id" BIGSERIAL PRIMARY KEY, "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "enable" SMALLINT NOT NULL DEFAULT 1, "user_id" BIGINT NOT NULL, "crop_id" BIGINT NULL, "farm_id" BIGINT NULL, "crop_name" VARCHAR(100) NULL, "state" VARCHAR(100) NULL, "district" VARCHAR(100) NULL, "disease_name" VARCHAR(255) NULL, "scientific_name" VARCHAR(255) NULL, "category" VARCHAR(30) NULL, "severity" VARCHAR(20) NULL, "urgency" VARCHAR(20) NULL, "confidence" DECIMAL(4,3) NULL, "language" VARCHAR(10) NULL, "model_used" VARCHAR(100) NULL, "safety_flags" INTEGER NOT NULL DEFAULT 0, "result" JSONB NULL);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'crop_diagnosis_user_id_foreign') THEN
    ALTER TABLE crop_diagnoses ADD CONSTRAINT crop_diagnosis_user_id_foreign FOREIGN KEY ("user_id") REFERENCES users ("id");
  END IF;
END $$;

-- District/state outbreak views read by place and time
CREATE INDEX IF NOT EXISTS crop_diagnoses_place_idx ON crop_diagnoses (state, district, created_at DESC);
CREATE INDEX IF NOT EXISTS crop_diagnoses_user_idx ON crop_diagnoses (user_id, created_at DESC);

COMMIT;
