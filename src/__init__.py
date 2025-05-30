# -*- coding: utf-8 -*-
"""
Real-time Whisper Subtitles Package
????????????????
"""

__version__ = "1.0.0"
__author__ = "nullpox7"
__email__ = "n.tsuboi@kumo-ichimonji.net"
__description__ = "Real-time speech recognition with faster-whisper for subtitle generation"

from .realtime_transcriber import RealtimeTranscriber, TranscriptionResult
from .subtitle_manager import SubtitleManager, SubtitleSegment
from .web_interface import RealtimeSubtitleApp, create_app

__all__ = [
    "RealtimeTranscriber",
    "TranscriptionResult", 
    "SubtitleManager",
    "SubtitleSegment",
    "RealtimeSubtitleApp",
    "create_app"
]