from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any
import logging
import sqlite3
from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask
import hashlib
import numpy as np
import tempfile
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SAGE Backend", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "sage.db"

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT UNIQUE NOT NULL,
            api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Global variable to store the API key
current_api_key = None
tl_client = None

# In-memory storage for temporary embeddings and videos
embedding_storage: Dict[str, Any] = {}
video_storage: Dict[str, bytes] = {}

async def get_api_key(request: Request) -> str:
    """Extract API key from X-API-Key header"""
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    return api_key

def get_twelve_labs_client(api_key: str = Depends(get_api_key)):
    """Get or initialize TwelveLabs client with API key"""
    global tl_client, current_api_key
    
    # If we have a client and it's the same key, return it
    if tl_client and current_api_key == api_key:
        return tl_client
    
    # Initialize new client
    try:
        tl_client = TwelveLabs(api_key=api_key)
        current_api_key = api_key
        save_api_key_hash(api_key)  # Save the API key hash
        logger.info("Successfully initialized TwelveLabs client")
        return tl_client
    except Exception as e:
        logger.error(f"Error initializing TwelveLabs client: {e}")
        raise HTTPException(status_code=401, detail="Invalid API key")

# Pydantic models
class ApiKeyValidation(BaseModel):
    key: str

class ApiKeyResponse(BaseModel):
    key: str
    isValid: bool

def hash_api_key(key: str) -> str:
    """Simple hash function for API key storage"""
    return hashlib.sha256(key.encode()).hexdigest()

def save_api_key_hash(key: str):
    """Save API key hash to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT OR REPLACE INTO api_keys (key_hash, api_key) VALUES (?, ?)', 
                      (hash_api_key(key), None))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving API key hash: {e}")
    finally:
        conn.close()

def has_stored_api_key() -> bool:
    """Check if there's a stored API key hash"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) FROM api_keys')
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except Exception as e:
        logger.error(f"Error checking stored API key: {e}")
        return False
    finally:
        conn.close()

def initialize_twelve_labs_client(api_key: str):
    """Initialize the TwelveLabs client with the provided API key"""
    global tl_client, current_api_key
    try:
        tl_client = TwelveLabs(api_key=api_key)
        current_api_key = api_key
        save_api_key_hash(api_key)  # Save the API key hash
        logger.info("Successfully initialized TwelveLabs client")
        return True
    except Exception as e:
        logger.error(f"Error initializing TwelveLabs client: {e}")
        return False

@app.get("/")
async def root():
    return {"message": "SAGE Backend API v2.0"}

@app.post("/validate-key")
async def validate_api_key(request: ApiKeyValidation):
    """Validate API key by trying to initialize TwelveLabs client"""
    logger.info("Validating API key...")
    if initialize_twelve_labs_client(request.key):
        logger.info("API key validation successful")
        return ApiKeyResponse(key=request.key, isValid=True)
    logger.error("API key validation failed")
    return ApiKeyResponse(key=request.key, isValid=False)

@app.get("/stored-api-key")
async def get_stored_key():
    """Check if there's a stored API key hash"""
    has_key = has_stored_api_key()
    return {"has_stored_key": has_key}

@app.post("/upload-and-generate-embeddings")
async def upload_and_generate_embeddings(
    file: UploadFile = File(...),
    tl: TwelveLabs = Depends(get_twelve_labs_client)
):
    """Upload a video file and generate embeddings using TwelveLabs"""
    try:
        # Read file content
        content = await file.read()
        
        # Save uploaded file temporarily for TwelveLabs
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Create embedding task
        logger.info(f"Creating embedding task for file: {file.filename}")
        task = tl.embed.task.create(
            model_name="Marengo-retrieval-2.7",
            video_file=tmp_file_path,
            video_clip_length=2,
            video_embedding_scopes=["clip", "video"]
        )
        
        # Wait for task completion
        logger.info(f"Waiting for embedding task {task.id} to complete")
        def on_task_update(task: EmbeddingsTask):
            logger.info(f"Task {task.id} status: {task.status}")
        
        task.wait_for_done(sleep_interval=5, callback=on_task_update)
        
        # Retrieve embeddings
        logger.info(f"Retrieving embeddings for task {task.id}")
        completed_task = tl.embed.task.retrieve(task.id)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        # Store embeddings and video in memory
        embedding_id = f"embed_{task.id}"
        video_id = f"video_{task.id}"
        
        # Calculate duration from segments
        duration = 0
        segment_count = 0
        if completed_task.video_embedding and completed_task.video_embedding.segments:
            # Get the end time of the last segment
            last_segment = completed_task.video_embedding.segments[-1]
            duration = last_segment.end_offset_sec
            segment_count = len(completed_task.video_embedding.segments)
        
        logger.info(f"Generated {segment_count} segments for {file.filename}, duration: {duration}s")
        
        embedding_storage[embedding_id] = {
            "filename": file.filename,
            "embeddings": completed_task.video_embedding,
            "duration": duration,
            "segment_count": segment_count
        }
        
        # Store video content
        video_storage[video_id] = content
        
        return {
            "embeddings": completed_task.video_embedding,
            "filename": file.filename,
            "duration": duration,
            "embedding_id": embedding_id,
            "video_id": video_id,
            "segment_count": segment_count
        }
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

@app.post("/compare-local-videos")
async def compare_local_videos(
    embedding_id1: str = Query(...),
    embedding_id2: str = Query(...),
    threshold: float = Query(0.1),  # Lower default threshold to catch more differences
    distance_metric: str = Query("cosine")
):
    """Compare two videos using their embeddings"""
    try:
        # Get embeddings from storage
        if embedding_id1 not in embedding_storage or embedding_id2 not in embedding_storage:
            raise HTTPException(status_code=404, detail="Embeddings not found")
        
        embed_data1 = embedding_storage[embedding_id1]
        embed_data2 = embedding_storage[embedding_id2]
        
        # Extract segment embeddings
        segments1 = []
        segments2 = []
        
        if embed_data1["embeddings"] and embed_data1["embeddings"].segments:
            for seg in embed_data1["embeddings"].segments:
                segments1.append({
                    "start_offset_sec": seg.start_offset_sec,
                    "end_offset_sec": seg.end_offset_sec,
                    "embedding": seg.embeddings_float
                })
        
        if embed_data2["embeddings"] and embed_data2["embeddings"].segments:
            for seg in embed_data2["embeddings"].segments:
                segments2.append({
                    "start_offset_sec": seg.start_offset_sec,
                    "end_offset_sec": seg.end_offset_sec,
                    "embedding": seg.embeddings_float
                })
        
        logger.info(f"Comparing {len(segments1)} segments from video1 with {len(segments2)} segments from video2, threshold: {threshold}")
        
        # Compare segments
        differences = compare_segments_by_time(segments1, segments2, threshold, distance_metric)
        
        logger.info(f"Found {len(differences)} differences with threshold {threshold}")
        if differences:
            logger.info(f"Sample differences: {differences[:3]}")
        
        return {
            "filename1": embed_data1["filename"],
            "filename2": embed_data2["filename"],
            "differences": differences,
            "total_segments": max(len(segments1), len(segments2)),
            "differing_segments": len(differences),
            "threshold_used": threshold
        }
        
    except Exception as e:
        logger.error(f"Error comparing videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare videos: {str(e)}")

def compare_segments_by_time(segments1, segments2, threshold=0.1, distance_metric="cosine"):
    """Compare two lists of segment embeddings"""
    def keyfunc(s):
        return round(s["start_offset_sec"], 2)
    
    dict_v1 = {keyfunc(seg): seg for seg in segments1}
    dict_v2 = {keyfunc(seg): seg for seg in segments2}
    
    all_keys = set(dict_v1.keys()).union(set(dict_v2.keys()))
    differing_segments = []
    all_distances = []  # Track all distances for debugging
    
    for k in sorted(all_keys):
        seg1 = dict_v1.get(k)
        seg2 = dict_v2.get(k)
        
        if not seg1 or not seg2:
            # One segment missing
            valid_seg = seg1 if seg1 is not None else seg2
            differing_segments.append({
                "start_sec": valid_seg["start_offset_sec"],
                "end_sec": valid_seg["end_offset_sec"],
                "distance": float('inf')
            })
            continue
        
        # Calculate distance
        v1 = np.array(seg1["embedding"], dtype=np.float32)
        v2 = np.array(seg2["embedding"], dtype=np.float32)
        
        if distance_metric == "cosine":
            dist = cosine_distance(v1, v2)
        else:
            dist = euclidean_distance(v1, v2)
        
        all_distances.append(float(dist))
        
        if float(dist) > threshold:
            differing_segments.append({
                "start_sec": seg1["start_offset_sec"],
                "end_sec": seg1["end_offset_sec"],
                "distance": float(dist)
            })
    
    # Log distance statistics for debugging
    if all_distances:
        logger.info(f"Distance stats - Min: {min(all_distances):.4f}, Max: {max(all_distances):.4f}, Mean: {np.mean(all_distances):.4f}")
    
    return differing_segments

def cosine_distance(v1, v2):
    """Calculate cosine distance between two vectors"""
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 1.0
    similarity = dot / (norm1 * norm2)
    return 1.0 - similarity

def euclidean_distance(v1, v2):
    """Calculate euclidean distance between two vectors"""
    return float(np.linalg.norm(v1 - v2))

@app.get("/serve-video/{video_id}")
async def serve_video(video_id: str):
    """Serve video from memory storage"""
    if video_id not in video_storage:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_content = video_storage[video_id]
    return Response(content=video_content, media_type="video/mp4")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 