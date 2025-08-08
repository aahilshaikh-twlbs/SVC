import { ApiKeyConfig } from '@/types';
import { shouldChunkFile, chunkFile, buildChunkFormData } from './fileChunker';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

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
    ...(options.headers as Record<string, string>),
  };
  
  // Use provided key or get from localStorage
  const keyToUse = apiKey || localStorage.getItem('sage_api_key');
  if (keyToUse) {
    headers['X-API-Key'] = keyToUse;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers,
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(
      errorData?.detail || `Request failed: ${response.statusText}`,
      response.status
    );
  }

  return response.json();
}

export const api = {
  // API Key validation
  validateApiKey: async (key: string): Promise<ApiKeyConfig> => {
    return apiRequest<ApiKeyConfig>('/validate-key', {
      method: 'POST',
      body: JSON.stringify({ key }),
    }, key);
  },

  // Upload video and generate embeddings (supports chunked pipeline)
  uploadAndGenerateEmbeddings: async (formData: FormData, apiKey?: string): Promise<{
    embeddings: unknown;
    filename: string;
    duration: number;
    embedding_id: string;
    video_id: string;
  }> => {
    const file = formData.get('file') as File;
    if (!file) throw new Error('file missing');

    const headers: Record<string, string> = {};
    const keyToUse = apiKey || localStorage.getItem('sage_api_key');
    if (keyToUse) headers['X-API-Key'] = keyToUse;

    if (shouldChunkFile(file)) {
      const startRes = await fetch(`${API_BASE_URL}/upload/start`, { method: 'POST', headers });
      if (!startRes.ok) throw new ApiError('Failed to start upload session', startRes.status);
      const { session_id } = await startRes.json();

      const cf = chunkFile(file);
      for (const c of cf.chunks) {
        const chunkFd = buildChunkFormData(session_id, c, cf.totalChunks);
        const r = await fetch(`${API_BASE_URL}/upload/chunk`, { method: 'POST', headers, body: chunkFd });
        if (!r.ok) throw new ApiError('Chunk upload failed', r.status);
      }

      const finalizeFd = new FormData();
      finalizeFd.append('session_id', session_id);
      finalizeFd.append('original_filename', file.name);
      finalizeFd.append('total_chunks', String(cf.totalChunks));
      const fin = await fetch(`${API_BASE_URL}/upload/finalize`, { method: 'POST', headers, body: finalizeFd });
      if (!fin.ok) throw new ApiError('Finalize failed', fin.status);
      return fin.json();
    }

    const response = await fetch(`${API_BASE_URL}/upload-and-generate-embeddings`, {
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

  // Compare local videos
  compareLocalVideos: async (embeddingId1: string, embeddingId2: string, threshold: number = 0.1, apiKey?: string): Promise<{
    filename1: string;
    filename2: string;
    differences: Array<{
      start_sec: number;
      end_sec: number;
      distance: number;
    }>;
    total_segments: number;
    differing_segments: number;
    threshold_used: number;
  }> => {
    const params = new URLSearchParams({
      embedding_id1: embeddingId1,
      embedding_id2: embeddingId2,
      threshold: threshold.toString()
    });
    
    return apiRequest(`/compare-local-videos?${params}`, {
      method: 'POST',
    }, apiKey);
  },
};