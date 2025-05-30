#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Interface for Real-time Whisper Subtitles
Web interface for real-time speech recognition subtitle system
"""

import asyncio
import logging
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# FastAPI and WebSocket
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import uvicorn

# Project modules
from .realtime_transcriber import RealtimeTranscriber, TranscriptionResult
from .subtitle_manager import SubtitleManager

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class WebSocketManager:
    """WebSocket connection manager class"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Add WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send personal message"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def broadcast(self, message: str):
        """Broadcast to all connections"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

class RealtimeSubtitleApp:
    """Real-time subtitle web application"""
    
    def __init__(self):
        # FastAPI setup
        self.app = FastAPI(
            title="Real-time Whisper Subtitles",
            description="Real-time speech recognition with faster-whisper for subtitle generation",
            version="1.0.0"
        )
        
        # Setup paths
        self.base_dir = Path(__file__).parent.parent
        self.static_dir = self.base_dir / "static"
        self.templates_dir = self.base_dir / "templates"
        self.outputs_dir = self.base_dir / "outputs"
        
        # Create directories
        self.static_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.outputs_dir.mkdir(exist_ok=True)
        
        # Components
        self.transcriber: Optional[RealtimeTranscriber] = None
        self.subtitle_manager: Optional[SubtitleManager] = None
        self.websocket_manager = WebSocketManager()
        
        # State
        self.is_recording = False
        self.current_device_index: Optional[int] = None
        
        # Setup routes and static files
        self._setup_routes()
        self._setup_static_files()
        
        logger.info("RealtimeSubtitleApp initialized")
    
    def _setup_static_files(self):
        """Setup static files and templates"""
        # Static files
        self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        # Templates
        self.templates = Jinja2Templates(directory=str(self.templates_dir))
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root(request: Request):
            """Main page"""
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint"""
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self._handle_websocket_message(message, websocket)
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.websocket_manager.disconnect(websocket)
        
        @self.app.get("/api/devices")
        async def get_audio_devices():
            """Get available audio devices list"""
            try:
                if not self.transcriber:
                    self.transcriber = RealtimeTranscriber()
                
                devices = self.transcriber.get_available_devices()
                return {"devices": devices}
            except Exception as e:
                logger.error(f"Failed to get audio devices: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/start")
        async def start_transcription(request: Request):
            """Start speech recognition"""
            try:
                data = await request.json()
                model_size = data.get("model_size", "base")
                language = data.get("language")
                device_index = data.get("device_index")
                
                if self.is_recording:
                    return {"error": "Already recording"}
                
                # Initialize components
                self.transcriber = RealtimeTranscriber(
                    model_size=model_size,
                    language=language
                )
                self.subtitle_manager = SubtitleManager(output_dir=str(self.outputs_dir))
                
                # Set callback
                self.transcriber.set_transcription_callback(self._on_transcription)
                
                # Start transcription
                self.transcriber.start(device_index=device_index)
                self.is_recording = True
                self.current_device_index = device_index
                
                # Broadcast status
                await self.websocket_manager.broadcast(json.dumps({
                    "type": "status",
                    "status": "recording",
                    "message": "Recording started"
                }))
                
                return {"status": "started"}
                
            except Exception as e:
                logger.error(f"Failed to start transcription: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/stop")
        async def stop_transcription():
            """Stop speech recognition"""
            try:
                if not self.is_recording:
                    return {"error": "Not recording"}
                
                # Stop transcription
                if self.transcriber:
                    self.transcriber.stop()
                
                self.is_recording = False
                
                # Broadcast status
                await self.websocket_manager.broadcast(json.dumps({
                    "type": "status",
                    "status": "stopped",
                    "message": "Recording stopped"
                }))
                
                return {"status": "stopped"}
                
            except Exception as e:
                logger.error(f"Failed to stop transcription: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            """Get current status"""
            return {
                "is_recording": self.is_recording,
                "device_index": self.current_device_index,
                "statistics": self.subtitle_manager.get_statistics() if self.subtitle_manager else None
            }
        
        @self.app.get("/api/subtitles")
        async def get_subtitles(count: int = 50):
            """Get latest subtitle segments"""
            if not self.subtitle_manager:
                return {"segments": []}
            
            segments = self.subtitle_manager.get_recent_segments(count)
            return {
                "segments": [segment.to_dict() for segment in segments]
            }
        
        @self.app.post("/api/export/{format}")
        async def export_subtitles(format: str):
            """Export subtitles"""
            if not self.subtitle_manager:
                raise HTTPException(status_code=400, detail="No subtitle data available")
            
            try:
                if format == "srt":
                    filepath = self.subtitle_manager.export_srt()
                elif format == "vtt":
                    filepath = self.subtitle_manager.export_webvtt()
                elif format == "json":
                    filepath = self.subtitle_manager.export_json()
                elif format == "txt":
                    filepath = self.subtitle_manager.export_txt()
                else:
                    raise HTTPException(status_code=400, detail="Unsupported format")
                
                return FileResponse(
                    path=filepath,
                    filename=Path(filepath).name,
                    media_type='application/octet-stream'
                )
                
            except Exception as e:
                logger.error(f"Export failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/clear")
        async def clear_subtitles():
            """Clear subtitle data"""
            if self.subtitle_manager:
                self.subtitle_manager.clear_segments()
                
                # Broadcast clear event
                await self.websocket_manager.broadcast(json.dumps({
                    "type": "clear",
                    "message": "Subtitles cleared"
                }))
            
            return {"status": "cleared"}
    
    async def _handle_websocket_message(self, message: Dict[str, Any], websocket: WebSocket):
        """WebSocket message handler"""
        message_type = message.get("type")
        
        if message_type == "ping":
            await self.websocket_manager.send_personal_message(
                json.dumps({"type": "pong"}), 
                websocket
            )
        elif message_type == "get_status":
            status = {
                "type": "status",
                "is_recording": self.is_recording,
                "device_index": self.current_device_index
            }
            await self.websocket_manager.send_personal_message(
                json.dumps(status), 
                websocket
            )
    
    def _on_transcription(self, result: TranscriptionResult):
        """Transcription result callback"""
        try:
            # Add to subtitle manager
            if self.subtitle_manager:
                segment = self.subtitle_manager.add_transcription(result)
                
                # Broadcast to all connected clients
                message = {
                    "type": "transcription",
                    "segment": segment.to_dict()
                }
                
                # Use asyncio to run the coroutine
                asyncio.create_task(self.websocket_manager.broadcast(json.dumps(message)))
                
        except Exception as e:
            logger.error(f"Error handling transcription result: {e}")
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Run web application"""
        logger.info(f"Starting Real-time Whisper Subtitles Web Interface on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="debug" if debug else "info",
            reload=debug
        )

def create_app() -> FastAPI:
    """FastAPI application factory"""
    app_instance = RealtimeSubtitleApp()
    return app_instance.app

if __name__ == "__main__":
    # Development server
    app_instance = RealtimeSubtitleApp()
    app_instance.run(debug=True)