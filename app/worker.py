"""arq Generation Worker."""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from arq.connections import RedisSettings

from app.config import get_settings
from app.generation.structure import SectionMarkov
from app.generation.markov_engine import generate_melody_for_sections
from app.generation.rhythm import generate_groove
from app.generation.midi_parser import notes_to_score, write_midi
from app.evaluation.metrics import compute_metrics
from app.models import JobStatus

settings = get_settings()


async def generate_midi(
    ctx,
    job_id: str,
    bars: int,
    style: str,
    seed: int,
    bpm: float,
    model: str,
    include_drums: bool = True,
):
    """Main generation task executed by the worker."""
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Mark running (best-effort; main process may not see it in this minimal example)
    try:
        from app.main import update_job
        update_job(job_id, status=JobStatus.running)
    except Exception:
        pass

    try:
        # 1. Macro structure
        planner = SectionMarkov(style=style, seed=seed)
        section_plan = planner.plan(total_bars=bars)

        # 2. Micro melody
        melody_notes = generate_melody_for_sections(
            section_plan=section_plan,
            seed=seed,
            notes_per_bar=4,
        )

        # 3. Rhythm layer
        drum_hits = None
        if include_drums:
            drum_hits = generate_groove(
                bpm=bpm,
                bars=bars,
                style=style,
                seed=seed + 1,
                humanize=0.35,
            )

        # 4. Build & write MIDI
        score = notes_to_score(melody_notes, drum_hits, bpm=bpm)
        out_path = data_dir / f"{job_id}.mid"
        write_midi(score, out_path)

        # 5. Automatic metrics
        metrics = compute_metrics(melody_notes)
        metrics["bars"] = bars
        metrics["style"] = style
        metrics["model"] = model
        metrics["seed"] = seed
        metrics["bpm"] = bpm
        metrics["sections"] = section_plan[:16]  # preview

        meta_path = data_dir / f"{job_id}.json"
        meta_path.write_text(json.dumps(metrics, indent=2))

        # Update status
        try:
            from app.main import update_job
            update_job(
                job_id,
                status=JobStatus.completed,
                finished_at=datetime.now(timezone.utc).isoformat(),
                metrics=metrics,
                midi_path=str(out_path),
            )
        except Exception:
            pass

        return {"job_id": job_id, "path": str(out_path), "metrics": metrics}

    except Exception as e:
        try:
            from app.main import update_job
            update_job(
                job_id,
                status=JobStatus.failed,
                message=str(e),
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception:
            pass
        raise


class WorkerSettings:
    functions = [generate_midi]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 4
    job_timeout = 300  # 5 minutes
