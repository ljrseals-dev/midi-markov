from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class ModelType(str, Enum):
    hierarchical = "hierarchical"
    pure_markov = "pure_markov"


class GenerateRequest(BaseModel):
    bars: int = Field(16, ge=4, le=64, description="Total number of bars to generate")
    style: str = Field("rnb", description="Style key for section transitions and rhythm")
    bpm: float = Field(90.0, ge=40.0, le=200.0)
    model: ModelType = ModelType.hierarchical
    seed: Optional[int] = Field(None, description="If omitted, derived from job_id")
    include_drums: bool = True


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    seed: Optional[int] = None
    message: Optional[str] = None
    midi_url: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    finished_at: Optional[str] = None


class GenerateResponse(BaseModel):
    job_id: str
    seed: int
    status: JobStatus = JobStatus.queued
