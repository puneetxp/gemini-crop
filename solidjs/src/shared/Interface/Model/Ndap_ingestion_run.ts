export interface Ndap_ingestion_run {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   file_name: string,
   file_hash: string,
   started_at: Date,
   completed_at: Date | null,
   status: string,
   records_ingested: number | null,
   error_message: string | null
}