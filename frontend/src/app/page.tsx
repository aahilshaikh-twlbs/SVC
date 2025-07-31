'use client';

import { useState, useEffect } from 'react';
import { ApiKeyConfig } from '@/components/ApiKeyConfig';
import { IndexVisualizer } from '@/components/IndexVisualizer';
import { VideoVisualizer } from '@/components/VideoVisualizer';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Settings } from 'lucide-react';
import { Index, Video } from '@/types';
import { api } from '@/lib/api';

export default function LandingPage() {
  const [apiKey, setApiKey] = useState('');
  const [selectedIndex, setSelectedIndex] = useState<Index | null>(null);
  const [selectedVideos, setSelectedVideos] = useState<Video[]>([]);
  const [showApiKeyConfig, setShowApiKeyConfig] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [allVideos, setAllVideos] = useState<Video[]>([]);

  // Check for stored API key on component mount
  useEffect(() => {
    const checkStoredApiKey = async () => {
      try {
        // Check localStorage for stored API key
        const storedKey = localStorage.getItem('sage_api_key');
        if (storedKey) {
          // Validate the stored key
          const result = await api.validateApiKey(storedKey);
          if (result.isValid) {
            setApiKey(storedKey);
            setShowApiKeyConfig(false);
          } else {
            // Invalid key, remove it
            localStorage.removeItem('sage_api_key');
            setShowApiKeyConfig(true);
          }
        } else {
          // Check backend for stored key
          const result = await api.getStoredApiKey();
          if (result.has_stored_key) {
            // Backend has a key but frontend doesn't, show config
            setShowApiKeyConfig(true);
          }
        }
      } catch (error) {
        console.error('Error checking stored API key:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkStoredApiKey();
  }, []);

  const handleKeyValidated = (key: string) => {
    setApiKey(key);
    // Store the API key in localStorage for persistence
    localStorage.setItem('sage_api_key', key);
    setSelectedIndex(null);
    setSelectedVideos([]);
    setAllVideos([]);
    setShowApiKeyConfig(false);
  };

  const handleIndexSelected = (index: Index) => {
    setSelectedIndex(index);
    // Don't clear selected videos - keep them persistent across indexes
  };

  const handleVideoSelected = (video: Video) => {
    setSelectedVideos(prev => {
      const isSelected = prev.find(v => v.id === video.id);
      if (isSelected) {
        return prev.filter(v => v.id !== video.id);
      } else {
        if (prev.length >= 2) {
          return [prev[1], video];
        } else {
          return [...prev, video];
        }
      }
    });
  };

  const handleRemoveVideo = (videoId: string) => {
    setSelectedVideos(prev => prev.filter(v => v.id !== videoId));
  };

  const handleVideosLoaded = (videos: Video[]) => {
    setAllVideos(prev => {
      // Remove videos from the current index and add new ones
      const filtered = prev.filter(v => !videos.some(newV => newV.id === v.id));
      return [...filtered, ...videos];
    });
  };

  const canRunComparison = () => {
    if (selectedVideos.length !== 2) return false;
    const [video1, video2] = selectedVideos;
    return video1.system_metadata.duration === video2.system_metadata.duration;
  };

  const handleBackToIndexes = () => {
    setSelectedIndex(null);
    // Don't clear selected videos - keep them persistent
  };

  const handleRunComparison = () => {
    if (selectedVideos.length === 2) {
      // Redirect to analysis page with video IDs
      const video1Id = selectedVideos[0].id;
      const video2Id = selectedVideos[1].id;
      const indexId = selectedIndex?.id;
      
      if (!indexId) {
        alert('No index selected');
        return;
      }
      
      const analysisUrl = `/analysis?video1=${video1Id}&video2=${video2Id}&index=${indexId}`;
      window.location.href = analysisUrl;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!apiKey) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <ApiKeyConfig onKeyValidated={handleKeyValidated} />
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
              <h1 className="text-xl font-semibold text-gray-900">SAGE</h1>
              {selectedIndex && (
                <Button
                  onClick={handleBackToIndexes}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Indexes
                </Button>
              )}
            </div>
            
            <Button
              onClick={() => setShowApiKeyConfig(true)}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              <Settings className="w-4 h-4" />
              Change API Key
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {showApiKeyConfig ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <ApiKeyConfig onKeyValidated={handleKeyValidated} />
          </div>
        ) : selectedIndex ? (
          <div className="space-y-8">
            {/* Video Selection Status */}
            {selectedVideos.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-medium text-blue-900">
                      Selected Videos: {selectedVideos.length}/2
                    </span>
                    <div className="flex gap-2">
                      {selectedVideos.map((video, index) => (
                        <span
                          key={video.id}
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded flex items-center gap-1"
                        >
                          <span>{index + 1}. {video.system_metadata.filename} ({Math.round(video.system_metadata.duration / 60)}min)</span>
                                              <button
                      onClick={() => handleRemoveVideo(video.id)}
                      className="ml-1 text-blue-600 hover:text-blue-800 text-sm font-bold"
                      title="Remove from selection"
                    >
                      ×
                    </button>
                        </span>
                      ))}
                    </div>
                  </div>
                  {selectedVideos.length === 2 && (
                    <Button
                      onClick={handleRunComparison}
                      disabled={!canRunComparison()}
                      className={`${
                        canRunComparison() 
                          ? 'bg-blue-600 hover:bg-blue-700' 
                          : 'bg-gray-400 cursor-not-allowed'
                      }`}
                    >
                      {canRunComparison() ? 'Run Comparison' : 'Videos must be same length'}
                    </Button>
                  )}
                </div>
                                    {selectedVideos.length === 2 && !canRunComparison() && (
                      <div className="mt-2 text-xs text-orange-700">
                        ⚠️ Both videos must have the exact same duration for comparison
                      </div>
                    )}
              </div>
            )}

            <VideoVisualizer
              selectedIndex={selectedIndex}
              selectedVideos={selectedVideos}
              allVideos={allVideos}
              apiKey={apiKey}
              onVideoSelected={handleVideoSelected}
              onVideosLoaded={handleVideosLoaded}
              onRemoveVideo={handleRemoveVideo}
            />
          </div>
        ) : (
          <IndexVisualizer
            apiKey={apiKey}
            selectedVideos={selectedVideos}
            onIndexSelected={handleIndexSelected}
            onRemoveVideo={handleRemoveVideo}
            onRunComparison={handleRunComparison}
            canRunComparison={canRunComparison}
          />
        )}
      </main>
    </div>
  );
}
