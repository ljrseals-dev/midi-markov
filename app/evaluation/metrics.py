"""Automatic evaluation metrics for generated MIDI.

These are symbolic-domain proxies. They do not equal human musical quality.
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any
import numpy as np
from collections import Counter


def _extract_pitches(notes: List[Tuple[int, int, int]]) -> List[int]:
    return [n[0] for n in notes]


def _extract_iois(notes: List[Tuple[int, int, int]]) -> np.ndarray:
    """Inter-onset intervals in ticks."""
    starts = sorted(n[1] for n in notes)
    if len(starts) < 2:
        return np.array([])
    return np.diff(starts)


def pitch_entropy(notes: List[Tuple[int, int, int]]) -> float:
    pitches = _extract_pitches(notes)
    if not pitches:
        return 0.0
    counts = Counter(pitches)
    total = sum(counts.values())
    probs = np.array([c / total for c in counts.values()])
    return float(-np.sum(probs * np.log2(probs + 1e-12)))


def rhythmic_entropy(notes: List[Tuple[int, int, int]]) -> float:
    iois = _extract_iois(notes)
    if len(iois) == 0:
        return 0.0
    # quantize to nearest 60 ticks (~1/8 note at 480 PPQ) for stability
    quantized = np.round(iois / 60) * 60
    counts = Counter(quantized.astype(int))
    total = sum(counts.values())
    probs = np.array([c / total for c in counts.values()])
    return float(-np.sum(probs * np.log2(probs + 1e-12)))


def interval_histogram(notes: List[Tuple[int, int, int]]) -> np.ndarray:
    pitches = _extract_pitches(notes)
    if len(pitches) < 2:
        return np.zeros(25)
    intervals = np.diff(pitches)
    # map -12..+12
    hist = np.zeros(25)
    for iv in intervals:
        idx = int(np.clip(iv + 12, 0, 24))
        hist[idx] += 1
    if hist.sum() > 0:
        hist /= hist.sum()
    return hist


def kl_divergence(p: np.ndarray, q: np.ndarray, eps: float = 1e-8) -> float:
    p = p + eps
    q = q + eps
    p /= p.sum()
    q /= q.sum()
    return float(np.sum(p * np.log(p / q)))


def compute_metrics(
    melody_notes: List[Tuple[int, int, int]],
    reference_interval_hist: np.ndarray | None = None,
) -> Dict[str, Any]:
    """Compute a small set of automatic metrics."""
    metrics = {
        "n_notes": len(melody_notes),
        "pitch_entropy": round(pitch_entropy(melody_notes), 4),
        "rhythmic_entropy": round(rhythmic_entropy(melody_notes), 4),
    }

    hist = interval_histogram(melody_notes)
    metrics["interval_hist_entropy"] = round(float(-np.sum(hist * np.log2(hist + 1e-12))), 4)

    if reference_interval_hist is not None:
        metrics["interval_kl"] = round(kl_divergence(hist, reference_interval_hist), 4)

    return metrics
