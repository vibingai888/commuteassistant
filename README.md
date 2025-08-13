# Podcast Generator API

A FastAPI application that generates multi-speaker podcasts using Google's Gemini AI. The application is designed with a modular architecture for better maintainability and scalability.

## Project Structure

```
cursor/
├── app/                          # Backend application
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application and routes
│   ├── config.py                # Configuration and environment variables
│   ├── models.py                # Pydantic models for API requests/responses
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── podcast_service.py   # Podcast generation orchestration
│   │   ├── script_service.py    # Script generation using Gemini AI
│   │   └── tts_service.py       # Text-to-speech using Gemini TTS
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── audio_utils.py       # Audio processing utilities
│   │   └── logging_utils.py     # Logging configuration
│   └── suggestions.json         # Topic suggestions
├── frontend/                    # Frontend application
│   ├── index.html              # Main HTML file
│   ├── css/
│   │   └── styles.css          # All CSS styles
│   └── js/
│       ├── app.js              # Main application logic
│       ├── api-client.js       # API communication
│       ├── audio-player.js     # Audio playback logic
│       └── ui-components.js    # UI components and rendering
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── .dockerignore              # Docker ignore patterns
├── test_local.sh              # Local testing script
├── deploy.sh                  # Deployment script
└── cloudbuild.yaml            # Cloud Build configuration
└── deprecated/                # Deprecated files (do not use)
    ├── README.md              # Deprecation documentation
    ├── main.py                # Old monolithic backend (deprecated)
    └── test_api.html          # Old monolithic frontend (deprecated)
```

## Features

- **Multi-speaker Podcast Generation**: Creates natural conversations between two speakers (Jay and Nik)
- **Chunked Audio Streaming**: Generates and streams audio segments for better user experience
- **Real-time Audio Buffering**: Prefetches audio segments as they're needed
- **Interactive UI**: Modern web interface with suggestion chips and progress tracking
- **API Flexibility**: Support for localhost, GCP Cloud Run, and custom API endpoints
- **Factual Accuracy**: Ensures factual accuracy for real-world information
- **Modular Architecture**: Clean separation of concerns with dedicated services

## Backend Architecture

### Services

1. **Script Service** (`app/services/script_service.py`)
   - Handles script generation using Google Gemini AI
   - Supports both single and chunked script generation
   - Includes fallback mechanisms for failed requests

2. **TTS Service** (`app/services/tts_service.py`)
   - Manages text-to-speech conversion using Gemini TTS
   - Supports multi-speaker voice configuration
   - Handles audio format conversion and validation

3. **Podcast Service** (`app/services/podcast_service.py`)
   - Orchestrates the complete podcast generation process
   - Manages segment generation and TTS requests
   - Provides error handling and retry logic

### Utilities

1. **Audio Utils** (`app/utils/audio_utils.py`)
   - Audio format conversion (PCM to WAV)
   - Duration calculation and formatting
   - Base64 encoding/decoding utilities

2. **Logging Utils** (`app/utils/logging_utils.py`)
   - Centralized logging configuration
   - Rotating file handlers
   - Structured logging for debugging

## Deprecated Files

**⚠️ Important**: The following files have been deprecated and should not be used for new development:

- `deprecated/main.py` - Old monolithic backend (replaced by `app/` structure)
- `deprecated/test_api.html` - Old monolithic frontend (replaced by `frontend/` structure)

See `deprecated/README.md` for detailed migration information.

## Frontend Architecture

### Modules

1. **API Client** (`frontend/js/api-client.js`)
   - Handles all API communication
   - Manages API URL configuration
   - Provides utility functions for data conversion

2. **Audio Player** (`frontend/js/audio-player.js`)
   - Manages audio playback and buffering
   - Handles segment fetching and caching
   - Provides progress tracking and visual feedback

3. **UI Components** (`frontend/js/ui-components.js`)
   - Manages user interface interactions
   - Handles form submissions and validation
   - Provides logging and status display

4. **Main App** (`frontend/js/app.js`)
   - Orchestrates all frontend components
   - Initializes the application
   - Provides cross-module communication

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /generate-podcast/` - Generate complete podcast (legacy)
- `POST /generate-script-chunked/` - Generate chunked script
- `POST /tts-segment/` - Generate TTS for specific segment
- `GET /suggestions` - Get topic suggestions

## Configuration

The application uses environment variables for configuration:

- `GOOGLE_API_KEY` - Google AI API key for TTS
- `GOOGLE_APPLICATION_CREDENTIALS` - Service account credentials
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GOOGLE_CLOUD_LOCATION` - GCP location (default: us-central1)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8080)
- `DEBUG` - Debug mode (default: false)

## Local Development

1. **Setup Environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   ```bash
   export GOOGLE_API_KEY="your-api-key"
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   ```

3. **Run Application**:
   ```bash
   # Using the test script
   ./test_local.sh
   
   # Or directly
   python -m app.main
   ```

4. **Access Frontend**:
   - Open `frontend/index.html` in your browser
   - Or serve it using a local server

## Deployment

### GCP Cloud Run

1. **Build and Deploy**:
   ```bash
   ./deploy.sh
   ```

2. **Manual Deployment**:
   ```bash
   # Build Docker image
   gcloud builds submit --config cloudbuild.yaml
   
   # Deploy to Cloud Run
   gcloud run deploy podcast-generator-api \
     --image gcr.io/PROJECT_ID/podcast-generator-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_API_KEY=your-api-key
   ```

## Testing

### Backend Testing

```bash
# Test API endpoints
curl -X GET http://localhost:8000/health
curl -X POST http://localhost:8000/generate-script-chunked/ \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in Healthcare", "minutes": 3}'
```

### Frontend Testing

1. Open `frontend/index.html` in a browser
2. Test API connectivity using the toggle switch
3. Generate a podcast and verify audio playback
4. Test suggestion chips and form validation

## Troubleshooting

### Common Issues

1. **TTS Authentication Errors**:
   - Ensure `GOOGLE_API_KEY` is set correctly
   - Verify the API key has TTS permissions

2. **Script Generation Failures**:
   - Check Vertex AI credentials
   - Verify project ID and location settings

3. **Frontend Connection Issues**:
   - Check CORS configuration
   - Verify API URL settings
   - Test with different API endpoints

### Logs

- Application logs are written to `podcast_api.log`
- Frontend logs are displayed in the browser console
- Cloud Run logs are available in GCP Console

## Contributing

1. Follow the modular architecture pattern
2. Add appropriate logging and error handling
3. Update documentation for new features
4. Test both local and deployed environments

## License

This project is licensed under the MIT License.
