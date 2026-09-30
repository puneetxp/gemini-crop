export interface Msp_rate {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   crop_name: string,
   year: number,
   season: string,
   msp_per_quintal: number,
   msp_per_kg: number | null,
   increase_over_previous: number | null,
   cost_of_production: number | null,
   return_over_cost_percent: number | null,
   source: string | null
}