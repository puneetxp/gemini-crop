export interface Offspring {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   birth_date: Date,
   gender: string | null,
   birth_weight: number | null,
   health_status: string,
   current_weight: number | null,
   growth_rate: number | null,
   weaning_date: Date | null,
   sale_date: Date | null,
   sale_price: number | null,
   notes: string | null,
   breeding_record_id: number,
   livestock_id: number | null,
   farmer_id: number
}