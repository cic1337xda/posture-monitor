# ⌚ Posture AI — Peranti Haptik Boleh Pakai (`esp32`)

Modul ini mengandungi firmware, skematik perkakasan, dan spesifikasi protokol komunikasi MQTT untuk **Peranti Boleh Pakai Jam Posture AI**. Dibina berasaskan mikropengawal **ESP32-C3** RISC-V, ia memberikan maklum balas getaran fizikal untuk membetulkan postur duduk dan memecah tempoh sedentari (duduk terlalu lama).

---

## 📑 Pilihan Bahasa Dokumentasi
* 🇬🇧 **[English Documentation](README.md)**
* 🇲🇾 **[Dokumentasi Bahasa Melayu (Sedang Dipaparkan)](README_MY.md)**

---

## 📚 Indeks Dokumentasi Teknikal

| Dokumen | Penerangan |
| :--- | :--- |
| 🔌 **[PINOUT_AND_WIRING_MY.md](PINOUT_AND_WIRING_MY.md)** | Pemetaan pin mikropengawal, litar skematik, senarai komponen (BOM), dan perlindungan elektrik. |
| 📡 **[MQTT_SPECIFICATION_MY.md](MQTT_SPECIFICATION_MY.md)** | Topik telemetri, muatan arahan (`vibrate_heavy`, `stop`, `linked`), dan mesin keadaan tanpa sekatan. |
| ⚡ **[FLASHING_AND_SETUP_MY.md](FLASHING_AND_SETUP_MY.md)** | Panduan lengkap Arduino IDE, pustaka tambahan, tetapan papan, dan konfigurasi WiFi Captive Portal. |

---

## 🏛️ Gambaran Keseluruhan Seni Bina Peranti

```text
                  +--------------------------------------------+
                  |         ESP32-C3 SUPERMINI (160MHz)        |
                  |                                            |
                  |  [WiFiManager]  -> Persediaan WiFi Hotspot |
                  |  [PubSubClient] -> Port Broker 1888/1883   |
                  |  [Radio Safety] -> btStop(), Tx 8.5 dBm    |
                  +--------------------------------------------+
                                         |
                                         | GPIO 8 (Picu Aktif-HIGH)
                                         v
                         +-------------------------------+
                         |     LITAR PEMACU TRANSISTOR   |
                         |  - Perintang Tapak 1k Ohm     |
                         |  - Transistor NPN 2N2222      |
                         |  - Diod Flyback 1N4001        |
                         +-------------------------------+
                                         |
                                         v
                         +-------------------------------+
                         |       MOTOR GETAR SYILING     |
                         |  - Kitaran Nadi Denyutan 400ms|
                         |  - LED Papan Berkelip Serentak|
                         +-------------------------------+
```

---

## 📂 Peta Kod Sumber

* **Firmware Pengeluaran Rasmi:** `use-for-production-12sept2026-332pm/use-for-production-12sept2026-332pm.ino`
