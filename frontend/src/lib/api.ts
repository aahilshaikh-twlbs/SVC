import { Index, Video, ApiKeyConfig, UploadVideoData, CreateIndexData } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  apiKey?: string
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Use provided apiKey or get from localStorage
  const keyToUse = apiKey || localStorage.getItem('sage_api_key');
  if (keyToUse) {
    headers['X-API-Key'] = keyToUse;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers,
    ...options,
  });

  if (!response.ok) {
    throw new ApiError(
      `API request failed: ${response.statusText}`,
      response.status
    );
  }

  return response.json();
}

export const api = {
  // API Key validation and persistence
  validateApiKey: async (key: string): Promise<ApiKeyConfig> => {
    return apiRequest<ApiKeyConfig>('/validate-key', {
      method: 'POST',
      body: JSON.stringify({ key }),
    }, key);
  },

  getStoredApiKey: async (): Promise<{ has_stored_key: boolean }> => {
    return apiRequest<{ has_stored_key: boolean }>('/stored-api-key');
  },

  // Index operations
  listIndexes: async (apiKey?: string): Promise<Index[]> => {
    return apiRequest<Index[]>('/indexes', {}, apiKey);
  },

  createIndex: async (data: CreateIndexData, apiKey?: string): Promise<Index> => {
    return apiRequest<Index>('/indexes', {
      method: 'POST',
      body: JSON.stringify(data),
    }, apiKey);
  },

  renameIndex: async (indexId: string, newName: string, apiKey?: string): Promise<Index> => {
    return apiRequest<Index>(`/indexes/${indexId}`, {
      method: 'PUT',
      body: JSON.stringify({ new_name: newName }),
    }, apiKey);
  },

  deleteIndex: async (indexId: string, apiKey?: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>(`/indexes/${indexId}`, {
      method: 'DELETE',
    }, apiKey);
  },

  // Video operations
  listVideos: async (indexId: string, apiKey?: string): Promise<Video[]> => {
    return apiRequest<Video[]>(`/indexes/${indexId}/videos`, {}, apiKey);
  },

  deleteVideo: async (indexId: string, videoId: string, apiKey?: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>(`/indexes/${indexId}/videos/${videoId}`, {
      method: 'DELETE',
    }, apiKey);
  },

  uploadVideo: async (data: UploadVideoData, apiKey?: string): Promise<{ task_id: string; video_id: string }> => {
    const formData = new FormData();
    formData.append('index_id', data.index_id);
    
    if (data.file) {
      formData.append('file', data.file);
    }
    if (data.url) {
      formData.append('url', data.url);
    }

    const headers: Record<string, string> = {};
    const keyToUse = apiKey || localStorage.getItem('sage_api_key');
    if (keyToUse) {
      headers['X-API-Key'] = keyToUse;
    }

    const response = await fetch(`${API_BASE_URL}/upload-video`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(`Upload failed: ${errorData.detail || response.statusText}`, response.status);
    }

    return response.json();
  },

  // Task status checking
  checkTaskStatus: async (taskId: string, apiKey?: string): Promise<{ status: string; video_id?: string }> => {
    return apiRequest<{ status: string; video_id?: string }>(`/tasks/${taskId}`, {}, apiKey);
  },

  // Comparison functions
  compareVideos: async (data: {
    video1_id: string;
    video2_id: string;
    index_id: string;
    threshold?: number;
    distance_metric?: string;
  }, apiKey?: string): Promise<{
    video1_id: string;
    video2_id: string;
    differences: Array<{
      start_sec: number;
      end_sec: number;
      distance: number;
    }>;
    total_segments: number;
    differing_segments: number;
  }> => {
    return apiRequest('/compare-videos', {
      method: 'POST',
      body: JSON.stringify(data),
    }, apiKey);
  },
}; 