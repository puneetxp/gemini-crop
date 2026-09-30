export interface Crop_milestone {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   stage: string,
   expected_start_date: Date,
   expected_end_date: Date,
   actual_start_date: Date | null,
   actual_end_date: Date | null,
   status: string | null,
   progress_percentage: number | null,
   recommendations: string | null,
   notes: string | null,
   alert_sent: boolean | null,
   crop_id: number
}