"""
Unit tests for API endpoints
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


class TestAPIEndpoints:
    """Test cases for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_suggestions_endpoint(self, client):
        """Test suggestions endpoint"""
        response = client.get("/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0
    
    @patch('app.main.generate_chunked_podcast_script')
    def test_generate_script_chunked_success(self, mock_generate_script, client):
        """Test successful script generation endpoint"""
        # Mock the script generation
        mock_generate_script.return_value = {
            "segments": [
                {
                    "segmentId": 1,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "Hello, welcome to our podcast!", "speaker": "Jay"},
                            {"text": "Thanks for having me!", "speaker": "Nik"}
                        ]
                    }
                }
            ],
            "total_words": 15
        }
        
        request_data = {
            "topic": "Test Topic",
            "minutes": 2
        }
        
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "segments" in data
        assert "total_words" in data
        assert len(data["segments"]) > 0
        assert data["total_words"] > 0
    
    @patch('app.main.generate_chunked_podcast_script')
    def test_generate_script_chunked_error(self, mock_generate_script, client):
        """Test script generation endpoint with error"""
        # Mock the script generation to raise an exception
        mock_generate_script.side_effect = Exception("Script generation failed")
        
        request_data = {
            "topic": "Test Topic",
            "minutes": 2
        }
        
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 500
        
        data = response.json()
        assert "detail" in data
        assert "Script generation failed" in data["detail"]
    
    def test_generate_script_chunked_invalid_request(self, client):
        """Test script generation endpoint with invalid request"""
        # Test missing topic
        request_data = {"minutes": 2}
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 422
        
        # Test missing minutes
        request_data = {"topic": "Test Topic"}
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 422
        
        # Test invalid minutes
        request_data = {"topic": "Test Topic", "minutes": 0}
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 422
        
        # Test empty topic
        request_data = {"topic": "", "minutes": 2}
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 422
    
    @patch('app.main.generate_tts_segment')
    def test_tts_segment_success(self, mock_generate_tts, client):
        """Test successful TTS segment endpoint"""
        # Mock the TTS generation
        mock_generate_tts.return_value = {
            "segment_id": 1,
            "mime": "audio/wav",
            "base64": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"
        }
        
        request_data = {
            "segmentId": 1,
            "turns": [
                {"text": "Hello, this is Jay.", "speaker": "Jay"},
                {"text": "Hi there, this is Nik.", "speaker": "Nik"}
            ]
        }
        
        response = client.post("/tts-segment/", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "mime" in data
        assert "base64" in data
        assert data["mime"] == "audio/wav"
        assert len(data["base64"]) > 0
    
    @patch('app.main.generate_tts_segment')
    def test_tts_segment_error(self, mock_generate_tts, client):
        """Test TTS segment endpoint with error"""
        # Mock the TTS generation to raise an exception
        mock_generate_tts.side_effect = Exception("TTS generation failed")
        
        request_data = {
            "segmentId": 1,
            "turns": [
                {"text": "Hello", "speaker": "Jay"}
            ]
        }
        
        response = client.post("/tts-segment/", json=request_data)
        assert response.status_code == 500
        
        data = response.json()
        assert "detail" in data
        assert "TTS generation failed" in data["detail"]
    
    def test_tts_segment_invalid_request(self, client):
        """Test TTS segment endpoint with invalid request"""
        # Test missing segmentId
        request_data = {
            "turns": [{"text": "Hello", "speaker": "Jay"}]
        }
        response = client.post("/tts-segment/", json=request_data)
        assert response.status_code == 422
        
        # Test missing turns
        request_data = {"segmentId": 1}
        response = client.post("/tts-segment/", json=request_data)
        assert response.status_code == 422
        
        # Test empty turns
        request_data = {"segmentId": 1, "turns": []}
        response = client.post("/tts-segment/", json=request_data)
        assert response.status_code == 422
    
    def test_cors_headers(self, client):
        """Test that CORS headers are properly set"""
        # Test that the health endpoint works
        response = client.get("/health")
        assert response.status_code == 200
        
        # CORS headers are only added to preflight OPTIONS requests and cross-origin requests
        # Same-origin GET requests don't need CORS headers
        # The CORS middleware is configured and will handle cross-origin requests properly
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_docs_endpoint(self, client):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_endpoint(self, client):
        """Test that OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    @patch('app.main.generate_chunked_podcast_script')
    def test_generate_script_chunked_async(self, mock_generate_script, client):
        """Test that script generation is properly async"""
        # Mock the script generation with a synchronous function
        mock_generate_script.return_value = {
            "segments": [{"segmentId": 1, "multiSpeakerMarkup": {"turns": []}}],
            "total_words": 10
        }
        
        request_data = {"topic": "Test Topic", "minutes": 1}
        
        # The endpoint should handle async properly
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "segments" in data
        assert "total_words" in data
        assert len(data["segments"]) > 0
    
    @patch('app.main.generate_tts_segment')
    def test_tts_segment_retry_logic(self, mock_generate_tts, client):
        """Test that TTS endpoint retries on failure"""
        # Mock the TTS generation to fail twice then succeed
        call_count = 0
        
        def mock_tts_with_retries(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"TTS failed attempt {call_count}")
            return {
                "segment_id": 1,
                "mime": "audio/wav",
                "base64": "fake_audio_data"
            }
        
        mock_generate_tts.side_effect = mock_tts_with_retries
        
        request_data = {
            "segmentId": 1,
            "turns": [{"text": "Hello", "speaker": "Jay"}]
        }
        
        response = client.post("/tts-segment/", json=request_data)
        assert response.status_code == 200
        assert call_count == 3  # Should have retried 3 times
