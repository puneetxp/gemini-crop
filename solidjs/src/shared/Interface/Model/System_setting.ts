export interface System_setting {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   key: string,
   value: string,
   description: string | null
}