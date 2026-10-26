# 🖥️ Posture AI — Pelayan & Papan Pemuka Web (`posture-monitor`)

Direktori ini mengandungi pelayan backend berkontena, saluran inferens penglihatan komputer MediaPipe, perkhidmatan pangkalan data pengesahan pengguna, dan papan pemuka web bertema Apple Liquid Glass bagi **Sistem Posture AI**.

---

## 📑 Pilihan Bahasa Dokumentasi
* 🇬🇧 **[English Documentation](README.md)**
* 🇲🇾 **[Dokumentasi Bahasa Melayu (Sedang Dipaparkan)](README_MY.md)**

---

## 📚 Indeks Dokumentasi Teknikal

| Dokumen | Penerangan |
| :--- | :--- |
| 📖 **[API_DOCUMENTATION_MY.md](API_DOCUMENTATION_MY.md)** | Rujukan lengkap endpoint REST API bagi pengesahan, inferens frame video, dan kawalan perkakasan. |
| 🐳 **[DOCKER_AND_SERVICES_MY.md](DOCKER_AND_SERVICES_MY.md)** | Seni bina multi-kontena Docker Compose, konfigurasi broker Mosquitto, dan senarai pemboleh ubah persekitaran. |
| 🛡️ **[SECURITY_AND_ARCHITECTURE_MY.md](SECURITY_AND_ARCHITECTURE_MY.md)** | Huraian mendalam mengenai keselamatan Bcrypt, cookie HttpOnly, OTP Resend, dan algoritma pengesanan 5-vektor. |

---

## 🛠️ Tindanan Teknologi (*Tech Stack*)

* **Rangka Kerja Web:** Flask 3.0+ / Python 3.11-slim
* **Pelayan Pengeluaran WSGI:** Gunicorn 21.2 (4 threads, tanpa sekatan)
* **Enjin Visi Komputer:** Google MediaPipe Pose 0.10.14 & Pillow 10+
* **Pengesahan & Kriptografi:** Bcrypt + PyJWT (Cookie selamat `HttpOnly; SameSite=Lax`)
* **Pangkalan Data:** SQLite 3 (`posture_auth.db`) dengan inisialisasi automatik
* **Emel Transaksi OTP:** Integrasi Resend API (`posture@mail.flowkraft.xyz`)
* **Broker Telemetri Haptik:** Eclipse Mosquitto v2.0 (MQTT)
* **Enjin Antara Muka Web:** Apple Liquid Glass (Vanilla JS, Canvas, WebRTC, Web Audio API, Google Font Roboto)

---

## 🚀 Pelancaran Docker Tempatan

```bash
# 1. Sediakan Pemboleh Ubah Persekitaran
cp .env.example .env

# 2. Bina dan Mulakan Kontena
docker compose up -d --build

# 3. Pantau Log Pelayan Secara Langsung
docker compose logs -f posture-monitor
```

* **Alamat Papan Pemuka:** `http://localhost:5000`
* **Endpoint Semakan Kesihatan:** `http://localhost:5000/api/v1/health`
* **Port Telemetri MQTT:** `1888` (luaran hos) $\rightarrow$ `1883` (dalaman rangkaian Docker)
