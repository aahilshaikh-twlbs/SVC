'use client';

import { useState, useEffect } from 'react';
import { ApiKeyConfig } from '@/components/ApiKeyConfig';
import { Button } from '@/components/ui/button';
import { Settings, Upload, Video, Loader2, X } from 'lucide-react';
import { api } from '@/lib/api';

interface LocalVideo {
  id: string;
  file: File;
  thumbnail: string;
  embeddings?: any;
}

export default function LandingPage() {
  const [apiKey, setApiKey] = useState('');
  const [showApiKeyConfig, setShowApiKeyConfig] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadedVideos, setUploadedVideos] = useState<LocalVideo[]>([]);
  const [isGeneratingEmbeddings, setIsGeneratingEmbeddings] = useState(false);

  // Check for stored API key on component mount
  useEffect(() => {
    const checkStoredApiKey = async () => {
      try {
        const storedKey = localStorage.getItem('sage_api_key');
        if (storedKey) {
          const result = await api.validateApiKey(storedKey);
          if (result.isValid) {
            setApiKey(storedKey);
            setShowApiKeyConfig(false);
          } else {
            localStorage.removeItem('sage_api_key');
            setShowApiKeyConfig(true);
          }
        } else {
          setShowApiKeyConfig(true);
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
    localStorage.setItem('sage_api_key', key);
    setShowApiKeyConfig(false);
  };

  const generateThumbnail = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const video = document.createElement('video');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;
      
      video.onloadedmetadata = () => {
        video.currentTime = 1; // Seek to 1 second
      };
      
      video.onseeked = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL());
      };
      
      video.src = URL.createObjectURL(file);
    });
  };

  const handleVideoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const file = files[0];
    if (uploadedVideos.length >= 2) {
      alert('Maximum 2 videos allowed');
      return;
    }
    
    const thumbnail = await generateThumbnail(file);
    const newVideo: LocalVideo = {
      id: `video-${Date.now()}`,
      file,
      thumbnail
    };
    
    setUploadedVideos(prev => [...prev, newVideo]);
  };

  const removeVideo = (videoId: string) => {
    setUploadedVideos(prev => prev.filter(v => v.id !== videoId));
  };

  const canRunComparison = () => {
    return uploadedVideos.length === 2 && !isGeneratingEmbeddings;
  };

  const handleRunComparison = async () => {
    if (uploadedVideos.length !== 2) return;
    
    setIsGeneratingEmbeddings(true);
    
    try {
      // Upload videos and generate embeddings
      const formData1 = new FormData();
      formData1.append('file', uploadedVideos[0].file);
      
      const formData2 = new FormData();
      formData2.append('file', uploadedVideos[1].file);
      
      // Upload and generate embeddings for both videos
      const [result1, result2] = await Promise.all([
        api.uploadAndGenerateEmbeddings(formData1),
        api.uploadAndGenerateEmbeddings(formData2)
      ]);
      
      // Store video data in session storage for analysis page
      sessionStorage.setItem('video1_data', JSON.stringify({
        id: uploadedVideos[0].id,
        filename: uploadedVideos[0].file.name,
        embedding_id: result1.embedding_id,
        video_id: result1.video_id,
        duration: result1.duration
      }));
      
      sessionStorage.setItem('video2_data', JSON.stringify({
        id: uploadedVideos[1].id,
        filename: uploadedVideos[1].file.name,
        embedding_id: result2.embedding_id,
        video_id: result2.video_id,
        duration: result2.duration
      }));
      
      // Navigate to analysis page
      window.location.href = '/analysis';
    } catch (error) {
      console.error('Error generating embeddings:', error);
      alert('Failed to generate embeddings. Please try again.');
    } finally {
      setIsGeneratingEmbeddings(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F4F3F3] flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0066FF]"></div>
      </div>
    );
  }

  if (!apiKey || showApiKeyConfig) {
    return (
      <div className="min-h-screen bg-[#F4F3F3] flex items-center justify-center p-4">
        <ApiKeyConfig onKeyValidated={handleKeyValidated} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4F3F3]">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-[#D3D1CF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-semibold text-[#1D1C1B]">SAGE</h1>
            
            <Button
              onClick={() => setShowApiKeyConfig(true)}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 border-[#D3D1CF] hover:bg-[#F4F3F3]"
            >
              <Settings className="w-4 h-4" />
              Change API Key
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Upload Section */}
          <div className="text-center">
            <h2 className="text-2xl font-bold text-[#1D1C1B] mb-4">
              Upload Videos for Comparison
            </h2>
            <p className="text-[#9B9896] mb-8">
              Upload two local videos to compare their content using TwelveLabs embeddings
            </p>
          </div>

          {/* Video Upload Area */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {uploadedVideos.map((video, index) => (
              <div key={video.id} className="relative">
                <div className="bg-white rounded-lg shadow-sm border border-[#D3D1CF] p-4">
                  <div className="relative">
                    <img
                      src={video.thumbnail}
                      alt={`Video ${index + 1}`}
                      className="w-full h-48 object-cover rounded"
                    />
                    <button
                      onClick={() => removeVideo(video.id)}
                      className="absolute top-2 right-2 bg-[#EF4444] text-white rounded-full p-1 hover:bg-[#DC2626]"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="mt-2 text-sm font-medium truncate text-[#1D1C1B]">{video.file.name}</p>
                  <p className="text-xs text-[#9B9896]">
                    Size: {(video.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
            ))}

            {uploadedVideos.length < 2 && (
              <div className="bg-white rounded-lg shadow-sm border-2 border-dashed border-[#D3D1CF] p-8 flex flex-col items-center justify-center">
                <Video className="w-12 h-12 text-[#9B9896] mb-4" />
                <label className="cursor-pointer">
                  <span className="text-[#0066FF] hover:text-[#0052CC] font-medium">
                    Choose video
                  </span>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleVideoUpload}
                    className="hidden"
                  />
                </label>
                <p className="text-sm text-[#9B9896] mt-2">or drag and drop</p>
              </div>
            )}
          </div>

          {/* Comparison Button */}
          <div className="flex justify-center">
            <Button
              onClick={handleRunComparison}
              disabled={!canRunComparison()}
              className="px-8 py-3 bg-[#0066FF] hover:bg-[#0052CC] text-white disabled:bg-[#D3D1CF] disabled:text-[#9B9896]"
            >
              {isGeneratingEmbeddings ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating Embeddings...
                </>
              ) : (
                'Compare Videos'
              )}
            </Button>
          </div>

          {/* Status Messages */}
          {uploadedVideos.length === 1 && (
            <p className="text-center text-[#9B9896]">
              Please upload one more video to enable comparison
            </p>
          )}
        </div>
      </main>
    </div>
  );
}