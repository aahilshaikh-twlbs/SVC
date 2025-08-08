from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Query, Form
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import sqlite3
from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask
import hashlib
import numpy as np
import tempfile
import os
from datetime import datetime, timezone
import sys
import uuid
from pathlib import Path
import subprocess

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SAGE Backend", version="2.0.0")

# Middleware to log all incoming requests with timestamps
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    client_host = request.client.host if request.client else "unknown"
    
    # Log suspicious requests
    path = str(request.url.path)
    if request.url.query:
        path += f"?{request.url.query}"
    
    # Check for suspicious patterns
    suspicious_patterns = [
        "http%3A//", "https%3A//",  # URL encoded URLs
        "CONNECT",  # CONNECT method abuse
        ".php", ".asp", ".cgi",  # Common exploit targets
        "../", "..\\",  # Path traversal attempts
        "admin", "wp-", "phpmyadmin",  # Common admin panels
        ".env", ".git", ".config",  # Sensitive files
    ]
    
    is_suspicious = any(pattern in path.lower() or pattern in request.method for pattern in suspicious_patterns)
    
    if is_suspicious:
        logger.warning(f"Suspicious request from {client_host}: {request.method} {path}")
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Calculate response time
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log based on status code
        if response.status_code == 404:
            logger.warning(f"{client_host} - {request.method} {path} - 404 Not Found ({duration:.3f}s)")
        elif response.status_code >= 400:
            logger.warning(f"{client_host} - {request.method} {path} - {response.status_code} ({duration:.3f}s)")
        elif response.status_code >= 200 and response.status_code < 300:
            logger.info(f"{client_host} - {request.method} {path} - {response.status_code} ({duration:.3f}s)")
        
        return response
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"{client_host} - {request.method} {path} - Error: {str(e)} ({duration:.3f}s)")
        raise

DB_PATH = "sage.db"

# Initialize database
conn = sqlite3.connect(DB_PATH)
conn.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_hash TEXT UNIQUE NOT NULL,
        api_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()

current_api_key = None
tl_client = None
embedding_storage: Dict[str, Any] = {}
video_storage: Dict[str, bytes] = {}
video_path_storage: Dict[str, str] = {}

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
VIDEOS_DIR = BASE_DIR / "videos"

# Clean up on startup
import shutil
for dir_path in [UPLOADS_DIR, VIDEOS_DIR]:
    if dir_path.exists():
        shutil.rmtree(dir_path)
        logger.info(f"Cleaned up {dir_path}")
    dir_path.mkdir(exist_ok=True)

MAX_EMBED_DURATION_SEC = 7200  # 2 hours
MAX_EMBED_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB

# Track server start time
server_start_time = datetime.now(timezone.utc)

@app.get("/")
async def root():
    """Root endpoint to handle scanner traffic"""
    return {"message": "SAGE API", "docs": "/docs"}

@app.get("/robots.txt")
async def robots():
    """Robots.txt to control crawlers"""
    return Response(content="User-agent: *\nDisallow: /", media_type="text/plain")

@app.get("/favicon.ico")
async def favicon():
    """Return 204 No Content for favicon requests"""
    return Response(status_code=204)

@app.get("/health")
async def health_check():
    """Health check endpoint that returns server status and basic info"""
    try:
        # Check database connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        db_status = "healthy"
    except Exception as e:
        db_status = "error"
    
    # Calculate uptime
    uptime = datetime.now(timezone.utc) - server_start_time
    uptime_seconds = int(uptime.total_seconds())
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "uptime_seconds": uptime_seconds,
        "uptime": str(uptime),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_status": db_status,
        "python_version": sys.version.split()[0]
    }

async def get_api_key(request: Request) -> str:
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    return api_key

def get_twelve_labs_client(api_key: str = Depends(get_api_key)):
    global tl_client, current_api_key
    
    if tl_client and current_api_key == api_key:
        return tl_client
    
    try:
        tl_client = TwelveLabs(api_key=api_key)
        current_api_key = api_key
        
        # Save API key hash
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT OR REPLACE INTO api_keys (key_hash, api_key) VALUES (?, ?)', 
                     (key_hash, None))
        conn.commit()
        conn.close()
        
        logger.info("Successfully initialized TwelveLabs client")
        return tl_client
    except Exception as e:
        logger.error(f"Error initializing TwelveLabs client: {e}")
        raise HTTPException(status_code=401, detail="Invalid API key")

class ApiKeyValidation(BaseModel):
    key: str

class ApiKeyResponse(BaseModel):
    key: str
    isValid: bool

@app.post("/validate-key")
async def validate_api_key(request: ApiKeyValidation):
    logger.info("Validating API key...")
    try:
        TwelveLabs(api_key=request.key)
        
        # Save API key hash
        key_hash = hashlib.sha256(request.key.encode()).hexdigest()
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT OR REPLACE INTO api_keys (key_hash, api_key) VALUES (?, ?)', 
                     (key_hash, None))
        conn.commit()
        conn.close()
        
        logger.info("API key validation successful")
        return ApiKeyResponse(key=request.key, isValid=True)
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return ApiKeyResponse(key=request.key, isValid=False)

@app.post("/upload-and-generate-embeddings")
async def upload_and_generate_embeddings(
    file: UploadFile = File(...),
    tl: TwelveLabs = Depends(get_twelve_labs_client)
):
    try:
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Creating embedding task for file: {file.filename}")
        task = tl.embed.task.create(
            model_name="Marengo-retrieval-2.7",
            video_file=tmp_file_path,
            video_clip_length=2,
            video_embedding_scopes=["clip", "video"]
        )
        
        logger.info(f"Waiting for embedding task {task.id} to complete")
        def on_task_update(task: EmbeddingsTask):
            logger.info(f"Task {task.id} status: {task.status}")
        
        task.wait_for_done(sleep_interval=5, callback=on_task_update)
        
        completed_task = tl.embed.task.retrieve(task.id)
        os.unlink(tmp_file_path)
        
        embedding_id = f"embed_{task.id}"
        video_id = f"video_{task.id}"
        
        duration = 0
        if completed_task.video_embedding and completed_task.video_embedding.segments:
            duration = completed_task.video_embedding.segments[-1].end_offset_sec
        
        embedding_storage[embedding_id] = {
            "filename": file.filename,
            "embeddings": completed_task.video_embedding,
            "duration": duration
        }
        
        video_storage[video_id] = content
        
        return {
            "embeddings": completed_task.video_embedding,
            "filename": file.filename,
            "duration": duration,
            "embedding_id": embedding_id,
            "video_id": video_id
        }
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")


def run_ffprobe_duration_seconds(file_path: str) -> Optional[float]:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def split_video_if_needed(src_path: str, dest_dir: Path) -> List[str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    duration = run_ffprobe_duration_seconds(src_path) or 0.0
    size_bytes = os.path.getsize(src_path)
    needs_split = (duration and duration > MAX_EMBED_DURATION_SEC) or size_bytes > MAX_EMBED_SIZE_BYTES
    if not needs_split:
        return [src_path]

    # Split by time into chunks no longer than 3600 seconds to stay safely under 2h and reduce size
    segment_time = 3600
    pattern = str(dest_dir / "part_%03d.mp4")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", src_path, "-c", "copy", "-f", "segment",
                "-reset_timestamps", "1", "-segment_time", str(segment_time), pattern
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        logger.error(f"ffmpeg split failed: {e}")
        # If split fails, fallback to single file
        return [src_path]

    # Collect generated parts
    parts = sorted([str(p) for p in dest_dir.glob("part_*.mp4")])
    return parts if parts else [src_path]


def concat_chunks_to_file(chunks_dir: Path, output_path: Path, total_chunks: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as out_f:
        for i in range(total_chunks):
            chunk_file = chunks_dir / f"chunk_{i}.bin"
            if not chunk_file.exists():
                raise HTTPException(status_code=400, detail=f"Missing chunk {i}")
            with open(chunk_file, "rb") as cf:
                out_f.write(cf.read())


@app.post("/upload/start")
async def start_chunked_upload(videoName: Optional[str] = Form(None)):
    session_id = uuid.uuid4().hex
    session_dir = UPLOADS_DIR / session_id
    chunks_dir = session_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    return {"session_id": session_id, "video_id": session_id, "video_name": videoName or "video.mp4"}


@app.post("/upload/chunk")
async def upload_chunk(
    session_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    chunk: UploadFile = File(...),
    tl: TwelveLabs = Depends(get_twelve_labs_client),
):
    try:
        session_dir = UPLOADS_DIR / session_id / "chunks"
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="Invalid session_id")
        dest_path = session_dir / f"chunk_{chunk_index}.bin"
        contents = await chunk.read()
        with open(dest_path, "wb") as f:
            f.write(contents)
        return {"message": f"Chunk {chunk_index + 1}/{total_chunks} stored"}
    except Exception as e:
        logger.error(f"Error storing chunk: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store chunk: {str(e)}")


@app.post("/upload/finalize")
async def finalize_upload(
    session_id: str = Form(...),
    original_filename: str = Form(...),
    total_chunks: int = Form(...),
    tl: TwelveLabs = Depends(get_twelve_labs_client),
):
    session_root = UPLOADS_DIR / session_id
    chunks_dir = session_root / "chunks"
    if not chunks_dir.exists():
        raise HTTPException(status_code=404, detail="Invalid session_id")

    # Concatenate chunks into a single mp4 file
    combined_path = str(session_root / "combined.mp4")
    try:
        concat_chunks_to_file(chunks_dir, Path(combined_path), int(total_chunks))
        combined_size_mb = os.path.getsize(combined_path) / (1024 * 1024)
        logger.info(f"Combined video size: {combined_size_mb:.1f}MB")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Concatenation failed: {e}")
        raise HTTPException(status_code=500, detail="Concatenation failed")

    # Split if needed
    parts_dir = session_root / "parts"
    parts = split_video_if_needed(combined_path, parts_dir)

    # Run embedding tasks on one or multiple parts
    all_segments: List[Dict[str, Any]] = []
    total_duration: float = 0.0
    part_offsets: List[float] = []
    for idx, part_path in enumerate(parts):
        part_start_offset = sum(run_ffprobe_duration_seconds(p) or 0.0 for p in parts[:idx])
        part_offsets.append(part_start_offset)
        logger.info(f"Creating embedding task for part {idx+1}/{len(parts)}: {part_path}")
        part_size_mb = os.path.getsize(part_path) / (1024 * 1024)
        logger.info(f"Part size: {part_size_mb:.1f}MB")
        
        try:
            task = tl.embed.task.create(
                model_name="Marengo-retrieval-2.7",
                video_file=part_path,
                video_clip_length=2,
                video_embedding_scopes=["clip", "video"],
            )

            def on_task_update(t: EmbeddingsTask):  # type: ignore
                logger.info(f"Task {t.id} status: {t.status}")

            task.wait_for_done(sleep_interval=5, callback=on_task_update)
            completed_task = tl.embed.task.retrieve(task.id)
        except Exception as e:
            logger.error(f"TwelveLabs API error: {str(e)}")
            # If TwelveLabs is down, clean up and return error
            raise HTTPException(status_code=503, detail=f"TwelveLabs API unavailable: {str(e)}")

        part_duration = 0.0
        if completed_task.video_embedding and completed_task.video_embedding.segments:
            for seg in completed_task.video_embedding.segments:
                all_segments.append({
                    "start_offset_sec": (seg.start_offset_sec + part_start_offset),
                    "end_offset_sec": (seg.end_offset_sec + part_start_offset),
                    "embeddings_float": seg.embeddings_float,
                })
            part_duration = completed_task.video_embedding.segments[-1].end_offset_sec + part_start_offset
        total_duration = max(total_duration, part_duration)

    embedding_id = f"embed_{session_id}"
    video_id = f"video_{session_id}"

    embedding_storage[embedding_id] = {
        "filename": original_filename,
        "segments": all_segments,
        "duration": total_duration,
    }

    # Persist combined file for serving
    final_video_path = str(VIDEOS_DIR / f"{session_id}.mp4")
    try:
        os.replace(combined_path, final_video_path)
    except Exception:
        # If replace fails, copy
        with open(combined_path, "rb") as src, open(final_video_path, "wb") as dst:
            dst.write(src.read())
    video_path_storage[video_id] = final_video_path

    # Cleanup chunks directory to save space
    try:
        for p in chunks_dir.glob("*"):
            p.unlink(missing_ok=True)
        chunks_dir.rmdir()
    except Exception:
        pass

    return {
        "embeddings": {"segments": all_segments},
        "filename": original_filename,
        "duration": total_duration,
        "embedding_id": embedding_id,
        "video_id": video_id,
    }

@app.post("/compare-local-videos")
async def compare_local_videos(
    embedding_id1: str = Query(...),
    embedding_id2: str = Query(...),
    threshold: float = Query(0.1),
    distance_metric: str = Query("cosine")
):
    try:
        if embedding_id1 not in embedding_storage or embedding_id2 not in embedding_storage:
            raise HTTPException(status_code=404, detail="Embeddings not found")
        
        embed_data1 = embedding_storage[embedding_id1]
        embed_data2 = embedding_storage[embedding_id2]
        
        segments1 = []
        segments2 = []
        
        if embed_data1.get("embeddings"):
            emb1 = embed_data1["embeddings"]
            if hasattr(emb1, "segments"):
                segments1 = [{
                    "start_offset_sec": seg.start_offset_sec,
                    "end_offset_sec": seg.end_offset_sec,
                    "embedding": seg.embeddings_float
                } for seg in emb1.segments]
            elif isinstance(emb1, dict) and isinstance(emb1.get("segments"), list):
                segments1 = [{
                    "start_offset_sec": seg["start_offset_sec"],
                    "end_offset_sec": seg["end_offset_sec"],
                    "embedding": seg.get("embedding") or seg.get("embeddings_float")
                } for seg in emb1["segments"]]
        
        if embed_data2.get("embeddings"):
            emb2 = embed_data2["embeddings"]
            if hasattr(emb2, "segments"):
                segments2 = [{
                    "start_offset_sec": seg.start_offset_sec,
                    "end_offset_sec": seg.end_offset_sec,
                    "embedding": seg.embeddings_float
                } for seg in emb2.segments]
            elif isinstance(emb2, dict) and isinstance(emb2.get("segments"), list):
                segments2 = [{
                    "start_offset_sec": seg["start_offset_sec"],
                    "end_offset_sec": seg["end_offset_sec"],
                    "embedding": seg.get("embedding") or seg.get("embeddings_float")
                } for seg in emb2["segments"]]
        
        logger.info(f"Comparing {len(segments1)} segments from video1 with {len(segments2)} segments from video2, threshold: {threshold}")
        
        # Compare segments
        def keyfunc(s):
            return round(s["start_offset_sec"], 2)
        
        dict_v1 = {keyfunc(seg): seg for seg in segments1}
        dict_v2 = {keyfunc(seg): seg for seg in segments2}
        
        all_keys = set(dict_v1.keys()).union(set(dict_v2.keys()))
        differing_segments = []
        all_distances = []
        
        for k in sorted(all_keys):
            seg1 = dict_v1.get(k)
            seg2 = dict_v2.get(k)
            
            if not seg1 or not seg2:
                valid_seg = seg1 if seg1 else seg2
                differing_segments.append({
                    "start_sec": valid_seg["start_offset_sec"],
                    "end_sec": valid_seg["end_offset_sec"],
                    "distance": float('inf')
                })
                continue
            
            v1 = np.array(seg1["embedding"], dtype=np.float32)
            v2 = np.array(seg2["embedding"], dtype=np.float32)
            
            if distance_metric == "cosine":
                # Cosine distance
                dot = np.dot(v1, v2)
                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)
                dist = 1.0 - (dot / (norm1 * norm2)) if norm1 > 0 and norm2 > 0 else 1.0
            else:
                # Euclidean distance
                dist = float(np.linalg.norm(v1 - v2))
            
            all_distances.append(float(dist))
            
            if float(dist) > threshold:
                differing_segments.append({
                    "start_sec": seg1["start_offset_sec"],
                    "end_sec": seg1["end_offset_sec"],
                    "distance": float(dist)
                })
        
        if all_distances:
            logger.info(f"Distance stats - Min: {min(all_distances):.4f}, Max: {max(all_distances):.4f}, Mean: {np.mean(all_distances):.4f}")
        
        logger.info(f"Found {len(differing_segments)} differences with threshold {threshold}")
        
        return {
            "filename1": embed_data1["filename"],
            "filename2": embed_data2["filename"],
            "differences": differing_segments,
            "total_segments": max(len(segments1), len(segments2)),
            "differing_segments": len(differing_segments),
            "threshold_used": threshold
        }
        
    except Exception as e:
        logger.error(f"Error comparing videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare videos: {str(e)}")

@app.get("/serve-video/{video_id}")
async def serve_video(video_id: str):
    # Prefer disk path serving for large files
    from fastapi.responses import FileResponse
    path = video_path_storage.get(video_id)
    if path and os.path.exists(path):
        return FileResponse(path, media_type="video/mp4")
    if video_id in video_storage:
        return Response(content=video_storage[video_id], media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video not found")

# Custom 404 handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    client_host = request.client.host if request.client else "unknown"
    path = str(request.url.path)
    if request.url.query:
        path += f"?{request.url.query}"
    
    logger.warning(f"404 Not Found: {client_host} attempted to access {request.method} {path}")
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource {path} was not found",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)