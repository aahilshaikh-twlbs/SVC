# SAGE - Semantic Analysis via Graph-based Embeddings

## Project Overview

SAGE is a comprehensive video analysis platform that leverages TwelveLabs API for semantic video comparison and analysis. The application provides a modern web interface for managing video indexes, uploading videos, and performing semantic comparisons.

## Architecture

### Backend (`backend/`)

#### Core Files:
- **`app.py`** - FastAPI backend server with SQLite database integration
- **`SAGE.py`** - Core TwelveLabs functionality and function definitions
- **`test_api.py`** - API testing script for TwelveLabs integration
- **`requirements.txt`** - Python dependencies

#### Key Features:
- **API Key Management**: SQLite database for persistent API key storage
- **Index Management**: Create, list, rename, and delete indexes
- **Video Management**: Upload, list, and delete videos from indexes
- **Real-time Processing**: Task status monitoring for video uploads (in progress)
- **Error Handling**: Comprehensive error handling and logging (in progress)

#### Database Schema:
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### API Endpoints:
- `POST /validate-key` - Validate TwelveLabs API key
- `GET /stored-api-key` - Check for stored API key
- `GET /indexes` - List all indexes
- `POST /indexes` - Create new index
- `PUT /indexes/{index_id}` - Rename index
- `DELETE /indexes/{index_id}` - Delete index
- `GET /indexes/{index_id}/videos` - List videos in index
- `DELETE /indexes/{index_id}/videos/{video_id}` - Delete video
- `POST /upload-video` - Upload video (file or YouTube URL)
- `GET /tasks/{task_id}` - Check task status

### Frontend (`frontend/`)

#### Technology Stack:
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Icon library
- **Radix UI** - Accessible UI primitives

#### Key Components:
- **`ApiKeyConfig`** - API key input and validation
- **`IndexVisualizer`** - Index management with rename/delete
- **`VideoVisualizer`** - Video management with upload/delete
- **`Button`** - Reusable UI components

#### Features:
- **Dark Theme**: Custom dark color scheme for better readability
- **API Key Persistence**: Remembers API key across sessions
- **Real-time Updates**: Automatic refresh after operations
- **Error Handling**: User-friendly error messages
- **Loading States**: Smooth loading indicators

#### Color Scheme:
```css
--background: #0f0f0f
--foreground: #ffffff
--card: #1a1a1a
--primary: #3b82f6
--secondary: #374151
--destructive: #ef4444
```

## Core Functionality

### Index Management
- **Create Index**: New indexes with Marengo 2.7 model
- **List Indexes**: Display all available indexes
- **Rename Index**: Update index names
- **Delete Index**: Remove indexes with confirmation

### Video Management
- **Upload Videos**: Support for local files and YouTube URLs
- **List Videos**: Display videos with thumbnails and metadata
- **Delete Videos**: Remove videos with confirmation
- **Video Selection**: Select up to 2 videos for comparison

### API Integration
- **TwelveLabs SDK**: Full integration with TwelveLabs API
- **Real-time Processing**: Task status monitoring
- **Error Recovery**: Robust error handling
- **Data Conversion**: Safe conversion between API and UI models

## Development Status

### ✅ Completed
- [x] Backend API with FastAPI
- [x] Frontend with Next.js and TypeScript
- [x] API key validation and persistence
- [x] Index management (CRUD operations)
- [x] Video management (CRUD operations)
- [x] Dark theme implementation
- [x] YouTube URL upload support
- [x] Error handling and loading states
- [x] Real-time task status monitoring

### 🚧 In Progress
- [ ] Semantic comparison logic
- [ ] Analysis page implementation
- [ ] Export functionality (PDF/OTIO)
- [ ] Advanced video processing

### 📋 Planned
- [ ] User authentication
- [ ] Advanced filtering and search
- [ ] Batch operations
- [ ] Performance optimizations
- [ ] Production deployment

## File Structure

```
SAGE/
├── backend/
│   ├── app.py              # FastAPI server
│   ├── SAGE.py             # Core functionality
│   ├── test_api.py         # API testing
│   ├── requirements.txt    # Dependencies
│   ├── sage.db            # SQLite database
│   └── README.md          # Backend docs
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   ├── components/    # React components
│   │   ├── lib/          # Utilities and API
│   │   └── types/        # TypeScript types
│   ├── package.json       # Dependencies
│   └── README.md         # Frontend docs
├── docs/
│   └── ARCHITECTURE.md   # This file
└── README.md             # Project overview
```

## Setup Instructions

### Backend Setup
```bash
cd SAGE/backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

### Frontend Setup
```bash
cd SAGE/frontend
npm install
npm run dev
```

## API Key Configuration

1. Get your TwelveLabs API key from the dashboard
2. Enter the key in the frontend
3. The key is automatically saved and validated
4. The key persists across browser sessions

## Usage

1. **Configure API Key**: Enter your TwelveLabs API key
2. **Browse Indexes**: View all your indexes
3. **Manage Indexes**: Create, rename, or delete indexes
4. **Upload Videos**: Add videos via file upload or YouTube URL
5. **Select Videos**: Choose 2 videos for comparison
6. **Run Analysis**: Perform semantic comparison (coming soon)

## Technical Notes

### TwelveLabs Integration
- Uses Marengo 2.7 model exclusively
- Supports visual and audio analysis
- Real-time task monitoring
- Robust error handling

### Database
- SQLite for simplicity
- API key hashing for security
- Automatic database initialization

### Frontend
- Responsive design
- Dark theme for better UX
- Type-safe development
- Accessible UI components

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]