"""Seed utilities for reproducibility."""

import hashlib


def job_id_to_seed(job_id: str) -> int:
    """Derive a stable 32-bit seed from a UUID/job_id string."""
    h = hashlib.sha256(job_id.encode("utf-8")).hexdigest()
    return int(h[:8], 16)
