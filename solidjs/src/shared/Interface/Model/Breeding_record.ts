export interface Breeding_record {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   breeding_type: string,
   breeding_date: Date,
   mate_breed: string | null,
   expected_delivery_date: Date | null,
   actual_delivery_date: Date | null,
   pregnancy_status: string,
   number_of_offspring: number | null,
   breeding_cost: number | null,
   veterinarian_name: string | null,
   notes: string | null,
   livestock_id: number,
   farmer_id: number,
   mate_id: number | null
}