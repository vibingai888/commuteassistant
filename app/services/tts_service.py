"""
Text-to-Speech service using Google Gemini AI
"""

import base64
import time
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from app.config import config
from app.utils.logging_utils import get_logger
from app.utils.audio_utils import create_wav_bytes

logger = get_logger(__name__)

# Reusable client (initialized at startup)
GENAI_TTS_CLIENT: Optional[genai.Client] = None

def initialize_tts_client() -> None:
    """Initialize the Google AI API client for TTS"""
    global GENAI_TTS_CLIENT
    try:
        api_key = config.GOOGLE_API_KEY
        if not api_key:
            logger.warning("[TTS] GOOGLE_API_KEY not set; TTS client not initialized")
            return
            
        GENAI_TTS_CLIENT = genai.Client(api_key=api_key)
        logger.info("[TTS] Initialized Google AI API client for TTS")
    except Exception as e:
        logger.exception("[TTS] Failed to initialize TTS client")
        raise

def get_tts_client() -> genai.Client:
    """Get the TTS client, initializing if needed"""
    global GENAI_TTS_CLIENT
    if GENAI_TTS_CLIENT is None:
        initialize_tts_client()
    return GENAI_TTS_CLIENT

def tts_for_turns(turns: List[Dict[str, str]]) -> Dict[str, Any]:
    """Synthesize given turns and return dict with base64 audio (WAV) and mime."""
    logger.info(f"[TTS] tts_for_turns called with {len(turns)} turns")
    
    if not turns:
        raise ValueError("Turns cannot be empty")
    
    api_key = config.GOOGLE_API_KEY
    if not api_key:
        logger.error("[TTS] GOOGLE_API_KEY not set")
        raise RuntimeError("GOOGLE_API_KEY not set; multi-speaker TTS requires Google AI API key")
    
    logger.info(f"[TTS] Using TTS client for API key: {api_key[:10]}...")
    tts_client = get_tts_client()
    
    # Build conversation text
    conversation_parts = []
    for i, turn in enumerate(turns):
        speaker = turn.get('speaker', 'Unknown')
        text = turn.get('text', '')
        conversation_parts.append(f"{speaker}: {text}")
        logger.info(f"[TTS] Turn {i}: speaker='{speaker}', text_length={len(text)}")
    
    conversation_text = "\n".join(conversation_parts)
    logger.info(f"[TTS] Built conversation text: {len(conversation_text)} chars, first 100 chars: {conversation_text[:100]!r}")
    
    logger.info(f"[TTS] Sending request to Gemini TTS API...")
    logger.info(f"[TTS] Model: gemini-2.5-flash-preview-tts")
    logger.info(f"[TTS] Configuring multi-speaker voices: Jay=Kore, Nik=Puck")
    
    try:
        response = tts_client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=conversation_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker="Jay",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                                )
                            ),
                            types.SpeakerVoiceConfig(
                                speaker="Nik",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
                                )
                            ),
                        ]
                    )
                )
            )
        )
        logger.info(f"[TTS] TTS API request sent successfully")
    except Exception as e:
        logger.error(f"[TTS] TTS API request failed: {e}")
        raise
    
    logger.info(f"[TTS] Processing TTS API response...")
    
    if not response or not getattr(response, 'candidates', None):
        logger.error("[TTS] Empty response or no candidates from TTS API")
        raise ValueError("Empty TTS response (no candidates)")
    
    logger.info(f"[TTS] Response has {len(response.candidates)} candidates")
    cand0 = response.candidates[0]
    
    if not cand0 or not getattr(cand0, 'content', None) or not getattr(cand0.content, 'parts', None):
        logger.error("[TTS] Candidate has no content parts")
        raise ValueError("TTS candidate missing content.parts")
    
    logger.info(f"[TTS] Candidate has {len(cand0.content.parts)} content parts")
    part = cand0.content.parts[0]
    
    inline = getattr(part, "inline_data", None)
    if not inline or not getattr(inline, 'data', None):
        logger.error("[TTS] Inline audio data missing in response part")
        raise ValueError("TTS response missing inline audio data")
    
    logger.info(f"[TTS] Found inline audio data in response")
    
    mime_type = getattr(inline, "mime_type", None) or ""
    data_b64_or_bytes = inline.data
    
    logger.info(f"[TTS] Audio data type: {type(data_b64_or_bytes)}, mime_type: {mime_type}")
    
    if isinstance(data_b64_or_bytes, (bytes, bytearray)):
        decoded = bytes(data_b64_or_bytes)
        logger.info(f"[TTS] Audio data is already bytes, length: {len(decoded)}")
    else:
        logger.info(f"[TTS] Decoding base64 audio data, length: {len(data_b64_or_bytes)}")
        decoded = base64.b64decode(data_b64_or_bytes)
        logger.info(f"[TTS] Decoded audio data length: {len(decoded)}")
    
    if "wav" in mime_type.lower():
        wav_bytes = decoded
        logger.info(f"[TTS] Using raw WAV data, no conversion needed")
    else:
        logger.info(f"[TTS] Converting PCM to WAV format...")
        wav_bytes = create_wav_bytes(decoded, channels=1, rate=24000, sample_width=2)
        mime_type = "audio/wav"
        logger.info(f"[TTS] Converted to WAV, new length: {len(wav_bytes)}")
    
    audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")
    logger.info(f"[TTS] Final audio: {len(wav_bytes)} bytes, base64 length: {len(audio_b64)}, mime: {mime_type}")
    
    return {"mime": mime_type or "audio/wav", "base64": audio_b64}

def synthesize_audio_multi_speaker(script_json_text: str, output_filepath: str) -> str:
    """Convert script to multi-speaker audio using Gemini TTS"""
    logger.info(f"[TTS] Starting audio synthesis to {output_filepath}")
    
    try:
        # Clean and parse JSON
        import json
        from app.services.script_service import clean_json_string, validate_script_json
        cleaned = clean_json_string(script_json_text)
        script_obj = json.loads(cleaned)
        logger.info("[TTS] JSON script parsed successfully")
        
        # Validate script structure
        validate_script_json(script_obj)
        turns = script_obj["multiSpeakerMarkup"]["turns"]
        conversation_text = "\n".join([f"{turn['speaker']}: {turn['text']}" for turn in turns])
        logger.info(f"[TTS] Prepared conversation with {len(turns)} turns")
        
        # Prefer Google AI API (api_key) for multi-speaker; Vertex AI does not support multi_speaker_voice_config
        api_key = config.GOOGLE_API_KEY
        if not api_key:
            logger.error("[TTS] GOOGLE_API_KEY is not set. Multi-speaker TTS is only supported via Google AI API. Set GOOGLE_API_KEY and retry.")
            raise RuntimeError("GOOGLE_API_KEY not set; multi-speaker TTS requires Google AI API key")
        
        tts_client = get_tts_client()
        logger.info("[TTS] Using shared Google AI API client for multi-speaker synthesis")
        
        # TTS request
        start = time.perf_counter()
        logger.info("[TTS] Sending request to Gemini TTS service...")
        
        response = tts_client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=conversation_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker="Jay",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name="Kore",
                                    )
                                )
                            ),
                            types.SpeakerVoiceConfig(
                                speaker="Nik",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name="Puck",
                                    )
                                )
                            ),
                        ]
                    )
                )
            )
        )
        
        end = time.perf_counter()
        logger.info(f"[TTS] TTS API completed in {end - start:.2f} seconds")
        
        # Extract audio data and mime type
        part = response.candidates[0].content.parts[0]
        mime_type = getattr(getattr(part, "inline_data", None), "mime_type", None)
        logger.info(f"[TTS] inline_data mime_type: {mime_type}")
        audio_data = part.inline_data.data
        
        # Handle different audio data formats
        if isinstance(audio_data, (bytes, bytearray)):
            decoded_audio = bytes(audio_data)
        elif isinstance(audio_data, str):
            try:
                decoded_audio = base64.b64decode(audio_data)
            except Exception as e:
                logger.error(f"[TTS] Failed to base64-decode audio data: {e}")
                raise RuntimeError(f"Failed to decode TTS audio data: {e}")
        else:
            logger.error(f"[TTS] Unsupported audio data type: {type(audio_data)}")
            raise RuntimeError("Unsupported audio data type in TTS response")
        
        logger.info(f"[TTS] Decoded audio size: {len(decoded_audio)} bytes")
        
        # Save audio according to mime type
        if mime_type and "wav" in mime_type:
            with open(output_filepath, "wb") as f:
                f.write(decoded_audio)
        elif mime_type and "pcm" in mime_type:
            wav_bytes = create_wav_bytes(decoded_audio, channels=1, rate=24000, sample_width=2)
            with open(output_filepath, "wb") as f:
                f.write(wav_bytes)
        else:
            logger.warning("[TTS] Unknown or missing mime_type; writing bytes directly as WAV")
            with open(output_filepath, "wb") as f:
                f.write(decoded_audio)
        
        return output_filepath
        
    except Exception as e:
        logger.error(f"[TTS] Audio synthesis failed: {str(e)}")
        raise RuntimeError(f"Audio synthesis failed: {str(e)}")
