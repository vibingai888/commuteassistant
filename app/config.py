"""
Configuration and environment variables for the Podcast Generator API
"""

import os
from typing import Optional


class Config:
    """Application configuration"""

    def __init__(self):
        """Initialize configuration from environment variables"""
        # Google API Configuration
        self.GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
        self.GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.GOOGLE_CLOUD_PROJECT: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        # API Configuration
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8080"))
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

        # Logging Configuration
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE: str = os.getenv("LOG_FILE", "podcast_api.log")

        # Content Configuration
        self.DEFAULT_MINUTES: int = 3
        self.MAX_MINUTES: int = 15
        self.MIN_FIRST_CHUNK_WORDS: int = 65
        self.TARGET_CHUNK_WORDS: int = 100

    def validate(self) -> None:
        """Validate required configuration"""
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        # GOOGLE_APPLICATION_CREDENTIALS is optional when using API keys
        # if not self.GOOGLE_APPLICATION_CREDENTIALS:
        #     raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is required")

        if not self.GOOGLE_CLOUD_PROJECT:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")


# Global config instance
config = Config()
