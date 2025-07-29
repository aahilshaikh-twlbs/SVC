'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, Database, Video, Clock } from 'lucide-react';
import { Index } from '@/types';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/utils';

interface IndexVisualizerProps {
  apiKey: string;
  onIndexSelected: (index: Index) => void;
}

export function IndexVisualizer({ apiKey, onIndexSelected }: IndexVisualizerProps) {
  const [indexes, setIndexes] = useState<Index[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newIndexName, setNewIndexName] = useState('');
  const [creating, setCreating] = useState(false);

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
            onClick={() => onIndexSelected(index)}
            className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-medium text-gray-900 truncate">{index.name}</h3>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {index.id.slice(0, 8)}...
              </span>
            </div>

            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4" />
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
        ))}
      </div>

      {indexes.length === 0 && !loading && (
        <div className="text-center py-8 text-gray-500">
          <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No indexes found. Create your first index to get started.</p>
        </div>
      )}
    </div>
  );
} 