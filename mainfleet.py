import subprocess
import os
import sys
import time
import threading
import requests

# CONFIGURATION
SERVER_IP = os.getenv("SERVER_IP", "100.97.37.123") 
UNIT_ID = os.getenv("UNIT_ID", "UNASSIGNED_PI")

# API URLS
STATUS_URL = os.getenv("STATUS_URL", "https://27carslivestream.co.uk/api/status")
COMMAND_URL = os.getenv("COMMAND_URL", f"https://27carslivestream.co.uk/api/command?unit_id={UNIT_ID}")

# STATE VARIABLES
current_status = "AVAILABLE"  # Boots up idle
assigned_driver = None
stream_process = None

# DYNAMIC STREAM STORAGE
current_stream_url = ""

def comms_loop():
    """Background thread: Sends status AND asks for commands every 5 seconds."""
    global current_status, assigned_driver, current_stream_url
    
    while True:
        # 1. SEND HEARTBEAT (Tell the server our current state)
        try:
            requests.post(STATUS_URL, json={
                "unit_id": UNIT_ID,
                "status": current_status,
                "driver": assigned_driver
            }, timeout=5)
        except Exception:
            pass # Ignore network blips

        # 2. CHECK FOR COMMANDS (Ask the server what we should do)
        try:
            response = requests.get(COMMAND_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                command = data.get("command")
                
                # If backend says "PAIR", trigger the start sequence dynamically
                if command == "PAIR" and current_status != "STREAMING":
                    assigned_driver = data.get("driver", "Unknown")
                    
                    # Pull dynamic routing targets from the API, or fallback to defaults
                    target_ip = data.get("stream_target", SERVER_IP)
                    stream_key = data.get("stream_key", UNIT_ID)
                    
                    # Construct the precise SRT destination path for this specific job session
                    current_stream_url = f"srt://{target_ip}:8890?streamid=publish:{stream_key}&latency=30000000&mode=caller&conntimeout=5000000"
                    
                    current_status = "STARTING"
                
                # If backend says "UNPAIR", trigger the stop sequence
                elif command == "UNPAIR" and current_status != "AVAILABLE":
                    assigned_driver = None
                    current_status = "STOPPING"
        except Exception:
            pass
        
        time.sleep(5) # Wait 5 seconds before asking again

def build_ffmpeg_cmd(srt_target_url):
    """Generates a fresh Pi 5 optimized ffmpeg command array on demand."""
    return [
        "ffmpeg", "-f", "v4l2", "-input_format", "mjpeg",   
        "-video_size", "1280x720", "-framerate", "15",         
        "-i", "/dev/video0", "-c:v", "libx264",          
        "-preset", "ultrafast", "-tune", "zerolatency",
        "-b:v", "2M", "-maxrate", "2M", "-bufsize", "4M",           
        "-pix_fmt", "yuv420p", "-g", "15", "-f", "mpegts",
        srt_target_url
    ]

def manage_stream():
    """Main thread: Turns the camera on or off based on the current status."""
    global current_status, stream_process, current_stream_url
    
    while True:
        if current_status == "STARTING":
            print(f"Paired with {assigned_driver}. Engaging Camera targeting {current_stream_url}...")
            
            # Generate the command line string with the fresh stream key details
            dynamic_cmd = build_ffmpeg_cmd(current_stream_url)
            stream_process = subprocess.Popen(dynamic_cmd)
            current_status = "STREAMING"
        
        elif current_status == "STREAMING":
            # Self-healing: If ffmpeg crashes while it should be streaming, recreate using same dynamic url
            if stream_process and stream_process.poll() is not None:
                print("Stream crashed or connection lost. Restarting stream runtime...")
                dynamic_cmd = build_ffmpeg_cmd(current_stream_url)
                stream_process = subprocess.Popen(dynamic_cmd)
        
        elif current_status == "STOPPING":
            if stream_process:
                print("Unpaired. Disengaging Camera...")
                stream_process.terminate()
                stream_process = None
            current_status = "AVAILABLE"
            
        time.sleep(1)

if __name__ == "__main__":
    print(f"--- {UNIT_ID} BOOTED. WAITING FOR DISPATCH ---")
    
    # Start the Comms thread to talk to the API
    comms_thread = threading.Thread(target=comms_loop, daemon=True)
    comms_thread.start()

    try:
        manage_stream()
    except KeyboardInterrupt:
        if stream_process:
            stream_process.terminate()
        sys.exit(0)
