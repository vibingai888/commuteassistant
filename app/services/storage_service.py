"""
Storage service for managing podcast data and audio files using Google Cloud Storage
"""

import os
import json
import uuid
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from google.cloud import storage
from app.models import StoredPodcast, PodcastFeedResponse
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

class PodcastStorageService:
    """Service for storing and retrieving podcast data using Google Cloud Storage"""
    
    def __init__(self):
        """Initialize storage service"""
        self.bucket_name = "commuteassistant-podcasts"
        self.storage_client = None
        self.bucket = None
        
        # Initialize Google Cloud Storage
        self._init_cloud_storage()
        
        logger.info(f"[Storage] Initialized podcast storage using bucket: {self.bucket_name}")
    
    def _init_cloud_storage(self):
        """Initialize Google Cloud Storage client and bucket"""
        try:
            # Initialize the client
            self.storage_client = storage.Client()
            
            # Get or create the bucket
            try:
                self.bucket = self.storage_client.get_bucket(self.bucket_name)
                logger.info(f"[Storage] Using existing bucket: {self.bucket_name}")
            except Exception:
                # Create bucket if it doesn't exist
                self.bucket = self.storage_client.create_bucket(self.bucket_name, location="us-central1")
                logger.info(f"[Storage] Created new bucket: {self.bucket_name}")
                
        except Exception as e:
            logger.error(f"[Storage] Failed to initialize Cloud Storage: {e}")
            # Fallback to local storage if Cloud Storage fails
            self._init_local_storage()
    
    def _init_local_storage(self):
        """Fallback to local file storage"""
        logger.warning("[Storage] Falling back to local file storage")
        self.storage_dir = Path("storage/podcasts")
        self.metadata_file = self.storage_dir / "metadata.json"
        self.audio_dir = self.storage_dir / "audio"
        
        # Create storage directories if they don't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata storage
        self._init_metadata()
    
    def _init_metadata(self):
        """Initialize metadata storage file (local fallback only)"""
        if not self.metadata_file.exists():
            initial_data = {
                "podcasts": {},
                "last_updated": datetime.now().isoformat()
            }
            self._save_metadata(initial_data)
            logger.info("[Storage] Created new metadata storage file")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from Cloud Storage or local file"""
        if self.bucket:
            try:
                # Load from Cloud Storage
                blob = self.bucket.blob("metadata.json")
                if blob.exists():
                    data = json.loads(blob.download_as_text())
                    logger.debug(f"[Storage] Loaded metadata from Cloud Storage with {len(data.get('podcasts', {}))} podcasts")
                    return data
                else:
                    # Create initial metadata
                    initial_data = {"podcasts": {}, "last_updated": datetime.now().isoformat()}
                    self._save_metadata(initial_data)
                    return initial_data
            except Exception as e:
                logger.error(f"[Storage] Failed to load metadata from Cloud Storage: {e}")
                # Fallback to local storage
                return self._load_local_metadata()
        else:
            # Use local storage
            return self._load_local_metadata()
    
    def _load_local_metadata(self) -> Dict[str, Any]:
        """Load metadata from local file (fallback)"""
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                logger.debug(f"[Storage] Loaded local metadata with {len(data.get('podcasts', {}))} podcasts")
                return data
        except Exception as e:
            logger.error(f"[Storage] Failed to load local metadata: {e}")
            return {"podcasts": {}, "last_updated": datetime.now().isoformat()}
    
    def _save_metadata(self, data: Dict[str, Any]):
        """Save metadata to Cloud Storage or local file"""
        data["last_updated"] = datetime.now().isoformat()
        
        if self.bucket:
            try:
                # Save to Cloud Storage
                blob = self.bucket.blob("metadata.json")
                blob.upload_from_string(json.dumps(data, indent=2, default=str), content_type="application/json")
                logger.debug("[Storage] Metadata saved to Cloud Storage successfully")
            except Exception as e:
                logger.error(f"[Storage] Failed to save metadata to Cloud Storage: {e}")
                # Fallback to local storage
                self._save_local_metadata(data)
        else:
            # Use local storage
            self._save_local_metadata(data)
    
    def _save_local_metadata(self, data: Dict[str, Any]):
        """Save metadata to local file (fallback)"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug("[Storage] Metadata saved to local file successfully")
        except Exception as e:
            logger.error(f"[Storage] Failed to save local metadata: {e}")
    
    def store_podcast(self, podcast_id: str, topic: str, minutes: int, duration_seconds: float, 
                      word_count: int, audio_file_path: str, mime_type: str) -> StoredPodcast:
        """Store a new podcast"""
        try:
            # Verify the audio file exists
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise ValueError(f"Audio file not found at {audio_file_path}")
            
            if self.bucket:
                # Store in Cloud Storage
                audio_filename = f"audio/{podcast_id}.wav"
                blob = self.bucket.blob(audio_filename)
                
                # Upload audio file
                blob.upload_from_filename(str(audio_path))
                logger.info(f"[Storage] Audio uploaded to Cloud Storage: {audio_filename}")
                
                # Clean up local file
                try:
                    audio_path.unlink()
                    logger.info(f"[Storage] Local audio file cleaned up: {audio_path}")
                except OSError:
                    pass
                
            else:
                # Use local storage (fallback)
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
        """Get a specific podcast by ID"""
        try:
            metadata = self._load_metadata()
            podcast_data = metadata["podcasts"].get(podcast_id)
            
            if podcast_data:
                return StoredPodcast(**podcast_data)
            return None
            
        except Exception as e:
            logger.error(f"[Storage] Failed to get podcast {podcast_id}: {e}")
            return None
    
    def get_podcast_feed(self, page: int = 1, page_size: int = 10, sort_by: str = "created_at") -> PodcastFeedResponse:
        """Get paginated podcast feed"""
        try:
            metadata = self._load_metadata()
            podcasts_data = metadata["podcasts"]
            
            # Convert to StoredPodcast objects
            podcasts = [StoredPodcast(**data) for data in podcasts_data.values()]
            
            # Sort podcasts
            if sort_by == "created_at":
                podcasts.sort(key=lambda x: x.created_at, reverse=True)
            elif sort_by == "plays":
                podcasts.sort(key=lambda x: x.plays, reverse=True)
            elif sort_by == "likes":
                podcasts.sort(key=lambda x: x.likes, reverse=True)
            
            # Calculate pagination
            total_count = len(podcasts)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_podcasts = podcasts[start_idx:end_idx]
            
            return PodcastFeedResponse(
                podcasts=page_podcasts,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"[Storage] Failed to get podcast feed: {e}")
            raise
    
    def like_podcast(self, podcast_id: str) -> bool:
        """Like a podcast and return new like count"""
        try:
            metadata = self._load_metadata()
            podcast_data = metadata["podcasts"].get(podcast_id)
            
            if podcast_data:
                podcast_data["likes"] = podcast_data.get("likes", 0) + 1
                self._save_metadata(metadata)
                logger.info(f"[Storage] Podcast {podcast_id} liked, new count: {podcast_data['likes']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[Storage] Failed to like podcast {podcast_id}: {e}")
            return False
    
    def get_audio_file_path(self, podcast_id: str) -> Optional[Path]:
        """Get the file path for a podcast's audio (local fallback only)"""
        if not self.bucket:
            # Local storage fallback
            try:
                audio_path = self.audio_dir / f"{podcast_id}.wav"
                if audio_path.exists():
                    return audio_path
            except Exception as e:
                logger.error(f"[Storage] Failed to get local audio path for {podcast_id}: {e}")
            return None
        else:
            # Cloud Storage - return None as we'll serve directly from Cloud Storage
            return None
    
    def get_audio_blob(self, podcast_id: str):
        """Get audio blob from Cloud Storage"""
        if self.bucket:
            try:
                audio_filename = f"audio/{podcast_id}.wav"
                blob = self.bucket.blob(audio_filename)
                
                if blob.exists():
                    return blob
                else:
                    logger.warning(f"[Storage] Audio blob not found: {audio_filename}")
                    return None
                    
            except Exception as e:
                logger.error(f"[Storage] Failed to get audio blob for {podcast_id}: {e}")
                return None
        return None

# Global storage service instance
storage_service = PodcastStorageService()
