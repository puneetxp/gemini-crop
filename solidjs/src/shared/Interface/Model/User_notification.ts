export interface User_notification {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   title: string,
   message: string,
   type: string,
   link: string | null,
   data: any | null,
   is_read: boolean,
   read_at: Date | null,
   user_id: number
}