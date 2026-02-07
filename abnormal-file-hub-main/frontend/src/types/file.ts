export interface File {
  id: string;
  original_filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  file: string;
  file_hash?: string;
}

export interface StorageStats {
  total_size: number;
  unique_size: number;
  saved_size: number;
  savings_percentage: number;
}