'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Key, Eye, EyeOff } from 'lucide-react';
import { api } from '@/lib/api';

interface ApiKeyConfigProps {
  onKeyValidated: (key: string) => void;
  onCancel?: () => void;
  showCancel?: boolean;
}

export function ApiKeyConfig({ onKeyValidated, onCancel, showCancel = false }: ApiKeyConfigProps) {
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState('');

  const handleValidateKey = async () => {
    if (!apiKey.trim()) {
      setError('Please enter an API key');
      return;
    }

    setIsValidating(true);
    setError('');

    try {
      const result = await api.validateApiKey(apiKey);
      if (result.isValid) {
        onKeyValidated(apiKey);
      } else {
        setError('Invalid API key');
      }
    } catch {
      setError('Failed to validate API key. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="w-full max-w-lg mx-auto p-10 bg-white rounded-lg shadow-lg border border-[#D3D1CF]">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Key className="w-6 h-6 text-[#0066FF]" />
          <h2 className="text-2xl font-semibold text-[#1D1C1B]">Configure API Key</h2>
        </div>
        {showCancel && onCancel && (
          <button
            onClick={onCancel}
            className="text-[#9B9896] hover:text-[#1D1C1B] text-sm font-medium"
          >
            Cancel
          </button>
        )}
      </div>
      
      <div className="space-y-8">
        <div>
          <label className="block text-sm font-medium text-[#1D1C1B] mb-3">
            TwelveLabs API Key
          </label>
          <div className="relative">
            <input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your TwelveLabs API key"
              className="w-full px-4 py-4 text-base border border-[#D3D1CF] rounded-md focus:outline-none focus:ring-2 focus:ring-[#0066FF] focus:border-transparent bg-white text-[#1D1C1B] pr-12"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#9B9896] hover:text-[#1D1C1B] p-1"
            >
              {showKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {error && (
          <p className="text-[#EF4444] text-sm bg-[#FEE2E2] p-3 rounded-md">{error}</p>
        )}

        <Button
          onClick={handleValidateKey}
          disabled={isValidating}
          className="w-full bg-[#0066FF] hover:bg-[#0052CC] text-white disabled:bg-[#D3D1CF] disabled:text-[#9B9896] py-4 text-base font-medium"
        >
          {isValidating ? 'Validating...' : 'Validate & Continue'}
        </Button>
        
        <p className="text-sm text-[#9B9896] text-center mt-6">
          Your API key will be stored locally in your browser
        </p>
      </div>
    </div>
  );
} 