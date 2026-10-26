# ⚡ ESP32 Firmware Flashing & Configuration Guide (`FLASHING_AND_SETUP.md`)

This guide walks you through compiling, flashing, and configuring the **Posture AI Wearable Haptic Client** firmware on an **ESP32-C3** microcontroller.

---

## 🛠️ Required Software & Libraries

### 1. Arduino IDE Setup
1. Download and install [Arduino IDE 2.x](https://www.arduino.cc/en/software).
2. Open **File** $\rightarrow$ **Preferences** and add the following URL into **Additional Boards Manager URLs**:
   ```text
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
3. Open **Tools** $\rightarrow$ **Board** $\rightarrow$ **Boards Manager**, search for `esp32` by **Espressif Systems**, and click **Install** (v2.0.14+ or v3.0+).

### 2. Required Libraries
Install the following libraries via **Tools** $\rightarrow$ **Manage Libraries**:
* **`PubSubClient`** (v2.8+) by *Nick O'Leary*
* **`WiFiManager`** (v2.0.16+) by *tzapu*

---

## ⚙️ Target Board Configurations (ESP32-C3)

Under the **Tools** menu, select the following parameters:

* **Board:** `ESP32C3 Dev Module`
* **Port:** Choose your serial COM / `/dev/ttyUSB0` port
* **USB CDC On Boot:** `Enabled` *(Crucial for serial terminal logs on ESP32-C3)*
* **Flash Frequency:** `80MHz`
* **Flash Mode:** `QIO`
* **Upload Speed:** `921600` (or `115200` if upload fails)
* **CPU Frequency:** `160MHz (WiFi)`

---

## 🚀 Flashing Steps

1. Connect the ESP32-C3 to your computer via a data-capable USB-C cable.
2. Open the source file:
   ```text
   esp32/use-for-production-12sept2026-332pm/use-for-production-12sept2026-332pm.ino
   ```
3. Click the **Upload** button ($\rightarrow$) in Arduino IDE.
4. If the device does not enter bootloader mode automatically, hold down the **BOOT** button, press and release the **RESET** button, then release **BOOT**.

---

## 📶 WiFiManager Captive Portal Provisioning

Once flashed, the wearable client broadcasts a localized WiFi hotspot for easy wireless provisioning without hardcoding credentials:

1. Power on the wearable.
2. Open WiFi settings on your phone or computer and connect to:
   ```text
   SSID: Posture_Watch_XXXXX
   ```
   *(XXXXX represents the last 5 characters of the device's MAC address).*
3. A captive portal page will automatically open (or navigate to `http://192.168.4.1`).
4. Click **Configure WiFi**:
   * Select your local 2.4GHz WiFi network and enter the password.
   * Enter your **MQTT Server** address (Your local server IP or configured domain).
5. Click **Save**. The wearable will reboot and connect to your network.

---

## 🔗 Linking Wearable to Web Dashboard

1. Open the Arduino IDE Serial Monitor at **115200 baud** to view the device's MAC address:
   ```text
   [NETWORK] Connection Established Successfully.
   [INFO] Target MAC Address for Web UI configuration: 70:04:1D:XX:XX:XX
   ```
2. Navigate to the Posture AI Web Dashboard (`http://localhost:5000`).
3. Under the **Wearable Watch (ESP32)** card on the sidebar:
   * Paste your MAC address into the text field.
   * Click the **Link** button.
4. The wearable motor will pulse once for **$300\,\text{ms}$**, and the status badge will display **Linked** in vibrant green!
