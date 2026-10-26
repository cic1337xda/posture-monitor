# 🐳 Seni Bina Docker & Perkhidmatan Kontena (`DOCKER_AND_SERVICES_MY.md`)

Dokumen ini memperincikan infrastruktur kontena, topologi rangkaian multi-servis, spesifikasi pemboleh ubah persekitaran (*environment variables*), dan arahan pengurusan bagi **Platform Posture AI**.

---

## 🏛️ Topologi Multi-Kontena

Sistem ini diuruskan menggunakan `docker-compose.yml` yang membahagikan aplikasi kepada dua perkhidmatan mikro bebas berprestasi tinggi:

```
+---------------------------------------------------------------------------------------------------+
|                                  RANGKAIAN DOCKER: pwn20wnd-network                               |
+---------------------------------------------------------------------------------------------------+

              [ TRAFIK PELAYAR DESKTOP ]                         [ TRAFIK MQTT JAM WEARABLE ]
                     Port: 5000                                         Port: 1888
                          |                                                  |
                          v                                                  v
     +-----------------------------------------+        +-----------------------------------------+
     |        SERVIS: posture-monitor          |        |       SERVIS: posturemonitor-mqtt       |
     |                                         |        |                                         |
     |  - Nama Kontena: posture-monitor        |        |  - Nama Kontena: posturemonitor-mqtt    |
     |  - Asas: python:3.11-slim-bookworm      |  TCP   |  - Imej: eclipse-mosquitto:latest       |
     |  - Pelayan Web: Gunicorn (4 Threads)    | =====> |  - Port: 1888 (Hos) -> 1883 (Kontena)   |
     |  - Enjin AI: MediaPipe Pose 0.10.14     | :1883  |  - Volume: mosquitto.conf dipautkan     |
     |  - Storan: Pangkalan Data SQLite Auth   |        |  - Rangkaian: pwn20wnd-network          |
     +-----------------------------------------+        +-----------------------------------------+
```

---

## ⚙️ Spesifikasi Perkhidmatan

### 1. `posture-monitor` (Pelayan Aplikasi & Enjin Inferens AI)
* **Konteks Binaan:** `./backend` (`Dockerfile`)
* **Imej Asas:** `python:3.11-slim-bookworm`
* **Port Terdedah:** `5000:5000`
* **Pengurus Proses:** `gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 0 app:app`
* **Zon Masa:** `Asia/Kuala_Lumpur` (GMT+8)
* **Had Saiz Log:** Dihadkan kepada $10\,\text{MB}$ setiap fail, maksimum 3 fail putaran (*log rotation*).

### 2. `posturemonitor-mqtt` (Broker Telemetri Haptik)
* **Imej:** `eclipse-mosquitto:latest`
* **Port Hos:** `1888` $\rightarrow$ Port Dalaman Kontena `1883`
* **Pautan Konfigurasi:** `./mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf`
* **Rangkaian:** Disambungkan ke jambatan rangkaian luaran `pwn20wnd-network`.

---

## 📋 Matriks Pemboleh Ubah Persekitaran (`.env`)

| Pemboleh Ubah | Nilai Lalai | Penerangan Fungsi |
| :--- | :--- | :--- |
| `TZ` | `Asia/Kuala_Lumpur` | Menyelaraskan zon masa sistem ke Waktu Malaysia (GMT+8) |
| `MAX_SITTING_SECONDS` | `600` | Had masa duduk berterusan sebelum amaran sedentari berbunyi ($10\,\text{minit}$) |
| `MAX_BAD_POSTURE_SECONDS` | `5.0` | Had masa postur teruk berterusan sebelum amaran bongkok diaktifkan |
| `WARNING_PERCENT` | `0.60` | Peratusan masa duduk sebelum amaran kuning dipaparkan |
| `CRITICAL_PERCENT` | `0.85` | Peratusan masa duduk sebelum amaran merah dipaparkan |
| `DETECTION_CONFIDENCE` | `0.60` | Ambang keyakinan pengesanan titik MediaPipe Pose |
| `CALIBRATION_FRAMES` | `25` | Bilangan frame berturut-turut untuk merekodkan garis asas tegak |
| `RESEND_API_KEY` | *(Rahsia)* | Kunci pengesahan Bearer bagi perkhidmatan Resend Email API |
| `RESEND_FROM_EMAIL` | `posture@mail.flowkraft.xyz` | Alamat penghantar rasmi untuk penghantaran kod OTP |
| `JWT_SECRET_KEY` | *(Rahsia 32+ bytes)* | Kunci rahsia kriptografi HMAC untuk menandatangani cookie sesi |
| `MQTT_BROKER` | `posturemonitor-mqtt` | Nama hos perkhidmatan broker Mosquitto dalam rangkaian Docker |

---

## 🚀 Arahan Pengurusan & Pelancaran

### 1. Pastikan Rangkaian Docker Wujud
```bash
docker network inspect pwn20wnd-network >/dev/null 2>&1 || docker network create pwn20wnd-network
```

### 2. Lancarkan Kontena di Latar Belakang
```bash
docker compose up -d --build
```

### 3. Pantau Log Kontena Secara Langsung
```bash
docker compose logs -f posture-monitor
```

### 4. Hentikan Kontena
```bash
docker compose down
```

### 5. Semak Kesihatan Pelayan
```bash
curl http://localhost:5000/api/v1/health
```
