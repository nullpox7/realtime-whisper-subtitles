# Real-time Whisper Subtitles Docker Environment
# CUDA 12.2 + faster-whisper optimized
FROM nvidia/cuda:12.2-devel-ubuntu22.04

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install system packages including audio support
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    python3.11-venv \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    vim \
    htop \
    # Audio libraries
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    pulseaudio \
    alsa-utils \
    # System libraries
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/src /app/static /app/outputs /app/models

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 8888

# Default command
CMD ["python", "src/web_interface.py"]