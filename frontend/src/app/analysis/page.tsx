'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api, API_BASE_URL } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Play, Pause } from 'lucide-react';

interface VideoData {
  id: string;
  filename: string;
  embedding_id: string;
  video_id: string;
  duration: number;
}

interface Difference {
  start_sec: number;
  end_sec: number;
  distance: number;
}

export default function AnalysisPage() {
  const router = useRouter();
  const [video1Data, setVideo1Data] = useState<VideoData | null>(null);
  const [video2Data, setVideo2Data] = useState<VideoData | null>(null);
  const [differences, setDifferences] = useState<Difference[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const video1Ref = useRef<HTMLVideoElement>(null);
  const video2Ref = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        // Get video data from session storage
        const video1Str = sessionStorage.getItem('video1_data');
        const video2Str = sessionStorage.getItem('video2_data');
        
        if (!video1Str || !video2Str) {
          setError('No video data found. Please upload videos first.');
          return;
        }
        
        const video1 = JSON.parse(video1Str) as VideoData;
        const video2 = JSON.parse(video2Str) as VideoData;
        
        setVideo1Data(video1);
        setVideo2Data(video2);
        
        // Compare videos
        const comparison = await api.compareLocalVideos(
          video1.embedding_id,
          video2.embedding_id
        );
        
        setDifferences(comparison.differences);
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load comparison data');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, []);

  const handlePlayPause = () => {
    if (video1Ref.current && video2Ref.current) {
      if (isPlaying) {
        video1Ref.current.pause();
        video2Ref.current.pause();
      } else {
        video1Ref.current.play();
        video2Ref.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const seekToTime = (time: number) => {
    if (video1Ref.current && video2Ref.current) {
      video1Ref.current.currentTime = time;
      video2Ref.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleTimeUpdate = () => {
    if (video1Ref.current) {
      setCurrentTime(video1Ref.current.currentTime);
    }
  };

  const getSeverityColor = (distance: number) => {
    if (distance === Infinity) return 'bg-red-500';
    if (distance > 0.5) return 'bg-red-400';
    if (distance > 0.3) return 'bg-orange-400';
    return 'bg-yellow-400';
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Analyzing videos...</p>
        </div>
      </div>
    );
  }

  if (error || !video1Data || !video2Data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Failed to load video data'}</p>
          <Button onClick={() => router.push('/')}>
            Back to Upload
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => router.push('/')}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Upload
              </Button>
              <h1 className="text-xl font-semibold text-gray-900">Video Comparison Analysis</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Players */}
          <div className="lg:col-span-2 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">{video1Data.filename}</h3>
                <video
                  ref={video1Ref}
                  src={`${API_BASE_URL}/serve-video/${video1Data.video_id}`}
                  className="w-full rounded-lg shadow-sm"
                  onTimeUpdate={handleTimeUpdate}
                />
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">{video2Data.filename}</h3>
                <video
                  ref={video2Ref}
                  src={`${API_BASE_URL}/serve-video/${video2Data.video_id}`}
                  className="w-full rounded-lg shadow-sm"
                />
              </div>
            </div>

            {/* Video Controls */}
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="flex items-center gap-4">
                <Button
                  onClick={handlePlayPause}
                  size="sm"
                  variant="outline"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </Button>
                <span className="text-sm text-gray-600">
                  {formatTime(currentTime)} / {formatTime(video1Data.duration)}
                </span>
              </div>

              {/* Timeline with Markers */}
              <div className="mt-4 relative">
                <div className="h-2 bg-gray-200 rounded-full relative">
                  {/* Progress bar */}
                  <div 
                    className="absolute h-full bg-blue-500 rounded-full"
                    style={{ width: `${(currentTime / video1Data.duration) * 100}%` }}
                  />
                  
                  {/* Difference markers */}
                  {differences.map((diff, index) => (
                    <div
                      key={index}
                      className={`absolute w-1 h-4 -top-1 ${getSeverityColor(diff.distance)}`}
                      style={{ left: `${(diff.start_sec / video1Data.duration) * 100}%` }}
                      title={`Difference at ${formatTime(diff.start_sec)}`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Differences List */}
          <div className="lg:col-span-1">
            <Card className="p-4">
              <h2 className="text-lg font-semibold mb-4">
                Detected Differences ({differences.length})
              </h2>
              
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {differences.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    No significant differences found
                  </p>
                ) : (
                  differences.map((diff, index) => (
                    <div
                      key={index}
                      className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                      onClick={() => seekToTime(diff.start_sec)}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {formatTime(diff.start_sec)} - {formatTime(diff.end_sec)}
                        </span>
                        <Badge className={`${getSeverityColor(diff.distance)} text-white`}>
                          {diff.distance === Infinity ? 'Missing' : diff.distance.toFixed(3)}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Summary */}
              <div className="mt-4 pt-4 border-t">
                <div className="text-sm text-gray-600">
                  <p>Total segments analyzed: {Math.floor(video1Data.duration / 2)}</p>
                  <p>Segments with differences: {differences.length}</p>
                  <p>Similarity: {((1 - differences.length / Math.floor(video1Data.duration / 2)) * 100).toFixed(1)}%</p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}