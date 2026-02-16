import subprocess
import sys
import time

# CONFIGURATION
SERVER_IP = "100.89.114.117" 
DRIVER_ID = "pi_unit_01"
SRT_URL = f"srt://{SERVER_IP}:8890?streamid=publish:{DRIVER_ID}&latency=200000"

# PI 5 OPTIMIZED COMMAND (Uses Software Encoding because Pi 5 is a beast)
cmd = [
    "ffmpeg",
    "-f", "v4l2",
    "-input_format", "mjpeg",   # Your Vitade AF sends MJPEG
    "-video_size", "1280x720",  # 720p is safer for 5G stability
    "-framerate", "30",
    "-i", "/dev/video0",        # Path from step 1
    "-c:v", "libx264",          # Software encoding for Pi 5
    "-preset", "ultrafast",     # Low CPU usage
    "-tune", "zerolatency",
    "-b:v", "2M",               # 2Mbps bitrate
    "-pix_fmt", "yuv420p",
    "-f", "mpegts",
    SRT_URL
]

print(f"--- STARTING PI 5 USB STREAM ---")
process = subprocess.Popen(cmd)

try:
    while True:
        if process.poll() is not None:
            print("Restarting...")
            time.sleep(2)
            process = subprocess.Popen(cmd)
        time.sleep(1)
except KeyboardInterrupt:
    process.terminate()
