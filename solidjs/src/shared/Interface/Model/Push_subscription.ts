export interface Push_subscription {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   user_id: number,
   endpoint: string,
   p256dh: string,
   auth: string,
   user_agent: string | null
}