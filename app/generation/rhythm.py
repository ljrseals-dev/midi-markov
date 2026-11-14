"""Rhythm / groove layer.

Prefers beatstoch when available; otherwise falls back to a simple
probabilistic drum pattern with micro-timing.
"""

from __future__ import annotations
from typing import Optional, List, Tuple
import numpy as np


def generate_groove(
    bpm: float = 90.0,
    bars: int = 16,
    style: str = "rnb",
    seed: int = 42,
    humanize: float = 0.4,
) -> List[Tuple[int, int, int, int]]:
    """
    Return list of drum hits: (pitch, start_tick, duration_ticks, velocity).
    Uses General MIDI drum map.
    """
    try:
        from beatstoch import generate_stochastic_pattern
        # beatstoch returns a mido.MidiFile; we convert later if needed
        # For simplicity we still use the pure fallback path here so the
        # service stays dependency-light out of the box.
        # Uncomment the following block once beatstoch is installed:
        #
        # mid = generate_stochastic_pattern(
        #     bpm=bpm, bars=bars, style=style if style in ("house","breaks","rock") else "generic",
        #     seed=seed, humanize=humanize, groove_intensity=0.7
        # )
        # return _mido_to_hits(mid)
        pass
    except ImportError:
        pass

    return _fallback_groove(bpm=bpm, bars=bars, style=style, seed=seed, humanize=humanize)


def _fallback_groove(
    bpm: float,
    bars: int,
    style: str,
    seed: int,
    humanize: float,
) -> List[Tuple[int, int, int, int]]:
    """Simple probabilistic 4/4 groove with micro-timing."""
    rng = np.random.default_rng(seed)
    ppq = 480
    bar_ticks = ppq * 4
    hits: List[Tuple[int, int, int, int]] = []

    # GM drum map
    KICK = 36
    SNARE = 38
    CHH = 42
    OHH = 46
    RIM = 37

    for bar in range(bars):
        base = bar * bar_ticks
        # Kick on 1 and 3 (with occasional variation)
        for beat in (0, 2):
            if rng.random() > 0.08:
                offset = int(rng.normal(0, 8 * humanize)) if humanize else 0
                start = max(0, base + beat * ppq + offset)
                vel = int(rng.integers(90, 115))
                hits.append((KICK, start, ppq // 4, vel))

        # Snare on 2 and 4
        for beat in (1, 3):
            if rng.random() > 0.05:
                offset = int(rng.normal(0, 6 * humanize)) if humanize else 0
                start = max(0, base + beat * ppq + offset)
                vel = int(rng.integers(85, 110))
                hits.append((SNARE, start, ppq // 4, vel))

        # Closed hats on 8ths
        for eighth in range(8):
            if rng.random() > 0.12:
                offset = int(rng.normal(0, 4 * humanize)) if humanize else 0
                start = max(0, base + eighth * (ppq // 2) + offset)
                vel = int(rng.integers(55, 90))
                hits.append((CHH, start, ppq // 8, vel))

        # Occasional open hat on the "and" of 4
        if rng.random() < 0.35:
            hits.append((OHH, base + 7 * (ppq // 2), ppq // 4, int(rng.integers(60, 85))))

    # sort by time
    hits.sort(key=lambda x: x[1])
    return hits
