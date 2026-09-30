export interface Slusi_ingestion_run {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   started_at: Date,
   completed_at: Date | null,
   status: string,
   lcc_records_ingested: number | null,
   maps_ingested: number | null,
   error_message: string | null
}