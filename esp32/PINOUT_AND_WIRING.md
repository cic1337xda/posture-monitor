# 🔌 Pinout & Hardware Wiring Specification (`PINOUT_AND_WIRING.md`)

This document provides the complete hardware wiring blueprint, component specifications, and pin mapping for the **Posture AI Wearable Haptic Feedback Client** based on the **ESP32-C3** architecture.

---

## 📌 Complete Pin Assignment Table

| Microcontroller Pin | Subsystem Connection | Signal Description | Electrical Characteristics |
| :--- | :--- | :--- | :--- |
| **`GPIO 8`** | Transistor Base ($R_1$) | PWM Haptic Trigger / Built-in LED | 3.3V Logic HIGH active, synchronized with onboard LED |
| **`3.3V` / `5V`** | Motor (+) & Diode Cathode | DC Power Supply Rail | Supplies operating current to vibration motor (~70mA peak) |
| **`GND`** | Transistor Emitter (E) | System Common Ground | Reference ground plane |
| **Motor (-)** | Transistor Collector (C) | Switched Ground Sink | Pulled LOW when `GPIO 8` is driven HIGH |

---

## 📐 Circuit Schematic Diagram

The wearable client employs an **NPN low-side transistor switch** with an inductive flyback suppression diode:

<p align="center">
  <img src="Schematic_posturemonitor_2026-10-26.png" width="820" alt="ESP32-C3 Wearable Haptic Schematic" />
</p>

* 📄 **Download Printable Schematic PDF:** [`Schematic_posturemonitor_2026-10-26.pdf`](Schematic_posturemonitor_2026-10-26.pdf)

---

## 🧩 Bill of Materials (BOM)

| Item | Component Description | Recommended Model | Purpose |
| :---: | :--- | :--- | :--- |
| **1** | ESP32-C3 RISC-V Microcontroller | ESP32-C3 SuperMini / Xiao ESP32C3 | Main processing unit, WiFi client, and MQTT subscriber |
| **2** | Coin Vibration Motor | 1027 / 1030 3V Coin Disc Motor | Generates tactile haptic alerts on user's wrist |
| **3** | NPN Switching Transistor | 2N2222 / 2N3904 / S8050 | Amplifies low-current GPIO to drive motor current (~70mA) |
| **4** | Base Current-Limiting Resistor | $1\,\text{k}\Omega$ ($0.25\text{W}$) | Limits base current to $\approx 2.6\text{mA}$, protecting GPIO pin |
| **5** | Flyback Protection Diode | 1N4001 / 1N4148 | Absorbs inductive voltage spikes when motor stops |
| **6** | Power Source | 3.7V LiPo Battery or USB-C 5V | Portable battery pack or direct USB tether |

---

## ⚠️ Hardware Protection Principles

1. **Why Direct GPIO Connection Is Prohibited:**
   An ESP32-C3 GPIO pin can source a maximum of **$20\text{mA}$**. Coin vibration motors draw **$60\text{mA}$ to $90\text{mA}$** during rotation. Connecting the motor directly to a GPIO pin will permanently burn out the microcontroller output driver.
2. **Flyback Spike Suppression:**
   Because motors are inductive loads, rapidly switching them off causes an opposing voltage spike ($V = -L \frac{di}{dt}$) exceeding 30V. The **1N4001 diode** placed across the motor terminals redirects and clamps this back-EMF pulse safely.
3. **Power Stability Workarounds in Firmware:**
   - `btStop()` is invoked immediately in `setup()` to deactivate Bluetooth radio and conserve peak operating current.
   - `WiFi.setTxPower(WIFI_POWER_8_5dBm)` caps transmission power to $8.5\,\text{dBm}$ to prevent brownout resets caused by small linear regulators.
