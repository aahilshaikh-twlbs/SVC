'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Play, Pause } from 'lucide-react';
import { api } from '@/lib/api';
import CustomHLSPlayer from '@/components/CustomHLSPlayer';

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

        // Fetch video details and try to get working video streams
        const videos = await api.listVideos(indexId, apiKey);
        const v1 = videos.find(v => v.id === video1Id);
        const v2 = videos.find(v => v.id === video2Id);

        if (v1) {
          setVideo1(v1);
          console.log('Video 1 HLS URL:', v1.hls?.video_url);
          
          // Try to get working video stream via new endpoint
          try {
            const stream1 = await api.getVideoUrl(video1Id, indexId, apiKey);
            console.log('Video 1 URL:', stream1);
            // Update video with working stream URL and additional info
            setVideo1({
              ...v1,
              hls: {
                ...v1.hls,
                video_url: stream1.video_url, // Use original URL
                thumbnail_urls: stream1.thumbnail_urls
              }
            });
          } catch (err) {
            console.error('Failed to get Video 1 URL:', err);
          }
        }
        
        if (v2) {
          setVideo2(v2);
          console.log('Video 2 HLS URL:', v2.hls?.video_url);
          
          // Try to get working video stream via new endpoint
          try {
            const stream2 = await api.getVideoUrl(video2Id, indexId, apiKey);
            console.log('Video 2 URL:', stream2);
            // Update video with working stream URL and additional info
            setVideo2({
              ...v2,
              hls: {
                ...v2.hls,
                video_url: stream2.video_url, // Use original URL
                thumbnail_urls: stream2.thumbnail_urls
              }
            });
          } catch (err) {
            console.error('Failed to get Video 2 URL:', err);
          }
        }

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
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mx-auto mb-6"></div>
          <h2 className="text-xl font-semibold text-white mb-2">Running Semantic Analysis</h2>
          <p className="text-gray-400 text-lg">Comparing video embeddings...</p>
          <div className="mt-4 flex justify-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/50 border border-red-600 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-red-400 mb-2">Comparison Failed</h2>
            <p className="text-red-300">{error}</p>
            <Button 
              onClick={() => window.history.back()} 
              className="mt-4 bg-blue-600 hover:bg-blue-700"
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
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <p className="text-lg text-gray-300">No comparison data available</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Semantic Analysis</h1>
            <p className="text-gray-300">
              Comparing <span className="font-medium">{video1.system_metadata.filename}</span> vs <span className="font-medium">{video2.system_metadata.filename}</span>
            </p>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-sm text-gray-300">Total Segments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">{comparisonResult.total_segments}</p>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-sm text-gray-300">Differing Segments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-orange-400">
                {comparisonResult.differing_segments}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-sm text-gray-300">Difference Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">
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
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">Video Player</CardTitle>
                  <Button
                    variant={showSideBySide ? "default" : "outline"}
                    onClick={() => setShowSideBySide(!showSideBySide)}
                    className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
                    size="sm"
                  >
                    {showSideBySide ? "Single View" : "Side by Side"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Video Selection - Only show in single view */}
                  {!showSideBySide && (
                    <div className="flex gap-2">
                      <Button
                        variant={selectedVideo === 'video1' ? 'default' : 'outline'}
                        onClick={() => setSelectedVideo('video1')}
                        className={selectedVideo === 'video1' ? 'bg-blue-600 hover:bg-blue-700' : 'border-gray-600 text-gray-300 hover:bg-gray-700'}
                      >
                        Video A: {video1.system_metadata.filename}
                      </Button>
                      <Button
                        variant={selectedVideo === 'video2' ? 'default' : 'outline'}
                        onClick={() => setSelectedVideo('video2')}
                        className={selectedVideo === 'video2' ? 'bg-blue-600 hover:bg-blue-700' : 'border-gray-600 text-gray-300 hover:bg-gray-700'}
                      >
                        Video B: {video2.system_metadata.filename}
                      </Button>
                    </div>
                  )}

                  {/* Video Player */}
                  {showSideBySide ? (
                    <div className="grid grid-cols-2 gap-4">
                      {/* Video 1 */}
                      <div className="relative bg-black rounded-lg overflow-hidden">
                        <div className="absolute top-2 left-2 bg-blue-600 text-white px-2 py-1 rounded text-xs font-medium z-10">
                          Video A
                        </div>
                        {video1.hls?.video_url ? (
                          <CustomHLSPlayer
                            src={video1.hls.video_url}
                            className="w-full h-80 object-contain"
                            onTimeUpdate={(currentTime) => {
                              setCurrentTime(currentTime);
                              // Sync with video 2
                              const video2 = document.getElementById('video-player-2') as HTMLVideoElement;
                              if (video2 && Math.abs(currentTime - video2.currentTime) > 0.5) {
                                video2.currentTime = currentTime;
                              }
                            }}
                            onLoadedData={() => {
                              const video = document.getElementById('video-player-1') as HTMLVideoElement;
                              if (video) setDuration(video.duration);
                            }}
                            onError={(error) => {
                              console.error('Video 1 playback error:', error);
                            }}
                            uniqueKey={`video1-${video1.id}`}
                          />
                        ) : (
                          <div className="w-full h-80 flex items-center justify-center bg-gray-800 text-white">
                            <div className="text-center">
                              <p className="text-sm mb-2">Video A Not Available</p>
                              <p className="text-xs text-gray-400">HLS stream missing</p>
                              {video1.hls?.thumbnail_urls && video1.hls.thumbnail_urls.length > 0 && (
                                <img 
                                  src={video1.hls.thumbnail_urls[0]} 
                                  alt="Video A thumbnail"
                                  className="mt-2 max-w-full max-h-32 object-contain"
                                />
                              )}
                              <div className="mt-2 text-xs text-gray-400">
                                <p>Duration: {Math.round(video1.system_metadata.duration / 60)}min</p>
                                <p>Resolution: {video1.system_metadata.width}x{video1.system_metadata.height}</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Video 2 */}
                      <div className="relative bg-black rounded-lg overflow-hidden">
                        <div className="absolute top-2 left-2 bg-green-600 text-white px-2 py-1 rounded text-xs font-medium z-10">
                          Video B
                        </div>
                        {video2.hls?.video_url ? (
                          <CustomHLSPlayer
                            src={video2.hls.video_url}
                            className="w-full h-80 object-contain"
                            onTimeUpdate={(currentTime) => {
                              setCurrentTime(currentTime);
                              // Sync with video 1
                              const video1 = document.getElementById('video-player-1') as HTMLVideoElement;
                              if (video1 && Math.abs(currentTime - video1.currentTime) > 0.5) {
                                video1.currentTime = currentTime;
                              }
                            }}
                            onLoadedData={() => {
                              const video = document.getElementById('video-player-2') as HTMLVideoElement;
                              if (video) setDuration(video.duration);
                            }}
                            onError={(error) => {
                              console.error('Video 2 playback error:', error);
                            }}
                            uniqueKey={`video2-${video2.id}`}
                          />
                        ) : (
                          <div className="w-full h-80 flex items-center justify-center bg-gray-800 text-white">
                            <div className="text-center">
                              <p className="text-sm mb-2">Video B Not Available</p>
                              <p className="text-xs text-gray-400">HLS stream missing</p>
                              {video2.hls?.thumbnail_urls && video2.hls.thumbnail_urls.length > 0 && (
                                <img 
                                  src={video2.hls.thumbnail_urls[0]} 
                                  alt="Video B thumbnail"
                                  className="mt-2 max-w-full max-h-32 object-contain"
                                />
                              )}
                              <div className="mt-2 text-xs text-gray-400">
                                <p>Duration: {Math.round(video2.system_metadata.duration / 60)}min</p>
                                <p>Resolution: {video2.system_metadata.width}x{video2.system_metadata.height}</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="relative bg-black rounded-lg overflow-hidden">
                      {selectedVideo === 'video1' && video1.hls?.video_url ? (
                        <CustomHLSPlayer
                          src={video1.hls.video_url}
                          className="w-full h-96 object-contain"
                          onTimeUpdate={handleTimeUpdate}
                          onLoadedData={() => {
                            const video = document.getElementById('video-player') as HTMLVideoElement;
                            if (video) setDuration(video.duration);
                          }}
                          onError={(error) => {
                            console.error('Video playback error:', error);
                          }}
                          uniqueKey={`single-video1-${video1.id}`}
                        />
                      ) : selectedVideo === 'video2' && video2.hls?.video_url ? (
                        <CustomHLSPlayer
                          src={video2.hls.video_url}
                          className="w-full h-96 object-contain"
                          onTimeUpdate={handleTimeUpdate}
                          onLoadedData={() => {
                            const video = document.getElementById('video-player') as HTMLVideoElement;
                            if (video) setDuration(video.duration);
                          }}
                          onError={(error) => {
                            console.error('Video playback error:', error);
                          }}
                          uniqueKey={`single-video2-${video2.id}`}
                        />
                      ) : (
                        <div className="w-full h-96 flex items-center justify-center bg-gray-800 text-white">
                          <div className="text-center">
                            <p className="text-lg mb-2">Video Not Available</p>
                            <p className="text-sm text-gray-400">
                              HLS stream not available for {selectedVideo === 'video1' ? video1.system_metadata.filename : video2.system_metadata.filename}
                            </p>
                          </div>
                        </div>
                      )}
                      
                      {/* Current Differences Overlay */}
                      {getCurrentDifferences().length > 0 && (
                        <div className="absolute top-4 right-4 bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium z-10">
                          ⚠️ Difference Detected
                        </div>
                      )}
                    </div>
                  )}

                  {/* Video Controls */}
                  {showSideBySide ? (
                    <div className="flex items-center justify-center gap-4 py-4">
                      <Button 
                        onClick={() => {
                          const video1 = document.getElementById('video-player-1') as HTMLVideoElement;
                          const video2 = document.getElementById('video-player-2') as HTMLVideoElement;
                          if (video1 && video2) {
                            if (isPlaying) {
                              video1.pause();
                              video2.pause();
                            } else {
                              video1.play();
                              video2.play();
                            }
                          }
                        }}
                        className="bg-blue-600 hover:bg-blue-700 px-6 py-2"
                      >
                        {isPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                        {isPlaying ? 'Pause Both' : 'Play Both'}
                      </Button>
                      <span className="text-sm text-gray-300">
                        Synchronized playback
                      </span>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Button size="sm" onClick={handlePlayPause} className="bg-blue-600 hover:bg-blue-700">
                          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        </Button>
                        <span className="text-sm text-gray-300">
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
                          className="w-full h-3 bg-gray-700 rounded-lg appearance-none cursor-pointer relative z-10"
                          style={{
                            background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(currentTime / duration) * 100}%, #374151 ${(currentTime / duration) * 100}%, #374151 100%)`
                          }}
                        />
                        
                        {/* Difference Markers */}
                        <div className="absolute top-0 left-0 right-0 h-3 pointer-events-none">
                          {comparisonResult.differences.map((diff, index) => (
                            <div
                              key={index}
                              className="absolute h-3 bg-red-500 opacity-90 rounded-sm"
                              style={{
                                left: `${(diff.start_sec / duration) * 100}%`,
                                width: `${Math.max(((diff.end_sec - diff.start_sec) / duration) * 100, 1)}%`,
                                minWidth: '3px'
                              }}
                              title={`Difference: ${formatTime(diff.start_sec)} - ${formatTime(diff.end_sec)} (${diff.distance.toFixed(3)})`}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Differences List */}
          <div className="lg:col-span-1">
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Differences</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {comparisonResult.differences.length === 0 ? (
                    <p className="text-gray-400 text-sm">No significant differences found</p>
                  ) : (
                    comparisonResult.differences.map((diff, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          currentTime >= diff.start_sec && currentTime <= diff.end_sec
                            ? 'bg-red-900/50 border-red-600'
                            : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                        }`}
                        onClick={() => {
                          if (showSideBySide) {
                            const video1 = document.getElementById('video-player-1') as HTMLVideoElement;
                            const video2 = document.getElementById('video-player-2') as HTMLVideoElement;
                            if (video1) {
                              video1.currentTime = diff.start_sec;
                              setCurrentTime(diff.start_sec);
                            }
                            if (video2) {
                              video2.currentTime = diff.start_sec;
                            }
                          } else {
                            const video = document.getElementById('video-player') as HTMLVideoElement;
                            if (video) {
                              video.currentTime = diff.start_sec;
                              setCurrentTime(diff.start_sec);
                            }
                          }
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-white">
                            {formatTime(diff.start_sec)} - {formatTime(diff.end_sec)}
                          </span>
                          <Badge variant="destructive" className="text-xs bg-red-600">
                            {diff.distance.toFixed(3)}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-400 mt-1">
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