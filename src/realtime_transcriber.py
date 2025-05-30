#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time Audio Transcription with faster-whisper
"""

import asyncio
import logging
import time
import threading
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
from queue import Queue, Empty
import numpy as np

# Audio processing
import pyaudio
import soundfile as sf
from scipy import signal

# Whisper and AI
from faster_whisper import WhisperModel
import torch

# VAD (Voice Activity Detection)
try:
    import webrtcvad
    HAS_WEBRTC_VAD = True
except ImportError:
    HAS_WEBRTC_VAD = False
    logging.warning("webrtcvad not available, using energy-based VAD")

@dataclass
class TranscriptionResult:
    """Speech recognition result data class"""
    text: str
    start_time: float
    end_time: float
    confidence: float
    language: str
    is_final: bool = True

class AudioProcessor:
    """Audio processing and VAD (Voice Activity Detection) class"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 chunk_size: int = 1024,
                 vad_mode: int = 3):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.vad_mode = vad_mode
        
        # VAD setup
        self.vad = None
        if HAS_WEBRTC_VAD:
            self.vad = webrtcvad.Vad(vad_mode)
        
        # Audio buffer
        self.audio_buffer = Queue()
        self.is_recording = False
        
        # PyAudio setup
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        
        logging.info(f"AudioProcessor initialized: {sample_rate}Hz, chunk_size={chunk_size}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback function"""
        if status:
            logging.warning(f"Audio callback status: {status}")
        
        # Add audio data to buffer
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        self.audio_buffer.put(audio_data)
        
        return (None, pyaudio.paContinue)
    
    def start_recording(self, device_index: Optional[int] = None):
        """Start audio recording"""
        try:
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            self.is_recording = True
            logging.info("Audio recording started")
            
        except Exception as e:
            logging.error(f"Failed to start audio recording: {e}")
            raise
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        logging.info("Audio recording stopped")
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get audio chunk"""
        try:
            return self.audio_buffer.get(timeout=timeout)
        except Empty:
            return None
    
    def is_speech(self, audio_data: np.ndarray) -> bool:
        """Voice activity detection"""
        if self.vad and len(audio_data) >= 320:  # WebRTC VAD requires at least 320 samples
            # Convert to bytes for WebRTC VAD
            audio_bytes = audio_data.astype(np.int16).tobytes()
            try:
                return self.vad.is_speech(audio_bytes, self.sample_rate)
            except Exception as e:
                logging.warning(f"WebRTC VAD error: {e}, falling back to energy-based VAD")
        
        # Energy-based VAD fallback
        energy = np.sum(audio_data.astype(np.float32) ** 2) / len(audio_data)
        threshold = 1000  # Adjust based on your environment
        return energy > threshold
    
    def __del__(self):
        """Cleanup"""
        self.stop_recording()
        if hasattr(self, 'pyaudio'):
            self.pyaudio.terminate()

class RealtimeTranscriber:
    """Real-time speech recognition main class"""
    
    def __init__(self,
                 model_size: str = "base",
                 device: str = "auto",
                 compute_type: str = "auto",
                 language: Optional[str] = None,
                 sample_rate: int = 16000,
                 buffer_duration: float = 5.0):
        
        self.model_size = model_size
        self.device = self._detect_device() if device == "auto" else device
        self.compute_type = self._detect_compute_type() if compute_type == "auto" else compute_type
        self.language = language
        self.sample_rate = sample_rate
        self.buffer_duration = buffer_duration
        self.buffer_size = int(sample_rate * buffer_duration)
        
        # Initialize components
        self.audio_processor = AudioProcessor(sample_rate=sample_rate)
        self.model = None
        self.audio_buffer = np.array([], dtype=np.float32)
        
        # Transcription callback
        self.transcription_callback: Optional[Callable[[TranscriptionResult], None]] = None
        
        # Control flags
        self.is_running = False
        self.transcription_thread = None
        
        logging.info(f"RealtimeTranscriber initialized: model={model_size}, device={self.device}, compute_type={self.compute_type}")
    
    def _detect_device(self) -> str:
        """Detect available device"""
        if torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def _detect_compute_type(self) -> str:
        """Detect optimal compute type"""
        if self.device == "cuda":
            # Decide based on CUDA compute capability
            try:
                capability = torch.cuda.get_device_capability()
                if capability[0] >= 8:  # RTX 30xx series and newer
                    return "float16"
                else:
                    return "int8"
            except:
                return "float16"
        else:
            return "int8"
    
    def load_model(self):
        """Load Whisper model"""
        try:
            logging.info(f"Loading Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            logging.info("Whisper model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load Whisper model: {e}")
            raise
    
    def set_transcription_callback(self, callback: Callable[[TranscriptionResult], None]):
        """Set callback function for transcription results"""
        self.transcription_callback = callback
    
    def _transcription_worker(self):
        """Transcription worker thread"""
        logging.info("Transcription worker started")
        
        while self.is_running:
            try:
                # Get audio data
                audio_chunk = self.audio_processor.get_audio_chunk(timeout=0.1)
                
                if audio_chunk is None:
                    continue
                
                # Add to audio buffer
                audio_float = audio_chunk.astype(np.float32) / 32768.0
                self.audio_buffer = np.concatenate([self.audio_buffer, audio_float])
                
                # Limit buffer size
                if len(self.audio_buffer) > self.buffer_size:
                    self.audio_buffer = self.audio_buffer[-self.buffer_size:]
                
                # Voice activity detection
                if not self.audio_processor.is_speech(audio_chunk):
                    continue
                
                # Check if we have enough audio data
                if len(self.audio_buffer) < self.sample_rate * 1.0:  # At least 1 second
                    continue
                
                # Perform speech recognition
                start_time = time.time()
                segments, info = self.model.transcribe(
                    self.audio_buffer,
                    language=self.language,
                    task="transcribe",
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                # Process results
                for segment in segments:
                    if segment.text.strip():
                        result = TranscriptionResult(
                            text=segment.text.strip(),
                            start_time=segment.start,
                            end_time=segment.end,
                            confidence=getattr(segment, 'avg_logprob', 0.0),
                            language=info.language,
                            is_final=True
                        )
                        
                        if self.transcription_callback:
                            self.transcription_callback(result)
                
                # Clear old buffer to prevent memory buildup
                self.audio_buffer = self.audio_buffer[-int(self.sample_rate * 2.0):]
                
            except Exception as e:
                logging.error(f"Transcription error: {e}")
                time.sleep(0.1)
        
        logging.info("Transcription worker stopped")
    
    def start(self, device_index: Optional[int] = None):
        """Start real-time speech recognition"""
        if self.is_running:
            logging.warning("Transcriber is already running")
            return
        
        if self.model is None:
            self.load_model()
        
        try:
            # Start audio recording
            self.audio_processor.start_recording(device_index=device_index)
            
            # Start recognition thread
            self.is_running = True
            self.transcription_thread = threading.Thread(target=self._transcription_worker)
            self.transcription_thread.start()
            
            logging.info("Real-time transcription started")
            
        except Exception as e:
            logging.error(f"Failed to start transcription: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop real-time speech recognition"""
        self.is_running = False
        
        # Stop audio recording
        self.audio_processor.stop_recording()
        
        # Wait for recognition thread to finish
        if self.transcription_thread and self.transcription_thread.is_alive():
            self.transcription_thread.join(timeout=5.0)
        
        logging.info("Real-time transcription stopped")
    
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get list of available audio devices"""
        devices = []
        
        for i in range(self.audio_processor.pyaudio.get_device_count()):
            info = self.audio_processor.pyaudio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:  # Input device
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': int(info['defaultSampleRate'])
                })
        
        return devices

if __name__ == "__main__":
    # Simple test execution
    logging.basicConfig(level=logging.INFO)
    
    def on_transcription(result: TranscriptionResult):
        print(f"[{result.start_time:.2f}-{result.end_time:.2f}] {result.text} (confidence: {result.confidence:.2f})")
    
    transcriber = RealtimeTranscriber(model_size="base")
    transcriber.set_transcription_callback(on_transcription)
    
    try:
        transcriber.start()
        print("Recording... Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        transcriber.stop()
        print("Stopped.")