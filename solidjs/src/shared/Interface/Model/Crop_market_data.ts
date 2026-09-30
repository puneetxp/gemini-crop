export interface Crop_market_data {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   crop_name: string,
   state: string,
   district: string | null,
   price_per_kg: number,
   date: Date,
   season: string,
   yoy_growth: number | null,
   demand_level: string | null
}