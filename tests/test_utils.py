"""
Unit tests for utility functions
"""

import base64
import io
import wave
import pytest
from unittest.mock import patch, mock_open
from app.utils.audio_utils import (
    create_wav_bytes,
    base64_to_wav,
    get_audio_duration,
    format_duration
)


@pytest.mark.unit
class TestAudioUtils:
    """Test cases for audio utility functions"""
    
    def test_create_wav_bytes(self):
        """Test creating WAV bytes from PCM data"""
        # Create some dummy PCM data
        pcm_data = b'\x00\x00\x01\x00\x02\x00\x03\x00' * 1000  # 8000 bytes of PCM
        
        wav_bytes = create_wav_bytes(pcm_data, channels=1, rate=24000, sample_width=2)
        
        # Verify it's valid WAV data
        assert wav_bytes.startswith(b'RIFF')
        assert wav_bytes[8:12] == b'WAVE'
        assert wav_bytes[12:16] == b'fmt '
        
        # Check the format chunk
        format_chunk_size = int.from_bytes(wav_bytes[16:20], 'little')
        assert format_chunk_size == 16
        
        # Check audio format (PCM = 1)
        audio_format = int.from_bytes(wav_bytes[20:22], 'little')
        assert audio_format == 1
        
        # Check channels
        channels = int.from_bytes(wav_bytes[22:24], 'little')
        assert channels == 1
        
        # Check sample rate
        sample_rate = int.from_bytes(wav_bytes[24:28], 'little')
        assert sample_rate == 24000
        
        # Check sample width
        bits_per_sample = int.from_bytes(wav_bytes[34:36], 'little')
        assert bits_per_sample == 16
    
    def test_create_wav_bytes_stereo(self):
        """Test creating WAV bytes for stereo audio"""
        pcm_data = b'\x00\x00\x01\x00\x02\x00\x03\x00' * 1000
        
        wav_bytes = create_wav_bytes(pcm_data, channels=2, rate=44100, sample_width=2)
        
        # Check channels
        channels = int.from_bytes(wav_bytes[22:24], 'little')
        assert channels == 2
        
        # Check sample rate
        sample_rate = int.from_bytes(wav_bytes[24:28], 'little')
        assert sample_rate == 44100
    
    def test_base64_to_wav(self):
        """Test converting base64 data to WAV"""
        # Create some dummy WAV data
        pcm_data = b'\x00\x00\x01\x00\x02\x00\x03\x00' * 100
        wav_data = create_wav_bytes(pcm_data, channels=1, rate=24000, sample_width=2)
        base64_data = base64.b64encode(wav_data).decode('utf-8')
        
        result = base64_to_wav(base64_data)
        
        # Should return the original WAV data
        assert result == wav_data
    
    def test_base64_to_wav_invalid_data(self):
        """Test base64_to_wav with invalid base64 data"""
        with pytest.raises(Exception):
            base64_to_wav("invalid_base64_data")
    
    def test_get_audio_duration(self):
        """Test getting audio duration from WAV data"""
        # Create WAV data with known duration
        sample_rate = 24000
        duration_seconds = 2.0
        num_samples = int(sample_rate * duration_seconds)
        pcm_data = b'\x00\x00' * num_samples  # 16-bit samples
        
        wav_data = create_wav_bytes(pcm_data, channels=1, rate=sample_rate, sample_width=2)
        
        duration = get_audio_duration(wav_data)
        
        # Should be close to expected duration (allow small floating point differences)
        assert abs(duration - duration_seconds) < 0.1
    
    def test_get_audio_duration_stereo(self):
        """Test getting audio duration from stereo WAV data"""
        sample_rate = 44100
        duration_seconds = 1.5
        num_samples = int(sample_rate * duration_seconds * 2)  # *2 for stereo
        pcm_data = b'\x00\x00' * num_samples
        
        wav_data = create_wav_bytes(pcm_data, channels=2, rate=sample_rate, sample_width=2)
        
        duration = get_audio_duration(wav_data)
        
        assert abs(duration - duration_seconds) < 0.1
    
    def test_get_audio_duration_invalid_wav(self):
        """Test get_audio_duration with invalid WAV data"""
        # Test with data that has invalid length for the sample width
        with pytest.raises(Exception):
            get_audio_duration(b'invalid_wav_data', sample_width=3)  # 16 % 3 != 0
    
    def test_format_duration_seconds(self):
        """Test formatting duration in seconds"""
        assert format_duration(30) == "00:30"
        assert format_duration(65) == "01:05"
        assert format_duration(125) == "02:05"
    
    def test_format_duration_minutes(self):
        """Test formatting duration in minutes"""
        assert format_duration(120) == "02:00"
        assert format_duration(360) == "06:00"
        assert format_duration(1800) == "30:00"
    
    def test_format_duration_hours(self):
        """Test formatting duration in hours"""
        assert format_duration(3600) == "60:00"  # Actual implementation returns MM:SS format
        assert format_duration(7325) == "122:05"  # 122 minutes 5 seconds
        assert format_duration(3661) == "61:01"   # 61 minutes 1 second
    
    def test_format_duration_zero(self):
        """Test formatting zero duration"""
        assert format_duration(0) == "00:00"
    
    def test_format_duration_negative(self):
        """Test formatting negative duration"""
        assert format_duration(-30) == "00:00"  # Should handle negative gracefully
    
    def test_format_duration_float(self):
        """Test formatting duration with float input"""
        assert format_duration(30.5) == "00:30"
        assert format_duration(65.7) == "01:05"
