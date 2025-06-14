#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle Management and Export
Subtitle management and file export functionality
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path

# Subtitle format libraries
try:
    import srt
    HAS_SRT = True
except ImportError:
    HAS_SRT = False
    logging.warning("srt library not available")

try:
    import webvtt
    HAS_WEBVTT = True
except ImportError:
    HAS_WEBVTT = False
    logging.warning("webvtt library not available")

from .realtime_transcriber import TranscriptionResult

@dataclass
class SubtitleSegment:
    """Subtitle segment data class"""
    index: int
    start_time: float
    end_time: float
    text: str
    confidence: float
    language: str
    created_at: datetime
    
    def duration(self) -> float:
        """Get segment duration in seconds"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubtitleSegment':
        """Restore from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

class SubtitleManager:
    """Subtitle management class"""
    
    def __init__(self, 
                 output_dir: str = "outputs",
                 auto_save_interval: float = 30.0,
                 max_segments: int = 1000):
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.auto_save_interval = auto_save_interval
        self.max_segments = max_segments
        
        # Subtitle segment management
        self.segments: List[SubtitleSegment] = []
        self.segment_counter = 0
        
        # Session management
        self.session_start_time = datetime.now()
        self.session_id = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        
        # Auto-save timer
        self.last_save_time = time.time()
        
        logging.info(f"SubtitleManager initialized: session_id={self.session_id}")
    
    def add_transcription(self, result: TranscriptionResult) -> SubtitleSegment:
        """Add transcription result as subtitle segment"""
        self.segment_counter += 1
        
        segment = SubtitleSegment(
            index=self.segment_counter,
            start_time=result.start_time,
            end_time=result.end_time,
            text=result.text,
            confidence=result.confidence,
            language=result.language,
            created_at=datetime.now()
        )
        
        self.segments.append(segment)
        
        # Remove old segments if exceeding max
        if len(self.segments) > self.max_segments:
            self.segments = self.segments[-self.max_segments:]
        
        # Check for auto-save
        current_time = time.time()
        if current_time - self.last_save_time >= self.auto_save_interval:
            self.auto_save()
            self.last_save_time = current_time
        
        logging.debug(f"Added subtitle segment: {segment.text[:50]}...")
        return segment
    
    def get_recent_segments(self, count: int = 10) -> List[SubtitleSegment]:
        """Get recent segments"""
        return self.segments[-count:] if self.segments else []
    
    def get_segments_by_time_range(self, 
                                  start_time: float, 
                                  end_time: float) -> List[SubtitleSegment]:
        """Get segments by time range"""
        return [
            segment for segment in self.segments
            if (segment.start_time >= start_time and segment.end_time <= end_time) or
               (segment.start_time <= start_time and segment.end_time >= start_time) or
               (segment.start_time <= end_time and segment.end_time >= end_time)
        ]
    
    def search_segments(self, query: str) -> List[SubtitleSegment]:
        """Search segments by text"""
        query_lower = query.lower()
        return [
            segment for segment in self.segments
            if query_lower in segment.text.lower()
        ]
    
    def export_srt(self, filename: Optional[str] = None) -> str:
        """Export in SRT format"""
        if not HAS_SRT:
            raise ImportError("srt library is required for SRT export")
        
        if filename is None:
            filename = f"subtitles_{self.session_id}.srt"
        
        filepath = self.output_dir / filename
        
        # Generate SRT subtitles
        srt_subtitles = []
        for segment in self.segments:
            subtitle = srt.Subtitle(
                index=segment.index,
                start=timedelta(seconds=segment.start_time),
                end=timedelta(seconds=segment.end_time),
                content=segment.text
            )
            srt_subtitles.append(subtitle)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(srt.compose(srt_subtitles))
        
        logging.info(f"SRT exported: {filepath}")
        return str(filepath)
    
    def export_webvtt(self, filename: Optional[str] = None) -> str:
        """Export in WebVTT format"""
        if not HAS_WEBVTT:
            raise ImportError("webvtt library is required for WebVTT export")
        
        if filename is None:
            filename = f"subtitles_{self.session_id}.vtt"
        
        filepath = self.output_dir / filename
        
        # Generate WebVTT subtitles
        vtt = webvtt.WebVTT()
        
        for segment in self.segments:
            start_time = self._seconds_to_webvtt_time(segment.start_time)
            end_time = self._seconds_to_webvtt_time(segment.end_time)
            
            caption = webvtt.Caption(
                start_time,
                end_time,
                segment.text
            )
            vtt.captions.append(caption)
        
        # Write to file
        vtt.save(str(filepath))
        
        logging.info(f"WebVTT exported: {filepath}")
        return str(filepath)
    
    def export_json(self, filename: Optional[str] = None) -> str:
        """Export in JSON format (with detailed info)"""
        if filename is None:
            filename = f"subtitles_{self.session_id}.json"
        
        filepath = self.output_dir / filename
        
        # JSON data structure
        data = {
            'session_id': self.session_id,
            'session_start_time': self.session_start_time.isoformat(),
            'export_time': datetime.now().isoformat(),
            'total_segments': len(self.segments),
            'segments': [segment.to_dict() for segment in self.segments]
        }
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"JSON exported: {filepath}")
        return str(filepath)
    
    def export_txt(self, filename: Optional[str] = None) -> str:
        """Export in plain text format"""
        if filename is None:
            filename = f"subtitles_{self.session_id}.txt"
        
        filepath = self.output_dir / filename
        
        # Write text
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Subtitles Session: {self.session_id}\n")
            f.write(f"# Created: {self.session_start_time}\n\n")
            
            for segment in self.segments:
                f.write(f"[{self._seconds_to_timestamp(segment.start_time)} - ")
                f.write(f"{self._seconds_to_timestamp(segment.end_time)}] ")
                f.write(f"{segment.text}\n")
        
        logging.info(f"TXT exported: {filepath}")
        return str(filepath)
    
    def load_from_json(self, filepath: str) -> int:
        """Load subtitle data from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Restore segments
        loaded_segments = [
            SubtitleSegment.from_dict(segment_data)
            for segment_data in data['segments']
        ]
        
        self.segments.extend(loaded_segments)
        
        # Update counter
        if loaded_segments:
            max_index = max(segment.index for segment in loaded_segments)
            self.segment_counter = max(self.segment_counter, max_index)
        
        logging.info(f"Loaded {len(loaded_segments)} segments from {filepath}")
        return len(loaded_segments)
    
    def auto_save(self):
        """Auto-save (JSON format)"""
        try:
            auto_save_file = f"autosave_{self.session_id}.json"
            self.export_json(auto_save_file)
            logging.debug(f"Auto-saved: {auto_save_file}")
        except Exception as e:
            logging.error(f"Auto-save failed: {e}")
    
    def clear_segments(self):
        """Clear all segments"""
        self.segments.clear()
        self.segment_counter = 0
        logging.info("All segments cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics information"""
        if not self.segments:
            return {
                'total_segments': 0,
                'total_duration': 0.0,
                'average_confidence': 0.0,
                'languages': {},
                'session_duration': 0.0
            }
        
        total_duration = sum(segment.duration() for segment in self.segments)
        average_confidence = sum(segment.confidence for segment in self.segments) / len(self.segments)
        
        # Language statistics
        languages = {}
        for segment in self.segments:
            lang = segment.language
            if lang not in languages:
                languages[lang] = {'count': 0, 'duration': 0.0}
            languages[lang]['count'] += 1
            languages[lang]['duration'] += segment.duration()
        
        # Session duration
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        return {
            'total_segments': len(self.segments),
            'total_duration': total_duration,
            'average_confidence': average_confidence,
            'languages': languages,
            'session_duration': session_duration,
            'session_start': self.session_start_time.isoformat(),
            'segment_rate': len(self.segments) / session_duration if session_duration > 0 else 0
        }
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to timestamp string"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def _seconds_to_webvtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

if __name__ == "__main__":
    # Simple test execution
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample data
    manager = SubtitleManager()
    
    # Add sample transcription results
    from .realtime_transcriber import TranscriptionResult
    
    results = [
        TranscriptionResult("Hello, this is a test.", 0.0, 2.5, 0.95, "en"),
        TranscriptionResult("Testing speech recognition.", 2.5, 5.0, 0.92, "en"),
        TranscriptionResult("Using faster-whisper.", 5.0, 7.8, 0.88, "en"),
    ]
    
    for result in results:
        manager.add_transcription(result)
    
    # Export test
    print("Exporting subtitles...")
    print(f"JSON: {manager.export_json()}")
    print(f"TXT: {manager.export_txt()}")
    
    if HAS_SRT:
        print(f"SRT: {manager.export_srt()}")
    
    if HAS_WEBVTT:
        print(f"WebVTT: {manager.export_webvtt()}")
    
    # Statistics
    stats = manager.get_statistics()
    print(f"Statistics: {stats}")