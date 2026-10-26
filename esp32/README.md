# ⌚ Posture AI — Wearable Haptic Feedback Client (`esp32`)

This module houses the firmware, hardware schematics, and MQTT protocol specifications for the **Posture AI Wrist Wearable Device**. Built on the **ESP32-C3** RISC-V platform, it delivers synchronized haptic pulses to correct poor sitting posture and break up prolonged sedentary time.

---

## 📑 Language Options
* 🇬🇧 **[English Documentation (Current)](README.md)**
* 🇲🇾 **[Dokumentasi Bahasa Melayu](README_MY.md)**

---

## 📚 Technical Documentation Index

| Document | Description |
| :--- | :--- |
| 🔌 **[PINOUT_AND_WIRING.md](PINOUT_AND_WIRING.md)** | Microcontroller pin assignments, circuit schematic, BOM, and electrical protection rules. |
| 📡 **[MQTT_SPECIFICATION.md](MQTT_SPECIFICATION.md)** | Telemetry topics, payload commands (`vibrate_heavy`, `stop`, `linked`), and non-blocking state machine. |
| ⚡ **[FLASHING_AND_SETUP.md](FLASHING_AND_SETUP.md)** | Step-by-step Arduino IDE setup, libraries, board options, and captive portal WiFi configuration. |

---

## 🏛️ Wearable Architecture Overview

```text
                  +--------------------------------------------+
                  |         ESP32-C3 SUPERMINI (160MHz)        |
                  |                                            |
                  |  [WiFiManager]  -> Captive Portal AP Setup |
                  |  [PubSubClient] -> Port 1888/1883 Broker   |
                  |  [Radio Safety] -> btStop(), Tx 8.5 dBm    |
                  +--------------------------------------------+
                                         |
                                         | GPIO 8 (PWM Active-HIGH)
                                         v
                         +-------------------------------+
                         |   TRANSISTOR DRIVER CIRCUIT   |
                         |  - 1k Ohm Base Resistor       |
                         |  - 2N2222 NPN Transistor      |
                         |  - 1N4001 Flyback Clamp Diode |
                         +-------------------------------+
                                         |
                                         v
                         +-------------------------------+
                         |     COIN VIBRATION MOTOR      |
                         |  - 400ms Pulsating Cycle      |
                         |  - Synchronous Onboard LED    |
                         +-------------------------------+
```

---

## 📂 Source Code Map

* **Production Firmware:** `use-for-production-12sept2026-332pm/use-for-production-12sept2026-332pm.ino`
