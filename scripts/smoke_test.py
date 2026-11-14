#!/usr/bin/env python3
"""Local smoke test that does not require Redis or the full service."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.generation.structure import SectionMarkov
from app.generation.markov_engine import generate_melody_for_sections
from app.generation.rhythm import generate_groove
from app.generation.midi_parser import notes_to_score, write_midi
from app.evaluation.metrics import compute_metrics


def main():
    seed = 42
    bars = 8
    bpm = 92.0

    print("1. Planning sections...")
    planner = SectionMarkov(style="rnb", seed=seed)
    plan = planner.plan(bars)
    print(f"   Section plan: {plan}")

    print("2. Generating melody...")
    melody = generate_melody_for_sections(plan, seed=seed)
    print(f"   Generated {len(melody)} notes")

    print("3. Generating groove...")
    drums = generate_groove(bpm=bpm, bars=bars, style="rnb", seed=seed)
    print(f"   Generated {len(drums)} drum hits")

    print("4. Building MIDI...")
    score = notes_to_score(melody, drums, bpm=bpm)
    out = Path("data/smoke_test.mid")
    write_midi(score, out)
    print(f"   Wrote {out}")

    print("5. Metrics...")
    metrics = compute_metrics(melody)
    for k, v in metrics.items():
        print(f"   {k}: {v}")

    print("\nSmoke test passed.")


if __name__ == "__main__":
    main()
