"""
API routes for the MapToPoster web service.
"""
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.schemas import (
    GenerateRequest,
    GenerateResponse,
    JobStatusResponse,
    ThemesResponse,
    PresetsResponse,
    DimensionPreset,
)
from core.config import settings
from core.jobs import create_job, get_job, submit_job, JobStatus
from core.generator import get_all_themes, generate_poster

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# Dimension presets
DIMENSION_PRESETS = [
    DimensionPreset(
        id="instagram",
        name="Instagram Post",
        width=3.6,
        height=3.6,
        description="1080 x 1080 px at 300 DPI"
    ),
    DimensionPreset(
        id="mobile",
        name="Mobile Wallpaper",
        width=3.6,
        height=6.4,
        description="1080 x 1920 px at 300 DPI"
    ),
    DimensionPreset(
        id="hd",
        name="HD Wallpaper",
        width=6.4,
        height=3.6,
        description="1920 x 1080 px at 300 DPI"
    ),
    DimensionPreset(
        id="4k",
        name="4K Wallpaper",
        width=12.8,
        height=7.2,
        description="3840 x 2160 px at 300 DPI"
    ),
    DimensionPreset(
        id="a4",
        name="A4 Print",
        width=8.3,
        height=11.7,
        description="2480 x 3508 px at 300 DPI"
    ),
    DimensionPreset(
        id="poster",
        name="Standard Poster",
        width=12,
        height=16,
        description="3600 x 4800 px at 300 DPI"
    ),
]


@router.get("/themes", response_model=ThemesResponse)
async def list_themes():
    """Get all available themes with their metadata and colors."""
    themes = get_all_themes()
    return ThemesResponse(themes=themes)


@router.get("/presets", response_model=PresetsResponse)
async def list_presets():
    """Get available dimension presets."""
    return PresetsResponse(presets=DIMENSION_PRESETS)


@router.post("/generate", response_model=GenerateResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def generate_poster_endpoint(request: Request, body: GenerateRequest):
    """
    Submit a poster generation job.

    Returns a job ID that can be used to check status and download the result.
    """
    # Validate theme exists
    themes = get_all_themes()
    theme_ids = [t["id"] for t in themes]
    if body.theme not in theme_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid theme '{body.theme}'. Available themes: {', '.join(theme_ids)}"
        )

    # Create job
    job = create_job(
        city=body.city,
        country=body.country,
        theme=body.theme,
        is_preview=body.preview,
    )

    # Submit to background thread
    submit_job(
        job,
        generate_poster,
        city=body.city,
        country=body.country,
        theme_name=body.theme,
        distance=body.options.distance,
        width=body.options.width,
        height=body.options.height,
        output_format=body.options.format,
        city_label=body.options.city_label,
        country_label=body.options.country_label,
        is_preview=body.preview,
    )

    # Estimate wait time (rough heuristic)
    estimated_wait = 15 if body.preview else 45

    return GenerateResponse(
        job_id=job.id,
        status=job.status.value,
        estimated_wait=estimated_wait,
    )


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Check the status of a generation job."""
    job = get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    response = JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
    )

    if job.status == JobStatus.COMPLETE and job.result_path:
        response.download_url = f"/api/download/{job.id}"
        response.expires_at = job.expires_at.isoformat()

    if job.status == JobStatus.ERROR:
        response.error = job.error

    return response


@router.get("/download/{job_id}")
async def download_poster(job_id: str):
    """Download a completed poster."""
    job = get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Job not complete")

    if not job.result_path or not os.path.exists(job.result_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    ext = os.path.splitext(job.result_path)[1].lower()
    media_types = {
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".pdf": "application/pdf",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    # Create filename for download
    filename = os.path.basename(job.result_path)

    return FileResponse(
        path=job.result_path,
        media_type=media_type,
        filename=filename,
    )
