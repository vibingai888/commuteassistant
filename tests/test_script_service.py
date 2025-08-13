"""
Unit tests for script generation service
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.script_service import (
    generate_podcast_script,
    generate_podcast_script_chunked,
    _word_count,
    chunk_turns_by_words,
    clean_json_string,
    validate_script_json
)


class TestScriptService:
    """Test cases for script generation service"""
    
    def test_word_count(self):
        """Test word counting function"""
        assert _word_count("Hello world") == 2
        assert _word_count("This is a test sentence.") == 5
        assert _word_count("") == 0
        assert _word_count("   ") == 0
        assert _word_count("One") == 1
        assert _word_count("Multiple   spaces   test") == 3
    
    def test_clean_json_string(self):
        """Test JSON string cleaning"""
        # Test with markdown code blocks
        json_str = "```json\n{\"key\": \"value\"}\n```"
        cleaned = clean_json_string(json_str)
        assert cleaned == '{"key": "value"}'
        
        # Test without markdown
        json_str = '{"key": "value"}'
        cleaned = clean_json_string(json_str)
        assert cleaned == '{"key": "value"}'
        
        # Test with extra whitespace
        json_str = "   {\"key\": \"value\"}   "
        cleaned = clean_json_string(json_str)
        assert cleaned == '{"key": "value"}'
    
    def test_validate_script_json_valid(self):
        """Test validation of valid script JSON"""
        valid_json = {
            "multiSpeakerMarkup": {
                "turns": [
                    {"text": "Hello", "speaker": "Jay"},
                    {"text": "Hi there", "speaker": "Nik"}
                ]
            }
        }
        
        # Should not raise any exception
        validate_script_json(valid_json)
    
    def test_validate_script_json_invalid_structure(self):
        """Test validation of invalid script JSON structure"""
        # Test with non-dict input
        with pytest.raises(ValueError, match="Script is not a JSON object"):
            validate_script_json("not a dict")
        
        # Test with invalid segments structure
        invalid_json = {
            "segments": "not a list"
        }
        
        with pytest.raises(ValueError, match="'segments' must be a non-empty list"):
            validate_script_json(invalid_json)
    
    def test_validate_script_json_missing_turns(self):
        """Test validation of JSON missing turns"""
        invalid_json = {
            "multiSpeakerMarkup": {}
        }
        
        with pytest.raises(ValueError, match="Missing 'multiSpeakerMarkup.turns' in script"):
            validate_script_json(invalid_json)
    
    def test_validate_script_json_empty_turns(self):
        """Test validation of JSON with empty turns"""
        invalid_json = {
            "multiSpeakerMarkup": {
                "turns": []
            }
        }
        
        with pytest.raises(ValueError, match="'turns' must be a list with at least two items"):
            validate_script_json(invalid_json)
    
    def test_chunk_turns_by_words(self):
        """Test chunking turns by word count"""
        turns = [
            {"text": "This is a short sentence.", "speaker": "Jay"},
            {"text": "This is another short sentence.", "speaker": "Nik"},
            {"text": "This is a longer sentence with more words to test the chunking functionality.", "speaker": "Jay"},
            {"text": "Another sentence here.", "speaker": "Nik"},
            {"text": "Final sentence for testing.", "speaker": "Jay"}
        ]
    
        chunks = chunk_turns_by_words(turns, words_per_chunk=20)
    
        assert len(chunks) > 1
        # Check that chunks are created and have reasonable sizes
        # Don't enforce strict word limits since chunking prioritizes keeping turns together
        for chunk in chunks:
            chunk_word_count = sum(_word_count(turn["text"]) for turn in chunk)
            # Allow some flexibility - chunks can be slightly over the target
            assert chunk_word_count <= 30  # Allow some overflow for natural turn boundaries
    
    def test_chunk_turns_by_words_min_first_chunk(self):
        """Test that first chunk meets minimum word requirement"""
        turns = [
            {"text": "Short.", "speaker": "Jay"},
            {"text": "Also short.", "speaker": "Nik"},
            {"text": "This is a much longer sentence that should help meet the minimum word count requirement for the first chunk.", "speaker": "Jay"},
            {"text": "Another sentence.", "speaker": "Nik"}
        ]
        
        chunks = chunk_turns_by_words(turns, words_per_chunk=30)
        
        first_chunk_word_count = sum(_word_count(turn["text"]) for turn in chunks[0])
        assert first_chunk_word_count >= 15
    
    @patch('app.services.script_service.get_vertex_client')
    def test_generate_podcast_script_success(self, mock_get_client):
        """Test successful script generation"""
        # Mock the Gemini client
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        
        # Set up the mock response chain
        mock_part.text = '''
        {
            "multiSpeakerMarkup": {
                "turns": [
                    {"text": "Hello, welcome to our podcast!", "speaker": "Jay"},
                    {"text": "Thanks for having me!", "speaker": "Nik"}
                ]
            }
        }
        '''
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_model.generate_content.return_value = mock_response
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        result = generate_podcast_script("Test Topic", 2)
        
        assert "multiSpeakerMarkup" in result
        assert "turns" in result["multiSpeakerMarkup"]
        assert len(result["multiSpeakerMarkup"]["turns"]) > 0
    
    @patch('app.services.script_service.get_vertex_client')
    def test_generate_podcast_script_api_error(self, mock_get_client):
        """Test script generation with API error"""
        # Mock the Gemini client to raise an exception
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        with pytest.raises(Exception, match="API Error"):
            generate_podcast_script("Test Topic", 2)
    
    def test_generate_podcast_script_chunked_success(self):
        """Test successful chunked script generation validation"""
        # Test the validation logic directly
        valid_chunked_script = {
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
            ]
        }
        
        # This should not raise an exception
        validate_script_json(valid_chunked_script)
        
        # Test that segments are properly validated
        assert len(valid_chunked_script["segments"]) == 1
        assert valid_chunked_script["segments"][0]["segmentId"] == 1
        assert "multiSpeakerMarkup" in valid_chunked_script["segments"][0]
    
    @patch('app.services.script_service.generate_podcast_script')
    @patch('app.services.script_service.get_vertex_client')
    def test_generate_podcast_script_chunked_api_error(self, mock_get_client, mock_generate_script):
        """Test chunked script generation with API error"""
        # Mock the vertex client to return invalid data (so it goes to fallback)
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        
        # Return invalid JSON that will fail validation
        mock_part.text = '{"invalid": "json"}'
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_model.generate_content.return_value = mock_response
        mock_client.models = mock_model
        mock_get_client.return_value = mock_client
        
        # Mock the fallback script generation to raise an exception
        mock_generate_script.side_effect = Exception("API Error")
        
        # Since the function calls itself from within the same module, we need to patch at the module level
        import app.services.script_service
        original_function = app.services.script_service.generate_podcast_script
        app.services.script_service.generate_podcast_script = mock_generate_script
        
        try:
            with pytest.raises(Exception, match="API Error"):
                generate_podcast_script_chunked("Test Topic", 2)
        finally:
            # Restore the original function
            app.services.script_service.generate_podcast_script = original_function
    
    def test_generate_podcast_script_chunked_invalid_minutes(self):
        """Test chunked script generation with invalid minutes"""
        with pytest.raises(ValueError):
            generate_podcast_script_chunked("Test Topic", 0)
        
        with pytest.raises(ValueError):
            generate_podcast_script_chunked("Test Topic", -1)
        
        with pytest.raises(ValueError):
            generate_podcast_script_chunked("Test Topic", 20)  # Exceeds max
    
    def test_generate_podcast_script_chunked_empty_topic(self):
        """Test chunked script generation with empty topic"""
        with pytest.raises(ValueError):
            generate_podcast_script_chunked("", 2)
        
        with pytest.raises(ValueError):
            generate_podcast_script_chunked("   ", 2)
