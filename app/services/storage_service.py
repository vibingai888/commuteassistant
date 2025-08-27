"""
Storage service for managing podcast data and audio files
"""

import os
import json
import uuid
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.models import StoredPodcast, PodcastFeedResponse
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

class PodcastStorageService:
    """Service for storing and retrieving podcast data"""
    
    def __init__(self):
        """Initialize storage service"""
        self.storage_dir = Path("storage/podcasts")
        self.metadata_file = self.storage_dir / "metadata.json"
        self.audio_dir = self.storage_dir / "audio"
        
        # Create storage directories if they don't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata storage
        self._init_metadata()
        
        logger.info(f"[Storage] Initialized podcast storage at {self.storage_dir}")
    
    def _init_metadata(self):
        """Initialize metadata storage file"""
        if not self.metadata_file.exists():
            initial_data = {
                "podcasts": {},
                "last_updated": datetime.now().isoformat()
            }
            self._save_metadata(initial_data)
            logger.info("[Storage] Created new metadata storage file")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file"""
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                logger.debug(f"[Storage] Loaded metadata with {len(data.get('podcasts', {}))} podcasts")
                return data
        except Exception as e:
            logger.error(f"[Storage] Failed to load metadata: {e}")
            return {"podcasts": {}, "last_updated": datetime.now().isoformat()}
    
    def _save_metadata(self, data: Dict[str, Any]):
        """Save metadata to file"""
        try:
            data["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug("[Storage] Metadata saved successfully")
        except Exception as e:
            logger.error(f"[Storage] Failed to save metadata: {e}")
    
    def store_podcast(self, podcast_id: str, topic: str, minutes: int, duration_seconds: float, 
                      word_count: int, audio_file_path: str, mime_type: str) -> StoredPodcast:
        """Store a new podcast"""
        try:
            # Verify the audio file exists
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise ValueError(f"Audio file not found at {audio_file_path}")
            
            # Move the audio file to our storage directory if it's not already there
            audio_filename = f"{podcast_id}.wav"
            final_audio_path = self.audio_dir / audio_filename
            
            if audio_path != final_audio_path:
                import shutil
                shutil.move(str(audio_path), str(final_audio_path))
                logger.info(f"[Storage] Moved audio file to {final_audio_path}")
            
            # Create podcast metadata
            podcast = StoredPodcast(
                id=podcast_id,
                topic=topic,
                minutes=minutes,
                duration_seconds=duration_seconds,
                word_count=word_count,
                audio_url=f"/podcasts/audio/{podcast_id}",
                created_at=datetime.now(),
                plays=0,
                likes=0
            )
            
            # Save to metadata
            metadata = self._load_metadata()
            metadata["podcasts"][podcast_id] = podcast.model_dump()
            self._save_metadata(metadata)
            
            logger.info(f"[Storage] Podcast '{topic}' stored successfully with ID: {podcast_id}")
            return podcast
            
        except Exception as e:
            logger.error(f"[Storage] Failed to store podcast: {e}")
            raise
    
    def get_podcast(self, podcast_id: str) -> Optional[StoredPodcast]:
        """Retrieve a podcast by ID"""
        try:
            metadata = self._load_metadata()
            podcast_data = metadata["podcasts"].get(podcast_id)
            
            if podcast_data:
                # Increment play count
                podcast_data["plays"] += 1
                self._save_metadata(metadata)
                
                logger.info(f"[Storage] Retrieved podcast {podcast_id}, plays: {podcast_data['plays']}")
                return StoredPodcast(**podcast_data)
            
            logger.warning(f"[Storage] Podcast {podcast_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"[Storage] Failed to retrieve podcast {podcast_id}: {e}")
            return None
    
    def get_podcast_feed(self, page: int = 1, page_size: int = 10, 
                         sort_by: str = "created_at") -> PodcastFeedResponse:
        """Get paginated podcast feed"""
        try:
            metadata = self._load_metadata()
            podcasts_data = list(metadata["podcasts"].values())
            
            # Sort podcasts
            if sort_by == "created_at":
                podcasts_data.sort(key=lambda x: x["created_at"], reverse=True)
            elif sort_by == "plays":
                podcasts_data.sort(key=lambda x: x["plays"], reverse=True)
            elif sort_by == "likes":
                podcasts_data.sort(key=lambda x: x["likes"], reverse=True)
            
            # Paginate
            total_count = len(podcasts_data)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_podcasts = podcasts_data[start_idx:end_idx]
            
            # Convert to StoredPodcast objects
            podcasts = [StoredPodcast(**podcast) for podcast in page_podcasts]
            
            logger.info(f"[Storage] Retrieved feed: page {page}, {len(podcasts)} podcasts")
            
            return PodcastFeedResponse(
                podcasts=podcasts,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"[Storage] Failed to retrieve podcast feed: {e}")
            return PodcastFeedResponse(
                podcasts=[],
                total_count=0,
                page=page,
                page_size=page_size
            )
    
    def like_podcast(self, podcast_id: str) -> bool:
        """Like a podcast"""
        try:
            metadata = self._load_metadata()
            podcast_data = metadata["podcasts"].get(podcast_id)
            
            if podcast_data:
                podcast_data["likes"] += 1
                self._save_metadata(metadata)
                
                logger.info(f"[Storage] Podcast {podcast_id} liked, total likes: {podcast_data['likes']}")
                return True
            
            logger.warning(f"[Storage] Cannot like podcast {podcast_id}: not found")
            return False
            
        except Exception as e:
            logger.error(f"[Storage] Failed to like podcast {podcast_id}: {e}")
            return False
    
    def get_audio_file_path(self, podcast_id: str) -> Optional[Path]:
        """Get the file path for a podcast's audio"""
        try:
            audio_path = self.audio_dir / f"{podcast_id}.wav"
            if audio_path.exists():
                return audio_path
            logger.warning(f"[Storage] Audio file not found for podcast {podcast_id}")
            return None
        except Exception as e:
            logger.error(f"[Storage] Failed to get audio path for podcast {podcast_id}: {e}")
            return None

# Global storage service instance
storage_service = PodcastStorageService()
