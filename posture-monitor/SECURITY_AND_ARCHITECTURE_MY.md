# 🛡️ Seni Bina Keselamatan & Algoritma Biometrik (`SECURITY_AND_ARCHITECTURE_MY.md`)

Dokumen ini menyediakan kupasan teknikal menyeluruh mengenai pelaksanaan keselamatan siber, perlindungan kriptografi, dan algoritma penglihatan komputer MediaPipe yang menguasai **Platform Posture AI**.

---

## 🔒 1. Seni Bina Keselamatan & Pematuhan Mandat

Sistem Posture AI mematuhi sepenuhnya piawaian keselamatan perusahaan yang digariskan dalam `DEVELOPMENT.md`:

### A. Pengesahan Sesi Cookie HttpOnly JWT (Kalis XSS)
* **Kelemahan Dicegah:** Kecurian token melalui serangan Cross-Site Scripting (XSS).
* **Pelaksanaan:** Token sesi tidak sekali-kali disimpan di dalam `localStorage` atau `sessionStorage` pelayar web.
* Pelayan mengeluarkan token JSON Web Token (JWT) yang ditandatangani secara kriptografi di dalam cookie dengan konfigurasi:
  * `HttpOnly`: Tidak boleh dibaca atau dimanipulasi oleh kod JavaScript pelayar.
  * `SameSite=Lax`: Menghalang serangan Cross-Site Request Forgery (CSRF) daripada laman web luar.
  * `Max-Age=604800`: Sesi tamat secara automatik selepas 7 hari.

### B. Enkripsi Kata Laluan Bcrypt & Syarat Kekuatan
* **Algoritma:** **Bcrypt** dengan penjanaan garam rawak unik (`bcrypt.gensalt()`).
* **Syarat Wajib Kata Laluan:**
  1. Minimum 8 aksara.
  2. Sekurang-kurangnya satu huruf besar (`[A-Z]`).
  3. Sekurang-kurangnya satu huruf kecil (`[a-z]`).
  4. Sekurang-kurangnya satu digit nombor (`[0-9]`).
  5. Sekurang-kurangnya satu simbol khas (`[!@#$%^&*(),.?":{}|<>]`).

### C. Perlindungan Serangan Brute-Force & Kunci Akaun
* Sistem mencatatkan bilangan kegagalan log masuk secara berterusan di dalam pangkalan data.
* Apabila mencapai **5 kali percubaan gagal**, akaun akan **dikunci secara automatik selama 15 minit** (`lockout_until = now + 15m`).
* Menghalang serangan tekaan kata laluan secara automatik (*dictionary attack*).

### D. Enjin Pengesahan Emel OTP Dua Faktor (Resend API)
* Akaun baharu didaftarkan dalam status tidak aktif (`is_active = 0`).
* **Penjanaan Kriptografi:** Menggunakan fungsi selamat Python `secrets.randbelow(900000) + 100000` untuk menghasilkan kod 6-digit rawak.
* **Had Keselamatan:**
  * Sah laku terhad kepada **10 minit** sahaja.
  * Terhad kepada **5 kali percubaan salah** sebelum kod dibatalkan.
  * Ditandakan sebagai sudah diguna (`is_used = 1`) sebaik sahaja pengesahan berjaya.
* **Saluran Emel:** Dihantar melalui Resend API daripada `posture@mail.flowkraft.xyz`.

### E. Kawalan Had Permintaan (*Rate Limiting*)
* Semua endpoint pengesahan (`/login`, `/register`, `/verify-otp`, `/forgot-password`) dilindungi oleh penapis had trafik IP (maksimum 15 permintaan dalam tempoh 60 saat).

### F. Pengepala Keselamatan HTTP (*Security Headers*)
Setiap respon HTTP daripada pelayan dilindungi dengan:
* `X-Frame-Options: DENY` (Menghalang serangan Clickjacking).
* `X-Content-Type-Options: nosniff` (Menghalang manipulasi jenis fail MIME).
* `Referrer-Policy: strict-origin-when-cross-origin`.

---

## 📐 2. Huraian Algoritma Visi Komputer & Biometrik

### A. Penyingkiran Getaran Isyarat (*EMASmoother*)
Koordinat titik tubuh MediaPipe daripada kamera webcam sentiasa terdedah kepada gangguan pencahayaan dan bunyi penderia (*noise*). Posture AI menapis koordinat penting menggunakan penapis **Purata Bergerak Eksponen (EMA)**:

$$S_t = \alpha \cdot X_t + (1 - \alpha) \cdot S_{t-1}$$

Dengan nilai $\alpha = 0.25$. Ini memastikan titik rangka bergerak lancar tanpa sebarang herotan atau kelewatan (*lag*).

### B. Penyelarasan Ambang Kalis Jarak Kamera (*Proximity-Invariant Scaling*)
Bagi mengelakkan sistem tersilap mengesan keadaan "Berdiri" apabila pengguna condong menghampiri webcam:
1. Lebar bahu asas ($W_{\text{base}}$) dan ketinggian Y asas ($Y_{\text{base}}$) disimpan semasa kalibrasi duduk tegak.
2. Nisbah lebar bahu semasa ($W_{\text{curr}}$) dihitung untuk menjana faktor skala dinamik:
   $$\text{Faktor Skala} = \frac{W_{\text{curr}}}{W_{\text{base}}}$$
3. Ketinggian bahu duduk dijangka diselaraskan pada setiap frame:
   $$Y_{\text{dijangka}} = 0.5 + (Y_{\text{base}} - 0.5) \cdot \text{Faktor Skala}$$
4. Garisan ambang berdiri diselaraskan secara automatik mengikut jarak pengguna:
   $$\text{Ambang}_Y = Y_{\text{dijangka}} - \text{Ofset Sensitiviti}$$

### C. Matriks 5 Vektor Anti-Tipu (*Anti-Cheat Detection*)
Bagi menghalang helah pengguna (seperti melorot ke belakang kerusi sambil mendongakkan dagu ke atas):

```text
                  +-----------------------------------+
                  |      MATRIKS BIOMETRIK 5-VEKTOR   |
                  +-----------------------------------+
                                    |
     +------------------------------+------------------------------+
     |                              |                              |
     v                              v                              v
[ 1. NISBAH LEHER ]        [ 2. BAHU TENGGELAM ]          [ 3. DONGAK KEPALA ]
Picu Bongkok:              Picu Anti-Cheat 1:             Picu Anti-Cheat 2:
Leher < 88% daripada Asas  Bahu > +0.035 Bawah Asas       Dongak > +0.045 Atas Asas
     |                              |                              |
     +------------------------------+------------------------------+
                                    |
     +------------------------------+------------------------------+
     |                                                             |
     v                                                             v
[ 4. TUNDUK KEPALA ]                                          [ 5. CONDONG TEPI ]
Picu Tunduk Bawah:                                            Picu Senget:
Sudut < -0.065 Bawah Asas                                     Bahu Senget > 10%
```

1. **Nisbah Leher Mengecut ($< 88\%$):** Mengesan leher tertekan dan badan membongkok ke hadapan (*slouching*).
2. **Bahu Tenggelam ($> +0.035$):** Mengesan apabila badan melorot ke bawah kerusi. Walaupun kepala didongakkan, paras bahu tetap rendah, lalu mencetuskan **Bad Posture**.
3. **Mendongak Berlebihan ($> +0.045$):** Menilai perbezaan menegak telinga dan hidung. Dagu yang didongakkan ke atas melepasi sudut biasa dicetuskan sebagai **Bad Posture**.
4. **Kepala Tertunduk ($< -0.065$):** Mengesan pandangan menunduk ke bawah (seperti melihat telefon pintar).
5. **Kecondongan Bahu ($> 10\%$):** Mengesan posisi badan senget sebelah atau bersandar pada satu pemegang kerusi.

### D. Penapis Kestabilan Undian Majoriti (*State Hysteresis*)
Bagi mengelakkan status berkelip-kelip laju akibat pergerakan rawak, klasifikasi mentah dimasukkan ke dalam giliran undian (`deque(maxlen=6)`). Status hanya akan berubah apabila undian majoriti ($\ge 50\% + 1$) bersetuju dengan keadaan baharu.
