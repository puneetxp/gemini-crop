export interface Livestock_health_record {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   record_type: string,
   record_date: Date,
   description: string,
   veterinarian_name: string | null,
   cost: number | null,
   next_due_date: Date | null,
   notes: string | null,
   livestock_id: number
}