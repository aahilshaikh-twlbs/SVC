'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, Database, Video as VideoIcon, Clock, Edit, Trash2, MoreVertical, Check } from 'lucide-react';
import { Index, Video } from '@/types';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/utils';

interface IndexVisualizerProps {
  apiKey: string;
  selectedVideos: Video[];
  onIndexSelected: (index: Index) => void;
  onRemoveVideo?: (videoId: string) => void;
  onRunComparison?: () => void;
  canRunComparison?: () => boolean;
}

export function IndexVisualizer({ apiKey, selectedVideos, onIndexSelected, onRemoveVideo, onRunComparison, canRunComparison }: IndexVisualizerProps) {
  const [indexes, setIndexes] = useState<Index[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newIndexName, setNewIndexName] = useState('');
  const [creating, setCreating] = useState(false);
  const [editingIndex, setEditingIndex] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [deletingIndex, setDeletingIndex] = useState<string | null>(null);

  useEffect(() => {
    loadIndexes();
  }, [apiKey]);

  const loadIndexes = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await api.listIndexes();
      setIndexes(data);
    } catch (err) {
      setError('Failed to load indexes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateIndex = async () => {
    if (!newIndexName.trim()) return;

    setCreating(true);
    try {
      const newIndex = await api.createIndex({ name: newIndexName });
      setIndexes(prev => [newIndex, ...prev]);
      setNewIndexName('');
      setShowCreateForm(false);
    } catch (err) {
      setError('Failed to create index');
    } finally {
      setCreating(false);
    }
  };

  const handleRenameIndex = async (indexId: string) => {
    if (!editingName.trim()) return;

    try {
      const updatedIndex = await api.renameIndex(indexId, editingName);
      setIndexes(prev => prev.map(index => 
        index.id === indexId ? updatedIndex : index
      ));
      setEditingIndex(null);
      setEditingName('');
    } catch (err) {
      setError('Failed to rename index');
    }
  };

  const handleDeleteIndex = async (indexId: string) => {
    try {
      await api.deleteIndex(indexId);
      setIndexes(prev => prev.filter(index => index.id !== indexId));
      setDeletingIndex(null);
    } catch (err) {
      setError('Failed to delete index');
    }
  };

  const startEditing = (index: Index) => {
    setEditingIndex(index.id);
    setEditingName(index.name);
  };

  const getSelectedVideosFromIndex = (indexId: string) => {
    return selectedVideos.filter(video => {
      // We need to check if this video belongs to this index
      // For now, we'll show all selected videos, but ideally we'd track which index each video belongs to
      return true; // This will show all selected videos for now
    });
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
      {/* Selected Videos Banner */}
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
                      onClick={() => onRemoveVideo?.(video.id)}
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
                onClick={() => onRunComparison?.()}
                disabled={!canRunComparison?.()}
                className={`${
                  canRunComparison?.() 
                    ? 'bg-blue-600 hover:bg-blue-700' 
                    : 'bg-gray-400 cursor-not-allowed'
                }`}
              >
                {canRunComparison?.() ? 'Run Comparison' : 'Videos must be same length'}
              </Button>
            )}
          </div>
          {selectedVideos.length === 2 && !canRunComparison?.() && (
            <div className="mt-2 text-xs text-orange-700">
              ⚠️ Both videos must have the exact same duration for comparison
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Indexes</h2>
        </div>
        <Button
          onClick={() => setShowCreateForm(true)}
          size="sm"
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Index
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {showCreateForm && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
          <h3 className="font-medium mb-3">Create New Index</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={newIndexName}
              onChange={(e) => setNewIndexName(e.target.value)}
              placeholder="Enter index name"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Button
              onClick={handleCreateIndex}
              disabled={creating || !newIndexName.trim()}
              size="sm"
            >
              {creating ? 'Creating...' : 'Create'}
            </Button>
            <Button
              onClick={() => {
                setShowCreateForm(false);
                setNewIndexName('');
              }}
              variant="outline"
              size="sm"
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {indexes.map((index) => (
          <div
            key={index.id}
            className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-medium text-gray-900 truncate">{index.name}</h3>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {index.id.slice(0, 8)}...
                </span>
                <div className="relative">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Toggle edit mode
                      if (editingIndex === index.id) {
                        setEditingIndex(null);
                        setEditingName('');
                      } else {
                        startEditing(index);
                      }
                    }}
                    className="p-1 h-6 w-6"
                  >
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {editingIndex === index.id ? (
              <div className="mb-3 space-y-2">
                <input
                  type="text"
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                />
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    onClick={() => handleRenameIndex(index.id)}
                    className="text-xs"
                  >
                    Save
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setEditingIndex(null);
                      setEditingName('');
                    }}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => {
                      setDeletingIndex(index.id);
                      setEditingIndex(null);
                    }}
                    className="text-xs"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ) : (
              <div 
                className="cursor-pointer"
                onClick={() => onIndexSelected(index)}
              >
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <VideoIcon className="w-4 h-4" />
                    <span>{index.video_count} videos</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>{Math.round(index.total_duration / 60)} min total</span>
                  </div>

                  <div className="text-xs text-gray-500">
                    Created {formatDate(index.created_at)}
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="text-xs text-gray-500">
                    Models: {index.models.map(m => m.name).join(', ')}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Delete Confirmation Modal */}
      {deletingIndex && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-medium mb-4">Delete Index</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete this index? This action cannot be undone.
            </p>
            <div className="flex gap-2">
              <Button
                onClick={() => handleDeleteIndex(deletingIndex)}
                variant="destructive"
              >
                Delete
              </Button>
              <Button
                onClick={() => setDeletingIndex(null)}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {indexes.length === 0 && !loading && (
        <div className="text-center py-8 text-gray-500">
          <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No indexes found. Create your first index to get started.</p>
        </div>
      )}
    </div>
  );
} 