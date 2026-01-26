"""
Job management for poster generation.
"""
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading

from core.config import settings


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class Job:
    """Represents a poster generation job."""
    id: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    result_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=settings.job_expiry_hours))

    # Job parameters (for tracking)
    city: str = ""
    country: str = ""
    theme: str = ""
    is_preview: bool = False


# In-memory job store
_jobs: Dict[str, Job] = {}
_jobs_lock = threading.Lock()

# Thread pool for background processing
_executor = ThreadPoolExecutor(max_workers=settings.max_workers)


def create_job(city: str, country: str, theme: str, is_preview: bool = False) -> Job:
    """Create a new job and return it."""
    job_id = str(uuid.uuid4())[:8]
    job = Job(
        id=job_id,
        city=city,
        country=country,
        theme=theme,
        is_preview=is_preview,
    )

    with _jobs_lock:
        _jobs[job_id] = job

    return job


def get_job(job_id: str) -> Optional[Job]:
    """Get a job by ID."""
    with _jobs_lock:
        return _jobs.get(job_id)


def update_job(
    job_id: str,
    status: Optional[JobStatus] = None,
    progress: Optional[int] = None,
    result_path: Optional[str] = None,
    error: Optional[str] = None,
) -> Optional[Job]:
    """Update a job's status."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return None

        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if result_path is not None:
            job.result_path = result_path
        if error is not None:
            job.error = error

        return job


def submit_job(job: Job, task_func, *args, **kwargs):
    """Submit a job to the thread pool for processing."""
    _executor.submit(task_func, job, *args, **kwargs)


def cleanup_expired_jobs():
    """Remove expired jobs and their files."""
    now = datetime.utcnow()
    expired_ids = []

    with _jobs_lock:
        for job_id, job in _jobs.items():
            if job.expires_at < now:
                expired_ids.append(job_id)

                # Clean up file if it exists
                if job.result_path and os.path.exists(job.result_path):
                    try:
                        os.remove(job.result_path)
                    except OSError:
                        pass

        # Remove expired jobs from store
        for job_id in expired_ids:
            del _jobs[job_id]

    if expired_ids:
        print(f"Cleaned up {len(expired_ids)} expired jobs")


def get_active_job_count() -> int:
    """Get count of active (non-expired) jobs."""
    with _jobs_lock:
        return len(_jobs)
