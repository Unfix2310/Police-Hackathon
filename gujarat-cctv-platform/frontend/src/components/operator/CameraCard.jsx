import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Video, ExternalLink, Copy, Check, Loader2 } from 'lucide-react';
import Hls from 'hls.js';

export default function CameraCard({ camera, loadDelay = 0 }) {
  const videoRef = useRef(null);
  const cardRef = useRef(null);
  const hlsRef = useRef(null);
  const retryCountRef = useRef(0);
  const maxRetries = 2;
  const [copied, setCopied] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isFocused, setIsFocused] = useState(false);
  const [ready, setReady] = useState(loadDelay === 0);
  const streamUrl = camera.hls_url || camera.web_url;

  // Staggered mount: wait for loadDelay before activating HLS
  useEffect(() => {
    if (loadDelay <= 0) { setReady(true); return; }
    const t = setTimeout(() => setReady(true), loadDelay);
    return () => clearTimeout(t);
  }, [loadDelay]);

  useEffect(() => {
    const handleFocusCamera = (e) => {
      if (e.detail?.camId === camera.cam_id) {
        setIsFocused(true);
        if (cardRef.current) {
          cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        setTimeout(() => setIsFocused(false), 3000);
      }
    };
    window.addEventListener('focus-camera', handleFocusCamera);
    return () => window.removeEventListener('focus-camera', handleFocusCamera);
  }, [camera.cam_id]);

  useEffect(() => {
    if (!ready) return;
    let hlsInstance = null;
    const video = videoRef.current;
    if (!video || !streamUrl) return;

    setHasError(false);
    setIsLoading(true);

    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Safari native HLS
      video.src = streamUrl;
      video.addEventListener('loadeddata', () => setIsLoading(false), { once: true });
      video.play().catch(() => {});
    } else if (Hls && Hls.isSupported()) {
      hlsInstance = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 30,
        manifestLoadingTimeOut: 8000,
        manifestLoadingMaxRetry: 1,
        levelLoadingTimeOut: 8000,
        fragLoadingTimeOut: 10000,
      });
      hlsRef.current = hlsInstance;
      hlsInstance.loadSource(streamUrl);
      hlsInstance.attachMedia(video);

      hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {});
      });

      hlsInstance.on(Hls.Events.FRAG_LOADED, () => {
        setIsLoading(false);
      });

      hlsInstance.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal) {
          // Fatal error — try recovery once, then show error state
          if (retryCountRef.current < maxRetries) {
            retryCountRef.current += 1;
            if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
              hlsInstance.startLoad();
            } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
              hlsInstance.recoverMediaError();
            } else {
              setHasError(true);
              setIsLoading(false);
            }
          } else {
            hlsInstance.destroy();
            setHasError(true);
            setIsLoading(false);
          }
        }
      });
    }

    return () => {
      retryCountRef.current = 0;
      if (hlsInstance) {
        hlsInstance.destroy();
        hlsRef.current = null;
      }
    };
  }, [streamUrl, ready]);

  const copyCamId = () => {
    const textToCopy = camera.cam_id || streamUrl || '';
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      ref={cardRef}
      id={`camera-card-${camera.cam_id}`}
      className={`bg-slate-900 border rounded-lg aspect-video flex flex-col relative overflow-hidden group shadow-lg transition-all duration-300 ${
        isFocused ? 'ring-4 ring-blue-500 border-blue-400 scale-[1.02]' : 'border-slate-800'
      }`}
    >
      <div className="flex-1 w-full h-full bg-black relative flex items-center justify-center">
        {streamUrl && !hasError ? (
          <>
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              playsInline
              muted
              autoPlay
              onError={() => { setHasError(true); setIsLoading(false); }}
            />
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/60">
                <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center text-slate-500 gap-1 text-xs">
            <Video className="w-8 h-8 opacity-40" />
            <span>Feed Standby / Authentication Required</span>
          </div>
        )}

        {/* Overlay Information */}
        <div className="absolute top-2 left-2 bg-black/80 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded font-medium border border-white/15 flex items-center gap-1.5 shadow-md">
          <span className="font-bold text-blue-400">
            {camera.cam_id ? (camera.cam_id.toUpperCase().replace('CAM', 'CAM-')) : 'CAM'}
          </span>
          {camera.location && (
            <>
              <span className="text-slate-400">•</span>
              <span className="truncate max-w-[130px] text-slate-200" title={camera.location}>
                {camera.location}
              </span>
            </>
          )}
        </div>
        
        <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-red-950/80 border border-red-500/30 text-red-400 text-[10px] font-bold px-2 py-0.5 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping"></span>
          LIVE
        </div>

        {/* Hover action bar */}
        <div className="absolute bottom-0 left-0 right-0 p-2.5 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-end text-xs text-white">
          <div className="flex items-center gap-1.5">
            <button
              onClick={copyCamId}
              title="Copy Camera ID"
              className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-600/50 flex items-center gap-1 text-[11px]"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'ID'}</span>
            </button>
            {camera.hls_url && (
              <a
                href={camera.hls_url}
                target="_blank"
                rel="noreferrer"
                title="Open HLS in new tab"
                className="p-1 bg-blue-600/80 hover:bg-blue-600 rounded text-white"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

