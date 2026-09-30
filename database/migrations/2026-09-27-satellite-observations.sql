-- CropSense: additive Cloud SQL migration (2026-09-27) for per-farm Sentinel-2 crop health readings.
-- Generated from database/structure.sql + relation.sql (php setup.php). Safe to re-run; nothing is dropped.
BEGIN;

CREATE TABLE IF NOT EXISTS satellite_observations ("id" BIGSERIAL PRIMARY KEY, "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "enable" SMALLINT NOT NULL DEFAULT 1, "farm_id" BIGINT NOT NULL, "scene_id" VARCHAR(120) NOT NULL, "observed_on" DATE NOT NULL, "source" VARCHAR(50) NOT NULL DEFAULT 'sentinel-2-l2a', "ndvi" DECIMAL(5,3) NULL, "ndmi" DECIMAL(5,3) NULL, "ndre" DECIMAL(5,3) NULL, "clear_pct" DECIMAL(5,1) NULL, "pixels" INTEGER NULL, "state" VARCHAR(100) NULL, "district" VARCHAR(100) NULL);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'satellite_observation_farm_id_foreign') THEN
    ALTER TABLE satellite_observations ADD CONSTRAINT satellite_observation_farm_id_foreign FOREIGN KEY ("farm_id") REFERENCES farms ("id");
  END IF;
END $$;

-- One reading per farm per scene (re-fetching updates it)
CREATE UNIQUE INDEX IF NOT EXISTS satellite_observations_farm_scene_uidx ON satellite_observations (farm_id, scene_id);
CREATE INDEX IF NOT EXISTS satellite_observations_place_idx ON satellite_observations (state, district, observed_on DESC);

COMMIT;
