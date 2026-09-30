export interface Quality_verification {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   verification_date: Date,
   verifier_type: string,
   quality_grade: string,
   quality_metrics: string | null,
   photos: string | null,
   passed: boolean,
   notes: string | null,
   booking_id: number
}