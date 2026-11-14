"""Helpers for building and writing MIDI with symusic (preferred) or mido fallback."""

from __future__ import annotations
from typing import List, Tuple, Optional
from pathlib import Path


def notes_to_score(
    melody_notes: List[Tuple[int, int, int]],
    drum_hits: Optional[List[Tuple[int, int, int, int]]] = None,
    bpm: float = 90.0,
    ppq: int = 480,
):
    """
    Build a Score from note lists.
    melody_notes: (pitch, start_tick, duration_ticks)
    drum_hits: (pitch, start_tick, duration_ticks, velocity)
    """
    try:
        import symusic
        from symusic import Score, Track, Note, Tempo

        score = Score(ttype="tick")
        score.ticks_per_quarter = ppq
        score.tempos.append(Tempo(time=0, qpm=bpm))

        # Melody track
        mel_track = Track(program=0, is_drum=False, name="Melody")
        for pitch, start, dur in melody_notes:
            mel_track.notes.append(
                Note(time=start, duration=dur, pitch=pitch, velocity=90)
            )
        score.tracks.append(mel_track)

        # Drum track
        if drum_hits:
            drum_track = Track(program=0, is_drum=True, name="Drums")
            for pitch, start, dur, vel in drum_hits:
                drum_track.notes.append(
                    Note(time=start, duration=dur, pitch=pitch, velocity=vel)
                )
            score.tracks.append(drum_track)

        return score
    except ImportError:
        return _mido_fallback(melody_notes, drum_hits, bpm, ppq)


def _mido_fallback(melody_notes, drum_hits, bpm, ppq):
    import mido
    mid = mido.MidiFile(ticks_per_beat=ppq)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

    events = []
    for pitch, start, dur in melody_notes:
        events.append((start, "note_on", pitch, 90, 0))
        events.append((start + dur, "note_off", pitch, 0, 0))
    if drum_hits:
        for pitch, start, dur, vel in drum_hits:
            events.append((start, "note_on", pitch, vel, 9))  # channel 10
            events.append((start + dur, "note_off", pitch, 0, 9))

    events.sort(key=lambda x: x[0])
    last = 0
    for abs_tick, typ, pitch, vel, ch in events:
        abs_tick = max(0, abs_tick)
        delta = max(0, abs_tick - last)
        track.append(mido.Message(typ, note=pitch, velocity=vel, time=delta, channel=ch))
        last = abs_tick
    return mid


def merge_scores(score_a, score_b):
    """Placeholder – currently we build everything in one pass."""
    return score_a


def write_midi(score, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(score, "dump_midi"):
        score.dump_midi(str(path))
    else:
        # mido
        score.save(str(path))
    return path
