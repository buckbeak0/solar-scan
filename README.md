# SolarScan: Webots Drone Solar Panel Inspection Dashboard

SolarScan is a real-time drone simulation and solar array inspection command center. It features a Python FastAPI backend that interfaces with a Webots simulation (controlling a DJI Mavic 2 Pro drone) and serves a high-tech, dark-themed, glassmorphic web interface.

> [!NOTE]
> **Synthetic Fallback Mode:** If Webots is not running or connected, the system automatically falls back to an interactive synthetic thermal solar array inspection stream so the web application is fully usable and testable standalone.

---

## 🛠️ Features

- **Live Video Viewport:** Displays the live drone camera feed with an interactive HUD overlay (gimbal FOV, target lock, and current status).
- **Asynchronous Webots IPC Sync:** Connects to the Webots drone simulation on-demand using a background thread (`POST /api/connect_webots`) without blocking the server.
- **Real-Time Telemetry:** Continuous display of altitude, battery percentage (with progression bar), airspeed, pitch/roll values, and detected thermal hotspot anomalies.
- **Interactive Controls:** Control panel to issue drone commands (`Takeoff`, `Start Solar Scan`, `Return to Home`, `Land`, and `Sync Webots`).
- **Media tools:** Instant camera snapshots and fullscreen view support directly from the browser.

---

## 📂 Project Structure

- `main.py` - Single FastAPI server hosting web endpoints, API telemetry, control commands, and static pages.
- `static/` - Web assets containing:
  - `index.html` - Structural markup for the control dashboard.
  - `style.css` - Custom styling using dark mode glassmorphism and subtle animations.
  - `app.js` - Telemetry polling, UI updates, and control handler actions.
- `requirements.txt` - Python package list.
- `setup_env.bat` - Automates python virtualenv initialization and dependency installation.
- `run.bat` - Starts the FastAPI application.

---

## 🚀 Setup & Launch Instructions

### Prerequisites
1. **Python 3.10+** installed and added to system PATH.
2. **Webots Simulator** (optional, version R2023 or newer recommended) installed at default directory `C:\Program Files\Webots`.

### Setup Environment
1. Double-click the **`setup_env.bat`** script or run it in your terminal:
   ```cmd
   .\setup_env.bat
   ```
   This will:
   - Create a local python virtual environment (`.venv`).
   - Upgrade pip.
   - Install dependencies (`fastapi`, `uvicorn`, `opencv-python`, `numpy`).

### Run the Project
1. Run the launcher script **`run.bat`**:
   ```cmd
   .\run.bat
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

### 🛰️ Connecting to Webots Simulation

To connect the FastAPI dashboard to a running Webots simulation, follow these steps:

1. **Open the Webots World:**
   Open Webots and load your drone simulation scene.
2. **Configure the Drone Robot in Webots:**
   - In the Webots scene tree, locate the drone node (e.g. `Mavic2Pro`).
   - Change the `name` field of the robot to **`Mavic 2 Pro`** (case-sensitive, matches `main.py`).
   - Find the `controller` field of the robot and set it to **`<extern>`**. This allows external Python programs to control it.
3. **Run the Simulation:**
   - Click the **Play** button in the Webots window to start the simulation clock.
4. **Synchronize Dashboard:**
   - Open `http://localhost:8000` in your web browser.
   - Click the **Sync Webots** button in the top navigation header. The dashboard status pill will transition to `CONNECTING...` in the background and switch seamlessly to the live drone camera feed once the IPC handshake completes.

> [!TIP]
> The Python environment variables (`WEBOTS_HOME`, `PYTHONPATH`, and `PATH`) required to resolve Webots controller libraries are automatically configured inside [run.bat](file:///e:/Projects/SolarScan/run.bat) at launch.

