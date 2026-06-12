# 1. Use the official Python image for Raspberry Pi (ARM64)
FROM python:3.11-slim-bookworm

# 2. Install FFmpeg and hardware libraries
# v4l-utils is added to help with camera detection
RUN apt-get update && apt-get install -y ffmpeg libcamera-apps python3-requests

# 3. Install Python dependencies
# We install 'requests' here so the heartbeat logic works
RUN pip install --no-cache-dir requests

# 4. Set the working directory
WORKDIR /app

# 5. Copy your script into the container
COPY mainfleet.py .

# 6. Run the script
CMD ["python3", "mainfleet.py"]
