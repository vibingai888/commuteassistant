"""
FastAPI application for Podcast Generator API
"""

import json
import asyncio
from contextlib import asynccontextmanager
from typing import List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.models import (
    PodcastRequest, PodcastResponse, ScriptChunkedResponse, 
    TTSSegmentRequest, TTSSegmentResponse, SuggestionsResponse, HealthResponse,
    StoredPodcast, PodcastFeedResponse, LikePodcastRequest, LikePodcastResponse
)
from app.utils.logging_utils import setup_logging, get_logger
from app.services.script_service import initialize_vertex_client
from app.services.tts_service import initialize_tts_client
from app.services.podcast_service import (
    generate_full_podcast, generate_chunked_podcast_script, generate_tts_segment
)
from app.services.storage_service import storage_service

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Podcast Generator API...")
    logger.info(f"Project ID: {config.GOOGLE_CLOUD_PROJECT}")
    logger.info(f"Location: {config.GOOGLE_CLOUD_LOCATION}")
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Initialize clients
    try:
        initialize_vertex_client()
    except Exception as e:
        logger.exception("[Startup] Failed to initialize Vertex client")
    
    try:
        initialize_tts_client()
    except Exception as e:
        logger.exception("[Startup] Failed to initialize TTS client")
    
    yield
    
    logger.info("🛑 Shutting down Podcast Generator API...")

# Initialize FastAPI app
app = FastAPI(
    title="Podcast Generator API",
    description="Generate multi-speaker podcasts using Google's Gemini AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )

@app.post("/generate-podcast/", response_model=PodcastResponse)
async def generate_podcast(request: PodcastRequest):
    """Generate a complete podcast with script and audio"""
    logger.info(f"[API] generate-podcast called with topic: '{request.topic}' ({request.minutes} minutes)")
    
    try:
        result = await asyncio.to_thread(generate_full_podcast, request.topic, request.minutes)
        
        # Store the podcast for public access
        try:
            stored_podcast = storage_service.store_podcast(
                podcast_id=result["podcast_id"],
                topic=request.topic,
                minutes=request.minutes,
                duration_seconds=result["duration_seconds"],
                word_count=result["word_count"],
                audio_file_path=result["audio_file_path"],
                mime_type=result["mime_type"]
            )
            logger.info(f"[API] Podcast stored with ID: {stored_podcast.id}")
        except Exception as e:
            logger.warning(f"[API] Failed to store podcast: {e}")
            # Continue even if storage fails
        
        return PodcastResponse(**result)
    except Exception as e:
        logger.exception("[API] generate-podcast failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/podcasts/feed", response_model=PodcastFeedResponse)
async def get_podcast_feed(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Podcasts per page"),
    sort_by: str = Query("created_at", description="Sort by: created_at, plays, likes")
):
    """Get public podcast feed"""
    logger.info(f"[API] get-podcast-feed called: page={page}, size={page_size}, sort={sort_by}")
    
    try:
        feed = storage_service.get_podcast_feed(page=page, page_size=page_size, sort_by=sort_by)
        logger.info(f"[API] Retrieved feed with {len(feed.podcasts)} podcasts")
        return feed
    except Exception as e:
        logger.exception("[API] get-podcast-feed failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/podcasts/{podcast_id}", response_model=StoredPodcast)
async def get_podcast(podcast_id: str):
    """Get a specific podcast by ID"""
    logger.info(f"[API] get-podcast called with ID: {podcast_id}")
    
    try:
        podcast = storage_service.get_podcast(podcast_id)
        if podcast:
            logger.info(f"[API] Retrieved podcast: {podcast.topic}")
            return podcast
        else:
            logger.warning(f"[API] Podcast {podcast_id} not found")
            raise HTTPException(status_code=404, detail="Podcast not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[API] get-podcast failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/podcasts/audio/{podcast_id}")
@app.head("/podcasts/audio/{podcast_id}")
async def get_podcast_audio(podcast_id: str):
    """Get podcast audio file"""
    logger.info(f"[API] get-podcast-audio called with ID: {podcast_id}")
    
    try:
        audio_path = storage_service.get_audio_file_path(podcast_id)
        if audio_path and audio_path.exists():
            logger.info(f"[API] Serving audio for podcast {podcast_id}")
            return FileResponse(
                path=audio_path,
                media_type="audio/mpeg",
                filename=f"podcast_{podcast_id}.mp3",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, HEAD",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        else:
            logger.warning(f"[API] Audio file not found for podcast {podcast_id}")
            raise HTTPException(status_code=404, detail="Audio file not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[API] get-podcast-audio failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/podcasts/{podcast_id}/like", response_model=LikePodcastResponse)
async def like_podcast(podcast_id: str):
    """Like a podcast"""
    logger.info(f"[API] like-podcast called with ID: {podcast_id}")
    
    try:
        success = storage_service.like_podcast(podcast_id)
        if success:
            # Get updated like count
            podcast = storage_service.get_podcast(podcast_id)
            like_count = podcast.likes if podcast else 0
            
            logger.info(f"[API] Podcast {podcast_id} liked successfully, total likes: {like_count}")
            return LikePodcastResponse(success=True, new_like_count=like_count)
        else:
            logger.warning(f"[API] Failed to like podcast {podcast_id}")
            raise HTTPException(status_code=404, detail="Podcast not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[API] like-podcast failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-script-chunked/", response_model=ScriptChunkedResponse)
async def generate_script_chunked(request: PodcastRequest):
    """Generate a chunked podcast script"""
    logger.info(f"[API] generate-script-chunked called with topic: '{request.topic}' ({request.minutes} minutes)")
    logger.info(f"[API] generate-script-chunked request validation passed")
    
    try:
        logger.info(f"[API] generate-script-chunked starting async execution...")
        result = await asyncio.to_thread(generate_chunked_podcast_script, request.topic, request.minutes)
        logger.info(f"[API] generate-script-chunked completed successfully, returning {len(result.get('segments', []))} segments")
        return ScriptChunkedResponse(**result)
    except Exception as e:
        logger.exception(f"[API] generate-script-chunked failed for topic '{request.topic}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts-segment/", response_model=TTSSegmentResponse)
async def api_tts_segment(request: TTSSegmentRequest):
    """Generate TTS for a specific segment"""
    logger.info(f"[API] tts-segment called with id={request.segment_id}, turns={len(request.turns)}")
    logger.info(f"[API] tts-segment request data: segment_id={request.segment_id}, turns_count={len(request.turns)}")
    
    # Log first few turns for debugging
    for i, turn in enumerate(request.turns[:3]):
        logger.info(f"[API] tts-segment turn {i}: speaker='{turn.get('speaker', 'N/A')}', text_length={len(turn.get('text', ''))}")
    
    try:
        # Simple retry for transient TTS failures
        attempts = 0
        last_err = None
        while attempts < 3:
            attempts += 1
            logger.info(f"[API] tts-segment id={request.segment_id} attempt {attempts}/3 starting...")
            try:
                result = await asyncio.to_thread(generate_tts_segment, request.segment_id, request.turns)
                logger.info(f"[API] tts-segment id={request.segment_id} attempt {attempts} succeeded")
                return TTSSegmentResponse(**result)
            except Exception as e:
                last_err = e
                logger.warning(f"[API] tts-segment id={request.segment_id} attempt {attempts} failed: {e}")
                if attempts < 3:
                    logger.info(f"[API] tts-segment id={request.segment_id} waiting {0.8 * attempts}s before retry...")
                    await asyncio.sleep(0.8 * attempts)
        logger.error(f"[API] tts-segment id={request.segment_id} all 3 attempts failed, last error: {last_err}")
        raise last_err or RuntimeError("Unknown TTS failure")
    except Exception as e:
        logger.exception(f"[API] tts-segment id={request.segment_id} failed completely: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")

@app.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions():
    """Get topic suggestions"""
    try:
        with open("app/suggestions.json", "r") as f:
            suggestions = json.load(f)
        return SuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        logger.error(f"[API] Failed to load suggestions: {e}")
        # Return default suggestions if file not found
        default_suggestions = [
            "The Future of AI in Healthcare",
            "Climate Change Solutions",
            "The History of Las Vegas",
            "Space Exploration",
            "Digital Privacy",
            "Renewable Energy",
            "Mental Health Awareness",
            "Cybersecurity Trends",
            "Sustainable Living",
            "Artificial Intelligence Ethics"
        ]
        return SuggestionsResponse(suggestions=default_suggestions)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG
    )
