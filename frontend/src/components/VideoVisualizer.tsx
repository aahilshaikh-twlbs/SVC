'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, Video, Clock, Upload, Link, FileVideo, Trash2, Check } from 'lucide-react';
import { Video as VideoType, Index } from '@/types';
import { api } from '@/lib/api';
import { formatDuration, formatFileSize, formatDate } from '@/lib/utils';
import Image from 'next/image';

interface VideoVisualizerProps {
  selectedIndex: Index;
  selectedVideos: VideoType[];
  onVideoSelected: (video: VideoType) => void;
  onVideosLoaded: (videos: VideoType[]) => void;
}

export function VideoVisualizer({ selectedIndex, selectedVideos, onVideoSelected, onVideosLoaded }: VideoVisualizerProps) {
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadType, setUploadType] = useState<'file' | 'url'>('file');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadUrl, setUploadUrl] = useState('');
  const [fileInputKey, setFileInputKey] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [deletingVideo, setDeletingVideo] = useState<string | null>(null);

  const loadVideos = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await api.listVideos(selectedIndex.id);
      setVideos(data);
      onVideosLoaded(data);
    } catch {
      setError('Failed to load videos');
    } finally {
      setLoading(false);
    }
  }, [selectedIndex.id]);

  useEffect(() => {
    loadVideos();
  }, [loadVideos]);

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

      await api.uploadVideo(uploadData);
      
      // Reset form
      resetFileInput();
      setUploadUrl('');
      setShowUploadForm(false);
      
      // Reload videos after successful upload
      setTimeout(() => {
        loadVideos();
      }, 2000);
      
    } catch (err) {
      console.error('Upload error:', err);
      if (err instanceof Error) {
        setError(`Failed to upload video: ${err.message}`);
      } else {
        setError('Failed to upload video');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteVideo = async (videoId: string) => {
    try {
      await api.deleteVideo(selectedIndex.id, videoId);
      setVideos(prev => prev.filter(video => video.id !== videoId));
      setDeletingVideo(null);
    } catch {
      setError('Failed to delete video');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadFile(file);
      
      // Check video duration if it's a video file
      if (file.type.startsWith('video/')) {
        const video = document.createElement('video');
        video.preload = 'metadata';
        video.onloadedmetadata = () => {
          const durationInSeconds = video.duration;
          const maxDuration = 3600; // 60 minutes in seconds
          
          if (durationInSeconds > maxDuration) {
            setError(`Video is too long (${Math.round(durationInSeconds / 60)} minutes). Maximum allowed duration is 60 minutes.`);
          } else {
            setError(''); // Clear any previous errors
          }
        };
        video.src = URL.createObjectURL(file);
      }
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
            
                    {uploadType === 'url' && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-sm text-yellow-800">
                ⚠️ <strong>Supported URLs:</strong> Direct video file links (MP4, MOV, AVI, WebM) from cloud storage or web servers.
                <br />
                <strong>Not supported:</strong> YouTube, Vimeo, or streaming platform URLs.
                <br />
                For best results, use file upload instead.
              </p>
            </div>
          )}

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
                disabled={uploading || (uploadType === 'file' ? !uploadFile : !uploadUrl.trim()) || (uploadFile !== null && error !== '' && error.includes('too long'))}
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
        {videos.map((video) => {
          const isSelected = selectedVideos.some(selected => selected.id === video.id);
          return (
            <div
              key={video.id}
              className={`p-4 bg-white border rounded-lg shadow-sm hover:shadow-md transition-all ${
                isSelected 
                  ? 'border-blue-500 bg-blue-50 shadow-lg ring-2 ring-blue-200' 
                  : 'border-gray-200'
              }`}
            >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <h3 className="font-medium text-gray-900 truncate">
                  {video.system_metadata.filename}
                </h3>
                {isSelected && (
                  <div className="flex-shrink-0">
                    <Check className="w-4 h-4 text-blue-600" />
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {video.id.slice(0, 8)}...
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeletingVideo(video.id);
                  }}
                  className="p-1 h-6 w-6 text-red-500 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div 
              className="cursor-pointer"
              onClick={() => onVideoSelected(video)}
            >
              {video.hls?.thumbnail_urls?.[0] && (
                <div className="mb-3">
                  <Image
                    src={video.hls.thumbnail_urls[0]}
                    alt="Video thumbnail"
                    width={320}
                    height={128}
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
          </div>
        );
        })}
      </div>

      {/* Delete Confirmation Modal */}
      {deletingVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-medium mb-4">Delete Video</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete this video? This action cannot be undone.
            </p>
            <div className="flex gap-2">
              <Button
                onClick={() => handleDeleteVideo(deletingVideo)}
                variant="destructive"
              >
                Delete
              </Button>
              <Button
                onClick={() => setDeletingVideo(null)}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {videos.length === 0 && !loading && (
        <div className="text-center py-8 text-gray-500">
          <Video className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No videos in this index. Upload your first video to get started.</p>
        </div>
      )}
    </div>
  );
} 