export interface Slusi_microwatershed_map {
   id: number,
   created_at: Date,
   updated_at: Date,
   enable: number,
   state: string,
   map_data: string,
   file_size_bytes: number | null,
   ingested_at: Date
}