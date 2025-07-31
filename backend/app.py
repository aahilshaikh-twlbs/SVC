from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import sqlite3
from twelvelabs import TwelveLabs
import hashlib
import numpy as np

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
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()

def save_api_key_hash(key: str):
    """Save API key hash to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT OR REPLACE INTO api_keys (key_hash) VALUES (?)', 
                      (hash_api_key(key),))
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
                if hasattr(video, 'embedding') and video.embedding and video.embedding.video_embedding and video.embedding.video_embedding.segments:
                    logger.info(f"Found embeddings for video {video_id} with option: {embedding_option}")
                    
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
                    logger.info(f"No embeddings found with option: {embedding_option}")
                    
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
        indexes = tl_client.index.list(
            model_family="marengo",
            sort_by="created_at",
            sort_option="desc"
        )
        
        logger.info(f"Found {len(indexes)} indexes")
        
        # Convert to our model format
        result = []
        for index in indexes:
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
        videos = tl_client.index.video.list(
            index_id=index_id,
            sort_by="created_at",
            sort_option="desc"
        )
        
        logger.info(f"Found {len(videos)} videos")
        
        # Convert to our model format
        result = []
        for video in videos:
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
        
        return ComparisonResponse(
            video1_id=request.video1_id,
            video2_id=request.video2_id,
            differences=[ComparisonResult(**diff) for diff in differing_segments],
            total_segments=min(len(segments_v1), len(segments_v2)),
            differing_segments=len(differing_segments)
        )
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 