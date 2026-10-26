<p align="center">
  <img src="logo.svg" width="130" height="130" alt="Posture AI Project Logo" />
</p>

<h1 align="center">Posture AI</h1>

<p align="center">
  <b>Next-Gen Real-Time Computer Vision Ergonomic Posture Tracking & IoT Haptic Feedback System</b>
</p>

<p align="center">
  <a href="posture-monitor/DOCKER_AND_SERVICES.md"><img src="https://img.shields.io/badge/Architecture-Edge--to--Cloud-3d63dd?style=for-the-badge&logo=espressif" alt="Architecture" /></a>
  <a href="posture-monitor/API_DOCUMENTATION.md"><img src="https://img.shields.io/badge/Backend-Flask%203.0+-009688?style=for-the-badge&logo=flask" alt="Flask" /></a>
  <a href="posture-monitor/SECURITY_AND_ARCHITECTURE.md"><img src="https://img.shields.io/badge/AI%20Vision-MediaPipe%20Pose-ff6f00?style=for-the-badge&logo=google" alt="MediaPipe" /></a>
  <a href="esp32/MQTT_SPECIFICATION.md"><img src="https://img.shields.io/badge/MQTT-Mosquitto%202.0-d32f2f?style=for-the-badge&logo=eclipse-mosquitto" alt="MQTT" /></a>
  <a href="posture-monitor/DOCKER_AND_SERVICES.md"><img src="https://img.shields.io/badge/Docker-Multi--Container-2496ed?style=for-the-badge&logo=docker" alt="Docker" /></a>
  <a href="posture-monitor/SECURITY_AND_ARCHITECTURE.md"><img src="https://img.shields.io/badge/Auth-Bcrypt%20%2B%20Resend%20OTP-34c759?style=for-the-badge&logo=gmail" alt="Auth" /></a>
</p>

> **Posture AI** is an intelligent ergonomic health and biometric tracking platform. Combining real-time **Google MediaPipe Pose Computer Vision** with an **ESP32-C3 Wearable Haptic Watch**, it analyzes seating posture, detects spine slouching, monitors sedentary time, and enforces healthy workplace habits through synchronous audio and tactile vibration alarms.

---

## 📑 Language Options
* 🇬🇧 **[English Documentation (Current)](README.md)**
* 🇲🇾 **[Dokumentasi Bahasa Melayu](README_MY.md)**

---

## 🏛️ High-Level System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                     POSTURE AI SYSTEM TOPOLOGY                                    |
+---------------------------------------------------------------------------------------------------+

     [ DESKTOP CLIENT / WEBCAM ]                                      [ SERVER & DOCKER ENGINE ]
     Folder: posture-monitor/backend/static                           Folder: posture-monitor/

 +------------------------------------+                             +-----------------------------------+
 |         DESKTOP WEB BROWSER        |                             |         POSTURE-MONITOR           |
 |  - Apple Liquid Glass Theme Engine |   HTTPS / REST POST Frame   |         CONTAINER (5000)          |
 |  - WebRTC Video Stream Capture     | ==========================> |  - Flask 3.0 + Gunicorn Engine    |
 |  - Client-Side Mobile Device Block |                             |  - Google MediaPipe Pose 0.10.14  |
 |  - Web Audio Synthesizer Beep      | <========================== |  - Real-Time Feature Extractor    |
 |  - JWT HttpOnly Cookie Auth        |    Telemetry JSON Response  |  - Sedentary & Slouch Chronometer |
 +------------------------------------+                             |  - SQLite Auth + Bcrypt Hash      |
                                                                    +-----------------------------------+
                                                                                      |
     [ WEARABLE HAPTIC CLIENT ]                                                       | Local TCP:1883
     Folder: esp32/                                                                   v
 +------------------------------------+                             +-----------------------------------+
 |       ESP32-C3 WEARABLE WATCH      |                             |        ECLIPSE MOSQUITTO          |
 |  - RISC-V 160MHz Microcontroller   |    MQTT (Port 1888/1883)    |        MQTT BROKER (v2.0)         |
 |  - WiFiManager Captive Portal AP   | <========================== |  - Non-Blocking Publish/Subscribe |
 |  - Transistor-Driven Coin Motor    |   posture/wearable/{MAC}/cmd|  - Port 1888 Upstream Host Map    |
 |  - 400ms Haptic Duty Pulse         |                             +-----------------------------------+
 |  - RF Power Limiter (8.5 dBm)      |                                               |
 +------------------------------------+                                               v
                                                                    +-----------------------------------+
                                                                    |        RESEND EMAIL API           |
                                                                    |  - 6-Digit Cryptographic OTP      |
                                                                    |  - Account Activation & Password  |
                                                                    |  - posture@mail.flowkraft.xyz     |
                                                                    +-----------------------------------+
```

---

## 🔌 Hardware Circuit & Wiring Schematic

The wearable haptic device is driven by an **ESP32-C3 SuperMini** paired with an NPN transistor-driven coin vibration motor with flyback protection:

<p align="center">
  <img src="Schematic_posturemonitor_2026-10-26.png" width="860" alt="Posture AI ESP32-C3 Wearable Circuit Schematic" />
</p>

### 📌 Hardware Pinout Table
| Component | ESP32-C3 Pin | Purpose | Technical Specification |
| :--- | :--- | :--- | :--- |
| **Vibration Motor (+)** | `3.3V` / `VCC` | Power Supply | 3.3V DC / ~70mA operating current |
| **Transistor Base (B)** | `GPIO 8` | PWM Trigger Signal | Controlled via $1\,\text{k}\Omega$ series resistor (`MOTOR_PIN`) |
| **Transistor Emitter (E)** | `GND` | Ground Reference | Common ground rail |
| **Transistor Collector (C)**| Motor (-) | Switched Ground Sink | Connects to vibration motor negative terminal |
| **Flyback Diode (1N4001)** | Across Motor | Inductive Spike Protection | Cathode to 3.3V, Anode to Collector |
| **Built-in LED** | `GPIO 8` | Visual Indicator | Blinks synchronously with haptic motor pulse |

* 📄 **Download Printable Schematic PDF:** [`Schematic_posturemonitor_2026-10-26.pdf`](Schematic_posturemonitor_2026-10-26.pdf)
* 📄 **Detailed Wiring & Pinout Guide:** [`esp32/PINOUT_AND_WIRING.md`](esp32/PINOUT_AND_WIRING.md)
* 📡 **MQTT Telemetry Protocol Guide:** [`esp32/MQTT_SPECIFICATION.md`](esp32/MQTT_SPECIFICATION.md)
* ⚡ **Firmware Flashing Guide:** [`esp32/FLASHING_AND_SETUP.md`](esp32/FLASHING_AND_SETUP.md)

---

## 🌟 Key Features & Innovations

### 1. Proximity-Invariant Standing vs. Sitting Detection
* Measures Euclidean distance between `LEFT_SHOULDER` and `RIGHT_SHOULDER`.
* Calculates dynamic scale factor:
  $$\text{Scale Factor} = \frac{\text{Current Shoulder Width}}{\text{Baseline Shoulder Width}}$$
* Scales the expected resting shoulder Y line dynamically. When a user leans closer or pushes back from the webcam, the system **never falsely triggers a standing state**.

### 2. Multi-Vector Bad Posture & Anti-Cheat Engine
Unlike naive posture trackers that only measure neck compression, Posture AI implements a 5-point evaluation matrix:
1. **Forward Slouching:** Detects when $\text{Neck Ratio} < 88\%$ of upright baseline.
2. **Anti-Cheat 1 (Shoulder Slump):** If a user slumps into their chair and tilts their chin upward to cheat the tracker, the system flags **Shoulder Drop** ($> +0.035$).
3. **Anti-Cheat 2 (Head Pitch Craning):** Detects excessive upward chin craning ($\text{Head Pitch} > +0.045$).
4. **Bowed Head:** Detects downward gaze/phone browsing ($\text{Head Pitch} < -0.065$).
5. **Lateral Leaning:** Detects uneven shoulder tilt ($> 10\%$).

### 3. Dual Alert Mechanism (Sedentary + Slouch)
* **Sedentary Limit:** Alerts users when continuous sitting duration exceeds configured limits (e.g. 10m, 20m, 30m, or custom seconds). Requires standing for **5 uninterrupted seconds** to reset.
* **Persistent Bad Posture:** If a user remains in a bad posture for **$\ge 5$ consecutive seconds**, browser alarms and ESP32 haptic vibration engage simultaneously until posture is corrected.
* **100% Standalone Capable:** If no ESP32 is online, the browser uses internal **Web Audio API** beeps and visual indicators seamlessly.

### 4. Apple Liquid Glass UI & Desktop Blocker
* Engineered with `backdrop-filter: blur(45px) saturate(190%)` and Radix Precision color tokens.
* **Desktop-First Mobile Blocker:** Automatically displays an ergonomic notice when accessed from smartphones, requiring desktop/laptop screen dimensions.
* **Consistent Typography:** Strict global Google Font **Roboto** rendering across all controls, switches, and badges.

### 5. Enterprise Security & Authentication (DEVELOPMENT.md Standard)
* User registration and login protected with **Bcrypt** cryptographic password hashing.
* **Resend API Integration:** One-Time Passcodes (6-digit OTP) delivered via `posture@mail.flowkraft.xyz` for account activation and password recovery.
* **HttpOnly JWT Session Cookies:** Protection against Cross-Site Scripting (XSS).
* Account lockout after 5 consecutive failed login attempts.

---

## 📂 Repository Structure

```text
.
├── logo.svg                          # Master Vector Project Logo
├── favicon.svg                       # Browser Tab Vector Icon
├── favicon.ico                       # Multi-resolution ICO (16x16 to 64x64)
├── schematic.svg                     # Vector Hardware Circuit Schematic
├── Schematic_posturemonitor_2026-10-26.png # Hardware Circuit Schematic (PNG)
├── Schematic_posturemonitor_2026-10-26.pdf # Printable Circuit Schematic (PDF)
├── README.md                         # Main Documentation (English)
├── README_MY.md                      # Dokumentasi Utama (Bahasa Melayu)
│
├── esp32/                            # Wearable Haptic Client Scope
│   ├── README.md                     # Hardware Overview (English)
│   ├── README_MY.md                  # Gambaran Keseluruhan Hardware (Melayu)
│   ├── PINOUT_AND_WIRING.md          # Hardware Pinout & Breadboard Guide
│   ├── MQTT_SPECIFICATION.md         # MQTT Topics & Payload Specifications
│   ├── FLASHING_AND_SETUP.md         # Arduino IDE / ESP-IDF Setup Guide
│   └── use-for-production-12sept2026-332pm/
│       └── use-for-production-12sept2026-332pm.ino # Production Firmware
│
└── posture-monitor/                  # Containerized Server & Web Dashboard Scope
    ├── README.md                     # Backend & Dashboard Overview (English)
    ├── README_MY.md                  # Gambaran Keseluruhan Backend (Melayu)
    ├── API_DOCUMENTATION.md          # Complete REST API Endpoint Reference
    ├── DOCKER_AND_SERVICES.md        # Docker Compose & Architecture Guide
    ├── SECURITY_AND_ARCHITECTURE.md  # Security Mandates & Algorithm Deep Dive
    ├── docker-compose.yml            # Multi-Container Orchestration (Flask + MQTT)
    ├── .env.example                  # Environment Configuration Template
    ├── mosquitto/                    # Mosquitto Broker Configuration
    └── backend/                      # Python Core
        ├── app.py                    # Flask Server & Inference Pipeline
        ├── auth_db.py                # SQLite User & OTP Management
        ├── email_service.py          # Resend API Integration
        ├── requirements.txt          # Python Dependencies
        ├── Dockerfile                # Production Container Image
        └── static/                   # Liquid Glass Web Assets (index, login, privacy, 404)
```

---

## 🚀 Quick Start Guide

### 1. Launch the Docker Server Stack
```bash
cd posture-monitor/
cp .env.example .env
# Edit .env with your RESEND_API_KEY if testing email delivery

docker compose up -d --build
```
* **Web Dashboard:** Open `http://localhost:5000` (or `http://<SERVER_IP>:5000`)
* **Health Check:** `http://localhost:5000/api/v1/health`
* **MQTT Port:** Exposed on `1888` (external) $\rightarrow$ `1883` (internal container).

### 2. Flash the ESP32 Wearable Watch
1. Open Arduino IDE and install board package `esp32 by Espressif Systems` (select **ESP32C3 Dev Module**).
2. Install libraries: `PubSubClient` by Nick O'Leary and `WiFiManager` by tzapu.
3. Open `esp32/use-for-production-12sept2026-332pm/use-for-production-12sept2026-332pm.ino`.
4. Upload to the ESP32-C3.
5. Connect your phone/laptop to AP `Posture_Watch_XXXX` to configure your local WiFi and MQTT broker.
6. Copy the MAC address shown in the Serial Monitor and click **Link** in the web dashboard!

---

## 📜 License
* Developed for **Educational Purposes Only**.
