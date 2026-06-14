"""
Audio mixer: combines voice (foreground) + ambience (background) into a single MP3.
Uses pydub with imageio-ffmpeg for the codec backend — no system ffmpeg required.
"""

import os
from pathlib import Path

import imageio_ffmpeg
from pydub import AudioSegment

from app.core.logging import get_logger

logger = get_logger(__name__)

# Point pydub at the bundled ffmpeg binary from imageio-ffmpeg.
# Also set ffprobe to the same binary — imageio-ffmpeg ships ffmpeg only,
# and pydub calls ffprobe to detect format unless we pass format= explicitly.
_ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
AudioSegment.converter = _ffmpeg_bin
AudioSegment.ffprobe = _ffmpeg_bin
os.environ["PATH"] = str(Path(_ffmpeg_bin).parent) + os.pathsep + os.environ.get("PATH", "")


def mix_audio(
    voice_path: str,
    ambience_path: str,
    output_path: str,
    ambience_volume_db: float = -12.0,
    voice_volume_db: float = 0.0,
) -> tuple[str, float]:
    """
    Mix voice and ambience audio files.

    Ambience is looped to match or exceed voice duration, then trimmed.
    Returns (output_path, duration_seconds).
    """
    logger.info(f"Mixing audio | voice={voice_path} | ambience={ambience_path}")

    # Pass codec= to skip pydub's ffprobe call — pydub only skips mediainfo_json
    # when codec is set, not when format is set (checked against pydub source).
    voice = AudioSegment.from_file(voice_path, format="mp3", codec="mp3")
    ambience = AudioSegment.from_file(ambience_path, format="mp3", codec="mp3")

    # Apply volume adjustments
    voice = voice + voice_volume_db
    ambience = ambience + ambience_volume_db

    # Loop ambience until it's at least as long as voice
    if len(ambience) < len(voice):
        repeats = (len(voice) // len(ambience)) + 2
        ambience = ambience * repeats

    # Trim ambience to exactly voice length + short tail for soft ending
    tail_ms = 400
    ambience = ambience[: len(voice) + tail_ms]

    # Gentle fade-in; very short fade-out so music plays through entire speech
    ambience = ambience.fade_in(1200).fade_out(tail_ms)

    # Overlay: voice on top of ambience
    mixed = ambience.overlay(voice)

    # Normalize to prevent clipping
    mixed = mixed.normalize()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    mixed.export(output_path, format="mp3", bitrate="192k")

    duration_seconds = len(mixed) / 1000.0
    logger.info(f"Mixed audio saved: {output_path} | duration={duration_seconds:.1f}s")
    return output_path, duration_seconds


def get_audio_duration(audio_path: str) -> float:
    """Return duration in seconds for an audio file."""
    segment = AudioSegment.from_file(audio_path, format="mp3", codec="mp3")
    return len(segment) / 1000.0
