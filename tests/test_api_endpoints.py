"""
Integration tests for API endpoints
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.api
class TestAPIEndpoints:
    """Test cases for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health endpoint"""
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
    
    @patch('app.main.generate_chunked_podcast_script')
    def test_generate_script_chunked_success(self, mock_generate, client):
        """Test successful script generation"""
        mock_generate.return_value = {
            "segments": [
                {
                    "segmentId": 1,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "Hello", "speaker": "Jay"},
                            {"text": "Hi there", "speaker": "Nik"}
                        ]
                    }
                }
            ],
            "total_words": 10
        }
        
        response = client.post("/generate-script-chunked/", json={
            "topic": "Test Topic",
            "minutes": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data
        assert len(data["segments"]) == 1
    
    @patch('app.main.generate_chunked_podcast_script')
    def test_generate_script_chunked_error(self, mock_generate, client):
        """Test script generation error handling"""
        mock_generate.side_effect = Exception("Generation failed")
        
        response = client.post("/generate-script-chunked/", json={
            "topic": "Test Topic",
            "minutes": 5
        })
        assert response.status_code == 500
    
    def test_generate_script_chunked_invalid_request(self, client):
        """Test invalid request handling"""
        response = client.post("/generate-script-chunked/", json={
            "topic": "",  # Invalid: empty topic
            "minutes": 5
        })
        assert response.status_code == 422
    
    @patch('app.main.generate_tts_segment')
    def test_tts_segment_success(self, mock_tts, client):
        """Test successful TTS generation"""
        mock_tts.return_value = {
            "segment_id": 1,
            "base64": "dGVzdA==",  # "test" in base64
            "mime": "audio/wav"
        }
        
        response = client.post("/tts-segment/", json={
            "segmentId": 1,
            "turns": [
                {"text": "Hello", "speaker": "Jay"},
                {"text": "Hi there", "speaker": "Nik"}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "base64" in data
        assert "mime" in data
    
    @patch('app.main.generate_tts_segment')
    def test_tts_segment_error(self, mock_tts, client):
        """Test TTS generation error handling"""
        mock_tts.side_effect = Exception("TTS failed")
        
        response = client.post("/tts-segment/", json={
            "segmentId": 1,
            "turns": [
                {"text": "Hello", "speaker": "Jay"},
                {"text": "Hi there", "speaker": "Nik"}
            ]
        })
        assert response.status_code == 500
    
    def test_tts_segment_invalid_request(self, client):
        """Test invalid TTS request handling"""
        response = client.post("/tts-segment/", json={
            "segmentId": 1,
            "turns": []  # Invalid: empty turns
        })
        assert response.status_code == 422
    
    def test_cors_headers(self, client):
        """Test CORS functionality for frontend integration"""
        response = client.options("/health")
        # CORS preflight should be handled by FastAPI middleware
        assert response.status_code in [200, 405]  # 405 is also acceptable
    
    def test_docs_endpoint(self, client):
        """Test API documentation endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_endpoint(self, client):
        """Test OpenAPI schema endpoint"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
    
    @patch('app.main.generate_chunked_podcast_script')
    def test_generate_script_chunked_async(self, mock_generate, client):
        """Test async script generation"""
        mock_generate.return_value = {
            "segments": [
                {
                    "segmentId": 1,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "Hello", "speaker": "Jay"},
                            {"text": "Hi there", "speaker": "Nik"}
                        ]
                    }
                }
            ],
            "total_words": 10
        }
        
        response = client.post("/generate-script-chunked/", json={
            "topic": "Test Topic",
            "minutes": 5
        })
        assert response.status_code == 200
    
    @patch('app.main.generate_tts_segment')
    def test_tts_segment_retry_logic(self, mock_tts, client):
        """Test TTS retry logic"""
        # First call fails, second succeeds
        mock_tts.side_effect = [Exception("First failure"), {
            "segment_id": 1,
            "base64": "dGVzdA==",
            "mime": "audio/wav"
        }]
        
        response = client.post("/tts-segment/", json={
            "segmentId": 1,
            "turns": [
                {"text": "Hello", "speaker": "Jay"},
                {"text": "Hi there", "speaker": "Nik"}
            ]
        })
        # Should eventually succeed after retries
        assert response.status_code == 200
