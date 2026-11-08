export interface SystemCapabilities {
  os: string;
  gpu: string;
  total_vram_mb: number;
  vulkan_device_index: number;
  vulkan_device_name: string;
  active_backend: string;
  max_output_megapixels: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  scale: number;
  code_license: string;
  weight_license: string;
  license_class: string;
  status: string;
  available: boolean;
}

export interface ImageUploadResult {
  image_id: string;
  filename: string;
  width: number;
  height: number;
  format: string;
  size_bytes: number;
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'paused' | 'completed' | 'failed' | 'cancelled';
  stage: string;
  progress: number | null;
  message: string | null;
  result_available: boolean;
  warnings?: string[];
  error?: string | null;
  scale?: number;
  mode?: string;
  output_format?: string;
  created_at?: number;
}

export interface VersionItem {
  id: string;
  parent_version_id: string | null;
  project_id: string;
  width: number;
  height: number;
  megapixels: number;
  pixel_format: string;
  operation: string;
  mode?: string;
  model_id?: string;
  decision: 'accepted' | 'rejected' | 'pending';
  state: string;
  created_at: number;
  runtime_s?: number;
  sha256?: string;
}

export interface StageInfo {
  stage_id: string;
  stage_index: number;
  operation: string;
  model: string;
  from_size: string;
  to_size: string;
  status: string;
  completed_tiles: number;
  total_tiles: number;
}

export interface PlanOption {
  plan_type: 'A' | 'B' | 'C';
  name: string;
  description: string;
  source_dimensions: [number, number];
  target_dimensions: [number, number];
  scale_factor: number;
  recommended: boolean;
  resource_estimate?: {
    output_megapixels: number;
    peak_ram_mb: number;
    peak_vram_mb: number;
    required_disk_mb: number;
    estimated_runtime_seconds: number;
  };
}

export interface ResolutionPlan {
  plan_type: 'plan_a' | 'plan_b' | 'plan_c';
  name: string;
  target_width: number;
  target_height: number;
  stages: Array<{
    stage_index: number;
    operation: string;
    model_name: string;
    from_res: [number, number];
    to_res: [number, number];
    model_scale: number;
    target_scale: number;
  }>;
  warnings: string[];
  resource_estimate?: {
    output_megapixels: number;
    peak_ram_mb: number;
    peak_vram_mb: number;
    required_disk_mb: number;
    estimated_runtime_seconds: number;
    requires_disk_streaming: boolean;
  };
  all_plans?: PlanOption[];
}

export interface AnalysisResult {
  analysis: {
    width: number;
    height: number;
    format: string;
    has_alpha: boolean;
    estimated_blur_score: number;
    is_blurry: boolean;
    estimated_noise_sigma: number;
    has_high_noise: boolean;
    jpeg_quality_estimate: number;
    detected_category: string;
    category_confidence: number;
  };
  recommendation: {
    selected_model: string;
    model_name: string;
    scale: number;
    reasoning: string;
  };
}

const BASE_URL = '/api/v1';

export async function fetchCapabilities(): Promise<SystemCapabilities> {
  const res = await fetch(`${BASE_URL}/system/capabilities`);
  if (!res.ok) throw new Error('Failed to fetch capabilities');
  return res.json();
}

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${BASE_URL}/models`);
  if (!res.ok) throw new Error('Failed to fetch models');
  const data = await res.json();
  return data.models;
}

export async function fetchRecentJobs(limit = 20): Promise<JobStatus[]> {
  const res = await fetch(`${BASE_URL}/jobs?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch jobs');
  return res.json();
}

export async function uploadImage(file: File): Promise<ImageUploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/images`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function analyzeImage(imageId: string, mode = 'upscale', scale = 4, requestedModel?: string): Promise<AnalysisResult> {
  let url = `${BASE_URL}/images/${imageId}/analyze?mode=${mode}&scale=${scale}`;
  if (requestedModel) url += `&requested_model=${requestedModel}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Analysis failed');
  return res.json();
}

export async function createJob(params: {
  image_id: string;
  mode: string;
  scale: number;
  model: string;
  preset?: string;
  tile_size?: number;
  output_format?: string;
  quality?: number;
  crop_region?: number[];
  plan_json?: string;
}): Promise<JobStatus> {
  const res = await fetch(`${BASE_URL}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create job' }));
    throw new Error(err.detail || 'Failed to create job');
  }
  return res.json();
}

export async function cancelJob(jobId: string): Promise<void> {
  await fetch(`${BASE_URL}/jobs/${jobId}/cancel`, { method: 'POST' });
}

export async function pauseJob(jobId: string): Promise<void> {
  await fetch(`${BASE_URL}/jobs/${jobId}/pause`, { method: 'POST' });
}

export async function resumeJob(jobId: string): Promise<void> {
  await fetch(`${BASE_URL}/jobs/${jobId}/resume`, { method: 'POST' });
}

export async function deleteJob(jobId: string): Promise<void> {
  await fetch(`${BASE_URL}/jobs/${jobId}`, { method: 'DELETE' });
}

export async function fetchJobStages(jobId: string): Promise<{ stages: StageInfo[] }> {
  const res = await fetch(`${BASE_URL}/jobs/${jobId}/stages`);
  if (!res.ok) throw new Error('Failed to fetch job stages');
  return res.json();
}

export async function fetchProjectVersions(projectId: string): Promise<VersionItem[]> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/versions`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.versions || [];
}

export async function getResolutionPlan(
  projectId: string,
  targetWidth: number,
  targetHeight: number,
  sourceVersionId?: string,
  preset?: string,
  model?: string,
  planChoice?: string
): Promise<ResolutionPlan> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_width: targetWidth,
      target_height: targetHeight,
      source_version_id: sourceVersionId,
      preset,
      model,
      plan_choice: planChoice
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to get plan' }));
    throw new Error(err.detail || 'Failed to compute plan');
  }
  return res.json();
}

export async function upscaleFromVersion(
  projectId: string,
  versionId: string,
  targetWidth: number,
  targetHeight: number,
  outputFormat = 'png',
  planChoice?: string
): Promise<{ job_id: string; status: string; plan: ResolutionPlan }> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/versions/${versionId}/upscale`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_width: targetWidth,
      target_height: targetHeight,
      output_format: outputFormat,
      plan_choice: planChoice
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to upscale version' }));
    throw new Error(err.detail || 'Failed to start progressive upscale');
  }
  return res.json();
}

export async function updateVersionDecision(versionId: string, decision: 'accepted' | 'rejected'): Promise<void> {
  await fetch(`${BASE_URL}/versions/${versionId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision })
  });
}

export function subscribeJobEvents(
  jobId: string,
  onEvent: (status: JobStatus) => void,
  onComplete?: () => void
): () => void {
  const eventSource = new EventSource(`${BASE_URL}/jobs/${jobId}/events`);

  eventSource.onmessage = (event) => {
    try {
      const data: JobStatus = JSON.parse(event.data);
      onEvent(data);
      if (['completed', 'failed', 'cancelled'].includes(data.status)) {
        eventSource.close();
        if (onComplete) onComplete();
      }
    } catch (e) {
      console.error('Error parsing SSE event:', e);
    }
  };

  eventSource.onerror = () => {
    eventSource.close();
  };

  return () => eventSource.close();
}

export function getDownloadUrl(jobId: string, format?: string, quality?: number): string {
  let url = `${BASE_URL}/jobs/${jobId}/download`;
  const params = new URLSearchParams();
  if (format) params.append('format', format);
  if (quality) params.append('quality', quality.toString());
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

export function getPreviewUrl(jobId: string): string {
  return `${BASE_URL}/jobs/${jobId}/preview`;
}

export function getCropUrl(jobId: string, x: number, y: number, w: number, h: number): string {
  return `${BASE_URL}/jobs/${jobId}/crop?x=${x}&y=${y}&width=${w}&height=${h}`;
}

export async function uploadImagesBatch(files: File[]): Promise<ImageUploadResult[]> {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }
  const res = await fetch(`${BASE_URL}/images/batch`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    throw new Error('Failed to upload batch images');
  }
  return res.json();
}

export async function createJobsBatch(jobs: Array<{
  image_id: string;
  mode?: string;
  scale?: number;
  model?: string;
  preset?: string;
  output_format?: string;
  quality?: number;
}>): Promise<JobStatus[]> {
  const res = await fetch(`${BASE_URL}/jobs/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jobs })
  });
  if (!res.ok) {
    throw new Error('Failed to create batch upscale jobs');
  }
  return res.json();
}

export async function fetchQueueStatus(): Promise<{
  active_job_id: string | null;
  active_count: number;
  total_queued: number;
  queue: any[];
}> {
  const res = await fetch(`${BASE_URL}/jobs/queue`);
  if (!res.ok) {
    throw new Error('Failed to fetch queue status');
  }
  return res.json();
}

export async function clearQueue(): Promise<void> {
  await fetch(`${BASE_URL}/jobs/queue/clear`, { method: 'POST' });
}

export async function downloadBatchZip(jobIds: string[]): Promise<void> {
  const res = await fetch(`${BASE_URL}/jobs/batch/download-zip`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_ids: jobIds })
  });
  if (!res.ok) {
    throw new Error('Failed to download batch zip');
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'aether_batch_upscaled.zip';
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
