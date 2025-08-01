'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Key, Eye, EyeOff } from 'lucide-react';
import { api } from '@/lib/api';

interface ApiKeyConfigProps {
  onKeyValidated: (key: string) => void;
}

export function ApiKeyConfig({ onKeyValidated }: ApiKeyConfigProps) {
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
    <div className="w-full max-w-md mx-auto p-6 bg-white rounded-lg shadow-sm border border-[#D3D1CF]">
      <div className="flex items-center gap-2 mb-4">
        <Key className="w-5 h-5 text-[#0066FF]" />
        <h2 className="text-xl font-semibold text-[#1D1C1B]">Configure API Key</h2>
      </div>
      
      <div className="space-y-4">
        <div className="relative">
          <input
            type={showKey ? 'text' : 'password'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Enter your TwelveLabs API key"
            className="w-full px-3 py-2 border border-[#D3D1CF] rounded-md focus:outline-none focus:ring-2 focus:ring-[#0066FF] focus:border-transparent bg-white text-[#1D1C1B]"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#9B9896] hover:text-[#1D1C1B]"
          >
            {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>

        {error && (
          <p className="text-[#EF4444] text-sm">{error}</p>
        )}

        <Button
          onClick={handleValidateKey}
          disabled={isValidating}
          className="w-full bg-[#0066FF] hover:bg-[#0052CC] text-white disabled:bg-[#D3D1CF] disabled:text-[#9B9896]"
        >
          {isValidating ? 'Validating...' : 'Validate & Continue'}
        </Button>
      </div>
    </div>
  );
} 