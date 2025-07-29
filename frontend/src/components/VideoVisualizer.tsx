'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, Video, Clock, Upload, Link, FileVideo } from 'lucide-react';
import { Video as VideoType, Index } from '@/types';
import { api } from '@/lib/api';
import { formatDuration, formatFileSize, formatDate } from '@/lib/utils';

interface VideoVisualizerProps {
  selectedIndex: Index;
  onVideoSelected: (video: VideoType) => void;
}

export function VideoVisualizer({ selectedIndex, onVideoSelected }: VideoVisualizerProps) {
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadType, setUploadType] = useState<'file' | 'url'>('file');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadUrl, setUploadUrl] = useState('');
  const [fileInputKey, setFileInputKey] = useState(0);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadVideos();
  }, [selectedIndex.id]);

  const loadVideos = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await api.listVideos(selectedIndex.id);
      setVideos(data);
    } catch (err) {
      setError('Failed to load videos');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (uploadType === 'file' && !uploadFile) {
      setError('Please select a file');
      return;
    }
    if (uploadType === 'url' && !uploadUrl.trim()) {
      setError('Please enter a URL');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const uploadData = {
        index_id: selectedIndex.id,
        file: uploadType === 'file' ? uploadFile || undefined : undefined,
        url: uploadType === 'url' ? uploadUrl : undefined,
      };

      const result = await api.uploadVideo(uploadData);
      
      // Reset form
      resetFileInput();
      setUploadUrl('');
      setShowUploadForm(false);
      
      // Reload videos after successful upload
      setTimeout(() => {
        loadVideos();
      }, 2000);
      
    } catch (err) {
      setError('Failed to upload video');
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadFile(file);
    }
  };

  const resetFileInput = () => {
    setFileInputKey(prev => prev + 1);
    setUploadFile(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Video className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">
            Videos in "{selectedIndex.name}"
          </h2>
        </div>
        <Button
          onClick={() => setShowUploadForm(true)}
          size="sm"
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Upload Video
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {showUploadForm && (
        <div className="p-6 bg-gray-50 border border-gray-200 rounded-md">
          <h3 className="font-medium mb-4">Upload New Video</h3>
          
          <div className="space-y-4">
            <div className="flex gap-2">
              <Button
                variant={uploadType === 'file' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setUploadType('file')}
                className="flex items-center gap-2"
              >
                <FileVideo className="w-4 h-4" />
                File Upload
              </Button>
              <Button
                variant={uploadType === 'url' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setUploadType('url')}
                className="flex items-center gap-2"
              >
                <Link className="w-4 h-4" />
                YouTube URL
              </Button>
            </div>

            {uploadType === 'file' ? (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Select Video File
                </label>
                <input
                  key={fileInputKey}
                  type="file"
                  accept="video/*"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                {uploadFile && (
                  <p className="text-sm text-gray-600">
                    Selected: {uploadFile.name} ({formatFileSize(uploadFile.size)})
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  YouTube URL
                </label>
                <input
                  type="url"
                  value={uploadUrl || ''}
                  onChange={(e) => setUploadUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            <div className="flex gap-2">
              <Button
                onClick={handleUpload}
                disabled={uploading || (uploadType === 'file' ? !uploadFile : !uploadUrl.trim())}
                className="flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                {uploading ? 'Uploading...' : 'Upload'}
              </Button>
              <Button
                onClick={() => {
                  setShowUploadForm(false);
                  resetFileInput();
                  setUploadUrl('');
                  setError('');
                }}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {videos.map((video) => (
          <div
            key={video.id}
            onClick={() => onVideoSelected(video)}
            className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-medium text-gray-900 truncate">
                {video.system_metadata.filename}
              </h3>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {video.id.slice(0, 8)}...
              </span>
            </div>

            {video.hls?.thumbnail_urls?.[0] && (
              <div className="mb-3">
                <img
                  src={video.hls.thumbnail_urls[0]}
                  alt="Video thumbnail"
                  className="w-full h-32 object-cover rounded-md"
                />
              </div>
            )}

            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>{formatDuration(video.system_metadata.duration)}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4" />
                <span>{video.system_metadata.width}×{video.system_metadata.height}</span>
              </div>

              <div className="text-xs text-gray-500">
                {formatFileSize(video.system_metadata.size)}
              </div>

              <div className="text-xs text-gray-500">
                Uploaded {formatDate(video.created_at)}
              </div>
            </div>

            {video.source && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="text-xs text-gray-500">
                  Source: {video.source.type} - {video.source.name}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {videos.length === 0 && !loading && (
        <div className="text-center py-8 text-gray-500">
          <Video className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No videos in this index. Upload your first video to get started.</p>
        </div>
      )}
    </div>
  );
} 