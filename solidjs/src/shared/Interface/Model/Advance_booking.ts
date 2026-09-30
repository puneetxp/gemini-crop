export interface Advance_booking {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   quantity_booked: number,
   price_per_unit: number,
   total_amount: number,
   advance_payment_percent: number,
   advance_payment_amount: number,
   booking_date: Date,
   expected_delivery_date: Date,
   status: string,
   quality_standards: string | null,
   contract_terms: string | null,
   listing_id: number,
   buyer_id: number,
   farmer_id: number
}