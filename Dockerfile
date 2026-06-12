# 1. Use the official Raspberry Pi foundation base image
FROM bscheng/raspberrypi-os:bookworm-slim

# 2. Update and install Python, FFmpeg, and the pre-compiled camera utilities
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-requests \
    ffmpeg \
    libcamera-apps \
    && rm -rf /var/lib/apt/lists/*

# 3. Double-check Python dependencies match
RUN pip3 install --no-cache-dir --break-system-packages requests

# 4. Set the working directory
WORKDIR /app

# 5. Copy your main execution script into the container
COPY mainfleet.py .

# 6. Run the fleet monitor
CMD ["python3", "mainfleet.py"]
