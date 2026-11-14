# Symbolic MIDI Generation Service

Production-ready asynchronous service for hierarchical Markov-based symbolic MIDI generation.

Inspired by academic manuscripts covering Markov chains → hierarchical models (HHMM), this system implements a practical engineering simplification:

- **Macro layer**: Section-level transition matrix (intro → verse → chorus → bridge)
- **Micro layer**: Note / rhythm generation with deterministic seeds
- **Rhythm layer**: Independent stochastic groove generation (beatstoch)
- **API**: FastAPI + arq + Redis (async job queue)
- **Export**: Standard `.mid` files via symusic

## Features

- Asynchronous generation (`POST /v1/generate` → job_id)
- Deterministic reproducibility via seed
- Hierarchical structure planning
- Automatic evaluation metrics (cross-entropy, rhythmic entropy, interval KL)
- Docker Compose one-command deployment
- Graceful fallbacks when optional heavy dependencies are missing

## Quick Start (Local)

```bash
# 1. Create virtualenv
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Redis (required)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 4. Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. In another terminal, start worker
arq app.worker.WorkerSettings
```

## Docker Compose (Recommended)

```bash
docker compose -f docker/docker-compose.prod.yml up --build
```

API will be available at `http://localhost:8000`.

## API Usage

### Generate

```bash
curl -X POST http://localhost:8000/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "bars": 16,
    "style": "rnb",
    "bpm": 92,
    "model": "hierarchical",
    "seed": 42
  }'
```

Response:
```json
{
  "job_id": "a1b2c3d4-...",
  "seed": 42,
  "status": "queued"
}
```

### Poll Job

```bash
curl http://localhost:8000/v1/jobs/{job_id}
```

When completed you receive a download URL for the `.mid` file and evaluation metrics.

## Project Layout

```
app/
├── main.py                 # FastAPI gateway
├── worker.py               # arq generation worker
├── models.py               # Pydantic request/response schemas
├── config.py               # Settings
├── generation/
│   ├── structure.py        # Macro section Markov planner
│   ├── markov_engine.py    # Micro note generation + seed
│   ├── rhythm.py           # beatstoch wrapper / fallback
│   └── midi_parser.py      # symusic helpers
├── evaluation/
│   └── metrics.py          # Cross-entropy, IOI entropy, interval KL
└── utils/
    └── seed.py
docker/
├── Dockerfile
└── docker-compose.prod.yml
```

## Design Notes

- Generation is **always asynchronous**. Even fast Markov sampling benefits from queue isolation when adding evaluation, style calibration, or multi-model routing.
- Seeds are first-class: every job can be exactly reproduced.
- The system deliberately outputs pure symbolic MIDI. Audio rendering is left to downstream DAWs / VSTs.
- Hierarchical structure is an engineering simplification of HHMM: two loosely coupled Markov layers instead of a fully coupled hierarchical model. This is far cheaper to implement and still produces audible long-range form.

## Limitations (Honest)

- Output is stylistic raw material / creative draft, not production-ready arrangement.
- Quality is heavily dependent on the training corpus you supply.
- Automatic metrics (cross-entropy etc.) are useful proxies but do not equal human musical judgment.

## License

MIT
