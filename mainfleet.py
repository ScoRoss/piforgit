import subprocess
import sys
import time

# CONFIGURATION
SERVER_IP = "100.89.114.117" 
DRIVER_ID = "pi_unit_01"

# SRT SETTINGS: 
# latency=30000000 (30 seconds in microseconds)
# conntimeout=5000000 (5 seconds to wait for a handshake)
SRT_URL = f"srt://{SERVER_IP}:8890?streamid=publish:{DRIVER_ID}&latency=30000000&mode=caller&conntimeout=5000000"

# PI 5 OPTIMIZED COMMAND
cmd = [
    "ffmpeg",
    "-f", "v4l2",
    "-input_format", "mjpeg",   
    "-video_size", "1280x720",  
    "-framerate", "30",
    "-i", "/dev/video0",        
    "-c:v", "libx264",          
    "-preset", "ultrafast",     
    "-tune", "zerolatency",
    "-b:v", "2M",               
    "-maxrate", "2M",           # Keep bitrate tight for 5G
    "-bufsize", "4M",           # Internal ffmpeg buffer
    "-pix_fmt", "yuv420p",
    "-g", "60",                 # Keyframe every 2 seconds for better recovery
    "-f", "mpegts",
    SRT_URL
]

print(f"--- STARTING PI 5 USB STREAM WITH 30s BUFFER ---")
print(f"Target Server: {SERVER_IP}")

# Start the process
process = subprocess.Popen(cmd)

try:
    while True:
        # Check if the ffmpeg process died
        if process.poll() is not None:
            print("Process died or connection lost. Restarting in 5 seconds...")
            time.sleep(5)
            process = subprocess.Popen(cmd)
        
        # Heartbeat check every second
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping stream...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
