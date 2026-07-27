import os
import sys
import time
import math
import threading
from typing import Generator
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2

# Ensure Webots Python Controller library is in system path
WEBOTS_HOME = r"C:\Program Files\Webots"
if os.path.exists(WEBOTS_HOME):
    os.environ["WEBOTS_HOME"] = WEBOTS_HOME
    py_path = os.path.join(WEBOTS_HOME, "lib", "controller", "python")
    if py_path not in sys.path:
        sys.path.append(py_path)
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        dll_path = os.path.join(WEBOTS_HOME, "lib", "controller")
        if os.path.exists(dll_path):
            try:
                os.add_dll_directory(dll_path)
            except Exception as e:
                print(f"[WARN] Failed to add DLL directory: {e}")

os.environ["WEBOTS_CONTROLLER_URL"] = "ipc://1234/Mavic 2 Pro"

app = FastAPI(title="SolarScan Webots Drone Mission Control", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mounting
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Global Webots Connection State
webots_robot = None
camera_device = None
is_webots_connected = False
connection_status = "DISCONNECTED"  # DISCONNECTED | CONNECTING | CONNECTED | FAILED
connection_lock = threading.Lock()

drone_state = {
    "status": "SCANNING",
    "altitude": 12.4,
    "speed": 3.2,
    "battery": 88.5,
    "pitch": 0.0,
    "roll": 0.0,
    "yaw": 45.0,
    "hotspots_detected": 3,
    "mode": "AUTONOMOUS SCAN"
}

def _bg_connect_webots():
    """Asynchronous background worker to connect to Webots IPC without blocking FastAPI server."""
    global webots_robot, camera_device, is_webots_connected, connection_status
    with connection_lock:
        if connection_status == "CONNECTING":
            return
        connection_status = "CONNECTING"

    print("[INFO] Background thread attempting Webots IPC connection...")
    try:
        from controller import Robot
        robot = Robot()
        time_step = int(robot.getBasicTimeStep()) if hasattr(robot, "getBasicTimeStep") else 32
        cam = robot.getDevice("camera")
        if cam:
            cam.enable(time_step)
            webots_robot = robot
            camera_device = cam
            is_webots_connected = True
            connection_status = "CONNECTED"
            print("[INFO] Connected successfully to Webots Mavic 2 Pro Camera!")
            return
    except Exception as ex:
        print(f"[INFO] Webots connection attempt failed: {ex}")

    is_webots_connected = False
    connection_status = "FAILED"

def trigger_webots_connection():
    """Triggers non-blocking background connection attempt."""
    if connection_status == "CONNECTING":
        return False
    t = threading.Thread(target=_bg_connect_webots, daemon=True)
    t.start()
    return True

def generate_synthetic_solar_frame(frame_counter: int) -> np.ndarray:
    """Generates simulated camera feed showing solar panel array inspection with thermal overlays."""
    width, height = 640, 480
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Background terrain (dark green/gray ground)
    frame[:] = (35, 45, 35)

    # Grid of Solar Panels moving downwards to simulate drone flight
    offset_y = (frame_counter * 3) % 120
    panel_width, panel_height = 130, 90
    margin_x, margin_y = 20, 30

    for r in range(-1, 6):
        y1 = r * (panel_height + margin_y) + offset_y
        y2 = y1 + panel_height
        for c in range(4):
            x1 = c * (panel_width + margin_x) + 30
            x2 = x1 + panel_width

            if y2 > 0 and y1 < height:
                # Solar Panel Body (Deep Blue Metallic)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (120, 70, 20), -1)
                # Border
                cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 160, 80), 2)
                # Solar Grid Lines
                for gx in range(x1 + 25, x2, 25):
                    cv2.line(frame, (gx, y1), (gx, y2), (160, 110, 40), 1)
                for gy in range(y1 + 30, y2, 30):
                    cv2.line(frame, (x1, gy), (x2, gy), (160, 110, 40), 1)

    # Add simulated Thermal Hotspots (Faulty Solar Cells)
    hotspot_1_y = int((200 + offset_y) % height)
    hotspot_2_y = int((380 + offset_y) % height)
    
    # Hotspot 1 (Red/Yellow glow)
    cv2.circle(frame, (115, hotspot_1_y), 14, (0, 0, 255), -1)
    cv2.circle(frame, (115, hotspot_1_y), 7, (0, 255, 255), -1)
    cv2.putText(frame, "ANOMALY: 68C", (135, hotspot_1_y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

    # Hotspot 2
    cv2.circle(frame, (415, hotspot_2_y), 18, (0, 0, 255), -1)
    cv2.circle(frame, (415, hotspot_2_y), 9, (0, 255, 255), -1)
    cv2.putText(frame, "ANOMALY: 74C", (435, hotspot_2_y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

    # Drone HUD Overlays
    center_x, center_y = width // 2, height // 2
    
    # Reticle / Crosshair
    cv2.circle(frame, (center_x, center_y), 30, (0, 255, 180), 1)
    cv2.line(frame, (center_x - 45, center_y), (center_x - 15, center_y), (0, 255, 180), 2)
    cv2.line(frame, (center_x + 15, center_y), (center_x + 45, center_y), (0, 255, 180), 2)
    cv2.line(frame, (center_x, center_y - 45), (center_x, center_y - 15), (0, 255, 180), 2)
    cv2.line(frame, (center_x, center_y + 15), (center_x, center_y + 45), (0, 255, 180), 2)

    # Status Banner
    if connection_status == "CONNECTED":
        status_text = "MODE: WEBOTS MAVIC 2 PRO"
        status_color = (0, 255, 0)
    elif connection_status == "CONNECTING":
        status_text = "MODE: CONNECTING TO WEBOTS..."
        status_color = (0, 255, 255)
    else:
        status_text = "MODE: SIMULATED SOLAR ARRAY (CLICK CONNECT WEBOTS)"
        status_color = (0, 220, 255)

    cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, status_color, 2)
    
    # Timestamp overlay
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, f"CAM01 | {timestamp}", (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    # Battery and AI Target Lock
    cv2.putText(frame, "[AI TARGET LOCK: ACTIVE]", (width - 220, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 180), 1)

    return frame

def capture_webots_frame() -> np.ndarray:
    global webots_robot, camera_device, is_webots_connected, connection_status
    if not is_webots_connected or not webots_robot or not camera_device:
        return None
    try:
        time_step = int(webots_robot.getBasicTimeStep())
        if webots_robot.step(time_step) != -1:
            w, h = camera_device.getWidth(), camera_device.getHeight()
            raw_img = camera_device.getImage()
            if raw_img:
                img = np.frombuffer(raw_img, dtype=np.uint8).reshape((h, w, 4))
                return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    except Exception as e:
        print(f"[WARN] Error capturing frame from Webots: {e}")
        is_webots_connected = False
        connection_status = "FAILED"
    return None

def get_next_frame(frame_counter: int) -> bytes:
    frame = None
    if is_webots_connected:
        frame = capture_webots_frame()
    
    if frame is None:
        frame = generate_synthetic_solar_frame(frame_counter)

    ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ret:
        return b''
    return jpeg.tobytes()

def frame_generator():
    counter = 0
    while True:
        counter += 1
        frame_bytes = get_next_frame(counter)
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.04)  # ~25 FPS

@app.get("/")
def read_root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"service": "SolarScan FastAPI Webots Streaming Service", "status": "running"}

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/telemetry")
def get_telemetry():
    t = time.time()
    drone_state["pitch"] = round(math.sin(t * 1.5) * 2.5, 2)
    drone_state["roll"] = round(math.cos(t * 1.2) * 1.8, 2)
    drone_state["altitude"] = round(12.4 + math.sin(t * 0.5) * 0.3, 2)
    drone_state["speed"] = round(3.2 + math.cos(t * 0.8) * 0.4, 2)
    drone_state["battery"] = max(10.0, round(92.0 - (t % 300) * 0.05, 1))
    
    return {
        "connected_webots": is_webots_connected,
        "connection_status": connection_status,
        "drone_name": "Mavic 2 Pro",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "telemetry": drone_state
    }

@app.post("/api/connect_webots")
def connect_webots_endpoint():
    """Endpoint triggered by user on the website to initiate connection to Webots."""
    started = trigger_webots_connection()
    return {
        "status": "connection_initiated" if started else "already_connecting",
        "connection_status": connection_status,
        "is_connected": is_webots_connected
    }

@app.post("/api/control")
def send_control_command(payload: dict):
    cmd = payload.get("command", "")
    print(f"[CONTROL] Received drone command: {cmd}")
    if cmd == "takeoff":
        drone_state["status"] = "TAKEOFF"
        drone_state["altitude"] = 15.0
    elif cmd == "land":
        drone_state["status"] = "LANDING"
        drone_state["altitude"] = 0.0
    elif cmd == "scan":
        drone_state["status"] = "SCANNING"
    elif cmd == "rth":
        drone_state["status"] = "RETURNING HOME"
    elif cmd == "reconnect_webots":
        trigger_webots_connection()
        return {"status": "connection_initiated", "connection_status": connection_status}
    
    return {"status": "command_received", "executed": cmd, "current_state": drone_state}

if __name__ == "__main__":
    import uvicorn
    print("==================================================")
    print("SolarScan FastAPI Mission Control Server running at http://localhost:8000")
    print("==================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000)