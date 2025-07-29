# SVC - Semantic Video Comparison

A modern web application for comparing videos semantically using TwelveLabs AI technology.

## Overview

SVC allows users to:
- Configure their TwelveLabs API key
- Browse and create video indexes
- Upload videos from local files or YouTube URLs
- Select two videos for semantic comparison
- Run semantic analysis to find differences between videos

## Project Structure

```
SVC/
├── backend/           # FastAPI backend
│   ├── app.py        # Main API server
│   ├── requirements.txt
│   └── README.md
├── frontend/          # Next.js frontend
│   ├── src/
│   │   ├── app/      # Next.js app router
│   │   ├── components/
│   │   ├── lib/      # Utilities and API client
│   │   └── types/    # TypeScript definitions
│   ├── package.json
│   └── README.md
├── docs/             # Documentation
└── README.md         # This file
```

## Quick Start

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Test your TwelveLabs API key:
   ```bash
   python test_api.py
   ```

4. Start the backend server:
   ```bash
   python app.py
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

## Features

### Landing Page
- **API Key Configuration**: Secure input with validation
- **Index Visualization**: Browse all available indexes with metadata
- **Index Creation**: Create new indexes with Marengo 2.7 model
- **Video Visualization**: View videos in selected indexes with thumbnails
- **Video Upload**: Upload from local files or YouTube URLs
- **Video Selection**: Select exactly two videos for comparison

### User Experience
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean interface with Tailwind CSS
- **Real-time Feedback**: Loading states and error handling
- **Intuitive Navigation**: Clear flow from setup to comparison

## Technology Stack

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Lucide React**: Icon library
- **Radix UI**: Accessible components

### Backend
- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
- **CORS**: Cross-origin support

## API Integration

The application is designed to integrate with TwelveLabs API:

- **Index Management**: Create and manage video indexes
- **Video Upload**: Upload videos to indexes for processing
- **Semantic Analysis**: Compare videos using AI embeddings
- **Task Tracking**: Monitor processing status

## Development Status

This is a **landing page implementation** that includes:

✅ **Completed**
- API key configuration interface
- Index browsing and creation
- Video browsing and upload
- Video selection for comparison
- Modern, responsive UI
- Mock backend for testing

🔄 **In Progress**
- Backend integration with TwelveLabs API
- Semantic comparison logic
- Analysis page implementation

📋 **Planned**
- Real video processing
- Comparison results visualization
- Export functionality (PDF/OTIO)
- Production deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.