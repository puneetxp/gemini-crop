export interface Crop_expense {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   category: string,
   amount: number,
   description: string | null,
   expense_date: Date,
   crop_id: number
}