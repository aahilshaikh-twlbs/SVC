# SAGE - ARCHITECTURE

## Overview

SAGE is a streamlined web application for semantic analysis of graph-based embeds using TwelveLabs AI. The application allows users to upload videos, generate embeddings, and analyze them to identify differences at the segment level through graph-based representations.

## Architecture

### Technology Stack

#### Backend
- **FastAPI** - Modern Python web framework
- **SQLite** - Lightweight database for API key storage
- **TwelveLabs SDK** - Video embedding generation
- **NumPy** - Vector operations for similarity calculations

#### Frontend  
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS v3** - Utility-first styling (V3 due to dependency issues with V4)
- **Bun** - Fast JavaScript runtime and package manager

## Backend Architecture (`/backend`)

### Core File: `app.py` (269 lines)

The entire backend is contained in a single, focused file that handles:

1. **API Key Management**
   - Validation endpoint for TwelveLabs API keys
   - SHA-256 hashing for secure storage
   - SQLite persistence

2. **Video Processing**
   - Upload endpoint accepting video files
   - Temporary file handling for TwelveLabs API
   - Embedding generation using Marengo-retrieval-2.7 model
   - In-memory storage for embeddings and video content

3. **Video Comparison**
   - Segment-by-segment comparison
   - Cosine and Euclidean distance calculations
   - Configurable similarity threshold
   - Real-time comparison results

### API Endpoints

```
GET /
  - Root endpoint for bot traffic
  - Returns: { message: "SAGE API", docs: "/docs" }

GET /health
  - Server health check with uptime and status
  - Returns: status, version, uptime, database_status, python_version

GET /robots.txt
  - Controls web crawlers
  - Returns: "User-agent: *\nDisallow: /"

GET /favicon.ico
  - Handles browser favicon requests
  - Returns: 204 No Content (prevents 404 logs)

POST /validate-key
  - Validates TwelveLabs API key
  - Returns: { key: string, isValid: boolean }

POST /upload-and-generate-embeddings
  - Accepts video file upload
  - Generates embeddings via TwelveLabs
  - Returns: embedding data, video metadata

POST /compare-local-videos
  - Compares two videos by embedding IDs
  - Parameters: embedding_id1, embedding_id2, threshold, distance_metric
  - Returns: differences array with timestamps and distances

GET /serve-video/{video_id}
  - Serves video content from memory
  - Returns: video/mp4 stream
```

### Database Schema

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,
    api_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Dependencies (6 total)
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- python-multipart==0.0.6
- pydantic==2.5.0
- twelvelabs==1.0.0
- numpy==1.24.3

## Frontend Architecture (`/frontend`)

### Key Components

#### Pages
- **`/` (page.tsx)** - Video upload and comparison initiation
- **`/analysis` (analysis/page.tsx)** - Comparison results visualization

#### Components
- **`ApiKeyConfig`** - TwelveLabs API key input with validation
- **UI Components** - Minimal set: Button, Card, Badge

#### Libraries (`/lib`)
- **`api.ts`** - Centralized API client with 3 endpoints
- **`utils.ts`** - Utility functions (cn for className merging)

#### Types (`/types`)
- **`index.ts`** - Type definitions including ApiKeyConfig

### Recent UI/UX Improvements

#### Progress Tracking
- Real-time status updates during video processing
- Per-video progress indicators showing:
  - Upload status: "Uploading video X..."
  - Processing status: "Generating embeddings for video X..."
  - Completion status: "Video X ready!"
- Replaced generic spinning animation with informative messages

#### Drag and Drop Enhancement
- Fixed browser video playback issue on file drop
- Added event handlers: `onDragOver`, `onDragLeave`, `onDrop`
- `e.preventDefault()` prevents default browser behavior
- Visual feedback with blue border during drag operations
- MIME type validation for video files only

#### Error Handling
- Non-blocking error display in red alert box
- Errors clear automatically on retry
- No page refresh required for recovery
- Maintains user context and uploaded files

### Features

1. **Video Upload Interface**
   - Drag-and-drop or click to upload
   - Video thumbnail generation
   - Support for 2 video comparison
   - Real-time upload progress

2. **Analysis Page**
   - Synchronized video playback
   - Visual timeline with difference markers
   - Segment-level difference list
   - Adjustable similarity threshold
   - Color-coded severity indicators

3. **Design System**
   - TwelveLabs brand colors
   - Dark/light theme support
   - Responsive layout
   - Accessible components

### Dependencies (7 total)
- next: 15.4.5
- react: 19.1.0
- react-dom: 19.1.0
- tailwindcss: ^3
- lucide-react: ^0.534.0
- clsx: ^2.1.1
- tailwind-merge: ^3.3.1

## Data Flow

1. **API Key Setup**
   - User enters TwelveLabs API key
   - Frontend validates with backend
   - Key hash stored in SQLite
   - Key persisted in localStorage

2. **Video Upload & Processing**
   - User selects 2 videos
   - Videos uploaded to backend
   - Backend creates TwelveLabs embedding tasks
   - Embeddings stored in memory
   - IDs returned to frontend

3. **Comparison**
   - Frontend requests comparison with embedding IDs
   - Backend calculates segment distances
   - Results filtered by threshold
   - Differences returned with timestamps

4. **Visualization**
   - Videos served from backend memory
   - Synchronized playback controls
   - Timeline shows difference segments
   - Real-time threshold adjustment

## Design Decisions

### Simplifications
- **In-memory storage** instead of persistent database for videos/embeddings
- **Single-file backend** for easier maintenance
- **Minimal dependencies** for both frontend and backend
- **No authentication system** - relies on API key only

### Performance Optimizations
- **Client-side video thumbnail generation**
- **Efficient vector operations** with NumPy
- **Streaming video playback** from backend
- **Real-time comparison** without page reload

### Security Considerations
- **API key hashing** before storage
- **CORS middleware** for frontend access
- **Input validation** with Pydantic
- **Error handling** with appropriate status codes

## Deployment Considerations

### Development
```bash
# Backend
cd backend
python3 app.py

# Frontend  
cd frontend
bun install
bun run dev
```

### Production Deployment

#### Current Setup
- **Backend**: Digital Ocean droplet running Ubuntu
  - Python 3.12+ with virtual environment
  - FastAPI served via Uvicorn on port 8000
  - CORS configured for frontend domain
  - Health endpoint at `/health` for monitoring
  - Bot traffic handling endpoints (/, /robots.txt, /favicon.ico)
  
- **Frontend**: Vercel deployment
  - Automatic deployments from GitHub
  - Next.js rewrites to proxy API calls
  - Avoids HTTPS/HTTP mixed content issues
  
#### Configuration
1. **Backend CORS** - Update `allow_origins` in `app.py`:
   ```python
   allow_origins=[
       "http://localhost:3000",
       "https://your-app.vercel.app"
   ]
   ```

2. **Frontend Proxy** - Configure `next.config.ts`:
   ```typescript
   async rewrites() {
     return [{
       source: '/api/:path*',
       destination: 'http://YOUR_BACKEND_IP:8000/:path*',
     }];
   }
   ```

3. **API URL** - Update `frontend/src/lib/api.ts`:
   ```typescript
   export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';
   ```

#### Security & Bot Handling
- **Bot Traffic Management**
  - Root endpoint (/) returns API info instead of 404
  - robots.txt disallows all crawlers
  - favicon.ico returns 204 to prevent log spam
  - Reduces noise from internet scanners (e.g., 167.94.138.182, 206.168.34.221)
  
- **Common Scanner Requests Handled**
  - `GET /` - Returns JSON response
  - `GET /favicon.ico` - Returns 204 No Content
  - `GET /robots.txt` - Disallows all paths
  - Prevents 404 spam in logs from automated scanners

#### Future Production Improvements
- Use process manager (PM2/systemd) for backend
- Add SSL certificates for direct HTTPS
- Deploy with Gunicorn for better performance
- Database: Consider PostgreSQL for production
- Storage: Consider S3 for video storage
- Caching: Add Redis for embeddings cache
- Rate limiting for API endpoints
- Fail2ban for repeat offenders

## Limitations

1. **In-memory storage** - Videos/embeddings lost on restart
2. **Single server** - No horizontal scaling
3. **2-video limit** - UI designed for pairwise comparison
4. **No user management** - Single API key for all users
5. **No persistence** - Comparison results not saved

## Future Enhancements

1. **Persistent Storage** - Database for videos and results
2. **Batch Comparison** - Compare multiple videos
3. **Export Features** - Download comparison reports
4. **Advanced Analytics** - Aggregate statistics
5. **Collaboration** - Share comparison results