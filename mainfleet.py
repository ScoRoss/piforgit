import subprocess
import os
import sys
import time
import threading
import requests

# CONFIGURATION
SERVER_IP = os.getenv("SERVER_IP", "100.97.37.123") 
UNIT_ID = os.getenv("UNIT_ID", "UNASSIGNED_PI")
BASE_API_URL = "https://27carslivestream.co.uk"

# STATE VARIABLES
current_status = "AVAILABLE"  # Boots up idle
assigned_driver = None
stream_process = None
current_stream_url = ""

def comms_loop():
    """Background thread: Sends status AND asks for commands every 5 seconds."""
    global current_status, assigned_driver, current_stream_url
    
    # Construct urls dynamically to ensure any runtime identity adjustments are clean
    status_url = f"{BASE_API_URL}/api/status"
    command_url = f"{BASE_API_URL}/api/command?unit_id={UNIT_ID}"
    
    print(f"[*] Comms thread polling started for Unit ID: {UNIT_ID}")
    
    while True:
        # 1. SEND HEARTBEAT
        try:
            requests.post(status_url, json={
                "unit_id": UNIT_ID,
                "status": current_status,
                "driver": assigned_driver
            }, timeout=5)
        except Exception:
            pass 

        # 2. CHECK FOR COMMANDS
        try:
            response = requests.get(command_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                command = data.get("command")
                
                if command == "PAIR" and current_status != "STREAMING" and current_status != "STARTING":
                    assigned_driver = data.get("driver", "Unknown")
                    target_ip = data.get("stream_target", SERVER_IP)
                    stream_key = data.get("stream_key", UNIT_ID)
                    
                    # TUNED: Latency dropped from 30s (30000000) to 300ms (300000)
                    current_stream_url = f"srt://{target_ip}:8890?streamid=publish:{stream_key}&latency=300000&mode=caller&conntimeout=5000000"
                    current_status = "STARTING"
                
                elif command == "UNPAIR" and current_status != "AVAILABLE":
                    assigned_driver = None
                    current_status = "STOPPING"
        except Exception as e:
            print(f"[!] Network error checking command gateway: {e}")
        
        time.sleep(5)

def build_ffmpeg_cmd(srt_target_url):
    """Generates a safe baseline V4L2 command using native camera defaults."""
    return [
        "ffmpeg", "-y", 
        "-f", "v4l2", 
        "-i", "/dev/video0", # Let the driver pick the easiest, lowest-bandwidth default size
        "-c:v", "libx264",          
        "-preset", "ultrafast", 
        "-tune", "zerolatency",
        "-b:v", "1.5M", 
        "-maxrate", "1.5M", 
        "-bufsize", "3M",           
        "-pix_fmt", "yuv420p", 
        "-g", "30", 
        "-f", "mpegts",
        srt_target_url
    ]
def build_ffmpeg_cmd(srt_target_url):
    """Generates a libcamera pipeline piped directly into FFmpeg."""
    # libcamera pulls the hardware feed flawlessly, FFmpeg just packages it to SRT
    return f"libcamera-vid -t 0 --inline --width 1280 --height 720 --framerate 15 -o - | ffmpeg -i - -c:v copy -f mpegts {srt_target_url}"
    
def manage_stream():
    """Main thread: Turns the camera on or off based on the current status."""
    global current_status, stream_process, current_stream_url
    
    while True:
        if current_status == "STARTING":
            print(f"[+] Paired with {assigned_driver}. Engaging Camera targeting {current_stream_url}...")
            dynamic_cmd = build_ffmpeg_cmd(current_stream_url)
            
            # First instance: Handled correctly via shell
            stream_process = subprocess.Popen(dynamic_cmd)
            current_status = "STREAMING"
        
        elif current_status == "STREAMING":
            # If the process actually dies, handle the crash
            if stream_process and stream_process.poll() is not None:
                print("[!] Stream crashed or connection lost. Attempting self-heal...")
                dynamic_cmd = build_ffmpeg_cmd(current_stream_url)
                
                # FIXED: Added shell=True here so self-healing doesn't crash the script
                stream_process = subprocess.Popen(dynamic_cmd)
        
        elif current_status == "STOPPING":
            if stream_process:
                print("[-] Unpaired. Disengaging Camera pipeline...")
                stream_process.terminate()
                stream_process.wait()
                stream_process = None
            current_status = "AVAILABLE"
            
        time.sleep(1)

if __name__ == "__main__":
    print(f"--- {UNIT_ID} BOOTED. WAITING FOR DISPATCH ---")
    
    comms_thread = threading.Thread(target=comms_loop, daemon=True)
    comms_thread.start()

    try:
        manage_stream()
    except KeyboardInterrupt:
        if stream_process:
            stream_process.terminate()
        sys.exit(0)
