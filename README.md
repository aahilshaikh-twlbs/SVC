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

### Backend Setup

```bash
# Navigate to backend
cd SAGE/backend

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

Backend runs at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend
cd SAGE/frontend

# Install dependencies (using Bun)
bun install

# Start development server
bun run dev
```

Frontend runs at `http://localhost:3000`

## 📝 Usage

1. **Enter API Key** - Add your TwelveLabs API key when prompted
2. **Upload Videos** - Select two videos to compare
3. **Generate Embeddings** - Wait for AI processing (progress shown)
4. **View Analysis** - See synchronized playback with differences highlighted
5. **Adjust Threshold** - Use slider to show more/fewer differences

## 🏗️ Architecture

### Minimalist Design
- **Backend**: Single 269-line Python file
- **Frontend**: Focused React components
- **Dependencies**: Only 6 backend + 7 frontend packages

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

Frontend (optional):
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API Endpoints

- `POST /validate-key` - Validate TwelveLabs API key
- `POST /upload-and-generate-embeddings` - Process video
- `POST /compare-local-videos` - Compare embeddings
- `GET /serve-video/{video_id}` - Stream video

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