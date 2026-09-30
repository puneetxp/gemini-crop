export interface Soil_moisture_data {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   state: string,
   district: string,
   date: Date,
   year: number,
   month: string,
   moisture_level: number,
   agency_name: string | null
}