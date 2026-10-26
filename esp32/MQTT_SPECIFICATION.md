# 📡 MQTT Telemetry & Protocol Specification (`MQTT_SPECIFICATION.md`)

This document defines the MQTT communication protocol, topic architecture, payload payloads, and state machine governing the interaction between the **Posture AI Backend** and the **ESP32 Wearable Watch Client**.

---

## 🌐 Network & Broker Topology

* **Broker Engine:** Eclipse Mosquitto v2.0
* **External Host Mapping:** Port `1888` (bypasses Cloudflare proxy via DNS-only mapping)
* **Internal Docker Port:** Port `1883`
* **Transport:** TCP Socket
* **Broker Domain / IP:** Configurable (e.g. your local server IP or broker domain via WiFiManager)

---

## 🆔 Client Identification & Topic Structure

### Client Identifier
Every wearable device derives its unique client identifier from its physical factory hardware MAC address:
```text
ClientId: Wearable-<MAC_ADDRESS>
Example:  Wearable-A0764E551234
```

### Command Topic Architecture
The backend publishes actionable haptic instructions exclusively to the target wearable's dedicated topic:
```text
Topic: posture/wearable/<MAC_ADDRESS>/command
Example: posture/wearable/A0:76:4E:55:12:34/command
```

---

## 📨 Inbound Command Payloads & State Transitions

| Command String | Trigger Condition | Wearable Actuator Response | Duty Cycle / Timing |
| :--- | :--- | :--- | :--- |
| **`vibrate_heavy`** | Sedentary limit reached ($>600\text{s}$) or bad posture persists ($\ge 5\text{s}$) | Initiates continuous pulsating haptic vibration | Alternates HIGH/LOW every $400\,\text{ms}$ |
| **`stop`** | User stands up ($\ge 1\text{s}$) or corrects posture upright | Immediately terminates vibration and drives GPIO 8 LOW | Instantaneous ($0\,\text{ms}$) |
| **`linked`** | User successfully links device MAC on web dashboard | Halts any active vibration and executes a single confirmation pulse | Single pulse of $300\,\text{ms}$ |

---

## ⚙️ Non-Blocking Firmware State Machine

The ESP32 firmware executes a non-blocking haptic pulse loop using `millis()` timing, ensuring MQTT packet parsing and network polling remain uninterrupted:

```cpp
if (isVibrating) {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= pulseInterval) { // pulseInterval = 400ms
    previousMillis = currentMillis;
    motorState = (motorState == LOW) ? HIGH : LOW;
    digitalWrite(MOTOR_PIN, motorState);
  }
} else {
  digitalWrite(MOTOR_PIN, LOW);
}
```

---

## 🛡️ Resilience & Reconnection Watchdog

If the network connection drops or the broker restarts:
1. `mqttClient.connected()` evaluates to `false` in `loop()`.
2. `reconnectMQTT()` attempts connection using client ID `Wearable-<MAC>`.
3. Upon reconnection, the client automatically re-subscribes to `posture/wearable/<MAC>/command`.
4. If the broker is unreachable, a backoff timer waits $5\,\text{seconds}$ before retrying to prevent network congestion.
