# ⚡ Panduan Flashing Firmware & Persediaan ESP32 (`FLASHING_AND_SETUP_MY.md`)

Panduan ini menerangkan langkah demi langkah untuk mengkompilasi, memuat naik (*flash*), dan mengkonfigurasi firmware **Peranti Haptik Boleh Pakai Posture AI** pada mikropengawal **ESP32-C3**.

---

## 🛠️ Perisian & Pustaka Yang Diperlukan

### 1. Persediaan Arduino IDE
1. Muat turun dan pasang [Arduino IDE 2.x](https://www.arduino.cc/en/software).
2. Buka **File** $\rightarrow$ **Preferences** dan masukkan pautan URL berikut ke dalam ruangan **Additional Boards Manager URLs**:
   ```text
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
3. Buka **Tools** $\rightarrow$ **Board** $\rightarrow$ **Boards Manager**, cari pakej `esp32` oleh **Espressif Systems**, dan tekan **Install** (versi 2.0.14+ atau 3.0+).

### 2. Pustaka Tambahan
Pasang pustaka berikut melalui menu **Tools** $\rightarrow$ **Manage Libraries**:
* **`PubSubClient`** (v2.8+) oleh *Nick O'Leary*
* **`WiFiManager`** (v2.0.16+) oleh *tzapu*

---

## ⚙️ Tetapan Papan Sasaran (ESP32-C3)

Pada menu **Tools**, pilih tetapan konfigurasi seperti berikut:

* **Board:** `ESP32C3 Dev Module`
* **Port:** Pilih port siri COM anda (cth: `/dev/ttyUSB0`)
* **USB CDC On Boot:** `Enabled` *(Penting untuk melihat output Serial Monitor pada cip ESP32-C3)*
* **Flash Frequency:** `80MHz`
* **Flash Mode:** `QIO`
* **Upload Speed:** `921600` (atau `115200` jika gagal muat naik)
* **CPU Frequency:** `160MHz (WiFi)`

---

## 🚀 Langkah-langkah Muat Naik Firmware

1. Sambungkan papan ESP32-C3 ke komputer menggunakan kabel data USB-C.
2. Buka fail kod sumber:
   ```text
   esp32/use-for-production-12sept2026-332pm/use-for-production-12sept2026-332pm.ino
   ```
3. Tekan butang **Upload** ($\rightarrow$) dalam Arduino IDE.
4. Sekiranya peranti tidak memasuki mod bootloader secara automatik, tekan dan tahan butang **BOOT**, tekan dan lepaskan butang **RESET**, kemudian lepaskan butang **BOOT**.

---

## 📶 Konfigurasi WiFi Melalui Captive Portal

Selepas firmware berjaya dimuat naik, peranti wearable akan memancarkan WiFi Hotspot sendiri bagi membolehkan persediaan kata laluan tanpa perlu menulis kod secara manual:

1. Hidupkan peranti wearable.
2. Buka tetapan WiFi pada telefon atau laptop anda dan sambung ke:
   ```text
   SSID: Posture_Watch_XXXXX
   ```
   *(XXXXX mewakili 5 digit terakhir Alamat MAC peranti).*
3. Halaman Captive Portal akan terbuka secara automatik (atau buka pelayar web ke alamat `http://192.168.4.1`).
4. Klik **Configure WiFi**:
   * Pilih rangkaian WiFi 2.4GHz anda dan masukkan kata laluan.
   * Masukkan alamat **MQTT Server** (Alamat IP pelayan tempatan atau domain broker anda).
5. Klik **Save**. Peranti akan mula menyambung ke rangkaian WiFi anda.

---

## 🔗 Memautkan Peranti ke Papan Pemuka Web

1. Buka Serial Monitor di Arduino IDE pada kadar **115200 baud** untuk melihat Alamat MAC peranti:
   ```text
   [NETWORK] Connection Established Successfully.
   [INFO] Target MAC Address for Web UI configuration: 70:04:1D:XX:XX:XX
   ```
2. Buka Papan Pemuka Web Posture AI (`http://localhost:5000`).
3. Pada kad **Wearable Watch (ESP32)** di bar sisi kanan:
   * Tampal Alamat MAC peranti anda ke dalam ruangan teks.
   * Tekan butang **Link**.
4. Motor jam wearable akan bergetar sekali selama **$300\,\text{ms}$** sebagai pengesahan, dan status akan bertukar kepada warna hijau **Linked**!
