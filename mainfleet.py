import subprocess
import os
import sys
import time
import threading
import requests

# CONFIGURATION
SERVER_IP = os.getenv("SERVER_IP", "100.97.37.123")
UNIT_ID = os.getenv("UNIT_ID", "UNASSIGNED_PI")
BASE_API_URL = os.getenv("SERVER_URL", "https://27carslivestream.co.uk")

# The API now requires this on /api/status and /api/command. This is the
# DEVICE-level secret, deliberately separate from the dashboard/admin
# secret the server uses for pairing and stream start/stop - a leaked Pi
# only exposes device-level access, never admin-level. Must match
# VAULT_DEVICE_SECRET set on the server exactly, or every poll will 401.
DEVICE_SECRET = os.getenv("DEVICE_SECRET", "")
if not DEVICE_SECRET:
    print("[!] WARNING: DEVICE_SECRET is not set. Server will reject this unit's "
          "status/command requests with 401 once the hardened API is deployed.")
AUTH_HEADERS = {"Authorization": f"Bearer {DEVICE_SECRET}"}

# STATE VARIABLES
current_status = "AVAILABLE"  # Boots up idle
assigned_driver = None
stream_process = None
current_stream_url = ""


def kill_stale_ffmpeg():
    """Make sure no orphaned ffmpeg process is holding /dev/video0."""
    subprocess.run(
        ["sh", "-c", "pkill -9 -f 'ffmpeg.*video0' 2>/dev/null || true"]
    )
    time.sleep(1)  # give the kernel a moment to release the device


def comms_loop():
    """Background thread: Sends status AND asks for commands every 5 seconds."""
    global current_status, assigned_driver, current_stream_url

    status_url = f"{BASE_API_URL}/api/status"
    command_url = f"{BASE_API_URL}/api/command?unit_id={UNIT_ID}"

    print(f"[*] Comms thread polling started for Unit ID: {UNIT_ID}")

    while True:
        # 1. SEND HEARTBEAT
        try:
            resp = requests.post(status_url, json={
                "unit_id": UNIT_ID,
                "status": current_status,
                "driver": assigned_driver
            }, headers=AUTH_HEADERS, timeout=5)
            if resp.status_code == 401:
                print("[!] Heartbeat rejected (401) — DEVICE_SECRET mismatch with server.")
        except Exception:
            pass

        # 2. CHECK FOR COMMANDS
        try:
            response = requests.get(command_url, headers=AUTH_HEADERS, timeout=5)
            if response.status_code == 401:
                print("[!] Command poll rejected (401) — DEVICE_SECRET mismatch with server.")
            elif response.status_code == 200:
                data = response.json()
                command = data.get("command")

                if command == "PAIR" and current_status not in ("STREAMING", "STARTING"):
                    assigned_driver = data.get("driver", "Unknown")
                    target_ip = data.get("stream_target", SERVER_IP)
                    stream_key = data.get("stream_key", UNIT_ID)

                    current_stream_url = (
                        f"srt://{target_ip}:8890?streamid=publish:{stream_key}"
                        f"&latency=300000&mode=caller&conntimeout=5000000"
                    )
                    current_status = "STARTING"

                elif command == "STOP_STREAM" and current_status in ("STREAMING", "STARTING"):
                    # End of job: stop the camera/ffmpeg but keep the driver paired.
                    print("[*] STOP_STREAM received. Ending job stream, staying paired.")
                    current_status = "STOPPING_STREAM"

                elif command == "UNPAIR" and current_status != "AVAILABLE":
                    # End of shift / disconnect: stop everything and go fully idle.
                    print("[*] UNPAIR received. Ending shift.")
                    assigned_driver = None
                    current_status = "STOPPING"

                elif command == "PANIC":
                    # Panic is informational only — does not change streaming state.
                    print("[!] PANIC ACK received from server. No local action taken.")

        except Exception as e:
            print(f"[!] Network error checking command gateway: {e}")

        time.sleep(5)


def build_ffmpeg_cmd(srt_target_url, driver_name="Unknown"):
    # Overlay removed - the drawtext filter isn't reliably available across
    # the fleet's ffmpeg builds (see the working reference unit, which never
    # had it). Raw feed only for now.
    return [
        "ffmpeg", "-y",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-video_size", "1280x720",
        "-framerate", "15",           # half the native rate — still smooth enough
        "-i", "/dev/video0",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-b:v", "800k",               # drop from 1.5M to 800k for spotty 5G
        "-maxrate", "800k",
        "-bufsize", "1600k",
        "-pix_fmt", "yuv420p",
        "-g", "15",                   # keyframe every second at 15fps
        "-f", "mpegts",
        srt_target_url
    ]


def manage_stream():
    """Main thread: turns the camera on/off based on the current status."""
    global current_status, stream_process, current_stream_url

    while True:
        if current_status == "STARTING":
            print(f"[+] Paired with {assigned_driver}. Engaging Camera targeting {current_stream_url}...")
            kill_stale_ffmpeg()
            dynamic_cmd = build_ffmpeg_cmd(current_stream_url)
            stream_process = subprocess.Popen(dynamic_cmd)
            current_status = "STREAMING"

        elif current_status == "STREAMING":
            # Self-heal if the process died unexpectedly
            if stream_process and stream_process.poll() is not None:
                print("[!] Stream crashed or connection lost. Attempting self-heal...")
                kill_stale_ffmpeg()
                time.sleep(2)  # let the camera hardware settle before reopening
                dynamic_cmd = build_ffmpeg_cmd(current_stream_url)
                stream_process = subprocess.Popen(dynamic_cmd)

        elif current_status == "STOPPING_STREAM":
            # Job ended: stop ffmpeg, but the driver remains paired to this unit.
            if stream_process:
                print("[-] Job ended. Stopping camera, remaining paired to driver.")
                stream_process.terminate()
                stream_process.wait()
                stream_process = None
                kill_stale_ffmpeg()
            current_status = "PAIRED_IDLE"

        elif current_status == "STOPPING":
            # Full unpair: stop everything and go back to AVAILABLE.
            if stream_process:
                print("[-] Unpaired. Disengaging Camera pipeline...")
                stream_process.terminate()
                stream_process.wait()
                stream_process = None
                kill_stale_ffmpeg()
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
