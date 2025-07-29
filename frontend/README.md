# SVC Frontend

A Next.js frontend for the Semantic Video Comparison (SVC) application.

## Features

- **API Key Configuration**: Secure API key input with validation
- **Index Management**: View and create TwelveLabs indexes
- **Video Management**: Upload videos from files or YouTube URLs
- **Video Selection**: Select two videos for semantic comparison
- **Modern UI**: Clean, responsive interface built with Tailwind CSS

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **Configure API Key**: Enter your TwelveLabs API key to get started
2. **Browse Indexes**: View all available indexes for your account
3. **Create Indexes**: Create new indexes with Marengo 2.7 model
4. **Upload Videos**: Upload videos from local files or YouTube URLs
5. **Select Videos**: Choose two videos for semantic comparison
6. **Run Comparison**: Start the semantic analysis process

## Tech Stack

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library
- **Radix UI**: Accessible UI primitives

## Project Structure

```
src/
├── app/                 # Next.js app router
├── components/          # React components
│   ├── ui/             # Reusable UI components
│   ├── ApiKeyConfig.tsx
│   ├── IndexVisualizer.tsx
│   └── VideoVisualizer.tsx
├── lib/                # Utility functions
│   ├── api.ts          # API client
│   └── utils.ts        # Helper functions
└── types/              # TypeScript type definitions
    └── index.ts
```

## API Integration

The frontend communicates with the backend through RESTful APIs:

- `POST /validate-key` - Validate API key
- `GET /indexes` - List all indexes
- `POST /indexes` - Create new index
- `GET /indexes/{id}/videos` - List videos in index
- `POST /upload-video` - Upload video file or URL
- `GET /tasks/{id}` - Check task status
