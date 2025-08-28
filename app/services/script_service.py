"""
Script generation service using Google Gemini AI
"""

import json
import re
import time
from typing import Any, Dict, List, Optional

from google import genai

from app.config import config
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Reusable client (initialized at startup)
GENAI_VERTEX_CLIENT: Optional[genai.Client] = None


def initialize_vertex_client() -> None:
    """Initialize the Vertex AI client for script generation"""
    global GENAI_VERTEX_CLIENT
    try:
        GENAI_VERTEX_CLIENT = genai.Client(
            vertexai=True, project=config.GOOGLE_CLOUD_PROJECT, location=config.GOOGLE_CLOUD_LOCATION
        )
        logger.info("[Script] Initialized Vertex client for script generation")
    except Exception:
        logger.exception("[Script] Failed to initialize Vertex client")
        raise


def get_vertex_client() -> genai.Client:
    """Get the Vertex AI client, initializing if needed"""
    if GENAI_VERTEX_CLIENT is None:
        initialize_vertex_client()
    return GENAI_VERTEX_CLIENT


def clean_json_string(s) -> str:
    """Remove markdown code fences and whitespace from API responses"""
    # If s is already a dict, return it as is
    if isinstance(s, dict):
        return s

    # If s is a string, clean it
    if isinstance(s, str):
        s = s.strip()
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
        return s

    # If s is neither string nor dict, raise error
    raise ValueError(f"Expected string or dict, got {type(s)}")


def validate_script_json(script: dict) -> None:
    """Validate the generated JSON follows expected schema"""
    if not isinstance(script, dict):
        raise ValueError("Script is not a JSON object")

    # Check if it's a chunked script with segments
    if "segments" in script:
        segments = script.get("segments", [])
        if not isinstance(segments, list) or not segments:
            raise ValueError("'segments' must be a non-empty list")
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict) or "multiSpeakerMarkup" not in segment:
                raise ValueError(f"Segment {i} must contain 'multiSpeakerMarkup'")
            # Validate the multiSpeakerMarkup part of the segment
            msm = segment["multiSpeakerMarkup"]
            if not msm or "turns" not in msm:
                raise ValueError(f"Segment {i} multiSpeakerMarkup missing 'turns'")
            turns = msm["turns"]
            if not isinstance(turns, list) or len(turns) < 2:
                raise ValueError(f"Segment {i} 'turns' must be a list with at least two items")
            # Check turns have text and speaker
            for j, turn in enumerate(turns):
                if "text" not in turn or "speaker" not in turn:
                    raise ValueError(f"Segment {i}, turn {j} must contain 'text' and 'speaker' fields")
                if turn["speaker"] not in ["Jay", "Nik"]:
                    raise ValueError(f"Segment {i}, turn {j} has invalid speaker: {turn['speaker']}")
        return

    # Check if it's a single script with multiSpeakerMarkup
    msm = script.get("multiSpeakerMarkup")
    if not msm or "turns" not in msm:
        raise ValueError("Missing 'multiSpeakerMarkup.turns' in script")

    turns = msm["turns"]
    if not isinstance(turns, list) or len(turns) < 2:
        raise ValueError("'turns' must be a list with at least two items")

    # Check turns have text and speaker
    for i, turn in enumerate(turns):
        if "text" not in turn or "speaker" not in turn:
            raise ValueError(f"Turn {i} must contain 'text' and 'speaker' fields")
        if turn["speaker"] not in ["Jay", "Nik"]:
            raise ValueError(f"Turn {i} has invalid speaker: {turn['speaker']}")


def generate_podcast_script(topic: str, minutes: int, words_per_minute: int = 210) -> Dict[str, Any]:
    """Generate podcast script using Gemini AI"""
    total_words = max(1, minutes) * words_per_minute
    logger.info(f"[Script] Generating script for topic: '{topic}', {minutes} minutes (~{total_words} words)")

    prompt = f"""
Create a podcast dialogue in JSON format about the topic: "{topic}".
The dialogue should be a lively back-and-forth between two male speakers named Jay and Nik.
The podcast should have approximately {total_words} words in total.
The conversation should start with the following intro:

Jay: Hi this is Jay
Nik: Hi this is Nik
Jay: And you're listening to Vibing AI's product commute assist!

After the intro, Both Jay and Nik discuss the topic and bring up interesting points, questions, and answers.
Use clear explanations and relatable analogies.
Maintain a consistently positive and enthusiastic tone.
Critically: ensure factual accuracy. If asked about current affairs, upcoming events, movies, or any real‑world information that you are uncertain about, explicitly say you are unsure, avoid speculation, and provide only well‑sourced, widely accepted facts.
Generate the podcast script in valid JSON only.
Do not include markdown code fences or commentary.

JSON structure:
{{
  "multiSpeakerMarkup": {{
    "turns": [
      {{"text": "Podcast script content here...", "speaker": "Jay"}},
      {{"text": "Podcast script content here...", "speaker": "Nik"}}
    ]
  }}
}}
"""

    try:
        logger.info(f"[Script] Using shared Vertex client for project: {config.GOOGLE_CLOUD_PROJECT}")
        client = get_vertex_client()

        start = time.perf_counter()
        logger.info("[Script] Sending prompt to Gemini AI...")

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
        )

        end = time.perf_counter()
        output_text = response.candidates[0].content.parts[0].text.strip()
        word_count = len(output_text.split())

        logger.info(f"[Script] Script generation completed in {end - start:.2f} seconds")
        logger.info(f"[Script] Generated {word_count} words")

        # Parse and validate the JSON response
        cleaned = clean_json_string(output_text)
        script_obj = json.loads(cleaned)
        validate_script_json(script_obj)

        return script_obj

    except Exception as e:
        logger.error(f"[Script] Failed to generate script: {str(e)}")
        raise RuntimeError(f"Script generation failed: {str(e)}")


def _word_count(text: str) -> int:
    """Count words in text"""
    return len(re.findall(r"\w+", text or ""))


def chunk_turns_by_words(
    turns: List[Dict[str, str]], words_per_chunk: int = 100, first_words: Optional[int] = None, first_min_words: int = 65
) -> List[List[Dict[str, str]]]:
    """Group turns into chunks. First chunk can target first_words, enforce at least first_min_words, others words_per_chunk."""
    chunks: List[List[Dict[str, str]]] = []
    current: List[Dict[str, str]] = []
    current_words = 0
    target = first_words if first_words and first_words > 0 else words_per_chunk
    first_done = first_words is None

    for turn in turns:
        turn_words = _word_count(turn.get("text", ""))

        # If adding this turn would exceed the target, start a new chunk
        if current and current_words + turn_words > target:
            chunks.append(current)
            current = [turn]
            current_words = turn_words
            if not first_done:
                first_done = True
                target = words_per_chunk
        else:
            current.append(turn)
            current_words += turn_words

    # Add the last chunk
    if current:
        chunks.append(current)

    # Enforce minimum words for the first chunk by stealing from the next chunk
    if chunks and first_min_words and first_min_words > 0 and len(chunks) >= 2:

        def turns_words(ts):
            return sum(_word_count(t.get("text", "")) for t in ts)

        first_chunk_words = turns_words(chunks[0])
        while first_chunk_words < first_min_words and len(chunks) >= 2 and len(chunks[1]) > 1:
            # Move one turn from start of next chunk to first chunk
            moved = chunks[1].pop(0)
            chunks[0].append(moved)
            first_chunk_words = turns_words(chunks[0])

            # If next chunk became empty and there are more chunks, collapse
            if len(chunks[1]) == 0 and len(chunks) > 2:
                chunks.pop(1)
                break

    logger.info(
        f"[Chunking] Created {len(chunks)} chunks (first≈{first_words or words_per_chunk}, min_first={first_min_words}, rest≈{words_per_chunk}) from {len(turns)} turns"
    )
    return chunks


def generate_podcast_script_chunked(topic: str, minutes: int, words_per_chunk: int = 100, wpm: int = 190) -> Dict[str, Any]:
    """Ask the model for chunked segments; fallback to local chunking if needed."""
    logger.info("[Script] generate_podcast_script_chunked called")
    logger.info(f"[Script] Parameters: topic='{topic}', minutes={minutes}, words_per_chunk={words_per_chunk}, wpm={wpm}")

    # Validate inputs
    if not topic or not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic cannot be empty")

    if minutes <= 0 or minutes > 15:
        raise ValueError("Minutes must be between 1 and 15")

    total_words = max(1, minutes) * wpm
    logger.info(f"[Script] Target total words: {total_words}")

    prompt = f"""
You are an assistant that must output VALID JSON ONLY. No markdown. No commentary.
Create a podcast dialogue about: "{topic}" with two speakers Jay (host) and Nik (guest).
Requirements:
- Conversation must start with:
  Jay: Hi this is Jay
  Nik: Hi this is Nik
  Jay: And you're listening to Vibing AI's product commute assist!
- End with a short positive outro summarizing key takeaways.
- Ensure factual accuracy. For current affairs, upcoming events, movies, or any real‑world information, answer only if you are confident. Otherwise, explicitly state uncertainty and avoid speculation.
- Total words ≈ {total_words}
- Split into segments: the FIRST segment must be at least 65 words (prefer 65-80 words); each SUBSEQUENT segment ≈ {words_per_chunk} words (±20%).
- Maintain conversational continuity across segments.
- Speakers allowed: Jay, Nik only.
- Output must strictly follow this JSON schema:
{{
  "segments": [
    {{
      "segmentId": INTEGER >= 1,
      "multiSpeakerMarkup": {{
        "turns": [
          {{"speaker": "Jay", "text": STRING}},
          {{"speaker": "Nik", "text": STRING}}
        ]
      }}
    }}
  ]
}}
Do not wrap in code fences. Ensure keys and types match exactly.
"""

    client = get_vertex_client()
    start = time.perf_counter()
    response = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)
    elapsed = time.perf_counter() - start
    raw = response.candidates[0].content.parts[0].text.strip()
    logger.info(f"[Script] Chunked script response in {elapsed:.2f}s; length={len(raw)} chars")

    cleaned = clean_json_string(raw)
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict) or "segments" not in data:
            raise ValueError("missing 'segments'")
        segs = data.get("segments", [])
        if not isinstance(segs, list) or not segs:
            raise ValueError("segments empty")
        for s in segs:
            # Validate each segment's multiSpeakerMarkup structure
            if not isinstance(s, dict) or "multiSpeakerMarkup" not in s:
                raise ValueError(f"Segment missing 'multiSpeakerMarkup'")
            msm = s["multiSpeakerMarkup"]
            if not msm or "turns" not in msm:
                raise ValueError(f"Segment multiSpeakerMarkup missing 'turns'")
            turns = msm["turns"]
            if not isinstance(turns, list) or len(turns) < 2:
                raise ValueError(f"Segment 'turns' must be a list with at least two items")
            # Check turns have text and speaker
            for j, turn in enumerate(turns):
                if "text" not in turn or "speaker" not in turn:
                    raise ValueError(f"Segment turn {j} must contain 'text' and 'speaker' fields")
                if turn["speaker"] not in ["Jay", "Nik"]:
                    raise ValueError(f"Segment turn {j} has invalid speaker: {turn['speaker']}")
        return data
    except Exception as e:
        logger.warning(f"[Script] Model did not return valid chunked JSON ({e}). Falling back to local chunking.")
        # Fallback: generate single script and chunk locally
        t0 = time.perf_counter()
        single_script = generate_podcast_script(topic, minutes, words_per_minute=wpm)
        t1 = time.perf_counter()
        logger.info(f"[Script] Fallback single script in {t1 - t0:.2f}s")

        # single_script is now already a dict, no need to parse
        validate_script_json(single_script)
        chunks = chunk_turns_by_words(
            single_script["multiSpeakerMarkup"]["turns"], words_per_chunk=words_per_chunk, first_words=70, first_min_words=65
        )
        return {"segments": [{"segmentId": idx + 1, "multiSpeakerMarkup": {"turns": seg}} for idx, seg in enumerate(chunks)]}
