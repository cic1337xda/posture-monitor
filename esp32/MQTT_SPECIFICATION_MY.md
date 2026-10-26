# 📡 Spesifikasi Protokol & Telemetri MQTT (`MQTT_SPECIFICATION_MY.md`)

Dokumen ini memperincikan seni bina komunikasi MQTT, topik telemetri, muatan data (*payload*), dan mesin keadaan (*state machine*) bagi integrasi antara **Pelayan Posture AI** dan **Jam Wearable ESP32**.

---

## 🌐 Topologi Rangkaian & Broker

* **Enjin Broker:** Eclipse Mosquitto v2.0
* **Pemetaan Port Luaran (Hos):** Port `1888` (sambungan terus tanpa proksi Cloudflare)
* **Port Dalaman Kontena:** Port `1883`
* **Protokol Pengangkutan:** Soket TCP
* **Domain / IP Broker:** Boleh dilaraskan (cth: IP pelayan tempatan atau domain broker melalui WiFiManager)

---

## 🆔 Pengenalan Klien & Struktur Topik

### Pengecam Klien (*Client ID*)
Setiap peranti jam wearable membina ID unik secara automatik daripada Alamat MAC fizikal cip:
```text
ClientId: Wearable-<ALAMAT_MAC>
Contoh:   Wearable-A0764E551234
```

### Struktur Topik Arahan
Pelayan backend menghantar arahan haptik secara khusus ke topik peranti yang dipautkan:
```text
Topik: posture/wearable/<ALAMAT_MAC>/command
Contoh: posture/wearable/A0:76:4E:55:12:34/command
```

---

## 📨 Perintah Arahan & Tindak Balas Peranti

| Rentetan Arahan | Syarat Pencetus | Tindak Balas Motor Haptik | Kitaran & Tempoh Masa |
| :--- | :--- | :--- | :--- |
| **`vibrate_heavy`** | Had masa duduk tamat ($>600\text{s}$) atau postur teruk berterusan ($\ge 5\text{s}$) | Memulakan getaran fizikal berdenyut secara berterusan | Bertukar HIGH/LOW setiap $400\,\text{ms}$ |
| **`stop`** | Pengguna berdiri ($\ge 1\text{s}$) atau membetulkan postur tegak | Menamatkan getaran serta-merta dan meletakkan GPIO 8 ke LOW | Serta-merta ($0\,\text{ms}$) |
| **`linked`** | Pengguna berjaya memautkan Alamat MAC di papan pemuka web | Menghentikan sebarang getaran dan memberikan satu denyutan pengesahan | Satu denyutan sepanjang $300\,\text{ms}$ |

---

## ⚙️ Mesin Keadaan Firmware Tanpa Sekatan (*Non-Blocking*)

Firmware ESP32 menggunakan pemasaan `millis()` tanpa fungsi `delay()` yang menyekat thread utama, memastikan komunikasi MQTT sentiasa diproses secara lancar:

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

## 🛡️ Mekanisme Pemulihan & Sambung Semula

Sekiranya sambungan rangkaian terputus atau broker dimulakan semula:
1. `mqttClient.connected()` mengesan kegagalan sambungan dalam fungsi `loop()`.
2. Fungsi `reconnectMQTT()` menyambung semula secara automatik menggunakan ID `Wearable-<MAC>`.
3. Selepas berjaya bersambung, mikropengawal melanggan semula topik `posture/wearable/<MAC>/command`.
4. Jika pelayan belum sedia, peranti menunggu jeda masa $5\,\text{saat}$ sebelum mencuba semula.
