import subprocess
import os
import sys
import time

# CONFIGURATION - These now come from Docker/Environment Variables
# If not set, it defaults to your current test settings
SERVER_IP = os.getenv("SERVER_IP", "100.97.37.123") 
UNIT_ID = os.getenv("UNIT_ID", "UNASSIGNED_PI")

# SRT SETTINGS
# Using the UNIT_ID dynamically in the streamid
SRT_URL = f"srt://{SERVER_IP}:8890?streamid=publish:{UNIT_ID}&latency=30000000&mode=caller&conntimeout=5000000"

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
    "-maxrate", "2M",           
    "-bufsize", "4M",           
    "-pix_fmt", "yuv420p",
    "-g", "30",                 
    "-f", "mpegts",
    SRT_URL
]

print(f"--- STARTING {UNIT_ID} USB STREAM ---")
print(f"Target Server: {SERVER_IP}")

def run_stream():
    try:
        process = subprocess.Popen(cmd)
        while True:
            if process.poll() is not None:
                print(f"Connection to {SERVER_IP} lost. Restarting...")
                return # Exit this loop to trigger restart
            time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    try:
        while True:
            run_stream()
            time.sleep(5) # Wait before restart
    except KeyboardInterrupt:
        print("\nStopping Fleet Unit...")
        sys.exit(0)
