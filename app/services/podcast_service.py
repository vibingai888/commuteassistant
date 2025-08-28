"""
Podcast generation service that orchestrates script generation and TTS
"""

import json
import time
from typing import Any, Dict, List

from fastapi import HTTPException

from app.config import config
from app.services.script_service import generate_podcast_script, generate_podcast_script_chunked
from app.services.tts_service import synthesize_audio_multi_speaker, tts_for_turns
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


def generate_full_podcast(topic: str, minutes: int) -> Dict[str, Any]:
    """
    Generate a complete podcast with script and audio

    Args:
        topic: Podcast topic
        minutes: Duration in minutes

    Returns:
        Dictionary with audio_file_path, mime_type, duration_seconds, and word_count
    """
    logger.info(f"[Podcast] Starting full podcast generation for topic: '{topic}' ({minutes} minutes)")

    try:
        # Generate script
        start_time = time.perf_counter()
        script_json = generate_podcast_script(topic, minutes)
        script_time = time.perf_counter() - start_time

        # Parse script to get word count
        from app.services.script_service import clean_json_string, validate_script_json

        cleaned_script = clean_json_string(script_json)

        # If cleaned_script is already a dict, use it directly
        if isinstance(cleaned_script, dict):
            script_obj = cleaned_script
        else:
            # Otherwise, parse it as JSON
            script_obj = json.loads(cleaned_script)

        validate_script_json(script_obj)

        turns = script_obj["multiSpeakerMarkup"]["turns"]
        word_count = sum(len(turn["text"].split()) for turn in turns)

        logger.info(f"[Podcast] Script generated in {script_time:.2f}s ({word_count} words)")

        # Generate audio
        audio_start = time.perf_counter()

        # Create a unique filename for this podcast
        import uuid

        podcast_id = str(uuid.uuid4())
        audio_filename = f"{podcast_id}.wav"

        # Ensure the audio directory exists
        from pathlib import Path

        audio_dir = Path("storage/podcasts/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Generate audio directly to the final location
        output_path = audio_dir / audio_filename

        try:
            synthesize_audio_multi_speaker(script_json, str(output_path))
            audio_time = time.perf_counter() - audio_start

            # Get file size for duration calculation
            file_size = output_path.stat().st_size

            # Calculate approximate duration (WAV at 24kHz, 16-bit, mono)
            # 24kHz * 2 bytes * 1 channel = 48KB/s
            duration_seconds = file_size / 48000

            logger.info(f"[Podcast] Audio generated in {audio_time:.2f}s ({file_size} bytes, ~{duration_seconds:.1f}s)")
            logger.info(f"[Podcast] Total generation time: {time.perf_counter() - start_time:.2f}s")

            return {
                "podcast_id": podcast_id,
                "audio_file_path": str(output_path),
                "mime_type": "audio/wav",
                "duration_seconds": duration_seconds,
                "word_count": word_count,
            }

        except Exception as e:
            # Clean up the file if generation failed
            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass
            raise e

    except Exception as e:
        logger.error(f"[Podcast] Failed to generate podcast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Podcast generation failed: {str(e)}")


def generate_chunked_podcast_script(topic: str, minutes: int) -> Dict[str, Any]:
    """
    Generate a chunked podcast script

    Args:
        topic: Podcast topic
        minutes: Duration in minutes

    Returns:
        Dictionary with segments and total word count
    """
    logger.info(f"[Podcast] Generating chunked script for topic: '{topic}' ({minutes} minutes)")

    try:
        # Generate chunked script
        start_time = time.perf_counter()
        chunked_data = generate_podcast_script_chunked(topic, minutes, words_per_chunk=config.TARGET_CHUNK_WORDS)
        generation_time = time.perf_counter() - start_time

        # Calculate total word count
        total_words = 0
        for segment in chunked_data["segments"]:
            turns = segment["multiSpeakerMarkup"]["turns"]
            segment_words = sum(len(turn["text"].split()) for turn in turns)
            total_words += segment_words

        logger.info(
            f"[Podcast] Chunked script generated in {generation_time:.2f}s ({len(chunked_data['segments'])} segments, {total_words} words)"
        )

        return {"segments": chunked_data["segments"], "total_words": total_words}

    except Exception as e:
        logger.error(f"[Podcast] Failed to generate chunked script: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


def generate_tts_segment(segment_id: int, turns: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate TTS for a specific segment

    Args:
        segment_id: Segment identifier
        turns: List of speaker turns

    Returns:
        Dictionary with segment_id, base64 audio, and mime type
    """
    logger.info(f"[Podcast] Generating TTS for segment {segment_id} ({len(turns)} turns)")

    try:
        start_time = time.perf_counter()
        tts_result = tts_for_turns(turns)
        generation_time = time.perf_counter() - start_time

        logger.info(f"[Podcast] TTS for segment {segment_id} generated in {generation_time:.2f}s")

        return {"segment_id": segment_id, "base64": tts_result["base64"], "mime": tts_result["mime"]}

    except Exception as e:
        logger.error(f"[Podcast] Failed to generate TTS for segment {segment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
