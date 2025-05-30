# Real-time Whisper Subtitles

Real-time speech recognition subtitle generation system using faster-whisper

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![CUDA](https://img.shields.io/badge/CUDA-12.2-orange.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## Overview

This project is a real-time speech recognition system using [faster-whisper](https://github.com/SYSTRAN/faster-whisper). It transcribes audio input from microphones in real-time and displays subtitles through a web interface. Future plans include adding TTS (Text-to-Speech) functionality for AI voice output.

## Features

- ? **Real-time Speech Recognition**: High-speed, high-accuracy speech recognition with faster-whisper
- ?? **Web Interface**: Modern and user-friendly Web UI
- ? **Multi-format Export**: SRT, WebVTT, JSON, plain text support
- ? **Multi-language Support**: Supports Japanese, English, Chinese, and many other languages
- ? **Docker Support**: GPU-optimized Docker environment
- ? **GPU Acceleration**: CUDA-enabled high-speed processing
- ? **VAD Function**: Efficient processing with Voice Activity Detection
- ? **Statistics Display**: Real-time statistics and performance monitoring

## System Requirements

### Required
- Python 3.11+
- Docker & Docker Compose
- NVIDIA GPU (Recommended: RTX 3060 or higher)
- NVIDIA Container Toolkit
- 8GB+ RAM

### Recommended
- NVIDIA RTX 4080/5080
- 16GB+ RAM
- SSD Storage

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/nullpox7/realtime-whisper-subtitles.git
cd realtime-whisper-subtitles
```

### 2. Create Required Directories

```bash
mkdir -p outputs models static/css static/js templates
```

### 3. Start with Docker Environment

```bash
# Start with Docker Compose
docker-compose up --build

# Or use Makefile (if available)
make up
```

### 4. Access Web Interface

Open http://localhost:8000 in your browser

## Troubleshooting Docker Issues

### CUDA Version Issues

If you encounter CUDA Docker image not found errors:

```bash
# Option 1: Use CUDA 11.8 (more widely available)
# Edit Dockerfile, change first line to:
# FROM nvidia/cuda:11.8-devel-ubuntu22.04

# Option 2: Use CPU-only version
# Edit Dockerfile, change first line to:
# FROM ubuntu:22.04
# And remove CUDA-specific environment variables
```

### Alternative Docker Images

```dockerfile
# For older GPUs or compatibility issues:
FROM nvidia/cuda:11.8-devel-ubuntu22.04

# For CPU-only systems:
FROM ubuntu:22.04

# For specific CUDA versions:
FROM nvidia/cuda:12.1-devel-ubuntu22.04
```

### Docker Build Issues

```bash
# Clear Docker cache and rebuild
docker system prune -f
docker-compose build --no-cache
docker-compose up
```

## Usage

### Basic Usage

1. **Select Audio Device**: Choose an audio input device from available microphones
2. **Select Model Size**: Choose Whisper model based on speed/accuracy balance
   - Tiny: Fastest (39MB)
   - Base: Balanced (74MB) - Recommended
   - Small: High Quality (244MB)
   - Medium: Highest Quality (769MB)
   - Large: Best Quality (1550MB)
3. **Select Language**: Auto-detect or choose specific language
4. **Start Recording**: Click "Start Recording" button to begin speech recognition
5. **View Subtitles**: Check real-time generated subtitles in the web interface
6. **Export**: Download subtitles in various formats as needed

### Keyboard Shortcuts

- `Ctrl/Cmd + R`: Start recording
- `Ctrl/Cmd + S`: Stop recording
- `Ctrl/Cmd + E`: Clear subtitles

### Command Line Usage

```python
from src import RealtimeTranscriber, SubtitleManager

# Initialize speech recognition
transcriber = RealtimeTranscriber(model_size="base", language="ja")
subtitle_manager = SubtitleManager()

# Set callback
def on_transcription(result):
    segment = subtitle_manager.add_transcription(result)
    print(f"[{segment.start_time:.2f}s] {segment.text}")

transcriber.set_transcription_callback(on_transcription)

# Start recording
transcriber.start()

# Export subtitles
subtitle_manager.export_srt("output.srt")
subtitle_manager.export_json("output.json")
```

## API Reference

### WebSocket API

WebSocket connection for real-time communication:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// Message types
// - transcription: New subtitle segment
// - status: System status update
// - clear: Clear subtitles
```

### REST API

- `GET /api/devices` - List available audio devices
- `POST /api/start` - Start speech recognition
- `POST /api/stop` - Stop speech recognition
- `GET /api/status` - Get current status
- `GET /api/subtitles` - Get subtitle data
- `POST /api/export/{format}` - Export subtitles
- `DELETE /api/clear` - Clear subtitle data

## Configuration and Customization

### Docker Environment Configuration

Customize ports and volumes in `docker-compose.yml`:

```yaml
ports:
  - "8000:8000"  # Web interface
  - "8888:8888"  # Development

volumes:
  - ./outputs:/app/outputs
  - ./models:/app/models
```

### Whisper Model Configuration

Characteristics of different model sizes:

| Model | Size | Speed | Accuracy | Recommended Use |
|-------|------|-------|----------|-----------------|
| tiny | 39MB | Fastest | Low | Prototyping |
| base | 74MB | Fast | Good | General use |
| small | 244MB | Medium | High | High quality needed |
| medium | 769MB | Slow | Highest | Maximum quality |
| large | 1550MB | Slowest | Highest | Production |

## Development and Contribution

### Development Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start development server
python src/web_interface.py
```

### Project Structure

```
realtime-whisper-subtitles/
??? src/
?   ??? __init__.py
?   ??? realtime_transcriber.py    # Speech recognition engine
?   ??? subtitle_manager.py        # Subtitle management
?   ??? web_interface.py          # Web interface
?   ??? tts_integration.py        # TTS integration (future)
??? templates/
?   ??? index.html                # HTML template
??? static/
?   ??? css/style.css            # Stylesheet
?   ??? js/app.js                # JavaScript
??? outputs/                      # Output files
??? models/                       # Model cache
??? docker-compose.yml
??? Dockerfile
??? requirements.txt
??? README.md
```

### Testing

```bash
# Run system tests
python test_system.py

# Run unit tests
pytest tests/

# Code formatting
black src/
flake8 src/
```

## Future Features

### TTS (Text-to-Speech) Integration

Plans to implement subtitle reading with AI voice:

- ?? **Multi-language TTS**: Japanese, English, and other native voices
- ? **Voice Selection**: Choose from multiple voice characters
- ?? **Parameter Adjustment**: Speed, pitch, volume adjustment
- ? **Real-time Playback**: Audio output simultaneous with subtitle generation

## Troubleshooting

### Common Issues

1. **CUDA Docker image not found**
   - Use alternative CUDA versions (11.8, 12.1)
   - Or use CPU-only version for testing
   - Check NVIDIA Container Toolkit installation

2. **Audio device not recognized**
   - Check if audio device is mounted to Docker container
   - Verify `devices` configuration in `docker-compose.yml`

3. **GPU recognition error**
   - Check NVIDIA Container Toolkit installation
   - Verify GPU recognition with `nvidia-smi`

4. **Low speech recognition accuracy**
   - Try larger models (small, medium, large)
   - Improve audio input quality (noise reduction, microphone positioning)

5. **Memory shortage error**
   - Use smaller models (tiny, base)
   - Adjust Docker Compose memory limits

### Check Logs

```bash
# Check Docker logs
docker-compose logs -f

# Check specific service logs
docker-compose logs whisper-subtitles
```

### Performance Tips

```bash
# For RTX 4080/5080: Use medium or large models
# For RTX 3060/3070: Use base or small models  
# For CPU only: Use tiny or base models
```

## License

This project is released under the MIT License. See [LICENSE](LICENSE) file for details.

## Credits

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Fast Whisper implementation
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Docker](https://www.docker.com/) - Containerization platform

## Support

For issues or questions, please report them on [GitHub Issues](https://github.com/nullpox7/realtime-whisper-subtitles/issues).

---

**Real-time Whisper Subtitles** - Powered by faster-whisper & NVIDIA GPU