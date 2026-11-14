"""FastAPI Gateway – accepts generation requests and returns job_ids."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from arq import create_pool
from arq.connections import RedisSettings

from app.models import GenerateRequest, GenerateResponse, JobResponse, JobStatus
from app.config import get_settings
from app.utils.seed import job_id_to_seed

settings = get_settings()
app = FastAPI(
    title="Symbolic MIDI Generation Service",
    version="0.1.0",
    description="Hierarchical Markov-based symbolic MIDI generator",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store for the minimal example.
# In production replace with Redis hashes or PostgreSQL.
_JOBS: dict[str, dict] = {}


async def get_redis():
    return await create_pool(RedisSettings.from_dsn(settings.redis_url))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "data_dir": settings.data_dir,
    }


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    job_id = str(uuid.uuid4())
    seed = req.seed if req.seed is not None else job_id_to_seed(job_id)

    _JOBS[job_id] = {
        "status": JobStatus.queued,
        "seed": seed,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request": req.model_dump(),
    }

    try:
        redis = await get_redis()
        await redis.enqueue_job(
            "generate_midi",
            job_id=job_id,
            bars=req.bars,
            style=req.style,
            seed=seed,
            bpm=req.bpm,
            model=req.model.value,
            include_drums=req.include_drums,
        )
    except Exception as e:
        # If Redis is down we still keep the job in "queued" so the
        # caller can see it; worker will pick it up when Redis recovers.
        _JOBS[job_id]["message"] = f"enqueue warning: {e}"

    return GenerateResponse(job_id=job_id, seed=seed, status=JobStatus.queued)


@app.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        # Also check filesystem for completed jobs (worker may have written)
        midi_path = Path(settings.data_dir) / f"{job_id}.mid"
        meta_path = Path(settings.data_dir) / f"{job_id}.json"
        if midi_path.exists():
            import json
            metrics = None
            if meta_path.exists():
                metrics = json.loads(meta_path.read_text())
            return JobResponse(
                job_id=job_id,
                status=JobStatus.completed,
                midi_url=f"/v1/download/{job_id}",
                metrics=metrics,
            )
        raise HTTPException(status_code=404, detail="Job not found")

    resp = JobResponse(
        job_id=job_id,
        status=job["status"],
        seed=job.get("seed"),
        message=job.get("message"),
        created_at=job.get("created_at"),
        finished_at=job.get("finished_at"),
        metrics=job.get("metrics"),
    )
    if job["status"] == JobStatus.completed:
        resp.midi_url = f"/v1/download/{job_id}"
    return resp


@app.get("/v1/download/{job_id}")
async def download(job_id: str):
    path = Path(settings.data_dir) / f"{job_id}.mid"
    if not path.exists():
        raise HTTPException(status_code=404, detail="MIDI file not ready")
    return FileResponse(
        path,
        media_type="audio/midi",
        filename=f"{job_id}.mid",
    )


# Helper used by the worker to update job state
def update_job(job_id: str, **kwargs):
    if job_id not in _JOBS:
        _JOBS[job_id] = {}
    _JOBS[job_id].update(kwargs)
