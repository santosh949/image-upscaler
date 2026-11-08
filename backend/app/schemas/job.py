from pydantic import BaseModel, Field
from typing import Optional, List

class JobCreateRequest(BaseModel):
    image_id: str
    mode: str = "upscale"
    scale: int = Field(default=4, ge=1, le=8)
    model: str = "realesrgan-x4plus"
    tile_size: int = 0
    denoise: Optional[str] = "off"
    output_format: str = "png"
    quality: int = Field(default=95, ge=1, le=100)
    preset: Optional[str] = None
    crop_region: Optional[List[int]] = None  # [x, y, width, height]
    plan_json: Optional[str] = None
    recommended_parameters: Optional[dict] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    stage: str
    progress: Optional[float] = None
    message: Optional[str] = None
    result_available: bool
    warnings: List[str] = []
    error: Optional[str] = None
    scale: Optional[int] = 4
    mode: Optional[str] = "upscale"
    output_format: Optional[str] = "png"
    created_at: Optional[float] = None

class ImageUploadResponse(BaseModel):
    image_id: str
    filename: str
    width: int
    height: int
    format: str
    size_bytes: int

class BatchJobItem(BaseModel):
    image_id: str
    mode: str = "upscale"
    scale: int = Field(default=4, ge=1, le=8)
    model: str = "realesrgan-x4plus"
    preset: Optional[str] = None
    output_format: str = "png"
    quality: int = Field(default=95, ge=1, le=100)

class BatchJobCreateRequest(BaseModel):
    jobs: List[BatchJobItem]

class BatchZipRequest(BaseModel):
    job_ids: List[str]

class QueueStatusResponse(BaseModel):
    active_job_id: Optional[str] = None
    active_count: int
    total_queued: int
    queue: List[dict]
