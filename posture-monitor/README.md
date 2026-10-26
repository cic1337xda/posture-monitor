# 🖥️ Posture AI — Server & Web Dashboard Module (`posture-monitor`)

This directory houses the containerized backend server, computer vision inference pipeline, database authentication service, and Apple Liquid Glass web dashboard for the **Posture AI System**.

---

## 📑 Language Options
* 🇬🇧 **[English Documentation (Current)](README.md)**
* 🇲🇾 **[Dokumentasi Bahasa Melayu](README_MY.md)**

---

## 📚 Technical Documentation Index

| Document | Description |
| :--- | :--- |
| 📖 **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** | Complete endpoint reference for authentication, frame inference, and hardware controls. |
| 🐳 **[DOCKER_AND_SERVICES.md](DOCKER_AND_SERVICES.md)** | Multi-container Docker Compose architecture, Mosquitto broker setup, and environment variables. |
| 🛡️ **[SECURITY_AND_ARCHITECTURE.md](SECURITY_AND_ARCHITECTURE.md)** | Deep dive into Bcrypt authentication, HttpOnly cookies, Resend OTP, and 5-vector computer vision algorithms. |

---

## 🛠️ Technology Stack

* **Web Framework:** Flask 3.0+ / Python 3.11-slim
* **WSGI Production Server:** Gunicorn 21.2 (4 threads, non-blocking)
* **Computer Vision Engine:** Google MediaPipe Pose 0.10.14 & Pillow 10+
* **Authentication & Cryptography:** Bcrypt + PyJWT (`HttpOnly; SameSite=Lax` cookies)
* **Database:** SQLite 3 (`posture_auth.db`) with automatic table migration
* **Transactional Email:** Resend API integration (`posture@mail.flowkraft.xyz`)
* **Haptic Telemetry Broker:** Eclipse Mosquitto v2.0 (MQTT)
* **Frontend UI Engine:** Apple Liquid Glass (Vanilla JS, Canvas, WebRTC, Web Audio API, Google Font Roboto)

---

## 🚀 Local Docker Launch

```bash
# 1. Prepare Environment Variables
cp .env.example .env

# 2. Build and Start Multi-Container Stack
docker compose up -d --build

# 3. View Real-Time Server Logs
docker compose logs -f posture-monitor
```

* **Dashboard URL:** `http://localhost:5000`
* **Health Endpoint:** `http://localhost:5000/api/v1/health`
* **MQTT Telemetry Port:** `1888` (external WAN/host) $\rightarrow$ `1883` (internal Docker network)
