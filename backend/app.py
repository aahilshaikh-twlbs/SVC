from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
import sqlite3
from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask
import hashlib
import numpy as np
import urllib.parse
import httpx
import tempfile
import os
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SAGE Backend", version="1.0.0")

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
class IndexModel(BaseModel):
    name: str
    options: List[str]

class Index(BaseModel):
    id: str
    name: str
    models: List[IndexModel]
    video_count: int
    total_duration: int
    created_at: str
    updated_at: Optional[str] = None

class SystemMetadata(BaseModel):
    filename: str
    duration: int
    fps: int
    width: int
    height: int
    size: int

class HLSData(BaseModel):
    video_url: str
    thumbnail_urls: Optional[List[str]] = None
    status: str
    updated_at: str

class SourceData(BaseModel):
    type: str
    name: str
    url: str

class Video(BaseModel):
    id: str
    created_at: str
    updated_at: str
    system_metadata: SystemMetadata
    user_metadata: Optional[dict] = None
    hls: Optional[HLSData] = None
    source: Optional[SourceData] = None

class ApiKeyValidation(BaseModel):
    key: str

class ApiKeyResponse(BaseModel):
    key: str
    isValid: bool

class CreateIndexRequest(BaseModel):
    name: str

class RenameIndexRequest(BaseModel):
    new_name: str

class ComparisonRequest(BaseModel):
    video1_id: str
    video2_id: str
    index_id: str
    threshold: float = 0.03
    distance_metric: str = "cosine"

class ComparisonResult(BaseModel):
    start_sec: float
    end_sec: float
    distance: float

class ComparisonResponse(BaseModel):
    video1_id: str
    video2_id: str
    differences: List[ComparisonResult]
    total_segments: int
    differing_segments: int

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

def safe_date_conversion(date_obj):
    """Safely convert date objects to ISO string"""
    if date_obj is None:
        return None
    try:
        if hasattr(date_obj, 'isoformat'):
            return date_obj.isoformat() + "Z"
        else:
            return str(date_obj)
    except Exception as e:
        logger.warning(f"Error converting date {date_obj}: {e}")
        return str(date_obj)

def convert_twelve_labs_index_to_model(tl_index):
    """Convert TwelveLabs index to our Pydantic model"""
    try:
        models = []
        for model in tl_index.models:
            models.append(IndexModel(
                name=str(model.name),
                options=[str(opt) for opt in model.options]
            ))
        
        return Index(
            id=str(tl_index.id),
            name=str(tl_index.name),
            models=models,
            video_count=int(tl_index.video_count),
            total_duration=int(tl_index.total_duration),
            created_at=safe_date_conversion(tl_index.created_at),
            updated_at=safe_date_conversion(tl_index.updated_at)
        )
    except Exception as e:
        logger.error(f"Error converting index {tl_index.id}: {e}")
        raise

def convert_twelve_labs_video_to_model(tl_video):
    """Convert TwelveLabs video to our Pydantic model"""
    try:
        system_metadata = SystemMetadata(
            filename=str(tl_video.system_metadata.filename),
            duration=int(tl_video.system_metadata.duration),
            fps=int(tl_video.system_metadata.fps),
            width=int(tl_video.system_metadata.width),
            height=int(tl_video.system_metadata.height),
            size=int(tl_video.system_metadata.size)
        )
        
        hls_data = None
        if tl_video.hls:
            hls_data = HLSData(
                video_url=str(tl_video.hls.video_url),
                thumbnail_urls=[str(url) for url in (tl_video.hls.thumbnail_urls or [])],
                status=str(tl_video.hls.status),
                updated_at=safe_date_conversion(tl_video.hls.updated_at)
            )
        
        source_data = None
        if tl_video.source:
            source_data = SourceData(
                type=str(tl_video.source.type),
                name=str(tl_video.source.name),
                url=str(tl_video.source.url)
            )
        
        return Video(
            id=str(tl_video.id),
            created_at=safe_date_conversion(tl_video.created_at),
            updated_at=safe_date_conversion(tl_video.updated_at) or safe_date_conversion(tl_video.created_at),
            system_metadata=system_metadata,
            user_metadata=tl_video.user_metadata,
            hls=hls_data,
            source=source_data
        )
    except Exception as e:
        logger.error(f"Error converting video {tl_video.id}: {e}")
        raise

def cosine_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculate cosine distance between two vectors"""
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 1.0
    similarity = dot / (norm1 * norm2)
    return 1.0 - similarity

def euclidean_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculate euclidean distance between two vectors"""
    return float(np.linalg.norm(v1 - v2))

def fetch_video_embeddings(tl_client: TwelveLabs, video_id: str, index_id: str) -> List[dict]:
    """
    Fetch all segment embeddings for a video from TwelveLabs using video ID and index ID.
    Based on the SAGE.py retrieve_embeds function.
    
    Returns a list of dicts like:
    [
      {
        'start_offset_sec': 0.0,
        'end_offset_sec': 2.0,
        'embedding': [float, float, ...]
      },
      ...
    ]
    sorted by start_offset_sec ascending.
    """
    try:
        logger.info(f"Retrieving embeddings for video {video_id} from index {index_id}")
        
        # Try different embedding options to find what's available
        embedding_options_to_try = [
            ["visual-text"],
            ["audio"],
            ["visual-text", "audio"],
            []  # No embedding option - just get the video
        ]
        
        video = None
        segments = []
        
        for embedding_option in embedding_options_to_try:
            try:
                logger.info(f"Trying embedding option: {embedding_option}")
                video = tl_client.index.video.retrieve(
                    index_id=index_id, 
                    id=video_id, 
                    embedding_option=embedding_option if embedding_option else None
                )
                logger.info(f"Found video: {video.system_metadata.filename}")
                
                # Check if video has embeddings
                logger.info(f"Checking embeddings for video {video_id} with option: {embedding_option}")
                logger.info(f"Video object attributes: {dir(video)}")
                
                if hasattr(video, 'embedding'):
                    logger.info(f"Video has embedding attribute: {hasattr(video, 'embedding')}")
                    if video.embedding:
                        logger.info(f"Embedding object attributes: {dir(video.embedding)}")
                        if hasattr(video.embedding, 'video_embedding'):
                            logger.info(f"Video has video_embedding attribute")
                            if video.embedding.video_embedding and hasattr(video.embedding.video_embedding, 'segments'):
                                segment_count = len(video.embedding.video_embedding.segments) if video.embedding.video_embedding.segments else 0
                                logger.info(f"Found {segment_count} segments for video {video_id} with option: {embedding_option}")
                                
                                if segment_count > 0:
                                    # Get segments from the video embedding
                                    for segment in video.embedding.video_embedding.segments:
                                        seg = {
                                            "start_offset_sec": segment.start_offset_sec,
                                            "end_offset_sec": segment.end_offset_sec,
                                            "embedding": segment.embeddings_float
                                        }
                                        segments.append(seg)
                                    break
                                else:
                                    logger.info(f"No segments found with option: {embedding_option}")
                            else:
                                logger.info(f"No video_embedding.segments attribute found with option: {embedding_option}")
                        else:
                            logger.info(f"No video_embedding attribute found with option: {embedding_option}")
                    else:
                        logger.info(f"Embedding is None with option: {embedding_option}")
                else:
                    logger.info(f"No embedding attribute found with option: {embedding_option}")
                    
            except Exception as e:
                logger.info(f"Failed with embedding option {embedding_option}: {e}")
                continue
        
        if not video:
            raise HTTPException(status_code=404, detail=f"Could not retrieve video {video_id}")
        
        if not segments:
            raise HTTPException(status_code=404, detail=f"No embeddings found for video {video_id}. Please ensure the video has been processed.")
        
        # Sort by start_offset_sec ascending
        segments.sort(key=lambda s: s["start_offset_sec"])
        logger.info(f"Retrieved {len(segments)} segments for video {video_id}")
        return segments
        
    except Exception as e:
        logger.error(f"Error fetching embeddings for video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching embeddings: {str(e)}")

def compare_segments_by_time(
    segments_v1: List[dict],
    segments_v2: List[dict],
    threshold: float = 0.03,
    distance_metric: str = "cosine"
) -> List[dict]:
    """
    Compare two lists of segment embeddings and identify differences.
    
    Returns a list of dicts describing where differences occur:
    [
      {
        "start_sec": 0.0,
        "end_sec": 2.0,
        "distance": 0.45
      },
      ...
    ]
    """
    # Convert the lists into dictionaries keyed by start_offset_sec
    def keyfunc(s):
        return round(s["start_offset_sec"], 2)

    dict_v1 = {keyfunc(seg): seg for seg in segments_v1}
    dict_v2 = {keyfunc(seg): seg for seg in segments_v2}

    # Combine all possible start times
    all_keys = set(dict_v1.keys()).union(set(dict_v2.keys()))
    differing_segments = []

    for k in sorted(all_keys):
        seg1 = dict_v1.get(k)
        seg2 = dict_v2.get(k)

        if not seg1 or not seg2:
            # If one segment is missing, treat it as a difference
            valid_seg = seg1 if seg1 is not None else seg2
            if valid_seg:
                differing_segments.append({
                    "start_sec": valid_seg["start_offset_sec"],
                    "end_sec": valid_seg["end_offset_sec"],
                    "distance": 1.0  # Use maximum distance instead of infinity
                })
            continue

        # Convert to numpy for distance calculation
        v1 = np.array(seg1["embedding"], dtype=np.float32)
        v2 = np.array(seg2["embedding"], dtype=np.float32)

        if distance_metric == "cosine":
            dist = cosine_distance(v1, v2)
        else:
            dist = euclidean_distance(v1, v2)

        # Cast dist to float to avoid serialization issues
        dist_val = float(dist)
        
        # Handle infinity values for JSON serialization
        if dist_val == float('inf'):
            dist_val = 1.0  # Use maximum distance instead of infinity
        elif dist_val == float('-inf'):
            dist_val = 0.0  # Use minimum distance instead of negative infinity
            
        if dist_val > threshold:
            differing_segments.append({
                "start_sec": seg1["start_offset_sec"],
                "end_sec": seg1["end_offset_sec"],
                "distance": dist_val
            })

    return differing_segments

@app.get("/")
async def root():
    return {"message": "SAGE Backend API"}

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

@app.get("/indexes")
async def list_indexes(tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """List all indexes using real TwelveLabs API"""
    try:
        logger.info("Fetching indexes from TwelveLabs...")
        
        # Fetch all indexes with pagination
        all_indexes = []
        page = 1
        page_size = 50  # Max page size
        
        while True:
            try:
                # Fetch indexes page by page
                indexes_page = tl_client.index.list(
                    model_family="marengo",
                    sort_by="created_at",
                    sort_option="desc",
                    page=page,
                    page_size=page_size
                )
                
                # Check if we got a list or a paginated response
                if hasattr(indexes_page, 'data'):
                    # Paginated response
                    page_indexes = indexes_page.data
                    all_indexes.extend(page_indexes)
                    
                    # Check if there are more pages
                    if hasattr(indexes_page, 'page_info') and indexes_page.page_info.total_page > page:
                        page += 1
                        continue
                    else:
                        break
                else:
                    # Direct list response (no pagination)
                    all_indexes = indexes_page
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                # If pagination params not supported, try without them
                if page == 1:
                    all_indexes = tl_client.index.list(
                        model_family="marengo",
                        sort_by="created_at",
                        sort_option="desc"
                    )
                break
        
        logger.info(f"Found {len(all_indexes)} total indexes")
        
        # Convert to our model format
        result = []
        for index in all_indexes:
            try:
                converted_index = convert_twelve_labs_index_to_model(index)
                result.append(converted_index)
            except Exception as e:
                logger.error(f"Error converting index {index.id}: {e}")
                continue
        
        logger.info(f"Successfully converted {len(result)} indexes")
        return result
    except Exception as e:
        logger.error(f"Error fetching indexes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching indexes: {str(e)}")

@app.post("/indexes")
async def create_index(request: CreateIndexRequest, tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """Create new index using real TwelveLabs API"""
    try:
        logger.info(f"Creating new index: {request.name}")
        models = [
            {
                "name": "marengo2.7",
                "options": ["visual", "audio"]
            }
        ]
        
        created_index = tl_client.index.create(
            name=request.name,
            models=models,
            addons=["thumbnail"]
        )
        
        logger.info(f"Successfully created index: {created_index.id}")
        return convert_twelve_labs_index_to_model(created_index)
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating index: {str(e)}")

@app.put("/indexes/{index_id}")
async def rename_index(index_id: str, request: RenameIndexRequest, tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """Rename an index"""
    try:
        logger.info(f"Renaming index {index_id} to: {request.new_name}")
        tl_client.index.update(
            id=index_id,
            name=request.new_name
        )
        
        # Fetch the updated index to return the new data
        updated_index = tl_client.index.retrieve(id=index_id)
        
        logger.info(f"Successfully renamed index: {index_id}")
        return convert_twelve_labs_index_to_model(updated_index)
    except Exception as e:
        logger.error(f"Error renaming index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error renaming index: {str(e)}")

@app.delete("/indexes/{index_id}")
async def delete_index(index_id: str, tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """Delete an index"""
    try:
        logger.info(f"Deleting index: {index_id}")
        tl_client.index.delete(id=index_id)
        
        logger.info(f"Successfully deleted index: {index_id}")
        return {"message": f"Index {index_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting index: {str(e)}")

@app.get("/indexes/{index_id}/videos")
async def list_videos(index_id: str, tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """List videos in an index using real TwelveLabs API"""
    try:
        logger.info(f"Fetching videos for index: {index_id}")
        
        # Fetch all videos with pagination
        all_videos = []
        page = 1
        page_size = 50  # Max page size
        
        while True:
            try:
                # Fetch videos page by page
                videos_page = tl_client.index.video.list(
                    index_id=index_id,
                    sort_by="created_at",
                    sort_option="desc",
                    page=page,
                    page_size=page_size
                )
                
                # Check if we got a list or a paginated response
                if hasattr(videos_page, 'data'):
                    # Paginated response
                    page_videos = videos_page.data
                    all_videos.extend(page_videos)
                    
                    # Check if there are more pages
                    if hasattr(videos_page, 'page_info') and videos_page.page_info.total_page > page:
                        page += 1
                        continue
                    else:
                        break
                else:
                    # Direct list response (no pagination)
                    all_videos = videos_page
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                # If pagination params not supported, try without them
                if page == 1:
                    all_videos = tl_client.index.video.list(
                        index_id=index_id,
                        sort_by="created_at",
                        sort_option="desc"
                    )
                break
        
        logger.info(f"Found {len(all_videos)} total videos")
        
        # Convert to our model format
        result = []
        for video in all_videos:
            try:
                converted_video = convert_twelve_labs_video_to_model(video)
                result.append(converted_video)
            except Exception as e:
                logger.error(f"Error converting video {video.id}: {e}")
                continue
        
        logger.info(f"Successfully converted {len(result)} videos")
        return result
    except Exception as e:
        logger.error(f"Error fetching videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching videos: {str(e)}")

@app.delete("/indexes/{index_id}/videos/{video_id}")
async def delete_video(index_id: str, video_id: str, tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """Delete a video from an index"""
    try:
        logger.info(f"Deleting video {video_id} from index {index_id}")
        tl_client.task.delete(index_id=index_id, id=video_id)
        
        logger.info(f"Successfully deleted video: {video_id}")
        return {"message": f"Video {video_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting video: {str(e)}")

@app.post("/upload-video")
async def upload_video(
    index_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    tl_client: TwelveLabs = Depends(get_twelve_labs_client)
):
    """Upload video using real TwelveLabs API"""
    
    if not file and not url:
        raise HTTPException(status_code=400, detail="Either file or url must be provided")
    
    try:
        logger.info(f"Uploading video to index: {index_id}")
        
        if file:
            # Save uploaded file temporarily
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            logger.info(f"Uploading file: {temp_path}")
            task = tl_client.task.create(
                index_id=index_id,
                file=temp_path
            )
        else:
            # Handle YouTube URL
            if "youtube.com" in url or "youtu.be" in url:
                logger.info(f"Uploading YouTube URL: {url}")
                try:
                    task = tl_client.task.create(
                        index_id=index_id,
                        url=url
                    )
                except Exception as e:
                    logger.error(f"YouTube URL upload failed: {str(e)}")
                    raise HTTPException(
                        status_code=400, 
                        detail="YouTube URL upload failed. TwelveLabs may not support YouTube URLs directly. Please try uploading a video file instead."
                    )
            else:
                raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        logger.info(f"Upload task created: {task.id}")
        return {
            "task_id": task.id,
            "video_id": task.video_id if hasattr(task, 'video_id') else None
        }
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

@app.get("/tasks/{task_id}")
async def check_task_status(task_id: str, tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """Check task status using real TwelveLabs API"""
    try:
        logger.info(f"Checking task status: {task_id}")
        task = tl_client.task.retrieve(task_id)
        return {
            "status": task.status,
            "video_id": task.video_id if hasattr(task, 'video_id') else None
        }
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking task status: {str(e)}")

@app.get("/check-video-embeddings/{video_id}")
async def check_video_embeddings(
    video_id: str,
    index_id: str,
    tl_client: TwelveLabs = Depends(get_twelve_labs_client)
):
    """
    Check if a video has embeddings ready for comparison.
    """
    try:
        logger.info(f"Checking embeddings for video {video_id} in index {index_id}")
        
        # Try to get the video with embeddings - try different options
        video = None
        embedding_options_to_try = [
            ["visual-text"],
            ["audio"], 
            ["visual-text", "audio"],
            []  # No embedding option
        ]
        
        for embedding_option in embedding_options_to_try:
            try:
                logger.info(f"Trying to retrieve video with embedding option: {embedding_option}")
                video = tl_client.index.video.retrieve(
                    index_id=index_id, 
                    id=video_id,
                    embedding_option=embedding_option if embedding_option else None
                )
                logger.info(f"Successfully retrieved video with option: {embedding_option}")
                break
            except Exception as e:
                logger.info(f"Failed to retrieve video with option {embedding_option}: {e}")
                continue
        
        if not video:
            raise HTTPException(status_code=404, detail=f"Could not retrieve video {video_id}")
        
        # Check if video has embeddings
        has_embeddings = False
        
        # Debug: Log the video object structure
        logger.info(f"Video object attributes: {dir(video)}")
        if hasattr(video, 'embedding'):
            logger.info(f"Video has embedding attribute: {hasattr(video, 'embedding')}")
            if video.embedding:
                logger.info(f"Embedding object attributes: {dir(video.embedding)}")
                if hasattr(video.embedding, 'video_embedding'):
                    logger.info(f"Video has video_embedding attribute")
                    if video.embedding.video_embedding and hasattr(video.embedding.video_embedding, 'segments'):
                        logger.info(f"Segments: {len(video.embedding.video_embedding.segments) if video.embedding.video_embedding.segments else 0}")
                        has_embeddings = len(video.embedding.video_embedding.segments) > 0
                    else:
                        # Try alternative embedding structure
                        logger.info("No video_embedding attribute, checking for alternative structure")
                        if hasattr(video.embedding, 'segments'):
                            logger.info(f"Direct segments: {len(video.embedding.segments) if video.embedding.segments else 0}")
                            has_embeddings = len(video.embedding.segments) > 0
                        elif hasattr(video.embedding, 'embeddings'):
                            logger.info(f"Embeddings: {len(video.embedding.embeddings) if video.embedding.embeddings else 0}")
                            has_embeddings = len(video.embedding.embeddings) > 0
                else:
                    logger.info("Embedding is None - video may not have embeddings yet")
            else:
                logger.info("Embedding is None - video may not have embeddings yet")
        else:
            logger.info("Video does not have embedding attribute")
        
        return {
            "video_id": video_id,
            "index_id": index_id,
            "has_embeddings": has_embeddings,
            "filename": video.system_metadata.filename,
            "duration": video.system_metadata.duration,
            "status": "ready" if has_embeddings else "processing"
        }
        
    except Exception as e:
        logger.error(f"Error checking embeddings for video {video_id}: {e}")
        return {
            "video_id": video_id,
            "index_id": index_id,
            "has_embeddings": False,
            "error": str(e),
            "status": "error"
        }

@app.post("/compare-videos", response_model=ComparisonResponse)
async def compare_videos(
    request: ComparisonRequest,
    tl_client: TwelveLabs = Depends(get_twelve_labs_client)
):
    """
    Compare two videos and find semantic differences.
    """
    try:
        logger.info(f"Starting comparison between videos {request.video1_id} and {request.video2_id}")
        
        # Check if both videos have embeddings ready
        video1_check = await check_video_embeddings(request.video1_id, request.index_id, tl_client)
        video2_check = await check_video_embeddings(request.video2_id, request.index_id, tl_client)
        
        if not video1_check.get("has_embeddings", False):
            raise HTTPException(
                status_code=400, 
                detail=f"Video 1 ({video1_check.get('filename', request.video1_id)}) is still processing. Please wait for embeddings to be generated."
            )
        
        if not video2_check.get("has_embeddings", False):
            raise HTTPException(
                status_code=400, 
                detail=f"Video 2 ({video2_check.get('filename', request.video2_id)}) is still processing. Please wait for embeddings to be generated."
            )
        
        # Fetch embeddings for both videos
        segments_v1 = fetch_video_embeddings(tl_client, request.video1_id, request.index_id)
        segments_v2 = fetch_video_embeddings(tl_client, request.video2_id, request.index_id)
        
        logger.info(f"Retrieved {len(segments_v1)} segments for video 1, {len(segments_v2)} segments for video 2")
        
        # Compare segments
        differing_segments = compare_segments_by_time(
            segments_v1, 
            segments_v2, 
            threshold=request.threshold,
            distance_metric=request.distance_metric
        )
        
        logger.info(f"Found {len(differing_segments)} differing segments")
        
        # Log the actual results for debugging
        logger.info(f"Comparison results: total_segments={min(len(segments_v1), len(segments_v2))}, differing_segments={len(differing_segments)}")
        logger.info(f"First few differences: {differing_segments[:3] if differing_segments else 'None'}")
        
        return ComparisonResponse(
            video1_id=request.video1_id,
            video2_id=request.video2_id,
            differences=[ComparisonResult(**diff) for diff in differing_segments],
            total_segments=min(len(segments_v1), len(segments_v2)),
            differing_segments=len(differing_segments)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error comparing videos: {e}")
        raise HTTPException(status_code=500, detail=f"Error comparing videos: {str(e)}")

@app.get("/debug/raw-videos/{index_id}")
async def get_raw_videos(index_id: str):
    """Debug endpoint to get raw video data"""
    if not tl_client:
        return {"status": "error", "message": "API key not initialized"}
    
    try:
        videos = tl_client.index.video.list(
            index_id=index_id,
            sort_by="created_at",
            sort_option="desc"
        )
        
        # Return raw data without conversion
        raw_data = []
        for video in videos:
            raw_data.append({
                "id": str(video.id),
                "created_at": str(video.created_at),
                "updated_at": str(video.updated_at),
                "filename": str(video.system_metadata.filename),
                "duration": int(video.system_metadata.duration),
                "fps": int(video.system_metadata.fps),
                "width": int(video.system_metadata.width),
                "height": int(video.system_metadata.height),
                "size": int(video.system_metadata.size)
            })
        
        return {"status": "success", "videos": raw_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/raw-indexes")
async def get_raw_indexes():
    """Debug endpoint to get raw index data"""
    if not tl_client:
        return {"status": "error", "message": "API key not initialized"}
    
    try:
        indexes = tl_client.index.list(
            model_family="marengo",
            sort_by="created_at",
            sort_option="desc"
        )
        
        # Return raw data without conversion
        raw_data = []
        for index in indexes:
            raw_data.append({
                "id": str(index.id),
                "name": str(index.name),
                "video_count": int(index.video_count),
                "total_duration": int(index.total_duration),
                "created_at": str(index.created_at),
                "updated_at": str(index.updated_at) if index.updated_at else None
            })
        
        return {"status": "success", "indexes": raw_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/test-connection")
async def test_connection():
    """Debug endpoint to test TwelveLabs connection"""
    if not tl_client:
        return {"status": "error", "message": "API key not initialized"}
    
    try:
        # Try to list indexes to test connection
        indexes = tl_client.index.list(limit=1)
        return {
            "status": "success", 
            "message": "Connection successful",
            "index_count": len(indexes)
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Connection failed: {str(e)}"
        }

@app.get("/proxy-video/{video_id}")
async def proxy_video(video_id: str, index_id: str, tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """Proxy video stream to handle CORS and authentication issues"""
    try:
        # Get video details
        video = tl_client.index.video.retrieve(index_id=index_id, id=video_id)
        
        if not video.hls or not video.hls.video_url:
            raise HTTPException(status_code=404, detail="Video stream not available")
        
        # Return video info with authentication headers needed
        return {
            "video_url": video.hls.video_url,
            "status": video.hls.status,
            "filename": video.system_metadata.filename,
            "thumbnail_urls": video.hls.thumbnail_urls or [],
            "duration": video.system_metadata.duration,
            "width": video.system_metadata.width,
            "height": video.system_metadata.height
        }
    except Exception as e:
        logger.error(f"Error proxying video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get video stream: {str(e)}")

@app.get("/video-stream/{video_id}")
async def stream_video(
    video_id: str, 
    index_id: str = Query(...),
    path: str = Query(default=""),
    tl_client: TwelveLabs = Depends(get_twelve_labs_client)
):
    """Proxy HLS stream from TwelveLabs with proper CORS headers"""
    try:
        # Get the video to find the HLS URL
        video = tl_client.index.video.retrieve(index_id=index_id, id=video_id)
        if not video.hls or not video.hls.video_url:
            raise HTTPException(status_code=404, detail="Video stream not available")
        
        base_url = video.hls.video_url
        
        # If path is provided, it's a request for a specific segment or playlist
        if path:
            # Clean the path to remove any leading slashes
            path = path.lstrip('/')
            # Construct the full URL
            if path.startswith('http'):
                # Full URL was passed
                target_url = path
            else:
                # Relative path - append to base URL's directory
                base_parts = base_url.rsplit('/', 1)
                target_url = f"{base_parts[0]}/{path}"
        else:
            target_url = base_url
        
        logger.info(f"Proxying HLS request to: {target_url}")
        
        # Make request to TwelveLabs CDN with API key
        headers = {
            "X-Api-Key": tl_client.api_key,
            "User-Agent": "Mozilla/5.0 (compatible; HLS Proxy)",
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(target_url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Determine content type
            content_type = response.headers.get("content-type", "application/octet-stream")
            
            # For m3u8 manifests, we need to rewrite URLs to go through our proxy
            if "mpegurl" in content_type or target_url.endswith('.m3u8'):
                content = response.text
                
                # Parse base URL for relative path resolution
                base_url_parts = target_url.rsplit('/', 1)
                base_path = base_url_parts[0] if len(base_url_parts) > 1 else target_url
                
                # Replace relative URLs in the manifest
                lines = content.split('\n')
                modified_lines = []
                
                for line in lines:
                    if line and not line.startswith('#'):
                        # This is a URL line
                        if line.startswith('http'):
                            # Absolute URL - encode it as a query param
                            encoded_url = urllib.parse.quote(line, safe='')
                            new_url = f"/video-stream/{video_id}?index_id={index_id}&path={encoded_url}"
                        else:
                            # Relative URL
                            new_url = f"/video-stream/{video_id}?index_id={index_id}&path={line}"
                        modified_lines.append(new_url)
                    else:
                        modified_lines.append(line)
                
                content = '\n'.join(modified_lines)
                
                return Response(
                    content=content,
                    media_type="application/x-mpegURL",
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                    }
                )
            else:
                # For .ts segments and other content, pass through as-is
                return Response(
                    content=response.content,
                    media_type=content_type,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, OPTIONS", 
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                        "Cache-Control": "max-age=3600",
                    }
                )
                
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error streaming video {video_id}: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Upstream error: {str(e)}")
    except Exception as e:
        logger.error(f"Error streaming video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stream video: {str(e)}")

@app.head("/video-stream/{video_id}")
async def stream_video_head(
    video_id: str, 
    index_id: str = Query(...),
    path: str = Query(default=""),
    tl_client: TwelveLabs = Depends(get_twelve_labs_client)
):
    """Handle HEAD requests for video streaming"""
    # Return empty response with appropriate headers
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )

@app.options("/video-stream/{video_id}")
async def stream_video_options(video_id: str):
    """Handle OPTIONS requests for CORS preflight"""
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Range",
            "Access-Control-Max-Age": "3600",
        }
    )

@app.get("/video-url/{video_id}")
async def get_video_url(video_id: str, index_id: str, tl_client: TwelveLabs = Depends(get_twelve_labs_client)):
    """Get video URL with authentication headers for direct browser access"""
    try:
        # Get video details
        video = tl_client.index.video.retrieve(index_id=index_id, id=video_id)
        
        if not video.hls or not video.hls.video_url:
            raise HTTPException(status_code=404, detail="Video stream not available")
        
        # Return the proxied URL instead of the direct CloudFront URL
        proxied_url = f"/video-stream/{video_id}?index_id={index_id}"
        
        return {
            "video_url": proxied_url,
            "api_key": None,  # No longer needed since backend handles auth
            "status": video.hls.status,
            "filename": video.system_metadata.filename,
            "thumbnail_urls": video.hls.thumbnail_urls or [],
            "duration": video.system_metadata.duration,
            "width": video.system_metadata.width,
            "height": video.system_metadata.height
        }
    except Exception as e:
        logger.error(f"Error getting video URL {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get video URL: {str(e)}")

# In-memory storage for temporary embeddings and videos
embedding_storage: Dict[str, any] = {}
video_storage: Dict[str, bytes] = {}

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
        if completed_task.video_embedding and completed_task.video_embedding.segments:
            # Get the end time of the last segment
            last_segment = completed_task.video_embedding.segments[-1]
            duration = last_segment.end_offset_sec
        
        embedding_storage[embedding_id] = {
            "filename": file.filename,
            "embeddings": completed_task.video_embedding,
            "duration": duration
        }
        
        # Store video content
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

@app.post("/compare-local-videos")
async def compare_local_videos(
    embedding_id1: str = Query(...),
    embedding_id2: str = Query(...),
    threshold: float = Query(0.2),
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
        
        # Compare segments
        differences = compare_segments_by_time(segments1, segments2, threshold, distance_metric)
        
        return {
            "filename1": embed_data1["filename"],
            "filename2": embed_data2["filename"],
            "differences": differences,
            "total_segments": len(segments1),
            "differing_segments": len(differences)
        }
        
    except Exception as e:
        logger.error(f"Error comparing videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare videos: {str(e)}")

def compare_segments_by_time(segments1, segments2, threshold=0.2, distance_metric="cosine"):
    """Compare two lists of segment embeddings"""
    def keyfunc(s):
        return round(s["start_offset_sec"], 2)
    
    dict_v1 = {keyfunc(seg): seg for seg in segments1}
    dict_v2 = {keyfunc(seg): seg for seg in segments2}
    
    all_keys = set(dict_v1.keys()).union(set(dict_v2.keys()))
    differing_segments = []
    
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
        
        if float(dist) > threshold:
            differing_segments.append({
                "start_sec": seg1["start_offset_sec"],
                "end_sec": seg1["end_offset_sec"],
                "distance": float(dist)
            })
    
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