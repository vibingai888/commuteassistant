"""
Unit tests for TTS service
"""

import pytest
import base64
from unittest.mock import Mock, patch, MagicMock
from app.services.tts_service import tts_for_turns


@pytest.mark.unit
class TestTTSService:
    """Test cases for TTS service"""
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_valid_input(self, mock_get_client):
        """Test TTS generation with valid input"""
        turns = [
            {"text": "Hello, this is Jay speaking.", "speaker": "Jay"},
            {"text": "Hi there, this is Nik here.", "speaker": "Nik"},
            {"text": "Welcome to our podcast!", "speaker": "Jay"}
        ]
        
        with patch('app.services.tts_service.get_tts_client') as mock_get_client:
            # Mock the TTS client
            mock_client = MagicMock()
            mock_model = MagicMock()
            mock_response = MagicMock()
            
            # Mock the response structure
            mock_candidate = MagicMock()
            mock_content = MagicMock()
            mock_part = MagicMock()
            mock_inline_data = MagicMock()
            
            # Set up the mock response chain
            mock_inline_data.mime_type = "audio/wav"
            mock_inline_data.data = base64.b64encode(b"fake_audio_data").decode('utf-8')
            mock_part.inline_data = mock_inline_data
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]
            
            mock_model.generate_content.return_value = mock_response
            mock_client.models = mock_model
            mock_get_client.return_value = mock_client
            
            result = tts_for_turns(turns)
            
            assert "mime" in result
            assert "base64" in result
            assert result["mime"] == "audio/wav"
            assert len(result["base64"]) > 0
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    def test_tts_for_turns_empty_turns(self):
        """Test TTS generation with empty turns"""
        with pytest.raises(ValueError, match="Turns cannot be empty"):
            tts_for_turns([])
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_invalid_turn_structure(self, mock_get_client):
        """Test TTS generation with invalid turn structure"""
        turns = [
            {"text": "Hello", "speaker": "Jay"},
            {"text": "Hi"},  # Missing speaker
            {"speaker": "Nik"}  # Missing text
        ]
        
        with patch('app.services.tts_service.get_tts_client') as mock_get_client:
            mock_client = MagicMock()
            mock_model = MagicMock()
            mock_response = MagicMock()
            
            # Mock successful response
            mock_candidate = MagicMock()
            mock_content = MagicMock()
            mock_part = MagicMock()
            mock_inline_data = MagicMock()
            
            mock_inline_data.mime_type = "audio/wav"
            mock_inline_data.data = base64.b64encode(b"fake_audio_data").decode('utf-8')
            mock_part.inline_data = mock_inline_data
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]
            
            mock_model.generate_content.return_value = mock_response
            mock_client.models = mock_model
            mock_get_client.return_value = mock_client
            
            # Should still work even with invalid turns (filtered out)
            result = tts_for_turns(turns)
            assert "mime" in result
            assert "base64" in result
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_api_error(self, mock_get_client):
        """Test TTS generation with API error"""
        turns = [
            {"text": "Hello", "speaker": "Jay"}
        ]
        
        # Mock the TTS client to raise an exception
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("TTS API Error")
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        with pytest.raises(Exception, match="TTS API Error"):
            tts_for_turns(turns)
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_no_candidates(self, mock_get_client):
        """Test TTS generation with no candidates in response"""
        turns = [
            {"text": "Hello", "speaker": "Jay"}
        ]
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = []  # Empty candidates
        
        mock_model.generate_content.return_value = mock_response
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        with pytest.raises(ValueError, match="Empty TTS response \\(no candidates\\)"):
            tts_for_turns(turns)
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_no_content_parts(self, mock_get_client):
        """Test TTS generation with no content parts"""
        turns = [
            {"text": "Hello", "speaker": "Jay"}
        ]
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_content.parts = []  # Empty parts
        
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_model.generate_content.return_value = mock_response
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        with pytest.raises(ValueError, match="TTS candidate missing content.parts"):
            tts_for_turns(turns)
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_no_inline_data(self, mock_get_client):
        """Test TTS generation with no inline data"""
        turns = [
            {"text": "Hello", "speaker": "Jay"}
        ]
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data = None  # No inline data
        
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_model.generate_content.return_value = mock_response
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        with pytest.raises(ValueError, match="TTS response missing inline audio data"):
            tts_for_turns(turns)
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_pcm_to_wav_conversion(self, mock_get_client):
        """Test TTS generation with PCM data that needs conversion to WAV"""
        turns = [
            {"text": "Hello", "speaker": "Jay"}
        ]
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_inline_data = MagicMock()
        
        # Mock PCM data (not WAV)
        mock_inline_data.mime_type = "audio/pcm"
        mock_inline_data.data = base64.b64encode(b"fake_pcm_data").decode('utf-8')
        mock_part.inline_data = mock_inline_data
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_model.generate_content.return_value = mock_response
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        result = tts_for_turns(turns)
        
        assert "mime" in result
        assert "base64" in result
        assert result["mime"] == "audio/wav"  # Should be converted to WAV
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_bytes_data(self, mock_get_client):
        """Test TTS generation with bytes data instead of base64 string"""
        turns = [
            {"text": "Hello", "speaker": "Jay"}
        ]
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_inline_data = MagicMock()
        
        # Mock bytes data instead of base64 string
        mock_inline_data.mime_type = "audio/wav"
        mock_inline_data.data = b"fake_audio_bytes"
        mock_part.inline_data = mock_inline_data
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_model.generate_content.return_value = mock_response
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        result = tts_for_turns(turns)
        
        assert "mime" in result
        assert "base64" in result
        assert result["mime"] == "audio/wav"
    
    @patch('app.services.tts_service.config.GOOGLE_API_KEY', 'fake_api_key')
    @patch('app.services.tts_service.get_tts_client')
    def test_tts_for_turns_conversation_building(self, mock_get_client):
        """Test that conversation text is built correctly from turns"""
        turns = [
            {"text": "Hello, this is Jay.", "speaker": "Jay"},
            {"text": "Hi Jay, this is Nik.", "speaker": "Nik"},
            {"text": "Welcome to our podcast!", "speaker": "Jay"}
        ]

        with patch('app.services.tts_service.get_tts_client') as mock_get_client:
            mock_client = MagicMock()
            mock_model = MagicMock()
            mock_response = MagicMock()

            # Mock successful response
            mock_candidate = MagicMock()
            mock_content = MagicMock()
            mock_part = MagicMock()
            mock_inline_data = MagicMock()

            mock_inline_data.mime_type = "audio/wav"
            mock_inline_data.data = base64.b64encode(b"fake_audio_data").decode('utf-8')
            mock_part.inline_data = mock_inline_data
            mock_content.parts = [mock_part]
            mock_candidate.content = mock_content
            mock_response.candidates = [mock_candidate]

            mock_model.generate_content.return_value = mock_response
            mock_client.models = mock_model
            mock_get_client.return_value = mock_client

            result = tts_for_turns(turns)

            # Verify the result structure
            assert "mime" in result
            assert "base64" in result

            # Check that the conversation building was called correctly
            # We can verify this by checking the mock calls
            mock_model.generate_content.assert_called_once()
            call_args = mock_model.generate_content.call_args
            if call_args and call_args[0]:  # Check if args exist
                content = call_args[0][0]  # First positional argument
                assert "Jay: Hello, this is Jay." in content
                assert "Nik: Hi Jay, this is Nik." in content
                assert "Jay: Welcome to our podcast!" in content
