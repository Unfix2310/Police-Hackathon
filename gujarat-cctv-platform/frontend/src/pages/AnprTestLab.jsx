import React, { useState, useRef, useEffect } from 'react';
import { 
  Upload, FileVideo, Play, Pause, RefreshCw, CheckCircle, 
  AlertTriangle, XCircle, Eye, ScanLine, Clock, Tag, ChevronLeft, ChevronRight
} from 'lucide-react';
import api from '../services/api';

export default function AnprTestLab() {
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [maxFrames, setMaxFrames] = useState(20);
  const [analyzing, setAnalyzing] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [elapsedSec, setElapsedSec] = useState(0);
  const [results, setResults] = useState(null);
  const [filter, setFilter] = useState('ALL'); // 'ALL', 'READABLE', 'UNREADABLE'
  const [selectedFrameIdx, setSelectedFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const [engineStatus, setEngineStatus] = useState(null);

  const checkStatus = () => {
    api.get('/anpr/status')
      .then((res) => setEngineStatus(res.data))
      .catch((err) => {
        console.warn('Failed to query ANPR engine status:', err);
        setEngineStatus({ available: false, error: true, message: 'Backend unreachable' });
      });
  };

  useEffect(() => {
    checkStatus();
    // Auto-retry polling every 5s if backend is not yet ready or offline
    const interval = setInterval(() => {
      api.get('/anpr/status')
        .then((res) => {
          setEngineStatus(res.data);
          if (res.data?.available) clearInterval(interval);
        })
        .catch(() => {});
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Handle local file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
      setVideoFile(file);
      const url = URL.createObjectURL(file);
      setVideoUrl(url);
      setResults(null);
      setSelectedFrameIdx(0);
    }
  };

  // Run backend ANPR analysis at 2 FPS
  const handleAnalyze = async () => {
    if (!videoFile) return;
    setAnalyzing(true);
    setElapsedSec(0);
    setProgressMsg('Uploading video and processing frames with YOLOv8 + Tesseract at 2 FPS...');

    const timer = setInterval(() => {
      setElapsedSec((prev) => prev + 1);
    }, 1000);

    const formData = new FormData();
    formData.append('file', videoFile);
    formData.append('max_frames', maxFrames);
    formData.append('target_fps', 2.0);

    try {
      const response = await api.post('/anpr/test-video', formData, {
        headers: { 'Content-Type': undefined },
        timeout: 600000, // 10 minutes timeout
      });

      if (response.data?.status === 'success') {
        setResults(response.data);
        setSelectedFrameIdx(0);
        if (response.data.metadata?.frames_analyzed === 0) {
          alert('Warning: No frames could be extracted. The video codec may not be supported by OpenCV. Please re-encode as H.264 MP4.');
        }
      } else {
        alert('Analysis failed: ' + (response.data?.detail || response.data?.status || 'Unknown error'));
      }
    } catch (err) {
      console.error('ANPR video analysis failed:', err);
      alert('Analysis failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      clearInterval(timer);
      setAnalyzing(false);
      setProgressMsg('');
    }
  };

  // Synchronize canvas bounding boxes whenever video seeks or plays
  const renderCanvasOverlay = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !results?.frames) return;

    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 360;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const currentTime = video.currentTime;
    // Find closest analyzed frame within 0.6 seconds (since sampling is 2 FPS = 0.5s intervals)
    const closestFrame = results.frames.reduce((prev, curr) => {
      return Math.abs(curr.timestamp_sec - currentTime) < Math.abs(prev.timestamp_sec - currentTime)
        ? curr
        : prev;
    }, results.frames[0]);

    if (!closestFrame || Math.abs(closestFrame.timestamp_sec - currentTime) > 0.6) {
      return;
    }

    const detections = closestFrame.detections || [];
    detections.forEach((det) => {
      // 1. Draw vehicle bounding box (Cyan / Blue)
      const [vx1, vy1, vx2, vy2] = det.vehicle_bbox || [];
      if (vx1 !== undefined) {
        ctx.lineWidth = 3;
        ctx.strokeStyle = '#00e5ff';
        ctx.strokeRect(vx1, vy1, vx2 - vx1, vy2 - vy1);

        // Vehicle label
        ctx.fillStyle = '#00e5ff';
        ctx.font = 'bold 13px sans-serif';
        const vehLabel = `${det.vehicle_class} ${(det.vehicle_confidence * 100).toFixed(0)}%`;
        ctx.fillRect(vx1, Math.max(0, vy1 - 20), ctx.measureText(vehLabel).width + 8, 20);
        ctx.fillStyle = '#000000';
        ctx.fillText(vehLabel, vx1 + 4, Math.max(14, vy1 - 5));
      }

      // 2. Draw plate bounding box (Yellow / Green)
      if (det.plate_bbox) {
        const [px1, py1, px2, py2] = det.plate_bbox;
        if (px2 > px1 && py2 > py1) {
          const isReadable = det.status === 'READABLE';
          ctx.lineWidth = 2.5;
          ctx.strokeStyle = isReadable ? '#00ff66' : '#ffb703';
          ctx.strokeRect(px1, py1, px2 - px1, py2 - py1);

          // Plate badge
          const plateText = isReadable ? det.plate_text : `[${det.status}]`;
          ctx.fillStyle = isReadable ? '#00ff66' : '#ffb703';
          ctx.font = 'bold 12px monospace';
          const badgeWidth = ctx.measureText(plateText).width + 10;
          ctx.fillRect(px1, Math.min(canvas.height - 18, py2 + 2), badgeWidth, 18);
          ctx.fillStyle = '#000000';
          ctx.fillText(plateText, px1 + 5, Math.min(canvas.height - 4, py2 + 15));
        }
      }
    });
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onTimeUpdate = () => renderCanvasOverlay();
    video.addEventListener('timeupdate', onTimeUpdate);
    video.addEventListener('seeked', onTimeUpdate);
    video.addEventListener('play', () => setIsPlaying(true));
    video.addEventListener('pause', () => setIsPlaying(false));
    video.addEventListener('ended', () => setIsPlaying(false));

    return () => {
      video.removeEventListener('timeupdate', onTimeUpdate);
      video.removeEventListener('seeked', onTimeUpdate);
      video.removeEventListener('play', () => setIsPlaying(true));
      video.removeEventListener('pause', () => setIsPlaying(false));
      video.removeEventListener('ended', () => setIsPlaying(false));
    };
  }, [results]);

  // Render overlay immediately when results arrive
  useEffect(() => {
    if (results) {
      // Small delay to let video element settle
      setTimeout(() => renderCanvasOverlay(), 100);
    }
  }, [results]);

  // Jump to specific frame
  const seekToTimestamp = (sec, idx) => {
    if (videoRef.current) {
      videoRef.current.currentTime = sec;
      videoRef.current.pause();
      setIsPlaying(false);
      setSelectedFrameIdx(idx);
    }
  };

  // Step frame by frame
  const stepFrame = (direction) => {
    if (!results?.frames?.length) return;
    let nextIdx = selectedFrameIdx + direction;
    if (nextIdx < 0) nextIdx = 0;
    if (nextIdx >= results.frames.length) nextIdx = results.frames.length - 1;
    const target = results.frames[nextIdx];
    seekToTimestamp(target.timestamp_sec, nextIdx);
  };

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  };

  // Collect all vehicle detections across all analyzed frames for the gallery
  const allDetections = [];
  if (results?.frames) {
    results.frames.forEach((f, fIdx) => {
      (f.detections || []).forEach((d, dIdx) => {
        allDetections.push({
          ...d,
          frame_index: f.frame_index,
          analyzed_idx: fIdx,
          timestamp_sec: f.timestamp_sec,
          timestamp_formatted: f.timestamp_formatted,
          key: `${fIdx}-${dIdx}`,
        });
      });
    });
  }

  const filteredDetections = allDetections.filter((d) => {
    if (filter === 'READABLE') return d.status === 'READABLE';
    if (filter === 'UNREADABLE') return d.status === 'UNREADABLE';
    return true;
  });

  const meta = results?.metadata || {};
  const totalPlates = (meta.readable_plates || 0) + (meta.unreadable_plates || 0);
  const readabilityPct = totalPlates > 0
    ? Math.round((meta.readable_plates / totalPlates) * 100)
    : 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-50 text-police-blue rounded-md">
              <ScanLine className="w-6 h-6 text-police-blue" />
            </span>
            <div>
              <h1 className="text-xl font-bold text-police-blue flex items-center gap-2">
                ANPR Benchmarking & Test Lab
                <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-mono font-medium">
                  ISOLATED TEST MODE
                </span>
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Upload your local CCTV .mp4 footage to benchmark the baseline ANPR engine at 2 FPS. Live streams and database are untouched.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right text-xs">
            <div className="flex items-center justify-end gap-1.5 mb-0.5">
              <span className="text-gray-500">AI Device:</span>{' '}
              <span className={`font-mono font-medium px-1.5 py-0.2 rounded text-[11px] ${
                engineStatus?.device === 'mps' || engineStatus?.device === 'cuda'
                  ? 'bg-emerald-100 text-emerald-800 font-semibold'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {engineStatus?.device_name || 'Auto-Detecting...'}
              </span>
            </div>
            <span className="text-gray-500">OCR Engine:</span>{' '}
            <span className="font-semibold text-gray-800">Tesseract OCR</span>
            {engineStatus ? (
              engineStatus.available ? (
                <div className="text-emerald-600 font-medium">● Engine Online (Ready)</div>
              ) : engineStatus.error ? (
                <button
                  onClick={checkStatus}
                  className="text-amber-600 hover:text-amber-700 font-medium flex items-center justify-end gap-1 cursor-pointer"
                  title="Click to recheck backend connection"
                >
                  <RefreshCw className="w-3 h-3 animate-spin inline" /> Backend Connecting (Retry)
                </button>
              ) : (
                <div className="text-rose-600 font-medium flex items-center justify-end gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 inline" /> Binary Missing (Rebuild Docker)
                </div>
              )
            ) : (
              <div className="text-gray-400 font-medium">Checking engine status...</div>
            )}
          </div>
        </div>
      </div>

      {/* Warning only if Tesseract binary is genuinely missing from container */}
      {engineStatus && !engineStatus.available && !engineStatus.error && (
        <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs text-rose-800">
            <strong className="font-semibold text-rose-900">Tesseract OCR binary not detected in the running backend container!</strong>
            <p className="mt-1 text-rose-700">
              The backend container cannot decode license plate characters until rebuilt with <code>tesseract-ocr</code>. Run:
            </p>
            <code className="block bg-rose-100 p-2 rounded mt-1.5 font-mono text-rose-900 select-all">
              docker compose build backend && docker compose up -d backend
            </code>
          </div>
        </div>
      )}

      {/* Upload & Run Controls */}
      <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 items-end">
          <div className="lg:col-span-2">
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Select CCTV Video File (.mp4 / .mov)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="file"
                accept="video/mp4,video/mov,video/quicktime,video/avi"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-police-blue file:text-white
                  hover:file:bg-blue-900 cursor-pointer border border-gray-200 rounded-md p-1"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Sample Range (at 2 FPS)
            </label>
            <select
              value={maxFrames}
              onChange={(e) => setMaxFrames(Number(e.target.value))}
              disabled={analyzing}
              className="w-full border border-gray-300 rounded-md p-2 text-sm bg-white"
            >
              <option value={10}>10 frames (~5 seconds) [Ultra Fast Test]</option>
              <option value={20}>20 frames (~10 seconds) [Recommended Benchmark]</option>
              <option value={30}>30 frames (~15 seconds)</option>
              <option value={60}>60 frames (~30 seconds)</option>
            </select>
          </div>

          <div>
            <button
              onClick={handleAnalyze}
              disabled={!videoFile || analyzing}
              className="w-full bg-police-blue text-white py-2 px-4 rounded-md font-medium text-sm flex items-center justify-center gap-2 hover:bg-blue-900 disabled:opacity-50 transition-colors shadow-sm"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Analyzing at 2 FPS...
                </>
              ) : (
                <>
                  <ScanLine className="w-4 h-4" />
                  Run ANPR Benchmark
                </>
              )}
            </button>
          </div>
        </div>

        {analyzing && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
              <span>{progressMsg}</span>
            </div>
            <span className="font-mono font-semibold bg-blue-100 px-2 py-0.5 rounded text-blue-900">
              Elapsed: {elapsedSec}s
            </span>
          </div>
        )}
      </div>

      {/* Analysis Metrics Row (shown after results) */}
      {results && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <div className="text-xs text-gray-500">Frames Analyzed</div>
            <div className="text-2xl font-bold text-gray-800 mt-1">{meta.frames_analyzed}</div>
            <div className="text-[11px] text-gray-400 mt-0.5">at 2.0 FPS downsample</div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <div className="text-xs text-gray-500">Vehicles Detected</div>
            <div className="text-2xl font-bold text-police-blue mt-1">{meta.total_vehicles_detected}</div>
            <div className="text-[11px] text-gray-400 mt-0.5">YOLOv8 vehicle crops</div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <div className="text-xs text-emerald-600 font-medium">Readable Plates</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">{meta.readable_plates}</div>
            <div className="text-[11px] text-emerald-700 mt-0.5">Validated plate strings</div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <div className="text-xs text-amber-600 font-medium">Unreadable / Low Res</div>
            <div className="text-2xl font-bold text-amber-600 mt-1">{meta.unreadable_plates}</div>
            <div className="text-[11px] text-amber-700 mt-0.5">Below confidence floor</div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm col-span-2 md:col-span-1">
            <div className="text-xs text-gray-500">Readability Rate</div>
            <div className="text-2xl font-bold text-gray-800 mt-1">{readabilityPct}%</div>
            <div className="w-full bg-gray-200 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div 
                className={`h-full ${readabilityPct > 50 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                style={{ width: `${readabilityPct}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area: Video Player & Detections List */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Synchronized Video Player with Canvas Overlay */}
        <div className="lg:col-span-7 bg-white p-5 rounded-lg shadow-sm border border-gray-200 flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2">
              <FileVideo className="w-4 h-4 text-police-blue" />
              Synchronized Video & Bounding Box View
            </h2>
            {results && (
              <span className="text-xs text-gray-500 font-mono">
                Frame: {selectedFrameIdx + 1} / {results.frames?.length || 0}
              </span>
            )}
          </div>

          <div className="relative bg-black rounded-lg overflow-hidden flex items-center justify-center min-h-[300px]">
            {videoUrl ? (
              <>
                <video
                  ref={videoRef}
                  src={videoUrl}
                  className="w-full h-auto max-h-[500px] object-contain"
                  controls={false}
                  playsInline
                />
                <canvas
                  ref={canvasRef}
                  className="absolute inset-0 w-full h-full pointer-events-none"
                />
              </>
            ) : (
              <div className="text-center p-8 text-gray-400">
                <Upload className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Please select a local .mp4 video file to view playback</p>
              </div>
            )}
          </div>

          {/* Video Playback & Step Controls */}
          {videoUrl && (
            <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={togglePlay}
                  className="p-2 bg-police-blue text-white rounded hover:bg-blue-900 transition-colors"
                  title={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => stepFrame(-1)}
                  disabled={!results}
                  className="p-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-40 transition-colors"
                  title="Previous Analyzed Frame"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => stepFrame(1)}
                  disabled={!results}
                  className="p-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-40 transition-colors"
                  title="Next Analyzed Frame"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              <div className="text-xs text-gray-500 font-mono">
                Legend:{' '}
                <span className="text-[#00c8e0] font-semibold">■ Vehicle BBox</span>{' '}
                <span className="text-emerald-600 font-semibold ml-2">■ Readable Plate</span>{' '}
                <span className="text-amber-500 font-semibold ml-2">■ Unreadable</span>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Plate Detection & Evidence Gallery */}
        <div className="lg:col-span-5 bg-white p-5 rounded-lg shadow-sm border border-gray-200 flex flex-col h-[650px]">
          <div className="flex justify-between items-center pb-3 border-b border-gray-200">
            <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2">
              <Tag className="w-4 h-4 text-police-blue" />
              Detected Plates & Evidence Crops ({filteredDetections.length})
            </h2>

            {/* Filter Tabs */}
            <div className="flex bg-gray-100 p-0.5 rounded text-xs">
              <button
                onClick={() => setFilter('ALL')}
                className={`px-2 py-1 rounded transition-colors ${filter === 'ALL' ? 'bg-white font-bold shadow-xs text-police-blue' : 'text-gray-600'}`}
              >
                All
              </button>
              <button
                onClick={() => setFilter('READABLE')}
                className={`px-2 py-1 rounded transition-colors ${filter === 'READABLE' ? 'bg-white font-bold shadow-xs text-emerald-700' : 'text-gray-600'}`}
              >
                Readable
              </button>
              <button
                onClick={() => setFilter('UNREADABLE')}
                className={`px-2 py-1 rounded transition-colors ${filter === 'UNREADABLE' ? 'bg-white font-bold shadow-xs text-amber-700' : 'text-gray-600'}`}
              >
                Unreadable
              </button>
            </div>
          </div>

          {/* Scrollable Gallery */}
          <div className="flex-1 overflow-y-auto space-y-3 mt-3 pr-1">
            {!results ? (
              <div className="text-center py-16 text-gray-400 text-xs">
                Run the benchmark to inspect detected vehicle plates, crops, and confidence scores.
              </div>
            ) : filteredDetections.length === 0 ? (
              <div className="text-center py-16 text-gray-400 text-xs">
                No detections matching the "{filter}" filter.
              </div>
            ) : (
              filteredDetections.map((det) => {
                const isReadable = det.status === 'READABLE';
                return (
                  <div
                    key={det.key}
                    onClick={() => seekToTimestamp(det.timestamp_sec, det.analyzed_idx)}
                    className={`p-3 rounded-lg border transition-all cursor-pointer hover:shadow-md ${
                      isReadable
                        ? 'border-emerald-200 bg-emerald-50/30 hover:border-emerald-400'
                        : 'border-gray-200 bg-gray-50/50 hover:border-amber-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      {/* Left: Plate Crop Image */}
                      <div className="w-28 h-12 bg-black rounded border border-gray-300 flex items-center justify-center overflow-hidden shrink-0">
                        {det.plate_crop_base64 ? (
                          <img
                            src={det.plate_crop_base64}
                            alt="Plate crop"
                            className="w-full h-full object-contain"
                          />
                        ) : (
                          <span className="text-[10px] text-gray-400">No Crop</span>
                        )}
                      </div>

                      {/* Middle: Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-mono text-xs font-bold px-2 py-0.5 rounded border ${
                              isReadable
                                ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                                : 'bg-amber-100 text-amber-800 border-amber-300'
                            }`}
                          >
                            {det.plate_text}
                          </span>
                          <span className="text-[11px] text-gray-500 font-medium">
                            {det.vehicle_class}
                          </span>
                        </div>

                        {det.raw_text && det.raw_text !== det.plate_text && (
                          <div className="text-[10px] text-gray-400 font-mono mt-1 truncate">
                            Raw OCR: "{det.raw_text}"
                          </div>
                        )}

                        <div className="flex items-center gap-3 mt-1.5 text-[11px] text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {det.timestamp_formatted}
                          </span>
                          <span>
                            Conf: <strong>{(det.plate_confidence * 100).toFixed(0)}%</strong>
                          </span>
                        </div>
                      </div>

                      {/* Right: Seek Button */}
                      <button
                        className="p-1.5 text-gray-400 hover:text-police-blue hover:bg-white rounded border border-transparent hover:border-gray-200 transition-colors"
                        title="Seek to this moment"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
