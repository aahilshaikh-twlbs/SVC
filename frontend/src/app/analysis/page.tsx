'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Play, Pause } from 'lucide-react';
import { api } from '@/lib/api';

interface ComparisonDifference {
  start_sec: number;
  end_sec: number;
  distance: number;
}

interface ComparisonResult {
  video1_id: string;
  video2_id: string;
  differences: ComparisonDifference[];
  total_segments: number;
  differing_segments: number;
}

interface Video {
  id: string;
  system_metadata: {
    filename: string;
    duration: number;
    width: number;
    height: number;
  };
  hls?: {
    video_url: string;
    thumbnail_urls?: string[];
  };
}

function AnalysisPageContent() {
  const searchParams = useSearchParams();
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [video1, setVideo1] = useState<Video | null>(null);
  const [video2, setVideo2] = useState<Video | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<'video1' | 'video2'>('video1');
  const [showSideBySide, setShowSideBySide] = useState(false);

  const video1Id = searchParams.get('video1');
  const video2Id = searchParams.get('video2');
  const indexId = searchParams.get('index');

  useEffect(() => {
    if (!video1Id || !video2Id || !indexId) {
      setError('Missing video or index parameters');
      setLoading(false);
      return;
    }

    const runComparison = async () => {
      try {
        setLoading(true);
        setError('');

        // Get API key from localStorage
        const apiKey = localStorage.getItem('sage_api_key');
        if (!apiKey) {
          setError('API key not found');
          return;
        }

        // Run the comparison
        const result = await api.compareVideos({
          video1_id: video1Id,
          video2_id: video2Id,
          index_id: indexId,
          threshold: 0.03,
          distance_metric: 'cosine'
        }, apiKey);

        setComparisonResult(result);

        // Fetch video details
        const videos = await api.listVideos(indexId, apiKey);
        const v1 = videos.find(v => v.id === video1Id);
        const v2 = videos.find(v => v.id === video2Id);

        if (v1) setVideo1(v1);
        if (v2) setVideo2(v2);

        if (v1) setDuration(v1.system_metadata.duration);

      } catch (err) {
        console.error('Comparison error:', err);
        setError(err instanceof Error ? err.message : 'Failed to run comparison');
      } finally {
        setLoading(false);
      }
    };

    runComparison();
  }, [video1Id, video2Id, indexId]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCurrentDifferences = () => {
    if (!comparisonResult) return [];
    return comparisonResult.differences.filter(diff => 
      currentTime >= diff.start_sec && currentTime <= diff.end_sec
    );
  };

  const handleTimeUpdate = (e: React.SyntheticEvent<HTMLVideoElement>) => {
    setCurrentTime(e.currentTarget.currentTime);
  };

  const handlePlayPause = () => {
    const video = document.getElementById('video-player') as HTMLVideoElement;
    if (video) {
      if (isPlaying) {
        video.pause();
      } else {
        video.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = document.getElementById('video-player') as HTMLVideoElement;
    if (video) {
      const newTime = parseFloat(e.target.value);
      video.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-lg text-gray-600">Running semantic comparison...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-red-800 mb-2">Comparison Failed</h2>
            <p className="text-red-600">{error}</p>
            <Button 
              onClick={() => window.history.back()} 
              className="mt-4"
            >
              Go Back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!comparisonResult || !video1 || !video2) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <p className="text-lg text-gray-600">No comparison data available</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Semantic Analysis</h1>
            <p className="text-gray-600">
              Comparing {video1.system_metadata.filename} vs {video2.system_metadata.filename}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant={showSideBySide ? "default" : "outline"}
              onClick={() => setShowSideBySide(!showSideBySide)}
            >
              {showSideBySide ? "Single View" : "Side by Side"}
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Total Segments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{comparisonResult.total_segments}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Differing Segments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-orange-600">
                {comparisonResult.differing_segments}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Difference Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {comparisonResult.total_segments > 0 
                  ? ((comparisonResult.differing_segments / comparisonResult.total_segments) * 100).toFixed(1)
                  : 0}%
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Video Player Section */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Video Player */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <CardTitle>Video Player</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Video Selection */}
                  <div className="flex gap-2">
                    <Button
                      variant={selectedVideo === 'video1' ? 'default' : 'outline'}
                      onClick={() => setSelectedVideo('video1')}
                    >
                      Video A: {video1.system_metadata.filename}
                    </Button>
                    <Button
                      variant={selectedVideo === 'video2' ? 'default' : 'outline'}
                      onClick={() => setSelectedVideo('video2')}
                    >
                      Video B: {video2.system_metadata.filename}
                    </Button>
                  </div>

                  {/* Video Player */}
                  <div className="relative bg-black rounded-lg overflow-hidden">
                    <video
                      id="video-player"
                      className="w-full h-96 object-contain"
                      onTimeUpdate={handleTimeUpdate}
                      onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
                      onPlay={() => setIsPlaying(true)}
                      onPause={() => setIsPlaying(false)}
                      src={selectedVideo === 'video1' && video1.hls?.video_url 
                        ? video1.hls.video_url 
                        : video2.hls?.video_url}
                    />
                    
                    {/* Current Differences Overlay */}
                    {getCurrentDifferences().length > 0 && (
                      <div className="absolute top-4 right-4 bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                        ⚠️ Difference Detected
                      </div>
                    )}
                  </div>

                  {/* Video Controls */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Button size="sm" onClick={handlePlayPause}>
                        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      </Button>
                      <span className="text-sm text-gray-600">
                        {formatTime(currentTime)} / {formatTime(duration)}
                      </span>
                    </div>
                    
                    {/* Timeline */}
                    <div className="relative">
                      <input
                        type="range"
                        min="0"
                        max={duration}
                        value={currentTime}
                        onChange={handleSeek}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      
                      {/* Difference Markers */}
                      <div className="absolute top-0 left-0 right-0 h-2 pointer-events-none">
                        {comparisonResult.differences.map((diff, index) => (
                          <div
                            key={index}
                            className="absolute h-2 bg-red-500 opacity-60"
                            style={{
                              left: `${(diff.start_sec / duration) * 100}%`,
                              width: `${((diff.end_sec - diff.start_sec) / duration) * 100}%`
                            }}
                            title={`Difference: ${formatTime(diff.start_sec)} - ${formatTime(diff.end_sec)} (${diff.distance.toFixed(3)})`}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Differences List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Differences</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {comparisonResult.differences.length === 0 ? (
                    <p className="text-gray-500 text-sm">No significant differences found</p>
                  ) : (
                    comparisonResult.differences.map((diff, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          currentTime >= diff.start_sec && currentTime <= diff.end_sec
                            ? 'bg-red-50 border-red-200'
                            : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                        }`}
                        onClick={() => {
                          const video = document.getElementById('video-player') as HTMLVideoElement;
                          if (video) {
                            video.currentTime = diff.start_sec;
                            setCurrentTime(diff.start_sec);
                          }
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">
                            {formatTime(diff.start_sec)} - {formatTime(diff.end_sec)}
                          </span>
                          <Badge variant="destructive" className="text-xs">
                            {diff.distance.toFixed(3)}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                          Duration: {formatTime(diff.end_sec - diff.start_sec)}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading analysis...</p>
        </div>
      </div>
    }>
      <AnalysisPageContent />
    </Suspense>
  );
} 