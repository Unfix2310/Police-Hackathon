import React, { useEffect, useRef, useState } from 'react';
import { Video, ExternalLink, Copy, Check, MapPin } from 'lucide-react';

export default function CameraCard({ camera }) {
  const videoRef = useRef(null);
  const [copied, setCopied] = useState(false);
  const [hasError, setHasError] = useState(false);
  const streamUrl = camera.hls_url || camera.web_url;

  useEffect(() => {
    let hlsInstance = null;
    const video = videoRef.current;
    if (!video || !streamUrl) return;

    setHasError(false);

    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = streamUrl;
      video.play().catch(() => {});
    } else {
      // Dynamic Hls.js loader for Chrome/Firefox/Edge
      const initHls = () => {
        if (window.Hls && window.Hls.isSupported()) {
          hlsInstance = new window.Hls({
            enableWorker: true,
            lowLatencyMode: true,
            backBufferLength: 30,
          });
          hlsInstance.loadSource(streamUrl);
          hlsInstance.attachMedia(video);
          hlsInstance.on(window.Hls.Events.MANIFEST_PARSED, () => {
            video.play().catch(() => {});
          });
          hlsInstance.on(window.Hls.Events.ERROR, () => {
            // Non-fatal or CDN session limitation
          });
        }
      };

      if (window.Hls) {
        initHls();
      } else {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest';
        script.async = true;
        script.onload = initHls;
        document.head.appendChild(script);
      }
    }

    return () => {
      if (hlsInstance) {
        hlsInstance.destroy();
      }
    };
  }, [streamUrl]);

  const copyRtsp = () => {
    if (camera.rtsp_url) {
      navigator.clipboard.writeText(camera.rtsp_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg aspect-video flex flex-col relative overflow-hidden group shadow-lg">
      <div className="flex-1 w-full h-full bg-black relative flex items-center justify-center">
        {streamUrl && !hasError ? (
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            playsInline
            muted
            autoPlay
            onError={() => setHasError(true)}
          />
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
        <div className="absolute bottom-0 left-0 right-0 p-2.5 bg-gradient-to-t from-black/95 via-black/75 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-between text-xs text-white">
          <span className="text-slate-200 text-[11px] font-medium truncate max-w-[62%] flex items-center gap-1.5" title={`${camera.location || camera.display_name} (${camera.district || 'Gujarat'})`}>
            <MapPin className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate">
              {camera.location || camera.display_name || 'Gujarat Police Grid'}
              {camera.district ? ` • ${camera.district}` : ''}
            </span>
          </span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={copyRtsp}
              title="Copy RTSP inference endpoint (TCP)"
              className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-600/50 flex items-center gap-1 text-[11px]"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'RTSP'}</span>
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

