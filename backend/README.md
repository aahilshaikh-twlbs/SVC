# SVC Backend

A FastAPI backend for the Semantic Video Comparison (SVC) application.

## Features

- **API Key Validation**: Mock validation endpoint for TwelveLabs API keys
- **Index Management**: CRUD operations for video indexes
- **Video Management**: Upload and manage videos in indexes
- **CORS Support**: Configured for frontend integration
- **Mock Data**: Sample data for testing the frontend

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```bash
   python app.py
   ```

3. The API will be available at [http://localhost:8000](http://localhost:8000)

4. API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

### Authentication
- `POST /validate-key` - Validate API key

### Indexes
- `GET /indexes` - List all indexes
- `POST /indexes` - Create new index

### Videos
- `GET /indexes/{index_id}/videos` - List videos in index
- `POST /upload-video` - Upload video file or URL

### Tasks
- `GET /tasks/{task_id}` - Check task status

## Mock Data

The backend includes mock data for testing:

- **Sample Indexes**: Two pre-created indexes with different video counts
- **Sample Videos**: Videos with various metadata and thumbnail URLs
- **Upload Simulation**: Mock video upload process with task tracking

## Development

This is a mock backend for frontend development. In production, it would:

1. Integrate with TwelveLabs API for real functionality
2. Implement proper authentication and authorization
3. Handle file uploads and video processing
4. Manage database persistence
5. Implement proper error handling and validation

## Tech Stack

- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server
- **CORS**: Cross-origin resource sharing support 