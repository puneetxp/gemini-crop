export interface Satellite_observation {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   scene_id: string,
   observed_on: Date,
   source: string,
   ndvi: number | null,
   ndmi: number | null,
   ndre: number | null,
   clear_pct: number | null,
   pixels: number | null,
   state: string | null,
   district: string | null,
   farm_id: number
}