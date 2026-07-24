document.addEventListener("DOMContentLoaded", () => {
    console.log("[SOLARSCAN] Dashboard initialized.");

    // Elements
    const fastapiStatusEl = document.getElementById("fastapi-status");
    const webotsStatusEl = document.getElementById("webots-status");
    const webotsDotEl = document.getElementById("webots-dot");
    const webotsDescEl = document.getElementById("webots-desc-text");

    const quickAltEl = document.getElementById("quick-alt");
    const quickSpeedEl = document.getElementById("quick-speed");
    const quickAttEl = document.getElementById("quick-att");
    const quickBatEl = document.getElementById("quick-bat");

    const metricBatEl = document.getElementById("metric-bat");
    const batProgressEl = document.getElementById("bat-progress");
    const metricHotspotsEl = document.getElementById("metric-hotspots");
    const metricAltEl = document.getElementById("metric-alt");
    const metricStatusEl = document.getElementById("metric-status");
    const hudFlightModeEl = document.getElementById("hud-flight-mode");

    const streamImgEl = document.getElementById("live-stream-img");
    const fullscreenBtn = document.getElementById("fullscreen-btn");
    const snapshotBtn = document.getElementById("snapshot-btn");
    const reconnectBtn = document.getElementById("reconnect-webots-btn");
    const ctrlButtons = document.querySelectorAll(".ctrl-btn");

    // Fetch Telemetry periodically
    async function updateTelemetry() {
        try {
            const res = await fetch("/api/telemetry");
            if (!res.ok) throw new Error("Backend response error");
            
            const data = await res.json();
            const tel = data.telemetry || {};

            // Webots Status Update
            const connStatus = data.connection_status || (data.connected_webots ? "CONNECTED" : "DISCONNECTED");

            if (data.connected_webots || connStatus === "CONNECTED") {
                webotsStatusEl.textContent = "CONNECTED";
                webotsDotEl.className = "dot active";
                webotsDescEl.innerHTML = `Active IPC stream from Webots simulator (<code>Mavic 2 Pro</code>). Camera feed running at high fidelity.`;
            } else if (connStatus === "CONNECTING") {
                webotsStatusEl.textContent = "CONNECTING...";
                webotsDotEl.className = "dot warning";
                webotsDescEl.innerHTML = `Attempting IPC connection to Webots... Website remains active and responsive.`;
            } else {
                webotsStatusEl.textContent = "SYNTHETIC FEED";
                webotsDotEl.className = "dot warning";
                webotsDescEl.innerHTML = `Webots offline or not connected yet. Streaming synthetic solar array inspection feed. Click <strong>Sync Webots</strong> anytime to connect.`;
            }

            if (fastapiStatusEl) fastapiStatusEl.textContent = "8000 Active";

            // Update Telemetry Values
            const alt = tel.altitude !== undefined ? tel.altitude : 12.4;
            const spd = tel.speed !== undefined ? tel.speed : 3.2;
            const bat = tel.battery !== undefined ? tel.battery : 88.5;
            const pitch = tel.pitch !== undefined ? tel.pitch : 0.0;
            const roll = tel.roll !== undefined ? tel.roll : 0.0;
            const status = tel.status || "SCANNING";
            const hotspots = tel.hotspots_detected !== undefined ? tel.hotspots_detected : 3;

            quickAltEl.textContent = `${alt} m`;
            quickSpeedEl.textContent = `${spd} m/s`;
            quickAttEl.textContent = `${pitch}° / ${roll}°`;
            quickBatEl.textContent = `${bat}%`;

            metricBatEl.textContent = `${bat}%`;
            batProgressEl.style.width = `${bat}%`;
            metricHotspotsEl.textContent = hotspots;
            metricAltEl.innerHTML = `${alt} <small>m</small>`;
            metricStatusEl.textContent = status;
            hudFlightModeEl.textContent = status;

        } catch (err) {
            console.warn("[SOLARSCAN] Telemetry poll failed:", err);
            fastapiStatusEl.textContent = "Disconnected";
            webotsStatusEl.textContent = "Offline";
            webotsDotEl.className = "dot";
        }
    }

    // Control Commands
    async function sendControl(command) {
        try {
            console.log(`[SOLARSCAN] Sending control command: ${command}`);
            const res = await fetch("/api/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command })
            });
            const result = await res.json();
            console.log("[SOLARSCAN] Command result:", result);
            updateTelemetry();
        } catch (err) {
            console.error("[SOLARSCAN] Failed to send command:", err);
        }
    }

    // Event Listeners for Control Buttons
    ctrlButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const cmd = btn.getAttribute("data-command");
            if (cmd) sendControl(cmd);
        });
    });

    // Reconnect Button
    if (reconnectBtn) {
        reconnectBtn.addEventListener("click", async () => {
            reconnectBtn.disabled = true;
            reconnectBtn.innerText = "Connecting...";
            try {
                await fetch("/api/connect_webots", { method: "POST" });
            } catch (e) {
                console.warn("Connect request error:", e);
            }
            setTimeout(() => {
                reconnectBtn.disabled = false;
                reconnectBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg> Sync Webots`;
            }, 3000);
        });
    }

    // Fullscreen Mode
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener("click", () => {
            const wrapper = document.getElementById("stream-wrapper");
            if (!document.fullscreenElement) {
                wrapper.requestFullscreen().catch(err => {
                    alert(`Error attempting to enable fullscreen mode: ${err.message}`);
                });
            } else {
                document.exitFullscreen();
            }
        });
    }

    // Snapshot Feature
    if (snapshotBtn) {
        snapshotBtn.addEventListener("click", () => {
            const canvas = document.createElement("canvas");
            canvas.width = streamImgEl.naturalWidth || 640;
            canvas.height = streamImgEl.naturalHeight || 480;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(streamImgEl, 0, 0, canvas.width, canvas.height);

            const a = document.createElement("a");
            a.href = canvas.toDataURL("image/jpeg");
            a.download = `SolarScan_Snapshot_${Date.now()}.jpg`;
            a.click();
        });
    }

    // Stream error handler
    window.handleStreamError = function(img) {
        console.warn("[SOLARSCAN] Video stream disconnected. Retrying connection...");
        setTimeout(() => {
            img.src = "/video_feed?t=" + Date.now();
        }, 3000);
    };

    // Poll Telemetry every 1 second
    setInterval(updateTelemetry, 1000);
    updateTelemetry();
});
