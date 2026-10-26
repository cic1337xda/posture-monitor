# 📖 Rujukan Dokumentasi REST API (`API_DOCUMENTATION_MY.md`)

Dokumen ini menyediakan rujukan lengkap bagi setiap endpoint **REST API Pelayan Posture AI**, merangkumi fungsi pengesahan pengguna, pengesahan OTP, inferens penglihatan komputer MediaPipe, dan kawalan perkakasan.

---

## 🏛️ Sampul Respons Piawai (*Standard Response Envelope*)

Semua endpoint API mengembalikan data dalam format JSON mengikut format standard:

```json
{
  "success": true,
  "message": "Operasi berjaya disempurnakan.",
  "data": { ... },
  "error": null
}
```

---

## 🏥 Endpoint Kesihatan & Sistem

### 1. Semakan Kesihatan Pelayan (*Healthcheck*)
* **Kaedah:** `GET`
* **Laluan:** `/api/v1/health`
* **Pengesahan:** Tiada (Awam)
* **Contoh Respons:**
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "timestamp": "2026-10-26T20:30:00+08:00"
  }
  ```

---

## 🔒 Endpoint Pengesahan Pengguna & OTP

### 2. Pendaftaran Pengguna Baharu
* **Kaedah:** `POST`
* **Laluan:** `/api/auth/register`
* **Had Permintaan:** 15 kali / minit
* **Badan Permintaan (*Request Body*):**
  ```json
  {
    "username": "ahmad",
    "email": "ahmad@example.com",
    "password": "PasswordKuat123!"
  }
  ```
* **Syarat Pengesahan:**
  * Nama pengguna: $\ge 3$ aksara.
  * Kata laluan: $\ge 8$ aksara, mengandungi huruf besar, huruf kecil, nombor, dan simbol.
* **Tindak Balas:** Mencipta rekod pengguna dalam status belum aktif (`is_active = 0`) dan menghantar kod OTP 6-digit ke emel melalui Resend API.

---

### 3. Pengesahan OTP & Pengaktifan Akaun
* **Kaedah:** `POST`
* **Laluan:** `/api/auth/verify-otp`
* **Badan Permintaan:**
  ```json
  {
    "email": "ahmad@example.com",
    "otp_code": "849201",
    "purpose": "register"
  }
  ```
* **Tindak Balas:** Mengesahkan kod OTP 6-digit. Jika sah, akaun diaktifkan dan token sesi ditanam dalam cookie `session_token` (`HttpOnly; SameSite=Lax; Max-Age=604800`).

---

### 4. Log Masuk Pengguna
* **Kaedah:** `POST`
* **Laluan:** `/api/auth/login`
* **Had Permintaan:** 15 kali / minit
* **Badan Permintaan:**
  ```json
  {
    "identifier": "ahmad",
    "password": "PasswordKuat123!"
  }
  ```
* **Tindak Balas:** Menyemak status kunci akaun (akaun dikunci 15 minit selepas 5 percubaan salah). Mengesahkan hash Bcrypt. Jika sah, token sesi dikeluarkan.

---

### 5. Permintaan Lupa Kata Laluan (*Forgot Password*)
* **Kaedah:** `POST`
* **Laluan:** `/api/auth/forgot-password`
* **Badan Permintaan:**
  ```json
  {
    "email": "ahmad@example.com"
  }
  ```
* **Tindak Balas:** Menjana kod OTP 6-digit untuk set semula kata laluan dan dihantar ke emel pengguna.

---

### 6. Kemas Kini Kata Laluan Baharu Menggunakan OTP
* **Kaedah:** `POST`
* **Laluan:** `/api/auth/reset-password`
* **Badan Permintaan:**
  ```json
  {
    "email": "ahmad@example.com",
    "otp_code": "849201",
    "new_password": "PasswordBaru456!"
  }
  ```
* **Tindak Balas:** Mengesahkan OTP pemulihan dan mengemas kini hash kata laluan baharu pengguna.

---

### 7. Log Keluar
* **Kaedah:** `POST`
* **Laluan:** `/api/auth/logout`
* **Tindak Balas:** Memadamkan cookie `session_token` (`Max-Age=0`).

---

### 8. Profil Sesi Semasa
* **Kaedah:** `GET`
* **Laluan:** `/api/auth/me`
* **Cookie Diperlukan:** `session_token`
* **Respons Berjaya (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "user": {
        "id": 1,
        "username": "ahmad",
        "email": "ahmad@example.com"
      }
    },
    "error": null
  }
  ```

---

## 👁️ Endpoint Penglihatan Komputer & Inferens

### 9. Pemprosesan Frame Video
* **Kaedah:** `POST`
* **Laluan:** `/api/process`
* **Format Kandungan:** `image/jpeg` (Bait binari frame mentah)
* **Contoh Respons (200 OK):**
  ```json
  {
    "state": "Sitting",
    "alert_level": "normal",
    "alert_message": "You're doing fine.",
    "remaining": 582,
    "fraction": 0.03,
    "bad_posture_duration": 0.0,
    "alarm": false,
    "metrics": "Neck: 98% | Drop: +0.01 | Pitch: -0.01",
    "calibrating": false,
    "calibration_progress": 0,
    "stand_up_count": 3,
    "recent_celebration": false,
    "landmarks": [ ... ]
  }
  ```

---

## 🎮 Kawalan Perkakasan & Arahan

### 10. Kalibrasi Semula Kedudukan Asas
* **Kaedah:** `POST`
* **Laluan:** `/command/calibrate`
* **Tindak Balas:** Memulakan proses 25 frame untuk merakam ketinggian bahu, lebar bahu, dan nisbah leher semasa pengguna duduk tegak.

### 11. Tetapan Masa Duduk Kustom
* **Kaedah:** `POST`
* **Laluan:** `/command/set_time/<int:seconds>`
* **Contoh:** `POST /command/set_time/300` (Menetapkan had masa duduk berterusan kepada 5 minit).

### 12. Pautkan Jam Wearable ESP32
* **Kaedah:** `POST`
* **Laluan:** `/command/wearable`
* **Badan Permintaan:**
  ```json
  {
    "mac": "70:04:1D:XX:XX:XX"
  }
  ```
* **Tindak Balas:** Mengikat alamat MAC ke topik MQTT `posture/wearable/<MAC>/command` dan menghantar isyarat `"linked"` untuk mencetuskan getaran pengesahan selama 300ms pada jam.
