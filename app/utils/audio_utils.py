"""
Audio processing utilities
"""

import base64
import io
import wave
from typing import Union


def create_wav_bytes(pcm_data: Union[bytes, bytearray], channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bytes:
    """
    Convert PCM audio data to WAV format

    Args:
        pcm_data: Raw PCM audio data
        channels: Number of audio channels
        rate: Sample rate in Hz
        sample_width: Sample width in bytes

    Returns:
        WAV format audio data as bytes
    """
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(rate)
            wav_file.writeframes(pcm_data)

        return wav_buffer.getvalue()


def base64_to_wav(base64_data: str, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bytes:
    """
    Convert base64 encoded WAV data back to WAV format

    Args:
        base64_data: Base64 encoded WAV audio data
        channels: Number of audio channels (unused, kept for compatibility)
        rate: Sample rate in Hz (unused, kept for compatibility)
        sample_width: Sample width in bytes (unused, kept for compatibility)

    Returns:
        WAV format audio data as bytes
    """
    try:
        wav_data = base64.b64decode(base64_data)
        # Validate that it's actually WAV data
        if not wav_data.startswith(b"RIFF") or not wav_data[8:12] == b"WAVE":
            raise ValueError("Invalid WAV data")
        return wav_data
    except Exception as e:
        raise ValueError(f"Failed to decode base64 WAV data: {e}")


def get_audio_duration(
    audio_data: Union[bytes, bytearray], channels: int = 1, rate: int = 24000, sample_width: int = 2
) -> float:
    """
    Calculate duration of audio data in seconds

    Args:
        audio_data: Raw audio data
        channels: Number of audio channels
        rate: Sample rate in Hz
        sample_width: Sample width in bytes

    Returns:
        Duration in seconds
    """
    if not audio_data:
        return 0.0

    # For WAV files, try to parse the header first
    if audio_data.startswith(b"RIFF") and audio_data[8:12] == b"WAVE":
        try:
            with io.BytesIO(audio_data) as wav_buffer:
                with wave.open(wav_buffer, "rb") as wav_file:
                    frames = wav_file.getnframes()
                    framerate = wav_file.getframerate()
                    return frames / framerate
        except Exception:
            # If WAV parsing fails, raise an exception for invalid WAV data
            raise ValueError("Invalid WAV data format")

    # For raw PCM data, validate that the data length makes sense
    if len(audio_data) % sample_width != 0:
        raise ValueError("Invalid audio data length for given sample width")

    if len(audio_data) % (sample_width * channels) != 0:
        raise ValueError("Invalid audio data length for given channels and sample width")

    # For raw PCM data or fallback
    total_samples = len(audio_data) // sample_width
    samples_per_channel = total_samples // channels
    duration = samples_per_channel / rate

    return duration


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to MM:SS format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 0:
        return "00:00"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    return f"{minutes:02d}:{remaining_seconds:02d}"
