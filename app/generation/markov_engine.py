"""Micro-level note generation with deterministic seed.

Falls back to a pure-Python first-order Markov chain when Subsequence
is not installed. The interface stays the same so the rest of the
pipeline does not need to change.
"""

from __future__ import annotations
import numpy as np
from typing import List, Tuple, Dict, Optional


# Very small illustrative pitch transition matrix (MIDI note numbers).
# In production this should be trained on a real corpus via symusic.
DEFAULT_PITCH_TRANSITIONS: Dict[int, Dict[int, float]] = {
    60: {62: 0.35, 64: 0.25, 67: 0.20, 59: 0.10, 60: 0.10},  # C
    62: {60: 0.25, 64: 0.30, 65: 0.20, 67: 0.15, 62: 0.10},  # D
    64: {62: 0.20, 65: 0.25, 67: 0.30, 60: 0.15, 64: 0.10},  # E
    65: {64: 0.25, 67: 0.30, 69: 0.20, 62: 0.15, 65: 0.10},  # F
    67: {65: 0.20, 69: 0.25, 72: 0.15, 64: 0.20, 67: 0.20},  # G
    69: {67: 0.30, 72: 0.25, 65: 0.20, 69: 0.15, 71: 0.10},  # A
    71: {69: 0.35, 72: 0.30, 67: 0.20, 71: 0.15},            # B
    72: {71: 0.25, 69: 0.25, 67: 0.25, 60: 0.15, 72: 0.10},  # C'
}


class SimpleMarkovMelody:
    """Deterministic first-order pitch Markov chain."""

    def __init__(self, seed: int = 42, transitions: Optional[Dict] = None):
        self.rng = np.random.default_rng(seed)
        self.trans = transitions or DEFAULT_PITCH_TRANSITIONS
        self.pitches = sorted(self.trans.keys())

    def _sample_next(self, current: int) -> int:
        if current not in self.trans:
            current = self.rng.choice(self.pitches)
        choices = list(self.trans[current].keys())
        probs = np.array(list(self.trans[current].values()), dtype=float)
        probs /= probs.sum()
        return int(self.rng.choice(choices, p=probs))

    def generate(
        self,
        n_notes: int,
        start_pitch: int = 60,
        duration_ticks: int = 480,  # quarter note @ 480 PPQ
    ) -> List[Tuple[int, int, int]]:
        """Return list of (pitch, start_tick, duration_ticks)."""
        notes = []
        pitch = start_pitch
        tick = 0
        for _ in range(n_notes):
            notes.append((pitch, tick, duration_ticks))
            pitch = self._sample_next(pitch)
            # simple rhythmic variation
            if self.rng.random() < 0.15:
                tick += duration_ticks // 2
            else:
                tick += duration_ticks
        return notes


def generate_melody_for_sections(
    section_plan: List[str],
    seed: int,
    notes_per_bar: int = 4,
    ppq: int = 480,
) -> List[Tuple[int, int, int]]:
    """Generate a continuous melody conditioned lightly on section type."""
    engine = SimpleMarkovMelody(seed=seed)
    all_notes: List[Tuple[int, int, int]] = []
    tick = 0
    bar_ticks = ppq * 4  # 4/4

    # Different average pitch centres per section (very crude conditioning)
    section_centres = {
        "intro": 60,
        "verse": 62,
        "chorus": 67,
        "bridge": 65,
        "outro": 60,
    }

    for bar_idx, section in enumerate(section_plan):
        centre = section_centres.get(section, 60)
        # generate a few notes for this bar
        local_engine = SimpleMarkovMelody(seed=seed + bar_idx)
        local_notes = local_engine.generate(
            n_notes=notes_per_bar,
            start_pitch=centre,
            duration_ticks=bar_ticks // notes_per_bar,
        )
        for pitch, local_start, dur in local_notes:
            all_notes.append((pitch, tick + local_start, dur))
        tick += bar_ticks

    return all_notes
