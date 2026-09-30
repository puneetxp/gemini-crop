export interface Payment_milestone {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   milestone_type: string,
   amount: number,
   due_date: Date,
   paid_date: Date | null,
   status: string,
   payment_method: string | null,
   transaction_id: string | null,
   booking_id: number
}