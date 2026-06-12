# 1. Start with the slim bookworm base image
FROM python:3.11-slim-bookworm

# 2. Add the official Raspberry Pi repository keys and sources so apt can find libcamera-apps
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://archive.raspberrypi.org/debian/raspberrypi.gpg.key | gpg --dearmor -o /etc/apt/trusted.gpg.d/raspberrypi.gpg && \
    echo "deb http://archive.raspberrypi.org/debian/ bookworm main" > /etc/apt/sources.list.d/raspi.list

# 3. Install FFmpeg, the real Pi camera tools, and clean up apt cache to keep the image small
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libcamera-apps \
    && rm -rf /var/lib/apt/lists/*

# 4. Set the working directory
WORKDIR /app

# 5. Copy your script into the container
COPY mainfleet.py .

# 6. Run the script
CMD ["python3", "mainfleet.py"]
