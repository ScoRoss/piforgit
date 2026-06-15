# 1. Use the official Python image for Raspberry Pi (ARM64)
FROM python:3.11-slim-bookworm
# 2. Install standard FFmpeg and v4l utilities
RUN apt-get update && apt-get install -y ffmpeg v4l-utils procps && rm -rf /var/lib/apt/lists/*
# 3. Install Python dependencies
RUN pip install --no-cache-dir requests
# 4. Set the working directory
WORKDIR /app
# 5. Copy your script into the container
COPY mainfleet.py .
# 6. Run the script
CMD ["python3", "mainfleet.py"]
