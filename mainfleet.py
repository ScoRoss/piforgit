import subprocess
import sys
import time
import os

# CONFIGURATION
# 1. Matches your Rocky VM Tailscale IP
SERVER_IP = "100.89.114.117" 
DRIVER_ID = "pi_unit_01"  # Changed for clarity
DEVICE_ID = "raspberry_pi"

# 2. SRT URL with Latency tweak
# Latency is in microseconds (200000 = 200ms)
SRT_URL = f"srt://{SERVER_IP}:8890?streamid=publish:{DRIVER_ID}&latency=200000"

print(f"--- STARTING PI ARDUCAM STREAM ---")
print(f"Streaming to: {SRT_URL}")

# RASPBERRY PI COMMAND
cmd = [
    "ffmpeg",
    "-f", "v4l2",             # Linux video driver
    "-input_format", "mjpeg", # Arducam USBs usually output MJPEG
    "-video_size", "1280x720",# Standard HD
    "-framerate", "30",       # Smooth movement
    "-i", "/dev/video0",      # The first camera device on Pi
    "-c:v", "h264_v4l2m2m",   # PI HARDWARE ACCELERATION
    "-b:v", "2M",             # Bitrate (2Mbps is good for 5G)
    "-pix_fmt", "yuv420p",    # Required for compatibility
    "-f", "mpegts",
    SRT_URL
]

# Start the process
process = subprocess.Popen(cmd)

try:
    while True:
        # Check if process is still running
        if process.poll() is not None:
            print("FFmpeg process died. Restarting in 5 seconds...")
            time.sleep(5)
            process = subprocess.Popen(cmd)
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping stream...")
    process.terminate()
    sys.exit(0)