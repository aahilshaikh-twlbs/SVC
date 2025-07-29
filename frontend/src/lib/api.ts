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
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
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
    });
  },

  getStoredApiKey: async (): Promise<{ has_stored_key: boolean }> => {
    return apiRequest<{ has_stored_key: boolean }>('/stored-api-key');
  },

  // Index operations
  listIndexes: async (): Promise<Index[]> => {
    return apiRequest<Index[]>('/indexes');
  },

  createIndex: async (data: CreateIndexData): Promise<Index> => {
    return apiRequest<Index>('/indexes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  renameIndex: async (indexId: string, newName: string): Promise<Index> => {
    return apiRequest<Index>(`/indexes/${indexId}`, {
      method: 'PUT',
      body: JSON.stringify({ new_name: newName }),
    });
  },

  deleteIndex: async (indexId: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>(`/indexes/${indexId}`, {
      method: 'DELETE',
    });
  },

  // Video operations
  listVideos: async (indexId: string): Promise<Video[]> => {
    return apiRequest<Video[]>(`/indexes/${indexId}/videos`);
  },

  deleteVideo: async (indexId: string, videoId: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>(`/indexes/${indexId}/videos/${videoId}`, {
      method: 'DELETE',
    });
  },

  uploadVideo: async (data: UploadVideoData): Promise<{ task_id: string; video_id: string }> => {
    const formData = new FormData();
    formData.append('index_id', data.index_id);
    
    if (data.file) {
      formData.append('file', data.file);
    }
    if (data.url) {
      formData.append('url', data.url);
    }

    const response = await fetch(`${API_BASE_URL}/upload-video`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new ApiError(`Upload failed: ${response.statusText}`, response.status);
    }

    return response.json();
  },

  // Task status checking
  checkTaskStatus: async (taskId: string): Promise<{ status: string; video_id?: string }> => {
    return apiRequest<{ status: string; video_id?: string }>(`/tasks/${taskId}`);
  },
}; 