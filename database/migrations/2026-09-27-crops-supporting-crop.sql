-- CropSense: additive migration (2026-09-27) for supporting (inter/companion) crops.
-- Generated from database/Model/crop.json (php setup.php). Safe to re-run: only ADD COLUMN IF NOT EXISTS. Nothing is dropped.
BEGIN;

ALTER TABLE crops ADD COLUMN IF NOT EXISTS "parent_crop_id" BIGINT NULL;
ALTER TABLE crops ADD COLUMN IF NOT EXISTS "crop_role" VARCHAR(20) DEFAULT 'main';

COMMIT;
