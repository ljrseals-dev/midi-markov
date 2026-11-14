"""Macro-level section planner (engineering simplification of HHMM)."""

from __future__ import annotations
import numpy as np
from typing import List, Dict


# Practical transition matrices. These are illustrative; in production
# they should be learned from annotated corpus.
SECTION_TRANSITIONS: Dict[str, Dict[str, Dict[str, float]]] = {
    "rnb": {
        "intro":  {"verse": 0.75, "chorus": 0.25},
        "verse":  {"verse": 0.35, "chorus": 0.50, "bridge": 0.15},
        "chorus": {"verse": 0.25, "chorus": 0.40, "bridge": 0.25, "outro": 0.10},
        "bridge": {"chorus": 0.70, "verse": 0.30},
        "outro":  {"outro": 1.0},
    },
    "pop": {
        "intro":  {"verse": 0.80, "chorus": 0.20},
        "verse":  {"verse": 0.30, "chorus": 0.60, "bridge": 0.10},
        "chorus": {"verse": 0.20, "chorus": 0.45, "bridge": 0.25, "outro": 0.10},
        "bridge": {"chorus": 0.85, "verse": 0.15},
        "outro":  {"outro": 1.0},
    },
    "default": {
        "intro":  {"verse": 0.70, "chorus": 0.30},
        "verse":  {"verse": 0.40, "chorus": 0.45, "bridge": 0.15},
        "chorus": {"verse": 0.30, "chorus": 0.40, "bridge": 0.20, "outro": 0.10},
        "bridge": {"chorus": 0.75, "verse": 0.25},
        "outro":  {"outro": 1.0},
    },
}


class SectionMarkov:
    """Simple first-order Markov chain over song sections."""

    def __init__(self, style: str = "rnb", seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.trans = SECTION_TRANSITIONS.get(style, SECTION_TRANSITIONS["default"])

    def plan(self, total_bars: int, section_length: int = 4) -> List[str]:
        """Return a list of section labels, one per bar."""
        current = "intro"
        plan: List[str] = []
        remaining = total_bars

        while remaining > 0:
            length = min(section_length, remaining)
            # slight length variation
            if remaining > section_length and self.rng.random() < 0.25:
                length = min(section_length + 2, remaining)

            plan.extend([current] * length)
            remaining -= length

            next_states = list(self.trans[current].keys())
            probs = np.array(list(self.trans[current].values()), dtype=float)
            probs /= probs.sum()
            current = self.rng.choice(next_states, p=probs)

        return plan

    def section_boundaries(self, plan: List[str]) -> List[tuple[str, int, int]]:
        """Return (section_name, start_bar, end_bar) inclusive."""
        if not plan:
            return []
        boundaries = []
        start = 0
        current = plan[0]
        for i, s in enumerate(plan[1:], 1):
            if s != current:
                boundaries.append((current, start, i - 1))
                start = i
                current = s
        boundaries.append((current, start, len(plan) - 1))
        return boundaries
