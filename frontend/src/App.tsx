import React, { useState, useEffect, useRef } from 'react';
import {
  UploadIcon, SparklesIcon,
  AlertCircleIcon, XCircleIcon, DownloadIcon, CpuIcon,
  HistoryIcon, TrashIcon, SplitIcon, ZoomInIcon, ZoomOutIcon, CropIcon,
  PauseIcon, PlayIcon, InfoIcon
} from './components/Icons';
import {
  fetchCapabilities, fetchModels, fetchRecentJobs, uploadImage, createJob,
  cancelJob, pauseJob, resumeJob, deleteJob, subscribeJobEvents, getDownloadUrl, getPreviewUrl,
  analyzeImage, fetchProjectVersions, getResolutionPlan, upscaleFromVersion,
  updateVersionDecision, uploadImagesBatch, createJobsBatch,
  clearQueue, downloadBatchZip
} from './services/api';
import type {
  SystemCapabilities, ModelInfo, ImageUploadResult, JobStatus, AnalysisResult,
  VersionItem, ResolutionPlan
} from './services/api';

// Task Category definitions per Part K3
interface TaskCategory {
  id: string;
  name: string;
  desc: string;
  icon: string;
  recommendedModel: string;
  recommendedMode: string;
}

const TASK_CATEGORIES: TaskCategory[] = [
  {
    id: 'photo',
    name: 'Improve a Photo',
    desc: 'Enhance clarity, textural sharpness, and detail in photos.',
    icon: '📸',
    recommendedModel: 'realesrgan-x4plus',
    recommendedMode: 'upscale'
  },
  {
    id: 'restore',
    name: 'Restore an Old Photo',
    desc: 'Suppress JPEG artifacts, film grain, and noise degradation.',
    icon: '🕰️',
    recommendedModel: 'realesrgan-x4plus',
    recommendedMode: 'restore_upscale'
  },
  {
    id: 'anime',
    name: 'Anime & Cartoons',
    desc: 'Preserve flat color fills, clean cel shading, and clean lines.',
    icon: '🎨',
    recommendedModel: 'realesrgan-x4plus-anime',
    recommendedMode: 'upscale'
  },
  {
    id: 'lineart',
    name: 'Manga & Line Art',
    desc: 'Deep ink borders, paper whitening, and screentone dot protection.',
    icon: '✒️',
    recommendedModel: 'realesrgan-x4plus-anime',
    recommendedMode: 'upscale'
  },
  {
    id: 'compressed',
    name: 'Repair Compressed Image',
    desc: 'Remove JPEG compression ringing and 8x8 block boundaries.',
    icon: '📦',
    recommendedModel: 'realesrgan-x4plus',
    recommendedMode: 'restore_upscale'
  },
  {
    id: 'transparent',
    name: 'Transparent Art & Icons',
    desc: 'Preserve alpha channel transparency without dark edge bleed.',
    icon: '💎',
    recommendedModel: 'realesrgan-x4plus',
    recommendedMode: 'upscale'
  }
];

// Plain-Language Quality Presets per Part K4
interface QualityPreset {
  id: string;
  name: string;
  desc: string;
  category?: 'photo' | 'anime' | 'general';
  scale: number;
}

const QUALITY_PRESETS: QualityPreset[] = [
  { id: 'manga_crisp', name: 'Manga & Inking', desc: 'Specialized for B&W manga panels. Deep black ink reinforcement, white paper cleanup, and screentone dot protection.', category: 'anime', scale: 4 },
  { id: 'anime_clean', name: 'Anime & Cel Art', desc: 'Modern digital anime & cartoons. Preserves flat color fills, sharp vector-like outlines, and smooth shading.', category: 'anime', scale: 4 },
  { id: 'vintage_cel', name: 'Vintage Cel', desc: 'Classic 80s/90s retro anime. Gentle analog film noise suppression while preserving authentic pencil and ink outlines.', category: 'anime', scale: 4 },
  { id: 'natural', name: 'Natural (Photo)', desc: 'Photographic balance. Classical denoise disabled, low-weight blend preserves natural skin grain.', category: 'photo', scale: 4 },
  { id: 'faithful', name: 'Faithful (Photo)', desc: 'Strict source adherence. Pure neural reconstruction with zero pre-filtering.', category: 'photo', scale: 4 },
  { id: 'more_detail', name: 'More Detail', desc: 'Deep high-frequency neural reconstruction. Notice: Increases invented-detail tendency.', category: 'photo', scale: 4 },
  { id: 'smooth_clean', name: 'Smooth & Clean', desc: 'Aggressive artifact and noise cleanup. Warning: natural grain/fine skin texture will be softened.', category: 'photo', scale: 4 },
  { id: 'artwork', name: 'Artwork (All)', desc: 'General anime, manga, and digital illustrations. No photographic denoising.', category: 'anime', scale: 4 },
  { id: 'custom', name: 'Custom', desc: 'Manual technical overrides and custom parameters.', category: 'general', scale: 4 }
];

export default function App() {
  const [capabilities, setCapabilities] = useState<SystemCapabilities | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [currentImage, setCurrentImage] = useState<ImageUploadResult | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);

  // Workflow State (Part K2 & K3)
  const [selectedTask, setSelectedTask] = useState<string>('photo');
  const [selectedPreset, setSelectedPreset] = useState<string>('faithful');
  const [resolutionTarget, setResolutionTarget] = useState<'2x' | '4x' | '4k' | '8k' | 'custom'>('4x');
  const [customWidth, setCustomWidth] = useState<number>(3840);
  const [customHeight, setCustomHeight] = useState<number>(2160);

  // Advanced / Expert Mode (Part K7 & K8)
  const [expertModeOpen, setExpertModeOpen] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<string>('auto');
  const [outputFormat, setOutputFormat] = useState<string>('png');
  const [quality, setQuality] = useState<number>(95);

  // Version Graph State (Part E & K9)
  const [projectVersions, setProjectVersions] = useState<VersionItem[]>([]);
  const [activeVersionId, setActiveVersionId] = useState<string | null>(null);

  // Resolution Plan (Part F)
  const [currentPlan, setCurrentPlan] = useState<ResolutionPlan | null>(null);
  const [planLoading, setPlanLoading] = useState<boolean>(false);
  const [selectedPlanChoice, setSelectedPlanChoice] = useState<'A' | 'B' | 'C' | null>(null);

  // Analysis & Job Execution
  const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [currentJob, setCurrentJob] = useState<JobStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Viewer & Comparison Modes
  const [viewMode, setViewMode] = useState<'slider' | 'side-by-side' | 'original' | 'result'>('slider');
  const [sliderPos, setSliderPos] = useState<number>(50);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [zoom, setZoom] = useState<number>(1.0);

  // History Drawer
  const [historyOpen, setHistoryOpen] = useState<boolean>(false);
  const [jobsList, setJobsList] = useState<JobStatus[]>([]);

  const sliderContainerRef = useRef<HTMLDivElement | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    fetchCapabilities().then(setCapabilities).catch(console.error);
    fetchModels().then(setModels).catch(console.error);
    loadRecentJobs();
    return () => {
      if (unsubscribeRef.current) unsubscribeRef.current();
    };
  }, []);

  const loadRecentJobs = () => {
    fetchRecentJobs(20).then(setJobsList).catch(console.error);
  };

  // Batch Queue State
  const [batchOpen, setBatchOpen] = useState<boolean>(false);
  const [batchImages, setBatchImages] = useState<ImageUploadResult[]>([]);
  const [batchJobs, setBatchJobs] = useState<JobStatus[]>([]);
  const [batchScale, setBatchScale] = useState<number>(4);
  const [batchPreset, setBatchPreset] = useState<string>('manga_crisp');
  const [isBatchProcessing, setIsBatchProcessing] = useState<boolean>(false);
  const [batchLoading, setBatchLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!batchOpen || batchJobs.length === 0) return;
    const interval = setInterval(async () => {
      try {
        const recent = await fetchRecentJobs(50);
        const updatedBatch = batchJobs.map((bj) => {
          const match = recent.find((r) => r.job_id === bj.job_id);
          return match || bj;
        });
        setBatchJobs(updatedBatch);
        setJobsList(recent);

        const allDone = updatedBatch.every((j) => ['completed', 'failed', 'cancelled'].includes(j.status));
        if (allDone && isBatchProcessing) {
          setIsBatchProcessing(false);
        }
      } catch (err) {
        console.error('Error polling batch queue', err);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [batchOpen, batchJobs, isBatchProcessing]);

  const loadProjectVersions = async (projectId: string) => {
    try {
      const vers = await fetchProjectVersions(projectId);
      setProjectVersions(vers);
      if (vers.length > 0 && !activeVersionId) {
        setActiveVersionId(vers[vers.length - 1].id);
      }
    } catch (e) {
      console.error('Failed to load project versions', e);
    }
  };

  // Compute Target Dimensions based on Resolution Studio selection
  const computeTargetDimensions = (): { width: number; height: number } => {
    if (!currentImage) return { width: 0, height: 0 };
    const srcW = currentImage.width;
    const srcH = currentImage.height;
    const aspect = srcW / Math.max(1, srcH);

    if (resolutionTarget === '2x') {
      return { width: srcW * 2, height: srcH * 2 };
    } else if (resolutionTarget === '4x') {
      return { width: srcW * 4, height: srcH * 4 };
    } else if (resolutionTarget === '4k') {
      // 4K UHD: 3840 wide (or 2160 tall if portrait)
      if (aspect >= 1.0) {
        return { width: 3840, height: Math.round(3840 / aspect) };
      } else {
        return { width: Math.round(3840 * aspect), height: 3840 };
      }
    } else if (resolutionTarget === '8k') {
      // 8K UHD: 7680 wide (or 4320 tall)
      if (aspect >= 1.0) {
        return { width: 7680, height: Math.round(7680 / aspect) };
      } else {
        return { width: Math.round(7680 * aspect), height: 7680 };
      }
    } else {
      return { width: customWidth, height: customHeight };
    }
  };

  const targetDims = computeTargetDimensions();
  const targetMP = ((targetDims.width * targetDims.height) / 1000000).toFixed(1);

  // Recalculate plan when target or image changes
  useEffect(() => {
    if (!currentImage) return;
    const projId = `proj_${currentImage.image_id}`;
    const taskObj = TASK_CATEGORIES.find((t) => t.id === selectedTask) || TASK_CATEGORIES[0];
    const targetModel = selectedModel === 'auto' ? taskObj.recommendedModel : selectedModel;
    setPlanLoading(true);
    getResolutionPlan(projId, targetDims.width, targetDims.height, activeVersionId || undefined, selectedPreset, targetModel, selectedPlanChoice || undefined)
      .then((plan) => {
        setCurrentPlan(plan);
      })
      .catch((e) => {
        console.warn('Plan preflight info:', e);
      })
      .finally(() => {
        setPlanLoading(false);
      });
  }, [currentImage, resolutionTarget, customWidth, customHeight, activeVersionId, selectedPreset, selectedTask, selectedModel, selectedPlanChoice]);

  const handleFileUpload = async (file: File) => {
    try {
      setError(null);
      setCurrentJob(null);
      setAnalysisData(null);
      const res = await uploadImage(file);
      setCurrentImage(res);
      setImagePreviewUrl(URL.createObjectURL(file));
      setViewMode('original');

      const projId = `proj_${res.image_id}`;
      loadProjectVersions(projId);

      // Auto-analyze degradation
      setIsAnalyzing(true);
      try {
        const analysis = await analyzeImage(res.image_id, 'upscale', 4);
        setAnalysisData(analysis);
        // Automatically suggest category from analysis
        if (analysis.analysis.has_alpha) {
          setSelectedTask('transparent');
        } else if (analysis.analysis.detected_category === 'manga') {
          setSelectedTask('anime');
          setSelectedPreset('manga_crisp');
        } else if (analysis.analysis.detected_category.includes('anime')) {
          setSelectedTask('anime');
          setSelectedPreset('artwork');
        } else if (analysis.analysis.has_high_noise || analysis.analysis.jpeg_quality_estimate < 75) {
          setSelectedTask('restore');
        } else {
          setSelectedTask('photo');
        }
      } catch (err) {
        console.error('Image analysis error:', err);
      } finally {
        setIsAnalyzing(false);
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    }
  };

  const handleFilesSelected = async (files: File[]) => {
    if (!files || files.length === 0) return;
    if (files.length === 1) {
      handleFileUpload(files[0]);
      return;
    }

    try {
      setBatchLoading(true);
      setError(null);
      const uploaded = await uploadImagesBatch(files);
      setBatchImages(uploaded);
      setBatchJobs([]);
      setBatchOpen(true);
    } catch (err: any) {
      setError(err.message || 'Batch upload failed');
    } finally {
      setBatchLoading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelected(Array.from(e.dataTransfer.files));
    }
  };

  const startBatchUpscale = async () => {
    if (batchImages.length === 0) return;
    try {
      setIsBatchProcessing(true);
      setError(null);
      const taskObj = TASK_CATEGORIES.find((t) => t.id === selectedTask) || TASK_CATEGORIES[0];
      const modelToUse = selectedModel === 'auto' ? taskObj.recommendedModel : selectedModel;

      const payload = batchImages.map((img) => ({
        image_id: img.image_id,
        mode: taskObj.recommendedMode,
        scale: batchScale,
        model: modelToUse,
        preset: batchPreset,
        output_format: outputFormat,
        quality: quality
      }));

      const createdJobs = await createJobsBatch(payload);
      setBatchJobs(createdJobs);
      loadRecentJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to start batch queue');
      setIsBatchProcessing(false);
    }
  };

  const startJob = async (cropRegion?: number[]) => {
    if (!currentImage) return;
    try {
      setError(null);
      setIsProcessing(true);

      const taskObj = TASK_CATEGORIES.find((t) => t.id === selectedTask) || TASK_CATEGORIES[0];
      const targetModel = selectedModel === 'auto' ? taskObj.recommendedModel : selectedModel;
      let effectiveMode = taskObj.recommendedMode;
      const effectiveScale = resolutionTarget === '2x' ? 2 : 4;
      if (effectiveMode === 'restore' && effectiveScale > 1) {
        effectiveMode = 'restore_upscale';
      }

      const isLargeOrMultiStage = (resolutionTarget === '4k' || resolutionTarget === '8k' || resolutionTarget === 'custom');
      const job = await createJob({
        image_id: currentImage.image_id,
        mode: effectiveMode,
        scale: effectiveScale,
        model: targetModel,
        preset: selectedPreset,
        output_format: outputFormat,
        quality,
        crop_region: cropRegion,
        plan_json: isLargeOrMultiStage && currentPlan ? JSON.stringify(currentPlan) : undefined
      });
      setCurrentJob(job);

      if (unsubscribeRef.current) unsubscribeRef.current();

      unsubscribeRef.current = subscribeJobEvents(
        job.job_id,
        (status) => {
          setCurrentJob(status);
          if (status.status === 'completed') {
            setIsProcessing(false);
            setViewMode('slider');
            loadRecentJobs();
            loadProjectVersions(`proj_${currentImage.image_id}`);
          } else if (status.status === 'failed' || status.status === 'cancelled') {
            setIsProcessing(false);
            if (status.error) setError(status.error);
            loadRecentJobs();
          }
        },
        () => setIsProcessing(false)
      );
    } catch (err: any) {
      setError(err.message || 'Failed to start job');
      setIsProcessing(false);
    }
  };

  // Flagship 4K -> 8K Continuation
  const continueTo8kProgressive = async () => {
    if (!currentImage || !activeVersionId) return;
    try {
      setError(null);
      setIsProcessing(true);
      const projId = `proj_${currentImage.image_id}`;
      const res = await upscaleFromVersion(projId, activeVersionId, 7680, 4320, outputFormat);

      const jobStub: JobStatus = {
        job_id: res.job_id,
        status: 'processing',
        stage: 'starting',
        progress: 0.05,
        message: 'Starting Progressive 4K→8K Pipeline...',
        result_available: false
      };
      setCurrentJob(jobStub);

      if (unsubscribeRef.current) unsubscribeRef.current();

      unsubscribeRef.current = subscribeJobEvents(
        res.job_id,
        (status) => {
          setCurrentJob(status);
          if (status.status === 'completed') {
            setIsProcessing(false);
            setViewMode('slider');
            loadRecentJobs();
            loadProjectVersions(projId);
          } else if (status.status === 'failed' || status.status === 'cancelled') {
            setIsProcessing(false);
            if (status.error) setError(status.error);
            loadRecentJobs();
          }
        },
        () => setIsProcessing(false)
      );
    } catch (err: any) {
      setError(err.message || 'Failed to continue to 8K');
      setIsProcessing(false);
    }
  };

  const handlePause = async () => {
    if (!currentJob) return;
    try {
      await pauseJob(currentJob.job_id);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleResume = async () => {
    if (!currentJob) return;
    try {
      await resumeJob(currentJob.job_id);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleCancel = async () => {
    if (!currentJob) return;
    try {
      await cancelJob(currentJob.job_id);
      setIsProcessing(false);
      loadRecentJobs();
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      await deleteJob(jobId);
      if (currentJob?.job_id === jobId) setCurrentJob(null);
      loadRecentJobs();
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleSliderMove = (clientX: number) => {
    if (!sliderContainerRef.current) return;
    const rect = sliderContainerRef.current.getBoundingClientRect();
    const pos = ((clientX - rect.left) / rect.width) * 100;
    setSliderPos(Math.max(0, Math.min(100, pos)));
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (isDragging) handleSliderMove(e.clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    if (isDragging && e.touches[0]) handleSliderMove(e.touches[0].clientX);
  };

  // Active version for inspection
  const activeVersion = projectVersions.find((v) => v.id === activeVersionId);
  const is4kVersion = activeVersion && activeVersion.width >= 3800 && activeVersion.width <= 4000;

  return (
    <div
      className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col font-sans select-none"
      onMouseUp={() => setIsDragging(false)}
      onTouchEnd={() => setIsDragging(false)}
      onMouseMove={onMouseMove}
      onTouchMove={onTouchMove}
    >
      {/* Header */}
      <header className="border-b border-neutral-800 bg-neutral-900/60 backdrop-blur px-6 py-3.5 flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            Æ
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold tracking-tight">AETHER UPSCALE 2.0</h1>
              <span className="text-[10px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full">
                Vulkan Engine
              </span>
            </div>
            <p className="text-[11px] text-neutral-400">100% Local Neural Studio · Zero Cloud Telemetry</p>
          </div>
        </div>

                {/* Hardware Status & History */}
        <div className="flex items-center gap-3 text-xs">
          {capabilities && (
            <div className="hidden md:flex items-center gap-2 bg-neutral-900 border border-neutral-800 px-3 py-1.5 rounded-full text-neutral-300">
              <CpuIcon className="w-3.5 h-3.5 text-emerald-400" />
              <span>{capabilities.gpu}</span>
              <span className="text-neutral-600">|</span>
              <span className="text-neutral-400">Vulkan #{capabilities.vulkan_device_index} (4GB VRAM)</span>
            </div>
          )}

          {models.length > 0 && (
            <div className="hidden sm:flex items-center gap-1.5 bg-neutral-900 border border-neutral-800 px-3 py-1.5 rounded-full text-neutral-300 text-xs">
              <span className="text-emerald-400">●</span>
              <span>{models.length} Models Verified</span>
            </div>
          )}

          <button
            onClick={() => setBatchOpen(!batchOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs transition ${
              batchOpen || batchImages.length > 0
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/20'
                : 'bg-neutral-900 border-neutral-800 text-neutral-400 hover:text-white'
            }`}
          >
            <SparklesIcon className="w-3.5 h-3.5 text-indigo-300" />
            <span>Batch Queue {batchImages.length > 0 ? `(${batchImages.length})` : ''}</span>
          </button>

          <button
            onClick={() => setHistoryOpen(!historyOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs transition ${
              historyOpen
                ? 'bg-neutral-800 border-neutral-700 text-white'
                : 'bg-neutral-900 border-neutral-800 text-neutral-400 hover:text-white'
            }`}
          >
            <HistoryIcon className="w-3.5 h-3.5 text-indigo-400" />
            <span>History ({jobsList.length})</span>
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <div className="flex-1 flex overflow-hidden">
        <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 overflow-y-auto">
          {/* Left Column: Canvas, Versions & Visual Comparison (8 cols) */}
          <section className="lg:col-span-8 flex flex-col gap-3">
            {/* Toolbar above canvas */}
            {currentImage && (
              <div className="flex items-center justify-between bg-neutral-900/60 border border-neutral-800/80 px-4 py-2 rounded-xl text-xs">
                {/* View Mode Selector */}
                <div className="flex items-center gap-1 bg-neutral-950 p-1 rounded-lg border border-neutral-800">
                  <button
                    disabled={!currentJob || currentJob.status !== 'completed'}
                    onClick={() => setViewMode('slider')}
                    className={`px-2.5 py-1 rounded text-xs flex items-center gap-1.5 transition ${
                      viewMode === 'slider' ? 'bg-indigo-600 text-white' : 'text-neutral-400 hover:text-white disabled:opacity-40'
                    }`}
                  >
                    <SplitIcon className="w-3.5 h-3.5" />
                    Slider
                  </button>
                  <button
                    disabled={!currentJob || currentJob.status !== 'completed'}
                    onClick={() => setViewMode('side-by-side')}
                    className={`px-2.5 py-1 rounded text-xs transition ${
                      viewMode === 'side-by-side' ? 'bg-indigo-600 text-white' : 'text-neutral-400 hover:text-white disabled:opacity-40'
                    }`}
                  >
                    Side-by-Side
                  </button>
                  <button
                    onClick={() => setViewMode('original')}
                    className={`px-2.5 py-1 rounded text-xs transition ${
                      viewMode === 'original' ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-white'
                    }`}
                  >
                    Original
                  </button>
                  <button
                    disabled={!currentJob || currentJob.status !== 'completed'}
                    onClick={() => setViewMode('result')}
                    className={`px-2.5 py-1 rounded text-xs transition ${
                      viewMode === 'result' ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-white disabled:opacity-40'
                    }`}
                  >
                    Result
                  </button>
                </div>

                {/* Zoom Controls */}
                <div className="flex items-center gap-1 text-neutral-400">
                  <button
                    onClick={() => setZoom((z) => Math.max(1.0, z - 0.25))}
                    className="p-1.5 hover:bg-neutral-800 rounded text-neutral-300"
                    title="Zoom Out"
                  >
                    <ZoomOutIcon className="w-3.5 h-3.5" />
                  </button>
                  <span className="w-10 text-center font-mono text-[11px]">{Math.round(zoom * 100)}%</span>
                  <button
                    onClick={() => setZoom((z) => Math.min(3.0, z + 0.25))}
                    className="p-1.5 hover:bg-neutral-800 rounded text-neutral-300"
                    title="Zoom In"
                  >
                    <ZoomInIcon className="w-3.5 h-3.5" />
                  </button>
                  {zoom !== 1.0 && (
                    <button
                      onClick={() => setZoom(1.0)}
                      className="text-[10px] bg-neutral-800 hover:bg-neutral-700 px-1.5 py-0.5 rounded text-neutral-300 ml-1"
                    >
                      Reset
                    </button>
                  )}
                </div>

                {/* Download Button */}
                {currentJob?.status === 'completed' && (
                  <a
                    href={getDownloadUrl(currentJob.job_id, outputFormat, quality)}
                    download
                    className="flex items-center gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-3 py-1.5 rounded-lg shadow transition"
                  >
                    <DownloadIcon className="w-3.5 h-3.5" />
                    Download {outputFormat.toUpperCase()}
                  </a>
                )}
              </div>
            )}

            {/* Canvas Container */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={onDrop}
              ref={sliderContainerRef}
              className="flex-1 min-h-[500px] border-2 border-dashed border-neutral-800 bg-neutral-900/30 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden transition-colors"
            >
              {!currentImage ? (
                <div className="text-center p-8 max-w-sm">
                  <div className="w-16 h-16 rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-center mx-auto mb-4 text-neutral-400">
                    <UploadIcon className="w-8 h-8" />
                  </div>
                  <h3 className="text-base font-medium mb-1">Choose Images or Batch</h3>
                  <p className="text-xs text-neutral-400 mb-6">Drag and drop single or multiple PNG, JPEG, WebP, BMP up to 100 MP</p>
                  <label className="cursor-pointer bg-neutral-100 hover:bg-white text-neutral-950 font-medium text-xs px-4 py-2.5 rounded-xl shadow transition">
                    Browse Files
                    <input
                      type="file"
                      multiple
                      className="hidden"
                      accept="image/*"
                      onChange={(e) => e.target.files && handleFilesSelected(Array.from(e.target.files))}
                    />
                  </label>
                </div>
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center p-2 relative overflow-hidden">
                  {/* Slider View Mode */}
                  {viewMode === 'slider' && currentJob?.status === 'completed' && imagePreviewUrl && (
                    <div
                      className="relative w-full h-[520px] flex items-center justify-center overflow-hidden cursor-ew-resize select-none"
                      onMouseDown={() => setIsDragging(true)}
                      onTouchStart={() => setIsDragging(true)}
                    >
                      <img
                        src={imagePreviewUrl}
                        alt="Original"
                        style={{ transform: `scale(${zoom})` }}
                        className="absolute max-h-[500px] max-w-full object-contain pointer-events-none transition-transform"
                      />
                      <img
                        src={getPreviewUrl(currentJob.job_id)}
                        alt="Upscaled"
                        style={{
                          transform: `scale(${zoom})`,
                          clipPath: `inset(0 0 0 ${sliderPos}%)`
                        }}
                        className="absolute max-h-[500px] max-w-full object-contain pointer-events-none transition-transform"
                      />
                      <div
                        className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(0,0,0,0.8)] pointer-events-none"
                        style={{ left: `${sliderPos}%` }}
                      >
                        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-neutral-900 border-2 border-white shadow-xl flex items-center justify-center text-[10px] text-white font-bold">
                          ↔
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Side-by-Side View */}
                  {viewMode === 'side-by-side' && currentJob?.status === 'completed' && imagePreviewUrl && (
                    <div className="w-full h-[520px] grid grid-cols-2 gap-2 p-2">
                      <div className="flex flex-col items-center justify-center bg-neutral-950/60 rounded-xl overflow-hidden relative">
                        <img
                          src={imagePreviewUrl}
                          alt="Original"
                          style={{ transform: `scale(${zoom})` }}
                          className="max-h-[460px] max-w-full object-contain transition-transform"
                        />
                        <span className="absolute bottom-2 left-2 bg-black/70 px-2 py-0.5 rounded text-[10px] text-neutral-300">
                          Original ({currentImage.width}×{currentImage.height})
                        </span>
                      </div>
                      <div className="flex flex-col items-center justify-center bg-neutral-950/60 rounded-xl overflow-hidden relative">
                        <img
                          src={getPreviewUrl(currentJob.job_id)}
                          alt="Upscaled"
                          style={{ transform: `scale(${zoom})` }}
                          className="max-h-[460px] max-w-full object-contain transition-transform"
                        />
                        <span className="absolute bottom-2 right-2 bg-indigo-950/80 border border-indigo-700/50 px-2 py-0.5 rounded text-[10px] text-indigo-300">
                          Result ({targetDims.width}×{targetDims.height})
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Single View: Original */}
                  {viewMode === 'original' && imagePreviewUrl && (
                    <div className="w-full h-[520px] flex items-center justify-center overflow-hidden">
                      <img
                        src={imagePreviewUrl}
                        alt="Original"
                        style={{ transform: `scale(${zoom})` }}
                        className="max-h-[500px] max-w-full object-contain transition-transform"
                      />
                    </div>
                  )}

                  {/* Single View: Result */}
                  {viewMode === 'result' && currentJob?.status === 'completed' && (
                    <div className="w-full h-[520px] flex items-center justify-center overflow-hidden">
                      <img
                        src={getPreviewUrl(currentJob.job_id)}
                        alt="Result"
                        style={{ transform: `scale(${zoom})` }}
                        className="max-h-[500px] max-w-full object-contain transition-transform"
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Version Graph Strip (Part E & K9) */}
            {projectVersions.length > 0 && (
              <div className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-3 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-neutral-400 font-medium">Version Graph:</span>
                  <div className="flex items-center gap-1.5 overflow-x-auto">
                    {projectVersions.map((v, idx) => (
                      <button
                        key={v.id}
                        onClick={() => setActiveVersionId(v.id)}
                        className={`px-2.5 py-1 rounded-lg border text-[11px] font-mono flex items-center gap-1.5 transition ${
                          activeVersionId === v.id
                            ? 'bg-indigo-600 border-indigo-500 text-white shadow-sm'
                            : 'bg-neutral-950 border-neutral-800 text-neutral-400 hover:text-white'
                        }`}
                      >
                        <span>v{idx + 1}</span>
                        <span className="text-[10px] text-neutral-400">({v.width}×{v.height})</span>
                        {v.decision === 'accepted' && <span className="text-emerald-400 text-[10px]">✓</span>}
                      </button>
                    ))}
                  </div>
                </div>

                {activeVersion && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateVersionDecision(activeVersion.id, 'accepted')}
                      className="px-2 py-0.5 rounded text-[11px] bg-emerald-950/60 text-emerald-400 border border-emerald-800 hover:bg-emerald-900"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => updateVersionDecision(activeVersion.id, 'rejected')}
                      className="px-2 py-0.5 rounded text-[11px] bg-neutral-900 text-neutral-400 hover:text-rose-400 border border-neutral-800"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Flagship Continuation Banner (Part F4) */}
            {is4kVersion && (
              <div className="bg-gradient-to-r from-indigo-950/70 to-purple-950/70 border border-indigo-500/40 p-3.5 rounded-xl flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <span className="text-xl">🌟</span>
                  <div>
                    <h4 className="font-semibold text-indigo-200">Flagship 4K → 8K UHD Progressive Upscale</h4>
                    <p className="text-neutral-300 text-[11px]">
                      Continue directly from this 4K version to 8K UHD (7680×4320) with no re-upload. Tiled Hann accumulation prevents RAM OOM.
                    </p>
                  </div>
                </div>
                <button
                  disabled={isProcessing}
                  onClick={continueTo8kProgressive}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-xs shadow-md shadow-indigo-600/30 whitespace-nowrap transition"
                >
                  Upscale to 8K UHD (2×)
                </button>
              </div>
            )}

            {/* Generative detail disclaimer banner */}
            {currentJob?.status === 'completed' && (
              <div className="bg-neutral-900 border border-neutral-800 px-3.5 py-2 rounded-xl text-xs flex items-center justify-between text-neutral-400">
                <span>Model: Real-ESRGAN x4plus (Vulkan GPU #0)</span>
                <span className="text-amber-400/90 text-[11px]">Notice: Generated textures may invent plausible detail</span>
              </div>
            )}
          </section>

          {/* Right Column: Everyday Usability Redesign & Resolution Studio (4 cols) */}
          <aside className="lg:col-span-4 flex flex-col gap-4">
            <div className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-5 flex flex-col gap-4">
              {/* Step 1: User-Facing Task Categories (Part K3) */}
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold text-neutral-200 flex items-center gap-1.5">
                    <span>1. What do you want to do?</span>
                  </label>
                  {isAnalyzing && <span className="text-[10px] text-indigo-400 animate-pulse">Analyzing image...</span>}
                </div>

                <div className="grid grid-cols-2 gap-2">
                  {TASK_CATEGORIES.map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => {
                        setSelectedTask(cat.id);
                        if (cat.id === 'lineart') {
                          setSelectedPreset('manga_crisp');
                        } else if (cat.id === 'anime') {
                          setSelectedPreset('anime_clean');
                        } else if (cat.id === 'photo') {
                          setSelectedPreset('natural');
                        } else if (cat.id === 'restore') {
                          setSelectedPreset('smooth_clean');
                        }
                      }}
                      className={`p-2.5 rounded-xl border text-left flex flex-col gap-1 transition ${
                        selectedTask === cat.id
                          ? 'border-indigo-500 bg-indigo-500/10 text-white shadow-sm'
                          : 'border-neutral-800 bg-neutral-950 text-neutral-400 hover:border-neutral-700'
                      }`}
                    >
                      <div className="flex items-center gap-1.5">
                        <span className="text-base">{cat.icon}</span>
                        <span className="text-xs font-medium text-neutral-200 leading-tight">{cat.name}</span>
                      </div>
                      <p className="text-[10px] text-neutral-400 line-clamp-2 leading-tight">{cat.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Step 2: Plain-Language Quality Presets (Part K4) */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-neutral-200">2. Quality Preset</label>
                <div className="grid grid-cols-3 gap-1.5 bg-neutral-950 p-1 rounded-xl border border-neutral-800">
                  {QUALITY_PRESETS.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setSelectedPreset(p.id)}
                      className={`py-1.5 px-2 rounded-lg text-xs capitalize transition text-center ${
                        selectedPreset === p.id
                          ? 'bg-neutral-800 text-white font-medium shadow-sm'
                          : 'text-neutral-400 hover:text-white'
                      }`}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>

                {/* Active Preset Description & Grain Warning per V3 Addendum §9 */}
                {(() => {
                  const activeP = QUALITY_PRESETS.find((p) => p.id === selectedPreset);
                  return (
                    <div className="flex flex-col gap-1 mt-0.5">
                      <p className="text-[11px] text-neutral-400 italic leading-snug">{activeP?.desc}</p>
                      {selectedPreset === 'smooth_clean' && (
                        <div className="bg-amber-950/40 border border-amber-800/50 p-1.5 rounded text-[10px] text-amber-300 leading-tight">
                          ⚠️ Warning: Natural film grain, skin pores, and microscopic textures will be softened by noise suppression.
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>

              {/* Step 3: Resolution Studio & Target Size (Part K6 & F5a) */}
              <div className="flex flex-col gap-2 pt-1 border-t border-neutral-800/80">
                <label className="text-xs font-semibold text-neutral-200 flex items-center justify-between">
                  <span>3. Output Size (Resolution Studio)</span>
                  <span className="text-[10px] text-emerald-400 font-mono">{targetMP} MP</span>
                </label>

                <div className="grid grid-cols-5 gap-1.5">
                  {(['2x', '4x', '4k', '8k', 'custom'] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setResolutionTarget(t)}
                      className={`py-2 px-1 rounded-xl border text-xs font-medium flex flex-col items-center justify-center transition ${
                        resolutionTarget === t
                          ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300'
                          : 'border-neutral-800 bg-neutral-950 text-neutral-400 hover:border-neutral-700'
                      }`}
                    >
                      <span className="uppercase font-semibold">{t}</span>
                      <span className="text-[9px] text-neutral-400">
                        {t === '4k' ? 'UHD' : t === '8k' ? '7680p' : t === 'custom' ? 'Manual' : `${t.replace('x', '')}×`}
                      </span>
                    </button>
                  ))}
                </div>

                {resolutionTarget === 'custom' && (
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <div>
                      <label className="text-[10px] text-neutral-400 block mb-0.5">Width (px)</label>
                      <input
                        type="number"
                        value={customWidth}
                        onChange={(e) => setCustomWidth(Math.max(100, Number(e.target.value)))}
                        className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-1.5 text-xs text-neutral-200 outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-neutral-400 block mb-0.5">Height (px)</label>
                      <input
                        type="number"
                        value={customHeight}
                        onChange={(e) => setCustomHeight(Math.max(100, Number(e.target.value)))}
                        className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-1.5 text-xs text-neutral-200 outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                )}

                {/* Maximum Resolution Explorer (Part F5a) */}
                <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-3 text-xs flex flex-col gap-1.5 text-neutral-400">
                  <div className="flex justify-between items-center text-neutral-300 font-medium pb-1 border-b border-neutral-900">
                    <span>Resolution Preflight</span>
                    <span className="text-[10px] text-indigo-400">
                      {planLoading ? 'Calculating Plan...' : (currentPlan ? currentPlan.name : 'Computing Plan...')}
                    </span>
                  </div>

                  {/* Plan Choice Selector (Plan A vs Plan B vs Plan C) per V3 Addendum §1.7 */}
                  <div className="grid grid-cols-3 gap-1 my-1">
                    <button
                      type="button"
                      onClick={() => setSelectedPlanChoice('A')}
                      className={`p-1.5 rounded text-[10px] font-medium border text-center transition ${
                        (selectedPlanChoice === 'A' || (!selectedPlanChoice && currentPlan?.plan_type === 'plan_a'))
                          ? 'bg-indigo-950/70 border-indigo-500 text-indigo-200'
                          : 'bg-neutral-900 border-neutral-800 text-neutral-400 hover:border-neutral-700'
                      }`}
                      title="Direct single-pass upscale from original ancestor"
                    >
                      Plan A (Direct)
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedPlanChoice('B')}
                      className={`p-1.5 rounded text-[10px] font-medium border text-center transition ${
                        (selectedPlanChoice === 'B' || (!selectedPlanChoice && currentPlan?.plan_type === 'plan_b'))
                          ? 'bg-indigo-950/70 border-indigo-500 text-indigo-200'
                          : 'bg-neutral-900 border-neutral-800 text-neutral-400 hover:border-neutral-700'
                      }`}
                      title="Progressive multi-stage continuation"
                    >
                      Plan B (Progressive)
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedPlanChoice('C')}
                      className={`p-1.5 rounded text-[10px] font-medium border text-center transition ${
                        (selectedPlanChoice === 'C' || currentPlan?.plan_type === 'plan_c')
                          ? 'bg-indigo-950/70 border-indigo-500 text-indigo-200'
                          : 'bg-neutral-900 border-neutral-800 text-neutral-400 hover:border-neutral-700'
                      }`}
                      title="Traditional Resample (Lanczos): Pure anti-aliased interpolation, 0 invented detail"
                    >
                      Plan C (Traditional)
                    </button>
                  </div>

                  {analysisData && (
                    <div className="text-[11px] bg-neutral-900/60 border border-neutral-900 p-2 rounded-lg text-neutral-300 flex justify-between items-center">
                      <span>Signal: <strong className="text-white capitalize">{analysisData.analysis.detected_category}</strong></span>
                      <span className="text-neutral-400 text-[10px] font-mono">σ {analysisData.analysis.estimated_noise_sigma} | ~Q{analysisData.analysis.jpeg_quality_estimate}</span>
                    </div>
                  )}

                  <div className="flex justify-between">
                    <span>Target Dimensions:</span>
                    <span className="text-neutral-200 font-medium">{targetDims.width} × {targetDims.height} px</span>
                  </div>

                  {currentPlan?.resource_estimate && (
                    <>
                      <div className="flex justify-between">
                        <span>Peak RAM Estimate:</span>
                        <span className="text-neutral-200 font-mono">{currentPlan.resource_estimate.peak_ram_mb} MB / 8GB</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Peak VRAM Estimate:</span>
                        <span className="text-neutral-200 font-mono">{currentPlan.resource_estimate.peak_vram_mb} MB / 4GB</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Estimated Runtime:</span>
                        <span className="text-emerald-400 font-medium">~{currentPlan.resource_estimate.estimated_runtime_seconds}s</span>
                      </div>
                    </>
                  )}

                  {/* Warning if repeated model or aspect change */}
                  {currentPlan?.warnings && currentPlan.warnings.length > 0 && (
                    <div className="bg-amber-950/30 border border-amber-800/40 p-2 rounded text-[11px] text-amber-300 leading-tight mt-1">
                      {currentPlan.warnings[0]}
                    </div>
                  )}
                </div>
              </div>

              {/* Step 4: Expandable Expert Mode / Technical Details (Part K7 & K8) */}
              <div className="border-t border-neutral-800/80 pt-2">
                <button
                  onClick={() => setExpertModeOpen(!expertModeOpen)}
                  className="w-full flex items-center justify-between text-xs text-neutral-400 hover:text-neutral-200 transition py-1"
                >
                  <span className="flex items-center gap-1.5 font-medium">
                    <InfoIcon className="w-3.5 h-3.5 text-indigo-400" />
                    Technical Details & Expert Mode
                  </span>
                  <span>{expertModeOpen ? '▲' : '▼'}</span>
                </button>

                {expertModeOpen && (
                  <div className="mt-2.5 p-3 bg-neutral-950 border border-neutral-800 rounded-xl flex flex-col gap-2.5 text-xs">
                    <div className="flex flex-col gap-1">
                      <label className="text-neutral-400 text-[11px]">Neural Checkpoint Override</label>
                      <select
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        className="bg-neutral-900 border border-neutral-800 text-neutral-200 text-xs rounded-lg p-2 outline-none"
                      >
                        <option value="auto">Auto (Task Selected)</option>
                        <option value="realesrgan-x4plus">Real-ESRGAN x4plus (BSD-3-Clause)</option>
                        <option value="realesrgan-x4plus-anime">Real-ESRGAN x4plus Anime (BSD-3-Clause)</option>
                        <option value="realesr-animevideov3-x4">Real-ESRGAN AnimeVideo v3 (BSD-3-Clause)</option>
                        <option value="diffbir" disabled>DiffBIR (Tier 3 Generative - 4GB VRAM Cap)</option>
                      </select>
                    </div>

                    <div className="flex justify-between text-[11px] text-neutral-400 border-t border-neutral-900 pt-1.5">
                      <span>Vulkan Device:</span>
                      <span className="text-neutral-200 font-mono">{capabilities?.vulkan_device_name || "NVIDIA GeForce RTX 2050 (Vulkan #0)"}</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-neutral-400">
                      <span>Active Backend:</span>
                      <span className="text-neutral-200 font-mono">ncnn-vulkan</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-neutral-400">
                      <span>Tile Strategy:</span>
                      <span className="text-neutral-200 font-mono">256px tile, 32px cosine feather</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-neutral-400">
                      <span>Texture Preservation:</span>
                      <span className="text-emerald-400 font-mono">
                        {selectedPreset === 'natural' ? '20% Optical Blend' : selectedPreset === 'faithful' ? '10% Optical Blend' : '0% (Model Pure)'}
                      </span>
                    </div>
                    <p className="text-[10px] text-neutral-500 italic">
                      Notice: Texture preservation controls the app's cleanup steps; the underlying AI model may still soften microscopic grain.
                    </p>
                    <div className="flex justify-between text-[11px] text-neutral-400">
                      <span>Safety Cap:</span>
                      <span className="text-emerald-400 font-mono">100 Megapixels max</span>
                    </div>

                    {/* Export Format */}
                    <div className="flex flex-col gap-1 border-t border-neutral-900 pt-1.5">
                      <label className="text-neutral-400 text-[11px]">Export Format</label>
                      <div className="grid grid-cols-3 gap-1 bg-neutral-900 p-1 rounded-lg">
                        {['png', 'jpeg', 'webp'].map((fmt) => (
                          <button
                            key={fmt}
                            onClick={() => setOutputFormat(fmt)}
                            className={`py-1 text-[11px] uppercase rounded transition ${
                              outputFormat === fmt ? 'bg-neutral-800 text-white font-medium' : 'text-neutral-400'
                            }`}
                          >
                            {fmt}
                          </button>
                        ))}
                      </div>

                      {outputFormat !== 'png' && (
                        <div className="flex flex-col gap-1 mt-2">
                          <div className="flex justify-between text-[10px] text-neutral-400">
                            <span>Compression Quality</span>
                            <span>{quality}%</span>
                          </div>
                          <input
                            type="range"
                            min="20"
                            max="100"
                            value={quality}
                            onChange={(e) => setQuality(Number(e.target.value))}
                            className="w-full accent-indigo-500 h-1 bg-neutral-800 rounded-lg cursor-pointer"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons & Execution Controls */}
              <div className="flex flex-col gap-2 pt-1">
                {!isProcessing ? (
                  <>
                    <button
                      disabled={!currentImage}
                      onClick={() => startJob()}
                      className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-xl shadow-lg shadow-indigo-600/20 text-xs flex items-center justify-center gap-2 transition"
                    >
                      <SparklesIcon className="w-4 h-4" />
                      Run Enhancement ({targetDims.width}×{targetDims.height})
                    </button>

                    <button
                      disabled={!currentImage}
                      onClick={() => startJob([0, 0, 256, 256])}
                      className="w-full bg-neutral-800 hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed text-neutral-200 font-medium py-2 rounded-xl text-xs flex items-center justify-center gap-1.5 transition"
                    >
                      <CropIcon className="w-3.5 h-3.5 text-indigo-400" />
                      Fast Crop Preview (256px Region)
                    </button>
                  </>
                ) : (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      {currentJob?.status === 'paused' ? (
                        <button
                          onClick={handleResume}
                          className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2.5 rounded-xl text-xs flex items-center justify-center gap-1.5 transition shadow"
                        >
                          <PlayIcon className="w-4 h-4" />
                          Resume Processing
                        </button>
                      ) : (
                        <button
                          onClick={handlePause}
                          className="flex-1 bg-amber-600 hover:bg-amber-500 text-white font-medium py-2.5 rounded-xl text-xs flex items-center justify-center gap-1.5 transition shadow"
                        >
                          <PauseIcon className="w-4 h-4" />
                          Pause at Checkpoint
                        </button>
                      )}

                      <button
                        onClick={handleCancel}
                        className="bg-rose-600 hover:bg-rose-500 text-white font-medium px-4 py-2.5 rounded-xl text-xs flex items-center justify-center gap-1.5 transition shadow"
                      >
                        <XCircleIcon className="w-4 h-4" />
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Live Progress Card */}
            {currentJob && (
              <div className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-4 flex flex-col gap-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-neutral-300">Live Progress</span>
                  <span className="capitalize px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 text-[11px]">
                    {currentJob.status}
                  </span>
                </div>

                <div className="w-full bg-neutral-950 rounded-full h-2 overflow-hidden border border-neutral-800">
                  <div
                    className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.round((currentJob.progress || 0) * 100)}%` }}
                  />
                </div>

                <div className="text-xs text-neutral-400 flex items-center justify-between">
                  <span>{currentJob.message || 'Processing...'}</span>
                  <span>{Math.round((currentJob.progress || 0) * 100)}%</span>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-rose-950/40 border border-rose-800/80 rounded-2xl p-4 flex items-start gap-3 text-xs text-rose-300">
                <AlertCircleIcon className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
          </aside>
        </main>

        {/* Batch Queue Drawer */}
        {batchOpen && (
          <aside className="w-96 border-l border-neutral-800 bg-neutral-900/95 backdrop-blur p-4 flex flex-col gap-3 z-30 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
              <div className="flex items-center gap-2">
                <SparklesIcon className="w-4 h-4 text-indigo-400" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-200">
                  Batch Processing Queue
                </h3>
              </div>
              <button
                onClick={() => setBatchOpen(false)}
                className="text-neutral-400 hover:text-white text-xs p-1"
              >
                ✕
              </button>
            </div>

            {/* Batch Controls */}
            <div className="bg-neutral-950/80 border border-neutral-800/80 rounded-xl p-3 flex flex-col gap-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-neutral-400">Preset:</span>
                <select
                  value={batchPreset}
                  onChange={(e) => setBatchPreset(e.target.value)}
                  disabled={isBatchProcessing}
                  className="bg-neutral-900 border border-neutral-800 rounded px-2 py-1 text-xs text-neutral-200"
                >
                  <option value="manga_crisp">Manga Master (Inking)</option>
                  <option value="anime_clean">Anime Master (Cel Art)</option>
                  <option value="natural">Natural (Photo)</option>
                  <option value="faithful">Faithful (Strict Neural)</option>
                  <option value="more_detail">More Detail</option>
                  <option value="smooth_clean">Smooth & Clean</option>
                </select>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-neutral-400">Scale:</span>
                <div className="flex gap-1.5">
                  <button
                    onClick={() => setBatchScale(2)}
                    disabled={isBatchProcessing}
                    className={`px-2.5 py-1 rounded text-xs transition ${
                      batchScale === 2 ? 'bg-indigo-600 text-white' : 'bg-neutral-900 text-neutral-400'
                    }`}
                  >
                    2×
                  </button>
                  <button
                    onClick={() => setBatchScale(4)}
                    disabled={isBatchProcessing}
                    className={`px-2.5 py-1 rounded text-xs transition ${
                      batchScale === 4 ? 'bg-indigo-600 text-white' : 'bg-neutral-900 text-neutral-400'
                    }`}
                  >
                    4×
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={startBatchUpscale}
                  disabled={isBatchProcessing || batchLoading || batchImages.length === 0}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium py-2 rounded-lg transition shadow flex items-center justify-center gap-1.5"
                >
                  <SparklesIcon className="w-3.5 h-3.5" />
                  {batchLoading ? 'Uploading Images...' : (isBatchProcessing ? 'Processing Queue...' : `Start Batch (${batchImages.length})`)}
                </button>
                {batchJobs.some((j) => j.status === 'completed') && (
                  <button
                    onClick={() => {
                      const completedIds = batchJobs.filter((j) => j.status === 'completed').map((j) => j.job_id);
                      downloadBatchZip(completedIds);
                    }}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium px-3 py-2 rounded-lg transition shadow flex items-center gap-1"
                    title="Download All as ZIP"
                  >
                    <DownloadIcon className="w-3.5 h-3.5" />
                    ZIP
                  </button>
                )}
              </div>
            </div>

            {/* Overall Progress */}
            {batchJobs.length > 0 && (
              <div className="bg-neutral-950/60 border border-neutral-800/80 rounded-xl p-3 flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-[11px] text-neutral-400">
                  <span>Sequential GPU Queue</span>
                  <span>
                    {batchJobs.filter((j) => j.status === 'completed').length} / {batchJobs.length} Done
                  </span>
                </div>
                <div className="w-full bg-neutral-900 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-1.5 rounded-full transition-all duration-300"
                    style={{
                      width: `${(batchJobs.filter((j) => j.status === 'completed').length / Math.max(1, batchJobs.length)) * 100}%`
                    }}
                  />
                </div>
              </div>
            )}

            {/* Item List */}
            <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1">
              {batchImages.length === 0 ? (
                <div className="text-center py-10 px-4">
                  <p className="text-xs text-neutral-500 mb-3">No images in batch queue</p>
                  <label className="cursor-pointer bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs px-3 py-1.5 rounded-lg transition">
                    Add Images
                    <input
                      type="file"
                      multiple
                      className="hidden"
                      accept="image/*"
                      onChange={(e) => {
                        if (e.target.files) {
                          uploadImagesBatch(Array.from(e.target.files)).then((newImgs) => {
                            setBatchImages((prev) => [...prev, ...newImgs]);
                          });
                        }
                      }}
                    />
                  </label>
                </div>
              ) : (
                batchImages.map((img, idx) => {
                  const job = batchJobs[idx];
                  return (
                    <div
                      key={img.image_id}
                      className="bg-neutral-950/80 border border-neutral-800/80 rounded-xl p-2.5 flex items-center justify-between gap-2.5 hover:border-neutral-700 transition text-xs"
                    >
                      <div className="flex items-center gap-2.5 min-w-0 flex-1">
                        <div className="w-8 h-8 rounded bg-neutral-900 border border-neutral-800 flex items-center justify-center shrink-0 overflow-hidden text-[10px] text-neutral-500 font-mono">
                          {idx + 1}
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-medium text-neutral-200 truncate">{img.filename}</span>
                          <span className="text-[10px] text-neutral-500">
                            {img.width}×{img.height} → {img.width * batchScale}×{img.height * batchScale}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {job ? (
                          job.status === 'completed' ? (
                            <div className="flex items-center gap-1.5">
                              <span className="text-[10px] text-emerald-400 bg-emerald-950/50 border border-emerald-800 px-1.5 py-0.5 rounded">
                                Done
                              </span>
                              <button
                                onClick={() => {
                                  setCurrentImage(img);
                                  setCurrentJob(job);
                                  setViewMode('slider');
                                  setBatchOpen(false);
                                }}
                                className="text-[10px] bg-neutral-800 hover:bg-neutral-700 px-2 py-1 rounded text-neutral-300"
                                title="View in Studio Slider"
                              >
                                View
                              </button>
                              <a
                                href={getDownloadUrl(job.job_id, outputFormat, quality)}
                                download
                                className="p-1 hover:bg-neutral-800 rounded text-neutral-400 hover:text-emerald-400"
                                title="Download"
                              >
                                <DownloadIcon className="w-3.5 h-3.5" />
                              </a>
                            </div>
                          ) : job.status === 'processing' ? (
                            <span className="text-[10px] text-indigo-400 bg-indigo-950/50 border border-indigo-800 px-2 py-0.5 rounded animate-pulse">
                              {Math.round((job.progress || 0) * 100)}%
                            </span>
                          ) : job.status === 'failed' ? (
                            <span className="text-[10px] text-rose-400 bg-rose-950/50 border border-rose-800 px-1.5 py-0.5 rounded">
                              Failed
                            </span>
                          ) : (
                            <span className="text-[10px] text-neutral-500 bg-neutral-900 px-1.5 py-0.5 rounded">
                              Queued
                            </span>
                          )
                        ) : (
                          <span className="text-[10px] text-neutral-500">Ready</span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="pt-2 border-t border-neutral-800 flex items-center justify-between text-xs text-neutral-400">
              <label className="cursor-pointer text-indigo-400 hover:text-indigo-300 text-xs">
                + Add More
                <input
                  type="file"
                  multiple
                  className="hidden"
                  accept="image/*"
                  onChange={(e) => {
                    if (e.target.files) {
                      uploadImagesBatch(Array.from(e.target.files)).then((newImgs) => {
                        setBatchImages((prev) => [...prev, ...newImgs]);
                      });
                    }
                  }}
                />
              </label>
              {batchImages.length > 0 && (
                <button
                  onClick={() => {
                    clearQueue();
                    setBatchImages([]);
                    setBatchJobs([]);
                    setIsBatchProcessing(false);
                  }}
                  className="text-neutral-500 hover:text-rose-400 text-xs"
                >
                  Clear Queue
                </button>
              )}
            </div>
          </aside>
        )}

        {/* Sliding History Drawer */}
        {historyOpen && (
          <aside className="w-80 border-l border-neutral-800 bg-neutral-900/90 backdrop-blur p-4 flex flex-col gap-3 z-30">
            <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Job History</h3>
              <button
                onClick={() => setHistoryOpen(false)}
                className="text-neutral-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1">
              {jobsList.length === 0 ? (
                <p className="text-xs text-neutral-500 text-center py-8">No jobs in history yet</p>
              ) : (
                jobsList.map((job) => (
                  <div
                    key={job.job_id}
                    className="bg-neutral-950/80 border border-neutral-800/80 rounded-xl p-2.5 flex items-center justify-between gap-2.5 hover:border-neutral-700 transition"
                  >
                    <div
                      onClick={() => {
                        setCurrentJob(job);
                        setViewMode('slider');
                      }}
                      className="flex items-center gap-2.5 cursor-pointer flex-1 min-w-0"
                    >
                      {job.result_available ? (
                        <img
                          src={getPreviewUrl(job.job_id)}
                          alt="Thumb"
                          className="w-10 h-10 object-cover rounded bg-neutral-900 shrink-0"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded bg-neutral-900 flex items-center justify-center text-neutral-600 shrink-0 text-xs">
                          {job.status[0].toUpperCase()}
                        </div>
                      )}
                      <div className="flex flex-col min-w-0">
                        <span className="text-xs font-medium truncate text-neutral-200">
                          {job.scale}× {job.output_format?.toUpperCase()}
                        </span>
                        <span className="text-[10px] text-neutral-500 capitalize">{job.status}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      {job.result_available && (
                        <a
                          href={getDownloadUrl(job.job_id, job.output_format)}
                          download
                          className="p-1.5 hover:bg-neutral-800 rounded text-neutral-400 hover:text-emerald-400 transition"
                          title="Download"
                        >
                          <DownloadIcon className="w-3.5 h-3.5" />
                        </a>
                      )}
                      <button
                        onClick={() => handleDeleteJob(job.job_id)}
                        className="p-1.5 hover:bg-neutral-800 rounded text-neutral-500 hover:text-rose-400 transition"
                        title="Delete"
                      >
                        <TrashIcon className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
