export interface Index {
  id: string;
  name: string;
  models: Model[];
  video_count: number;
  total_duration: number;
  created_at: string;
  updated_at?: string;
}

export interface Model {
  name: string;
  options: string[];
}

export interface Video {
  id: string;
  created_at: string;
  updated_at: string;
  system_metadata: SystemMetadata;
  user_metadata?: Record<string, any>;
  hls?: HLSData;
  source?: SourceData;
}

export interface SystemMetadata {
  filename: string;
  duration: number;
  fps: number;
  width: number;
  height: number;
  size: number;
}

export interface HLSData {
  video_url: string;
  thumbnail_urls?: string[];
  status: string;
  updated_at: string;
}

export interface SourceData {
  type: string;
  name: string;
  url: string;
}

export interface ApiKeyConfig {
  key: string;
  isValid: boolean;
}

export interface UploadVideoData {
  file?: File;
  url?: string;
  index_id: string;
}

export interface CreateIndexData {
  name: string;
} 