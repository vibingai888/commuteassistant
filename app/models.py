"""
Pydantic models for API requests and responses
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class PodcastRequest(BaseModel):
    """Request model for podcast generation"""
    topic: str = Field(..., min_length=1, max_length=500, description="Podcast topic")
    minutes: int = Field(..., ge=1, le=30, description="Duration in minutes")
    
    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v):
        if not v.strip():
            raise ValueError('Topic cannot be empty')
        return v.strip()

class PodcastResponse(BaseModel):
    """Response model for podcast generation"""
    podcast_id: str = Field(..., description="Unique podcast identifier")
    audio_file_path: str = Field(..., description="Path to the generated audio file")
    mime_type: str = Field(..., description="MIME type of audio")
    duration_seconds: float = Field(..., description="Duration in seconds")
    word_count: int = Field(..., description="Total word count")

class StoredPodcast(BaseModel):
    """Model for storing podcast metadata and audio"""
    id: str = Field(..., description="Unique podcast identifier")
    topic: str = Field(..., description="Podcast topic")
    minutes: int = Field(..., description="Duration in minutes")
    duration_seconds: float = Field(..., description="Duration in seconds")
    word_count: int = Field(..., description="Total word count")
    audio_url: str = Field(..., description="URL to access the audio file")
    created_at: datetime = Field(..., description="When the podcast was created")
    plays: int = Field(default=0, description="Number of times played")
    likes: int = Field(default=0, description="Number of likes")
    
    model_config = ConfigDict(from_attributes=True)

class PodcastFeedResponse(BaseModel):
    """Response model for podcast feeds"""
    podcasts: List[StoredPodcast] = Field(..., description="List of stored podcasts")
    total_count: int = Field(..., description="Total number of podcasts")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of podcasts per page")

class LikePodcastRequest(BaseModel):
    """Request model for liking a podcast"""
    podcast_id: str = Field(..., description="Podcast ID to like")

class LikePodcastResponse(BaseModel):
    """Response model for liking a podcast"""
    success: bool = Field(..., description="Whether the like was successful")
    new_like_count: int = Field(..., description="Updated like count")

class ScriptSegment(BaseModel):
    """Model for a script segment"""
    segment_id: int = Field(..., description="Segment identifier", alias="segmentId")
    multi_speaker_markup: Dict[str, Any] = Field(..., description="Multi-speaker markup", alias="multiSpeakerMarkup")
    
    model_config = ConfigDict(populate_by_name=True)

class ScriptChunkedResponse(BaseModel):
    """Response model for chunked script generation"""
    segments: List[ScriptSegment] = Field(..., description="List of script segments")
    total_words: int = Field(..., ge=0, description="Total word count")
    
    @field_validator('segments')
    @classmethod
    def validate_segments(cls, v):
        if not v:
            raise ValueError('Segments cannot be empty')
        return v

class TTSSegmentRequest(BaseModel):
    """Request model for TTS segment generation"""
    segment_id: int = Field(..., description="Segment identifier", alias="segmentId")
    turns: List[Dict[str, str]] = Field(..., description="Speaker turns")
    
    model_config = ConfigDict(populate_by_name=True)
    
    @field_validator('turns')
    @classmethod
    def validate_turns(cls, v):
        if not v:
            raise ValueError('Turns cannot be empty')
        for turn in v:
            if not isinstance(turn, dict) or 'speaker' not in turn or 'text' not in turn:
                raise ValueError('Each turn must have speaker and text fields')
        return v

class TTSSegmentResponse(BaseModel):
    """Response model for TTS segment generation"""
    segment_id: int = Field(..., description="Segment identifier")
    base64: str = Field(..., description="Base64 encoded audio data")
    mime: str = Field(..., description="MIME type of audio")
    
    @field_validator('base64')
    @classmethod
    def validate_base64(cls, v):
        if not v:
            raise ValueError('Base64 data cannot be empty')
        return v

class SuggestionsResponse(BaseModel):
    """Response model for topic suggestions"""
    suggestions: List[str] = Field(..., description="List of topic suggestions")

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
