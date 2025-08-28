"""
Unit tests for Pydantic models
"""

import pytest
from pydantic import ValidationError
from app.models import (
    PodcastRequest, 
    ScriptChunkedResponse, 
    ScriptSegment, 
    TTSSegmentRequest, 
    TTSSegmentResponse
)


class TestPodcastRequest:
    """Test cases for PodcastRequest model"""
    
    def test_valid_request(self):
        """Test valid podcast request"""
        data = {
            "topic": "Test Topic",
            "minutes": 5
        }
        request = PodcastRequest(**data)
        assert request.topic == "Test Topic"
        assert request.minutes == 5
    
    def test_missing_topic(self):
        """Test validation error when topic is missing"""
        data = {"minutes": 5}
        with pytest.raises(ValidationError):
            PodcastRequest(**data)
    
    def test_missing_minutes(self):
        """Test validation error when minutes is missing"""
        data = {"topic": "Test Topic"}
        with pytest.raises(ValidationError):
            PodcastRequest(**data)
    
    def test_empty_topic(self):
        """Test validation error when topic is empty"""
        data = {"topic": "", "minutes": 5}
        with pytest.raises(ValidationError):
            PodcastRequest(**data)
    
    def test_negative_minutes(self):
        """Test validation error when minutes is negative"""
        data = {"topic": "Test Topic", "minutes": -1}
        with pytest.raises(ValidationError):
            PodcastRequest(**data)
    
    def test_zero_minutes(self):
        """Test validation error when minutes is zero"""
        data = {"topic": "Test Topic", "minutes": 0}
        with pytest.raises(ValidationError):
            PodcastRequest(**data)
    
    def test_large_minutes(self):
        """Test validation error when minutes exceeds maximum"""
        data = {"topic": "Test Topic", "minutes": 31}
        with pytest.raises(ValidationError):
            PodcastRequest(**data)
    
    def test_maximum_minutes(self):
        """Test that maximum minutes (30) is allowed"""
        data = {"topic": "Test Topic", "minutes": 30}
        request = PodcastRequest(**data)
        assert request.minutes == 30


class TestScriptSegment:
    """Test cases for ScriptSegment model"""
    
    def test_valid_segment(self):
        """Test valid script segment"""
        data = {
            "segmentId": 1,
            "multiSpeakerMarkup": {
                "turns": [
                    {"text": "Hello", "speaker": "Jay"},
                    {"text": "Hi there", "speaker": "Nik"}
                ]
            }
        }
        segment = ScriptSegment(**data)
        assert segment.segment_id == 1
        assert segment.multi_speaker_markup["turns"][0]["text"] == "Hello"
        assert segment.multi_speaker_markup["turns"][0]["speaker"] == "Jay"
    
    def test_camel_case_alias(self):
        """Test that camelCase field names work with alias"""
        data = {
            "segmentId": 2,
            "multiSpeakerMarkup": {
                "turns": [
                    {"text": "Test", "speaker": "Jay"}
                ]
            }
        }
        segment = ScriptSegment(**data)
        assert segment.segment_id == 2  # Should map from segmentId
    
    def test_missing_segment_id(self):
        """Test validation error when segment_id is missing"""
        data = {
            "multiSpeakerMarkup": {
                "turns": [{"text": "Hello", "speaker": "Jay"}]
            }
        }
        with pytest.raises(ValidationError):
            ScriptSegment(**data)
    
    def test_missing_markup(self):
        """Test validation error when multi_speaker_markup is missing"""
        data = {"segmentId": 1}
        with pytest.raises(ValidationError):
            ScriptSegment(**data)


class TestScriptChunkedResponse:
    """Test cases for ScriptChunkedResponse model"""
    
    def test_valid_response(self):
        """Test valid script chunked response"""
        data = {
            "segments": [
                {
                    "segmentId": 1,
                    "multiSpeakerMarkup": {
                        "turns": [{"text": "Hello", "speaker": "Jay"}]
                    }
                }
            ],
            "total_words": 100
        }
        response = ScriptChunkedResponse(**data)
        assert len(response.segments) == 1
        assert response.total_words == 100
    
    def test_empty_segments(self):
        """Test validation error when segments is empty"""
        data = {
            "segments": [],
            "total_words": 0
        }
        with pytest.raises(ValidationError):
            ScriptChunkedResponse(**data)
    
    def test_negative_total_words(self):
        """Test validation error when total_words is negative"""
        data = {
            "segments": [
                {
                    "segmentId": 1,
                    "multiSpeakerMarkup": {
                        "turns": [{"text": "Hello", "speaker": "Jay"}]
                    }
                }
            ],
            "total_words": -1
        }
        with pytest.raises(ValidationError):
            ScriptChunkedResponse(**data)


class TestTTSSegmentRequest:
    """Test cases for TTSSegmentRequest model"""
    
    def test_valid_request(self):
        """Test valid TTS segment request"""
        data = {
            "segmentId": 1,
            "turns": [
                {"text": "Hello", "speaker": "Jay"},
                {"text": "Hi there", "speaker": "Nik"}
            ]
        }
        request = TTSSegmentRequest(**data)
        assert request.segment_id == 1
        assert len(request.turns) == 2
        assert request.turns[0]["text"] == "Hello"
        assert request.turns[0]["speaker"] == "Jay"
    
    def test_camel_case_alias(self):
        """Test that camelCase field names work with alias"""
        data = {
            "segmentId": 2,
            "turns": [{"text": "Test", "speaker": "Jay"}]
        }
        request = TTSSegmentRequest(**data)
        assert request.segment_id == 2  # Should map from segmentId
    
    def test_missing_segment_id(self):
        """Test validation error when segment_id is missing"""
        data = {
            "turns": [{"text": "Hello", "speaker": "Jay"}]
        }
        with pytest.raises(ValidationError):
            TTSSegmentRequest(**data)
    
    def test_missing_turns(self):
        """Test validation error when turns is missing"""
        data = {"segmentId": 1}
        with pytest.raises(ValidationError):
            TTSSegmentRequest(**data)
    
    def test_empty_turns(self):
        """Test validation error when turns is empty"""
        data = {
            "segmentId": 1,
            "turns": []
        }
        with pytest.raises(ValidationError):
            TTSSegmentRequest(**data)
    
    def test_invalid_turn_structure(self):
        """Test validation error when turn structure is invalid"""
        data = {
            "segmentId": 1,
            "turns": [
                {"text": "Hello"},  # Missing speaker
                {"speaker": "Jay"}   # Missing text
            ]
        }
        with pytest.raises(ValidationError):
            TTSSegmentRequest(**data)


class TestTTSSegmentResponse:
    """Test cases for TTSSegmentResponse model"""
    
    def test_valid_response(self):
        """Test valid TTS segment response"""
        data = {
            "segment_id": 1,
            "mime": "audio/wav",
            "base64": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"
        }
        response = TTSSegmentResponse(**data)
        assert response.segment_id == 1
        assert response.mime == "audio/wav"
        assert len(response.base64) > 0
    
    def test_missing_segment_id(self):
        """Test validation error when segment_id is missing"""
        data = {
            "mime": "audio/wav",
            "base64": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"
        }
        with pytest.raises(ValidationError):
            TTSSegmentResponse(**data)
    
    def test_missing_mime(self):
        """Test validation error when mime is missing"""
        data = {
            "segment_id": 1,
            "base64": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"
        }
        with pytest.raises(ValidationError):
            TTSSegmentResponse(**data)
    
    def test_missing_base64(self):
        """Test validation error when base64 is missing"""
        data = {
            "segment_id": 1,
            "mime": "audio/wav"
        }
        with pytest.raises(ValidationError):
            TTSSegmentResponse(**data)
    
    def test_empty_base64(self):
        """Test validation error when base64 is empty"""
        data = {
            "segment_id": 1,
            "mime": "audio/wav",
            "base64": ""
        }
        with pytest.raises(ValidationError):
            TTSSegmentResponse(**data)
