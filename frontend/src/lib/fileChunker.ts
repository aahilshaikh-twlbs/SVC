export interface FileChunk {
  chunk: Blob;
  index: number;
  totalChunks: number;
  filename: string;
}

export interface ChunkedFile {
  chunks: FileChunk[];
  originalFile: File;
  totalChunks: number;
}

// Use conservative values to stay well under platform limits
const CHUNKING_THRESHOLD_BYTES = 4 * 1024 * 1024; // 4MB
const CHUNK_SIZE_BYTES = 4 * 1024 * 1024; // 4MB

export function shouldChunkFile(file: File): boolean {
  return file.size >= CHUNKING_THRESHOLD_BYTES;
}

export function chunkFile(file: File): ChunkedFile {
  const chunks: FileChunk[] = [];
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE_BYTES);
  for (let i = 0; i < totalChunks; i++) {
    const start = i * CHUNK_SIZE_BYTES;
    const end = Math.min(start + CHUNK_SIZE_BYTES, file.size);
    const chunk = file.slice(start, end);
    chunks.push({ chunk, index: i, totalChunks, filename: file.name });
  }
  return { chunks, originalFile: file, totalChunks };
}

export function buildChunkFormData(
  sessionId: string,
  chunk: FileChunk,
  totalChunks: number
): FormData {
  const fd = new FormData();
  fd.append('session_id', sessionId);
  fd.append('chunk_index', String(chunk.index));
  fd.append('total_chunks', String(totalChunks));
  fd.append('chunk', chunk.chunk, `${chunk.filename}.part${chunk.index}`);
  return fd;
}


