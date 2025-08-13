# Deprecated Files

This folder contains files that have been replaced by the new modular architecture.

## Deprecated Files

### `test_api.html`
- **Status**: DEPRECATED - Replaced by modular frontend
- **Replacement**: `frontend/index.html` + `frontend/js/` modules
- **Reason**: Refactored into separate CSS and JavaScript modules for better maintainability
- **New Structure**:
  - `frontend/index.html` - Main HTML file
  - `frontend/css/styles.css` - All styles
  - `frontend/js/api-client.js` - API communication
  - `frontend/js/audio-player.js` - Audio playback logic
  - `frontend/js/ui-components.js` - UI interactions
  - `frontend/js/app.js` - Main application logic

### `main.py`
- **Status**: DEPRECATED - Replaced by modular backend
- **Replacement**: `app/` directory structure
- **Reason**: Refactored into separate modules for better maintainability and organization
- **New Structure**:
  - `app/main.py` - Main FastAPI application
  - `app/config.py` - Configuration management
  - `app/models.py` - Pydantic models
  - `app/services/script_service.py` - Script generation logic
  - `app/services/tts_service.py` - Text-to-speech logic
  - `app/services/podcast_service.py` - Orchestration logic
  - `app/utils/logging_utils.py` - Logging utilities
  - `app/utils/audio_utils.py` - Audio processing utilities

## Migration Notes

The new modular structure provides:
- Better code organization
- Easier maintenance
- Clear separation of concerns
- Improved debugging capabilities

**Do not use these deprecated files for new development.**
