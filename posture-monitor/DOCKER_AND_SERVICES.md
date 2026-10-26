# 🐳 Docker Architecture & Container Services (`DOCKER_AND_SERVICES.md`)

This document defines the containerized infrastructure, multi-service network topology, environment variable specifications, and orchestration commands for the **Posture AI Platform**.

---

## 🏛️ Multi-Container Topology

The application stack is orchestrated via `docker-compose.yml` into two decoupled, high-performance microservices:

```
+---------------------------------------------------------------------------------------------------+
|                                  DOCKER NETWORK: pwn20wnd-network                                 |
+---------------------------------------------------------------------------------------------------+

              [ INBOUND CLIENT TRAFFIC ]                         [ INBOUND WEARABLE MQTT ]
                     Port: 5000                                         Port: 1888
                          |                                                  |
                          v                                                  v
     +-----------------------------------------+        +-----------------------------------------+
     |        SERVICE: posture-monitor         |        |       SERVICE: posturemonitor-mqtt      |
     |                                         |        |                                         |
     |  - Container Name: posture-monitor      |        |  - Container Name: posturemonitor-mqtt  |
     |  - Base: python:3.11-slim-bookworm      |  TCP   |  - Image: eclipse-mosquitto:latest      |
     |  - Web Server: Gunicorn (4 Threads)     | =====> |  - Ports: 1888 (Host) -> 1883 (Cont.)   |
     |  - AI Engine: MediaPipe Pose 0.10.14    | :1883  |  - Persistence: mosquitto.conf mounted  |
     |  - Storage: Persistent SQLite Auth DB   |        |  - Network: pwn20wnd-network            |
     +-----------------------------------------+        +-----------------------------------------+
```

---

## ⚙️ Service Specifications

### 1. `posture-monitor` (Application Server & AI Engine)
* **Build Context:** `./backend` (`Dockerfile`)
* **Base Image:** `python:3.11-slim-bookworm`
* **Exposed Port:** `5000:5000`
* **Process Manager:** `gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 0 app:app`
* **Timezone:** `Asia/Kuala_Lumpur` (GMT+8)
* **Log Rotation:** Limited to $10\,\text{MB}$ per file, maximum 3 rotated files.

### 2. `posturemonitor-mqtt` (Haptic Telemetry Broker)
* **Image:** `eclipse-mosquitto:latest`
* **Host Port:** `1888` $\rightarrow$ Container Port `1883`
* **Configuration Volume:** `./mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf`
* **Network:** Connected to bridge network `pwn20wnd-network`.

---

## 📋 Environment Variables Matrix

All configuration parameters are defined in `.env` and injected into the containers:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `TZ` | `Asia/Kuala_Lumpur` | Synchronizes system timestamps to Malaysia Time (GMT+8) |
| `MAX_SITTING_SECONDS` | `600` | Continuous sitting threshold before sedentary alarm triggers ($10\,\text{mins}$) |
| `MAX_BAD_POSTURE_SECONDS` | `5.0` | Threshold of continuous slouching before bad posture alarm fires |
| `WARNING_PERCENT` | `0.60` | Fraction of sitting time at which visual warning state triggers |
| `CRITICAL_PERCENT` | `0.85` | Fraction of sitting time at which critical warning state triggers |
| `DETECTION_CONFIDENCE` | `0.60` | MediaPipe pose tracking & landmark confidence threshold |
| `CALIBRATION_FRAMES` | `25` | Number of sequential frames collected during baseline calibration |
| `RESEND_API_KEY` | *(Secret)* | Bearer authentication key for Resend Email API |
| `RESEND_FROM_EMAIL` | `posture@mail.flowkraft.xyz` | Authoritative sender address for transactional OTP emails |
| `JWT_SECRET_KEY` | *(Secret 32+ bytes)* | Cryptographic HMAC secret for signing session cookies |
| `MQTT_BROKER` | `posturemonitor-mqtt` | Hostname of the Mosquitto broker service within the Docker network |

---

## 🚀 Lifecycle & Deployment Commands

### 1. Ensure Shared Docker Network Exists
```bash
docker network inspect pwn20wnd-network >/dev/null 2>&1 || docker network create pwn20wnd-network
```

### 2. Launch Services in Background
```bash
docker compose up -d --build
```

### 3. Monitor Real-Time Container Logs
```bash
docker compose logs -f posture-monitor
```

### 4. Graceful Shutdown
```bash
docker compose down
```

### 5. Check Service Health Status
```bash
curl http://localhost:5000/api/v1/health
```
