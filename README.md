# SAGE - Semantic Video Comparison

A lightweight web application for comparing videos using TwelveLabs AI embeddings to identify semantic differences.

![SAGE Banner](https://img.shields.io/badge/SAGE-Semantic%20Video%20Comparison-blue)

## 🎯 Features

- **🔑 Simple Setup** - Just add your TwelveLabs API key
- **📹 Local Video Upload** - Compare any two MP4 videos
- **🧠 AI-Powered Analysis** - Uses TwelveLabs Marengo-retrieval-2.7 model
- **📊 Visual Comparison** - Side-by-side playback with difference timeline
- **🎚️ Adjustable Threshold** - Fine-tune sensitivity in real-time
- **🎨 Modern UI** - Clean interface with TwelveLabs branding

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+ or Bun
- TwelveLabs API key ([Get one here](https://twelvelabs.io))

### Local Development

#### Backend Setup

```bash
# Navigate to backend
cd SAGE/backend

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

Backend runs at `http://localhost:8000`

#### Frontend Setup

```bash
# Navigate to frontend
cd SAGE/frontend

# Install dependencies (using Bun)
bun install

# Start development server
bun run dev
```

Frontend runs at `http://localhost:3000`

### Production Deployment

#### Backend on Digital Ocean

1. Deploy to a Digital Ocean droplet
2. Install dependencies and run:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```
3. Update CORS in `app.py` to include your frontend URL
4. Ensure port 8000 is accessible

#### Frontend on Vercel

1. Push code to GitHub
2. Connect repository to Vercel
3. Configure Next.js rewrites in `next.config.ts`:
   ```typescript
   async rewrites() {
     return [{
       source: '/api/:path*',
       destination: 'http://YOUR_BACKEND_IP:8000/:path*',
     }];
   }
   ```
4. Deploy automatically on push

## 📝 Usage

1. **Enter API Key** - Add your TwelveLabs API key when prompted
2. **Upload Videos** - Select two videos to compare
3. **Generate Embeddings** - Wait for AI processing (progress shown)
4. **View Analysis** - See synchronized playback with differences highlighted
5. **Adjust Threshold** - Use slider to show more/fewer differences

## 🏗️ Architecture

### Minimalist Design
- **Backend**: Single Python file with FastAPI
- **Frontend**: Focused React components with Next.js
- **Dependencies**: Only 6 backend + 7 frontend packages

### Production Architecture
- **Backend**: Digital Ocean droplet (Ubuntu)
- **Frontend**: Vercel deployment
- **Communication**: HTTPS proxy via Vercel rewrites (avoids CORS issues)

### Key Technologies
- **FastAPI** - High-performance Python API
- **Next.js 15** - Modern React framework
- **TwelveLabs SDK** - Video AI embeddings
- **Tailwind CSS** - Utility-first styling

## 📁 Project Structure

```
SAGE/
├── backend/
│   ├── app.py              # Entire backend (269 lines)
│   ├── requirements.txt    # 6 dependencies
│   └── sage.db            # SQLite database
├── frontend/
│   ├── src/
│   │   ├── app/           # Pages (upload, analysis)
│   │   ├── components/    # UI components
│   │   ├── lib/          # API client
│   │   └── types/        # TypeScript types
│   └── package.json       # 7 dependencies
└── docs/
    └── ARCHITECTURE.md    # Detailed documentation
```

## 🔧 Configuration

### Environment Variables

#### Local Development
```bash
# Frontend .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Production
```bash
# Frontend (Vercel)
# No env needed if using rewrites
# OR set NEXT_PUBLIC_API_URL in Vercel dashboard
```

### API Endpoints

- `GET /health` - Health check (server status, uptime)
- `POST /validate-key` - Validate TwelveLabs API key
- `POST /upload-and-generate-embeddings` - Process video
- `POST /compare-local-videos` - Compare embeddings
- `GET /serve-video/{video_id}` - Stream video

#### Health Endpoint Response
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "uptime": "1:00:00",
  "timestamp": "2025-08-02T12:00:00Z",
  "database_status": "healthy",
  "python_version": "3.12.3"
}

## 🎨 UI Features

### Upload Page
- Drag-and-drop video upload
- Thumbnail preview
- File size display
- Progress indicators

### Analysis Page
- Synchronized dual video players
- Interactive timeline with markers
- Color-coded difference segments
- Real-time threshold adjustment
- Segment list with timestamps

## 📊 Comparison Metrics

- **Distance Methods**: Cosine (default) or Euclidean
- **Segment Length**: 2-second clips
- **Threshold**: 0.05 default (adjustable 0-1)
- **Color Coding**: 
  - 🟦 Minimal (< 0.05)
  - 🟩 Minor (0.05-0.1)
  - 🟨 Moderate (0.1-0.2)
  - 🟧 Significant (0.2-0.3)
  - 🟥 Major (> 0.3)

## ⚡ Performance

- **Fast Processing**: ~30 seconds per minute of video
- **Memory Efficient**: Streams videos, stores only embeddings
- **Real-time Updates**: Instant threshold changes
- **Lightweight**: < 10MB total codebase

## 🚧 Limitations

- Videos stored in memory (lost on restart)
- 2-video comparison only
- No result persistence
- Single user (no auth system)

## 🛠️ Development

### Testing
```bash
# Backend
cd backend
python -m pytest

# Frontend
cd frontend
bun test
```

### Building
```bash
# Frontend production build
cd frontend
bun run build
```

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open Pull Request

## 🙏 Acknowledgments

- [TwelveLabs](https://twelvelabs.io) for the amazing video AI API
- [FastAPI](https://fastapi.tiangolo.com) for the backend framework
- [Next.js](https://nextjs.org) for the frontend framework
- [Tailwind CSS](https://tailwindcss.com) for styling

---

Built with ❤️ for semantic video analysis