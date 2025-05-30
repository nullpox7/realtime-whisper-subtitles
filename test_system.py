#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Real-time Whisper Subtitles
Testing script for the real-time speech recognition system
"""

import sys
import time
import logging
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.realtime_transcriber import RealtimeTranscriber, TranscriptionResult
from src.subtitle_manager import SubtitleManager
from src.web_interface import RealtimeSubtitleApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_transcriber():
    """Test the real-time transcriber"""
    print("=== Testing Real-time Transcriber ===")
    
    def on_transcription(result: TranscriptionResult):
        print(f"[{result.start_time:.2f}-{result.end_time:.2f}] {result.text}")
        print(f"  Language: {result.language}, Confidence: {result.confidence:.2f}")
    
    try:
        # Initialize transcriber
        transcriber = RealtimeTranscriber(model_size="tiny")  # Use tiny for faster testing
        transcriber.set_transcription_callback(on_transcription)
        
        # Get available devices
        devices = transcriber.get_available_devices()
        print(f"Available audio devices: {len(devices)}")
        for device in devices[:3]:  # Show first 3 devices
            print(f"  {device['index']}: {device['name']}")
        
        if not devices:
            print("No audio devices found. Testing skipped.")
            return
        
        print("\nStarting transcription test (10 seconds)...")
        print("Please speak into your microphone...")
        
        # Start transcription
        transcriber.start()
        
        # Wait for 10 seconds
        time.sleep(10)
        
        # Stop transcription
        transcriber.stop()
        print("Transcription test completed!")
        
    except Exception as e:
        print(f"Transcriber test failed: {e}")

def test_subtitle_manager():
    """Test the subtitle manager"""
    print("\n=== Testing Subtitle Manager ===")
    
    try:
        # Create manager
        manager = SubtitleManager(output_dir="test_outputs")
        
        # Add sample transcription results
        sample_results = [
            TranscriptionResult("Hello, this is a test.", 0.0, 2.5, 0.95, "en"),
            TranscriptionResult("Testing speech recognition system.", 2.5, 5.0, 0.92, "en"),
            TranscriptionResult("Using faster-whisper for real-time processing.", 5.0, 8.8, 0.88, "en"),
        ]
        
        for result in sample_results:
            segment = manager.add_transcription(result)
            print(f"Added segment: {segment.text[:50]}...")
        
        # Test exports
        print("\nTesting exports...")
        
        try:
            json_file = manager.export_json("test_subtitles.json")
            print(f"JSON exported: {json_file}")
        except Exception as e:
            print(f"JSON export failed: {e}")
        
        try:
            txt_file = manager.export_txt("test_subtitles.txt")
            print(f"TXT exported: {txt_file}")
        except Exception as e:
            print(f"TXT export failed: {e}")
        
        try:
            srt_file = manager.export_srt("test_subtitles.srt")
            print(f"SRT exported: {srt_file}")
        except Exception as e:
            print(f"SRT export failed: {e}")
        
        # Show statistics
        stats = manager.get_statistics()
        print(f"\nStatistics:")
        print(f"  Total segments: {stats['total_segments']}")
        print(f"  Total duration: {stats['total_duration']:.2f}s")
        print(f"  Average confidence: {stats['average_confidence']:.2f}")
        
        print("Subtitle manager test completed!")
        
    except Exception as e:
        print(f"Subtitle manager test failed: {e}")

def test_web_interface():
    """Test the web interface (basic initialization)"""
    print("\n=== Testing Web Interface ===")
    
    try:
        # Initialize web app
        app_instance = RealtimeSubtitleApp()
        print("Web interface initialized successfully!")
        
        # Test static files setup
        if app_instance.static_dir.exists():
            print(f"Static directory exists: {app_instance.static_dir}")
        
        if app_instance.templates_dir.exists():
            print(f"Templates directory exists: {app_instance.templates_dir}")
        
        if app_instance.outputs_dir.exists():
            print(f"Outputs directory exists: {app_instance.outputs_dir}")
        
        print("Web interface test completed!")
        
    except Exception as e:
        print(f"Web interface test failed: {e}")

async def test_tts_integration():
    """Test TTS integration (if available)"""
    print("\n=== Testing TTS Integration ===")
    
    try:
        from src.tts_integration import TTSEngine, TTSConfig, create_english_tts_config
        
        # Create TTS config
        config = create_english_tts_config()
        print(f"TTS config created: {config.model_name}")
        
        # Initialize TTS engine
        tts_engine = TTSEngine(config)
        print("TTS engine initialized!")
        
        # Note: Not loading model in test to avoid downloading large files
        print("TTS integration test completed (model not loaded)!")
        
    except ImportError as e:
        print(f"TTS libraries not available: {e}")
    except Exception as e:
        print(f"TTS integration test failed: {e}")

def test_gpu_availability():
    """Test GPU availability"""
    print("\n=== Testing GPU Availability ===")
    
    try:
        import torch
        
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU count: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                print(f"  GPU {i}: {gpu_name}")
                
                # Get GPU capability
                capability = torch.cuda.get_device_capability(i)
                print(f"    Compute capability: {capability[0]}.{capability[1]}")
        else:
            print("CUDA not available - will use CPU")
        
        print("GPU availability test completed!")
        
    except Exception as e:
        print(f"GPU availability test failed: {e}")

def main():
    """Run all tests"""
    print("Real-time Whisper Subtitles - Test Script")
    print("=" * 50)
    
    # Test GPU availability first
    test_gpu_availability()
    
    # Test subtitle manager (doesn't require audio)
    test_subtitle_manager()
    
    # Test web interface initialization
    test_web_interface()
    
    # Test TTS integration
    asyncio.run(test_tts_integration())
    
    # Test transcriber (requires audio input)
    response = input("\nDo you want to test the real-time transcriber? (requires microphone) [y/N]: ")
    if response.lower() in ['y', 'yes']:
        test_transcriber()
    else:
        print("Skipping transcriber test.")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("\nTo start the web interface:")
    print("  docker-compose up")
    print("  # or")
    print("  make up")
    print("  # then open http://localhost:8000")

if __name__ == "__main__":
    main()