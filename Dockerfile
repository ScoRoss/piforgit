# 1. Use the official Python image for Raspberry Pi (ARM64)
FROM python:3.11-slim-bookworm

# Install dependencies
RUN apt-get update && apt-get install -y \
    v4l-utils \
    procps \
    wget \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install ffmpeg 7.x static build (matches what works on the host)
RUN wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz \
    && tar xf ffmpeg-release-arm64-static.tar.xz \
    && mv ffmpeg-*-arm64-static/ffmpeg /usr/local/bin/ffmpeg \
    && mv ffmpeg-*-arm64-static/ffprobe /usr/local/bin/ffprobe \
    && rm -rf ffmpeg-*

RUN pip install --no-cache-dir requests

WORKDIR /app
COPY mainfleet.py .
CMD ["python3", "mainfleet.py"]
