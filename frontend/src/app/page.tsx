'use client';

import { useState } from 'react';
import { ApiKeyConfig } from '@/components/ApiKeyConfig';
import { IndexVisualizer } from '@/components/IndexVisualizer';
import { VideoVisualizer } from '@/components/VideoVisualizer';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Settings } from 'lucide-react';
import { Index, Video } from '@/types';

export default function LandingPage() {
  const [apiKey, setApiKey] = useState('');
  const [selectedIndex, setSelectedIndex] = useState<Index | null>(null);
  const [selectedVideos, setSelectedVideos] = useState<Video[]>([]);
  const [showApiKeyConfig, setShowApiKeyConfig] = useState(false);

  const handleKeyValidated = (key: string) => {
    setApiKey(key);
    setSelectedIndex(null);
    setSelectedVideos([]);
  };

  const handleIndexSelected = (index: Index) => {
    setSelectedIndex(index);
    setSelectedVideos([]);
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

  const handleBackToIndexes = () => {
    setSelectedIndex(null);
    setSelectedVideos([]);
  };

  const handleRunComparison = () => {
    if (selectedVideos.length === 2) {
      // TODO: Navigate to analysis page with selected videos
      console.log('Running comparison with:', selectedVideos);
    }
  };

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
              <h1 className="text-xl font-semibold text-gray-900">SVC - Semantic Video Comparison</h1>
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
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                        >
                          {index + 1}. {video.system_metadata.filename}
                        </span>
                      ))}
                    </div>
                  </div>
                  {selectedVideos.length === 2 && (
                    <Button
                      onClick={handleRunComparison}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      Run Comparison
                    </Button>
                  )}
                </div>
              </div>
            )}

            <VideoVisualizer
              selectedIndex={selectedIndex}
              onVideoSelected={handleVideoSelected}
            />
          </div>
        ) : (
          <IndexVisualizer
            apiKey={apiKey}
            onIndexSelected={handleIndexSelected}
          />
        )}
      </main>
    </div>
  );
}
