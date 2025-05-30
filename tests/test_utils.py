# -*- coding: utf-8 -*-
"""
Test utilities for Real-time Whisper Subtitles
Testing utilities and test data generation
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Test data for subtitle testing
SAMPLE_TRANSCRIPTION_DATA = [
    {
        "text": "Hello, welcome to the real-time speech recognition system.",
        "start_time": 0.0,
        "end_time": 3.5,
        "confidence": 0.95,
        "language": "en"
    },
    {
        "text": "This system uses faster-whisper for accurate transcription.",
        "start_time": 3.5,
        "end_time": 7.2,
        "confidence": 0.92,
        "language": "en"
    },
    {
        "text": "You can export subtitles in multiple formats.",
        "start_time": 7.2,
        "end_time": 10.8,
        "confidence": 0.89,
        "language": "en"
    },
    {
        "text": "The web interface provides real-time feedback.",
        "start_time": 10.8,
        "end_time": 14.5,
        "confidence": 0.94,
        "language": "en"
    }
]

def create_test_audio_data():
    """Create test audio data for testing purposes"""
    import numpy as np
    
    # Generate simple sine wave for testing
    sample_rate = 16000
    duration = 2.0  # seconds
    frequency = 440  # Hz (A note)
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
    
    return audio_data.astype(np.float32), sample_rate

def create_test_config():
    """Create test configuration"""
    return {
        "model_size": "tiny",
        "language": "en",
        "sample_rate": 16000,
        "device": "cpu",
        "compute_type": "int8"
    }

def create_test_subtitle_file(format_type: str = "json") -> str:
    """Create test subtitle file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
        if format_type == "json":
            test_data = {
                "session_id": "test_20250530_120000",
                "segments": SAMPLE_TRANSCRIPTION_DATA
            }
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        elif format_type == "txt":
            for i, data in enumerate(SAMPLE_TRANSCRIPTION_DATA):
                f.write(f"[{data['start_time']:.2f} - {data['end_time']:.2f}] {data['text']}\n")
        
        return f.name

def cleanup_test_files(file_paths: List[str]):
    """Clean up test files"""
    for file_path in file_paths:
        try:
            Path(file_path).unlink()
        except FileNotFoundError:
            pass

class MockTranscriptionResult:
    """Mock transcription result for testing"""
    
    def __init__(self, text: str, start_time: float, end_time: float, 
                 confidence: float, language: str):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.confidence = confidence
        self.language = language
        self.is_final = True

def get_test_transcription_results():
    """Get list of test transcription results"""
    results = []
    for data in SAMPLE_TRANSCRIPTION_DATA:
        results.append(MockTranscriptionResult(
            text=data["text"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            confidence=data["confidence"],
            language=data["language"]
        ))
    return results

if __name__ == "__main__":
    # Test the utilities
    print("Testing utilities...")
    
    # Test audio data generation
    audio_data, sample_rate = create_test_audio_data()
    print(f"Generated test audio: {len(audio_data)} samples at {sample_rate}Hz")
    
    # Test subtitle file creation
    test_file = create_test_subtitle_file("json")
    print(f"Created test subtitle file: {test_file}")
    
    # Test transcription results
    results = get_test_transcription_results()
    print(f"Generated {len(results)} test transcription results")
    
    # Cleanup
    cleanup_test_files([test_file])
    print("Test utilities validation completed!")