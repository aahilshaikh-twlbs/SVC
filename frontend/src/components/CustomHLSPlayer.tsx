import React, { useRef, useState, useEffect, useCallback } from 'react';
import Hls from 'hls.js';

interface CustomHLSPlayerProps {
  src: string;
  className?: string;
  autoPlay?: boolean;
  controls?: boolean;
  onError?: (error: any) => void;
  onLoadedData?: () => void;
  onTimeUpdate?: (currentTime: number) => void;
  uniqueKey?: string; // For forcing remount when switching videos
}

// Helper function to get user-friendly error message
const getVideoErrorMessage = (code: number): string => {
  switch (code) {
    case 1:
      return 'Video loading aborted';
    case 2:
      return 'Network error - please check your connection';
    case 3:
      return 'Video decoding failed - format may be unsupported';
    case 4:
      return 'Video source is not supported or unavailable';
    default:
      return 'Unknown video playback error';
  }
};

const CustomHLSPlayer: React.FC<CustomHLSPlayerProps> = ({
  src,
  className = "w-full h-full",
  autoPlay = false,
  controls = true,
  onError,
  onLoadedData,
  onTimeUpdate,
  uniqueKey = ''
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup function
  const cleanupHls = useCallback(() => {
    if (hlsRef.current) {
      console.log('🧹 Cleaning up HLS instance');
      hlsRef.current.destroy();
      hlsRef.current = null;
    }
    
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
      loadingTimeoutRef.current = null;
    }
    
    if (videoRef.current) {
      const video = videoRef.current;
      video.pause();
      video.removeAttribute('src');
      video.load();
      
      // Remove all event listeners
      video.onloadeddata = null;
      video.onerror = null;
      video.ontimeupdate = null;
      video.onplay = null;
      video.onpause = null;
      video.onended = null;
    }
  }, []);

  // Forward declare loadVideo function
  const loadVideoRef = useRef<(() => void) | null>(null);

  // Enhanced error handler
  const handleError = useCallback((type: 'loading' | 'video' | 'fatal', error: any) => {
    console.error(`🎬 Video ${type} error:`, error);
    
    // If we've already tried or there isn't one, show the error
    let errorMessage = '';
    if (type === 'loading') {
      errorMessage = error?.message || 'Failed to load video';
    } else if (type === 'video') {
      const videoError = videoRef.current?.error;
      errorMessage = videoError ? getVideoErrorMessage(videoError.code) : 'Video playback error';
    } else {
      errorMessage = 'Fatal video playback error';
      if (error?.type === Hls.ErrorTypes.NETWORK_ERROR) {
        errorMessage = 'Network error - please check your connection';
      } else if (error?.type === Hls.ErrorTypes.MEDIA_ERROR) {
        errorMessage = 'Media format error - video may be corrupted';
      }
    }

    setError(errorMessage);
    setLoading(false);
    onError?.(error);
  }, [onError]);

  // Load video function
  const loadVideo = useCallback(async () => {
    if (!src || !videoRef.current) return;

    console.log('🎬 Loading video:', src);
    setLoading(true);
    setError(null);

    // Set a loading timeout of 30 seconds
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }
    loadingTimeoutRef.current = setTimeout(() => {
      if (loading) {
        console.error('⏱️ Video loading timeout after 30 seconds');
        handleError('loading', new Error('Video loading timeout - please try refreshing the page'));
      }
    }, 30000);

    // Clean up previous instance
    cleanupHls();

    const video = videoRef.current;
    
    try {
      // Test URL accessibility for external URLs
      try {
        console.log('🎬 Testing URL accessibility:', src);
        const testResponse = await fetch(src, { 
          method: 'HEAD',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });
        if (!testResponse.ok) {
          throw new Error(`HTTP ${testResponse.status}: ${testResponse.statusText}`);
        }
        console.log('✅ URL is accessible:', testResponse.status);
      } catch (urlError: any) {
        console.error('❌ URL not accessible:', urlError);
        if (retryCount < 3) {
          console.log(`🔄 Retrying (${retryCount + 1}/3)...`);
          setRetryCount(prev => prev + 1);
          setTimeout(() => loadVideo(), 1000);
          return;
        }
        handleError('loading', urlError);
        return;
      }

      // Check if this is likely an MP4 file
      const isDirectVideo = src.endsWith('.mp4') || 
                          src.includes('/api/video/hls/') || 
                          src.includes('/api/investigation/');

      if (isDirectVideo) {
        console.log('🎬 Using direct video playback');
        
        const loadTimeout = setTimeout(() => {
          console.warn('🎬 Direct video loading timeout');
          handleError('loading', new Error('Video loading timeout'));
        }, 15000);

        const handleSuccess = () => {
          clearTimeout(loadTimeout);
          if (loadingTimeoutRef.current) {
            clearTimeout(loadingTimeoutRef.current);
            loadingTimeoutRef.current = null;
          }
          setLoading(false);
          onLoadedData?.();
        };

        video.addEventListener('loadeddata', handleSuccess, { once: true });
        video.addEventListener('canplay', handleSuccess, { once: true });
        video.addEventListener('error', (e) => {
          clearTimeout(loadTimeout);
          handleError('video', e);
        }, { once: true });

        video.src = src;
        video.load();
      } else {
        // Try HLS playback
        if (!Hls.isSupported()) {
          console.log('⚠️ HLS not supported, falling back to native playback');
          video.src = src;
          return;
        }

        console.log('🎬 Initializing HLS.js');
        const hls = new Hls({
          debug: false,
          enableWorker: true,
          lowLatencyMode: true,
          backBufferLength: 90,
          maxBufferLength: 30,
          maxMaxBufferLength: 600,
          maxBufferSize: 60 * 1000 * 1000,
          maxBufferHole: 0.5,
          highBufferWatchdogPeriod: 2,
          nudgeOffset: 0.2,
          nudgeMaxRetry: 5,
          // Add more resilient network settings
          fragLoadingTimeOut: 20000,
          manifestLoadingTimeOut: 20000,
          levelLoadingTimeOut: 20000,
          fragLoadingMaxRetry: 6,
          manifestLoadingMaxRetry: 6,
          levelLoadingMaxRetry: 6,
        });

        hlsRef.current = hls;

        hls.on(Hls.Events.MEDIA_ATTACHED, () => {
          console.log('🎬 HLS media attached');
        });

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          console.log('🎬 HLS manifest parsed');
          if (loadingTimeoutRef.current) {
            clearTimeout(loadingTimeoutRef.current);
            loadingTimeoutRef.current = null;
          }
          setLoading(false);
          onLoadedData?.();
        });

        hls.on(Hls.Events.ERROR, (_, data) => {
          console.error('🎬 HLS.js error:', data);
          
          if (data.fatal) {
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                if (retryCount < 3) {
                  console.log(`🔄 Network error, retrying (${retryCount + 1}/3)...`);
                  hls.startLoad();
                  setRetryCount(prev => prev + 1);
                } else {
                  handleError('fatal', data);
                }
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                console.log('🎬 Media error, attempting to recover...');
                hls.recoverMediaError();
                break;
              default:
                handleError('fatal', data);
                break;
            }
          }
        });

        hls.loadSource(src);
        hls.attachMedia(video);
      }

      // Set up video event listeners
      video.addEventListener('timeupdate', () => {
        setCurrentTime(video.currentTime);
        onTimeUpdate?.(video.currentTime);
      });

    } catch (err) {
      console.error('🎬 Failed to load video:', err);
      handleError('loading', err);
    }
  }, [src, retryCount, onLoadedData, onTimeUpdate, cleanupHls, handleError, loading]);

  // Store loadVideo in ref so handleError can access it
  loadVideoRef.current = loadVideo;

  // Load video when src changes
  useEffect(() => {
    if (src) {
      console.log('🎬 CustomHLSPlayer src changed:', src);
      setRetryCount(0);
      loadVideo();
    }
    return () => {
      cleanupHls();
    };
  }, [src, uniqueKey, loadVideo, cleanupHls]);

  // Render error state
  if (error) {
    return (
      <div className={`${className} flex items-center justify-center bg-gray-800 text-white rounded-lg`}>
        <div className="text-center p-6 max-w-md">
          <div className="text-red-500 mb-3 text-2xl">⚠️</div>
          <h3 className="text-base font-medium text-white mb-2">
            Video Error
          </h3>
          <p className="text-sm text-gray-300 mb-3">
            {error}
          </p>
          {retryCount > 0 && (
            <p className="text-xs text-gray-400 mb-2">
              Retry attempt {retryCount}/3
            </p>
          )}
          <div className="flex flex-col gap-2">
            <button
              onClick={() => {
                setError(null);
                setRetryCount(0);
                loadVideo();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => {
                // Force reload the video with a new key
                setError(null);
                setRetryCount(0);
                setTimeout(loadVideo, 500);
              }}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm hover:bg-gray-600 transition-colors"
            >
              Reset Player
            </button>
          </div>
          <p className="mt-4 text-xs text-gray-400">
            If the issue persists, try refreshing the page or contact support.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-800 text-white rounded-lg z-20">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin"></div>
            <p className="text-sm text-gray-300">
              Loading video...
            </p>
            {retryCount > 0 && (
              <p className="text-xs text-gray-400">Retry {retryCount}/3</p>
            )}
          </div>
        </div>
      )}
      
      {/* Video element */}
      <video
        ref={videoRef}
        className={className}
        controls={controls}
        playsInline
        muted={autoPlay}
        preload="metadata"
        crossOrigin="anonymous"
        style={{ backgroundColor: 'black' }}
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
};

export default CustomHLSPlayer; 