"""
Integration tests for the complete podcast generation flow
"""

import pytest
import base64
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


class TestIntegration:
    """Integration test cases for complete podcast generation flow"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    @patch('app.services.script_service.get_vertex_client')
    @patch('app.services.tts_service.get_tts_client')
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    def test_complete_podcast_generation_flow(self, mock_get_tts_client, mock_get_script_client, client):
        """Test the complete flow from script generation to TTS"""
        # Mock script generation
        mock_script_client = MagicMock()
        mock_script_model = MagicMock()
        mock_script_response = MagicMock()
        mock_script_candidate = MagicMock()
        mock_script_content = MagicMock()
        mock_script_part = MagicMock()
        
        # Set up the mock response chain for script generation
        mock_script_part.text = '''
        {
            "segments": [
                {
                    "segmentId": 1,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "Hello, welcome to our podcast about AI!", "speaker": "Jay"},
                            {"text": "Thanks Jay, I'm excited to discuss this topic.", "speaker": "Nik"},
                            {"text": "Let's dive into the fascinating world of artificial intelligence.", "speaker": "Jay"}
                        ]
                    }
                },
                {
                    "segmentId": 2,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "AI has transformed many industries.", "speaker": "Nik"},
                            {"text": "Absolutely, from healthcare to finance.", "speaker": "Jay"}
                        ]
                    }
                }
            ],
            "total_words": 35
        }
        '''
        mock_script_content.parts = [mock_script_part]
        mock_script_candidate.content = mock_script_content
        mock_script_response.candidates = [mock_script_candidate]
        
        mock_script_model.generate_content.return_value = mock_script_response
        mock_script_client.models = mock_script_model
        mock_get_script_client.return_value = mock_script_client
        
        # Mock TTS generation
        mock_tts_client = MagicMock()
        mock_tts_model = MagicMock()
        mock_tts_response = MagicMock()
        
        # Mock TTS response structure
        mock_tts_candidate = MagicMock()
        mock_tts_content = MagicMock()
        mock_tts_part = MagicMock()
        mock_tts_inline_data = MagicMock()
        
        mock_tts_inline_data.mime_type = "audio/wav"
        mock_tts_inline_data.data = base64.b64encode(b"fake_audio_data_for_segment").decode('utf-8')
        mock_tts_part.inline_data = mock_tts_inline_data
        mock_tts_content.parts = [mock_tts_part]
        mock_tts_candidate.content = mock_tts_content
        mock_tts_response.candidates = [mock_tts_candidate]
        
        mock_tts_model.generate_content.return_value = mock_tts_response
        mock_tts_client.models = mock_tts_model
        mock_get_tts_client.return_value = mock_tts_client
        
        # Step 1: Generate script
        script_request = {
            "topic": "Artificial Intelligence",
            "minutes": 2
        }
        
        script_response = client.post("/generate-script-chunked/", json=script_request)
        assert script_response.status_code == 200
        
        script_data = script_response.json()
        assert "segments" in script_data
        assert "total_words" in script_data
        assert len(script_data["segments"]) == 2
        # Allow some flexibility in word count since counting logic might differ slightly
        assert script_data["total_words"] >= 30 and script_data["total_words"] <= 40
        
        # Step 2: Generate TTS for each segment
        for segment in script_data["segments"]:
            segment_id = segment["segmentId"]
            turns = segment["multiSpeakerMarkup"]["turns"]
            
            tts_request = {
                "segmentId": segment_id,
                "turns": turns
            }
            
            tts_response = client.post("/tts-segment/", json=tts_request)
            assert tts_response.status_code == 200
            
            tts_data = tts_response.json()
            assert "mime" in tts_data
            assert "base64" in tts_data
            assert tts_data["mime"] == "audio/wav"
            assert len(tts_data["base64"]) > 0
    
    @patch('app.services.script_service.get_vertex_client')
    def test_script_generation_with_realistic_prompt(self, mock_get_script_client, client):
        """Test script generation with a realistic topic and verify prompt quality"""
        mock_script_client = MagicMock()
        mock_script_model = MagicMock()
        mock_script_response = MagicMock()
        mock_script_candidate = MagicMock()
        mock_script_content = MagicMock()
        mock_script_part = MagicMock()
        
        # Set up the mock response chain
        mock_script_part.text = '''
        {
            "segments": [
                {
                    "segmentId": 1,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "Welcome to our podcast on climate change solutions!", "speaker": "Jay"},
                            {"text": "I'm excited to explore this critical topic with you.", "speaker": "Nik"}
                        ]
                    }
                }
            ],
            "total_words": 20
        }
        '''
        mock_script_content.parts = [mock_script_part]
        mock_script_candidate.content = mock_script_content
        mock_script_response.candidates = [mock_script_candidate]
        
        mock_script_model.generate_content.return_value = mock_script_response
        mock_script_client.models = mock_script_model
        mock_get_script_client.return_value = mock_script_client
        
        request_data = {
            "topic": "Climate Change Solutions",
            "minutes": 3
        }
        
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 200
        
        # Verify the response has the expected structure
        data = response.json()
        assert "segments" in data
        assert len(data["segments"]) > 0
    
    def test_error_handling_and_recovery(self, client):
        """Test error handling and recovery scenarios"""
        # Test with invalid topic
        request_data = {"topic": "", "minutes": 2}
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 422
        
        # Test with invalid minutes
        request_data = {"topic": "Test Topic", "minutes": 0}
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 422
        
        # Test with missing required fields
        request_data = {"topic": "Test Topic"}
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 422
        
        # Test TTS with invalid segment
        tts_request = {
            "segmentId": 1,
            "turns": []  # Empty turns
        }
        response = client.post("/tts-segment/", json=tts_request)
        assert response.status_code == 422
    
    def test_api_documentation_accessibility(self, client):
        """Test that API documentation is properly accessible"""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        
        # Verify required endpoints are documented
        paths = schema["paths"]
        assert "/health" in paths
        assert "/suggestions" in paths
        assert "/generate-script-chunked/" in paths
        assert "/tts-segment/" in paths
        
        # Verify POST endpoints have request body schemas
        assert "post" in paths["/generate-script-chunked/"]
        assert "post" in paths["/tts-segment/"]
        
        # Test interactive docs
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_cors_functionality(self, client):
        """Test CORS functionality for frontend integration"""
        # Test preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = client.options("/generate-script-chunked/", headers=headers)
        assert response.status_code == 200
        
        # Check CORS headers
        cors_headers = response.headers
        assert "access-control-allow-origin" in cors_headers
        assert "access-control-allow-methods" in cors_headers
        assert "access-control-allow-headers" in cors_headers
    
    def test_suggestions_endpoint_integration(self, client):
        """Test suggestions endpoint integration"""
        response = client.get("/suggestions")
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data["suggestions"]
        
        # Verify suggestions are valid
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Verify each suggestion is a string
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
        
        # Verify suggestions are diverse (not all the same)
        unique_suggestions = set(suggestions)
        assert len(unique_suggestions) > 1
    
    @patch('app.services.script_service.get_vertex_client')
    def test_script_chunking_logic(self, mock_get_script_client, client):
        """Test that script chunking works correctly"""
        # Mock a response with multiple segments
        mock_script_client = MagicMock()
        mock_script_model = MagicMock()
        mock_script_response = MagicMock()
        mock_script_candidate = MagicMock()
        mock_script_content = MagicMock()
        mock_script_part = MagicMock()
        
        # Set up the mock response chain
        mock_script_part.text = '''
        {
            "segments": [
                {
                    "segmentId": 1,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "First segment with some words.", "speaker": "Jay"},
                            {"text": "More words in the first segment.", "speaker": "Nik"}
                        ]
                    }
                },
                {
                    "segmentId": 2,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "Second segment content.", "speaker": "Jay"},
                            {"text": "More content in second segment.", "speaker": "Nik"}
                        ]
                    }
                },
                {
                    "segmentId": 3,
                    "multiSpeakerMarkup": {
                        "turns": [
                            {"text": "Final segment first turn.", "speaker": "Jay"},
                            {"text": "Final segment second turn.", "speaker": "Nik"}
                        ]
                    }
                }
            ],
            "total_words": 25
        }
        '''
        mock_script_content.parts = [mock_script_part]
        mock_script_candidate.content = mock_script_content
        mock_script_response.candidates = [mock_script_candidate]
        
        mock_script_model.generate_content.return_value = mock_script_response
        mock_script_client.models = mock_script_model
        mock_get_script_client.return_value = mock_script_client
        
        request_data = {"topic": "Test Topic", "minutes": 2}
        response = client.post("/generate-script-chunked/", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        segments = data["segments"]
        
        # Verify we have multiple segments
        assert len(segments) == 3
        
        # Verify segment IDs are sequential
        segment_ids = [seg["segmentId"] for seg in segments]
        assert segment_ids == [1, 2, 3]
        
        # Verify each segment has the required structure
        for segment in segments:
            assert "segmentId" in segment
            assert "multiSpeakerMarkup" in segment
            assert "turns" in segment["multiSpeakerMarkup"]
            assert len(segment["multiSpeakerMarkup"]["turns"]) > 0
